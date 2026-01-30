<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useApi, type DashboardData, type Incident } from '../composables/useApi'

const api = useApi()
const dashboard = ref<DashboardData | null>(null)
const openIncidents = ref<Incident[]>([])
const loading = ref(true)

async function loadDashboard() {
  loading.value = true
  try {
    const [dashData, incidents] = await Promise.all([
      api.getDashboard(),
      api.getOpenIncidents(),
    ])
    dashboard.value = dashData
    openIncidents.value = incidents
  } catch (e) {
    console.error('Failed to load dashboard:', e)
  } finally {
    loading.value = false
  }
}

const uptimeColor = computed(() => {
  if (!dashboard.value) return 'var(--text-muted)'
  const uptime = dashboard.value.monitoring.uptime_24h
  if (uptime >= 99) return 'var(--accent-green)'
  if (uptime >= 95) return 'var(--accent-yellow)'
  return 'var(--accent-red)'
})

onMounted(loadDashboard)
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <h1>Dashboard</h1>
      <button @click="loadDashboard" :disabled="loading">
        {{ loading ? 'Loading...' : '↻ Refresh' }}
      </button>
    </header>

    <div v-if="loading && !dashboard" class="loading">Loading dashboard...</div>

    <template v-else-if="dashboard">
      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon" style="color: var(--accent-blue)">☑</div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboard.tasks.completed }} / {{ dashboard.tasks.total }}</div>
            <div class="stat-label">Tasks Completed</div>
            <div class="stat-bar">
              <div
                class="stat-bar-fill"
                :style="{ width: `${dashboard.tasks.completion_rate}%`, background: 'var(--accent-blue)' }"
              />
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="color: var(--accent-green)">◎</div>
          <div class="stat-content">
            <div class="stat-value" :style="{ color: uptimeColor }">
              {{ dashboard.monitoring.uptime_24h }}%
            </div>
            <div class="stat-label">Uptime (24h)</div>
            <div class="stat-bar">
              <div
                class="stat-bar-fill"
                :style="{ width: `${dashboard.monitoring.uptime_24h}%`, background: uptimeColor }"
              />
            </div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" :style="{ color: dashboard.monitoring.open_incidents > 0 ? 'var(--accent-red)' : 'var(--accent-green)' }">⚡</div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboard.monitoring.open_incidents }}</div>
            <div class="stat-label">Open Incidents</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="color: var(--accent-magenta)">☰</div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboard.activity.recent_24h }}</div>
            <div class="stat-label">Actions (24h)</div>
          </div>
        </div>
      </div>

      <!-- Two Column Layout -->
      <div class="dashboard-grid">
        <!-- Tasks by Column -->
        <div class="card">
          <h3>Tasks by Status</h3>
          <div class="task-columns">
            <div
              v-for="(count, column) in dashboard.tasks.by_column"
              :key="column"
              class="task-column-item"
            >
              <span class="column-name">{{ column }}</span>
              <span class="column-count">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- Open Incidents -->
        <div class="card">
          <h3>Open Incidents</h3>
          <div v-if="openIncidents.length === 0" class="empty-state">
            <span class="empty-icon">✓</span>
            <span>All systems operational</span>
          </div>
          <ul v-else class="incident-list">
            <li v-for="incident in openIncidents" :key="incident.id" class="incident-item">
              <span :class="['badge', incident.severity]">{{ incident.severity }}</span>
              <span class="incident-title">{{ incident.title }}</span>
            </li>
          </ul>
        </div>

        <!-- Monitors Status -->
        <div class="card">
          <h3>Monitors</h3>
          <div class="monitor-status">
            <div class="monitor-stat">
              <span class="badge up">Up</span>
              <span>{{ dashboard.monitoring.by_status.up || 0 }}</span>
            </div>
            <div class="monitor-stat">
              <span class="badge down">Down</span>
              <span>{{ dashboard.monitoring.by_status.down || 0 }}</span>
            </div>
            <div class="monitor-stat">
              <span class="badge unknown">Unknown</span>
              <span>{{ dashboard.monitoring.by_status.unknown || 0 }}</span>
            </div>
          </div>
          <div class="response-time">
            Avg Response: <strong>{{ dashboard.monitoring.avg_response_time_ms }}ms</strong>
          </div>
        </div>

        <!-- Tasks by Priority -->
        <div class="card">
          <h3>Tasks by Priority</h3>
          <div class="priority-list">
            <div class="priority-item">
              <span class="priority-dot priority-high">●</span>
              <span>High</span>
              <span class="priority-count">{{ dashboard.tasks.by_priority.high || 0 }}</span>
            </div>
            <div class="priority-item">
              <span class="priority-dot priority-medium">●</span>
              <span>Medium</span>
              <span class="priority-count">{{ dashboard.tasks.by_priority.medium || 0 }}</span>
            </div>
            <div class="priority-item">
              <span class="priority-dot priority-low">●</span>
              <span>Low</span>
              <span class="priority-count">{{ dashboard.tasks.by_priority.low || 0 }}</span>
            </div>
          </div>
          <div v-if="dashboard.tasks.overdue > 0" class="overdue-warning">
            ⚠ {{ dashboard.tasks.overdue }} overdue task(s)
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  margin: 0;
}

.loading {
  text-align: center;
  color: var(--text-muted);
  padding: 4rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.stat-bar {
  height: 4px;
  background: var(--bg-highlight);
  border-radius: 2px;
  margin-top: 0.75rem;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.card h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--text-secondary);
}

.task-columns {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-column-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
}

.task-column-item:last-child {
  border-bottom: none;
}

.column-name {
  color: var(--text-secondary);
}

.column-count {
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--accent-green);
  padding: 1rem 0;
}

.empty-icon {
  font-size: 1.25rem;
}

.incident-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.incident-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-color);
}

.incident-item:last-child {
  border-bottom: none;
}

.incident-title {
  color: var(--text-primary);
  font-size: 0.875rem;
}

.monitor-status {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.monitor-stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.response-time {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.priority-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.priority-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.priority-dot {
  font-size: 0.5rem;
}

.priority-count {
  margin-left: auto;
  font-weight: 600;
}

.overdue-warning {
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(247, 118, 142, 0.1);
  border-radius: 6px;
  color: var(--accent-red);
  font-size: 0.875rem;
}
</style>
