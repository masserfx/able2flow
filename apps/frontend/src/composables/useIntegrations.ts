import { ref } from 'vue'
import { useAuth } from './useAuth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export interface IntegrationSettings {
  id: number
  user_id: string
  project_id: number | null
  integration_type: string
  settings: Record<string, unknown>
  enabled: boolean
}

export interface CalendarEvent {
  id: string
  summary: string
  start: { dateTime: string }
  end: { dateTime: string }
  description?: string
}

export interface LinkedDocument {
  id: number
  task_id: number
  provider: string
  external_id: string
  title: string
  url: string
}

export interface SlackChannel {
  id: string
  name: string
  is_private: boolean
}

export function useIntegrations() {
  const { getAuthHeaders, isProviderConnected } = useAuth()
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchWithAuth<T>(path: string, options?: RequestInit): Promise<T> {
    loading.value = true
    error.value = null

    try {
      const authHeaders = await getAuthHeaders()
      const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...options?.headers,
        },
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      throw e
    } finally {
      loading.value = false
    }
  }

  // Integration Settings
  async function getIntegrationSettings(): Promise<IntegrationSettings[]> {
    const data = await fetchWithAuth<{ settings: IntegrationSettings[] }>('/integrations/oauth/settings')
    return data.settings
  }

  async function saveIntegrationSettings(
    integrationType: string,
    settings: Record<string, unknown>,
    projectId?: number,
    enabled: boolean = true
  ) {
    return fetchWithAuth('/integrations/oauth/settings', {
      method: 'POST',
      body: JSON.stringify({
        integration_type: integrationType,
        settings,
        project_id: projectId,
        enabled,
      }),
    })
  }

  async function toggleIntegration(integrationType: string, enabled: boolean, projectId?: number) {
    const params = new URLSearchParams({ enabled: String(enabled) })
    if (projectId) params.append('project_id', String(projectId))

    return fetchWithAuth(`/integrations/oauth/settings/${integrationType}/toggle?${params}`, {
      method: 'PATCH',
    })
  }

  // Calendar
  async function getCalendars() {
    const data = await fetchWithAuth<{ calendars: unknown[] }>('/integrations/calendar/calendars')
    return data.calendars
  }

  async function getCalendarEvents(calendarId: string = 'primary', days: number = 30) {
    const data = await fetchWithAuth<{ events: CalendarEvent[] }>(
      `/integrations/calendar/events?calendar_id=${calendarId}&days=${days}`
    )
    return data.events
  }

  async function createCalendarEvent(
    summary: string,
    start: Date,
    end?: Date,
    description?: string,
    calendarId: string = 'primary'
  ) {
    return fetchWithAuth('/integrations/calendar/events', {
      method: 'POST',
      body: JSON.stringify({
        summary,
        start: start.toISOString(),
        end: end?.toISOString(),
        description,
        calendar_id: calendarId,
      }),
    })
  }

  async function syncTaskToCalendar(taskId: number, calendarId: string = 'primary') {
    return fetchWithAuth('/integrations/calendar/sync/task', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, calendar_id: calendarId }),
    })
  }

  async function syncAllTasksToCalendar(projectId?: number, calendarId: string = 'primary') {
    return fetchWithAuth('/integrations/calendar/sync/all', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, calendar_id: calendarId }),
    })
  }

  async function syncFromCalendar(projectId?: number, calendarId: string = 'primary') {
    return fetchWithAuth<{ completed: number; updated: number; checked: number }>('/integrations/calendar/sync/from-calendar', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, calendar_id: calendarId }),
    })
  }

  // Docs
  async function getLinkedDocuments(taskId: number): Promise<LinkedDocument[]> {
    const data = await fetchWithAuth<{ documents: LinkedDocument[] }>(`/integrations/docs/task/${taskId}`)
    return data.documents
  }

  async function createDocFromTask(taskId: number) {
    return fetchWithAuth('/integrations/docs/create-from-task', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId }),
    })
  }

  async function attachDocument(taskId: number, documentId: string) {
    return fetchWithAuth('/integrations/docs/attach', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, document_id: documentId }),
    })
  }

  async function unlinkDocument(taskId: number, documentId: string) {
    return fetchWithAuth(`/integrations/docs/task/${taskId}/document/${documentId}`, {
      method: 'DELETE',
    })
  }

  // Gmail
  async function getEmails(query?: string, maxResults: number = 10) {
    const params = new URLSearchParams({ max_results: String(maxResults) })
    if (query) params.append('query', query)

    const data = await fetchWithAuth<{ messages: unknown[] }>(`/integrations/gmail/messages?${params}`)
    return data.messages
  }

  async function createTaskFromEmail(messageId: string, projectId: number = 1) {
    return fetchWithAuth('/integrations/gmail/create-task-from-email', {
      method: 'POST',
      body: JSON.stringify({ message_id: messageId, project_id: projectId }),
    })
  }

  async function sendEmailNotification(to: string, incidentId?: number, taskId?: number) {
    return fetchWithAuth('/integrations/gmail/send-notification', {
      method: 'POST',
      body: JSON.stringify({ to, incident_id: incidentId, task_id: taskId }),
    })
  }

  // Google OAuth Token (from Clerk)
  async function getGoogleToken(): Promise<{ access_token: string; scopes: string[] }> {
    return fetchWithAuth('/integrations/oauth/google/token')
  }

  async function getGoogleUserInfo(): Promise<Record<string, unknown>> {
    return fetchWithAuth('/integrations/oauth/google/user-info')
  }

  async function syncGoogleTokenToBackend(): Promise<{ status: string; scopes: string[] }> {
    return fetchWithAuth('/integrations/oauth/google/sync-token', { method: 'POST' })
  }

  // Slack
  async function getSlackChannels(): Promise<SlackChannel[]> {
    const data = await fetchWithAuth<{ channels: SlackChannel[] }>('/integrations/slack/channels')
    return data.channels
  }

  async function sendSlackMessage(channel: string, text: string) {
    return fetchWithAuth('/integrations/slack/message', {
      method: 'POST',
      body: JSON.stringify({ channel, text }),
    })
  }

  async function notifyIncidentToSlack(channel: string, incidentId: number) {
    return fetchWithAuth('/integrations/slack/notify/incident', {
      method: 'POST',
      body: JSON.stringify({ channel, incident_id: incidentId }),
    })
  }

  async function notifyTaskToSlack(channel: string, taskId: number, eventType: string = 'created') {
    return fetchWithAuth('/integrations/slack/notify/task', {
      method: 'POST',
      body: JSON.stringify({ channel, task_id: taskId, event_type: eventType }),
    })
  }

  return {
    loading,
    error,
    isProviderConnected,

    // Settings
    getIntegrationSettings,
    saveIntegrationSettings,
    toggleIntegration,

    // Google OAuth
    getGoogleToken,
    getGoogleUserInfo,
    syncGoogleTokenToBackend,

    // Calendar
    getCalendars,
    getCalendarEvents,
    createCalendarEvent,
    syncTaskToCalendar,
    syncAllTasksToCalendar,
    syncFromCalendar,

    // Docs
    getLinkedDocuments,
    createDocFromTask,
    attachDocument,
    unlinkDocument,

    // Gmail
    getEmails,
    createTaskFromEmail,
    sendEmailNotification,

    // Slack
    getSlackChannels,
    sendSlackMessage,
    notifyIncidentToSlack,
    notifyTaskToSlack,
  }
}
