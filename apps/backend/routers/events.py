"""Event sourcing and time-travel router."""

from fastapi import APIRouter, HTTPException, Query

from services.event_store import event_store

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/feed")
def get_activity_feed(
    limit: int = Query(50, le=200),
    entity_types: str | None = Query(None, description="Comma-separated: task,incident,monitor"),
) -> list[dict]:
    """Get activity feed across all entities.

    Real-time feed of all system changes.
    """
    types = entity_types.split(",") if entity_types else None
    return event_store.get_activity_feed(limit=limit, entity_types=types)


@router.get("/{entity_type}/{entity_id}/history")
def get_entity_history(entity_type: str, entity_id: int) -> dict:
    """Get complete history of an entity.

    Shows all changes from creation to current state.
    """
    history = event_store.get_entity_history(entity_type, entity_id)

    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for {entity_type} #{entity_id}",
        )

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "event_count": len(history),
        "first_event": history[0]["timestamp"] if history else None,
        "last_event": history[-1]["timestamp"] if history else None,
        "events": history,
    }


@router.get("/{entity_type}/{entity_id}/state-at")
def get_state_at_timestamp(
    entity_type: str,
    entity_id: int,
    timestamp: str = Query(..., description="ISO format: 2024-01-15T10:30:00"),
) -> dict:
    """Time travel: Get entity state at a specific point in time.

    Reconstructs what the entity looked like at any historical moment.
    """
    state = event_store.get_state_at(entity_type, entity_id, timestamp)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"No state found for {entity_type} #{entity_id} at {timestamp}",
        )

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "requested_timestamp": timestamp,
        "state": state,
        "was_deleted": state.get("_deleted", False),
    }


@router.get("/{entity_type}/{entity_id}/diff")
def diff_entity_states(
    entity_type: str,
    entity_id: int,
    from_timestamp: str = Query(..., alias="from"),
    to_timestamp: str = Query(..., alias="to"),
) -> dict:
    """Compare entity state between two points in time.

    Shows exactly what changed and when.
    """
    return event_store.diff_states(
        entity_type, entity_id, from_timestamp, to_timestamp
    )


@router.get("/{entity_type}/{entity_id}/replay")
def replay_entity_events(
    entity_type: str,
    entity_id: int,
    until: str | None = Query(None, description="Stop replay at this timestamp"),
) -> dict:
    """Replay events to see state evolution step by step.

    Useful for debugging and understanding how state changed.
    """
    events = list(event_store.replay_events(entity_type, entity_id, until))

    if not events:
        raise HTTPException(
            status_code=404,
            detail=f"No events found for {entity_type} #{entity_id}",
        )

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "replayed_events": len(events),
        "final_state": events[-1]["state_after"] if events else None,
        "replay": events,
    }


@router.post("/{entity_type}/{entity_id}/restore")
def restore_entity(
    entity_type: str,
    entity_id: int,
    to_timestamp: str = Query(..., alias="to", description="Restore to this timestamp"),
) -> dict:
    """Disaster recovery: Restore entity to previous state.

    Rolls back an entity to its state at specified timestamp.
    WARNING: This modifies the database.
    """
    result = event_store.restore_entity(entity_type, entity_id, to_timestamp)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Restoration failed"),
        )

    return result
