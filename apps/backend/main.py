"""Able2Flow MVP - Task management + Monitoring/Incident response API."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tasks, columns, monitors, incidents, audit, dashboard
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
    description="Task management + Monitoring/Incident response MVP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
