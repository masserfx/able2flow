"""Google Docs integration endpoints."""

from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from auth.clerk_middleware import ClerkUser
from services.integrations import DocsService

router = APIRouter(prefix="/api/integrations/docs", tags=["Docs"])


class CreateDocRequest(BaseModel):
    """Request to create a new document."""
    title: str
    content: Optional[str] = None


class AttachDocRequest(BaseModel):
    """Request to attach a document to a task."""
    task_id: int
    document_id: str


class CreateDocFromTaskRequest(BaseModel):
    """Request to create a document from a task."""
    task_id: int


@router.post("/create")
async def create_document(
    request: CreateDocRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Create a new Google Doc."""
    service = DocsService(user.user_id)

    doc = await service.create_document(
        title=request.title,
        content=request.content,
    )

    if not doc:
        raise HTTPException(status_code=400, detail="Failed to create document")

    doc_id = doc.get("documentId")

    return {
        "status": "success",
        "document": {
            "id": doc_id,
            "title": request.title,
            "url": f"https://docs.google.com/document/d/{doc_id}/edit",
        },
    }


@router.post("/create-from-task")
async def create_doc_from_task(
    request: CreateDocFromTaskRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Create a Google Doc from a task."""
    service = DocsService(user.user_id)

    doc = await service.create_doc_from_task(request.task_id)

    if not doc:
        raise HTTPException(status_code=400, detail="Failed to create document from task")

    doc_id = doc.get("documentId")

    return {
        "status": "success",
        "document": {
            "id": doc_id,
            "url": f"https://docs.google.com/document/d/{doc_id}/edit",
        },
    }


@router.post("/attach")
async def attach_document(
    request: AttachDocRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Attach an existing Google Doc to a task."""
    service = DocsService(user.user_id)

    result = await service.attach_document_to_task(
        task_id=request.task_id,
        document_id=request.document_id,
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to attach document")

    return {
        "status": "success",
        "attachment": result,
    }


@router.get("/task/{task_id}")
async def get_linked_documents(
    task_id: int,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Get all documents linked to a task."""
    documents = DocsService.get_linked_documents(task_id)

    return {
        "task_id": task_id,
        "documents": documents,
    }


@router.get("/{document_id}/preview")
async def get_document_preview(
    document_id: str,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Get document preview/metadata."""
    service = DocsService(user.user_id)

    preview = await service.get_document_preview(document_id)

    if not preview:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document": preview,
    }


@router.delete("/task/{task_id}/document/{document_id}")
async def unlink_document(
    task_id: int,
    document_id: str,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Remove document link from task."""
    success = DocsService.unlink_document(task_id, document_id)

    if not success:
        raise HTTPException(status_code=404, detail="Link not found")

    return {
        "status": "success",
        "message": "Document unlinked from task",
    }
