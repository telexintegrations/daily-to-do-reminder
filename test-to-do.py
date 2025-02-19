import os
import sqlite3
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import main

# Override the DB file for testing
TEST_DB_FILE = "test_reminders.db"
main.DB_FILE = TEST_DB_FILE

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    main.init_db()
    yield
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

def insert_task(date, time, task):
    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (date, time, task) VALUES (?, ?, ?)", (date, time, task))
    conn.commit()
    conn.close()

def get_all_tasks(date):
    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT time, task FROM reminders WHERE date = ?", (date,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Daily To-Do Reminder" in response.text

def test_add_task_success():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime('%H:%M')
    response = client.post("/add-task", json={"task": "Test Task", "time": future_time, "date": today})
    assert response.status_code == 200
    assert response.json() == {"message": "Task added successfully!"}

def test_add_task_error_empty():
    response = client.post("/add-task", json={"task": "", "time": "10:00"})
    data = response.json()
    assert "error" in data

def test_add_task_error_past_date_time():
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    past_time = "00:00"
    response = client.post("/add-task", json={"task": "Past Task", "time": past_time, "date": past_date})
    assert response.status_code == 400

def test_list_tasks():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime('%H:%M')
    client.post("/add-task", json={"task": "List Task", "time": future_time, "date": today})
    response = client.get("/list-tasks")
    data = response.json()
    assert "tasks" in data
    assert any("List Task" in task for task in data["tasks"])

@pytest.mark.asyncio
async def test_tick_endpoint():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime('%H:%M')
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime('%H:%M')
    insert_task(today, past_time, "Expired Task")
    insert_task(today, future_time, "Future Task")
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None
        response = client.post("/tick", json={"return_url": "http://example.com/webhook"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Reminder sent successfully"
    
    tasks = get_all_tasks(today)
    for t, task in tasks:
        assert "Expired Task" not in task
    assert any("Future Task" in task for t, task in tasks)

def test_integration_json():
    response = client.get("/integration-json")
    data = response.json()
    assert "data" in data
    assert "tick_url" in data["data"]
