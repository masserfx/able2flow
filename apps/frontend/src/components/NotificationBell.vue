<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type Notification } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import AppIcon from './AppIcon.vue'

const { t } = useI18n()
const api = useApi()
const toast = useToast()

// Mock user ID (TODO: Replace with auth)
const currentUserId = 'user_petr'

const notifications = ref<Notification[]>([])
const unreadCount = ref(0)
const showDropdown = ref(false)
const loading = ref(false)

let pollingInterval: number | null = null
let lastPollTime = new Date().toISOString()

const hasUnread = computed(() => unreadCount.value > 0)

async function loadNotifications() {
  try {
    notifications.value = await api.getMyNotifications(currentUserId, false, 20)
    const countData = await api.getUnreadCount(currentUserId)
    unreadCount.value = countData.unread_count
  } catch (e) {
    console.error('Failed to load notifications:', e)
  }
}

async function pollNotifications() {
  try {
    const newNotifs = await api.pollNotifications(lastPollTime, currentUserId)
    if (newNotifs.length > 0) {
      // Prepend new notifications
      notifications.value = [...newNotifs, ...notifications.value]

      // Update unread count
      const countData = await api.getUnreadCount(currentUserId)
      unreadCount.value = countData.unread_count

      // Show toast for first notification (FOMO effect)
      const firstNotif = newNotifs[0]
      if (firstNotif) {
        toast.show({
          title: firstNotif.title,
          message: firstNotif.message,
          type: 'info',
          icon: getNotificationIcon(firstNotif.notification_type),
          duration: 4000,
        })
      }

      // Play sound effect
      playNotificationSound()
    }
    lastPollTime = new Date().toISOString()
  } catch (e) {
    console.error('Failed to poll notifications:', e)
  }
}

function playNotificationSound() {
  try {
    // Simple beep sound using Web Audio API
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    oscillator.frequency.value = 800
    oscillator.type = 'sine'
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2)

    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.2)
  } catch (e) {
    // Silently fail if audio not supported
    console.debug('Audio not supported:', e)
  }
}

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value && notifications.value.length === 0) {
    loadNotifications()
  }
}

function closeDropdown() {
  showDropdown.value = false
}

async function markAsRead(notification: Notification) {
  if (notification.is_read) return

  try {
    await api.markNotificationRead(notification.id)
    notification.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (e) {
    console.error('Failed to mark notification as read:', e)
  }
}

async function markAllAsRead() {
  loading.value = true
  try {
    for (const notif of notifications.value) {
      if (!notif.is_read) {
        await api.markNotificationRead(notif.id)
        notif.is_read = true
      }
    }
    unreadCount.value = 0
  } catch (e) {
    console.error('Failed to mark all as read:', e)
  } finally {
    loading.value = false
  }
}

function getNotificationIcon(type: string): string {
  switch (type) {
    case 'task_claimed': return 'target'
    case 'task_completed': return 'check-circle'
    case 'points_awarded': return 'gem'
    case 'leaderboard': return 'trophy'
    case 'announcement': return 'megaphone'
    default: return 'bell'
  }
}

function formatTime(timestamp: string): string {
  const now = Date.now()
  const time = new Date(timestamp).getTime()
  const diff = Math.floor((now - time) / 1000)

  if (diff < 60) return t('common.justNow')
  if (diff < 3600) return t('common.minutesAgo', { count: Math.floor(diff / 60) })
  if (diff < 86400) return t('common.hoursAgo', { count: Math.floor(diff / 3600) })
  return t('common.daysAgo', { count: Math.floor(diff / 86400) })
}

// Start polling on mount
onMounted(() => {
  loadNotifications()

  // Poll every 10 seconds
  pollingInterval = window.setInterval(pollNotifications, 10000)
})

// Clean up on unmount
onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
})
</script>

