import json
from unittest.mock import patch

import pytest
from django.test import Client
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from lessons.models import Lesson, Question, InteractionRecord


@pytest.mark.django_db
class TestLessonAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_list_lessons(self, lesson):
        response = self.client.get('/api/lessons/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_get_lesson_detail(self, lesson, questions):
        response = self.client.get(f'/api/lessons/{lesson.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Lesson'
        assert len(response.data['questions']) == 2
        for q in response.data['questions']:
            assert len(q['choices']) == 3
            assert set(q['choices']) == {'4', '5', '22'} or set(q['choices']) == {
                'Paris',
                'Lyon',
                'Marseille',
            }

    def test_start_lesson(self, lesson, questions):
        response = self.client.post(f'/api/lessons/{lesson.id}/start/', {
            'session_id': 'new-session'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['session_id'] == 'new-session'
        assert response.data['current_question'] is not None
        assert response.data['current_question']['text'] == 'What is 2+2?'
        cq = response.data['current_question']
        assert len(cq['choices']) == 3
        assert set(cq['choices']) == {'4', '5', '22'}

    def test_start_lesson_resume_index(self, lesson, questions, session):
        session.current_question_index = 1
        session.save()
        response = self.client.post(f'/api/lessons/{lesson.id}/start/', {
            'session_id': 'test-session-123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_question']['text'] == 'What is the capital of France?'

    def test_start_after_completed_resets_attempt(self, lesson, questions, session):
        session.is_completed = True
        session.completed_at = timezone.now()
        session.current_question_index = 2
        session.save()
        InteractionRecord.objects.create(
            session_id=session.session_id,
            lesson=lesson,
            question=questions[0],
            user_answer='4',
            is_correct=True,
            ml_service_success=True,
        )
        response = self.client.post(
            f'/api/lessons/{lesson.id}/start/',
            {'session_id': session.session_id},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_question_index'] == 0
        assert response.data['current_question']['id'] == str(questions[0].id)
        session.refresh_from_db()
        assert session.is_completed is False
        assert (
            InteractionRecord.objects.filter(
                session_id=session.session_id, lesson=lesson
            ).count()
            == 0
        )

    def test_complete_lesson_fills_remaining(self, lesson, questions, session):
        response = self.client.post(f'/api/lessons/{lesson.id}/complete/', {
            'session_id': 'test-session-123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['remaining_marked_incorrect'] == 2

    def test_complete_lesson(self, lesson, questions, session):
        response = self.client.post(f'/api/lessons/{lesson.id}/complete/', {
            'session_id': 'test-session-123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True


@pytest.mark.django_db
class TestAnswerAPI:
    def setup_method(self):
        self.client = APIClient()

    @patch('lessons.views.validate_answer_task.delay')
    def test_submit_answer(self, mock_delay, lesson, questions, session):
        response = self.client.post('/api/answer/submit/', {
            'session_id': 'test-session-123',
            'question_id': str(questions[0].id),
            'answer': '4'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'processing'
        mock_delay.assert_called_once()

    def test_submit_answer_missing_session(self, questions):
        response = self.client.post('/api/answer/submit/', {
            'question_id': str(questions[0].id),
            'answer': '4'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('lessons.views.validate_answer_task.delay')
    def test_submit_wrong_question_order(self, _mock, lesson, questions, session):
        response = self.client.post('/api/answer/submit/', {
            'session_id': 'test-session-123',
            'question_id': str(questions[1].id),
            'answer': 'Paris'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestStatisticsAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_get_statistics(self, interaction):
        response = self.client.get('/api/statistics/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_sessions' in response.data
        assert 'success_rate' in response.data
        assert 'ml_successful_validations' in response.data
        assert 'avg_session_duration_sec' in response.data
        assert response.data.get('scope') == 'all'

    def test_statistics_scoped_to_lesson(self, lesson, questions, session):
        lesson2 = Lesson.objects.create(title='L2', text='t2')
        q2 = Question.objects.create(
            lesson=lesson2,
            text='Other Q',
            correct_answer='a',
            distractor_1='b',
            distractor_2='c',
            order=1,
        )
        InteractionRecord.objects.create(
            session_id=session.session_id,
            lesson=lesson,
            question=questions[0],
            user_answer='4',
            is_correct=True,
            ml_service_success=True,
        )
        InteractionRecord.objects.create(
            session_id=session.session_id,
            lesson=lesson2,
            question=q2,
            user_answer='x',
            is_correct=False,
            ml_service_success=True,
        )
        r_all = self.client.get(
            '/api/statistics/',
            {'session_id': session.session_id},
        )
        assert r_all.status_code == status.HTTP_200_OK
        assert r_all.data['total_questions_answered'] == 2
        assert r_all.data['scope'] == 'all'

        r_one = self.client.get(
            '/api/statistics/',
            {'session_id': session.session_id, 'lesson_id': str(lesson.id)},
        )
        assert r_one.status_code == status.HTTP_200_OK
        assert r_one.data['total_questions_answered'] == 1
        assert r_one.data['correct_answers'] == 1
        assert r_one.data['scope'] == 'lesson'
        assert r_one.data['lesson_title'] == lesson.title

    def test_statistics_lesson_without_session_fails(self, lesson):
        r = self.client.get('/api/statistics/', {'lesson_id': str(lesson.id)})
        assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestQuestionCurrentAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_current_requires_lesson_id(self, session):
        response = self.client.get(
            '/api/questions/current/',
            {'session_id': 'test-session-123'},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_current_ok(self, lesson, questions, session):
        response = self.client.get(
            '/api/questions/current/',
            {'session_id': 'test-session-123', 'lesson_id': str(lesson.id)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_question'] is not None
        assert len(response.data['current_question']['choices']) == 3


@pytest.mark.django_db
class TestBackendRoot:
    def test_root_html(self):
        r = Client().get('/')
        assert r.status_code == 200
        assert b'Nastavnik' in r.content
        assert b'localhost:3000' in r.content
        assert b'swagger-ui' in r.content.lower()

    def test_openapi_schema_served(self):
        r = Client().get('/api/schema/')
        assert r.status_code == 200
        assert b'openapi' in r.content.lower()

    def test_root_json(self):
        r = Client().get('/', HTTP_ACCEPT='application/json')
        assert r.status_code == 200
        data = json.loads(r.content)
        assert data['service'] == 'nastavnik-backend'
        assert 'frontend' in data
        assert '/api/schema/swagger-ui/' in data.get('swagger_ui', '')
