<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { SignedIn, SignedOut, SignInButton, useAuth as useClerkAuth, useUser } from '@clerk/vue'
import { useAuth } from '../composables/useAuth'
import { useIntegrations } from '../composables/useIntegrations'
import IntegrationCard from '../components/IntegrationCard.vue'

const { t } = useI18n()
const { isSignedIn } = useClerkAuth()
const { user: clerkUser } = useUser()
const { connectedProviders, integrations, disconnectProvider, fetchCurrentUser, connectGoogle, isGoogleConnected } = useAuth()
const { loading, getIntegrationSettings, getSlackChannels, syncGoogleTokenToBackend, getGoogleUserInfo, getCalendarEvents, syncAllTasksToCalendar, syncFromCalendar } = useIntegrations()

const settings = ref<unknown[]>([])
const slackChannels = ref<unknown[]>([])
const activeModal = ref<string | null>(null)
const configuring = ref<string | null>(null)
const googleUserInfo = ref<Record<string, unknown> | null>(null)
const syncingGoogle = ref(false)

// Calendar events
const calendarEvents = ref<any[]>([])
const loadingEvents = ref(false)
const eventsError = ref<string | null>(null)

// Sync status
const syncingTasks = ref(false)
const syncResult = ref<{ synced: number; updated: number; deleted: number; failed: number; total: number } | null>(null)
const syncingFromCalendar = ref(false)
const syncFromResult = ref<{ completed: number; updated: number; checked: number } | null>(null)

// Current date/time
const currentDateTime = ref(new Date())

// Update time every second
setInterval(() => {
  currentDateTime.value = new Date()
}, 1000)

