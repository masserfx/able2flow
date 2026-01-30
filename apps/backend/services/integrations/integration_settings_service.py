"""Service for managing integration settings."""

import json
from typing import Optional
from database import get_db


class IntegrationSettingsService:
    """Service for managing user integration settings."""

    INTEGRATION_TYPES = ["calendar", "docs", "gmail", "slack"]

    @staticmethod
    def get_settings(
        user_id: str,
        integration_type: str,
        project_id: Optional[int] = None,
    ) -> Optional[dict]:
        """Get integration settings for a user."""
        with get_db() as conn:
            cursor = conn.cursor()

            if project_id:
                cursor.execute("""
                    SELECT * FROM integration_settings
                    WHERE user_id = ? AND integration_type = ? AND project_id = ?
                """, (user_id, integration_type, project_id))
            else:
                cursor.execute("""
                    SELECT * FROM integration_settings
                    WHERE user_id = ? AND integration_type = ? AND project_id IS NULL
                """, (user_id, integration_type))

            row = cursor.fetchone()
            if not row:
                return None

            settings = dict(row)
            if settings.get("settings"):
                settings["settings"] = json.loads(settings["settings"])
            return settings

    @staticmethod
    def save_settings(
        user_id: str,
        integration_type: str,
        settings: dict,
        project_id: Optional[int] = None,
        enabled: bool = True,
    ) -> dict:
        """Save or update integration settings."""
        if integration_type not in IntegrationSettingsService.INTEGRATION_TYPES:
            raise ValueError(f"Invalid integration type: {integration_type}")

        settings_json = json.dumps(settings)

        with get_db() as conn:
            cursor = conn.cursor()

            # Check if settings exist
            if project_id:
                cursor.execute("""
                    SELECT id FROM integration_settings
                    WHERE user_id = ? AND integration_type = ? AND project_id = ?
                """, (user_id, integration_type, project_id))
            else:
                cursor.execute("""
                    SELECT id FROM integration_settings
                    WHERE user_id = ? AND integration_type = ? AND project_id IS NULL
                """, (user_id, integration_type))

            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE integration_settings
                    SET settings = ?, enabled = ?
                    WHERE id = ?
                """, (settings_json, enabled, existing["id"]))
            else:
                cursor.execute("""
                    INSERT INTO integration_settings (user_id, project_id, integration_type, settings, enabled)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, project_id, integration_type, settings_json, enabled))

            conn.commit()

            return {
                "user_id": user_id,
                "project_id": project_id,
                "integration_type": integration_type,
                "settings": settings,
                "enabled": enabled,
            }

    @staticmethod
    def toggle_integration(
        user_id: str,
        integration_type: str,
        enabled: bool,
        project_id: Optional[int] = None,
    ) -> bool:
        """Enable or disable an integration."""
        with get_db() as conn:
            cursor = conn.cursor()

            if project_id:
                cursor.execute("""
                    UPDATE integration_settings
                    SET enabled = ?
                    WHERE user_id = ? AND integration_type = ? AND project_id = ?
                """, (enabled, user_id, integration_type, project_id))
            else:
                cursor.execute("""
                    UPDATE integration_settings
                    SET enabled = ?
                    WHERE user_id = ? AND integration_type = ? AND project_id IS NULL
                """, (enabled, user_id, integration_type))

            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete_settings(
        user_id: str,
        integration_type: str,
        project_id: Optional[int] = None,
    ) -> bool:
        """Delete integration settings."""
        with get_db() as conn:
            cursor = conn.cursor()

            if project_id:
                cursor.execute("""
                    DELETE FROM integration_settings
                    WHERE user_id = ? AND integration_type = ? AND project_id = ?
                """, (user_id, integration_type, project_id))
            else:
                cursor.execute("""
                    DELETE FROM integration_settings
                    WHERE user_id = ? AND integration_type = ? AND project_id IS NULL
                """, (user_id, integration_type))

            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def list_user_integrations(user_id: str) -> list:
        """List all integration settings for a user."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM integration_settings
                WHERE user_id = ?
                ORDER BY integration_type
            """, (user_id,))

            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get("settings"):
                    item["settings"] = json.loads(item["settings"])
                results.append(item)
            return results

    @staticmethod
    def is_integration_enabled(
        user_id: str,
        integration_type: str,
        project_id: Optional[int] = None,
    ) -> bool:
        """Check if an integration is enabled."""
        settings = IntegrationSettingsService.get_settings(user_id, integration_type, project_id)
        return settings.get("enabled", False) if settings else False
