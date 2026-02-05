# Plan: Incident Templates (Quick Win)

## Task Description
Implementovat Incident Templates feature, která umožní uživatelům rychle vytvářet incidenty z předdefinovaných šablon. Šablony obsahují předvyplněné hodnoty pro často se opakující typy incidentů (Database slow, API timeout, High CPU usage, Low disk space, SSL expiry).

## Objective
Snížit čas potřebný k vytvoření incidentu z ~3 minut na ~30 sekund (83% improvement) pomocí dropdown selectoru s 5 předdefinovanými šablonami a automatickým vyplněním formuláře.

## Problem Statement
Uživatelé musí ručně vyplňovat stejné incidenty opakovaně (Database slow, API timeout, High CPU atd.), což vede k:
- Vysokému time-to-report (~3 minuty)
- Typografickým chybám v názvech a popisech
- Nekonzistentní severity klasifikaci
- Zbytečnému manuálnímu úsilí při rutinních incidentech

## Solution Approach
Přidat template selector dropdown nad existující incident creation form v IncidentsView.vue, který po výběru šablony automaticky vyplní pole \`title\`, \`severity\` a (nový) \`description\`. Uživatel může hodnoty upravit před odesláním.

Backend poskytne statický seznam 5 templates přes nový GET \`/api/incidents/templates\` endpoint. Templates jsou definovány jako konstanty (ne v databázi) pro rychlou implementaci quick win feature.

## Relevant Files

### Existing Files to Modify:
- **apps/backend/routers/incidents.py** - Přidat templates endpoint a description support
- **apps/frontend/src/views/IncidentsView.vue** - Přidat template selector UI
- **apps/frontend/src/composables/useApi.ts** - Přidat getIncidentTemplates()
- **apps/backend/init_db.py** - Migration pro description column

### New Files:
Žádné nové soubory - vše se implementuje do existujících.

## Step by Step Tasks

### 1. Backend: Přidat Description Column (DB Migration)
- Upravit \`apps/backend/init_db.py\` v \`_run_migrations()\`
- Přidat migration pro description column

### 2. Backend: Definovat Templates Konstantu
- V \`apps/backend/routers/incidents.py\` přidat INCIDENT_TEMPLATES
- 5 šablon: db-slow, api-timeout, high-cpu, disk-space, ssl-expiry

### 3. Backend: Přidat GET /templates Endpoint
- Endpoint vrací \`{"templates": INCIDENT_TEMPLATES}\`

### 4. Backend: Aktualizovat Models
- IncidentCreate: přidat description field
- Incident: přidat description field
- row_to_incident(): přidat description do return

### 5. Backend: Aktualizovat create_incident()
- INSERT query zahrnuje description field

### 6. Frontend: Aktualizovat useApi
- Přidat IncidentTemplate interface
- Přidat getIncidentTemplates() metodu
- Aktualizovat Incident interface s description

### 7. Frontend: Template Selector UI
- Přidat templates state, selectedTemplate state
- Rozšířit newIncident o description
- Implementovat applyTemplate() funkci
- V onMounted načíst templates

### 8. Frontend: Template Dropdown
- Přidat select element s templates
- Přidat description textarea
- Aktualizovat createIncident() pro description

### 9. Frontend: i18n Translations
- Přidat template, customIncident, description do en.json
- Přidat template, customIncident, description do cs.json

### 10. Frontend: Zobrazit Description
- V incident card/list přidat description rendering
- Přidat CSS pro incident-description

### 11. Testing
- Test backend API: curl /api/incidents/templates
- Test DB migration: sqlite3 check description column
- Test frontend: template selection a auto-fill
- E2E test: vytvoření incidentu s template

## Acceptance Criteria
- [ ] GET /api/incidents/templates vrací 5 templates
- [ ] Template selector dropdown v UI
- [ ] Auto-fill funguje při výběru šablony
- [ ] Description field v incidents
- [ ] Time-to-create < 30s
- [ ] i18n funguje (CS + EN)
- [ ] Žádné errory v konzoli

## Validation Commands
\`\`\`bash
# Test backend API
curl http://localhost:8000/api/incidents/templates | jq

# Verify DB migration
sqlite3 apps/backend/starter.db "PRAGMA table_info(incidents);" | grep description

# Run servers
just be  # backend
just fe  # frontend
\`\`\`

## Notes
**Complexity:** Low (2 days)
**Success Metric:** Time-to-report 3min → 30s (83% improvement)
