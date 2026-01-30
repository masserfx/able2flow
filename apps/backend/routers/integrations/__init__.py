"""Integration routers for Google and Slack services."""

from .calendar import router as calendar_router
from .docs import router as docs_router
from .gmail import router as gmail_router
from .slack import router as slack_router
from .oauth import router as oauth_router

__all__ = [
    "calendar_router",
    "docs_router",
    "gmail_router",
    "slack_router",
    "oauth_router",
]
