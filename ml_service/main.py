import os
import asyncio
import random
import logging
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationRequest(BaseModel):
    question_id: str
    user_answer: str


class ValidationResponse(BaseModel):
    result: int


class HealthResponse(BaseModel):
    status: str


def _async_db_url(url: str) -> str:
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    return url


redis_client = None
engine = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_redis():
    global redis_client
    if redis_client is None:
        redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
        redis_client = redis.from_url(redis_url)
    return redis_client


def check_answer_cached(question_id: str, user_answer: str) -> bool | None:
    r = get_redis()
    cache_key = f'answer:{question_id}'
    cached = r.get(cache_key)
    if cached:
        correct_answer = cached.decode('utf-8').lower()
        return user_answer.lower().strip() == correct_answer
    return None


async def check_answer_db(question_id: str, user_answer: str) -> bool:
    assert async_session_factory is not None
    async with async_session_factory() as session:
        result = await session.execute(
            text(
                'SELECT correct_answer FROM lessons_question '
                'WHERE id = CAST(:qid AS uuid)'
            ),
            {'qid': question_id},
        )
        row = result.fetchone()
        if not row:
            return False
        correct_answer = row[0]
        r = get_redis()
        r.setex(f'answer:{question_id}', 3600, correct_answer)
        return user_answer.lower().strip() == str(correct_answer).lower()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, async_session_factory
    logger.info('ML Service starting up')
    db_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://nastavnik:nastavnik_secret@db:5432/nastavnik',
    )
    engine = create_async_engine(_async_db_url(db_url), pool_pre_ping=True)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    yield
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None
    if engine:
        await engine.dispose()
        engine = None
        async_session_factory = None
    logger.info('ML Service shutting down')


app = FastAPI(
    title='Nastavnik ML Service',
    description='Simulated ML service for answer validation',
    version='1.0.0',
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint='/metrics')


@app.get('/health', response_model=HealthResponse)
async def health_check():
    return {'status': 'ok'}


@app.post('/validate', response_model=ValidationResponse)
async def validate_answer(request: ValidationRequest):
    logger.info('Validating answer for question %s', request.question_id)

    await asyncio.sleep(5)

    if random.random() < 0.33:
        logger.warning('Simulating LLM service unavailable')
        raise HTTPException(status_code=503, detail='LLM unavailable')

    is_correct = check_answer_cached(request.question_id, request.user_answer)

    if is_correct is None:
        try:
            is_correct = await check_answer_db(request.question_id, request.user_answer)
        except Exception as e:
            logger.error('Failed to check answer: %s', e)
            raise HTTPException(status_code=503, detail='Service unavailable') from e

    result = 1 if is_correct else 0
    logger.info('Answer validation result: %s', result)

    return ValidationResponse(result=result)
