import pytest
from unittest.mock import AsyncMock, Mock
from api.main import app
from api.database import pool

@pytest.fixture
def mock_db_pool(mocker):
    pool_mock = AsyncMock()
    mocker.patch('api.database.pool', pool_mock)
    mocker.patch('api.routes.scan.get_db_connection', return_value=AsyncMock())
    return pool_mock

@pytest.fixture
def mock_celery(mocker):
    celery_mock = mocker.patch('api.workers.celery_app.celery_app.send_task')
    return celery_mock
