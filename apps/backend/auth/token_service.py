"""Service for managing OAuth tokens with encryption."""

import os
import base64
import json
from datetime import datetime, timedelta
from typing import Optional
from cryptography.fernet import Fernet

from database import get_db


# Encryption key for tokens (should be set in environment)
ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY", "")


def _get_fernet() -> Optional[Fernet]:
    """Get Fernet instance for encryption/decryption."""
    if not ENCRYPTION_KEY:
        # Generate a key for development (not secure for production!)
        return None
    try:
        return Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
    except Exception:
        return None


def _encrypt(data: str) -> str:
    """Encrypt sensitive data."""
    fernet = _get_fernet()
    if fernet:
        return fernet.encrypt(data.encode()).decode()
    # Fallback: base64 encode (not secure, only for development)
    return base64.b64encode(data.encode()).decode()


def _decrypt(data: str) -> str:
    """Decrypt sensitive data."""
    fernet = _get_fernet()
    if fernet:
        return fernet.decrypt(data.encode()).decode()
    # Fallback: base64 decode
    return base64.b64decode(data.encode()).decode()


class TokenService:
    """Service for managing OAuth tokens."""

    PROVIDERS = ["google", "slack"]

    @staticmethod
    def save_token(
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        scopes: Optional[list] = None,
        expires_at: Optional[datetime] = None,
    ) -> dict:
        """Save or update OAuth token for a user."""
        if provider not in TokenService.PROVIDERS:
            raise ValueError(f"Invalid provider: {provider}")

        encrypted_access = _encrypt(access_token)
        encrypted_refresh = _encrypt(refresh_token) if refresh_token else None
        scopes_str = ",".join(scopes) if scopes else None
        expires_str = expires_at.isoformat() if expires_at else None

        with get_db() as conn:
            cursor = conn.cursor()

            # Check if token exists
            cursor.execute(
                "SELECT id FROM user_oauth_tokens WHERE user_id = ? AND provider = ?",
                (user_id, provider)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing token
                cursor.execute("""
                    UPDATE user_oauth_tokens
                    SET access_token = ?, refresh_token = ?, scopes = ?, expires_at = ?
                    WHERE user_id = ? AND provider = ?
                """, (encrypted_access, encrypted_refresh, scopes_str, expires_str, user_id, provider))
            else:
                # Insert new token
                cursor.execute("""
                    INSERT INTO user_oauth_tokens (user_id, provider, access_token, refresh_token, scopes, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, provider, encrypted_access, encrypted_refresh, scopes_str, expires_str))

            conn.commit()

            return {
                "user_id": user_id,
                "provider": provider,
                "scopes": scopes,
                "expires_at": expires_str,
            }

    @staticmethod
    def get_token(user_id: str, provider: str) -> Optional[dict]:
        """Get OAuth token for a user and provider."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_oauth_tokens WHERE user_id = ? AND provider = ?",
                (user_id, provider)
            )
            row = cursor.fetchone()

            if not row:
                return None

            token_data = dict(row)

            # Decrypt tokens
            token_data["access_token"] = _decrypt(token_data["access_token"])
            if token_data.get("refresh_token"):
                token_data["refresh_token"] = _decrypt(token_data["refresh_token"])

            # Parse scopes
            if token_data.get("scopes"):
                token_data["scopes"] = token_data["scopes"].split(",")

            return token_data

    @staticmethod
    def delete_token(user_id: str, provider: str) -> bool:
        """Delete OAuth token for a user and provider."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_oauth_tokens WHERE user_id = ? AND provider = ?",
                (user_id, provider)
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_all_tokens(user_id: str) -> list:
        """Get all OAuth tokens for a user (without decrypting)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT provider, scopes, expires_at, created_at FROM user_oauth_tokens WHERE user_id = ?",
                (user_id,)
            )
            tokens = []
            for row in cursor.fetchall():
                token = dict(row)
                if token.get("scopes"):
                    token["scopes"] = token["scopes"].split(",")
                tokens.append(token)
            return tokens

    @staticmethod
    def is_token_expired(user_id: str, provider: str) -> bool:
        """Check if a token is expired."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT expires_at FROM user_oauth_tokens WHERE user_id = ? AND provider = ?",
                (user_id, provider)
            )
            row = cursor.fetchone()

            if not row or not row["expires_at"]:
                return False  # No expiration set

            expires_at = datetime.fromisoformat(row["expires_at"])
            return datetime.now() > expires_at

    @staticmethod
    def refresh_google_token(user_id: str) -> Optional[dict]:
        """Refresh Google OAuth token using refresh_token."""
        import httpx

        token_data = TokenService.get_token(user_id, "google")
        if not token_data or not token_data.get("refresh_token"):
            return None

        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            return None

        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": token_data["refresh_token"],
                        "grant_type": "refresh_token",
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Calculate new expiration
                expires_in = data.get("expires_in", 3600)
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                # Save new token
                return TokenService.save_token(
                    user_id=user_id,
                    provider="google",
                    access_token=data["access_token"],
                    refresh_token=token_data["refresh_token"],  # Keep existing refresh token
                    scopes=token_data.get("scopes"),
                    expires_at=expires_at,
                )
        except Exception:
            return None
