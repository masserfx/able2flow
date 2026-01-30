"""OAuth callback and token management endpoints."""

import os
import httpx
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user, get_optional_user
from auth.clerk_middleware import ClerkUser
from auth.user_service import UserService
from auth.token_service import TokenService
from services.integrations import IntegrationSettingsService

router = APIRouter(prefix="/api/integrations/oauth", tags=["OAuth"])

# Clerk configuration
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")


class TokenSaveRequest(BaseModel):
    """Request to save OAuth token."""
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    scopes: Optional[list] = None
    expires_in: Optional[int] = None


class IntegrationSettingsRequest(BaseModel):
    """Request to update integration settings."""
    integration_type: str
    settings: dict
    project_id: Optional[int] = None
    enabled: bool = True


@router.get("/me")
async def get_current_user_info(user: ClerkUser = Depends(get_current_user)) -> dict:
    """Get current user information."""
    # Get or create user in database
    db_user = UserService.get_or_create_user(user)

    # Get connected integrations
    tokens = TokenService.get_all_tokens(user.user_id)

    return {
        "user": {
            "id": user.user_id,
            "email": user.email,
            "name": user.name,
            "image_url": user.image_url,
        },
        "connected_providers": [t["provider"] for t in tokens],
        "integrations": tokens,
    }


@router.post("/token")
async def save_oauth_token(
    request: TokenSaveRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Save OAuth token for a provider."""
    expires_at = None
    if request.expires_in:
        expires_at = datetime.now() + timedelta(seconds=request.expires_in)

    result = TokenService.save_token(
        user_id=user.user_id,
        provider=request.provider,
        access_token=request.access_token,
        refresh_token=request.refresh_token,
        scopes=request.scopes,
        expires_at=expires_at,
    )

    return {
        "status": "success",
        "provider": request.provider,
        "scopes": request.scopes,
    }


@router.delete("/token/{provider}")
async def disconnect_provider(
    provider: str,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Disconnect/revoke OAuth token for a provider."""
    deleted = TokenService.delete_token(user.user_id, provider)

    if not deleted:
        raise HTTPException(status_code=404, detail="Token not found")

    # Also delete integration settings
    for integration_type in IntegrationSettingsService.INTEGRATION_TYPES:
        if integration_type.startswith(provider.split("_")[0]):
            IntegrationSettingsService.delete_settings(user.user_id, integration_type)

    return {
        "status": "success",
        "message": f"Disconnected from {provider}",
    }


@router.get("/status/{provider}")
async def check_provider_status(
    provider: str,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Check if a provider is connected and token is valid."""
    token = TokenService.get_token(user.user_id, provider)

    if not token:
        return {
            "connected": False,
            "provider": provider,
        }

    is_expired = TokenService.is_token_expired(user.user_id, provider)

    return {
        "connected": True,
        "provider": provider,
        "scopes": token.get("scopes", []),
        "expired": is_expired,
        "expires_at": token.get("expires_at"),
    }


@router.get("/settings")
async def get_integration_settings(
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Get all integration settings for current user."""
    settings = IntegrationSettingsService.list_user_integrations(user.user_id)

    return {
        "settings": settings,
    }


@router.post("/settings")
async def save_integration_settings(
    request: IntegrationSettingsRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Save integration settings."""
    result = IntegrationSettingsService.save_settings(
        user_id=user.user_id,
        integration_type=request.integration_type,
        settings=request.settings,
        project_id=request.project_id,
        enabled=request.enabled,
    )

    return {
        "status": "success",
        "settings": result,
    }


@router.patch("/settings/{integration_type}/toggle")
async def toggle_integration(
    integration_type: str,
    enabled: bool,
    project_id: Optional[int] = None,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Enable or disable an integration."""
    success = IntegrationSettingsService.toggle_integration(
        user_id=user.user_id,
        integration_type=integration_type,
        enabled=enabled,
        project_id=project_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {
        "status": "success",
        "integration_type": integration_type,
        "enabled": enabled,
    }


@router.get("/google/token")
async def get_google_oauth_token(
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """
    Get Google OAuth access token from Clerk.

    This endpoint fetches the OAuth access token for Google from Clerk's Backend API.
    The token can be used to access Google APIs (Calendar, Gmail, Docs, etc.).
    """
    if not CLERK_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Clerk secret key not configured"
        )

    async with httpx.AsyncClient() as client:
        try:
            # Fetch OAuth access tokens from Clerk Backend API
            response = await client.get(
                f"https://api.clerk.com/v1/users/{user.user_id}/oauth_access_tokens/oauth_google",
                headers={
                    "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                    "Content-Type": "application/json",
                }
            )

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Google account not connected. Please sign in with Google first."
                )

            response.raise_for_status()
            data = response.json()

            if not data or len(data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No Google OAuth tokens found"
                )

            # Return the first (most recent) token
            token_data = data[0]

            return {
                "access_token": token_data.get("token"),
                "scopes": token_data.get("scopes", []),
                "provider": "google",
                "token_secret": token_data.get("token_secret"),  # For OAuth 1.0 providers
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Google account not connected"
                )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch Google token from Clerk: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching Google token: {str(e)}"
            )


@router.get("/google/user-info")
async def get_google_user_info(
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """
    Get Google user info using the OAuth token from Clerk.
    Useful for verifying the connection works.
    """
    # First get the token
    token_response = await get_google_oauth_token(user)
    access_token = token_response.get("access_token")

    if not access_token:
        raise HTTPException(status_code=404, detail="No Google token available")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to fetch Google user info"
            )


@router.post("/google/sync-token")
async def sync_google_token_to_backend(
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """
    Sync Google OAuth token from Clerk to local storage.

    This fetches the token from Clerk and saves it locally for use
    by background services that don't have access to Clerk session.
    """
    # Get token from Clerk
    token_response = await get_google_oauth_token(user)
    access_token = token_response.get("access_token")
    scopes = token_response.get("scopes", [])

    if not access_token:
        raise HTTPException(status_code=404, detail="No Google token available")

    # Save to local token storage
    # Note: Clerk tokens don't have refresh tokens accessible via API
    # They are managed by Clerk automatically
    result = TokenService.save_token(
        user_id=user.user_id,
        provider="google",
        access_token=access_token,
        refresh_token=None,  # Clerk manages refresh
        scopes=scopes,
        expires_at=datetime.now() + timedelta(hours=1),  # Clerk tokens typically last 1 hour
    )

    return {
        "status": "success",
        "message": "Google token synced to backend",
        "scopes": scopes,
    }
