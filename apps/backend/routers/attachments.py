"""Attachments router for task file uploads."""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import get_db

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".md", ".csv", ".json",
    # Archives
    ".zip", ".rar", ".7z", ".tar", ".gz",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# MIME type mapping for inline preview
MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
}


class Attachment(BaseModel):
    id: int
    task_id: int
    filename: str
    original_name: str
    file_type: str
    file_size: int
    created_at: str


def row_to_attachment(row) -> dict:
    """Convert database row to attachment dict."""
    return {
        "id": row["id"],
        "task_id": row["task_id"],
        "filename": row["filename"],
        "original_name": row["original_name"],
        "file_type": row["file_type"],
        "file_size": row["file_size"],
        "created_at": row["created_at"],
    }


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase."""
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


@router.get("/task/{task_id}", response_model=list[Attachment])
def list_attachments(task_id: int) -> list[dict]:
    """Get all attachments for a task."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM attachments WHERE task_id = ? ORDER BY created_at DESC",
            (task_id,)
        )
        return [row_to_attachment(row) for row in cursor.fetchall()]


@router.post("/task/{task_id}", response_model=Attachment)
async def upload_attachment(task_id: int, file: UploadFile = File(...)) -> dict:
    """Upload a file attachment to a task."""
    # Verify task exists
    with get_db() as conn:
        cursor = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB"
        )

    # Generate unique filename
    ext = get_file_extension(file.filename)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Save to database
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO attachments (task_id, filename, original_name, file_type, file_size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, unique_filename, file.filename, ext, file_size)
        )
        conn.commit()
        attachment_id = cursor.lastrowid

        cursor = conn.execute("SELECT * FROM attachments WHERE id = ?", (attachment_id,))
        return row_to_attachment(cursor.fetchone())


@router.get("/{attachment_id}/download")
def download_attachment(attachment_id: int):
    """Download an attachment file."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM attachments WHERE id = ?",
            (attachment_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Attachment not found")

        attachment = row_to_attachment(row)
        file_path = UPLOAD_DIR / attachment["filename"]

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            path=file_path,
            filename=attachment["original_name"],
            media_type="application/octet-stream"
        )


@router.get("/{attachment_id}/preview")
def preview_attachment(attachment_id: int):
    """Preview an attachment file with correct MIME type (inline display)."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM attachments WHERE id = ?",
            (attachment_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Attachment not found")

        attachment = row_to_attachment(row)
        file_path = UPLOAD_DIR / attachment["filename"]

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        mime_type = MIME_TYPES.get(
            attachment["file_type"].lower(),
            "application/octet-stream"
        )

        return FileResponse(
            path=file_path,
            media_type=mime_type,
            headers={"Content-Disposition": "inline"},
        )


@router.delete("/{attachment_id}")
def delete_attachment(attachment_id: int) -> dict:
    """Delete an attachment."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM attachments WHERE id = ?",
            (attachment_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Attachment not found")

        attachment = row_to_attachment(row)

        # Delete file from disk
        file_path = UPLOAD_DIR / attachment["filename"]
        if file_path.exists():
            os.remove(file_path)

        # Delete from database
        conn.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
        conn.commit()

        return {"message": "Attachment deleted"}
