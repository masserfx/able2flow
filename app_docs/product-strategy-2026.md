# Able2Flow - Strategický Dokument 2026

**Verze:** 1.0
**Datum:** Leden 2026
**Autor:** Product Strategy Team

---

## 1. Executive Summary

### 1.1 Positioning

Able2Flow je **první hybrid task management + monitoring/incident response aplikace s AI-powered triage**. Kombinuje:

- **Task Management** (Trello-style kanban board)
- **Health Monitoring** (Betterstack-style uptime tracking)
- **AI Incident Triage** (Claude-powered analysis, runbook suggestions, root cause hypothesis)

### 1.2 Unique Selling Point

**Jediná aplikace na trhu**, která integruje:
1. Task management s prioritami a due dates
2. Automated health monitoring (30-60s checks)
3. **AI-powered incident analysis** - auto-severity, confidence scoring, multi-language (CS/EN)
4. Event sourcing & time travel (disaster recovery)
5. SLA tracking (MTTA/MTTR, uptime percentiles p50/p95/p99)

**Konkurenční výhoda**: Žádná jiná aplikace neposkytuje AI triage pro incidenty s takovou úrovní integrace.

### 1.3 Klíčová Zjištění

**Strengths:**
- ✅ AI triage je **game changer** - unique feature
- ✅ Multi-language support (CS/EN) - rare v této kategorii
- ✅ Event sourcing poskytuje complete audit trail
- ✅ Integrace s Google Calendar/Docs, Slack

**Gaps:**
- ❌ **Chybí observability dashboard** (žádná vizualizace metrik v čase)
- ❌ Žádné collaboration features (comments, @mentions)
- ❌ Omezený search (žádný global search Cmd+K)
- ❌ Mobile experience není optimalizována
- ❌ Bulk operations nejsou podporovány

### 1.4 Strategic Priorities H1 2026

1. **Quick Wins** (5 features, 2-3 týdny) - Incident templates, context menu, notifications
2. **Observability Dashboard** (2 týdny) - Metric visualization, agent performance tracking
3. **Collaboration MVP** (2 týdny) - Comments, @mentions, activity feed
4. **PostgreSQL Migration** (1 týden) - Scalability pro 100+ concurrent users
5. **Mobile PWA** (3 týdny) - Offline-first progressive web app

---

## 2. Quick Wins (High ROI, Low Effort)

### Feature 1: Incident Templates

**Problém**: Users musí ručně vyplňovat stejné incidenty opakovaně (Database slow, API timeout, High CPU).

**Řešení**: Pre-filled incident templates s dropdownem v IncidentsView.

**Wireframe:**
```
┌─────────────────────────────────────────────┐
│ New Incident                            [X] │
├─────────────────────────────────────────────┤
│ Template: [Database Slow Query ▼]           │
│                                             │
│ Title: Database response time > 5s          │
│ Severity: [Critical ▼]                      │
│ Description: (auto-filled)                  │
│   Database queries taking longer than 5s.   │
│   Check slow query log and index usage.     │
│                                             │
│ [Create Incident]                           │
└─────────────────────────────────────────────┘
```

**Code Snippet (Vue 3 + TypeScript):**

```typescript
// IncidentsView.vue
<script setup lang="ts">
import { ref } from 'vue'

interface IncidentTemplate {
  id: string
  name: string
  title: string
  severity: 'warning' | 'critical'
  description: string
}

const templates: IncidentTemplate[] = [
  {
    id: 'db-slow',
    name: 'Database Slow Query',
    title: 'Database response time > 5s',
    severity: 'critical',
    description: 'Database queries taking longer than 5s. Check slow query log and index usage.'
  },
  {
    id: 'api-timeout',
    name: 'API Timeout',
    title: 'API endpoint timeout',
    severity: 'critical',
    description: 'External API not responding within timeout threshold (10s).'
  },
  {
    id: 'high-cpu',
    name: 'High CPU Usage',
    title: 'CPU usage above 80%',
    severity: 'warning',
    description: 'Server CPU usage sustained above 80% for 5+ minutes.'
  },
  {
    id: 'disk-space',
    name: 'Low Disk Space',
    title: 'Disk space < 10%',
    severity: 'warning',
    description: 'Available disk space below 10%. Consider cleanup or expansion.'
  },
  {
    id: 'ssl-expiry',
    name: 'SSL Certificate Expiring',
    title: 'SSL certificate expires in <30 days',
    severity: 'warning',
    description: 'SSL certificate nearing expiration. Renew before expiry date.'
  }
]

const selectedTemplate = ref<string>('')
const newIncident = ref({ title: '', severity: 'warning', description: '' })

function applyTemplate(templateId: string) {
  const template = templates.find(t => t.id === templateId)
  if (template) {
    newIncident.value = {
      title: template.title,
      severity: template.severity,
      description: template.description
    }
  }
}
</script>

<template>
  <div class="new-form card">
    <div class="form-group">
      <label>Template (optional)</label>
      <select v-model="selectedTemplate" @change="applyTemplate(selectedTemplate)">
        <option value="">Custom incident</option>
        <option v-for="t in templates" :key="t.id" :value="t.id">
          {{ t.name }}
        </option>
      </select>
    </div>

    <div class="form-group">
      <input v-model="newIncident.title" placeholder="Incident title" />
    </div>

    <div class="form-group">
      <select v-model="newIncident.severity">
        <option value="warning">Warning</option>
        <option value="critical">Critical</option>
      </select>
    </div>

    <div class="form-group">
      <textarea
        v-model="newIncident.description"
        placeholder="Description"
        rows="4"
      />
    </div>

    <button @click="createIncident">Create Incident</button>
  </div>
</template>
```

**Backend API:**
```python
# routers/incidents.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

INCIDENT_TEMPLATES = [
    {
        "id": "db-slow",
        "name": "Database Slow Query",
        "title": "Database response time > 5s",
        "severity": "critical",
        "description": "Database queries taking longer than 5s. Check slow query log and index usage."
    },
    # ... more templates
]

@router.get("/templates")
def get_incident_templates():
    """List all incident templates."""
    return {"templates": INCIDENT_TEMPLATES}
```

**Metrics:**
- **Time-to-report**: 3 min → 30s (83% improvement)
- **User errors**: -70% (fewer typos, consistent naming)
- **Template adoption**: Expected 60% of incidents

**Effort:** Low (2 dny)

---

### Feature 2: Quick Actions Context Menu

**Problém**: Users musí klikat na task card, otevřít modal, pak provést akci. Slow workflow.

**Řešení**: Right-click context menu přímo na task cardech.

**Wireframe:**
```
┌──────────────────────────┐
│ ☰ High Priority          │
│ Database migration       │ ← Right-click here
│                          │
│ Due: Jan 15              │
└──────────────────────────┘
         ↓
┌──────────────────────────┐
│ Duplicate Task           │
│ Move to Project...       │
│ Convert to Incident      │
│ Change Priority  ▶       │
│ Archive                  │
│ ──────────────────       │
│ Delete                   │
└──────────────────────────┘
```

**Code Snippet:**

```typescript
// components/TaskCard.vue
<script setup lang="ts">
import { ref } from 'vue'
import { useContextMenu } from '../composables/useContextMenu'

const props = defineProps<{ task: Task }>()
const emit = defineEmits(['duplicate', 'move', 'convert', 'archive', 'delete'])

const contextMenu = ref<{ x: number; y: number; visible: boolean }>({
  x: 0,
  y: 0,
  visible: false
})

function showContextMenu(event: MouseEvent) {
  event.preventDefault()
  contextMenu.value = {
    x: event.clientX,
    y: event.clientY,
    visible: true
  }
}

function closeContextMenu() {
  contextMenu.value.visible = false
}

function handleAction(action: string) {
  emit(action, props.task.id)
  closeContextMenu()
}
</script>

<template>
  <div class="task-card" @contextmenu="showContextMenu">
    <!-- Task card content -->

    <Teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <div class="context-item" @click="handleAction('duplicate')">
          <span class="icon">📋</span> Duplicate Task
        </div>
        <div class="context-item" @click="handleAction('move')">
          <span class="icon">📁</span> Move to Project...
        </div>
        <div class="context-item" @click="handleAction('convert')">
          <span class="icon">⚡</span> Convert to Incident
        </div>
        <div class="context-item submenu">
          <span class="icon">🔖</span> Change Priority ▶
          <!-- Submenu -->
        </div>
        <div class="context-divider" />
        <div class="context-item" @click="handleAction('archive')">
          <span class="icon">📦</span> Archive
        </div>
        <div class="context-item danger" @click="handleAction('delete')">
          <span class="icon">🗑️</span> Delete
        </div>
      </div>
    </Teleport>

    <!-- Backdrop to close menu -->
    <div
      v-if="contextMenu.visible"
      class="context-backdrop"
      @click="closeContextMenu"
    />
  </div>
</template>

<style scoped>
.context-menu {
  position: fixed;
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  min-width: 200px;
  padding: 4px;
  z-index: 9999;
}

.context-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
}

.context-item:hover {
  background: var(--bg-highlight);
}

.context-item.danger {
  color: var(--accent-red);
}

.context-divider {
  height: 1px;
  background: var(--border-color);
  margin: 4px 0;
}

.context-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
}
</style>
```

**Backend Support:**
```python
# routers/tasks.py

@router.post("/{task_id}/duplicate")
def duplicate_task(task_id: int):
    """Create a copy of task."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        original = cursor.fetchone()

        conn.execute("""
            INSERT INTO tasks (title, description, priority, column_id, project_id)
            VALUES (?, ?, ?, ?, ?)
        """, (f"{original['title']} (Copy)", original['description'],
              original['priority'], original['column_id'], original['project_id']))
        conn.commit()

        return {"success": True}

@router.post("/{task_id}/convert-to-incident")
def convert_task_to_incident(task_id: int):
    """Convert task to incident."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()

        conn.execute("""
            INSERT INTO incidents (title, severity, status, started_at)
            VALUES (?, ?, ?, ?)
        """, (task['title'], 'warning', 'open', datetime.now()))
        conn.commit()

        return {"success": True}
```

