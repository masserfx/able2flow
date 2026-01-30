# Changelog

All notable changes to Flowable MVP.

## [0.1.0] - 2026-01-30

### Added

#### Backend
- FastAPI application with router structure
- SQLite database with tables: tasks, columns, monitors, incidents, metrics, audit_log
- **Tasks API**: CRUD + move endpoint for drag & drop
- **Columns API**: Kanban column management
- **Monitors API**: Health check monitors with manual check trigger
- **Incidents API**: Create, acknowledge, resolve workflow
- **Audit API**: Complete action logging with old/new values
- **Dashboard API**: Aggregated statistics
- Background monitoring service with automatic health checks
- Automatic incident creation/resolution based on monitor status

#### Frontend
- Vue 3 + TypeScript + Vite setup
- Tokyo Night dark theme
- Vue Router with 5 views:
  - **Dashboard**: Stats overview, open incidents, task distribution
  - **Board**: Kanban board with drag & drop
  - **Monitors**: Health monitor management with live checks
  - **Incidents**: Incident timeline with acknowledge/resolve
  - **Audit**: Activity log timeline
- Responsive sidebar navigation
- API composable for all endpoints

#### Infrastructure
- justfile with development commands
- uv for Python dependency management
- Demo data seeding (tasks, columns, monitors)

### MVP Features Completed
- [x] Kanban Board with drag & drop
- [x] Audit Log for disaster recovery
- [x] Health Monitoring with auto-checks
- [x] Dashboard with key metrics
- [x] Incident Management workflow

### Skipped for MVP
- Authentication/Authorization
- WebSocket real-time updates
- Email notifications
- Complex MCP integrations
