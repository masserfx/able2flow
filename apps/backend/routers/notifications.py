"""Notifications API for ANT HILL - FOMO system."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """Notification response."""

    id: int
    notification_type: str
    title: str
    message: str
    related_task_id: int | None
    is_read: bool
    created_at: str


class NotificationCreate(BaseModel):
    """Create broadcast notification."""

    title: str
    message: str
    notification_type: str = "announcement"


@router.get("/me", response_model=list[NotificationResponse])
async def get_my_notifications(user_id: str | None = None, unread_only: bool = False, limit: int = 50):
    """Get notifications for current user."""
    with get_db() as conn:
        conditions = []
        params = []

        # User-specific or broadcast (user_id IS NULL)
        if user_id:
            conditions.append("(notifications.user_id = ? OR notifications.user_id IS NULL)")
            params.append(user_id)

        if unread_only:
            conditions.append("notifications.is_read = 0")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        rows = conn.execute(
            f"""SELECT id, notification_type, title, message, related_task_id, is_read, created_at
               FROM notifications
               WHERE {where_clause}
               ORDER BY created_at DESC
               LIMIT ?""",
            params + [limit],
        ).fetchall()

        return [
            {
                "id": row["id"],
                "notification_type": row["notification_type"],
                "title": row["title"],
                "message": row["message"],
                "related_task_id": row["related_task_id"],
                "is_read": bool(row["is_read"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


@router.get("/poll", response_model=list[NotificationResponse])
async def poll_notifications(since: str, user_id: str | None = None):
    """Poll for new notifications since timestamp (for FOMO effect)."""
    with get_db() as conn:
        conditions = ["notifications.created_at > ?"]
        params = [since]

        if user_id:
            conditions.append("(notifications.user_id = ? OR notifications.user_id IS NULL)")
            params.append(user_id)

        where_clause = " AND ".join(conditions)

        rows = conn.execute(
            f"""SELECT id, notification_type, title, message, related_task_id, is_read, created_at
               FROM notifications
               WHERE {where_clause}
               ORDER BY created_at DESC
               LIMIT 20""",
            params,
        ).fetchall()

        return [
            {
                "id": row["id"],
                "notification_type": row["notification_type"],
                "title": row["title"],
                "message": row["message"],
                "related_task_id": row["related_task_id"],
                "is_read": bool(row["is_read"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


@router.put("/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark notification as read."""
    with get_db() as conn:
        result = conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,),
        )
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"message": "Notification marked as read"}


@router.post("/broadcast")
async def create_broadcast_notification(notification: NotificationCreate):
    """Create a broadcast notification (visible to all users)."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO notifications (user_id, notification_type, title, message)
               VALUES (NULL, ?, ?, ?)""",
            (notification.notification_type, notification.title, notification.message),
        )
        notification_id = cursor.lastrowid
        conn.commit()

        return {
            "id": notification_id,
            "message": "Broadcast notification created",
        }


@router.delete("/{notification_id}")
async def delete_notification(notification_id: int):
    """Delete a notification."""
    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM notifications WHERE id = ?",
            (notification_id,),
        )
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {"message": "Notification deleted"}


@router.get("/unread-count")
async def get_unread_count(user_id: str | None = None):
    """Get count of unread notifications."""
    with get_db() as conn:
        if user_id:
            row = conn.execute(
                """SELECT COUNT(*) as count
                   FROM notifications
                   WHERE (user_id = ? OR user_id IS NULL) AND is_read = 0""",
                (user_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM notifications WHERE is_read = 0"
            ).fetchone()

        return {"unread_count": row["count"] if row else 0}


@router.post("/test/create-sample")
async def create_sample_notification():
    """Create a sample notification for testing (DEV ONLY)."""
    import random

    samples = [
        ("task_claimed", "🎯 Jana si vzala task!", "Task 'Fix login bug' byl přiřazen", None),
        ("points_awarded", "💎 Petr získal 15 bodů!", "Dokončil task: Implement feature X", None),
        ("leaderboard", "🏆 Nový týdenní leader!", "Martin vede s 150 body!", None),
        ("announcement", "📢 Nový task v marketplace!", "Task za 8 bodů čeká na řešení", None),
        ("task_completed", "✅ Task dokončen!", "Všechny testy prošly úspěšně", None),
    ]

    notif_type, title, message, task_id = random.choice(samples)

    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO notifications (user_id, notification_type, title, message, related_task_id)
               VALUES (NULL, ?, ?, ?, ?)""",
            (notif_type, title, message, task_id),
        )
        notification_id = cursor.lastrowid
        conn.commit()

        return {
            "id": notification_id,
            "message": "Sample notification created",
            "type": notif_type,
            "title": title,
        }
