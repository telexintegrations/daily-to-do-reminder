
import pytest, os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
import main as reminder_app

client = TestClient(app)

# Use a temporary SQLite database file for testing
TEST_DB_FILE = "test_reminders.db"
reminder_app.DB_FILE = TEST_DB_FILE

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    reminder_app.init_db()
    yield
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

@pytest.fixture
def mock_httpx():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None
        yield mock_post

def test_add_task():
    response = client.post("/add-task", json={"task": "Test Task", "time": "10:00"})
    assert response.status_code == 200
    assert response.json() == {"message": "Task added successfully!"}

def test_list_tasks_empty():
    response = client.get("/list-tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert data["tasks"] == []

def test_add_and_list_tasks():
    client.post("/add-task", json={"task": "Test Task", "time": "10:00"})
    response = client.get("/list-tasks")
    data = response.json()
    assert len(data["tasks"]) == 1
    assert "10:00 - Test Task" in data["tasks"][0]

def test_tick_endpoint(mock_httpx):
    client.post("/add-task", json={"task": "Test Task", "time": "10:00"})
    response = client.post("/tick", json={"return_url": "http://example.com/webhook"})
    assert response.status_code == 200
    assert response.json()["status"] == "Reminder sent successfully"
    # After tick, tasks for today should be cleared
    response = client.get("/list-tasks")
    assert response.json()["tasks"] == []

def test_integration_json():
    response = client.get("/integration-json")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "tick_url" in data["data"]