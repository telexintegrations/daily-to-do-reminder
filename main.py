from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx, os, sqlite3  # Import required modules   

# Load environment variables from .env file
load_dotenv()


app = FastAPI()

# Configure CORS    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# Load environment variables    
TELEX_CHANNEL_WEBHOOK = os.getenv("TELEX_CHANNEL_WEBHOOK")
DEFAULT_REMINDER_TIME = os.getenv("DEFAULT_REMINDER_TIME")  # Default reminder time

# Initialize SQLite Database
DB_FILE = "reminders.db"

def init_db():
    """Creates the reminders table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            task TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()  # Ensure DB is initialized

def get_reminders():
    """Fetches stored reminders from SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT date, time, task FROM reminders")
    reminders = {}
    for date, time, task in cursor.fetchall():
        reminders.setdefault(date, []).append(f"{time} - {task}")
    conn.close()
    return reminders

def save_reminder(date, time, task):
    """Saves a new reminder to SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (date, time, task) VALUES (?, ?, ?)", (date, time, task))
    conn.commit()
    conn.close()

def delete_today_reminders(date):
    """Deletes reminders for a specific date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE date = ?", (date,))
    conn.commit()
    conn.close()

@app.post("/tick")
async def tick(request: Request):
    """Triggered by Telex at a scheduled interval to send daily reminders."""
    data = await request.json()
    return_url = data.get("return_url", TELEX_CHANNEL_WEBHOOK)

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    reminders = get_reminders()
    tasks = reminders.get(today, ["No pending tasks!"])

    # Format tasks into a message
    message = "\n".join([f"- {task}" for task in tasks])
    payload = {"message": f"\U0001F4DD Daily To-Do List:\n{message}"}

    # Send reminder message asynchronously to the Telex channel
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(return_url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"Failed to send reminder: {e.response.status_code}"}
        except httpx.RequestError:
            return {"status": "error", "detail": "Failed to reach Telex server"}

    # Clear tasks after sending the reminder
    delete_today_reminders(today)

    return {"status": "Reminder sent successfully"}

@app.post("/add-task")
async def add_task(request: Request):
    """
    Adds a new task to the reminder list.
    """
    data = await request.json()
    task = data.get("task")
    time = data.get("time", DEFAULT_REMINDER_TIME)  # Use default time if no time provided

    if not task:
        return {"error": "Task cannot be empty"}

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    save_reminder(today, time, task)

    return {"message": "Task added successfully!"}

@app.get("/list-tasks")
async def list_tasks():
    """
    Lists all tasks scheduled for today.
    """
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    reminders = get_reminders()
    tasks = reminders.get(today, [])
    return {"tasks": tasks}

@app.get("/integration-json")
async def get_integration_json(request: Request):
   
   # Get the base URL
    base_url = str(request.base_url).rstrip("/") # Remove trailing slash
    """
    Returns the JSON payload for the integration.
    """
    integration_json = {
        "data": {
            "date": {
                "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                "updated_at": datetime.now(timezone.utc).strftime('%Y-%m-%d')
            },
            "descriptions": {
                "app_description": "A simple to-do reminder that sends tasks daily at custom times.",
                "app_logo": "https://res.cloudinary.com/dcnnysxm9/image/upload/v1739862586/to-do_reminder_xdzgb2.webp",
                "app_name": "Daily To-Do Reminder",
                "app_url": base_url,
                "background_color": "#00fbff"
            },
            "integration_category": "Project Management",
            "integration_type": "interval",
            "is_active": True,
            "key_features": [
                "Sends daily reminders",
                "Allows adding tasks dynamically",
                "Clears tasks after sending reminders",
                "Allows setting custom reminder times",
                "Lists tasks scheduled for the day"
            ],
            "author": "Onyishi James",
            "website": base_url, 
            "settings": [
                {
                    "label": "interval",
                    "type": "text",
                    "required": True,
                    "default": "0 9 * * *"  # Default set to every day at 9 AM in your timezone.
                }
            ],
            "endpoints": [
      {
        "path": "/add-task",
        "method": "POST",
        "description": "adds a new task and time to the reminder list",
      },
      {
        "path": "/list-tasks",
        "method": "GET",
        "description": "lists all task scheduled for that day",
      }
      ],
        "target_url": "",
        "tick_url": f"{base_url}/tick"
        }
    }
    return integration_json