**Metrics:**
- **User productivity**: +40% (fewer clicks)
- **Task operations**: 5 clicks → 2 clicks (60% reduction)
- **Feature discovery**: +80% (contextual actions visible)

**Effort:** Low (3 dny)

---

### Feature 3: Smart Notifications

**Problém**: Users musí manuálně checkovat dashboard pro critical incidents. Missed SLA alerts.

**Řešení**: Desktop push notifications s priority-based filtering.

**Wireframe:**
```
┌────────────────────────────────────┐
│ 🔴 Able2Flow - Critical Incident   │
├────────────────────────────────────┤
│ Database response time > 5s        │
│                                    │
│ Severity: Critical                 │
│ Started: 2 minutes ago             │
│                                    │
│ [Acknowledge]  [View Details]      │
└────────────────────────────────────┘
```

**Code Snippet:**

```typescript
// services/notificationService.ts
class NotificationService {
  private permissionGranted = false

  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications')
      return false
    }

    if (Notification.permission === 'granted') {
      this.permissionGranted = true
      return true
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission()
      this.permissionGranted = permission === 'granted'
      return this.permissionGranted
    }

    return false
  }

  showIncidentNotification(incident: Incident) {
    if (!this.permissionGranted) return

    const severity = incident.severity === 'critical' ? '🔴' : '⚠️'

    const notification = new Notification(`${severity} Able2Flow - ${incident.severity} Incident`, {
      body: incident.title,
      icon: '/logo.png',
      badge: '/badge.png',
      tag: `incident-${incident.id}`, // Prevents duplicates
      requireInteraction: incident.severity === 'critical', // Stays until clicked
      actions: [
        { action: 'acknowledge', title: 'Acknowledge' },
        { action: 'view', title: 'View Details' }
      ]
    })

    notification.onclick = () => {
      window.focus()
      // Navigate to incident details
      window.location.href = `/incidents?id=${incident.id}`
      notification.close()
    }
  }

  showTaskDeadlineNotification(task: Task) {
    if (!this.permissionGranted) return

    const notification = new Notification('📅 Task Due Soon', {
      body: `"${task.title}" is due in 1 hour`,
      icon: '/logo.png',
      tag: `task-deadline-${task.id}`
    })

    notification.onclick = () => {
      window.focus()
      window.location.href = `/board?task=${task.id}`
      notification.close()
    }
  }
}

export const notificationService = new NotificationService()
```

**Integration with WebSocket:**
```typescript
// App.vue
import { onMounted } from 'vue'
import { notificationService } from './services/notificationService'
import { useWebSocket } from './composables/useWebSocket'

onMounted(async () => {
  // Request notification permission on app load
  await notificationService.requestPermission()

  // Listen for real-time incident events
  const ws = useWebSocket()
  ws.on('incident:created', (incident) => {
    notificationService.showIncidentNotification(incident)
  })

  ws.on('incident:severity-upgraded', (incident) => {
    if (incident.severity === 'critical') {
      notificationService.showIncidentNotification(incident)
    }
  })
})
```

**User Settings:**
```typescript
// Settings page
<script setup lang="ts">
import { ref } from 'vue'

const notificationSettings = ref({
  enabled: true,
  criticalIncidents: true,
  warningIncidents: false,
  taskDeadlines: true,
  deadlineThreshold: 60 // minutes
})

function saveSettings() {
  localStorage.setItem('notification-settings', JSON.stringify(notificationSettings.value))
}
</script>

<template>
  <div class="settings-section">
    <h3>🔔 Notifications</h3>

    <div class="setting-item">
      <label>
        <input type="checkbox" v-model="notificationSettings.enabled" />
        Enable desktop notifications
      </label>
    </div>

    <div class="setting-item" v-if="notificationSettings.enabled">
      <label>
        <input type="checkbox" v-model="notificationSettings.criticalIncidents" />
        Critical incidents
      </label>
    </div>

    <div class="setting-item" v-if="notificationSettings.enabled">
      <label>
        <input type="checkbox" v-model="notificationSettings.warningIncidents" />
        Warning incidents
      </label>
    </div>

    <div class="setting-item" v-if="notificationSettings.enabled">
      <label>
        <input type="checkbox" v-model="notificationSettings.taskDeadlines" />
        Task deadline reminders
      </label>
    </div>

    <button @click="saveSettings">Save Settings</button>
  </div>
</template>
```

**Metrics:**
- **Response time**: -50% (immediate awareness)
- **Missed critical incidents**: 0 (real-time alerts)
- **MTTA (Mean Time To Acknowledge)**: 15 min → 3 min

**Effort:** Medium (4 dny)

---

### Feature 4: Global Search (Cmd+K)

**Problém**: Users musí manuálně navigovat mezi views pro hledání tasks/incidents/monitors.

**Řešení**: Command palette s fuzzy search across all entities.

**Wireframe:**
```
Cmd+K ↓
┌────────────────────────────────────────────┐
│ 🔍 Search tasks, incidents, monitors...    │
├────────────────────────────────────────────┤
│ 📋 Database migration task          (Task) │
│ ⚡ Database response > 5s        (Incident) │
│ 🖥️ Production API Monitor        (Monitor) │
│ 📁 Backend Project                (Project) │
└────────────────────────────────────────────┘
```

**Code Snippet:**

```typescript
// components/GlobalSearch.vue
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Fuse from 'fuse.js' // Fuzzy search library

interface SearchResult {
  type: 'task' | 'incident' | 'monitor' | 'project'
  id: number
  title: string
  subtitle?: string
  icon: string
}

const router = useRouter()
const visible = ref(false)
const query = ref('')
const selectedIndex = ref(0)
const allItems = ref<SearchResult[]>([])

// Keyboard shortcut
function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    visible.value = !visible.value
    if (visible.value) query.value = ''
  }

  if (!visible.value) return

  if (e.key === 'Escape') {
    visible.value = false
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = Math.min(selectedIndex.value + 1, searchResults.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    selectResult(searchResults.value[selectedIndex.value])
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  await loadAllItems()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

async function loadAllItems() {
  const [tasks, incidents, monitors, projects] = await Promise.all([
    fetch('/api/tasks').then(r => r.json()),
    fetch('/api/incidents').then(r => r.json()),
    fetch('/api/monitors').then(r => r.json()),
    fetch('/api/projects').then(r => r.json())
  ])

  allItems.value = [
    ...tasks.map((t: any) => ({
      type: 'task',
      id: t.id,
      title: t.title,
      subtitle: t.column_name,
      icon: '📋'
    })),
    ...incidents.map((i: any) => ({
      type: 'incident',
      id: i.id,
      title: i.title,
      subtitle: `${i.severity} - ${i.status}`,
      icon: '⚡'
    })),
    ...monitors.map((m: any) => ({
      type: 'monitor',
      id: m.id,
      title: m.name,
      subtitle: m.url,
      icon: '🖥️'
    })),
    ...projects.map((p: any) => ({
      type: 'project',
      id: p.id,
      title: p.name,
      subtitle: `${p.task_count || 0} tasks`,
      icon: '📁'
    }))
  ]
}

const fuse = computed(() => new Fuse(allItems.value, {
  keys: ['title', 'subtitle'],
  threshold: 0.3, // Fuzzy match threshold
  includeScore: true
}))

const searchResults = computed(() => {
  if (!query.value) return allItems.value.slice(0, 10)

  return fuse.value
    .search(query.value)
    .slice(0, 10)
    .map(result => result.item)
})

function selectResult(result: SearchResult) {
  if (!result) return

  visible.value = false

  switch (result.type) {
    case 'task':
      router.push(`/board?task=${result.id}`)
      break
    case 'incident':
      router.push(`/incidents?id=${result.id}`)
      break
    case 'monitor':
      router.push(`/monitors?id=${result.id}`)
      break
    case 'project':
      router.push(`/board?project=${result.id}`)
      break
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="search-overlay" @click.self="visible = false">
      <div class="search-modal">
        <div class="search-input-wrapper">
          <span class="search-icon">🔍</span>
          <input
            v-model="query"
            type="text"
            placeholder="Search tasks, incidents, monitors..."
            class="search-input"
            autofocus
          />
          <kbd class="search-hint">ESC</kbd>
        </div>

        <div class="search-results">
          <div
            v-for="(result, index) in searchResults"
            :key="`${result.type}-${result.id}`"
            :class="['search-result', { selected: index === selectedIndex }]"
            @click="selectResult(result)"
            @mouseenter="selectedIndex = index"
          >
            <span class="result-icon">{{ result.icon }}</span>
            <div class="result-content">
              <div class="result-title">{{ result.title }}</div>
              <div class="result-subtitle">{{ result.subtitle }}</div>
            </div>
            <span class="result-type">{{ result.type }}</span>
          </div>

          <div v-if="searchResults.length === 0" class="search-empty">
            No results found for "{{ query }}"
          </div>
        </div>

        <div class="search-footer">
          <kbd>↑↓</kbd> Navigate
          <kbd>⏎</kbd> Select
          <kbd>ESC</kbd> Close
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 10vh;
  z-index: 10000;
}

.search-modal {
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  gap: 0.75rem;
}

.search-icon {
  font-size: 1.25rem;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 1rem;
  color: var(--text-primary);
}

.search-hint {
  padding: 0.25rem 0.5rem;
  background: var(--bg-highlight);
  border-radius: 4px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.search-results {
  max-height: 400px;
  overflow-y: auto;
}

.search-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.15s;
}

.search-result:hover,
.search-result.selected {
  background: var(--bg-highlight);
}

.result-icon {
  font-size: 1.25rem;
}

.result-content {
  flex: 1;
}

.result-title {
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 500;
}

.result-subtitle {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.result-type {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: var(--bg-dark);
  border-radius: 4px;
  color: var(--text-muted);
  text-transform: uppercase;
}

.search-empty {
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
}

.search-footer {
  display: flex;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border-color);
  font-size: 0.75rem;
  color: var(--text-muted);
}

.search-footer kbd {
  padding: 0.25rem 0.5rem;
  background: var(--bg-highlight);
  border-radius: 4px;
  font-family: monospace;
}
</style>
```

