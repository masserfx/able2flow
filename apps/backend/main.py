"""Able2Flow MVP - Task management + Monitoring/Incident response API."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (two levels up from apps/backend)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from routers import tasks, columns, monitors, incidents, audit, dashboard, ai, sla, events, projects, attachments
from routers.integrations import calendar_router, docs_router, gmail_router, slack_router, oauth_router
from services.monitor_service import monitor_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize database and start background monitor checks
    from init_db import init_database
    init_database()

    # Start background monitoring task
    task = asyncio.create_task(monitor_service.start_background_checks())

    yield

    # Shutdown: Stop background tasks and close connections
    monitor_service.stop_background_checks()
    task.cancel()
    await monitor_service.close()


app = FastAPI(
    title="Able2Flow API",
    description="Task management + Monitoring/Incident response with AI-powered triage, SLA tracking, and event sourcing",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS for frontend
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router)
app.include_router(columns.router)
app.include_router(monitors.router)
app.include_router(incidents.router)
app.include_router(audit.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(sla.router)
app.include_router(events.router)
app.include_router(projects.router)
app.include_router(attachments.router)

# Integration routers
app.include_router(oauth_router)
app.include_router(calendar_router)
app.include_router(docs_router)
app.include_router(gmail_router)
app.include_router(slack_router)


@app.get("/")
def root() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Able2Flow API is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health() -> dict:
    """Detailed health check."""
    from database import get_db

    db_status = "ok"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "monitoring": "active",
    }


# Legacy endpoints for backward compatibility
@app.get("/tasks")
def legacy_list_tasks():
    """Legacy endpoint - redirects to /api/tasks."""
    return tasks.list_tasks()


@app.get("/tasks/{task_id}")
def legacy_get_task(task_id: int):
    """Legacy endpoint - redirects to /api/tasks/{id}."""
    return tasks.get_task(task_id)


@app.post("/tasks")
def legacy_create_task(task: tasks.TaskCreate):
    """Legacy endpoint - redirects to /api/tasks."""
    return tasks.create_task(task)


@app.put("/tasks/{task_id}")
def legacy_update_task(task_id: int, task: tasks.TaskUpdate):
    """Legacy endpoint - redirects to /api/tasks/{id}."""
    return tasks.update_task(task_id, task)


@app.delete("/tasks/{task_id}")
def legacy_delete_task(task_id: int):
    """Legacy endpoint - redirects to /api/tasks/{id}."""
    return tasks.delete_task(task_id)
