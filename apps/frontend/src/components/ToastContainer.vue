<script setup lang="ts">
import { useToast } from '../composables/useToast'
import ToastNotification from './ToastNotification.vue'

const { toasts, remove } = useToast()
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <ToastNotification
        v-for="toast in toasts"
        :key="toast.id"
        :title="toast.title"
        :message="toast.message"
        :type="toast.type"
        :icon="toast.icon"
        :duration="toast.duration"
        @close="remove(toast.id)"
      />
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  pointer-events: none;
}

.toast-container > * {
  pointer-events: auto;
}

@media (max-width: 768px) {
  .toast-container {
    top: 70px;
    right: 10px;
    left: 10px;
  }
}
</style>
