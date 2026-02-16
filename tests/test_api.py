from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch, MagicMock
from uuid import uuid4

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health():
    # Health check is just root for now or we add a simple one
    response = client.get("/")
    assert response.status_code == 200

@patch("api.routes.scan.get_db_connection")
@patch("api.routes.scan.celery_app.send_task")
def test_create_scan_job_success(mock_send_task, mock_get_db_connection):
    # Mock database connection and response
    mock_conn = MagicMock()
    
    # Mock the async context manager
    mock_get_db_connection.return_value.__aenter__.return_value = mock_conn
    
    # Mock row returned from INSERT
    mock_job_id = uuid4()
    
    # Use AsyncMock for async methods
    from unittest.mock import AsyncMock
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": mock_job_id,
        "query": "dropshipping",
        "country": "CO",
        "max_count": 10,
        "status": "pending",
        "ads_found": 0,
        "error": None,
        "created_at": "2026-02-16T00:00:00",
        "completed_at": None
    })
    
    response = client.post(
        "/api/v1/scan",
        json={"query": "dropshipping", "country": "CO", "max_count": 10}
    )
    
    assert response.status_code == 201
    assert response.json()["query"] == "dropshipping"
    assert response.json()["status"] == "pending"
    
    # Verify Celery task was dispatched
    mock_send_task.assert_called_once()
    args, kwargs = mock_send_task.call_args
    assert args[0] == "api.workers.harvester.run_search"