**Metrics:**
- **Task discovery**: +300% (instant access)
- **Navigation time**: 8 clicks → 2 keystrokes
- **User satisfaction**: Expected +60%

**Effort:** Medium (5 dní)

---

### Feature 5: Bulk Operations

**Problém**: Users musí upravovat tasks/incidents one-by-one. Time consuming for batch operations.

**Řešení**: Multi-select checkboxes s bulk action toolbar.

**Wireframe:**
```
Select mode: ON
┌─────────────────────────────────────────┐
│ [✓] 3 items selected                    │
│ [Change Priority ▼] [Move] [Archive]   │
└─────────────────────────────────────────┘

Board:
□ ☑ High Priority - Database migration
□ ☑ Medium Priority - Update docs
□ ☑ Low Priority - Refactor tests
□ ☐ High Priority - Deploy to prod
```

**Code Snippet:**

```typescript
// BoardView.vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const tasks = ref<Task[]>([])
const selectedTaskIds = ref<Set<number>>(new Set())
const bulkMode = ref(false)

const selectedTasks = computed(() =>
  tasks.value.filter(t => selectedTaskIds.value.has(t.id))
)

function toggleBulkMode() {
  bulkMode.value = !bulkMode.value
  if (!bulkMode.value) {
    selectedTaskIds.value.clear()
  }
}

function toggleTask(taskId: number) {
  if (selectedTaskIds.value.has(taskId)) {
    selectedTaskIds.value.delete(taskId)
  } else {
    selectedTaskIds.value.add(taskId)
  }
}

function selectAll() {
  tasks.value.forEach(t => selectedTaskIds.value.add(t.id))
}

function deselectAll() {
  selectedTaskIds.value.clear()
}

async function bulkChangePriority(priority: string) {
  await Promise.all(
    Array.from(selectedTaskIds.value).map(id =>
      fetch(`/api/tasks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priority })
      })
    )
  )

  selectedTaskIds.value.clear()
  await loadTasks()
}

async function bulkArchive() {
  await Promise.all(
    Array.from(selectedTaskIds.value).map(id =>
      fetch(`/api/tasks/${id}/archive`, { method: 'POST' })
    )
  )

  selectedTaskIds.value.clear()
  await loadTasks()
}

async function bulkDelete() {
  if (!confirm(`Delete ${selectedTaskIds.value.size} tasks?`)) return

  await Promise.all(
    Array.from(selectedTaskIds.value).map(id =>
      fetch(`/api/tasks/${id}`, { method: 'DELETE' })
    )
  )

  selectedTaskIds.value.clear()
  await loadTasks()
}
</script>

<template>
  <div class="board-view">
    <header class="board-header">
      <h1>Board</h1>
      <button @click="toggleBulkMode">
        {{ bulkMode ? '✕ Exit Bulk Mode' : '☑ Bulk Mode' }}
      </button>
    </header>

    <!-- Bulk Action Toolbar -->
    <Transition name="slide-down">
      <div v-if="bulkMode && selectedTaskIds.size > 0" class="bulk-toolbar">
        <div class="bulk-info">
          ☑ {{ selectedTaskIds.size }} items selected
        </div>

        <div class="bulk-actions">
          <select @change="bulkChangePriority($event.target.value)">
            <option value="">Change Priority</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <button @click="bulkArchive">📦 Archive</button>
          <button @click="bulkDelete" class="danger">🗑️ Delete</button>
        </div>

        <div class="bulk-controls">
          <button @click="selectAll">Select All</button>
          <button @click="deselectAll">Deselect All</button>
        </div>
      </div>
    </Transition>

    <!-- Kanban Columns -->
    <div class="kanban-board">
      <div v-for="column in columns" :key="column.id" class="kanban-column">
        <h2>{{ column.name }}</h2>

        <div
          v-for="task in getTasksInColumn(column.id)"
          :key="task.id"
          class="task-card"
          :class="{ selected: selectedTaskIds.has(task.id) }"
        >
          <input
            v-if="bulkMode"
            type="checkbox"
            :checked="selectedTaskIds.has(task.id)"
            @change="toggleTask(task.id)"
            class="task-checkbox"
          />

          <div class="task-content">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-priority">{{ task.priority }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bulk-toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.bulk-info {
  font-weight: 600;
  color: var(--accent-blue);
}

.bulk-actions {
  display: flex;
  gap: 0.5rem;
  flex: 1;
}

.bulk-controls {
  display: flex;
  gap: 0.5rem;
}

.task-card {
  position: relative;
  transition: all 0.2s;
}

.task-card.selected {
  border: 2px solid var(--accent-blue);
  background: rgba(122, 162, 247, 0.1);
}

