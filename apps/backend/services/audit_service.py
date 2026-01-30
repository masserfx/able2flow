"""Audit service for tracking all entity changes."""

import json
import sqlite3
from datetime import datetime
from typing import Any

from database import get_db


def log_action(
    entity_type: str,
    entity_id: int,
    action: str,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
) -> int:
    """Log an action to the audit log.

    Args:
        entity_type: Type of entity (task, column, monitor, incident)
        entity_id: ID of the entity
        action: Action performed (create, update, delete, move)
        old_value: Previous state of the entity (for updates/deletes)
        new_value: New state of the entity (for creates/updates)

    Returns:
        ID of the created audit log entry
    """
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO audit_log (entity_type, entity_id, action, old_value, new_value, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entity_type,
                entity_id,
                action,
                json.dumps(old_value) if old_value else None,
                json.dumps(new_value) if new_value else None,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_audit_logs(
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Get audit logs with optional filtering.

    Args:
        entity_type: Filter by entity type
        entity_id: Filter by entity ID
        limit: Maximum number of records to return
        offset: Number of records to skip

    Returns:
        List of audit log entries
    """
    with get_db() as conn:
        query = "SELECT * FROM audit_log WHERE 1=1"
        params: list[Any] = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "action": row["action"],
                "old_value": json.loads(row["old_value"]) if row["old_value"] else None,
                "new_value": json.loads(row["new_value"]) if row["new_value"] else None,
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]


def get_audit_stats() -> dict[str, Any]:
    """Get audit log statistics."""
    with get_db() as conn:
        # Total actions
        cursor = conn.execute("SELECT COUNT(*) as total FROM audit_log")
        total = cursor.fetchone()["total"]

        # Actions by type
        cursor = conn.execute(
            """
            SELECT action, COUNT(*) as count
            FROM audit_log
            GROUP BY action
            """
        )
        by_action = {row["action"]: row["count"] for row in cursor.fetchall()}

        # Actions by entity
        cursor = conn.execute(
            """
            SELECT entity_type, COUNT(*) as count
            FROM audit_log
            GROUP BY entity_type
            """
        )
        by_entity = {row["entity_type"]: row["count"] for row in cursor.fetchall()}

        # Recent activity (last 24h)
        cursor = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM audit_log
            WHERE timestamp > datetime('now', '-24 hours')
            """
        )
        recent = cursor.fetchone()["count"]

        return {
            "total_actions": total,
            "by_action": by_action,
            "by_entity": by_entity,
            "recent_24h": recent,
        }
