<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type Task, type Column, type Project, type Attachment } from '../composables/useApi'

const { t, te } = useI18n()
const api = useApi()

const props = defineProps<{
  show: boolean
  columns: Column[]
  projects: Project[]
  currentProjectId: number | null
  task?: Task | null
}>()

const emit = defineEmits<{
  close: []
  save: [data: TaskFormData]
  createProject: [data: NewProjectData]
}>()

export interface TaskFormData {
  title: string
  description: string
  project_id: number | null
  column_id: number | null
  priority: string
  due_date: string | null
  start_date: string | null
  end_date: string | null
}

export interface NewProjectData {
  name: string
  color: string
  description: string
}

const title = ref('')
const description = ref('')
const projectId = ref<number | null>(null)
const columnId = ref<number | null>(null)
const priority = ref('medium')

// New project form
const showNewProjectForm = ref(false)
const newProjectName = ref('')
const newProjectColor = ref('#7aa2f7')
const newProjectDescription = ref('')
const creatingProject = ref(false)

const projectColors = [
  '#7aa2f7', // blue
  '#9ece6a', // green
  '#e0af68', // yellow
  '#f7768e', // red
  '#bb9af7', // purple
  '#7dcfff', // cyan
  '#ff9e64', // orange
]

// Attachments
const attachments = ref<Attachment[]>([])
const uploadingFile = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const allowedFileTypes = '.jpg,.jpeg,.png,.gif,.webp,.svg,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md,.csv,.json,.zip,.rar,.7z'

async function loadAttachments() {
  if (props.task?.id) {
    try {
      attachments.value = await api.getAttachments(props.task.id)
    } catch (e) {
      console.error('Failed to load attachments:', e)
    }
  } else {
    attachments.value = []
  }
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !props.task?.id) return

  uploadingFile.value = true
  try {
    const attachment = await api.uploadAttachment(props.task.id, file)
    attachments.value.unshift(attachment)
  } catch (e) {
    console.error('Failed to upload file:', e)
    alert(e instanceof Error ? e.message : 'Upload failed')
  } finally {
    uploadingFile.value = false
    input.value = '' // Reset input
  }
}

async function deleteAttachment(attachment: Attachment) {
  if (!confirm(t('taskModal.deleteAttachmentConfirm', { name: attachment.original_name }))) return

  try {
    await api.deleteAttachment(attachment.id)
    attachments.value = attachments.value.filter(a => a.id !== attachment.id)
  } catch (e) {
    console.error('Failed to delete attachment:', e)
  }
}

function downloadAttachment(attachment: Attachment) {
  window.open(api.getAttachmentDownloadUrl(attachment.id), '_blank')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getFileIcon(fileType: string): string {
  const type = fileType.toLowerCase()
  if (['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'].includes(type)) return '🖼️'
  if (['.pdf'].includes(type)) return '📄'
  if (['.doc', '.docx'].includes(type)) return '📝'
  if (['.xls', '.xlsx'].includes(type)) return '📊'
  if (['.ppt', '.pptx'].includes(type)) return '📽️'
  if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(type)) return '📦'
  return '📎'
}
const dueDate = ref('')
const dueTime = ref('')
const startDate = ref('')
const startTime = ref('')
const endDate = ref('')
const endTime = ref('')
const useTimeRange = ref(false)

const priorities = [
  { value: 'low', label: 'taskModal.priorityLow', color: '#10b981' },
  { value: 'medium', label: 'taskModal.priorityMedium', color: '#f59e0b' },
  { value: 'high', label: 'taskModal.priorityHigh', color: '#ef4444' },
  { value: 'critical', label: 'taskModal.priorityCritical', color: '#dc2626' },
]

function translateColumn(name: string): string {
  const key = `columns.${name}`
  return te(key) ? t(key) : name
}

// Filter columns by selected project
const filteredColumns = computed(() => {
  if (!projectId.value) return props.columns
  return props.columns.filter(col => col.project_id === projectId.value)
})

