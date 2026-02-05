"""ANT HILL Database Migration Script"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "starter.db"

def run_migration():
    """Run ANT HILL migrations"""
    print(f"Running migrations on {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
    print("✓ Created time_logs table")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_task ON time_logs(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_user ON time_logs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_active ON time_logs(is_active)")
    print("✓ Created time_logs indexes")

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
    print("✓ Created user_points table")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_points_period ON user_points(period_type, period_start)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_points_user ON user_points(user_id)")
    print("✓ Created user_points indexes")

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
    print("✓ Created task_comments table")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_comments_task ON task_comments(task_id)")
    print("✓ Created task_comments indexes")

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
    print("✓ Created notifications table")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)")
    print("✓ Created notifications indexes")

    # ANT HILL: Alter tasks table
    columns_to_add = [
        ("assigned_to", "TEXT"),
        ("assigned_at", "TIMESTAMP"),
        ("estimated_minutes", "INTEGER"),
        ("points", "INTEGER"),
        ("time_spent_seconds", "INTEGER DEFAULT 0"),
        ("completed_at", "TIMESTAMP"),
        ("claimed_from_marketplace", "INTEGER DEFAULT 0"),
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added {col_name} column to tasks")
        except sqlite3.OperationalError:
            print(f"  (column {col_name} already exists)")

    # Create indexes for tasks
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_marketplace ON tasks(assigned_to, column_id)")
    print("✓ Created tasks indexes")

    # Insert mock users if not exist
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
        print("✓ Created mock users")

    # Insert sample marketplace tasks if needed
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to IS NULL AND estimated_minutes IS NOT NULL")
    if cursor.fetchone()[0] == 0:
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
            print("✓ Created sample marketplace tasks")

    conn.commit()
    conn.close()
    print("\n✅ ANT HILL migration completed successfully!")

if __name__ == "__main__":
    run_migration()
