"""Comments API for ANT HILL - Task knowledge base."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db

router = APIRouter(prefix="/api/comments", tags=["comments"])


class CommentCreate(BaseModel):
    """Create comment request."""

    task_id: int
    user_id: str  # TODO: Replace with auth dependency
    content: str
    is_solution: bool = False


class CommentResponse(BaseModel):
    """Comment response."""

    id: int
    task_id: int
    user_id: str
    user_name: str | None
    user_avatar: str | None
    content: str
    is_solution: bool
    created_at: str
    updated_at: str


@router.post("", response_model=CommentResponse)
async def create_comment(comment: CommentCreate):
    """Add a comment to a task."""
    with get_db() as conn:
        # Verify task exists
        task = conn.execute("SELECT id FROM tasks WHERE id = ?", (comment.task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Insert comment
        cursor = conn.execute(
            """INSERT INTO task_comments (task_id, user_id, content, is_solution)
               VALUES (?, ?, ?, ?)""",
            (comment.task_id, comment.user_id, comment.content, int(comment.is_solution)),
        )
        comment_id = cursor.lastrowid

        # Get comment with user info
        result = conn.execute(
            """SELECT tc.id, tc.task_id, tc.user_id, u.name as user_name,
                      u.avatar_url as user_avatar, tc.content, tc.is_solution,
                      tc.created_at, tc.updated_at
               FROM task_comments tc
               LEFT JOIN users u ON tc.user_id = u.id
               WHERE tc.id = ?""",
            (comment_id,),
        ).fetchone()

        conn.commit()

        return {
            "id": result["id"],
            "task_id": result["task_id"],
            "user_id": result["user_id"],
            "user_name": result["user_name"],
            "user_avatar": result["user_avatar"],
            "content": result["content"],
            "is_solution": bool(result["is_solution"]),
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
        }


@router.get("/task/{task_id}", response_model=list[CommentResponse])
async def get_task_comments(task_id: int):
    """Get all comments for a task, solutions first."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT tc.id, tc.task_id, tc.user_id, u.name as user_name,
                      u.avatar_url as user_avatar, tc.content, tc.is_solution,
                      tc.created_at, tc.updated_at
               FROM task_comments tc
               LEFT JOIN users u ON tc.user_id = u.id
               WHERE tc.task_id = ?
               ORDER BY tc.is_solution DESC, tc.created_at ASC""",
            (task_id,),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "task_id": row["task_id"],
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "user_avatar": row["user_avatar"],
                "content": row["content"],
                "is_solution": bool(row["is_solution"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


@router.put("/{comment_id}/mark-solution")
async def mark_comment_as_solution(comment_id: int):
    """Mark a comment as the solution."""
    with get_db() as conn:
        # Verify comment exists
        comment = conn.execute(
            "SELECT task_id FROM task_comments WHERE id = ?", (comment_id,)
        ).fetchone()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Unmark all other solutions for this task
        conn.execute(
            "UPDATE task_comments SET is_solution = 0 WHERE task_id = ?",
            (comment["task_id"],),
        )

        # Mark this comment as solution
        conn.execute(
            "UPDATE task_comments SET is_solution = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (comment_id,),
        )
        conn.commit()

        return {"message": "Comment marked as solution"}


@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, user_id: str):
    """Delete a comment (only owner can delete)."""
    with get_db() as conn:
        # Verify comment exists and ownership
        comment = conn.execute(
            "SELECT user_id FROM task_comments WHERE id = ?", (comment_id,)
        ).fetchone()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        if comment["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

        conn.execute("DELETE FROM task_comments WHERE id = ?", (comment_id,))
        conn.commit()

        return {"message": "Comment deleted"}