// Update column when project changes
watch(projectId, (newProjectId) => {
  if (newProjectId) {
    const projectColumns = props.columns.filter(col => col.project_id === newProjectId)
    if (projectColumns.length > 0 && !projectColumns.some(col => col.id === columnId.value)) {
      columnId.value = projectColumns[0].id
    }
  }
})

// Reset form when modal opens
watch(() => props.show, (show) => {
  if (show) {
    if (props.task) {
      // Edit mode
      title.value = props.task.title
      description.value = props.task.description || ''
      projectId.value = props.task.project_id
      columnId.value = props.task.column_id
      priority.value = props.task.priority || 'medium'

      if (props.task.due_date) {
        const [date, time] = props.task.due_date.split('T')
        dueDate.value = date
        dueTime.value = time?.slice(0, 5) || '09:00'
      } else {
        dueDate.value = ''
        dueTime.value = ''
      }

      startDate.value = ''
      startTime.value = ''
      endDate.value = ''
      endTime.value = ''
      useTimeRange.value = false

      // Load attachments for existing task
      loadAttachments()
    } else {
      // Create mode - use current project
      title.value = ''
      description.value = ''
      projectId.value = props.currentProjectId
      const projectColumns = props.columns.filter(col => col.project_id === projectId.value)
      columnId.value = projectColumns[0]?.id ?? props.columns[0]?.id ?? null
      priority.value = 'medium'
      dueDate.value = ''
      dueTime.value = '09:00'
      startDate.value = ''
      startTime.value = '09:00'
      endDate.value = ''
      endTime.value = '10:00'
      useTimeRange.value = false
    }
  }
})

const isValid = computed(() => {
  return title.value.trim().length > 0 && columnId.value !== null
})

function formatDateTime(date: string, time: string): string | null {
  if (!date) return null
  const t = time || '00:00'
  return `${date}T${t}:00`
}

function save() {
  if (!isValid.value) return

  const data: TaskFormData = {
    title: title.value.trim(),
    description: description.value.trim(),
    project_id: projectId.value,
    column_id: columnId.value,
    priority: priority.value,
    due_date: formatDateTime(dueDate.value, dueTime.value),
    start_date: useTimeRange.value ? formatDateTime(startDate.value, startTime.value) : null,
    end_date: useTimeRange.value ? formatDateTime(endDate.value, endTime.value) : null,
  }

  emit('save', data)
}

function close() {
  showNewProjectForm.value = false
  emit('close')
}

function toggleNewProjectForm() {
  showNewProjectForm.value = !showNewProjectForm.value
  if (showNewProjectForm.value) {
    newProjectName.value = ''
    newProjectColor.value = '#7aa2f7'
    newProjectDescription.value = ''
  }
}

async function createNewProject() {
  if (!newProjectName.value.trim()) return

  creatingProject.value = true
  emit('createProject', {
    name: newProjectName.value.trim(),
    color: newProjectColor.value,
    description: newProjectDescription.value.trim(),
  })
}

// Called by parent after project is created
function onProjectCreated(newProject: Project) {
  creatingProject.value = false
  showNewProjectForm.value = false
  projectId.value = newProject.id
}

