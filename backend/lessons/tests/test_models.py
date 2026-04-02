import pytest
from django.test import TestCase
from lessons.models import Lesson, Question, InteractionRecord, LessonSession


@pytest.mark.django_db
class TestLessonModel:
    def test_create_lesson(self, lesson):
        assert lesson.title == "Test Lesson"
        assert lesson.text == "This is a test lesson text."
        assert str(lesson) == "Test Lesson"

    def test_lesson_ordering(self):
        l1 = Lesson.objects.create(title="First", text="Text 1")
        l2 = Lesson.objects.create(title="Second", text="Text 2")
        lessons = list(Lesson.objects.all())
        assert lessons[0].id == l1.id


@pytest.mark.django_db
class TestQuestionModel:
    def test_create_question(self, question):
        assert question.text == "What is 2+2?"
        assert question.correct_answer == "4"
        assert question.order == 1

    def test_question_ordering(self, lesson):
        q1 = Question.objects.create(
            lesson=lesson,
            text="Q1",
            correct_answer="A1",
            distractor_1="x",
            distractor_2="y",
            order=2,
        )
        q2 = Question.objects.create(
            lesson=lesson,
            text="Q2",
            correct_answer="A2",
            distractor_1="x",
            distractor_2="y",
            order=1,
        )
        questions = list(lesson.questions.all())
        assert questions[0].id == q2.id

    def test_shuffled_choices_three_items(self, question):
        ch = question.shuffled_choices()
        assert len(ch) == 3
        assert set(ch) == {'4', '5', '22'}


@pytest.mark.django_db
class TestInteractionRecordModel:
    def test_create_interaction(self, interaction):
        assert interaction.user_answer == "4"
        assert interaction.is_correct is True
        assert interaction.ml_service_success is True

    def test_success_rate(self, session, interaction):
        assert session.success_rate == 100.0


@pytest.mark.django_db
class TestLessonSessionModel:
    def test_create_session(self, session):
        assert session.session_id == "test-session-123"
        assert session.is_completed is False
        assert session.current_question_index == 0
