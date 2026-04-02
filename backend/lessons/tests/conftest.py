import pytest
from django.test import TestCase
from lessons.models import Lesson, Question, InteractionRecord, LessonSession


@pytest.fixture
def lesson():
    return Lesson.objects.create(
        title="Test Lesson",
        text="This is a test lesson text."
    )


@pytest.fixture
def questions(lesson):
    return [
        Question.objects.create(
            lesson=lesson,
            text="What is 2+2?",
            correct_answer="4",
            distractor_1="5",
            distractor_2="22",
            order=1,
        ),
        Question.objects.create(
            lesson=lesson,
            text="What is the capital of France?",
            correct_answer="Paris",
            distractor_1="Lyon",
            distractor_2="Marseille",
            order=2,
        ),
    ]


@pytest.fixture
def question(questions):
    return questions[0]


@pytest.fixture
def session(lesson):
    return LessonSession.objects.create(
        session_id="test-session-123",
        lesson=lesson
    )


@pytest.fixture
def interaction(lesson, questions, session):
    return InteractionRecord.objects.create(
        session_id="test-session-123",
        lesson=lesson,
        question=questions[0],
        user_answer="4",
        is_correct=True,
        ml_service_success=True
    )