<template>
  <div class="notification-bell">
    <button
      class="bell-button"
      :class="{ 'has-unread': hasUnread }"
      @click="toggleDropdown"
    >
      <AppIcon name="bell" :size="20" class="bell-icon" />
      <span v-if="hasUnread" class="unread-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <!-- Dropdown -->
    <Teleport to="body">
      <div
        v-if="showDropdown"
        class="notification-dropdown"
        @click.stop
      >
        <div class="dropdown-header">
          <h3>{{ $t('notifications.title') }}</h3>
          <button
            v-if="hasUnread"
            class="mark-all-read"
            :disabled="loading"
            @click="markAllAsRead"
          >
            {{ $t('notifications.markAllRead') }}
          </button>
        </div>

        <div v-if="notifications.length === 0" class="empty-state">
          <AppIcon name="bell-off" :size="48" class="empty-icon" />
          <p>{{ $t('notifications.noNotifications') }}</p>
        </div>

        <div v-else class="notifications-list">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.is_read }"
            @click="markAsRead(notification)"
          >
            <AppIcon :name="getNotificationIcon(notification.notification_type)" :size="24" class="notif-icon" />
            <div class="notif-content">
              <div class="notif-title">{{ notification.title }}</div>
              <div class="notif-message">{{ notification.message }}</div>
              <div class="notif-time">{{ formatTime(notification.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Backdrop -->
      <div
        v-if="showDropdown"
        class="notification-backdrop"
        @click="closeDropdown"
      />
    </Teleport>
  </div>
</template>

<style scoped>
.notification-bell {
  position: relative;
}

.bell-button {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.bell-button:hover {
  background: var(--bg-highlight);
  border-color: var(--accent-blue);
  color: var(--text-primary);
}

.bell-button.has-unread {
  animation: ring 2s ease-in-out infinite;
}

@keyframes ring {
  0%, 100% { transform: rotate(0deg); }
  10%, 30% { transform: rotate(-10deg); }
  20%, 40% { transform: rotate(10deg); }
  50% { transform: rotate(0deg); }
}

.bell-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: linear-gradient(135deg, #f7768e 0%, #ff9e64 100%);
  color: var(--bg-dark);
  font-size: 0.625rem;
  font-weight: 700;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  min-width: 18px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* Dropdown */
.notification-dropdown {
  position: fixed;
  top: 70px;
  right: 20px;
  width: 380px;
  max-height: 480px;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-lighter);
}

.dropdown-header h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.mark-all-read {
  padding: 0.375rem 0.75rem;
  background: var(--accent-blue);
  border: none;
  border-radius: 6px;
  color: var(--bg-dark);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.mark-all-read:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.mark-all-read:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
  display: block;
  margin-bottom: 0.5rem;
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
}

.notifications-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.notification-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 0.5rem;
}

.notification-item:hover {
  background: var(--bg-lighter);
}

.notification-item.unread {
  background: rgba(122, 162, 247, 0.1);
  border-left: 3px solid var(--accent-blue);
}

.notif-icon {
  font-size: 1.5rem;
  line-height: 1;
  flex-shrink: 0;
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.notif-message {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.375rem;
  line-height: 1.4;
}

.notif-time {
  font-size: 0.625rem;
  color: var(--text-muted);
  opacity: 0.7;
}

.notification-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: transparent;
}

/* Responsive */
@media (max-width: 768px) {
  .notification-dropdown {
    right: 10px;
    width: calc(100vw - 20px);
    max-width: 380px;
  }
}

@media (max-width: 480px) {
  .bell-button {
    width: 36px;
    height: 36px;
  }

  .bell-icon {
    font-size: 1.125rem;
  }

  .notification-dropdown {
    top: 60px;
    right: 5px;
    width: calc(100vw - 10px);
  }

  .dropdown-header {
    padding: 0.875rem 1rem;
  }

  .notification-item {
    padding: 0.625rem;
  }

  .notif-icon {
    font-size: 1.25rem;
  }
}
</style>
