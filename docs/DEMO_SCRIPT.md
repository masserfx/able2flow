# Flowable MVP - Demo Script

**Délka:** 5-7 minut

---

## Úvod (30s)

> "Flowable je MVP kombinující task management ve stylu Trello s monitoringem a incident managementem podobným Betterstack. Vytvořeno za 5 hodin jako proof of concept."

**Ukázat:** Dashboard overview

---

## 1. Kanban Board (1:30)

### Vytvoření tasku
1. Klik na "Board" v navigaci
2. Klik "+ New Task"
3. Vyplnit: "Implementovat login" → vybrat "To Do"
4. Klik "Add Task"

### Drag & Drop
1. Přetáhnout task z "To Do" do "In Progress"
2. Ukázat, že se pozice aktualizovala

### Dokončení tasku
1. Zaškrtnout checkbox u tasku
2. Přetáhnout do "Done"

> "Každá akce je automaticky logována do audit logu pro disaster recovery."

---

## 2. Monitoring (1:30)

### Přehled monitorů
1. Klik na "Monitors"
2. Ukázat 3 demo monitory (API, Google, GitHub)
3. Ukázat status badges (up/down)

### Ruční check
1. Klik "Check Now" u Google monitoru
2. Ukázat response time a status code

### Přidání monitoru
1. Klik "+ New Monitor"
2. Vyplnit: "My Website" / "https://example.com" / 60s
3. Klik "Add"

> "Monitoring běží na pozadí a automaticky kontroluje všechny URL každých 30 sekund."

---

## 3. Incident Management (1:30)

### Vytvoření incidentu
1. Klik na "Incidents"
2. Klik "+ Report Incident"
3. Vyplnit: "Database connection timeout" / Critical
4. Klik "Report"

### Workflow
1. Ukázat incident s badges (critical, open)
2. Klik "Acknowledge" - ukázat timestamp
3. Klik "Resolve" - ukázat resolved_at

### Filtrování
1. Klik na "Open" tab - prázdné
2. Klik na "Resolved" tab - resolved incident
3. Klik na "All" - všechny

> "Incidenty se automaticky vytvářejí, když monitor detekuje výpadek, a automaticky se resolvují při obnovení."

---

## 4. Dashboard (45s)

1. Klik na "Dashboard"
2. Ukázat:
   - Tasks completed (progress bar)
   - Uptime 24h percentage
   - Open incidents count
   - Activity count

3. Ukázat sekce:
   - Tasks by Status (po sloupcích)
   - Open Incidents (nebo "All systems operational")
   - Monitors status (up/down/unknown)
   - Tasks by Priority

> "Dashboard poskytuje real-time přehled o stavu projektu i infrastruktury."

---

## 5. Audit Log (45s)

1. Klik na "Audit Log"
2. Ukázat timeline:
   - Různé akce (create, update, move, resolve)
   - Barevné rozlišení podle typu
   - Relativní časy (5m ago, 1h ago)

3. Scrollovat a ukázat historii

> "Kompletní audit log umožňuje disaster recovery - každá změna je zaznamenána včetně původní a nové hodnoty."

---

## 6. API Demo (30s)

```bash
# Health check
curl http://localhost:8000/health

# Dashboard data
curl http://localhost:8000/api/dashboard

# Audit log
curl http://localhost:8000/api/audit
```

> "Celá aplikace je postavena na REST API, které můžete integrovat s dalšími nástroji."

---

## Závěr (30s)

### Co je hotové:
- Kanban board s drag & drop
- Health monitoring s automatickými checks
- Incident management s workflow
- Kompletní audit log
- Dashboard s metrikami

### Další kroky:
- Autentizace
- WebSocket real-time updates
- Email notifikace
- Integrace s externími službami

> "Flowable MVP demonstruje, jak rychle lze vytvořit funkční aplikaci kombinující task management s DevOps monitoringem."

---

## Technické poznámky

- **Backend:** FastAPI + SQLite + httpx
- **Frontend:** Vue 3 + TypeScript + Vite
- **Theme:** Tokyo Night
- **Čas vývoje:** 5 hodin
