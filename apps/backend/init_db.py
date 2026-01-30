"""Initialize the SQLite database with tables for Flowable MVP."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "starter.db"


def init_database() -> None:
    """Create tables and insert mock data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create columns table (Kanban boards)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            position INTEGER NOT NULL,
            color TEXT DEFAULT '#3b82f6',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create tasks table with Kanban support
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed INTEGER DEFAULT 0,
            column_id INTEGER,
            position INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'medium',
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (column_id) REFERENCES columns(id)
        )
    """)

    # Create audit_log table for disaster recovery
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create monitors table for health checks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            check_interval INTEGER DEFAULT 60,
            last_status TEXT DEFAULT 'unknown',
            last_check TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create incidents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_id INTEGER,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            severity TEXT DEFAULT 'warning',
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            acknowledged_at TEXT,
            resolved_at TEXT,
            FOREIGN KEY (monitor_id) REFERENCES monitors(id)
        )
    """)

    # Create metrics table for response times
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_id INTEGER NOT NULL,
            response_time_ms INTEGER,
            status_code INTEGER,
            is_up INTEGER DEFAULT 1,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (monitor_id) REFERENCES monitors(id)
        )
    """)

    # Initialize default Kanban columns if not exist
    cursor.execute("SELECT COUNT(*) FROM columns")
    if cursor.fetchone()[0] == 0:
        default_columns = [
            (1, "Backlog", 0, "#6b7280"),
            (1, "To Do", 1, "#3b82f6"),
            (1, "In Progress", 2, "#f59e0b"),
            (1, "Done", 3, "#10b981"),
        ]
        cursor.executemany(
            "INSERT INTO columns (board_id, name, position, color) VALUES (?, ?, ?, ?)",
            default_columns,
        )
        print(f"Inserted {len(default_columns)} default columns")

    # Check if we already have tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        # Get column IDs
        cursor.execute("SELECT id FROM columns WHERE name = 'To Do'")
        todo_col = cursor.fetchone()
        cursor.execute("SELECT id FROM columns WHERE name = 'In Progress'")
        progress_col = cursor.fetchone()
        cursor.execute("SELECT id FROM columns WHERE name = 'Done'")
        done_col = cursor.fetchone()

        todo_id = todo_col[0] if todo_col else None
        progress_id = progress_col[0] if progress_col else None
        done_id = done_col[0] if done_col else None

        # Insert mock data with column assignments
        mock_tasks = [
            ("Setup Python backend", "Configure FastAPI with SQLite", 1, done_id, 0, "high"),
            ("Create Vue frontend", "Scaffold Vite Vue-TS project", 1, done_id, 1, "high"),
            ("Implement CRUD API", "Add endpoints for tasks", 0, progress_id, 0, "medium"),
            ("Connect frontend to backend", "Use fetch to call API", 0, todo_id, 0, "medium"),
            ("Add monitoring dashboard", "Track uptime and incidents", 0, todo_id, 1, "low"),
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, description, completed, column_id, position, priority) VALUES (?, ?, ?, ?, ?, ?)",
            mock_tasks,
        )
        print(f"Inserted {len(mock_tasks)} mock tasks")

    # Check if we have monitors
    cursor.execute("SELECT COUNT(*) FROM monitors")
    if cursor.fetchone()[0] == 0:
        # Insert demo monitors
        demo_monitors = [
            ("Flowable API", "http://localhost:8000/", 30),
            ("Google", "https://www.google.com", 60),
            ("GitHub", "https://github.com", 60),
        ]
        cursor.executemany(
            "INSERT INTO monitors (name, url, check_interval) VALUES (?, ?, ?)",
            demo_monitors,
        )
        print(f"Inserted {len(demo_monitors)} demo monitors")

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_database()
