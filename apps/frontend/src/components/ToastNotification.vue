<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps<{
  title: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
  icon?: string
  duration?: number
}>()

const emit = defineEmits<{
  close: []
}>()

const visible = ref(false)
const progress = ref(100)

const typeClass = props.type || 'info'
const duration = props.duration || 5000
let progressInterval: number | null = null

function close() {
  visible.value = false
  setTimeout(() => emit('close'), 300)
}

onMounted(() => {
  // Slide in animation
  setTimeout(() => {
    visible.value = true
  }, 50)

  // Progress bar
  const step = 100 / (duration / 50)
  progressInterval = window.setInterval(() => {
    progress.value -= step
    if (progress.value <= 0) {
      if (progressInterval) clearInterval(progressInterval)
      close()
    }
  }, 50)
})
</script>

<template>
  <div :class="['toast', typeClass, { visible }]" @click="close">
    <div class="toast-icon"><AppIcon :name="icon || 'bell'" :size="22" /></div>
    <div class="toast-content">
      <div class="toast-title">{{ title }}</div>
      <div class="toast-message">{{ message }}</div>
    </div>
    <button class="toast-close" @click.stop="close">✕</button>
    <div class="toast-progress" :style="{ width: progress + '%' }" />
  </div>
</template>

<style scoped>
.toast {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  min-width: 300px;
  max-width: 400px;
  cursor: pointer;
  transform: translateX(120%);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.toast.visible {
  transform: translateX(0);
  opacity: 1;
}

.toast:hover {
  transform: translateX(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
}

/* Type variants */
.toast.info {
  border-left: 4px solid var(--accent-blue);
}

.toast.success {
  border-left: 4px solid var(--accent-green);
}

.toast.warning {
  border-left: 4px solid var(--accent-yellow);
}

.toast.error {
  border-left: 4px solid var(--accent-red);
}

.toast-icon {
  font-size: 1.5rem;
  line-height: 1;
  flex-shrink: 0;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.toast-message {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  flex-shrink: 0;
}

.toast-close:hover {
  color: var(--text-primary);
}

.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
  transition: width 0.05s linear;
}

/* Responsive */
@media (max-width: 768px) {
  .toast {
    min-width: 280px;
    max-width: calc(100vw - 40px);
    padding: 0.875rem;
  }

  .toast-icon {
    font-size: 1.25rem;
  }

  .toast-title {
    font-size: 0.8rem;
  }

  .toast-message {
    font-size: 0.7rem;
  }
}
</style>
