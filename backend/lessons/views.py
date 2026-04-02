import logging
import os
import uuid
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Lesson, Question, InteractionRecord, LessonSession
from .serializers import (
    LessonSerializer, LessonListSerializer, QuestionSerializer,
    InteractionRecordSerializer,
    AnswerSubmitSerializer, StatisticsSerializer
)
from .tasks import validate_answer_task

logger = logging.getLogger(__name__)


def health_check(request):
    return JsonResponse({'status': 'ok'})


def backend_root(request):
    """
    Подсказка при открытии :8000/ в браузере (фронт отдельно, обычно :3000).
    """
    frontend = os.environ.get('FRONTEND_PUBLIC_URL', 'http://localhost:3000')
    accept = request.headers.get('Accept', '')
    if 'application/json' in accept and 'text/html' not in accept:
        return JsonResponse(
            {
                'service': 'nastavnik-backend',
                'docs': 'API под префиксом /api/',
                'openapi': '/api/schema/',
                'swagger_ui': '/api/schema/swagger-ui/',
                'health': '/api/health/',
                'frontend': frontend,
            }
        )
    body = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Nastavnik — backend</title></head>
<body style="font-family:system-ui,sans-serif;max-width:36rem;margin:2rem auto;line-height:1.5">
  <h1>Nastavnik (backend)</h1>
  <p>Это API-сервер Django. Веб-интерфейс откройте по ссылке:</p>
  <p><a href="{frontend}">{frontend}</a></p>
  <ul>
    <li><a href="/api/schema/swagger-ui/"><code>Swagger UI</code></a> (OpenAPI)</li>
    <li><a href="/api/health/"><code>/api/health/</code></a></li>
    <li><a href="/api/lessons/"><code>/api/lessons/</code></a></li>
    <li><a href="/admin/"><code>/admin/</code></a></li>
  </ul>
