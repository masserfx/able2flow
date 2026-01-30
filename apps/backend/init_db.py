"""Initialize the SQLite database with tables for Able2Flow MVP."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "starter.db"


def init_database() -> None:
    """Create tables and insert mock data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table (for Clerk integration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT,
            name TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create OAuth tokens table (encrypted)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_oauth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            scopes TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, provider)
        )
    """)

    # Create integration settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            project_id INTEGER,
            integration_type TEXT NOT NULL,
            settings TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    # Create linked documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS linked_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            external_id TEXT NOT NULL,
            title TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    # Create projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#7aa2f7',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create columns table (Kanban boards)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER DEFAULT 1,
            project_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            position INTEGER NOT NULL,
            color TEXT DEFAULT '#3b82f6',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
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
            project_id INTEGER DEFAULT 1,
            google_event_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (column_id) REFERENCES columns(id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
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
            project_id INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
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
            project_id INTEGER DEFAULT 1,
            FOREIGN KEY (monitor_id) REFERENCES monitors(id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
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

    # Create attachments table for task files
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """)

    # Initialize default projects if not exist
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        demo_projects = [
            ("Able2Flow", "Default project with existing data", "#7aa2f7"),
            ("Marketing Web", "Marketing website project", "#bb9af7"),
        ]
        cursor.executemany(
            "INSERT INTO projects (name, description, color) VALUES (?, ?, ?)",
            demo_projects,
        )
        print(f"Inserted {len(demo_projects)} demo projects")

    # Initialize default Kanban columns if not exist
    cursor.execute("SELECT COUNT(*) FROM columns")
    if cursor.fetchone()[0] == 0:
        # Columns for project 1 (Able2Flow)
        default_columns = [
            (1, 1, "Backlog", 0, "#6b7280"),
            (1, 1, "To Do", 1, "#3b82f6"),
            (1, 1, "In Progress", 2, "#f59e0b"),
            (1, 1, "Done", 3, "#10b981"),
        ]
        # Columns for project 2 (Marketing Web)
        project2_columns = [
            (1, 2, "Backlog", 0, "#6b7280"),
            (1, 2, "To Do", 1, "#3b82f6"),
            (1, 2, "In Progress", 2, "#f59e0b"),
            (1, 2, "Done", 3, "#10b981"),
        ]
        all_columns = default_columns + project2_columns
        cursor.executemany(
            "INSERT INTO columns (board_id, project_id, name, position, color) VALUES (?, ?, ?, ?, ?)",
            all_columns,
        )
        print(f"Inserted {len(all_columns)} default columns for both projects")

    # Check if we already have tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        # Get column IDs for project 1 (Able2Flow)
        cursor.execute("SELECT id FROM columns WHERE name = 'To Do' AND project_id = 1")
        todo_col = cursor.fetchone()
        cursor.execute("SELECT id FROM columns WHERE name = 'In Progress' AND project_id = 1")
        progress_col = cursor.fetchone()
        cursor.execute("SELECT id FROM columns WHERE name = 'Done' AND project_id = 1")
        done_col = cursor.fetchone()

        todo_id = todo_col[0] if todo_col else None
        progress_id = progress_col[0] if progress_col else None
        done_id = done_col[0] if done_col else None

        # Insert mock data with column assignments (all for project 1)
        mock_tasks = [
            ("Setup Python backend", "Configure FastAPI with SQLite", 1, done_id, 0, "high", 1),
            ("Create Vue frontend", "Scaffold Vite Vue-TS project", 1, done_id, 1, "high", 1),
            ("Implement CRUD API", "Add endpoints for tasks", 0, progress_id, 0, "medium", 1),
            ("Connect frontend to backend", "Use fetch to call API", 0, todo_id, 0, "medium", 1),
            ("Add monitoring dashboard", "Track uptime and incidents", 0, todo_id, 1, "low", 1),
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, description, completed, column_id, position, priority, project_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            mock_tasks,
        )
        print(f"Inserted {len(mock_tasks)} mock tasks")

    # Check if we have monitors
    cursor.execute("SELECT COUNT(*) FROM monitors")
    if cursor.fetchone()[0] == 0:
        # Insert demo monitors (all for project 1)
        demo_monitors = [
            ("Able2Flow API", "http://localhost:8000/", 30, 1),
            ("Google", "https://www.google.com", 60, 1),
            ("GitHub", "https://github.com", 60, 1),
        ]
        cursor.executemany(
            "INSERT INTO monitors (name, url, check_interval, project_id) VALUES (?, ?, ?, ?)",
            demo_monitors,
        )
        print(f"Inserted {len(demo_monitors)} demo monitors")

    # Migration: Add google_event_id column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN google_event_id TEXT")
        print("Added google_event_id column to tasks table")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_database()
