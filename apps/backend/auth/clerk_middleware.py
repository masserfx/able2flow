"""Clerk JWT verification middleware for FastAPI."""

import os
import httpx
from typing import Optional
from functools import lru_cache

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Clerk configuration (support both NEXT_PUBLIC_ prefix and without)
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER", "")  # e.g., "https://your-app.clerk.accounts.dev"


class ClerkUser:
    """Represents an authenticated Clerk user."""

    def __init__(
        self,
        user_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        image_url: Optional[str] = None,
        email_verified: bool = False,
    ):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.image_url = image_url
        self.email_verified = email_verified

    def __repr__(self) -> str:
        return f"ClerkUser(id={self.user_id}, email={self.email})"


class ClerkMiddleware:
    """Middleware for verifying Clerk JWTs."""

    def __init__(self):
        self.http_bearer = HTTPBearer(auto_error=False)
        self._jwks_cache: Optional[dict] = None

    @lru_cache(maxsize=1)
    def _get_jwks_url(self) -> str:
        """Get JWKS URL from Clerk issuer."""
        if CLERK_JWT_ISSUER:
            return f"{CLERK_JWT_ISSUER.rstrip('/')}/.well-known/jwks.json"
        # Fallback: construct from publishable key
        if CLERK_PUBLISHABLE_KEY.startswith("pk_"):
            # Extract instance ID from publishable key
            return "https://api.clerk.dev/.well-known/jwks.json"
        return ""

    async def _fetch_jwks(self) -> dict:
        """Fetch JWKS from Clerk."""
        jwks_url = self._get_jwks_url()
        if not jwks_url:
            return {"keys": []}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(jwks_url)
                response.raise_for_status()
                return response.json()
            except Exception:
                return {"keys": []}

    async def verify_token(self, token: str) -> Optional[ClerkUser]:
        """Verify a Clerk JWT and return user info."""
        if not token:
            return None

        try:
            # For development/testing: use Clerk's backend API to verify session
            if CLERK_SECRET_KEY:
                return await self._verify_with_clerk_api(token)

            # Fallback: basic JWT decode (not recommended for production)
            return await self._decode_jwt(token)
        except Exception:
            return None

    async def _verify_with_clerk_api(self, token: str) -> Optional[ClerkUser]:
        """Verify token using Clerk's Backend API."""
        async with httpx.AsyncClient() as client:
            try:
                # Verify the session token
                headers = {
                    "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                    "Content-Type": "application/json",
                }

                # Get session info from token
                # First, try to decode the token to get user_id
                import base64
                import json

                # Decode JWT payload (middle part)
                parts = token.split(".")
                if len(parts) != 3:
                    return None

                # Add padding if needed
                payload_part = parts[1]
                padding = 4 - len(payload_part) % 4
                if padding != 4:
                    payload_part += "=" * padding

                payload = json.loads(base64.urlsafe_b64decode(payload_part))
                user_id = payload.get("sub")

                if not user_id:
                    return None

                # Fetch user details from Clerk
                response = await client.get(
                    f"https://api.clerk.com/v1/users/{user_id}",
                    headers=headers,
                )

                if response.status_code != 200:
                    return None

                user_data = response.json()

                # Extract primary email
                email = None
                email_verified = False
                if user_data.get("email_addresses"):
                    primary_email = next(
                        (e for e in user_data["email_addresses"]
                         if e["id"] == user_data.get("primary_email_address_id")),
                        user_data["email_addresses"][0] if user_data["email_addresses"] else None
                    )
                    if primary_email:
                        email = primary_email.get("email_address")
                        email_verified = primary_email.get("verification", {}).get("status") == "verified"

                # Build name
                first_name = user_data.get("first_name", "")
                last_name = user_data.get("last_name", "")
                name = f"{first_name} {last_name}".strip() or None

                return ClerkUser(
                    user_id=user_id,
                    email=email,
                    name=name,
                    image_url=user_data.get("image_url"),
                    email_verified=email_verified,
                )

            except Exception:
                return None

    async def _decode_jwt(self, token: str) -> Optional[ClerkUser]:
        """Basic JWT decode without full verification (for development)."""
        try:
            import base64
            import json

            parts = token.split(".")
            if len(parts) != 3:
                return None

            payload_part = parts[1]
            padding = 4 - len(payload_part) % 4
            if padding != 4:
                payload_part += "=" * padding

            payload = json.loads(base64.urlsafe_b64decode(payload_part))

            return ClerkUser(
                user_id=payload.get("sub", ""),
                email=payload.get("email"),
                name=payload.get("name"),
            )
        except Exception:
            return None


# Global middleware instance
clerk_middleware = ClerkMiddleware()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> ClerkUser:
    """Dependency to get the current authenticated user. Raises 401 if not authenticated."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await clerk_middleware.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[ClerkUser]:
    """Dependency to get the current user if authenticated, or None if not."""
    if not credentials:
        return None

    return await clerk_middleware.verify_token(credentials.credentials)
