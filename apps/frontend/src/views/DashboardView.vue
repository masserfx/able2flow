<script setup lang="ts">
import { ref, onMounted, computed, inject, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type DashboardData, type Incident } from '../composables/useApi'
import AppIcon from '../components/AppIcon.vue'

const { t, te } = useI18n()
const api = useApi()
const currentProjectId = inject<Ref<number | null>>('currentProjectId', ref(null))

function translateColumn(name: string): string {
  const key = `columns.${name}`
  return te(key) ? t(key) : name
}
const dashboard = ref<DashboardData | null>(null)
const openIncidents = ref<Incident[]>([])
const loading = ref(true)

async function loadDashboard() {
  loading.value = true
  try {
    const projectId = currentProjectId.value ?? undefined
    const [dashData, incidents] = await Promise.all([
      api.getDashboard(projectId),
      api.getOpenIncidents(projectId),
    ])
    dashboard.value = dashData
    openIncidents.value = incidents
  } catch (e) {
    console.error('Failed to load dashboard:', e)
  } finally {
    loading.value = false
  }
}

watch(currentProjectId, loadDashboard)

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
      <h1>{{ $t('dashboard.title') }}</h1>
      <button @click="loadDashboard" :disabled="loading">
        {{ loading ? $t('common.loading') : '↻ ' + $t('dashboard.refresh') }}
      </button>
    </header>

    <div v-if="loading && !dashboard" class="loading">{{ $t('dashboard.loading') }}</div>

    <template v-else-if="dashboard">
      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <AppIcon name="check-circle" :size="32" class="stat-icon" style="color: var(--accent-blue)" />
          <div class="stat-content">
            <div class="stat-value">{{ dashboard.tasks.completed }} / {{ dashboard.tasks.total }}</div>
            <div class="stat-label">{{ $t('dashboard.tasksCompleted') }}</div>
            <div class="stat-bar">
              <div
                class="stat-bar-fill"
                :style="{ width: `${dashboard.tasks.completion_rate}%`, background: 'var(--accent-blue)' }"
              />
            </div>
          </div>
        </div>

        <div class="stat-card">
          <AppIcon name="monitor" :size="32" class="stat-icon" style="color: var(--accent-green)" />
          <div class="stat-content">
            <div class="stat-value" :style="{ color: uptimeColor }">
              {{ dashboard.monitoring.uptime_24h }}%
            </div>
            <div class="stat-label">{{ $t('dashboard.uptime24h') }}</div>
            <div class="stat-bar">
              <div
                class="stat-bar-fill"
                :style="{ width: `${dashboard.monitoring.uptime_24h}%`, background: uptimeColor }"
              />
            </div>
          </div>
        </div>

        <div class="stat-card">
          <AppIcon name="zap" :size="32" class="stat-icon" :style="{ color: dashboard.monitoring.open_incidents > 0 ? 'var(--accent-red)' : 'var(--accent-green)' }" />
          <div class="stat-content">
            <div class="stat-value">{{ dashboard.monitoring.open_incidents }}</div>
            <div class="stat-label">{{ $t('dashboard.openIncidents') }}</div>
          </div>
        </div>

        <div class="stat-card">
          <AppIcon name="list" :size="32" class="stat-icon" style="color: var(--accent-magenta)" />
          <div class="stat-content">
            <div class="stat-value">{{ dashboard.activity.recent_24h }}</div>
            <div class="stat-label">{{ $t('dashboard.actions24h') }}</div>
          </div>
        </div>
      </div>

      <!-- Two Column Layout -->
      <div class="dashboard-grid">
        <!-- Tasks by Column -->
        <div class="card">
          <h3>{{ $t('dashboard.tasksByStatus') }}</h3>
          <div class="task-columns">
            <div
              v-for="(count, column) in dashboard.tasks.by_column"
              :key="column"
              class="task-column-item"
            >
              <span class="column-name">{{ translateColumn(column as string) }}</span>
              <span class="column-count">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- Open Incidents -->
        <div class="card">
          <h3>{{ $t('dashboard.openIncidentsTitle') }}</h3>
          <div v-if="openIncidents.length === 0" class="empty-state">
            <AppIcon name="check-circle" :size="20" class="empty-icon" />
            <span>{{ $t('dashboard.allSystemsOperational') }}</span>
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
          <h3>{{ $t('dashboard.monitors') }}</h3>
          <div class="monitor-status">
            <div class="monitor-stat">
              <span class="badge up">{{ $t('dashboard.up') }}</span>
              <span>{{ dashboard.monitoring.by_status.up || 0 }}</span>
            </div>
            <div class="monitor-stat">
              <span class="badge down">{{ $t('dashboard.down') }}</span>
              <span>{{ dashboard.monitoring.by_status.down || 0 }}</span>
            </div>
            <div class="monitor-stat">
              <span class="badge unknown">{{ $t('dashboard.unknown') }}</span>
              <span>{{ dashboard.monitoring.by_status.unknown || 0 }}</span>
            </div>
          </div>
          <div class="response-time">
            {{ $t('dashboard.avgResponse') }}: <strong>{{ dashboard.monitoring.avg_response_time_ms }}ms</strong>
          </div>
        </div>

        <!-- Tasks by Priority -->
        <div class="card">
          <h3>{{ $t('dashboard.tasksByPriority') }}</h3>
          <div class="priority-list">
            <div class="priority-item">
              <span class="priority-dot priority-high">●</span>
              <span>{{ $t('dashboard.high') }}</span>
              <span class="priority-count">{{ dashboard.tasks.by_priority.high || 0 }}</span>
            </div>
            <div class="priority-item">
              <span class="priority-dot priority-medium">●</span>
              <span>{{ $t('dashboard.medium') }}</span>
              <span class="priority-count">{{ dashboard.tasks.by_priority.medium || 0 }}</span>
            </div>
            <div class="priority-item">
              <span class="priority-dot priority-low">●</span>
              <span>{{ $t('dashboard.low') }}</span>
              <span class="priority-count">{{ dashboard.tasks.by_priority.low || 0 }}</span>
            </div>
          </div>
          <div v-if="dashboard.tasks.overdue > 0" class="overdue-warning">
            {{ $t('dashboard.overdueTasksWarning', { count: dashboard.tasks.overdue }) }}
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