defineExpose({ onProjectCreated })
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="close">
      <div class="modal">
        <header class="modal-header">
          <h2>{{ task ? $t('taskModal.editTitle') : $t('taskModal.createTitle') }}</h2>
          <button class="close-btn" @click="close">&times;</button>
        </header>

        <div class="modal-body">
          <!-- Title -->
          <div class="form-group">
            <label>{{ $t('taskModal.name') }} *</label>
            <input
              v-model="title"
              type="text"
              :placeholder="$t('taskModal.namePlaceholder')"
              autofocus
            />
          </div>

          <!-- Description -->
          <div class="form-group">
            <label>{{ $t('taskModal.description') }}</label>
            <textarea
              v-model="description"
              rows="3"
              :placeholder="$t('taskModal.descriptionPlaceholder')"
            />
          </div>

          <!-- Project -->
          <div class="form-group">
            <div class="label-with-action">
              <label>{{ $t('taskModal.project') }}</label>
              <button
                type="button"
                class="add-new-btn"
                @click="toggleNewProjectForm"
              >
                {{ showNewProjectForm ? '✕' : '+ ' + $t('taskModal.newProject') }}
              </button>
            </div>

            <!-- New Project Form -->
            <div v-if="showNewProjectForm" class="new-project-form">
              <input
                v-model="newProjectName"
                type="text"
                :placeholder="$t('taskModal.projectNamePlaceholder')"
                class="project-name-input"
              />
              <div class="color-picker">
                <button
                  v-for="color in projectColors"
                  :key="color"
                  type="button"
                  class="color-btn"
                  :class="{ selected: newProjectColor === color }"
                  :style="{ backgroundColor: color }"
                  @click="newProjectColor = color"
                />
              </div>
              <button
                type="button"
                class="create-project-btn"
                :disabled="!newProjectName.trim() || creatingProject"
                @click="createNewProject"
              >
                {{ creatingProject ? $t('taskModal.creating') : $t('taskModal.createProject') }}
              </button>
            </div>

            <!-- Project Select -->
            <select v-else v-model="projectId">
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>

          <!-- Column & Priority Row -->
          <div class="form-row">
            <div class="form-group">
              <label>{{ $t('taskModal.column') }}</label>
              <select v-model="columnId">
                <option v-for="col in filteredColumns" :key="col.id" :value="col.id">
                  {{ translateColumn(col.name) }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>{{ $t('taskModal.priority') }}</label>
              <select v-model="priority">
                <option
                  v-for="p in priorities"
                  :key="p.value"
                  :value="p.value"
                >
                  {{ $t(p.label) }}
                </option>
              </select>
            </div>
          </div>

          <!-- Due Date Section -->
          <div class="form-section">
            <h3>{{ $t('taskModal.deadline') }}</h3>

            <div class="form-row">
              <div class="form-group">
                <label>{{ $t('taskModal.date') }}</label>
                <input v-model="dueDate" type="date" />
              </div>
              <div class="form-group">
                <label>{{ $t('taskModal.time') }}</label>
                <input v-model="dueTime" type="time" />
              </div>
            </div>
          </div>

          <!-- Time Range Toggle -->
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="useTimeRange" type="checkbox" />
              <span>{{ $t('taskModal.useTimeRange') }}</span>
            </label>
          </div>

          <!-- Time Range Section -->
          <div v-if="useTimeRange" class="form-section time-range">
            <h3>{{ $t('taskModal.timeRange') }}</h3>

            <div class="time-range-grid">
              <div class="form-group">
                <label>{{ $t('taskModal.startDate') }}</label>
                <input v-model="startDate" type="date" />
              </div>
              <div class="form-group">
                <label>{{ $t('taskModal.startTime') }}</label>
                <input v-model="startTime" type="time" />
              </div>
              <div class="form-group">
                <label>{{ $t('taskModal.endDate') }}</label>
                <input v-model="endDate" type="date" />
              </div>
              <div class="form-group">
                <label>{{ $t('taskModal.endTime') }}</label>
                <input v-model="endTime" type="time" />
              </div>
            </div>
          </div>

          <!-- Attachments Section (only for existing tasks) -->
          <div v-if="task" class="form-section attachments-section">
            <div class="attachments-header">
              <h3>{{ $t('taskModal.attachments') }}</h3>
              <button
                type="button"
                class="upload-btn"
                :disabled="uploadingFile"
                @click="triggerFileInput"
              >
                {{ uploadingFile ? $t('taskModal.uploading') : $t('taskModal.addAttachment') }}
              </button>
            </div>

            <!-- Hidden file input -->
            <input
              ref="fileInputRef"
              type="file"
              :accept="allowedFileTypes"
              style="display: none"
              @change="handleFileSelect"
            />

            <!-- Attachments list -->
            <div v-if="attachments.length > 0" class="attachments-list">
              <div
                v-for="attachment in attachments"
                :key="attachment.id"
                class="attachment-item"
              >
                <span class="attachment-icon">{{ getFileIcon(attachment.file_type) }}</span>
                <div class="attachment-info">
                  <span class="attachment-name" :title="attachment.original_name">
                    {{ attachment.original_name }}
                  </span>
                  <span class="attachment-size">{{ formatFileSize(attachment.file_size) }}</span>
                </div>
                <div class="attachment-actions">
                  <button
                    type="button"
                    class="action-btn download-btn"
                    :title="$t('taskModal.download')"
                    @click="downloadAttachment(attachment)"
                  >
                    ⬇️
                  </button>
                  <button
                    type="button"
                    class="action-btn delete-btn"
                    :title="$t('common.delete')"
                    @click="deleteAttachment(attachment)"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-else class="attachments-empty">
              {{ $t('taskModal.noAttachments') }}
            </div>
          </div>
        </div>

        <footer class="modal-footer">
          <button class="secondary" @click="close">{{ $t('taskModal.cancel') }}</button>
          <button class="primary" :disabled="!isValid" @click="save">
            {{ task ? $t('taskModal.save') : $t('taskModal.create') }}
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-lighter);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-muted);
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.9375rem;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-section {
  background: var(--bg-lighter);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.form-section h3 {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
  color: var(--accent-blue);
  font-weight: 600;
}

.form-section .form-group:last-child {
  margin-bottom: 0;
}

.time-range {
  border: 1px solid var(--accent-purple);
  background: rgba(168, 85, 247, 0.05);
}

.time-range h3 {
  color: var(--accent-purple);
}

.time-range-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-group {
  margin-bottom: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  background: var(--bg-lighter);
}

.modal-footer button {
  padding: 0.75rem 1.5rem;
}

.modal-footer button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* New Project Form */
.label-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.label-with-action label {
  margin-bottom: 0;
}

.add-new-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: transparent;
  border: 1px solid var(--accent-blue);
  color: var(--accent-blue);
  border-radius: 4px;
  cursor: pointer;
}

