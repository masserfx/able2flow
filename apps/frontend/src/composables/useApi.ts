import { ref } from 'vue'

const API_URL = 'http://localhost:8000/api'

export interface Task {
  id: number
  title: string
  description: string | null
  completed: boolean
  column_id: number | null
  position: number
  priority: string
  due_date: string | null
  created_at: string
}

export interface Column {
  id: number
  board_id: number
  name: string
  position: number
  color: string
  created_at: string
}

export interface Monitor {
  id: number
  name: string
  url: string
  check_interval: number
  last_status: string
  last_check: string | null
  created_at: string
}

export interface Incident {
  id: number
  monitor_id: number | null
  title: string
  status: string
  severity: string
  started_at: string
  acknowledged_at: string | null
  resolved_at: string | null
}

export interface AuditLog {
  id: number
  entity_type: string
  entity_id: number
  action: string
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  timestamp: string
}

export interface DashboardData {
  tasks: {
    total: number
    completed: number
    pending: number
    completion_rate: number
    by_priority: Record<string, number>
    by_column: Record<string, number>
    overdue: number
  }
  monitoring: {
    total_monitors: number
    by_status: Record<string, number>
    open_incidents: number
    avg_response_time_ms: number
    uptime_24h: number
  }
  activity: {
    total_actions: number
    recent_24h: number
  }
}

export function useApi() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `HTTP ${res.status}`)
      }
      return await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      throw e
    } finally {
      loading.value = false
    }
  }

  // Tasks
  const getTasks = (columnId?: number) =>
    fetchJson<Task[]>(columnId !== undefined ? `/tasks?column_id=${columnId}` : '/tasks')

  const createTask = (task: Partial<Task>) =>
    fetchJson<Task>('/tasks', { method: 'POST', body: JSON.stringify(task) })

  const updateTask = (id: number, task: Partial<Task>) =>
    fetchJson<Task>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(task) })

  const moveTask = (id: number, columnId: number, position: number) =>
    fetchJson<Task>(`/tasks/${id}/move`, {
      method: 'PUT',
      body: JSON.stringify({ column_id: columnId, position }),
    })

  const deleteTask = (id: number) =>
    fetchJson<{ message: string }>(`/tasks/${id}`, { method: 'DELETE' })

  // Columns
  const getColumns = () => fetchJson<Column[]>('/columns')

  const createColumn = (column: Partial<Column>) =>
    fetchJson<Column>('/columns', { method: 'POST', body: JSON.stringify(column) })

  const updateColumn = (id: number, column: Partial<Column>) =>
    fetchJson<Column>(`/columns/${id}`, { method: 'PUT', body: JSON.stringify(column) })

  const deleteColumn = (id: number) =>
    fetchJson<{ message: string }>(`/columns/${id}`, { method: 'DELETE' })

  // Monitors
  const getMonitors = () => fetchJson<Monitor[]>('/monitors')

  const createMonitor = (monitor: Partial<Monitor>) =>
    fetchJson<Monitor>('/monitors', { method: 'POST', body: JSON.stringify(monitor) })

  const checkMonitor = (id: number) =>
    fetchJson<{ is_up: boolean; status_code: number; response_time_ms: number }>(
      `/monitors/${id}/check`,
      { method: 'POST' }
    )

  const deleteMonitor = (id: number) =>
    fetchJson<{ message: string }>(`/monitors/${id}`, { method: 'DELETE' })

  // Incidents
  const getIncidents = (status?: string) =>
    fetchJson<Incident[]>(status ? `/incidents?status=${status}` : '/incidents')

  const getOpenIncidents = () => fetchJson<Incident[]>('/incidents/open')

  const createIncident = (incident: Partial<Incident>) =>
    fetchJson<Incident>('/incidents', { method: 'POST', body: JSON.stringify(incident) })

  const acknowledgeIncident = (id: number) =>
    fetchJson<Incident>(`/incidents/${id}/acknowledge`, { method: 'POST' })

  const resolveIncident = (id: number) =>
    fetchJson<Incident>(`/incidents/${id}/resolve`, { method: 'POST' })

  // Audit
  const getAuditLogs = (limit = 50) => fetchJson<AuditLog[]>(`/audit?limit=${limit}`)

  // Dashboard
  const getDashboard = () => fetchJson<DashboardData>('/dashboard')

  return {
    loading,
    error,
    // Tasks
    getTasks,
    createTask,
    updateTask,
    moveTask,
    deleteTask,
    // Columns
    getColumns,
    createColumn,
    updateColumn,
    deleteColumn,
    // Monitors
    getMonitors,
    createMonitor,
    checkMonitor,
    deleteMonitor,
    // Incidents
    getIncidents,
    getOpenIncidents,
    createIncident,
    acknowledgeIncident,
    resolveIncident,
    // Audit
    getAuditLogs,
    // Dashboard
    getDashboard,
  }
}