const formattedDate = computed(() => {
  return currentDateTime.value.toLocaleDateString('cs-CZ', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

const formattedTime = computed(() => {
  return currentDateTime.value.toLocaleTimeString('cs-CZ', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

// Check if we have calendar scopes (indicates full authorization)
const hasCalendarScopes = computed(() => {
  const scopes = getProviderScopes('google')
  return scopes.some(s =>
    s.includes('calendar') ||
    s.includes('gmail') ||
    s.includes('drive') ||
    s.includes('documents')
  )
})

// Integration definitions
const availableIntegrations = computed(() => [
  {
    name: 'Google Calendar',
    description: t('integrations.calendar.description'),
    icon: '📅',
    provider: 'google',
    type: 'calendar',
    connected: isGoogleConnected.value && hasCalendarScopes.value,
    needsScopes: isGoogleConnected.value && !hasCalendarScopes.value,
    scopes: getProviderScopes('google'),
  },
  {
    name: 'Google Docs',
    description: t('integrations.docs.description'),
    icon: '📄',
    provider: 'google',
    type: 'docs',
    connected: isGoogleConnected.value && hasCalendarScopes.value,
    needsScopes: isGoogleConnected.value && !hasCalendarScopes.value,
    scopes: getProviderScopes('google'),
  },
  {
    name: 'Gmail',
    description: t('integrations.gmail.description'),
    icon: '✉️',
    provider: 'google',
    type: 'gmail',
    connected: isGoogleConnected.value && hasCalendarScopes.value,
    needsScopes: isGoogleConnected.value && !hasCalendarScopes.value,
    scopes: getProviderScopes('google'),
  },
  {
    name: 'Slack',
    description: t('integrations.slack.description'),
    icon: '💬',
    provider: 'slack',
    type: 'slack',
    connected: connectedProviders.value.includes('slack'),
    needsScopes: false,
    scopes: getProviderScopes('slack'),
  },
])

function getProviderScopes(provider: string): string[] {
  if (provider === 'google' && clerkUser.value) {
    // Get scopes from Clerk external account
    const googleAccount = clerkUser.value.externalAccounts?.find(
      (acc: any) => acc.provider === 'oauth_google' || acc.provider === 'google'
    ) as any
    if (googleAccount?.approvedScopes) {
      // Parse scopes string into array
      return googleAccount.approvedScopes.split(' ').filter(Boolean)
    }
  }
  // Fallback to backend integrations
  const integration = integrations.value.find(i => i.provider === provider)
  return integration?.scopes || []
}

async function handleConnect(provider: string) {
  if (provider === 'google') {
    // Always try to (re)authorize Google with additional scopes
    try {
      await connectGoogle()
      // After redirect back, sync will happen automatically in loadData
    } catch (e) {
      console.error('Google connect error:', e)
      // If OAuth fails, show instructions modal
      activeModal.value = provider
    }
  } else {
    // Show modal with instructions for other providers
    activeModal.value = provider
  }
}

async function syncGoogleToken() {
  syncingGoogle.value = true
  try {
    // Sync token from Clerk to backend
    await syncGoogleTokenToBackend()

    // Fetch user info to verify connection works
    googleUserInfo.value = await getGoogleUserInfo()
  } catch (e) {
    console.error('Failed to sync Google token:', e)
  } finally {
    syncingGoogle.value = false
  }
}

async function loadCalendarEvents() {
  loadingEvents.value = true
  eventsError.value = null
  try {
    const events = await getCalendarEvents('primary', 14)
    calendarEvents.value = events
  } catch (e) {
    console.error('Failed to load calendar events:', e)
    eventsError.value = e instanceof Error ? e.message : 'Failed to load events'
  } finally {
    loadingEvents.value = false
  }
}

function formatEventDate(event: any): string {
  const start = event.start?.dateTime || event.start?.date
  if (!start) return ''
  const date = new Date(start)
  return date.toLocaleDateString('cs-CZ', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function syncTasksToCalendar() {
  syncingTasks.value = true
  syncResult.value = null
  try {
    const result = await syncAllTasksToCalendar()
    syncResult.value = result
    // Reload events to show newly synced
    await loadCalendarEvents()
  } catch (e) {
    console.error('Failed to sync tasks:', e)
    eventsError.value = e instanceof Error ? e.message : 'Failed to sync tasks'
  } finally {
    syncingTasks.value = false
  }
}

async function syncTasksFromCalendar() {
  syncingFromCalendar.value = true
  syncFromResult.value = null
  try {
    const result = await syncFromCalendar()
    syncFromResult.value = result
  } catch (e) {
    console.error('Failed to sync from calendar:', e)
    eventsError.value = e instanceof Error ? e.message : 'Failed to sync from calendar'
  } finally {
    syncingFromCalendar.value = false
  }
}

async function handleDisconnect(provider: string) {
  if (confirm(`Are you sure you want to disconnect ${provider}?`)) {
    await disconnectProvider(provider)
  }
}

function handleConfigure(type: string) {
  configuring.value = type
}

function closeModal() {
  activeModal.value = null
  configuring.value = null
}

async function loadData() {
  if (isSignedIn.value) {
    try {
      await fetchCurrentUser()
      settings.value = await getIntegrationSettings()

      // If Google is connected via Clerk, sync token to backend
      if (isGoogleConnected.value) {
        await syncGoogleToken()
      }

      if (connectedProviders.value.includes('slack')) {
        slackChannels.value = await getSlackChannels()
      }
    } catch (e) {
      console.error('Failed to load integration data:', e)
    }
  }
}

// Watch for auth state changes
watch(() => isSignedIn.value, (signedIn) => {
  if (signedIn) {
    loadData()
  }
}, { immediate: true })

onMounted(loadData)
</script>

<template>
  <div class="integrations-view">
    <header class="page-header">
      <h1>{{ t('integrations.title') }}</h1>
      <p class="page-description">{{ t('integrations.description') }}</p>
    </header>

    <SignedOut>
      <div class="auth-notice">
        <div class="notice-icon">🔐</div>
        <div class="notice-content">
          <h3>{{ t('integrations.signInRequired') }}</h3>
          <p>{{ t('integrations.signInDescription') }}</p>
          <SignInButton mode="modal">
            <button class="btn btn-primary">Sign In</button>
          </SignInButton>
        </div>
      </div>
    </SignedOut>

    <SignedIn>
      <section class="integrations-grid">
        <IntegrationCard
          v-for="integration in availableIntegrations"
          :key="integration.type"
          :name="integration.name"
          :description="integration.description"
          :icon="integration.icon"
          :provider="integration.provider"
          :connected="integration.connected"
          :needs-scopes="integration.needsScopes"
          :scopes="integration.scopes"
          :loading="loading || syncingGoogle"
          @connect="handleConnect(integration.provider)"
          @disconnect="handleDisconnect(integration.provider)"
          @configure="handleConfigure(integration.type)"
        />
      </section>

      <!-- Calendar Events Section -->
      <section v-if="hasCalendarScopes" class="calendar-section">
        <div class="current-datetime">
          <div class="datetime-date">{{ formattedDate }}</div>
          <div class="datetime-time">{{ formattedTime }}</div>
        </div>

        <div class="section-header">
          <h2>Google Calendar Events</h2>
          <div class="header-actions">
            <button
              class="btn btn-secondary"
              :disabled="syncingTasks"
              @click="syncTasksToCalendar"
            >
              <span v-if="syncingTasks" class="loading-spinner"></span>
              {{ syncingTasks ? 'Syncing...' : 'Sync Tasks to Calendar' }}
            </button>
            <button
              class="btn btn-warning"
              :disabled="syncingFromCalendar"
              @click="syncTasksFromCalendar"
              title="Mark deleted calendar events as completed tasks"
            >
              <span v-if="syncingFromCalendar" class="loading-spinner"></span>
              {{ syncingFromCalendar ? 'Syncing...' : 'Sync from Calendar' }}
            </button>
            <button
              class="btn btn-primary"
              :disabled="loadingEvents"
              @click="loadCalendarEvents"
            >
              <span v-if="loadingEvents" class="loading-spinner"></span>
              {{ loadingEvents ? 'Loading...' : 'Load Events' }}
            </button>
          </div>
        </div>

        <div v-if="syncResult" class="sync-result">
          {{ syncResult.total }} tasks:
          <span v-if="syncResult.synced > 0" class="sync-created">{{ syncResult.synced }} created</span>
          <span v-if="syncResult.updated > 0" class="sync-updated-result">{{ syncResult.updated }} updated</span>
          <span v-if="syncResult.deleted > 0" class="sync-deleted">{{ syncResult.deleted }} deleted</span>
          <span v-if="syncResult.failed > 0" class="sync-failed">({{ syncResult.failed }} failed)</span>
          <span v-if="syncResult.synced === 0 && syncResult.updated === 0 && syncResult.deleted === 0 && syncResult.failed === 0">
            all up to date
          </span>
        </div>

        <div v-if="syncFromResult" class="sync-result sync-from-result">
          Checked {{ syncFromResult.checked }} synced tasks
          <span v-if="syncFromResult.completed > 0" class="sync-completed">
            - {{ syncFromResult.completed }} completed
          </span>
          <span v-if="syncFromResult.updated > 0" class="sync-updated">
            - {{ syncFromResult.updated }} updated
          </span>
          <span v-if="syncFromResult.completed === 0 && syncFromResult.updated === 0">
            - no changes
          </span>
        </div>

        <div v-if="eventsError" class="error-message">
          {{ eventsError }}
        </div>

        <div v-if="calendarEvents.length > 0" class="events-list">
          <div
            v-for="event in calendarEvents"
            :key="event.id"
            class="event-item"
          >
            <div class="event-icon">📅</div>
            <div class="event-content">
              <div class="event-title">{{ event.summary || '(No title)' }}</div>
              <div class="event-time">{{ formatEventDate(event) }}</div>
            </div>
            <a
              v-if="event.htmlLink"
              :href="event.htmlLink"
              target="_blank"
              class="event-link"
              title="Open in Google Calendar"
            >
              ↗
            </a>
          </div>
        </div>

        <div v-else-if="!loadingEvents && calendarEvents.length === 0" class="no-events">
          Click "Load Events" to fetch your upcoming calendar events.
        </div>
      </section>
    </SignedIn>

    <!-- OAuth Instructions Modal -->
    <div v-if="activeModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <button class="modal-close" @click="closeModal">×</button>

        <template v-if="activeModal === 'google'">
          <h2>Connect Google Services</h2>
          <p>To connect Google Calendar, Docs, and Gmail:</p>
          <ol>
            <li>Go to your Clerk Dashboard</li>
            <li>Enable Google OAuth provider</li>
            <li>Add the required scopes: calendar, gmail.modify, documents</li>
            <li>Sign out and sign in again to grant permissions</li>
          </ol>
          <div class="modal-actions">
            <a
              href="https://dashboard.clerk.com"
              target="_blank"
              class="btn btn-google"
            >
              <span class="google-icon">G</span>
              Open Clerk Dashboard
            </a>
          </div>
        </template>

        <template v-else-if="activeModal === 'slack'">
          <h2>Connect Slack</h2>
          <p>To connect Slack notifications:</p>
          <ol>
            <li>Create a Slack App at api.slack.com</li>
            <li>Add Bot Token Scopes: chat:write, channels:read</li>
            <li>Install the app to your workspace</li>
            <li>Copy the Bot Token to your .env file</li>
          </ol>
          <div class="modal-actions">
            <a
              href="https://api.slack.com/apps"
              target="_blank"
              class="btn btn-slack"
            >
              <span class="slack-icon">#</span>
              Open Slack API
            </a>
          </div>
        </template>
      </div>
    </div>

    <!-- Configuration Modal -->
    <div v-if="configuring" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <button class="modal-close" @click="closeModal">×</button>

        <template v-if="configuring === 'calendar'">
          <h2>Calendar Settings</h2>
          <div class="config-form">
            <label class="config-option">
              <input type="checkbox" checked />
              <span>Sync task due dates to calendar</span>
            </label>
            <label class="config-option">
              <input type="checkbox" />
              <span>Create events for incidents</span>
            </label>
            <div class="form-group">
              <label>Default calendar</label>
              <select>
                <option value="primary">Primary Calendar</option>
              </select>
            </div>
          </div>
        </template>

        <template v-else-if="configuring === 'slack'">
          <h2>Slack Settings</h2>
          <div class="config-form">
            <div class="form-group">
              <label>Notification channel</label>
              <select>
                <option value="">Select channel...</option>
                <option v-for="ch in slackChannels" :key="(ch as any).id" :value="(ch as any).id">
                  #{{ (ch as any).name }}
                </option>
              </select>
            </div>
            <label class="config-option">
              <input type="checkbox" checked />
              <span>Notify on new incidents</span>
            </label>
            <label class="config-option">
              <input type="checkbox" />
              <span>Notify on task completion</span>
            </label>
          </div>
        </template>

        <template v-else-if="configuring === 'gmail'">
          <h2>Gmail Settings</h2>
          <div class="config-form">
            <label class="config-option">
              <input type="checkbox" checked />
              <span>Enable email notifications</span>
            </label>
            <label class="config-option">
              <input type="checkbox" />
              <span>Send daily digest</span>
            </label>
            <div class="form-group">
              <label>Notification email</label>
              <input type="email" placeholder="your@email.com" />
            </div>
          </div>
        </template>

        <template v-else-if="configuring === 'docs'">
          <h2>Google Docs Settings</h2>
          <div class="config-form">
            <label class="config-option">
              <input type="checkbox" checked />
              <span>Enable document linking</span>
            </label>
            <label class="config-option">
              <input type="checkbox" />
              <span>Auto-create docs for new tasks</span>
            </label>
          </div>
        </template>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="closeModal">Save Settings</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.integrations-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.page-description {
  color: var(--text-muted);
  margin: 0;
}

.auth-notice {
  display: flex;
  gap: 1rem;
  padding: 2rem;
  background-color: var(--bg-darker);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  text-align: center;
  flex-direction: column;
  align-items: center;
}

.notice-icon {
  font-size: 3rem;
}

.notice-content h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
}

.notice-content p {
  margin: 0 0 1rem 0;
  color: var(--text-muted);
}

.integrations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--bg-darker);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  max-width: 480px;
  width: 100%;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--text-muted);
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.modal-close:hover {
  background-color: var(--bg-highlight);
  color: var(--text-primary);
}

.modal-content h2 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.modal-content ol {
  margin: 1rem 0;
  padding-left: 1.5rem;
  color: var(--text-secondary);
}

.modal-content li {
  margin-bottom: 0.5rem;
}

.modal-actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--accent-blue);
  color: white;
}

.btn-secondary {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-warning {
  background-color: var(--accent-orange, #f59e0b);
  color: white;
}

.btn-google {
  background-color: #4285f4;
  color: white;
}

.btn-slack {
  background-color: #4a154b;
  color: white;
}

.google-icon,
.slack-icon {
  font-weight: bold;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.config-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  color: var(--text-secondary);
}

.config-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.form-group select,
.form-group input {
  padding: 0.5rem 0.75rem;
  background-color: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 0.875rem;
}

/* Calendar Section */
.calendar-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background-color: var(--bg-darker);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.current-datetime {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple, #a855f7) 100%);
  border-radius: 10px;
  color: white;
}

.datetime-date {
  font-size: 1.25rem;
  font-weight: 600;
  text-transform: capitalize;
}

.datetime-time {
  font-size: 2rem;
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.sync-result {
  padding: 0.75rem 1rem;
  background-color: rgba(34, 197, 94, 0.1);
  border: 1px solid var(--accent-green);
  border-radius: 8px;
  color: var(--accent-green);
  margin-bottom: 1rem;
}

.sync-failed {
  color: var(--accent-red, #ef4444);
}

.sync-created {
  color: var(--accent-green);
  font-weight: 500;
  margin-right: 0.5rem;
}

.sync-updated-result {
  color: var(--accent-blue);
  font-weight: 500;
  margin-right: 0.5rem;
}

.sync-deleted {
  color: var(--accent-orange, #f59e0b);
  font-weight: 500;
  margin-right: 0.5rem;
}

.sync-from-result {
  background-color: rgba(249, 115, 22, 0.1);
  border-color: var(--accent-orange, #f59e0b);
  color: var(--accent-orange, #f59e0b);
}

.sync-completed {
  color: var(--accent-green);
  font-weight: 500;
}

.sync-updated {
  color: var(--accent-blue);
  font-weight: 500;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.event-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background-color: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: border-color 0.2s;
}

.event-item:hover {
  border-color: var(--accent-blue);
}

.event-icon {
  font-size: 1.25rem;
}

.event-content {
  flex: 1;
}

.event-title {
  font-weight: 500;
  color: var(--text-primary);
}

.event-time {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.event-link {
  color: var(--accent-blue);
  text-decoration: none;
  font-size: 1.25rem;
  padding: 0.25rem;
}

.event-link:hover {
  color: var(--accent-blue-hover);
}

.no-events {
  color: var(--text-muted);
  text-align: center;
  padding: 2rem;
}

.error-message {
  color: var(--accent-red, #ef4444);
  background-color: rgba(239, 68, 68, 0.1);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
