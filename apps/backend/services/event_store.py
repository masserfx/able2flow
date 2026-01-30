"""Event sourcing store for complete state reconstruction."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generator

from database import get_db


@dataclass
class Event:
    """Immutable event record."""

    id: int
    entity_type: str
    entity_id: int
    event_type: str  # created, updated, deleted, etc.
    payload: dict[str, Any]
    metadata: dict[str, Any]
    timestamp: str


class EventStore:
    """Event sourcing store with time-travel capabilities."""

    def get_entity_history(
        self, entity_type: str, entity_id: int
    ) -> list[dict[str, Any]]:
        """Get complete history of an entity.

        Returns all events for an entity in chronological order,
        allowing full state reconstruction.
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM audit_log
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY timestamp ASC
                """,
                (entity_type, entity_id),
            )
            return [
                {
                    "id": row["id"],
                    "action": row["action"],
                    "old_value": json.loads(row["old_value"])
                    if row["old_value"]
                    else None,
                    "new_value": json.loads(row["new_value"])
                    if row["new_value"]
                    else None,
                    "timestamp": row["timestamp"],
                }
                for row in cursor.fetchall()
            ]

    def get_state_at(
        self, entity_type: str, entity_id: int, at_timestamp: str
    ) -> dict[str, Any] | None:
        """Reconstruct entity state at a specific point in time.

        This is the "time travel" feature - see what an entity
        looked like at any point in history.
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM audit_log
                WHERE entity_type = ? AND entity_id = ?
                AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (entity_type, entity_id, at_timestamp),
            )
            row = cursor.fetchone()

            if not row:
                return None

            # For updates and creates, new_value is the state
            # For deletes, old_value is the last known state
            if row["action"] == "delete":
                state = json.loads(row["old_value"]) if row["old_value"] else None
                if state:
                    state["_deleted"] = True
                    state["_deleted_at"] = row["timestamp"]
                return state
            else:
                return json.loads(row["new_value"]) if row["new_value"] else None

    def replay_events(
        self, entity_type: str, entity_id: int, until: str | None = None
    ) -> Generator[dict[str, Any], None, None]:
        """Replay events to rebuild state incrementally.

        Useful for debugging or auditing how state evolved.
        """
        state = {}
        history = self.get_entity_history(entity_type, entity_id)

        for event in history:
            if until and event["timestamp"] > until:
                break

            if event["action"] == "create":
                state = event["new_value"] or {}
            elif event["action"] == "update":
                if event["new_value"]:
                    state.update(event["new_value"])
            elif event["action"] == "delete":
                state["_deleted"] = True

            yield {
                "event": event,
                "state_after": state.copy(),
            }

    def diff_states(
        self,
        entity_type: str,
        entity_id: int,
        timestamp1: str,
        timestamp2: str,
    ) -> dict[str, Any]:
        """Compare entity state between two points in time."""
        state1 = self.get_state_at(entity_type, entity_id, timestamp1)
        state2 = self.get_state_at(entity_type, entity_id, timestamp2)

        if not state1 and not state2:
            return {"error": "Entity not found at either timestamp"}

        changes = {}
        all_keys = set((state1 or {}).keys()) | set((state2 or {}).keys())

        for key in all_keys:
            val1 = (state1 or {}).get(key)
            val2 = (state2 or {}).get(key)
            if val1 != val2:
                changes[key] = {"from": val1, "to": val2}

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp1": timestamp1,
            "timestamp2": timestamp2,
            "state_at_t1": state1,
            "state_at_t2": state2,
            "changes": changes,
        }

    def restore_entity(
        self, entity_type: str, entity_id: int, to_timestamp: str
    ) -> dict[str, Any]:
        """Restore an entity to its state at a specific timestamp.

        This is disaster recovery - rollback an entity to previous state.
        """
        target_state = self.get_state_at(entity_type, entity_id, to_timestamp)

        if not target_state:
            return {
                "success": False,
                "error": "Cannot find entity state at specified timestamp",
            }

        if target_state.get("_deleted"):
            return {
                "success": False,
                "error": "Entity was deleted at this timestamp",
                "last_known_state": target_state,
            }

        # Remove internal fields
        restore_data = {
            k: v for k, v in target_state.items() if not k.startswith("_")
        }

        # Perform restoration based on entity type
        table_map = {
            "task": "tasks",
            "column": "columns",
            "monitor": "monitors",
            "incident": "incidents",
        }

        table = table_map.get(entity_type)
        if not table:
            return {"success": False, "error": f"Unknown entity type: {entity_type}"}

        with get_db() as conn:
            # Check if entity exists
            cursor = conn.execute(
                f"SELECT * FROM {table} WHERE id = ?", (entity_id,)
            )
            exists = cursor.fetchone()

            if exists:
                # Update existing
                fields = [k for k in restore_data.keys() if k != "id"]
                set_clause = ", ".join(f"{f} = ?" for f in fields)
                values = [restore_data[f] for f in fields] + [entity_id]

                conn.execute(
                    f"UPDATE {table} SET {set_clause} WHERE id = ?", values
                )
            else:
                # Re-insert deleted entity
                fields = list(restore_data.keys())
                placeholders = ", ".join("?" * len(fields))
                field_names = ", ".join(fields)
                values = [restore_data[f] for f in fields]

                conn.execute(
                    f"INSERT INTO {table} ({field_names}) VALUES ({placeholders})",
                    values,
                )

            conn.commit()

        # Log restoration
        from services import audit_service

        audit_service.log_action(
            entity_type,
            entity_id,
            "restore",
            old_value=dict(exists) if exists else None,
            new_value=restore_data,
        )

        return {
            "success": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "restored_to": to_timestamp,
            "restored_state": restore_data,
        }

    def get_activity_feed(
        self, limit: int = 50, entity_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get activity feed across all entities.

        Useful for dashboard and real-time updates.
        """
        with get_db() as conn:
            query = """
                SELECT * FROM audit_log
                WHERE 1=1
            """
            params: list[Any] = []

            if entity_types:
                placeholders = ", ".join("?" * len(entity_types))
                query += f" AND entity_type IN ({placeholders})"
                params.extend(entity_types)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [
                {
                    "id": row["id"],
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "action": row["action"],
                    "timestamp": row["timestamp"],
                    "summary": self._generate_summary(row),
                }
                for row in cursor.fetchall()
            ]

    def _generate_summary(self, row) -> str:
        """Generate human-readable summary of an event."""
        entity = row["entity_type"]
        action = row["action"]
        entity_id = row["entity_id"]

        if row["new_value"]:
            data = json.loads(row["new_value"])
            name = data.get("title") or data.get("name") or f"#{entity_id}"
        elif row["old_value"]:
            data = json.loads(row["old_value"])
            name = data.get("title") or data.get("name") or f"#{entity_id}"
        else:
            name = f"#{entity_id}"

        action_verbs = {
            "create": "created",
            "update": "updated",
            "delete": "deleted",
            "move": "moved",
            "acknowledge": "acknowledged",
            "resolve": "resolved",
            "restore": "restored",
            "ai_analyze": "analyzed by AI",
            "ai_auto_triage": "auto-triaged by AI",
        }

        verb = action_verbs.get(action, action)
        return f'{entity.capitalize()} "{name}" was {verb}'


# Global instance
event_store = EventStore()
