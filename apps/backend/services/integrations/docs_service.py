"""Google Docs integration service."""

from typing import Optional
import httpx

from database import get_db
from auth.token_service import TokenService


class DocsService:
    """Service for Google Docs operations."""

    DOCS_API_BASE = "https://docs.googleapis.com/v1"
    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary."""
        if self._access_token:
            return self._access_token

        token_data = TokenService.get_token(self.user_id, "google")
        if not token_data:
            return None

        if TokenService.is_token_expired(self.user_id, "google"):
            refreshed = TokenService.refresh_google_token(self.user_id)
            if not refreshed:
                return None
            token_data = TokenService.get_token(self.user_id, "google")

        self._access_token = token_data.get("access_token")
        return self._access_token

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make authenticated request to Google API."""
        access_token = await self._get_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    return None

                if response.status_code in [200, 201]:
                    return response.json() if response.content else {}
                return None
            except Exception:
                return None

    async def create_document(
        self,
        title: str,
        content: Optional[str] = None,
    ) -> Optional[dict]:
        """Create a new Google Doc."""
        # Create empty document
        doc_data = {"title": title}
        result = await self._make_request(
            "POST",
            f"{self.DOCS_API_BASE}/documents",
            doc_data
        )

        if not result:
            return None

        doc_id = result.get("documentId")

        # Add content if provided
        if content and doc_id:
            await self._add_content_to_doc(doc_id, content)

        return result

    async def _add_content_to_doc(self, document_id: str, content: str) -> bool:
        """Add content to an existing document."""
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": content,
                }
            }
        ]

        result = await self._make_request(
            "POST",
            f"{self.DOCS_API_BASE}/documents/{document_id}:batchUpdate",
            {"requests": requests}
        )
        return result is not None

    async def get_document(self, document_id: str) -> Optional[dict]:
        """Get document metadata and content."""
        return await self._make_request(
            "GET",
            f"{self.DOCS_API_BASE}/documents/{document_id}"
        )

    async def get_document_preview(self, document_id: str) -> Optional[dict]:
        """Get document preview (metadata only for performance)."""
        # Use Drive API for basic metadata
        result = await self._make_request(
            "GET",
            f"{self.DRIVE_API_BASE}/files/{document_id}?fields=id,name,thumbnailLink,webViewLink,modifiedTime,owners"
        )
        return result

    async def create_doc_from_task(self, task_id: int) -> Optional[dict]:
        """Create a Google Doc from a task."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()

            if not task:
                return None

            task_dict = dict(task)

            # Create document with task details
            content = f"""Task: {task_dict['title']}

Description:
{task_dict.get('description', 'No description provided.')}

Priority: {task_dict.get('priority', 'medium')}
Due Date: {task_dict.get('due_date', 'Not set')}

---
Notes:


"""
            result = await self.create_document(
                title=f"Task: {task_dict['title']}",
                content=content,
            )

            if result:
                # Save link to linked_documents
                doc_id = result.get("documentId")
                doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

                cursor.execute("""
                    INSERT INTO linked_documents (task_id, provider, external_id, title, url)
                    VALUES (?, ?, ?, ?, ?)
                """, (task_id, "google_docs", doc_id, task_dict['title'], doc_url))
                conn.commit()

            return result

    async def attach_document_to_task(
        self,
        task_id: int,
        document_id: str,
    ) -> Optional[dict]:
        """Attach an existing Google Doc to a task."""
        # Get document info
        doc_info = await self.get_document_preview(document_id)
        if not doc_info:
            return None

        with get_db() as conn:
            cursor = conn.cursor()

            # Check if already attached
            cursor.execute(
                "SELECT id FROM linked_documents WHERE task_id = ? AND external_id = ?",
                (task_id, document_id)
            )
            if cursor.fetchone():
                return {"status": "already_attached"}

            # Save link
            cursor.execute("""
                INSERT INTO linked_documents (task_id, provider, external_id, title, url)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task_id,
                "google_docs",
                document_id,
                doc_info.get("name", "Untitled"),
                doc_info.get("webViewLink", f"https://docs.google.com/document/d/{document_id}/edit"),
            ))
            conn.commit()

            return {
                "task_id": task_id,
                "document_id": document_id,
                "title": doc_info.get("name"),
                "url": doc_info.get("webViewLink"),
            }

    @staticmethod
    def get_linked_documents(task_id: int) -> list:
        """Get all documents linked to a task."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM linked_documents WHERE task_id = ?",
                (task_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def unlink_document(task_id: int, document_id: str) -> bool:
        """Remove document link from task."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM linked_documents WHERE task_id = ? AND external_id = ?",
                (task_id, document_id)
            )
            conn.commit()
            return cursor.rowcount > 0
