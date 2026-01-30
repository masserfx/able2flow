<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  name: string
  description: string
  icon: string
  provider: string
  connected: boolean
  needsScopes?: boolean
  scopes?: string[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  needsScopes: false,
  scopes: () => [],
  loading: false,
})

const emit = defineEmits<{
  (e: 'connect'): void
  (e: 'disconnect'): void
  (e: 'configure'): void
}>()

const statusClass = computed(() => ({
  'status-connected': props.connected,
  'status-needs-scopes': props.needsScopes,
  'status-disconnected': !props.connected && !props.needsScopes,
}))

const statusText = computed(() => {
  if (props.connected) return 'Connected'
  if (props.needsScopes) return 'Needs authorization'
  return 'Not connected'
})

const actionButtonText = computed(() => {
  if (props.connected) return 'Configure'
  if (props.needsScopes) return 'Authorize'
  return 'Connect'
})

function handleAction() {
  if (props.connected) {
    emit('configure')
  } else {
    emit('connect')
  }
}
</script>

<template>
  <div class="integration-card" :class="{ connected, 'needs-scopes': needsScopes }">
    <div class="card-header">
      <div class="icon-wrapper">
        <span class="icon">{{ icon }}</span>
      </div>
      <div class="card-info">
        <h3 class="card-title">{{ name }}</h3>
        <p class="card-description">{{ description }}</p>
      </div>
    </div>

    <div class="card-status">
      <span class="status-indicator" :class="statusClass"></span>
      <span class="status-text">{{ statusText }}</span>
    </div>

    <div v-if="connected && scopes.length > 0" class="card-scopes">
      <span class="scopes-label">Permissions:</span>
      <div class="scopes-list">
        <span v-for="scope in scopes" :key="scope" class="scope-tag">{{ scope }}</span>
      </div>
    </div>

    <div class="card-actions">
      <button
        v-if="connected"
        class="btn btn-secondary"
        @click="emit('disconnect')"
        :disabled="loading"
      >
        Disconnect
      </button>
      <button
        class="btn"
        :class="connected ? 'btn-primary' : needsScopes ? 'btn-warning' : 'btn-connect'"
        @click="handleAction"
        :disabled="loading"
      >
        <span v-if="loading" class="loading-spinner"></span>
        {{ actionButtonText }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.integration-card {
  background-color: var(--bg-darker);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  transition: border-color 0.2s;
}

.integration-card:hover {
  border-color: var(--accent-blue);
}

.integration-card.connected {
  border-color: var(--accent-green);
}

.integration-card.needs-scopes {
  border-color: var(--accent-orange, #f59e0b);
}

.card-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  background-color: var(--bg-highlight);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
}

.card-description {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
}

.card-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-connected {
  background-color: var(--accent-green);
}

.status-disconnected {
  background-color: var(--text-muted);
}

.status-needs-scopes {
  background-color: var(--accent-orange, #f59e0b);
}

.status-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.card-scopes {
  margin-bottom: 1rem;
}

.scopes-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  display: block;
  margin-bottom: 0.5rem;
}

.scopes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.scope-tag {
  font-size: 0.625rem;
  background-color: var(--bg-highlight);
  color: var(--text-secondary);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--accent-blue);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--accent-blue-hover);
}

.btn-secondary {
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--bg-highlight);
  color: var(--text-primary);
}

.btn-connect {
  background-color: var(--accent-green);
  color: white;
}

.btn-connect:hover:not(:disabled) {
  filter: brightness(1.1);
}

.btn-warning {
  background-color: var(--accent-orange, #f59e0b);
  color: white;
}

.btn-warning:hover:not(:disabled) {
  filter: brightness(1.1);
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
