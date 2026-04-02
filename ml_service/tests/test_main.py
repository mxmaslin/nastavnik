import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


@patch('main.random.random', return_value=0.99)
@patch('main.check_answer_cached')
@patch('main.check_answer_db', new_callable=AsyncMock)
def test_validate_correct_answer(mock_db_check, mock_cached_check, _mock_random):
    mock_cached_check.return_value = True

    response = client.post('/validate', json={
        'question_id': 'test-id',
        'user_answer': 'correct'
    })

    assert response.status_code == 200
    assert response.json()['result'] == 1


@patch('main.random.random', return_value=0.99)
@patch('main.check_answer_cached')
@patch('main.check_answer_db', new_callable=AsyncMock)
def test_validate_incorrect_answer(mock_db_check, mock_cached_check, _mock_random):
    mock_cached_check.return_value = False

    response = client.post('/validate', json={
        'question_id': 'test-id',
        'user_answer': 'wrong'
    })

    assert response.status_code == 200
    assert response.json()['result'] == 0


@patch('main.random.random')
@patch('main.check_answer_cached')
def test_validate_service_unavailable(mock_cached_check, mock_random):
    mock_random.return_value = 0.1
    mock_cached_check.return_value = True

    response = client.post('/validate', json={
        'question_id': 'test-id',
        'user_answer': 'answer'
    })

    assert response.status_code == 503


@patch('main.random.random', return_value=0.99)
@patch('main.check_answer_cached')
@patch('main.check_answer_db', new_callable=AsyncMock)
def test_validate_cache_miss_db_fallback(mock_db_check, mock_cached_check, _mock_random):
    mock_cached_check.return_value = None
    mock_db_check.return_value = True

    response = client.post('/validate', json={
        'question_id': 'test-id',
        'user_answer': 'answer'
    })

    assert response.status_code == 200
    assert response.json()['result'] == 1
    mock_db_check.assert_awaited_once()
