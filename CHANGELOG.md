# Changelog

All notable changes to Able2Flow.

## [0.3.0] - 2026-01-30

### Added

#### Multi-Project Support
- **Projects**: Each project has its own kanban board, tasks, monitors, and incidents
- **Project Selector**: Dropdown in sidebar to switch between projects
- **Data Isolation**: All data filtered by project context
- **Default Columns**: New projects auto-created with 4 default columns
- New endpoints:
  - `GET /api/projects`
  - `POST /api/projects`
  - `GET /api/projects/{id}`
  - `PUT /api/projects/{id}`
  - `DELETE /api/projects/{id}`

#### Internationalization (i18n)
- **Czech Localization**: Full Czech translation with diacritics
- **English Localization**: Complete English translation
- **Language Switcher**: Toggle between 🇨🇿 CZ and 🇬🇧 EN
- **Translated Elements**:
  - Navigation menu
  - Dashboard labels and stats
  - Kanban column names (K řešení, Připraveno, Probíhá, Hotovo)
  - Monitor status badges
  - Incident workflow buttons
  - Audit log actions
- **Persistence**: Language preference saved to localStorage

### Changed
- All API endpoints support optional `project_id` query parameter
- Database schema updated with `project_id` foreign keys
- Frontend uses Vue 3 provide/inject for project context
- API version bumped to 0.3.0

---

## [0.2.0] - 2026-01-30

### Added

#### AI-Powered Incident Triage
- **Claude API Integration**: Automatic incident analysis using Anthropic Claude
- **Root Cause Hypothesis**: AI generates possible causes based on context
- **Runbook Suggestions**: Automatic step-by-step remediation guides
- **Auto-Triage**: Confidence-based automatic severity updates
- **Fallback Analysis**: Rule-based analysis when API unavailable
- New endpoints:
  - `POST /api/ai/incidents/{id}/analyze`
  - `POST /api/ai/incidents/{id}/auto-triage`
  - `GET /api/ai/incidents/{id}/runbook`

#### SLA Tracking & Reporting
- **Uptime Monitoring**: Track against 99.9% SLA target
- **Response Time Percentiles**: p50, p95, p99 calculations
- **MTTA Tracking**: Mean Time To Acknowledge (15min target)
- **MTTR Tracking**: Mean Time To Recovery (4h target)
- **Health Score**: Combined 0-100 system health metric
- **SLA Reports**: Comprehensive compliance reporting
- New endpoints:
  - `GET /api/sla/report`
  - `GET /api/sla/health-score`
  - `GET /api/sla/monitors/{id}/uptime`
  - `GET /api/sla/monitors/{id}/response-times`
  - `GET /api/sla/incidents/mtta`
  - `GET /api/sla/incidents/mttr`

#### Event Sourcing & Time Travel
- **Entity History**: Complete change history for all entities
- **Time Travel**: Reconstruct entity state at any timestamp
- **Event Replay**: Step through changes incrementally
- **State Diff**: Compare entity between two points in time
- **Disaster Recovery**: Restore entities to previous state
- **Activity Feed**: Real-time feed across all entities
- New endpoints:
  - `GET /api/events/feed`
  - `GET /api/events/{type}/{id}/history`
  - `GET /api/events/{type}/{id}/state-at`
  - `GET /api/events/{type}/{id}/replay`
  - `GET /api/events/{type}/{id}/diff`
  - `POST /api/events/{type}/{id}/restore`

#### Testing
- 11 new tests for advanced features
- Total test count: 27 (all passing)

### Changed
- Project renamed from Flowable to Able2Flow
- API version bumped to 0.2.0
- Enhanced API description

---

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