.task-checkbox {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
```

**Backend Support:**
```python
# routers/tasks.py

@router.post("/bulk/archive")
def bulk_archive_tasks(task_ids: list[int]):
    """Archive multiple tasks."""
    with get_db() as conn:
        conn.execute(
            f"UPDATE tasks SET archived = 1 WHERE id IN ({','.join('?' * len(task_ids))})",
            task_ids
        )
        conn.commit()

    return {"success": True, "archived_count": len(task_ids)}

@router.post("/bulk/update-priority")
def bulk_update_priority(task_ids: list[int], priority: str):
    """Update priority for multiple tasks."""
    with get_db() as conn:
        conn.execute(
            f"UPDATE tasks SET priority = ? WHERE id IN ({','.join('?' * len(task_ids))})",
            [priority] + task_ids
        )
        conn.commit()

    return {"success": True, "updated_count": len(task_ids)}
```

**Metrics:**
- **Batch processing**: +500% efficiency
- **Time savings**: 20 operations × 10s = 3.3 min → 20s (90% faster)
- **User frustration**: -75%

**Effort:** Medium (4 dny)

---

## 3. Strategic Initiatives (2-4 weeks each)

### Initiative 1: Observability Dashboard

**Současný Stav**: DashboardView zobrazuje pouze static stat cards bez historical data nebo trendů.

**Cíl**: Kompletní observability dashboard s real-time metrics, agent performance tracking, cost analysis, a event heatmap.

**Inspirace**: Datadog, Betterstack, Grafana

**MVP Features:**

#### 3.1 Metric Cards (Enhanced)

```typescript
// components/MetricCard.vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { Line } from 'vue-chartjs'

const props = defineProps<{
  title: string
  value: number
  unit: string
  sparklineData: number[] // Last 24 hours
  trend: 'up' | 'down' | 'stable'
  trendValue: number // Percentage change
}>()

const trendColor = computed(() => {
  if (props.trend === 'up') return 'var(--accent-green)'
  if (props.trend === 'down') return 'var(--accent-red)'
  return 'var(--text-muted)'
})

const chartData = computed(() => ({
  labels: Array(props.sparklineData.length).fill(''),
  datasets: [{
    data: props.sparklineData,
    borderColor: 'var(--accent-blue)',
    borderWidth: 2,
    fill: false,
    tension: 0.4,
    pointRadius: 0
  }]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { display: false },
    y: { display: false }
  }
}
</script>

<template>
  <div class="metric-card">
    <div class="metric-header">
      <span class="metric-title">{{ title }}</span>
      <span class="metric-trend" :style="{ color: trendColor }">
        {{ trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→' }}
        {{ Math.abs(trendValue) }}%
      </span>
    </div>

    <div class="metric-value">
      {{ value }}<span class="metric-unit">{{ unit }}</span>
    </div>

    <div class="metric-sparkline">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
```

#### 3.2 Agent Performance Table

```
┌──────────────────────────────────────────────────────────┐
│ Agent Performance (Last 24h)                             │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│ Agent    │ Tasks    │ Avg Time │ Success  │ Cost         │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│ Claude   │ 45       │ 2.3s     │ 97%      │ $3.20        │
│ Webhook  │ 120      │ 0.8s     │ 99%      │ $0.00        │
│ Monitor  │ 2,880    │ 0.5s     │ 98%      │ $0.00        │
└──────────┴──────────┴──────────┴──────────┴──────────────┘
```

#### 3.3 Cost Tracking Chart

```typescript
// views/ObservabilityView.vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'

const costData = ref({
  labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  datasets: [{
    label: 'AI Triage Cost',
    data: [2.5, 3.1, 2.8, 4.2, 3.9, 1.2, 0.8],
    backgroundColor: 'rgba(187, 154, 247, 0.5)',
    borderColor: '#bb9af7',
    borderWidth: 2
  }]
})

const chartOptions = {
  responsive: true,
  plugins: {
    title: {
      display: true,
      text: 'AI Usage Cost (Last 7 Days)'
    },
    tooltip: {
      callbacks: {
        label: (context) => `$${context.parsed.y.toFixed(2)}`
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value) => `$${value}`
      }
    }
  }
}
</script>

<template>
  <div class="observability-view">
    <h1>📊 Observability Dashboard</h1>

    <!-- Metric Cards Grid -->
    <div class="metrics-grid">
      <MetricCard
        title="Tasks Completed"
        :value="156"
        unit=""
        :sparklineData="[120, 135, 142, 150, 156]"
        trend="up"
        :trendValue="15"
      />
      <MetricCard
        title="Avg Response Time"
        :value="245"
        unit="ms"
        :sparklineData="[280, 265, 250, 240, 245]"
        trend="down"
        :trendValue="12"
      />
      <MetricCard
        title="Uptime"
        :value="99.8"
        unit="%"
        :sparklineData="[99.5, 99.7, 99.8, 99.8, 99.8]"
        trend="stable"
        :trendValue="0.3"
      />
      <MetricCard
        title="AI Cost (24h)"
        :value="3.20"
        unit="$"
        :sparklineData="[2.5, 3.1, 2.8, 4.2, 3.2]"
        trend="down"
        :trendValue="24"
      />
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <div class="chart-card">
        <Bar :data="costData" :options="chartOptions" />
      </div>

      <div class="chart-card">
        <h3>Event Heatmap (Last 7 Days)</h3>
        <div class="heatmap">
          <!-- Calendar heatmap component -->
        </div>
      </div>
    </div>

    <!-- Agent Performance Table -->
    <div class="table-card">
      <h3>Agent Performance</h3>
      <table class="performance-table">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Operations</th>
            <th>Avg Duration</th>
            <th>Success Rate</th>
            <th>Cost (24h)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>🤖 Claude AI</td>
            <td>45</td>
            <td>2.3s</td>
            <td><span class="badge success">97%</span></td>
            <td>$3.20</td>
          </tr>
          <tr>
            <td>🔗 Webhook Handler</td>
            <td>120</td>
            <td>0.8s</td>
            <td><span class="badge success">99%</span></td>
            <td>$0.00</td>
          </tr>
          <tr>
            <td>📊 Health Monitor</td>
            <td>2,880</td>
            <td>0.5s</td>
            <td><span class="badge success">98%</span></td>
            <td>$0.00</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
```

**Backend API:**
```python
# routers/observability.py
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from database import get_db

router = APIRouter(prefix="/api/observability", tags=["observability"])

@router.get("/metrics")
def get_observability_metrics(
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d")
):
    """Get aggregated metrics for observability dashboard."""

    hours = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}[time_range]
    start_time = datetime.now() - timedelta(hours=hours)

    with get_db() as conn:
        # Task completion trend
        task_trend = conn.execute("""
            SELECT
                date(completed_at) as date,
                COUNT(*) as count
            FROM tasks
            WHERE completed_at >= ?
            GROUP BY date(completed_at)
            ORDER BY date
        """, (start_time,)).fetchall()

        # AI usage cost
        ai_cost = conn.execute("""
            SELECT
                date(created_at) as date,
                SUM(cost_usd) as total_cost
            FROM ai_usage_log
            WHERE created_at >= ?
            GROUP BY date(created_at)
        """, (start_time,)).fetchall()

        # Response time percentiles
        response_times = conn.execute("""
            SELECT response_time_ms
            FROM monitor_checks
            WHERE checked_at >= ?
            ORDER BY response_time_ms
        """, (start_time,)).fetchall()

        p50 = percentile(response_times, 50)
        p95 = percentile(response_times, 95)
        p99 = percentile(response_times, 99)

    return {
        "task_completion_trend": task_trend,
        "ai_cost_trend": ai_cost,
        "response_time_percentiles": {
            "p50": p50,
            "p95": p95,
            "p99": p99
        },
        "uptime_24h": calculate_uptime(start_time)
    }

@router.get("/agent-performance")
def get_agent_performance():
    """Get performance metrics for each agent type."""

    with get_db() as conn:
        agents = conn.execute("""
            SELECT
                agent_type,
                COUNT(*) as operation_count,
                AVG(duration_ms) as avg_duration,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                SUM(cost_usd) as total_cost
            FROM agent_operations
            WHERE created_at >= datetime('now', '-24 hours')
            GROUP BY agent_type
        """).fetchall()

    return {"agents": [dict(a) for a in agents]}
```

**Database Schema (New Tables):**
```sql
-- AI usage tracking
CREATE TABLE ai_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER,
    operation_type TEXT, -- analyze, suggest_runbook, auto_triage
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(id)
);

-- Agent operations tracking
CREATE TABLE agent_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT, -- claude, webhook, monitor, scheduler
    operation TEXT,
    entity_type TEXT,
    entity_id INTEGER,
    duration_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    cost_usd REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Architecture:**

```
┌─────────────────────────────────────────┐
│ ObservabilityView.vue                   │
│ ├── MetricCard (x4)                     │
│ ├── CostChart (Bar chart)               │
│ ├── EventHeatmap (Calendar)             │
│ └── AgentPerformanceTable               │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Backend: /api/observability/metrics     │
│ ├── Task completion trend               │
│ ├── AI cost aggregation                 │
│ ├── Response time percentiles           │
│ └── Agent performance stats             │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ SQLite Database                         │
│ ├── ai_usage_log (costs & tokens)      │
│ ├── agent_operations (performance)      │
│ └── monitor_checks (response times)     │
└─────────────────────────────────────────┘
```

**Success Metrics:**
- **MTTD (Mean Time To Detect)**: 10 min → 5 min (-50%)
- **Dashboard load time**: < 1s
- **Cost visibility**: 100% (complete AI spend tracking)
- **User adoption**: >80% teams check dashboard daily

**Effort:** 2 weeks (10 working days)

---

### Initiative 2: Advanced AI Features

**Cíl**: Rozšířit AI capabilities beyond basic triage s predictive alerts, incident correlation, a cost optimization.

#### 2.1 Predictive Incident Alerts

**Koncept**: Machine learning model predikuje incidents based on historical patterns.

```python
# services/predictive_ai_service.py
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class PredictiveIncidentService:
    """Predict potential incidents before they occur."""

    def __init__(self):
        self.model = self._load_model()

    def predict_incident_probability(self, monitor_id: int) -> dict:
        """
        Predict likelihood of incident in next 1 hour.

        Features:
        - Response time trend (last 6 data points)
        - Error rate (last 1 hour)
        - Time of day (peak hours have higher risk)
        - Day of week (weekends typically lower)
        - Recent incident frequency
        """

        with get_db() as conn:
            # Fetch recent monitor checks
            checks = conn.execute("""
                SELECT response_time_ms, status_code, checked_at
                FROM monitor_checks
                WHERE monitor_id = ?
                ORDER BY checked_at DESC
                LIMIT 20
            """, (monitor_id,)).fetchall()

            if len(checks) < 6:
                return {"probability": 0.0, "confidence": "low"}

            # Feature engineering
            response_times = [c['response_time_ms'] for c in checks[:6]]
            response_trend = np.polyfit(range(6), response_times, 1)[0]  # Slope

            error_rate = sum(1 for c in checks if c['status_code'] >= 400) / len(checks)

            now = datetime.now()
            hour_of_day = now.hour
            day_of_week = now.weekday()

            # Recent incident count
            recent_incidents = conn.execute("""
                SELECT COUNT(*) as count
                FROM incidents
                WHERE monitor_id = ?
                AND started_at >= datetime('now', '-7 days')
            """, (monitor_id,)).fetchone()['count']

            # Feature vector
            features = np.array([[
                response_trend,
                error_rate,
                hour_of_day,
                day_of_week,
                recent_incidents
            ]])

            # Predict
            probability = self.model.predict_proba(features)[0][1]  # Prob of incident

            confidence = "high" if probability > 0.7 else "medium" if probability > 0.4 else "low"

            return {
                "monitor_id": monitor_id,
                "incident_probability": round(probability, 3),
                "confidence": confidence,
                "contributing_factors": {
                    "response_trend": "increasing" if response_trend > 0 else "stable",
                    "error_rate": round(error_rate, 2),
                    "recent_incidents": recent_incidents
                },
                "recommendation": self._get_recommendation(probability)
            }

    def _get_recommendation(self, probability: float) -> str:
        if probability > 0.7:
            return "High risk detected. Consider proactive investigation."
        elif probability > 0.4:
            return "Elevated risk. Monitor closely for next hour."
        else:
            return "Normal operation. No immediate action needed."
```

**API Endpoint:**
```python
# routers/ai.py

@router.get("/monitors/{monitor_id}/predict-incident")
async def predict_incident(monitor_id: int):
    """Predict incident probability for monitor."""
    service = PredictiveIncidentService()
    return service.predict_incident_probability(monitor_id)
```

**Frontend Integration:**
```typescript
// MonitorsView.vue
<template>
  <div class="monitor-card">
    <div class="monitor-header">
      <h3>{{ monitor.name }}</h3>
      <span v-if="prediction?.incident_probability > 0.7" class="risk-badge high">
        ⚠️ High Risk: {{ (prediction.incident_probability * 100).toFixed(0) }}%
      </span>
    </div>

    <p v-if="prediction?.recommendation" class="recommendation">
      💡 {{ prediction.recommendation }}
    </p>
  </div>
</template>
```

#### 2.2 Incident Correlation

**Koncept**: AI finds related incidents to identify systemic issues.

```python
# services/correlation_service.py

class IncidentCorrelationService:
    """Find related incidents using semantic similarity."""

    async def find_related_incidents(self, incident_id: int, limit: int = 5) -> list:
        """
        Find incidents similar to given incident.

        Uses:
        - Semantic similarity (embeddings)
        - Time proximity
        - Severity matching
        """

        with get_db() as conn:
            incident = conn.execute(
                "SELECT * FROM incidents WHERE id = ?",
                (incident_id,)
            ).fetchone()

            # Get embedding for current incident
            current_embedding = await self._get_embedding(incident['title'])

            # Find similar incidents
            all_incidents = conn.execute("""
                SELECT id, title, severity, started_at
                FROM incidents
                WHERE id != ?
                AND started_at >= datetime('now', '-30 days')
            """, (incident_id,)).fetchall()

            similarities = []
            for other in all_incidents:
                other_embedding = await self._get_embedding(other['title'])
                similarity = self._cosine_similarity(current_embedding, other_embedding)

                # Boost similarity if same severity
                if other['severity'] == incident['severity']:
                    similarity *= 1.2

                similarities.append({
                    "incident_id": other['id'],
                    "title": other['title'],
                    "similarity_score": round(similarity, 3),
                    "started_at": other['started_at']
                })

            # Sort by similarity and return top N
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similarities[:limit]

    async def _get_embedding(self, text: str) -> list:
        """Get embedding vector from Claude API."""
        # Use Claude API to generate embeddings
        # Or use a dedicated embedding model
        pass
```

**UI Component:**
```typescript
// components/RelatedIncidents.vue
<template>
  <div class="related-incidents">
    <h4>🔗 Related Incidents</h4>

    <div v-for="related in relatedIncidents" :key="related.incident_id" class="related-item">
      <div class="similarity-score">
        {{ (related.similarity_score * 100).toFixed(0) }}% match
      </div>
      <div class="related-title">{{ related.title }}</div>
      <div class="related-date">{{ formatDate(related.started_at) }}</div>
    </div>

    <p v-if="relatedIncidents.length >= 3" class="pattern-alert">
      ⚠️ Pattern detected: {{ relatedIncidents.length }} similar incidents in past 30 days
    </p>
  </div>
</template>
```

#### 2.3 Cost Optimization

**Koncept**: Intelligent caching a rate limiting pro AI requests.

```python
# services/ai_cache_service.py
from functools import lru_cache
import hashlib

class AICacheService:
    """Cache AI responses to reduce costs."""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def cache_key(self, incident_title: str, language: str) -> str:
        """Generate cache key from incident title and language."""
        content = f"{incident_title}:{language}"
        return hashlib.md5(content.encode()).hexdigest()

    async def get_or_analyze(self, incident_id: int, language: str):
        """Get cached analysis or fetch new one."""

        with get_db() as conn:
            incident = conn.execute(
                "SELECT title FROM incidents WHERE id = ?",
                (incident_id,)
            ).fetchone()

        cache_key = self.cache_key(incident['title'], language)

        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_ttl:
                print(f"Cache HIT for incident {incident_id}")
                return {**cached['data'], 'cached': True, 'cost_saved': 0.05}

        # Cache miss - fetch from AI
        print(f"Cache MISS for incident {incident_id}")
        analysis = await ai_triage.analyze_incident(incident_id, language)

        # Store in cache
        self.cache[cache_key] = {
            'data': analysis,
            'timestamp': datetime.now()
        }

        return {**analysis, 'cached': False}

# Usage
cache_service = AICacheService()

@router.post("/incidents/{incident_id}/analyze")
async def analyze_incident_cached(incident_id: int, lang: str = "en"):
    """Cached AI analysis endpoint."""
    return await cache_service.get_or_analyze(incident_id, lang)
```

**Success Metrics:**
- **AI accuracy**: >85% (incident prediction)
- **Cost reduction**: -30% (via caching)
- **Cache hit rate**: >60%
- **Related incident discovery**: 4.2 avg per incident

**Effort:** 3 weeks

---

### Initiative 3: Collaboration Features

**Cíl**: Přidat commenting system, @mentions, a activity feed pro team collaboration.

#### 3.1 Comments na Tasks/Incidents

**Database Schema:**
```sql
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, -- 'task' | 'incident' | 'monitor'
    entity_id INTEGER NOT NULL,
    user_id TEXT NOT NULL, -- Clerk user ID
    user_name TEXT,
    user_avatar TEXT,
    content TEXT NOT NULL,
    mentions TEXT, -- JSON array of mentioned user IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_comments_entity ON comments(entity_type, entity_id);
CREATE INDEX idx_comments_user ON comments(user_id);
```

**Backend API:**
```python
# routers/comments.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from auth.clerk_auth import get_current_user

router = APIRouter(prefix="/api/comments", tags=["comments"])

class CreateComment(BaseModel):
    entity_type: str
    entity_id: int
    content: str
    mentions: list[str] = []

@router.post("/")
def create_comment(comment: CreateComment, user = Depends(get_current_user)):
    """Create a new comment."""

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO comments (entity_type, entity_id, user_id, user_name, content, mentions)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            comment.entity_type,
            comment.entity_id,
            user['id'],
            user['name'],
            comment.content,
            json.dumps(comment.mentions)
        ))
        conn.commit()

        comment_id = cursor.lastrowid

        # Send notifications to mentioned users
        for mentioned_user_id in comment.mentions:
            send_mention_notification(mentioned_user_id, comment_id)

        return {"id": comment_id, "success": True}

@router.get("/{entity_type}/{entity_id}")
def get_comments(entity_type: str, entity_id: int):
    """Get all comments for entity."""

    with get_db() as conn:
        comments = conn.execute("""
            SELECT *
            FROM comments
            WHERE entity_type = ?
            AND entity_id = ?
            AND deleted_at IS NULL
            ORDER BY created_at ASC
        """, (entity_type, entity_id)).fetchall()

    return {"comments": [dict(c) for c in comments]}
```

**Frontend Component:**
```typescript
// components/CommentsSection.vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const props = defineProps<{
  entityType: 'task' | 'incident' | 'monitor'
  entityId: number
}>()

const { user } = useAuth()
const comments = ref<Comment[]>([])
const newComment = ref('')
const mentioning = ref<string[]>([])

async function loadComments() {
  const response = await fetch(`/api/comments/${props.entityType}/${props.entityId}`)
  const data = await response.json()
  comments.value = data.comments
}

async function postComment() {
  if (!newComment.value.trim()) return

  await fetch('/api/comments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      entity_type: props.entityType,
      entity_id: props.entityId,
      content: newComment.value,
      mentions: mentioning.value
    })
  })

  newComment.value = ''
  mentioning.value = []
  await loadComments()
}

function handleAtSymbol() {
  // Show user mention dropdown
  // Parse @username from input
}

onMounted(loadComments)
</script>

<template>
  <div class="comments-section">
    <h4>💬 Comments ({{ comments.length }})</h4>

    <!-- Comments List -->
    <div class="comments-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <img :src="comment.user_avatar" class="avatar" />
        <div class="comment-content">
          <div class="comment-header">
            <span class="author">{{ comment.user_name }}</span>
            <span class="timestamp">{{ formatRelativeTime(comment.created_at) }}</span>
          </div>
          <div class="comment-body" v-html="renderMarkdown(comment.content)" />
        </div>
      </div>

      <div v-if="comments.length === 0" class="empty-state">
        No comments yet. Be the first to comment!
      </div>
    </div>

    <!-- New Comment Form -->
    <div class="comment-form">
      <img :src="user.avatar" class="avatar" />
      <textarea
        v-model="newComment"
        placeholder="Add a comment... (use @ to mention someone)"
        @keydown.meta.enter="postComment"
        @keydown.ctrl.enter="postComment"
        rows="3"
      />
      <button @click="postComment" :disabled="!newComment.trim()">
        Comment
      </button>
    </div>

    <div class="comment-hint">
      Press <kbd>Cmd</kbd> + <kbd>Enter</kbd> to post
    </div>
  </div>
</template>

<style scoped>
.comments-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border-color);
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.comment-item {
  display: flex;
  gap: 0.75rem;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

.comment-content {
  flex: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.author {
  font-weight: 600;
  color: var(--text-primary);
}

.timestamp {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.comment-body {
  color: var(--text-secondary);
  line-height: 1.5;
}

.comment-form {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.comment-form textarea {
  flex: 1;
  padding: 0.75rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  resize: vertical;
  font-family: inherit;
}

.comment-form textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.comment-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

kbd {
  padding: 0.125rem 0.375rem;
  background: var(--bg-highlight);
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.7rem;
}
</style>
```

#### 3.2 @Mentions s Real-time Notifications

```typescript
// composables/useMentions.ts
import { ref, computed } from 'vue'

export function useMentions() {
  const mentionQuery = ref('')
  const showMentionDropdown = ref(false)
  const cursorPosition = ref(0)

  // Team members (loaded from API)
  const teamMembers = ref([
    { id: 'user_123', name: 'John Doe', avatar: '/avatars/john.jpg' },
    { id: 'user_456', name: 'Jane Smith', avatar: '/avatars/jane.jpg' }
  ])

  const filteredMembers = computed(() => {
    if (!mentionQuery.value) return teamMembers.value

    const query = mentionQuery.value.toLowerCase()
    return teamMembers.value.filter(m =>
      m.name.toLowerCase().includes(query)
    )
  })

  function detectMention(text: string, caretPos: number) {
    const beforeCaret = text.substring(0, caretPos)
    const atIndex = beforeCaret.lastIndexOf('@')

    if (atIndex === -1) {
      showMentionDropdown.value = false
      return
    }

    const afterAt = beforeCaret.substring(atIndex + 1)

    // Check if there's a space after @ (invalid mention)
    if (afterAt.includes(' ')) {
      showMentionDropdown.value = false
      return
    }

    mentionQuery.value = afterAt
    showMentionDropdown.value = true
    cursorPosition.value = atIndex
  }

  function insertMention(member: any, text: string) {
    const beforeMention = text.substring(0, cursorPosition.value)
    const afterMention = text.substring(cursorPosition.value + mentionQuery.value.length + 1)

    showMentionDropdown.value = false
    return `${beforeMention}@${member.name} ${afterMention}`
  }

  return {
    showMentionDropdown,
    filteredMembers,
    detectMention,
    insertMention
  }
}
```

#### 3.3 Activity Feed

```python
# routers/activity.py

@router.get("/activity/feed")
def get_activity_feed(limit: int = 50, offset: int = 0):
    """
    Get unified activity feed.

    Includes:
    - Task updates
    - Incident status changes
    - Comments
    - Monitor alerts
    """

    with get_db() as conn:
        activities = conn.execute("""
            SELECT
                'task' as type,
                id,
                title,
                'updated' as action,
                updated_at as timestamp
            FROM tasks
            WHERE updated_at IS NOT NULL

            UNION ALL

            SELECT
                'incident' as type,
                id,
                title,
                status as action,
                updated_at as timestamp
            FROM incidents

            UNION ALL

            SELECT
                'comment' as type,
                id,
                content as title,
                'commented' as action,
                created_at as timestamp
            FROM comments

            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()

    return {"activities": [dict(a) for a in activities]}
```

**Success Metrics:**
- **Comments per task**: 2.5 average
- **@Mention response rate**: >80% within 1 hour
- **Activity feed engagement**: 60% daily active users

**Effort:** 2 weeks

---

### Initiative 4: Mobile PWA

**Cíl**: Progressive Web App s offline-first architecture a mobile-optimized UI.

#### 4.1 PWA Setup

```javascript
// vite.config.ts
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['logo.svg', 'robots.txt'],
      manifest: {
        name: 'Able2Flow',
        short_name: 'Able2Flow',
        description: 'Task Management + Incident Response with AI',
        theme_color: '#7aa2f7',
        background_color: '#1a1b26',
        display: 'standalone',
        icons: [
          {
            src: 'icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\./,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 300 // 5 minutes
              }
            }
          },
          {
            urlPattern: /\.(png|jpg|jpeg|svg|gif)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 86400 // 1 day
              }
            }
          }
        ]
      }
    })
  ]
})
```

#### 4.2 Offline Support

```typescript
// services/offlineService.ts
import { openDB, DBSchema } from 'idb'

interface OfflineDB extends DBSchema {
  tasks: {
    key: number
    value: Task
  }
  incidents: {
    key: number
    value: Incident
  }
  pending_actions: {
    key: number
    value: {
      id: number
      type: string
      payload: any
      timestamp: number
    }
  }
}

class OfflineService {
  private db: any

  async init() {
    this.db = await openDB<OfflineDB>('able2flow-offline', 1, {
      upgrade(db) {
        db.createObjectStore('tasks', { keyPath: 'id' })
        db.createObjectStore('incidents', { keyPath: 'id' })
        db.createObjectStore('pending_actions', { keyPath: 'id', autoIncrement: true })
      }
    })
  }

  async cacheTasks(tasks: Task[]) {
    const tx = this.db.transaction('tasks', 'readwrite')
    await Promise.all(tasks.map(task => tx.store.put(task)))
    await tx.done
  }

  async getCachedTasks(): Promise<Task[]> {
    return await this.db.getAll('tasks')
  }

  async queueAction(type: string, payload: any) {
    await this.db.add('pending_actions', {
      type,
      payload,
      timestamp: Date.now()
    })
  }

  async syncPendingActions() {
    const actions = await this.db.getAll('pending_actions')

    for (const action of actions) {
      try {
        // Replay action to server
        await fetch(`/api/${action.type}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(action.payload)
        })

        // Remove from queue
        await this.db.delete('pending_actions', action.id)
      } catch (error) {
        console.error('Failed to sync action:', error)
        // Keep in queue for retry
      }
    }
  }
}

