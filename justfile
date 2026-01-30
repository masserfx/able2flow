# Able2Flow MVP - Task Management + Monitoring
set dotenv-load := true

# List all recipes
default:
  @just --list

# Install and run frontend
fe:
  cd apps/frontend && npm install && npm run dev

# Install and run backend
be:
  cd apps/backend && uv sync && uv run uvicorn main:app --reload

# Run both frontend and backend (in separate terminals)
dev:
  @echo "Run in separate terminals:"
  @echo "  just be  # Backend on :8000"
  @echo "  just fe  # Frontend on :5173"

# Initialize/reset database
init-db:
  cd apps/backend && uv run python -c "from init_db import init_database; init_database()"

# Run backend tests
test:
  cd apps/backend && uv run pytest -v

# Health check for API
health:
  @curl -s http://localhost:8000/health | python3 -m json.tool || echo "API not running"

# Get dashboard summary
dashboard:
  @curl -s http://localhost:8000/api/dashboard | python3 -m json.tool || echo "API not running"

# Check all monitors
check-monitors:
  @curl -s -X POST http://localhost:8000/api/monitors/1/check | python3 -m json.tool || echo "API not running"

# Backup database
backup:
  @mkdir -p backups
  @cp apps/backend/starter.db "backups/starter_$(date +%Y%m%d_%H%M%S).db"
  @echo "Database backed up to backups/"

# Reset artifacts (clean slate)
reset:
  rm -rf apps/backend/.venv
  rm -rf apps/backend/starter.db
  rm -rf apps/frontend/node_modules
  rm -rf .claude/hooks/*.log
  rm -rf app_docs/install_results.md
  rm -rf app_docs/maintenance_results.md

# Deterministic codebase setup
cldi:
  claude --model opus --dangerously-skip-permissions --init

# Deterministic codebase maintenance
cldm:
  claude --model opus --dangerously-skip-permissions --maintenance

# Agentic codebase setup
cldii:
  claude --model opus --dangerously-skip-permissions --init "/install"

# Agentic codebase setup interactive
cldit:
  claude --model opus --dangerously-skip-permissions --init "/install true"

# Agentic codebase maintenance
cldmm:
  claude --model opus --dangerously-skip-permissions --maintenance "/maintenance"
