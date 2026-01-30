# Flowable MVP

**Task Management + Monitoring/Incident Response**

Kombinace Trello-style kanban boardu s Betterstack-style monitoringem a incident managementem.

## Features

### Task Management
- **Kanban Board** - Drag & drop mezi sloupci (Backlog, To Do, In Progress, Done)
- **Priority levels** - High, Medium, Low s barevným rozlišením
- **Due dates** - Sledování termínů

### Monitoring
- **Health Checks** - Automatické kontroly URL každých 30-60 sekund
- **Uptime tracking** - Response time, status code, uptime percentage
- **Auto-incidents** - Automatické vytváření incidentů při výpadku

### Incident Management
- **Incident workflow** - Open → Acknowledged → Resolved
- **Severity levels** - Warning, Critical
- **Timeline tracking** - Kdy vznikl, kdy potvrzen, kdy vyřešen

### Audit Log
- **Disaster Recovery** - Kompletní log všech akcí
- **Old/New values** - Uložení stavu před a po změně
- **Activity tracking** - Přehled aktivity za 24h

## Tech Stack

**Backend:**
- FastAPI + Python 3.11+
- SQLite database
- httpx pro health checks
- APScheduler pro background jobs

**Frontend:**
- Vue 3 + TypeScript
- Vite build tool
- Vue Router
- Tokyo Night theme

## Quick Start

```bash
# Backend (terminal 1)
just be

# Frontend (terminal 2)
just fe
```

Otevři http://localhost:5173

## API Endpoints

### Tasks
```
GET    /api/tasks              # List all tasks
POST   /api/tasks              # Create task
GET    /api/tasks/{id}         # Get task
PUT    /api/tasks/{id}         # Update task
PUT    /api/tasks/{id}/move    # Move task (drag & drop)
DELETE /api/tasks/{id}         # Delete task
```

### Columns
```
GET    /api/columns            # List columns
POST   /api/columns            # Create column
PUT    /api/columns/{id}       # Update column
DELETE /api/columns/{id}       # Delete column
```

### Monitors
```
GET    /api/monitors           # List monitors
POST   /api/monitors           # Create monitor
POST   /api/monitors/{id}/check # Run check now
GET    /api/monitors/{id}/metrics # Get metrics
DELETE /api/monitors/{id}      # Delete monitor
```

### Incidents
```
GET    /api/incidents          # List incidents
GET    /api/incidents/open     # List open incidents
POST   /api/incidents          # Create incident
POST   /api/incidents/{id}/acknowledge # Acknowledge
POST   /api/incidents/{id}/resolve     # Resolve
```

### Dashboard & Audit
```
GET    /api/dashboard          # Dashboard summary
GET    /api/audit              # Audit log
GET    /api/audit/stats        # Audit statistics
```

## Project Structure

```
flowable/
├── apps/
│   ├── backend/
│   │   ├── main.py              # FastAPI app
│   │   ├── database.py          # DB connection
│   │   ├── init_db.py           # Schema + seed data
│   │   ├── routers/
│   │   │   ├── tasks.py
│   │   │   ├── columns.py
│   │   │   ├── monitors.py
│   │   │   ├── incidents.py
│   │   │   ├── audit.py
│   │   │   └── dashboard.py
│   │   └── services/
│   │       ├── audit_service.py
│   │       └── monitor_service.py
│   └── frontend/
│       └── src/
│           ├── App.vue
│           ├── router/index.ts
│           ├── composables/useApi.ts
│           └── views/
│               ├── DashboardView.vue
│               ├── BoardView.vue
│               ├── MonitorsView.vue
│               ├── IncidentsView.vue
│               └── AuditView.vue
├── justfile
└── README.md
```

## Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- uv (Python package manager)
- just (command runner)

### Commands

```bash
just          # List all commands
just be       # Run backend
just fe       # Run frontend
just test     # Run tests
just health   # Check API health
just backup   # Backup database
just reset    # Clean slate
```

### Testing

```bash
# Backend tests
cd apps/backend && uv run pytest -v

# Manual API test
curl http://localhost:8000/api/dashboard | jq
```

## License

MIT
