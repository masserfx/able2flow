# Able2Flow MVP

**Task Management + Monitoring/Incident Response**

Kombinace Trello-style kanban boardu s Betterstack-style monitoringem a incident managementem.

## Landing Page

Aplikace obsahuje interaktivní landing page (`/`) s kompletním přehledem funkcí:
- **Hero sekce** - Rychlý přehled s mockupem aplikace
- **Features** - Detailní popis všech funkcí
- **Tech Stack** - Použité technologie (Frontend + Backend)
- **AI Integration** - Ukázka AI-powered triage
- **Extensions** - Plánované a aktivní integrace
- **PDF Export** - Stažení popisu aplikace jako PDF (podpora češtiny s diakritikou)

## Features

### AI-Powered Incident Triage (Game Changer)
- **Auto-analysis** - Claude API analyzes incidents and suggests severity
- **Root cause hypothesis** - AI identifies possible causes
- **Runbook suggestions** - Automatic remediation steps
- **Confidence scoring** - AI indicates certainty of analysis

### SLA Tracking & Reporting
- **Uptime monitoring** - Track 99.9% SLA targets
- **Response time percentiles** - p50, p95, p99 tracking
- **MTTA/MTTR metrics** - Mean time to acknowledge/recover
- **Health score** - Single 0-100 score for system health

### Event Sourcing & Time Travel
- **Complete history** - Every change is recorded
- **Time travel** - Reconstruct state at any point
- **Event replay** - Step through changes
- **Disaster recovery** - Restore entities to previous state

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

### 1. Environment Setup

```bash
# Backend
cp .env.sample .env
# Edit .env with your API keys

# Frontend
cp apps/frontend/.env.sample apps/frontend/.env
# Edit with your Clerk publishable key
```

### 2. Run the App

```bash
# Backend (terminal 1)
just be

# Frontend (terminal 2)
just fe
```

Open http://localhost:5173

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLERK_SECRET_KEY` | Yes | Clerk authentication |
| `GOOGLE_CLIENT_ID` | For integrations | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | For integrations | Google OAuth |
| `ANTHROPIC_API_KEY` | For AI | AI triage feature |
| `SLACK_BOT_TOKEN` | For Slack | Slack notifications |
| `CORS_ORIGINS` | Production | Comma-separated origins |
| `SEED_DATA` | Optional | Set to "false" in production |

## Integrations

### Google Calendar
- Two-way sync between tasks and calendar
- Task due dates create calendar events
- Deleted/cancelled events mark tasks as completed

### Google Docs
- Link documents to tasks
- Create docs from task descriptions

### Slack
- Incident notifications to channels
- Slash commands: `/able2flow create [task]`

### File Attachments
- Upload files to tasks (max 10MB)
- Supported: images, documents, archives
- **Inline preview** - SVG, PNG, JPG thumbnails in kanban cards and task modal
- **PDF preview** - Open PDF files directly in browser
- Correct MIME types via `/preview` endpoint

### ANT HILL Gamification
- **Task Marketplace** - Pull-based system, workers choose their tasks
- **Time Tracking** - Built-in stopwatch per task
- **Points System** - 1 point = 10 min estimated time
- **Bonuses** - Speed (+20%), deadline (+10%), priority (critical +5, high +3)
- **Leaderboard** - Daily, weekly, monthly, all-time rankings
- **Notifications** - Real-time toast + bell notifications
- **Clerk Auth** - Real user identity (no mock data), auto-registration from Clerk

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

### Attachments
```
POST   /api/tasks/{id}/attachments           # Upload attachment
GET    /api/attachments/{id}/download         # Download file
GET    /api/attachments/{id}/preview          # Preview with correct MIME type
DELETE /api/attachments/{id}                  # Delete attachment
```

### Gamification
```
POST   /api/tasks/{id}/assign                # Claim task (marketplace)
POST   /api/tasks/{id}/release               # Release task
POST   /api/time-tracking/start              # Start timer
POST   /api/time-tracking/stop               # Stop timer
GET    /api/time-tracking/active             # Active time log
GET    /api/gamification/leaderboard         # Leaderboard
GET    /api/gamification/user/{id}/points    # User points
GET    /api/notifications/{user_id}          # Notifications
POST   /api/notifications/{id}/read          # Mark as read
GET    /api/tasks/marketplace                # Available tasks
```

### Dashboard & Audit
```
GET    /api/dashboard          # Dashboard summary
GET    /api/audit              # Audit log
GET    /api/audit/stats        # Audit statistics
```

### AI Triage
```
POST   /api/ai/incidents/{id}/analyze    # AI analysis
GET    /api/ai/incidents/{id}/runbook    # Suggested runbook
POST   /api/ai/incidents/{id}/auto-triage # Full auto-triage
```

### SLA Reporting
```
GET    /api/sla/report                   # Full SLA report
GET    /api/sla/health-score             # System health 0-100
GET    /api/sla/monitors/{id}/uptime     # Monitor uptime
GET    /api/sla/incidents/mtta           # Mean Time To Acknowledge
GET    /api/sla/incidents/mttr           # Mean Time To Recovery
```

### Event Sourcing
```
GET    /api/events/feed                  # Activity feed
GET    /api/events/{type}/{id}/history   # Entity history
GET    /api/events/{type}/{id}/state-at  # Time travel
GET    /api/events/{type}/{id}/replay    # Event replay
POST   /api/events/{type}/{id}/restore   # Restore entity
```

## Project Structure

```
able2flow/
├── apps/
│   ├── backend/
│   │   ├── main.py              # FastAPI app
│   │   ├── database.py          # DB connection
│   │   ├── init_db.py           # Schema + migrations
│   │   ├── auth/                # Clerk authentication
│   │   ├── routers/
│   │   │   ├── tasks.py
│   │   │   ├── columns.py
│   │   │   ├── monitors.py
│   │   │   ├── incidents.py
│   │   │   ├── attachments.py
│   │   │   └── integrations/    # Google, Slack APIs
│   │   └── services/
│   │       ├── audit_service.py
│   │       ├── monitor_service.py
│   │       └── integrations/    # Calendar, Docs, Gmail
│   └── frontend/
│       └── src/
│           ├── App.vue
│           ├── plugins/clerk.ts
│           ├── composables/
│           │   ├── useApi.ts
│           │   ├── useAuth.ts
│           │   └── useIntegrations.ts
│           ├── components/
│           │   ├── TaskModal.vue
│           │   ├── AppIcon.vue         # SVG icon library
│           │   ├── TimeTracker.vue     # Stopwatch component
│           │   ├── NotificationBell.vue
│           │   ├── PointsBadge.vue
│           │   └── IntegrationCard.vue
│           └── views/
│               ├── LandingView.vue       # Landing page
│               ├── DashboardView.vue
│               ├── BoardView.vue
│               ├── IntegrationsView.vue
│               └── ...
├── .env.sample          # Environment template
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
