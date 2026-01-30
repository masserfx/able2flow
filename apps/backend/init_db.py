"""Initialize the SQLite database with tables for Able2Flow."""

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "starter.db"
SEED_DATA = os.getenv("SEED_DATA", "true").lower() == "true"


def init_database() -> None:
    """Create database tables. Optionally insert seed data if SEED_DATA=true."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table (Clerk integration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT,
            name TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # OAuth tokens table
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

    # Integration settings table
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

    # Linked documents table
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

    # Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#7aa2f7',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Columns table (Kanban boards)
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

    # Tasks table
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

    # Audit log table
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

    # Monitors table
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

    # Incidents table
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

    # Metrics table
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

    # Attachments table
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

    # Seed data (only if SEED_DATA=true and tables are empty)
    if SEED_DATA:
        _seed_data(cursor)

    # Migrations
    _run_migrations(cursor)

    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)


def _seed_data(cursor) -> None:
    """Insert seed data for development/demo."""
    # Default project
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO projects (name, description, color) VALUES (?, ?, ?)",
            ("My Project", "Default project", "#7aa2f7"),
        )
        logger.info("Created default project")

    # Default columns
    cursor.execute("SELECT COUNT(*) FROM columns")
    if cursor.fetchone()[0] == 0:
        default_columns = [
            (1, 1, "Backlog", 0, "#6b7280"),
            (1, 1, "To Do", 1, "#3b82f6"),
            (1, 1, "In Progress", 2, "#f59e0b"),
            (1, 1, "Done", 3, "#10b981"),
        ]
        cursor.executemany(
            "INSERT INTO columns (board_id, project_id, name, position, color) VALUES (?, ?, ?, ?, ?)",
            default_columns,
        )
        logger.info("Created default columns")


def _run_migrations(cursor) -> None:
    """Run database migrations."""
    # Add google_event_id column if missing
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN google_event_id TEXT")
        logger.info("Migration: Added google_event_id column")
    except sqlite3.OperationalError:
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