.add-new-btn:hover {
  background: var(--accent-blue);
  color: var(--bg-dark);
}

.new-project-form {
  background: var(--bg-lighter);
  border: 1px solid var(--accent-green);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.project-name-input {
  width: 100%;
}

.color-picker {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.color-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
}

.color-btn:hover {
  transform: scale(1.1);
}

.color-btn.selected {
  border-color: white;
  box-shadow: 0 0 0 2px var(--bg-dark);
}

.create-project-btn {
  background: var(--accent-green);
  border: none;
  color: var(--bg-dark);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.create-project-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.create-project-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Attachments Section */
.attachments-section {
  border: 1px solid var(--accent-blue);
  background: rgba(59, 130, 246, 0.05);
}

.attachments-section h3 {
  color: var(--accent-blue);
}

.attachments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.attachments-header h3 {
  margin: 0;
}

.upload-btn {
  padding: 0.4rem 0.75rem;
  font-size: 0.75rem;
  background: var(--accent-blue);
  border: none;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.upload-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-dark);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.attachment-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.attachment-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.attachment-name {
  font-size: 0.875rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-size {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.attachment-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}

.action-btn {
  padding: 0.25rem 0.5rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  line-height: 1;
}

.action-btn:hover {
  background: var(--bg-lighter);
}

.download-btn:hover {
  border-color: var(--accent-green);
}

.delete-btn:hover {
  border-color: var(--accent-red);
}

.attachments-empty {
  text-align: center;
  padding: 1rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-style: italic;
}
</style>