</body></html>"""
    return HttpResponse(body, content_type='text/html; charset=utf-8')


def _ordered_questions(lesson):
    return list(lesson.questions.order_by('order'))


def _question_at_index(lesson, index):
    questions = _ordered_questions(lesson)
    if index < 0 or index >= len(questions):
        return None
    return questions[index]


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return LessonListSerializer
        return LessonSerializer

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        lesson = self.get_object()
        session_id = request.data.get('session_id') or str(uuid.uuid4())

        session, created = LessonSession.objects.get_or_create(
            session_id=session_id,
            lesson=lesson,
            defaults={'current_question_index': 0}
        )

        # Повтор того же урока с тем же session_id (после завершения и статистики).
        if not created and session.is_completed:
            InteractionRecord.objects.filter(session_id=session_id, lesson=lesson).delete()
            session.is_completed = False
            session.completed_at = None
            session.current_question_index = 0
            session.started_at = timezone.now()
            session.save(
                update_fields=[
                    'is_completed',
                    'completed_at',
                    'current_question_index',
                    'started_at',
                ]
            )

        if created:
            session.current_question_index = 0
            session.save(update_fields=['current_question_index'])

        current_question = _question_at_index(lesson, session.current_question_index)
        return Response({
            'session_id': session.session_id,
            'lesson': LessonSerializer(lesson).data,
            'current_question': QuestionSerializer(current_question).data if current_question else None,
            'current_question_index': session.current_question_index,
            'total_questions': lesson.questions.count()
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        lesson = self.get_object()
        session_id = request.data.get('session_id')

        if not session_id:
            return Response(
                {'error': 'session_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = LessonSession.objects.get(session_id=session_id, lesson=lesson)
        except LessonSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        questions = _ordered_questions(lesson)
        answered_ids = set(
            InteractionRecord.objects.filter(
                session_id=session_id,
                lesson=lesson,
            ).values_list('question_id', flat=True)
        )

        now = timezone.now()
        for q in questions:
            if q.id not in answered_ids:
                InteractionRecord.objects.create(
                    session_id=session_id,
                    lesson=lesson,
                    question=q,
                    user_answer='',
                    is_correct=False,
                    ml_service_success=False,
                    answered_at=now,
                )

        session.is_completed = True
        session.completed_at = now
        session.current_question_index = len(questions)
        session.save()

        return Response({
            'success': True,
            'success_rate': session.success_rate,
            'remaining_marked_incorrect': len(questions) - len(answered_ids),
        })


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    @action(detail=False, methods=['get'])
    def current(self, request):
        session_id = request.query_params.get('session_id')
        lesson_id = request.query_params.get('lesson_id')
        if not session_id or not lesson_id:
            return Response(
                {'error': 'session_id and lesson_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = LessonSession.objects.get(session_id=session_id, lesson_id=lesson_id)
            questions = _ordered_questions(session.lesson)
            question = _question_at_index(session.lesson, session.current_question_index)

            return Response({
                'current_question': QuestionSerializer(question).data if question else None,
                'current_question_index': session.current_question_index,
                'total_questions': len(questions),
                'is_completed': session.is_completed
            })
        except LessonSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
def submit_answer(request):
    serializer = AnswerSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session_id = serializer.validated_data['session_id']
    question_id = serializer.validated_data['question_id']
    answer = serializer.validated_data['answer']

    try:
        session = LessonSession.objects.get(session_id=session_id)
        question = Question.objects.get(id=question_id)
    except (LessonSession.DoesNotExist, Question.DoesNotExist):
        return Response(
            {'error': 'Session or question not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if session.is_completed:
        return Response(
            {'error': 'Session already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if question.lesson_id != session.lesson_id:
        return Response(
            {'error': 'Question does not belong to this session lesson'},
            status=status.HTTP_400_BAD_REQUEST
        )

    questions = _ordered_questions(session.lesson)
    if session.current_question_index >= len(questions):
        return Response(
            {'error': 'No more questions in this lesson'},
            status=status.HTTP_400_BAD_REQUEST
        )

    expected = questions[session.current_question_index]
    if expected.id != question.id:
        return Response(
            {'error': 'Answer the current question before moving on'},
            status=status.HTTP_400_BAD_REQUEST
        )

    interaction = InteractionRecord.objects.create(
        session_id=session_id,
        lesson=session.lesson,
        question=question,
        user_answer=answer,
        answered_at=timezone.now()
    )

    validate_answer_task.delay(
        str(interaction.id),
        str(question.id),
        answer
    )

    session.current_question_index += 1
    session.save(update_fields=['current_question_index'])

    next_question = _question_at_index(session.lesson, session.current_question_index)

    payload = {
        'interaction_id': str(interaction.id),
        'status': 'processing',
        'next_question': QuestionSerializer(next_question).data if next_question else None,
        'current_question_index': session.current_question_index,
        'total_questions': len(questions),
        'lesson_complete': next_question is None,
    }
    return Response(payload)


@api_view(['GET'])
def interaction_status(request, interaction_id):
    try:
        interaction = InteractionRecord.objects.get(id=interaction_id)
        return Response(InteractionRecordSerializer(interaction).data)
    except InteractionRecord.DoesNotExist:
        return Response(
            {'error': 'Interaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def statistics(request):
    session_id = request.query_params.get('session_id')
    lesson_id = request.query_params.get('lesson_id')
    if lesson_id and not session_id:
        return Response(
            {'error': 'session_id is required when lesson_id is set'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if lesson_id:
        try:
            uuid.UUID(str(lesson_id))
        except (ValueError, TypeError, AttributeError):
            return Response(
                {'error': 'invalid lesson_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    interactions = InteractionRecord.objects.all()
    session_qs = LessonSession.objects.all()
    if session_id:
        interactions = interactions.filter(session_id=session_id)
        session_qs = session_qs.filter(session_id=session_id)
    if lesson_id:
        interactions = interactions.filter(lesson_id=lesson_id)
        session_qs = session_qs.filter(lesson_id=lesson_id)

    lesson_title = None
    scope = 'lesson' if lesson_id else 'all'
    if lesson_id:
        try:
            lesson_title = Lesson.objects.only('title').get(id=lesson_id).title
        except Lesson.DoesNotExist:
            lesson_title = None

    total = interactions.count()
    correct = interactions.filter(is_correct=True).count()
    ml_failures = interactions.filter(ml_service_success=False).count()
    timeouts = interactions.filter(user_answer='').count()
    ml_ok = interactions.filter(ml_service_success=True).count()

    durations = []
    for s in session_qs.filter(is_completed=True):
        if s.completed_at and s.started_at:
            durations.append((s.completed_at - s.started_at).total_seconds())
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0

    serializer = StatisticsSerializer({
        'total_sessions': session_qs.count(),
        'completed_sessions': session_qs.filter(is_completed=True).count(),
        'total_questions_answered': total,
        'correct_answers': correct,
        'success_rate': round((correct / total) * 100, 1) if total > 0 else 0,
        'ml_failures': ml_failures,
        'timeouts': timeouts,
        'ml_successful_validations': ml_ok,
        'avg_session_duration_sec': avg_duration,
        'scope': scope,
        'lesson_title': lesson_title,
    })

    return Response(serializer.data)
