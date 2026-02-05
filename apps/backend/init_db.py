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
            source_incident_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (column_id) REFERENCES columns(id),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (source_incident_id) REFERENCES incidents(id)
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

    # ANT HILL: Time logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            started_at TIMESTAMP NOT NULL,
            ended_at TIMESTAMP,
            duration_seconds INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_task ON time_logs(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_user ON time_logs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_active ON time_logs(is_active)")

    # ANT HILL: User points leaderboard
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            period_type TEXT NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            points_earned INTEGER DEFAULT 0,
            tasks_completed INTEGER DEFAULT 0,
            bonus_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, period_type, period_start)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_points_period ON user_points(period_type, period_start)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_points_user ON user_points(user_id)")

    # ANT HILL: Task comments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            is_solution INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_comments_task ON task_comments(task_id)")

    # ANT HILL: Notifications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            notification_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            related_task_id INTEGER,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (related_task_id) REFERENCES tasks(id) ON DELETE SET NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)")

    # Migrations first (add columns before seeding)
    _run_migrations(cursor)

    # Seed data (only if SEED_DATA=true and tables are empty)
    if SEED_DATA:
        _seed_data(cursor)

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

    # ANT HILL: Mock users for development
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        mock_users = [
            ("user_petr", "petr@example.com", "Petr Novák", "https://i.pravatar.cc/150?img=1"),
            ("user_jana", "jana@example.com", "Jana Svobodová", "https://i.pravatar.cc/150?img=5"),
            ("user_martin", "martin@example.com", "Martin Dvořák", "https://i.pravatar.cc/150?img=12"),
        ]
        cursor.executemany(
            "INSERT INTO users (id, email, name, avatar_url) VALUES (?, ?, ?, ?)",
            mock_users,
        )
        logger.info("Created mock users for ANT HILL")

    # ANT HILL: Sample marketplace tasks (check for tasks with estimated_minutes set)
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE estimated_minutes IS NOT NULL")
    if cursor.fetchone()[0] == 0:
        # Get Backlog column id
        cursor.execute("SELECT id FROM columns WHERE name = 'Backlog' LIMIT 1")
        backlog_col = cursor.fetchone()
        if backlog_col:
            marketplace_tasks = [
                ("Fix login bug", "Critical OAuth issue", backlog_col[0], 120, 12, "critical"),
                ("Update documentation", "Add API examples to README", backlog_col[0], 30, 3, "medium"),
                ("Refactor database queries", "Improve performance", backlog_col[0], 180, 18, "high"),
                ("Add unit tests", "Cover auth module", backlog_col[0], 60, 6, "medium"),
                ("Design dashboard mockup", "New analytics view", backlog_col[0], 90, 9, "low"),
            ]
            cursor.executemany(
                """INSERT INTO tasks (title, description, column_id, estimated_minutes, points, priority)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                marketplace_tasks,
            )
            logger.info("Created sample marketplace tasks")


def _run_migrations(cursor) -> None:
    """Run database migrations."""
    # Add google_event_id column if missing
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN google_event_id TEXT")
        logger.info("Migration: Added google_event_id column")
    except sqlite3.OperationalError:
        pass

    # Add source_incident_id column if missing
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN source_incident_id INTEGER REFERENCES incidents(id)")
        logger.info("Migration: Added source_incident_id column")
    except sqlite3.OperationalError:
        pass

    # Add description column to incidents if missing
    try:
        cursor.execute("ALTER TABLE incidents ADD COLUMN description TEXT")
        logger.info("Migration: Added description column to incidents")
    except sqlite3.OperationalError:
        pass

    # Add archived column to tasks if missing
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN archived INTEGER DEFAULT 0")
        logger.info("Migration: Added archived column to tasks")
    except sqlite3.OperationalError:
        pass

    # ANT HILL migrations - Task assignment and gamification
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN assigned_to TEXT")
        logger.info("Migration: Added assigned_to column to tasks")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN assigned_at TIMESTAMP")
        logger.info("Migration: Added assigned_at column to tasks")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN estimated_minutes INTEGER")
        logger.info("Migration: Added estimated_minutes column to tasks")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN points INTEGER")
        logger.info("Migration: Added points column to tasks")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN time_spent_seconds INTEGER DEFAULT 0")
        logger.info("Migration: Added time_spent_seconds column to tasks")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")
        logger.info("Migration: Added completed_at column to tasks")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN claimed_from_marketplace INTEGER DEFAULT 0")
        logger.info("Migration: Added claimed_from_marketplace column to tasks")
    except sqlite3.OperationalError:
        pass

    # Create indexes for tasks
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_marketplace ON tasks(assigned_to, column_id)")
        logger.info("Migration: Created indexes for tasks")
    except sqlite3.OperationalError:
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()

