"""User service for managing users in the database."""

from typing import Optional
from database import get_db
from .clerk_middleware import ClerkUser


class UserService:
    """Service for user CRUD operations."""

    @staticmethod
    def get_or_create_user(clerk_user: ClerkUser) -> dict:
        """Get existing user or create new one from Clerk user data."""
        with get_db() as conn:
            cursor = conn.cursor()

            # Try to find existing user
            cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (clerk_user.user_id,)
            )
            row = cursor.fetchone()

            if row:
                # Update user data if changed
                cursor.execute("""
                    UPDATE users
                    SET email = ?, name = ?, avatar_url = ?
                    WHERE id = ?
                """, (clerk_user.email, clerk_user.name, clerk_user.image_url, clerk_user.user_id))
                conn.commit()

                cursor.execute("SELECT * FROM users WHERE id = ?", (clerk_user.user_id,))
                row = cursor.fetchone()
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO users (id, email, name, avatar_url)
                    VALUES (?, ?, ?, ?)
                """, (clerk_user.user_id, clerk_user.email, clerk_user.name, clerk_user.image_url))
                conn.commit()

                cursor.execute("SELECT * FROM users WHERE id = ?", (clerk_user.user_id,))
                row = cursor.fetchone()

            return dict(row) if row else None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[dict]:
        """Get user by ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[dict]:
        """Get user by email."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete user and all associated data."""
        with get_db() as conn:
            cursor = conn.cursor()

            # Delete user's OAuth tokens
            cursor.execute("DELETE FROM user_oauth_tokens WHERE user_id = ?", (user_id,))

            # Delete user's integration settings
            cursor.execute("DELETE FROM integration_settings WHERE user_id = ?", (user_id,))

            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def list_users(limit: int = 100, offset: int = 0) -> list:
        """List all users with pagination."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]
