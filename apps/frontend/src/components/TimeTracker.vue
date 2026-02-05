<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type TimeLog } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import AppIcon from './AppIcon.vue'

const { t } = useI18n()
const api = useApi()
const { user } = useAuth()

const props = defineProps<{
  taskId: number
}>()

const emit = defineEmits<{
  timeUpdated: [seconds: number]
}>()

const currentUserId = computed(() => user.value?.id || 'user_petr')

const activeLog = ref<TimeLog | null>(null)
const loading = ref(false)
const elapsedSeconds = ref(0)
let intervalId: number | null = null

const isTracking = computed(() => activeLog.value !== null)

const formattedTime = computed(() => {
  const hours = Math.floor(elapsedSeconds.value / 3600)
  const minutes = Math.floor((elapsedSeconds.value % 3600) / 60)
  const seconds = elapsedSeconds.value % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
})

async function loadActiveLog() {
  try {
    const log = await api.getActiveTimeLog(currentUserId.value)
    if (log && log.task_id === props.taskId) {
      activeLog.value = log
      startTimer()
    }
  } catch (e) {
    console.error('Failed to load active time log:', e)
  }
}

function startTimer() {
  if (!activeLog.value) return

  // Calculate initial elapsed time (backend sends UTC without 'Z' suffix)
  const raw = activeLog.value.started_at
  const startedAt = new Date(raw.endsWith('Z') ? raw : raw + 'Z').getTime()
  elapsedSeconds.value = Math.floor((Date.now() - startedAt) / 1000)

  // Start counting
  if (intervalId) clearInterval(intervalId)
  intervalId = window.setInterval(() => {
    elapsedSeconds.value++
  }, 1000)
}

function stopTimer() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
  elapsedSeconds.value = 0
}

async function startTracking() {
  if (loading.value || isTracking.value) return

  loading.value = true
  try {
    const log = await api.startTimeTracking(props.taskId, currentUserId.value)
    activeLog.value = log
    startTimer()
  } catch (e) {
    console.error('Failed to start time tracking:', e)
    alert(t('timeTracking.startError'))
  } finally {
    loading.value = false
  }
}

async function stopTracking() {
  if (loading.value || !isTracking.value || !activeLog.value) return

  loading.value = true
  try {
    const log = await api.stopTimeTracking(activeLog.value.id, currentUserId.value)
    stopTimer()
    activeLog.value = null

    // Emit updated time
    if (log.duration_seconds) {
      emit('timeUpdated', log.duration_seconds)
    }
  } catch (e) {
    console.error('Failed to stop time tracking:', e)
    alert(t('timeTracking.stopError'))
  } finally {
    loading.value = false
  }
}

watch(() => props.taskId, () => {
  stopTimer()
  activeLog.value = null
  loadActiveLog()
})

onMounted(loadActiveLog)

onUnmounted(() => {
  stopTimer()
})
</script>

<template>
  <div class="time-tracker">
    <button
      v-if="!isTracking"
      class="tracker-btn start-btn"
      :disabled="loading"
      @click="startTracking"
    >
      <AppIcon name="play" :size="14" class="btn-icon" />
      <span class="btn-text">{{ t('timeTracking.start') }}</span>
    </button>

    <div v-else class="tracking-active">
      <div class="timer-display">
        <AppIcon name="timer" :size="20" class="timer-icon pulse" />
        <span class="timer-value">{{ formattedTime }}</span>
      </div>
      <button
        class="tracker-btn stop-btn"
        :disabled="loading"
        @click="stopTracking"
      >
        <AppIcon name="stop" :size="14" class="btn-icon" />
        <span class="btn-text">{{ t('timeTracking.stop') }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.time-tracker {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.tracker-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-lighter);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tracker-btn:hover:not(:disabled) {
  background: var(--bg-highlight);
  border-color: var(--accent-blue);
}

.tracker-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.start-btn {
  background: linear-gradient(135deg, #9ece6a 0%, #73daca 100%);
  border-color: #9ece6a;
  color: var(--bg-dark);
}

.start-btn:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(158, 206, 106, 0.3);
  transform: translateY(-1px);
}

.stop-btn {
  background: linear-gradient(135deg, #f7768e 0%, #ff9e64 100%);
  border-color: #f7768e;
  color: var(--bg-dark);
}

.stop-btn:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(247, 118, 142, 0.3);
  transform: translateY(-1px);
}

.btn-icon {
  font-size: 1rem;
  line-height: 1;
}

.btn-text {
  font-weight: 600;
}

.tracking-active {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.timer-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.timer-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.timer-icon.pulse {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.1); }
}

.timer-value {
  font-size: 1.125rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  min-width: 4ch;
}

/* Responsive */
@media (max-width: 768px) {
  .time-tracker {
    gap: 0.5rem;
  }

  .tracker-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.8rem;
  }

  .btn-icon {
    font-size: 0.875rem;
  }

  .tracking-active {
    padding: 0.375rem 0.75rem;
    gap: 0.75rem;
  }

  .timer-icon {
    font-size: 1rem;
  }

  .timer-value {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .btn-text {
    display: none;
  }

  .tracker-btn {
    padding: 0.5rem;
    min-width: 36px;
    justify-content: center;
  }

  .btn-icon {
    font-size: 1rem;
  }
}
</style>
