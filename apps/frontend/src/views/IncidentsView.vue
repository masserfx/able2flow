<script setup lang="ts">
import { ref, onMounted, computed, inject, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type Incident } from '../composables/useApi'

const { t } = useI18n()
const api = useApi()
const currentProjectId = inject<Ref<number | null>>('currentProjectId', ref(null))
const incidents = ref<Incident[]>([])
const loading = ref(true)
const filter = ref<'all' | 'open' | 'resolved'>('all')

const showNewForm = ref(false)
const newIncident = ref({ title: '', severity: 'warning' })

async function loadIncidents() {
  loading.value = true
  try {
    const projectId = currentProjectId.value ?? undefined
    incidents.value = await api.getIncidents(undefined, projectId)
  } catch (e) {
    console.error('Failed to load incidents:', e)
  } finally {
    loading.value = false
  }
}

watch(currentProjectId, loadIncidents)

const filteredIncidents = computed(() => {
  if (filter.value === 'open') {
    return incidents.value.filter((i) => i.status !== 'resolved')
  }
  if (filter.value === 'resolved') {
    return incidents.value.filter((i) => i.status === 'resolved')
  }
  return incidents.value
})

const emptyHintText = computed(() => {
  if (filter.value === 'all') return t('incidents.allSystemsOperational')
  if (filter.value === 'open') return t('incidents.noOpenIncidents')
  return t('incidents.noResolvedIncidents')
})

async function createIncident() {
  if (!newIncident.value.title) return
  try {
    await api.createIncident(newIncident.value)
    newIncident.value = { title: '', severity: 'warning' }
    showNewForm.value = false
    await loadIncidents()
  } catch (e) {
    console.error('Failed to create incident:', e)
  }
}

async function acknowledgeIncident(incident: Incident) {
  try {
    await api.acknowledgeIncident(incident.id)
    await loadIncidents()
  } catch (e) {
    console.error('Failed to acknowledge incident:', e)
  }
}

async function resolveIncident(incident: Incident) {
  try {
    await api.resolveIncident(incident.id)
    await loadIncidents()
  } catch (e) {
    console.error('Failed to resolve incident:', e)
  }
}

function getSeverityClass(severity: string) {
  if (severity === 'critical') return 'critical'
  if (severity === 'warning') return 'warning'
  return 'unknown'
}

function getStatusClass(status: string) {
  if (status === 'open') return 'critical'
  if (status === 'acknowledged') return 'warning'
  return 'success'
}

function getStatusText(status: string) {
  if (status === 'open') return t('incidents.statusOpen')
  if (status === 'acknowledged') return t('incidents.statusAcknowledged')
  return t('incidents.statusResolved')
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function getDuration(startedAt: string, resolvedAt: string | null) {
  const start = new Date(startedAt).getTime()
  const end = resolvedAt ? new Date(resolvedAt).getTime() : Date.now()
  const diff = end - start

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ${hours % 24}h`
  if (hours > 0) return `${hours}h ${minutes % 60}m`
  return `${minutes}m`
}

onMounted(loadIncidents)
</script>

<template>
  <div class="incidents-view">
    <header class="page-header">
      <h1>{{ $t('incidents.title') }}</h1>
      <div class="header-actions">
        <div class="filter-tabs">
          <button
            :class="{ active: filter === 'all' }"
            @click="filter = 'all'"
          >{{ $t('incidents.all') }}</button>
          <button
            :class="{ active: filter === 'open' }"
            @click="filter = 'open'"
          >{{ $t('incidents.open') }}</button>
          <button
            :class="{ active: filter === 'resolved' }"
            @click="filter = 'resolved'"
          >{{ $t('incidents.resolved') }}</button>
        </div>
        <button class="primary" @click="showNewForm = !showNewForm">
          {{ showNewForm ? '✕ ' + $t('incidents.cancel') : '+ ' + $t('incidents.reportIncident') }}
        </button>
      </div>
    </header>

    <!-- New Incident Form -->
    <div v-if="showNewForm" class="new-form card">
      <div class="form-row">
        <input
          v-model="newIncident.title"
          type="text"
          :placeholder="$t('incidents.incidentDescriptionPlaceholder')"
        />
        <select v-model="newIncident.severity">
          <option value="warning">{{ $t('incidents.warning') }}</option>
          <option value="critical">{{ $t('incidents.critical') }}</option>
        </select>
        <button class="primary" @click="createIncident">{{ $t('incidents.report') }}</button>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ $t('incidents.loading') }}</div>

    <div v-else-if="filteredIncidents.length === 0" class="empty-state card">
      <div class="empty-icon">✓</div>
      <div class="empty-text">{{ $t('incidents.noIncidents') }}</div>
      <div class="empty-hint">
        {{ emptyHintText }}
      </div>
    </div>

    <!-- Incidents List -->
    <div v-else class="incidents-list">
      <div
        v-for="incident in filteredIncidents"
        :key="incident.id"
        class="incident-card card"
      >
        <div class="incident-header">
          <span :class="['badge', getSeverityClass(incident.severity)]">
            {{ incident.severity === 'critical' ? $t('incidents.critical') : $t('incidents.warning') }}
          </span>
          <span :class="['badge', getStatusClass(incident.status)]">
            {{ getStatusText(incident.status) }}
          </span>
          <span class="incident-duration">
            {{ getDuration(incident.started_at, incident.resolved_at) }}
          </span>
        </div>

        <h3 class="incident-title">{{ incident.title }}</h3>

        <div class="incident-timeline">
          <div class="timeline-item">
            <span class="timeline-label">{{ $t('incidents.started') }}</span>
            <span class="timeline-value">{{ formatDate(incident.started_at) }}</span>
          </div>
          <div v-if="incident.acknowledged_at" class="timeline-item">
            <span class="timeline-label">{{ $t('incidents.acknowledged') }}</span>
            <span class="timeline-value">{{ formatDate(incident.acknowledged_at) }}</span>
          </div>
          <div v-if="incident.resolved_at" class="timeline-item">
            <span class="timeline-label">{{ $t('incidents.resolvedAt') }}</span>
            <span class="timeline-value">{{ formatDate(incident.resolved_at) }}</span>
          </div>
        </div>

        <div v-if="incident.status !== 'resolved'" class="incident-actions">
          <button
            v-if="incident.status === 'open'"
            @click="acknowledgeIncident(incident)"
          >
            {{ $t('incidents.acknowledge') }}
          </button>
          <button class="success" @click="resolveIncident(incident)">
            {{ $t('incidents.resolve') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.incidents-view {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h1 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.filter-tabs {
  display: flex;
  background: var(--bg-lighter);
  border-radius: 8px;
  padding: 4px;
}

.filter-tabs button {
  background: transparent;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.filter-tabs button.active {
  background: var(--bg-highlight);
  color: var(--accent-blue);
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
  color: var(--accent-green);
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

.incidents-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.incident-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.incident-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.incident-duration {
  margin-left: auto;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.incident-title {
  margin: 0;
  font-size: 1.125rem;
}

.incident-timeline {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.timeline-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.timeline-value {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.incident-actions {
  display: flex;
  gap: 0.75rem;
}
</style>
