import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP


# ==================================================
# LifePilot-AI
# Amazon Developer Hackathon - Alexa+ Track
# MCP Server using Streamable HTTP
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "lifepilot.db"

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

GEMINI_MODEL = "gemini-3.8-flash"

mcp = FastMCP(
    "LifePilot-AI",
    host=HOST,
    port=PORT,
    json_response=True,
)


# ==================================================
# GEMINI AI CONFIGURATION
# ==================================================

# Load environment variables from the local .env file, if it exists.
# Existing environment variables (for example, those set in PowerShell)
# are preserved by default.
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)


# ==================================================
# DATABASE
# ==================================================

def initialize_database():
    """Create the tasks table if it does not already exist."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
            """
        )


# ==================================================
# ADD TASK
# ==================================================

@mcp.tool()
def add_task(
    title: str,
    description: str = "",
    due_date: str = ""
) -> dict:
    """
    Create a personal productivity task.

    Args:
        title: Task title.
        description: Additional task details.
        due_date: Optional due date in YYYY-MM-DD format.
    """

    title = title.strip()

    if not title:
        return {
            "success": False,
            "message": "Task title cannot be empty."
        }

    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "message": "Use YYYY-MM-DD for the due date."
            }

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO tasks (
                title,
                description,
                due_date,
                status,
                created_at
            )
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (
                title,
                description.strip(),
                due_date,
                datetime.now().isoformat(timespec="seconds")
            )
        )

        task_id = cursor.lastrowid

    return {
        "success": True,
        "task_id": task_id,
        "title": title,
        "message": "Task added successfully."
    }


# ==================================================
# LIST TASKS
# ==================================================

@mcp.tool()
def list_tasks(status: str = "all") -> dict:
    """
    Retrieve personal productivity tasks.

    Args:
        status: all, pending, or completed.
    """

    status = status.strip().lower()

    if status not in {"all", "pending", "completed"}:
        return {
            "success": False,
            "message": "Status must be all, pending, or completed."
        }

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        if status == "all":
            rows = connection.execute(
                "SELECT * FROM tasks ORDER BY id DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY id DESC
                """,
                (status,)
            ).fetchall()

    return {
        "success": True,
        "count": len(rows),
        "tasks": [dict(row) for row in rows]
    }


# ==================================================
# COMPLETE TASK
# ==================================================

@mcp.tool()
def complete_task(task_id: int) -> dict:
    """
    Mark a task as completed.

    Args:
        task_id: ID of the task.
    """

    if task_id <= 0:
        return {
            "success": False,
            "message": "Task ID must be positive."
        }

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE tasks
            SET status = 'completed'
            WHERE id = ?
            """,
            (task_id,)
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": f"Task {task_id} was not found."
            }

    return {
        "success": True,
        "task_id": task_id,
        "message": "Task completed successfully."
    }


# ==================================================
# DELETE TASK
# ==================================================

@mcp.tool()
def delete_task(task_id: int) -> dict:
    """
    Delete a selected task.

    Args:
        task_id: ID of the task to delete.
    """

    if task_id <= 0:
        return {
            "success": False,
            "message": "Task ID must be positive."
        }

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": f"Task {task_id} was not found."
            }

    return {
        "success": True,
        "task_id": task_id,
        "message": "Task deleted successfully."
    }


# ==================================================
# STUDY TIME PLANNER
# ==================================================

@mcp.tool()
def calculate_study_time(
    total_minutes: int,
    subjects: list[str]
) -> dict:
    """
    Divide study time equally between subjects.

    Args:
        total_minutes: Total available study time.
        subjects: Names of subjects to study.
    """

    if total_minutes <= 0:
        return {
            "success": False,
            "message": "Study time must be positive."
        }

    clean_subjects = [
        subject.strip()
        for subject in subjects
        if subject.strip()
    ]

    if not clean_subjects:
        return {
            "success": False,
            "message": "Provide at least one subject."
        }

    minutes_per_subject, remaining_minutes = divmod(
        total_minutes,
        len(clean_subjects)
    )

    schedule = [
        {
            "subject": subject,
            "minutes": minutes_per_subject
        }
        for subject in clean_subjects
    ]

    return {
        "success": True,
        "total_minutes": total_minutes,
        "schedule": schedule,
        "remaining_minutes": remaining_minutes,
        "message": (
            f"Allocated {minutes_per_subject} minutes per subject. "
            f"{remaining_minutes} minute(s) remain."
        )
    }


# ==================================================
# GEMINI AI ASSISTANT
# ==================================================

@mcp.tool()
def ask_lifepilot_ai(question: str) -> dict:
    """
    Ask Gemini AI for productivity, planning, study, and general assistance.

    Args:
        question: The question or request for the AI assistant.
    """

    if not question or not question.strip():
        return {
            "success": False,
            "message": "Please enter a question."
        }

    if gemini_client is None:
        return {
            "success": False,
            "message": (
                "Gemini API key is missing. Set the GEMINI_API_KEY "
                "environment variable and restart the server."
            )
        }

    try:
        start_time = time.perf_counter()
        print("LifePilot-AI: Sending request to Gemini...")

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                "You are LifePilot-AI, a fast, accurate study and productivity assistant. "
                "Answer the exact question directly. For simple questions, use a short "
                "answer with one example when useful. For programming questions, provide "
                "correct runnable code when requested and explain it briefly. For study plans, "
                "use clear day-by-day steps. Avoid unnecessary introductions and repetition.\n\n"
                f"User request: {question.strip()}"
            ),
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=512,
            ),
        )

        elapsed = time.perf_counter() - start_time
        print(f"LifePilot-AI: Gemini response received in {elapsed:.2f} seconds.")

        answer = response.text

        if not answer:
            return {
                "success": False,
                "message": "Gemini returned an empty response."
            }

        return {
            "success": True,
            "assistant": "LifePilot-AI",
            "model": GEMINI_MODEL,
            "answer": answer
        }

    except Exception as error:
        elapsed = time.perf_counter() - start_time
        print(f"LifePilot-AI: Gemini request failed after {elapsed:.2f} seconds.")
        print(f"Gemini request failed: {type(error).__name__}: {error}")

        return {
            "success": False,
            "message": (
                "The AI request failed. Check the server terminal "
                "for the error details."
            ),
            "error_type": type(error).__name__
        }


# ==================================================
# SERVER STARTUP
# ==================================================

if __name__ == "__main__":
    initialize_database()

    print("=" * 50)
    print("LifePilot-AI MCP server is starting...")
    print(f"Database: {DATABASE_PATH}")
    print("Transport: Streamable HTTP")
    print(f"Local endpoint: http://{HOST}:{PORT}/mcp")
    print(f"Gemini model: {GEMINI_MODEL}")
    print(f"Gemini API key configured: {bool(GEMINI_API_KEY)}")
    print("Available tools: 6")
    print("=" * 50)

    mcp.run(transport="streamable-http")