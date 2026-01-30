<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi, type AuditLog } from '../composables/useApi'

const api = useApi()
const logs = ref<AuditLog[]>([])
const loading = ref(true)

async function loadLogs() {
  loading.value = true
  try {
    logs.value = await api.getAuditLogs(100)
  } catch (e) {
    console.error('Failed to load audit logs:', e)
  } finally {
    loading.value = false
  }
}

function getActionColor(action: string) {
  switch (action) {
    case 'create':
      return 'var(--accent-green)'
    case 'update':
    case 'move':
      return 'var(--accent-blue)'
    case 'delete':
      return 'var(--accent-red)'
    case 'acknowledge':
    case 'resolve':
      return 'var(--accent-yellow)'
    default:
      return 'var(--text-muted)'
  }
}

function getEntityIcon(entityType: string) {
  switch (entityType) {
    case 'task':
      return '☑'
    case 'column':
      return '▦'
    case 'monitor':
      return '◎'
    case 'incident':
      return '⚡'
    default:
      return '•'
  }
}

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`

  return date.toLocaleDateString()
}

function formatChange(log: AuditLog) {
  if (log.action === 'create' && log.new_value) {
    const name = (log.new_value as Record<string, unknown>).title ||
                 (log.new_value as Record<string, unknown>).name ||
                 `#${log.entity_id}`
    return `Created "${name}"`
  }

  if (log.action === 'delete' && log.old_value) {
    const name = (log.old_value as Record<string, unknown>).title ||
                 (log.old_value as Record<string, unknown>).name ||
                 `#${log.entity_id}`
    return `Deleted "${name}"`
  }

  if (log.action === 'move' && log.old_value && log.new_value) {
    return `Moved task #${log.entity_id}`
  }

  if (log.action === 'acknowledge') {
    return `Acknowledged incident #${log.entity_id}`
  }

  if (log.action === 'resolve') {
    return `Resolved incident #${log.entity_id}`
  }

  if (log.action === 'update' && log.old_value && log.new_value) {
    const changes: string[] = []
    const oldVal = log.old_value as Record<string, unknown>
    const newVal = log.new_value as Record<string, unknown>

    for (const key of Object.keys(newVal)) {
      if (oldVal[key] !== newVal[key] && key !== 'id' && key !== 'created_at') {
        changes.push(key)
      }
    }

    if (changes.length > 0) {
      return `Updated ${changes.join(', ')} on #${log.entity_id}`
    }
  }

  return `${log.action} ${log.entity_type} #${log.entity_id}`
}

onMounted(loadLogs)
</script>

<template>
  <div class="audit-view">
    <header class="page-header">
      <h1>Audit Log</h1>
      <button @click="loadLogs" :disabled="loading">
        {{ loading ? 'Loading...' : '↻ Refresh' }}
      </button>
    </header>

    <div v-if="loading && logs.length === 0" class="loading">
      Loading audit logs...
    </div>

    <div v-else-if="logs.length === 0" class="empty-state card">
      <div class="empty-icon">☰</div>
      <div class="empty-text">No activity yet</div>
      <div class="empty-hint">Actions will appear here as you use the app</div>
    </div>

    <div v-else class="audit-timeline">
      <div
        v-for="log in logs"
        :key="log.id"
        class="audit-entry"
      >
        <div class="entry-icon" :style="{ color: getActionColor(log.action) }">
          {{ getEntityIcon(log.entity_type) }}
        </div>
        <div class="entry-content">
          <div class="entry-header">
            <span
              class="entry-action"
              :style="{ color: getActionColor(log.action) }"
            >
              {{ log.action }}
            </span>
            <span class="entry-entity">{{ log.entity_type }}</span>
          </div>
          <div class="entry-description">{{ formatChange(log) }}</div>
          <div class="entry-time">{{ formatTimestamp(log.timestamp) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audit-view {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  margin: 0;
}

.loading {
  text-align: center;
  color: var(--text-muted);
  padding: 4rem;
}

.empty-state {
  text-align: center;
  padding: 4rem;
}

.empty-icon {
  font-size: 3rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 1.25rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.empty-hint {
  color: var(--text-muted);
}

.audit-timeline {
  display: flex;
  flex-direction: column;
}

.audit-entry {
  display: flex;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color);
}

.audit-entry:last-child {
  border-bottom: none;
}

.entry-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-lighter);
  border-radius: 50%;
  font-size: 1rem;
  flex-shrink: 0;
}

.entry-content {
  flex: 1;
  min-width: 0;
}

.entry-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.entry-action {
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: capitalize;
}

.entry-entity {
  font-size: 0.75rem;
  color: var(--text-muted);
  background: var(--bg-highlight);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.entry-description {
  color: var(--text-primary);
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.entry-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