export const offlineService = new OfflineService()
```

#### 4.3 Mobile-Optimized UI

```css
/* Mobile-first responsive design */

/* Touch-friendly hit areas */
.mobile-button {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 16px;
}

/* Swipe gestures */
.swipe-item {
  touch-action: pan-y;
  position: relative;
}

.swipe-item.swiping {
  transition: transform 0.2s;
}

.swipe-actions {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  display: flex;
  gap: 8px;
}

/* Mobile navigation */
@media (max-width: 768px) {
  .desktop-sidebar {
    display: none;
  }

  .mobile-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--bg-lighter);
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: space-around;
    padding: 8px;
    z-index: 100;
  }

  .mobile-nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 8px 16px;
    font-size: 0.75rem;
  }
}
```

**Success Metrics:**
- **Mobile traffic**: 15% → 55% (+267%)
- **PWA install rate**: >25%
- **Offline functionality**: 100% for cached data
- **Mobile session duration**: +40%

**Effort:** 3 weeks

---

### Initiative 5: Workflow Automation

**Cíl**: If-then rule engine pro automatizaci common workflows.

#### 5.1 Rule Builder UI

```
┌─────────────────────────────────────────────────┐
│ Create Automation Rule                          │
├─────────────────────────────────────────────────┤
│ When: [Incident created ▼]                      │
│       AND severity is [Critical ▼]              │
│                                                 │
│ Then: ✓ Create task in [Backend Project ▼]     │
│       ✓ Notify Slack channel [#incidents ▼]    │
│       ✓ Send email to [ops@company.com]        │
│                                                 │
│ [Save Rule]                                     │
└─────────────────────────────────────────────────┘
```

#### 5.2 Rule Engine

```python
# services/automation_service.py
from pydantic import BaseModel
from typing import Literal

class Condition(BaseModel):
    field: str  # e.g., 'severity', 'status', 'priority'
    operator: Literal['equals', 'not_equals', 'contains', 'greater_than']
    value: str

class Action(BaseModel):
    type: Literal['create_task', 'notify_slack', 'send_email', 'webhook']
    config: dict

class AutomationRule(BaseModel):
    id: int
    name: str
    trigger: Literal['incident_created', 'task_completed', 'monitor_down']
    conditions: list[Condition]
    actions: list[Action]
    enabled: bool

class AutomationService:
    """Execute automation rules."""

    def __init__(self):
        self.rules = self._load_rules()

    async def process_event(self, event_type: str, entity: dict):
        """Process event and execute matching rules."""

        matching_rules = [
            rule for rule in self.rules
            if rule.trigger == event_type and rule.enabled
        ]

        for rule in matching_rules:
            if self._evaluate_conditions(rule.conditions, entity):
                await self._execute_actions(rule.actions, entity)

    def _evaluate_conditions(self, conditions: list[Condition], entity: dict) -> bool:
        """Check if all conditions are met."""

        for condition in conditions:
            entity_value = entity.get(condition.field)

            if condition.operator == 'equals':
                if entity_value != condition.value:
                    return False
            elif condition.operator == 'contains':
                if condition.value.lower() not in str(entity_value).lower():
                    return False
            # ... more operators

        return True

    async def _execute_actions(self, actions: list[Action], entity: dict):
        """Execute all actions."""

        for action in actions:
            if action.type == 'create_task':
                await self._create_task(action.config, entity)
            elif action.type == 'notify_slack':
                await self._notify_slack(action.config, entity)
            elif action.type == 'send_email':
                await self._send_email(action.config, entity)
            elif action.type == 'webhook':
                await self._call_webhook(action.config, entity)

    async def _create_task(self, config: dict, entity: dict):
        """Create task from automation."""

        with get_db() as conn:
            conn.execute("""
                INSERT INTO tasks (title, description, priority, project_id, column_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"Follow-up: {entity['title']}",
                f"Auto-created from incident #{entity['id']}",
                config.get('priority', 'medium'),
                config['project_id'],
                config['column_id']
            ))
            conn.commit()

# Usage in incident creation
@router.post("/api/incidents")
async def create_incident(incident: CreateIncident):
    # ... create incident ...

    # Trigger automation
    automation_service = AutomationService()
    await automation_service.process_event('incident_created', dict(incident))

    return {"id": incident_id}
```

**Success Metrics:**
- **Automated workflows**: 50% of incidents
- **Time savings**: 15 min/incident → 30s
- **Rule adoption**: 3.5 rules per team (average)

**Effort:** 4 weeks

---

## 4. UI/UX Redesign Recommendations

### 4.1 DashboardView Improvements

**Current Issues:**
- Static stat cards without historical context
- No drill-down capability
- Limited interactivity

**Proposed Enhancements:**

```typescript
// Enhanced DashboardView.vue
<template>
  <div class="dashboard-v2">
    <!-- Interactive Metric Cards -->
    <div class="metrics-grid">
      <MetricCard
        title="Tasks Completed"
        :value="dashboard.tasks.completed"
        :total="dashboard.tasks.total"
        :sparkline="taskCompletionTrend"
        @click="navigateTo('/board')"
      >
        <template #tooltip>
          <div class="metric-tooltip">
            <h4>Task Completion Trend (7 days)</h4>
            <Line :data="taskTrendChart" />
          </div>
        </template>
      </MetricCard>
    </div>

    <!-- Drilldown Charts -->
    <div class="charts-section">
      <ChartCard title="Response Time Distribution" :loading="loading">
        <HistogramChart :data="responseTimeDistribution" />
      </ChartCard>

      <ChartCard title="Incident Timeline">
        <TimelineChart :events="incidentTimeline" />
      </ChartCard>
    </div>
  </div>
</template>
```

**Accessibility Enhancements:**
- **Keyboard navigation**: Tab through metric cards, Enter to drill-down
- **Screen reader labels**: ARIA labels for charts
- **High contrast mode**: Dedicated color palette

### 4.2 BoardView Enhancements

**Current Issues:**
- No inline editing
- Limited filtering
- No WIP limits

**Proposed Features:**

1. **Inline Priority Editor**: Click priority badge to change without opening modal
2. **Column WIP Limits**: Visual indicator when column exceeds limit
3. **Quick Filters**: Filter by priority, due date, assignee
4. **Larger Attachment Previews**: Thumbnail hover to preview image
5. **Mobile Swipe Gestures**: Swipe right to archive

```typescript
// Enhanced TaskCard
<template>
  <div
    class="task-card"
    @swiperight="handleSwipeArchive"
  >
    <div class="task-priority" @click.stop="showPriorityPicker = true">
      <span :class="['priority-badge', task.priority]">
        {{ task.priority }}
      </span>

      <Teleport v-if="showPriorityPicker" to="body">
        <div class="priority-picker">
          <button @click="changePriority('high')">High</button>
          <button @click="changePriority('medium')">Medium</button>
          <button @click="changePriority('low')">Low</button>
        </div>
      </Teleport>
    </div>

    <h3>{{ task.title }}</h3>

    <div v-if="task.attachments" class="attachments">
      <img
        v-for="att in task.attachments"
        :src="att.thumbnail_url"
        @mouseover="showPreview(att)"
        class="attachment-thumb"
      />
    </div>
  </div>
</template>
```

### 4.3 IncidentsView Redesign

**Enhanced AI Modal:**

```
┌────────────────────────────────────────────┐
│ 🤖 AI Triage Analysis                      │
├────────────────────────────────────────────┤
│                                            │
│ ┌────────────────────────────────────────┐ │
│ │ Severity Suggestion: CRITICAL          │ │
│ │ Confidence: ████████░░ 85%             │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ Root Cause:                                │
│  1. Database connection pool exhausted    │
│  2. High query load from reporting job    │
│                                            │
│ Recommended Actions:                       │
│  ☐ Step 1: Check connection pool size     │
│  ☐ Step 2: Review slow query log          │
│  ☐ Step 3: Scale up database instances    │
│                                            │
│ [Apply Recommendations] [Create Task]     │
└────────────────────────────────────────────┘
```

**Timeline View:**

```
Incident Timeline:
━━━━●━━━━━━━●━━━━━━━━━━━●━━━━━━━━━━━━→
    ↑         ↑            ↑
  Started  Acknowledged  Resolved
  14:23      14:28        14:55
  (Now)    (+5 min)     (+32 min)
```

### 4.4 Header/Sidebar Improvements

**Global Header:**
```
┌─────────────────────────────────────────────────────┐
│ 🔍 Cmd+K   Able2Flow   📁 Projects   🔔(3)   👤    │
└─────────────────────────────────────────────────────┘
```

**Notification Bell:**
- Badge with unread count
- Dropdown with recent notifications
- Mark all as read

---

## 5. Technical Debt & Architecture

### 5.1 PostgreSQL Migration

**Why:**
- SQLite má write locks → blocking na concurrent operations
- Transaction conflicts při high load
- Limited scalability (single file database)

**When:**
- At 100+ concurrent users
- When response time degradation detected

**Migration Plan:**

```bash
# Step 1: Schema export
sqlite3 able2flow.db .schema > schema.sql

# Step 2: Convert to PostgreSQL
# Manual conversion of SQLite-specific syntax

# Step 3: Data migration
python migrate_to_postgres.py

# Step 4: Update connection string
DATABASE_URL=postgresql://user:pass@localhost/able2flow
```

```python
# database.py (PostgreSQL version)
import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_pool():
    return await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)

@asynccontextmanager
async def get_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
```

**Impact:**
- Support 1000+ concurrent users
- Transaction throughput: 50 tx/s → 500 tx/s
- Zero downtime migration (blue-green deployment)

**Effort:** 1 week

---

### 5.2 Redis Caching

**Purpose:** Cache frequently accessed data (dashboard metrics, monitor status)

```python
# services/cache_service.py
import redis
import json

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def get_dashboard_data(self, project_id: int = None):
        """Get cached dashboard data."""

        cache_key = f"dashboard:{project_id or 'all'}"
        cached = self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Cache miss - fetch from DB
        data = self._fetch_dashboard_from_db(project_id)

        # Cache for 60 seconds
        self.redis.setex(cache_key, 60, json.dumps(data))

        return data

    def invalidate_dashboard_cache(self, project_id: int = None):
        """Invalidate cache when data changes."""

        cache_key = f"dashboard:{project_id or 'all'}"
        self.redis.delete(cache_key)
```

**Cache Invalidation Strategy:**
```python
# After task update
@router.put("/tasks/{task_id}")
async def update_task(task_id: int, task: UpdateTask):
    # ... update task ...

    # Invalidate dashboard cache
    cache_service.invalidate_dashboard_cache(task.project_id)

    return {"success": True}
```

**Impact:**
- Dashboard load time: 800ms → 120ms (-85%)
- Database load reduction: -70%
- Improved user experience (instant dashboard)

**Effort:** 3 dny

---

### 5.3 Frontend Bundle Optimization

**Current State:**
- Bundle size: ~2.4MB (uncompressed)
- First load time: ~3.5s

**Optimizations:**

#### Code Splitting
```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/dashboard',
    component: () => import('../views/DashboardView.vue') // Lazy load
  },
  {
    path: '/board',
    component: () => import('../views/BoardView.vue')
  },
  {
    path: '/incidents',
    component: () => import('../views/IncidentsView.vue')
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

#### Tree Shaking
```typescript
// Only import what you need
import { ref, computed } from 'vue' // ✅ Good
// import * as Vue from 'vue' // ❌ Bad
```

#### Image Optimization
```bash
# Install vite-plugin-imagemin
npm install vite-plugin-imagemin -D
```

```typescript
// vite.config.ts
import imagemin from 'vite-plugin-imagemin'

export default defineConfig({
  plugins: [
    imagemin({
      gifsicle: { optimizationLevel: 3 },
      mozjpeg: { quality: 80 },
      pngquant: { quality: [0.8, 0.9] },
      svgo: { plugins: [{ removeViewBox: false }] }
    })
  ]
})
```

**Impact:**
- Bundle size: 2.4MB → 850KB (-65%)
- First load: 3.5s → 1.2s (-66%)
- Lighthouse score: 75 → 95

**Effort:** 2 dny

---

### 5.4 Security Fixes

#### Rate Limiting
```python
# middleware/rate_limit.py
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/ai/incidents/{incident_id}/analyze")
@limiter.limit("10/minute")  # Max 10 AI requests per minute
async def analyze_incident(request: Request, incident_id: int):
    # ... analysis logic ...
    pass
```

#### Input Validation
```python
# Pydantic models for validation
from pydantic import BaseModel, validator, constr

class CreateTask(BaseModel):
    title: constr(min_length=1, max_length=200)
    description: constr(max_length=5000) = ""
    priority: Literal['low', 'medium', 'high']

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v
```

#### Security Headers
```python
# main.py
from fastapi.middleware.security import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    content_security_policy="default-src 'self'",
    x_frame_options="DENY",
    x_content_type_options="nosniff"
)
```

**Effort:** 3 dny

---

## 6. Prioritization Matrix

```
HIGH IMPACT × LOW EFFORT (DO FIRST)
┌─────────────────────────────────────────────┐
│ ✅ Incident Templates          (9/10, 2/10) │
│ ✅ Context Menu                (8/10, 3/10) │
│ ✅ Smart Notifications         (9/10, 4/10) │
│ ✅ Global Search (Cmd+K)       (8/10, 6/10) │
│ ✅ Bulk Operations             (7/10, 5/10) │
│ ✅ Redis Caching               (8/10, 4/10) │
│ ✅ Frontend Bundle Opt         (7/10, 3/10) │
│ ✅ Security Fixes              (9/10, 4/10) │
└─────────────────────────────────────────────┘
Estimated: 2-3 weeks total

HIGH IMPACT × MEDIUM EFFORT (DO NEXT)
┌─────────────────────────────────────────────┐
│ 🟡 Observability Dashboard    (10/10, 7/10) │
│ 🟡 PostgreSQL Migration        (9/10, 6/10) │
│ 🟡 Collaboration Features      (9/10, 7/10) │
└─────────────────────────────────────────────┘
Estimated: 5-6 weeks total

HIGH IMPACT × HIGH EFFORT (LONG-TERM)
┌─────────────────────────────────────────────┐
│ 🔴 Advanced AI Features       (10/10, 8/10) │
│ 🔴 Mobile PWA                  (9/10, 7/10) │
│ 🔴 Workflow Automation        (10/10, 9/10) │
└─────────────────────────────────────────────┘
Estimated: 10-12 weeks total

LOW PRIORITY
┌─────────────────────────────────────────────┐
│ ⚪ Custom themes               (4/10, 3/10) │
│ ⚪ Export to Excel             (5/10, 2/10) │
│ ⚪ Gantt chart view            (6/10, 7/10) │
└─────────────────────────────────────────────┘
```

---

## 7. 3-Month Roadmap

### Sprint 1-2 (Week 1-4): Quick Wins & Foundation

**Week 1:**
- ✅ Incident Templates (2 dny)
- ✅ Context Menu (3 dny)

**Week 2:**
- ✅ Smart Notifications (4 dny)
- ✅ Security Fixes (3 dny)

**Week 3:**
- ✅ Global Search (5 dní)

**Week 4:**
- ✅ Bulk Operations (4 dny)
- ✅ Redis Caching (3 dny)

**Deliverables:**
- 5 quick wins deployed to production
- Time-to-report < 30s
- User productivity +40%
- Dashboard load time < 200ms

---

### Sprint 3-4 (Week 5-8): Strategic Phase 1

**Week 5-6:**
- 🟡 Observability Dashboard (2 weeks)
  - Metric cards with sparklines
  - Agent performance table
  - Cost tracking chart
  - Event heatmap

**Week 7:**
- 🟡 PostgreSQL Migration (1 week)
  - Schema conversion
  - Data migration
  - Blue-green deployment

**Week 8:**
- 🟡 Collaboration MVP (1 week)
  - Comments on tasks/incidents
  - @Mentions
  - Activity feed

**Deliverables:**
- Dashboard < 200ms load time
- Support 100+ concurrent users
- Comments/task: 2.5 average
- PostgreSQL in production

---

### Sprint 5-6 (Week 9-12): Polish & Scale

**Week 9-10:**
- 🔴 Advanced AI Features (2 weeks)
  - Predictive incident alerts
  - Incident correlation
  - Cost optimization (caching)

**Week 11-12:**
- 🔴 Mobile PWA (2 weeks)
  - PWA setup & manifest
  - Offline support (IndexedDB)
  - Mobile-optimized UI
  - Swipe gestures

**Deliverables:**
- AI prediction accuracy >80%
- PWA install rate >25%
- Mobile traffic +40%
- AI cost reduction -30%

---

## 8. Success Metrics & KPIs

### Performance Metrics

| Metric | Current | Target (3M) | Improvement |
|--------|---------|-------------|-------------|
| Time-to-first-task | ~5 min | <2 min | -60% |
| Incident resolution (MTTR) | 45 min | 27 min | -40% |
| Dashboard load time | 800ms | 120ms | -85% |
| Bundle size | 2.4MB | 850KB | -65% |
| First load time | 3.5s | 1.2s | -66% |

### User Engagement

| Metric | Current | Target (3M) | Improvement |
|--------|---------|-------------|-------------|
| Daily active users | 100% baseline | 120% | +20% |
| Task completion rate | 65% | 85% | +31% |
| Comments per task | 0 | 2.5 | NEW |
| Mobile traffic | 15% | 55% | +267% |
| Session duration | 8 min | 12 min | +50% |

### AI & Automation

| Metric | Current | Target (3M) | Improvement |
|--------|---------|-------------|-------------|
| AI triage accuracy | N/A | >85% | NEW |
| AI cost per incident | $0.15 | $0.10 | -33% |
| Cache hit rate | 0% | >60% | NEW |
| Automated workflows | 0% | 50% | NEW |

### Business Impact

| Metric | Current | Target (3M) | Improvement |
|--------|---------|-------------|-------------|
| MTTA (Mean Time To Acknowledge) | 15 min | 3 min | -80% |
| MTTD (Mean Time To Detect) | 10 min | 5 min | -50% |
| SLA compliance | 92% | 99% | +7.6% |
| Cost per incident | ~$20 | ~$8 | -60% |

---

## 9. Competitive Analysis

### Feature Comparison Matrix

| Feature | Able2Flow (Now) | Target (3M) | Trello | Jira | Betterstack | PagerDuty | Datadog |
|---------|-----------------|-------------|--------|------|-------------|-----------|---------|
| **AI Triage** | ✅ **Unique** | ✅ **Enhanced** | ❌ | ❌ | ❌ | ❌ | ⚠️ (Limited) |
| **Task Management** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Health Monitoring** | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **Incident Response** | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **Observability Dashboard** | ⚠️ Basic | ✅ **NEW** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Collaboration** | ❌ | ✅ **NEW** | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **Mobile App** | ⚠️ Web | ✅ **PWA** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Workflow Automation** | ❌ | ✅ **NEW** | ⚠️ (Butler) | ✅ | ⚠️ | ✅ | ✅ |
| **Multi-language** | ✅ CS/EN | ✅ CS/EN | ⚠️ | ⚠️ | ❌ | ❌ | ❌ |
| **Event Sourcing** | ✅ **Unique** | ✅ | ❌ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| **Pricing** | **Free/Low** | **Competitive** | $5-17/user | $7.75-15/user | $10/monitor | $21-41/user | $15+/host |

### Unique Value Proposition

**Able2Flow je jediný nástroj, který:**

1. **Kombinuje 3 kategorie** (task mgmt + monitoring + incidents) v jedné aplikaci
2. **AI-powered triage** s multi-language support (CS/EN) - unique na trhu
3. **Event sourcing** pro complete disaster recovery
4. **Cost advantage** - významně levnější než konkurence
5. **Developer-friendly** - open-source stack (FastAPI + Vue 3)

**Target Audience:**
- Small-to-medium engineering teams (5-50 členů)
- DevOps teams potřebující incident response + task tracking
- Czech/European teams (multi-language support)
- Startups hledající cost-effective alternative k PagerDuty/Datadog

---

## 10. Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **AI costs too high** | Medium | High | - Cache responses (5min TTL)<br>- Rate limit (10 req/min/user)<br>- Fallback to rule-based triage<br>- Monthly budget alerts |
| **PostgreSQL migration fail** | Low | Critical | - Full database backup<br>- Staged rollout (10% → 50% → 100%)<br>- Rollback plan<br>- Test on staging environment |
| **PWA adoption low** | Medium | Medium | - In-app install prompts<br>- Demo video<br>- Incentives (beta badges) |
| **Cache invalidation bugs** | Medium | Medium | - Conservative TTL (60s)<br>- Manual cache flush endpoint<br>- Cache versioning |

### Product Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Low user adoption** | Medium | High | - In-app tutorials<br>- Beta program with feedback loop<br>- User interviews (monthly)<br>- Onboarding flow optimization |
| **Feature bloat** | High | Medium | - Strict prioritization (impact/effort matrix)<br>- Feature flags<br>- User analytics (track usage)<br>- Quarterly feature review |
| **Performance degradation** | Low | High | - Load testing (100+ concurrent users)<br>- Performance monitoring (Sentry)<br>- Regular optimization sprints |

### Business Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Competitor copies AI triage** | Medium | Medium | - Patent/IP protection (if applicable)<br>- Focus on execution speed<br>- Build strong brand loyalty<br>- Continuous innovation |
| **AI API costs spike** | Low | High | - Monthly budget caps<br>- Alternative models (GPT-4 Turbo)<br>- Self-hosted model option |
| **Regulatory compliance (GDPR)** | Medium | High | - Data residency options (EU servers)<br>- Privacy policy<br>- Data retention controls<br>- Legal review |

---

## 11. Next Steps

### This Week (Week 1)

**Monday:**
- [ ] Setup Redis locally (Docker: `docker run -d -p 6379:6379 redis`)
- [ ] Review security OWASP checklist
- [ ] Design 10 incident templates (DB slow, API timeout, high CPU, ...)

**Tuesday:**
- [ ] Implement incident templates backend API
- [ ] Create IncidentTemplates UI component
- [ ] Write tests for template selection

**Wednesday:**
- [ ] Implement context menu (right-click on task cards)
- [ ] Add duplicate, move, convert actions

**Thursday:**
- [ ] Start smart notifications (request permission flow)
- [ ] Implement notification service

**Friday:**
- [ ] Demo session with team
- [ ] Collect feedback
- [ ] Plan Sprint 2

### Month 1 Goal

**By End of Week 4:**
- ✅ All 5 Quick Wins deployed to production
- ✅ 100 active users testing new features
- ✅ User feedback collected (survey)
- ✅ Incident templates used in 60% of reports
- ✅ Global search adoption >40%

### Month 2-3 Goals

**Month 2:**
- Observability dashboard live
- PostgreSQL migration completed
- Collaboration MVP (comments + mentions)

**Month 3:**
- Advanced AI features (prediction + correlation)
- Mobile PWA launched
- Workflow automation beta

---

## 12. Appendix

### A. Technology Stack Summary

**Frontend:**
- Vue 3.4+ (Composition API)
- TypeScript 5.3+
- Vite 5.0 (build tool)
- Pinia (state management)
- Vue Router 4
- Chart.js / Vue-Chartjs (visualizations)
- Fuse.js (fuzzy search)
- DOMPurify (XSS protection)
- PWA plugin (vite-plugin-pwa)

**Backend:**
- FastAPI 0.109+
- Python 3.11+
- SQLite → PostgreSQL
- Redis (caching)
- APScheduler (background jobs)
- httpx (health checks)
- Anthropic Claude API (AI)

**Infrastructure:**
- Docker (Redis, PostgreSQL)
- nginx (reverse proxy)
- Sentry (error tracking)
- GitHub Actions (CI/CD)

### B. Database Schema Changes

**New Tables:**
```sql
-- AI usage tracking
CREATE TABLE ai_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER,
    operation_type TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    user_name TEXT,
    content TEXT NOT NULL,
    mentions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Automation rules
CREATE TABLE automation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    trigger TEXT NOT NULL,
    conditions TEXT, -- JSON
    actions TEXT, -- JSON
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent operations
CREATE TABLE agent_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT,
    operation TEXT,
    duration_ms INTEGER,
    success BOOLEAN,
    cost_usd REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### C. API Endpoints Summary

**Quick Wins:**
- `GET /api/incidents/templates` - List incident templates
- `POST /api/tasks/{id}/duplicate` - Duplicate task
- `POST /api/tasks/{id}/convert-to-incident` - Convert task
- `POST /api/tasks/bulk/archive` - Bulk archive
- `GET /api/search?q=database` - Global search

**Observability:**
- `GET /api/observability/metrics?time_range=24h` - Dashboard metrics
- `GET /api/observability/agent-performance` - Agent stats
- `GET /api/observability/cost-trend` - AI cost over time

**AI Advanced:**
- `GET /api/ai/monitors/{id}/predict-incident` - Predictive alerts
- `GET /api/ai/incidents/{id}/related` - Incident correlation

**Collaboration:**
- `POST /api/comments` - Create comment
- `GET /api/comments/{type}/{id}` - Get comments
- `GET /api/activity/feed` - Activity feed

**Automation:**
- `GET /api/automation/rules` - List rules
- `POST /api/automation/rules` - Create rule
- `PUT /api/automation/rules/{id}` - Update rule

### D. Design System

**Colors:**
```css
:root {
  --bg-dark: #1a1b26;
  --bg-lighter: #24283b;
  --bg-highlight: #292e42;

  --text-primary: #c0caf5;
  --text-secondary: #a9b1d6;
  --text-muted: #565f89;

  --accent-blue: #7aa2f7;
  --accent-green: #9ece6a;
  --accent-red: #f7768e;
  --accent-yellow: #e0af68;
  --accent-purple: #bb9af7;
  --accent-cyan: #7dcfff;

  --border-color: #3b4261;
}
```

**Typography:**
- Headings: Inter, system-ui
- Body: -apple-system, BlinkMacSystemFont, "Segoe UI"
- Code: "Fira Code", monospace

**Spacing Scale:**
- 0.25rem (4px)
- 0.5rem (8px)
- 0.75rem (12px)
- 1rem (16px)
- 1.5rem (24px)
- 2rem (32px)
- 3rem (48px)

---

## Závěr

Tento strategický dokument poskytuje **kompletní roadmap** pro Able2Flow na H1 2026. Prioritizace je založená na **impact/effort matrix**, s fokusem na:

1. **Quick Wins** (Week 1-4) - Okamžitá value pro users
2. **Strategic Initiatives** (Week 5-12) - Long-term competitive advantage
3. **Technical Excellence** - Scalability, security, performance

**Klíčová differentiace**: AI-powered triage zůstává naším **unique selling point**. Rozšíření o observability dashboard, collaboration features, a mobile PWA nás posune do pozice **all-in-one nástroje** pro DevOps teams.

**Next Action**: Začít s implementací Quick Win #1 (Incident Templates) tento týden.

---

**Kontakt pro feedback:**
- Product Manager: product@able2flow.com
- Engineering Lead: eng@able2flow.com
- GitHub Issues: github.com/able2flow/issues

**Document Version:** 1.0
**Last Updated:** Leden 2026
**Next Review:** Duben 2026
