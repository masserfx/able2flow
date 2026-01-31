<script setup lang="ts">
import { ref, onMounted, inject, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type Monitor } from '../composables/useApi'

const { t } = useI18n()
const api = useApi()
const currentProjectId = inject<Ref<number | null>>('currentProjectId', ref(null))
const monitors = ref<Monitor[]>([])
const loading = ref(true)
const checkingId = ref<number | null>(null)

const showNewForm = ref(false)
const newMonitor = ref({ name: '', url: '', check_interval: 60 })

async function loadMonitors() {
  loading.value = true
  try {
    const projectId = currentProjectId.value ?? undefined
    monitors.value = await api.getMonitors(projectId)
  } catch (e) {
    console.error('Failed to load monitors:', e)
  } finally {
    loading.value = false
  }
}

watch(currentProjectId, loadMonitors)

async function createMonitor() {
  if (!newMonitor.value.name || !newMonitor.value.url) return
  try {
    // Include current project_id when creating monitor
    const monitorData = {
      ...newMonitor.value,
      project_id: currentProjectId.value,
    }
    await api.createMonitor(monitorData)
    newMonitor.value = { name: '', url: '', check_interval: 60 }
    showNewForm.value = false
    await loadMonitors()
  } catch (e) {
    console.error('Failed to create monitor:', e)
  }
}

async function checkMonitor(monitor: Monitor) {
  checkingId.value = monitor.id
  try {
    await api.checkMonitor(monitor.id)
    await loadMonitors()
  } catch (e) {
    console.error('Failed to check monitor:', e)
  } finally {
    checkingId.value = null
  }
}

async function deleteMonitor(monitor: Monitor) {
  if (!confirm(t('monitors.deleteConfirm', { name: monitor.name }))) return
  try {
    await api.deleteMonitor(monitor.id)
    await loadMonitors()
  } catch (e) {
    console.error('Failed to delete monitor:', e)
  }
}

function getStatusClass(status: string) {
  if (status === 'up') return 'up'
  if (status === 'down') return 'down'
  return 'unknown'
}

function formatLastCheck(lastCheck: string | null) {
  if (!lastCheck) return t('common.never')
  const date = new Date(lastCheck)
  return date.toLocaleString()
}

onMounted(loadMonitors)
</script>

<template>
  <div class="monitors-view">
    <header class="page-header">
      <h1>{{ $t('monitors.title') }}</h1>
      <button class="primary" @click="showNewForm = !showNewForm">
        {{ showNewForm ? '✕ ' + $t('monitors.cancel') : '+ ' + $t('monitors.newMonitor') }}
      </button>
    </header>

    <!-- New Monitor Form -->
    <div v-if="showNewForm" class="new-form card">
      <div class="form-row">
        <input
          v-model="newMonitor.name"
          type="text"
          :placeholder="$t('monitors.monitorNamePlaceholder')"
        />
        <input
          v-model="newMonitor.url"
          type="url"
          :placeholder="$t('monitors.urlPlaceholder')"
        />
        <select v-model="newMonitor.check_interval">
          <option :value="30">{{ $t('monitors.intervalOptions.30s') }}</option>
          <option :value="60">{{ $t('monitors.intervalOptions.1m') }}</option>
          <option :value="300">{{ $t('monitors.intervalOptions.5m') }}</option>
          <option :value="600">{{ $t('monitors.intervalOptions.10m') }}</option>
        </select>
        <button class="primary" @click="createMonitor">{{ $t('monitors.add') }}</button>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ $t('monitors.loading') }}</div>

    <div v-else-if="monitors.length === 0" class="empty-state card">
      <div class="empty-icon">◎</div>
      <div class="empty-text">{{ $t('monitors.noMonitorsConfigured') }}</div>
      <div class="empty-hint">{{ $t('monitors.addMonitorHint') }}</div>
    </div>

    <!-- Monitors Grid -->
    <div v-else class="monitors-grid">
      <div v-for="monitor in monitors" :key="monitor.id" class="monitor-card card">
        <div class="monitor-header">
          <span :class="['status-dot', getStatusClass(monitor.last_status)]" />
          <h3>{{ monitor.name }}</h3>
          <span :class="['badge', getStatusClass(monitor.last_status)]">
            {{ monitor.last_status }}
          </span>
        </div>

        <div class="monitor-url">{{ monitor.url }}</div>

        <div class="monitor-details">
          <div class="detail">
            <span class="detail-label">{{ $t('monitors.interval') }}</span>
            <span class="detail-value">{{ monitor.check_interval }}s</span>
          </div>
          <div class="detail">
            <span class="detail-label">{{ $t('monitors.lastCheck') }}</span>
            <span class="detail-value">{{ formatLastCheck(monitor.last_check) }}</span>
          </div>
        </div>

        <div class="monitor-actions">
          <button
            @click="checkMonitor(monitor)"
            :disabled="checkingId === monitor.id"
          >
            {{ checkingId === monitor.id ? $t('monitors.checking') : '↻ ' + $t('monitors.checkNow') }}
          </button>
          <button class="danger" @click="deleteMonitor(monitor)">{{ $t('monitors.delete') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.monitors-view {
  max-width: 1200px;
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

.new-form {
  margin-bottom: 1.5rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-row input {
  flex: 1;
}

.form-row select {
  width: 100px;
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

.monitors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.monitor-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.monitor-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.monitor-header h3 {
  margin: 0;
  flex: 1;
  font-size: 1.125rem;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-dot.up {
  background: var(--accent-green);
  box-shadow: 0 0 8px var(--accent-green);
}

.status-dot.down {
  background: var(--accent-red);
  box-shadow: 0 0 8px var(--accent-red);
  animation: pulse 1s ease-in-out infinite;
}

.status-dot.unknown {
  background: var(--text-muted);
}

.monitor-url {
  color: var(--text-muted);
  font-size: 0.875rem;
  word-break: break-all;
}

.monitor-details {
  display: flex;
  gap: 2rem;
}

.detail {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.detail-value {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.monitor-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: auto;
}

.monitor-actions button {
  flex: 1;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
