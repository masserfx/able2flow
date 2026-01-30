"""Audit router for viewing audit logs."""

from fastapi import APIRouter

from services import audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit_logs(
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Get audit logs with optional filtering."""
    return audit_service.get_audit_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )


@router.get("/stats")
def get_audit_stats() -> dict:
    """Get audit log statistics."""
    return audit_service.get_audit_stats()
