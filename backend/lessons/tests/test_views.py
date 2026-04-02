from unittest.mock import patch

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from lessons.models import Lesson, Question, LessonSession


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

    def test_start_lesson(self, lesson, questions):
        response = self.client.post(f'/api/lessons/{lesson.id}/start/', {
            'session_id': 'new-session'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['session_id'] == 'new-session'
        assert response.data['current_question'] is not None
        assert response.data['current_question']['text'] == 'What is 2+2?'

    def test_start_lesson_resume_index(self, lesson, questions, session):
        session.current_question_index = 1
        session.save()
        response = self.client.post(f'/api/lessons/{lesson.id}/start/', {
            'session_id': 'test-session-123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_question']['text'] == 'What is the capital of France?'

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
