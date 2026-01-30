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

// AI Triage
interface AIAnalysis {
  ai_powered: boolean
  model?: string
  severity_suggestion: string
  confidence: number
  root_cause_hypothesis: string[]
  recommended_actions: string[]
  estimated_impact: string
  runbook_suggestion?: string
  analyzed_at: string
}

const analyzingIncidentId = ref<number | null>(null)
const aiAnalysis = ref<AIAnalysis | null>(null)
const showAIModal = ref(false)

async function analyzeIncident(incident: Incident) {
  analyzingIncidentId.value = incident.id
  aiAnalysis.value = null
  showAIModal.value = true

  try {
    const response = await fetch(`http://localhost:8000/api/ai/incidents/${incident.id}/analyze`, {
      method: 'POST',
    })
    aiAnalysis.value = await response.json()
  } catch (e) {
    console.error('Failed to analyze incident:', e)
    aiAnalysis.value = {
      ai_powered: false,
      severity_suggestion: 'unknown',
      confidence: 0,
      root_cause_hypothesis: ['Analysis failed'],
      recommended_actions: ['Try again later'],
      estimated_impact: 'Unknown',
      analyzed_at: new Date().toISOString(),
    }
  } finally {
    analyzingIncidentId.value = null
  }
}

function closeAIModal() {
  showAIModal.value = false
  aiAnalysis.value = null
}

function getConfidenceColor(confidence: number) {
  if (confidence >= 0.8) return '#9ece6a'
  if (confidence >= 0.5) return '#e0af68'
  return '#f7768e'
}

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

        <div class="incident-actions">
          <button
            class="ai-btn"
            @click="analyzeIncident(incident)"
            :disabled="analyzingIncidentId === incident.id"
          >
            {{ analyzingIncidentId === incident.id ? '⏳ Analyzing...' : '🤖 AI Triage' }}
          </button>
          <template v-if="incident.status !== 'resolved'">
            <button
              v-if="incident.status === 'open'"
              @click="acknowledgeIncident(incident)"
            >
              {{ $t('incidents.acknowledge') }}
            </button>
            <button class="success" @click="resolveIncident(incident)">
              {{ $t('incidents.resolve') }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- AI Analysis Modal -->
    <div v-if="showAIModal" class="modal-overlay" @click.self="closeAIModal">
      <div class="modal ai-modal">
        <div class="modal-header">
          <h2>🤖 AI Triage Analysis</h2>
          <button class="close-btn" @click="closeAIModal">✕</button>
        </div>

        <div v-if="!aiAnalysis" class="modal-loading">
          <div class="spinner"></div>
          <p>Claude is analyzing the incident...</p>
        </div>

        <div v-else class="ai-results">
          <div class="ai-meta">
            <span v-if="aiAnalysis.ai_powered" class="ai-badge powered">
              ✨ AI Powered
            </span>
            <span v-else class="ai-badge fallback">
              📋 Rule-based Fallback
            </span>
            <span v-if="aiAnalysis.model" class="ai-model">{{ aiAnalysis.model }}</span>
          </div>

          <div class="ai-section">
            <h3>Severity Suggestion</h3>
            <div class="severity-row">
              <span :class="['badge', aiAnalysis.severity_suggestion]">
                {{ aiAnalysis.severity_suggestion }}
              </span>
              <span class="confidence" :style="{ color: getConfidenceColor(aiAnalysis.confidence) }">
                {{ Math.round(aiAnalysis.confidence * 100) }}% confidence
              </span>
            </div>
          </div>

          <div class="ai-section">
            <h3>Root Cause Hypothesis</h3>
            <ul class="hypothesis-list">
              <li v-for="(cause, i) in aiAnalysis.root_cause_hypothesis" :key="i">
                {{ cause }}
              </li>
            </ul>
          </div>

          <div class="ai-section">
            <h3>Recommended Actions</h3>
            <ol class="actions-list">
              <li v-for="(action, i) in aiAnalysis.recommended_actions" :key="i">
                {{ action }}
              </li>
            </ol>
          </div>

          <div class="ai-section">
            <h3>Estimated Impact</h3>
            <p class="impact-text">{{ aiAnalysis.estimated_impact }}</p>
          </div>

          <div v-if="aiAnalysis.runbook_suggestion" class="ai-section">
            <h3>Suggested Runbook</h3>
            <p class="runbook-text">📖 {{ aiAnalysis.runbook_suggestion }}</p>
          </div>

          <div class="ai-footer">
            <span class="analyzed-at">
              Analyzed: {{ new Date(aiAnalysis.analyzed_at).toLocaleString() }}
            </span>
          </div>
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

.ai-btn {
  background: linear-gradient(135deg, #bb9af7 0%, #7aa2f7 100%);
  color: #1a1b26;
  font-weight: 600;
  border: none;
}

.ai-btn:hover {
  opacity: 0.9;
}

.ai-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

/* AI Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.ai-modal {
  background: var(--bg-lighter);
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(135deg, rgba(187, 154, 247, 0.1) 0%, rgba(122, 162, 247, 0.1) 100%);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-muted);
  padding: 0.5rem;
}

.close-btn:hover {
  color: var(--text-primary);
}

.modal-loading {
  padding: 4rem;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-purple);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.ai-results {
  padding: 1.5rem;
}

.ai-meta {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1.5rem;
}

.ai-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-weight: 600;
}

.ai-badge.powered {
  background: rgba(187, 154, 247, 0.2);
  color: #bb9af7;
}

.ai-badge.fallback {
  background: rgba(224, 175, 104, 0.2);
  color: #e0af68;
}

.ai-model {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.ai-section {
  margin-bottom: 1.5rem;
}

.ai-section h3 {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.severity-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.confidence {
  font-weight: 600;
  font-size: 0.875rem;
}

.hypothesis-list,
.actions-list {
  margin: 0;
  padding-left: 1.25rem;
}

.hypothesis-list li,
.actions-list li {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.impact-text,
.runbook-text {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.runbook-text {
  background: var(--bg-dark);
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.ai-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.analyzed-at {
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
