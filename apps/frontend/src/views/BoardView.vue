<script setup lang="ts">
import { ref, computed, onMounted, inject, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type Task, type Column, type Project, type Attachment } from '../composables/useApi'
import TaskModal, { type TaskFormData, type NewProjectData } from '../components/TaskModal.vue'
import PointsBadge from '../components/PointsBadge.vue'
import AppIcon from '../components/AppIcon.vue'
import { useContextMenu } from '../composables/useContextMenu'

const { t, te } = useI18n()
const currentProjectId = inject<Ref<number | null>>('currentProjectId', ref(null))
const taskModalRef = ref<InstanceType<typeof TaskModal> | null>(null)

function translateColumn(name: string): string {
  const key = `columns.${name}`
  return te(key) ? t(key) : name
}
const api = useApi()
const columns = ref<Column[]>([])
const allColumns = ref<Column[]>([])
const projects = ref<Project[]>([])
const tasks = ref<Task[]>([])
const loading = ref(true)

const showTaskModal = ref(false)
const editingTask = ref<Task | null>(null)

const draggedTask = ref<Task | null>(null)

// Attachments map by task ID
const taskAttachments = ref<Map<number, Attachment[]>>(new Map())

// Local project selection for board (when "all projects" is selected globally)
const activeProjectId = ref<number | null>(null)

// Check if we're in "all projects" mode
const isAllProjectsMode = computed(() => currentProjectId.value === null)

// Get effective project ID for board display
const effectiveProjectId = computed(() => {
  if (isAllProjectsMode.value) {
    return activeProjectId.value
  }
  return currentProjectId.value
})

// Filter columns for display based on effective project
const displayColumns = computed(() => {
  if (!effectiveProjectId.value) {
    // No project selected yet, show first project's columns
    const firstProject = projects.value[0]
    if (firstProject) {
      return columns.value.filter(col => col.project_id === firstProject.id)
    }
    return []
  }
  return columns.value.filter(col => col.project_id === effectiveProjectId.value)
})

async function loadProjects() {
  try {
    projects.value = await api.getProjects()
  } catch (e) {
    console.error('Failed to load projects:', e)
  }
}

async function loadAllColumns() {
  try {
    // Load columns for all projects for the modal
    const allCols: Column[] = []
    for (const project of projects.value) {
      const cols = await api.getColumns(project.id)
      allCols.push(...cols)
    }
    allColumns.value = allCols
  } catch (e) {
    console.error('Failed to load all columns:', e)
  }
}

async function loadBoard() {
  loading.value = true
  try {
    if (isAllProjectsMode.value) {
      // Load all columns and tasks
      const allCols: Column[] = []
      const allTasks: Task[] = []
      for (const project of projects.value) {
        const [cols, projectTasks] = await Promise.all([
          api.getColumns(project.id),
          api.getTasks(undefined, project.id),
        ])
        allCols.push(...cols)
        allTasks.push(...projectTasks)
      }
      columns.value = allCols
      tasks.value = allTasks

      // Set active project to first if not set
      if (!activeProjectId.value && projects.value.length > 0) {
        const firstProject = projects.value[0]
        if (firstProject) {
          activeProjectId.value = firstProject.id
        }
      }
    } else {
      // Load specific project
      const projectId = currentProjectId.value ?? undefined
      const [cols, projectTasks] = await Promise.all([
        api.getColumns(projectId),
        api.getTasks(undefined, projectId),
      ])
      columns.value = cols
      tasks.value = projectTasks
      activeProjectId.value = currentProjectId.value
    }
    // Load attachments for all tasks
    await loadAttachments()
  } catch (e) {
    console.error('Failed to load board:', e)
  } finally {
    loading.value = false
  }
}

// When global project changes, reset active project
watch(currentProjectId, () => {
  if (!isAllProjectsMode.value) {
    activeProjectId.value = currentProjectId.value
  }
  loadBoard()
})

function selectProject(projectId: number) {
  activeProjectId.value = projectId
}

function getTasksForColumn(columnId: number) {
  return tasks.value
    .filter((t) => t.column_id === columnId)
    .sort((a, b) => a.position - b.position)
}

// Load attachments for all tasks
async function loadAttachments() {
  const attachmentsMap = new Map<number, Attachment[]>()

  // Load attachments in parallel for all tasks
  await Promise.all(
    tasks.value.map(async (task) => {
      try {
        const attachments = await api.getAttachments(task.id)
        if (attachments.length > 0) {
          attachmentsMap.set(task.id, attachments)
        }
      } catch (e) {
        console.error(`Failed to load attachments for task ${task.id}:`, e)
      }
    })
  )

  taskAttachments.value = attachmentsMap
}

// Get attachments for a specific task (images first)
function getTaskAttachments(taskId: number): Attachment[] {
  const attachments = taskAttachments.value.get(taskId) || []
  // Sort: images first, then other files
  return [...attachments].sort((a, b) => {
    const aIsImage = isImageAttachment(a)
    const bIsImage = isImageAttachment(b)
    if (aIsImage && !bIsImage) return -1
    if (!aIsImage && bIsImage) return 1
    return 0
  })
}

// Check if attachment is an image
function isImageAttachment(attachment: Attachment): boolean {
  const imageTypes = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
  return imageTypes.includes(attachment.file_type.toLowerCase())
}

// Get attachment preview URL
function getAttachmentUrl(attachment: Attachment): string {
  return api.getAttachmentDownloadUrl(attachment.id)
}

// Get file icon for non-image files
function getFileIcon(fileType: string): string {
  const type = fileType.toLowerCase()
  if (['.pdf', '.doc', '.docx'].includes(type)) return 'file-text'
  if (['.xls', '.xlsx'].includes(type)) return 'file-spreadsheet'
  if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(type)) return 'file-archive'
  if (['.txt', '.md', '.json', '.csv'].includes(type)) return 'file-text'
  return 'paperclip'
}

async function handleTaskSave(data: TaskFormData) {
  try {
    if (editingTask.value) {
      // Update existing task
      await api.updateTask(editingTask.value.id, {
        title: data.title,
        description: data.description || undefined,
        column_id: data.column_id ?? undefined,
        project_id: data.project_id ?? undefined,
        priority: data.priority,
        due_date: data.due_date ?? undefined,
      })
    } else {
      // Create new task
      await api.createTask({
        title: data.title,
        description: data.description || undefined,
        column_id: data.column_id ?? undefined,
        priority: data.priority,
        due_date: data.due_date ?? undefined,
        project_id: data.project_id ?? undefined,
      })
    }
    showTaskModal.value = false
    editingTask.value = null
    await loadBoard()  // This also reloads attachments
  } catch (e) {
    console.error('Failed to save task:', e)
  }
}

async function handleCreateProject(data: NewProjectData) {
  try {
    // Create the project
    const newProject = await api.createProject({
      name: data.name,
      color: data.color,
      description: data.description || undefined,
    })

    // Create default columns for the new project
    const defaultColumns = ['Backlog', 'To Do', 'In Progress', 'Done']
    const columnColors = ['#6b7280', '#3b82f6', '#f59e0b', '#10b981']

    for (let i = 0; i < defaultColumns.length; i++) {
      await api.createColumn({
        name: defaultColumns[i],
        project_id: newProject.id,
        position: i,
        color: columnColors[i],
      })
    }

    // Reload projects and columns
    await loadProjects()
    await loadAllColumns()

    // Notify TaskModal that project was created
    taskModalRef.value?.onProjectCreated(newProject)
  } catch (e) {
    console.error('Failed to create project:', e)
  }
}

async function toggleTaskComplete(task: Task) {
  try {
    await api.updateTask(task.id, { completed: !task.completed })
    await loadBoard()
  } catch (e) {
    console.error('Failed to toggle task:', e)
  }
}

async function deleteTask(task: Task) {
  if (!confirm(t('board.deleteConfirm', { title: task.title }))) return
  try {
    await api.deleteTask(task.id)
    await loadBoard()
  } catch (e) {
    console.error('Failed to delete task:', e)
  }
}

function onDragStart(task: Task) {
  draggedTask.value = task
}

function onDragEnd() {
  draggedTask.value = null
}

async function onDrop(columnId: number, position: number) {
  if (!draggedTask.value) return

  const task = draggedTask.value
  if (task.column_id === columnId && task.position === position) {
    draggedTask.value = null
    return
  }

  try {
    await api.moveTask(task.id, columnId, position)
    await loadBoard()
  } catch (e) {
    console.error('Failed to move task:', e)
  }

  draggedTask.value = null
}

function getPriorityClass(priority: string) {
  return `priority-${priority}`
}

async function openNewTaskModal() {
  // Ensure we have projects and all columns loaded
  if (projects.value.length === 0) {
    await loadProjects()
  }
  if (allColumns.value.length === 0) {
    await loadAllColumns()
  }
  editingTask.value = null
  showTaskModal.value = true
}

async function openEditTaskModal(task: Task) {
  // Ensure we have projects and all columns loaded
  if (projects.value.length === 0) {
    await loadProjects()
  }
  if (allColumns.value.length === 0) {
    await loadAllColumns()
  }
  editingTask.value = task
  showTaskModal.value = true
}

// Context Menu
const contextMenu = useContextMenu()

function showContextMenu(event: MouseEvent, task: Task) {
  const menuItems = [
    {
      label: t('board.contextMenu.duplicate'),
      icon: 'clipboard',
      action: async () => {
        try {
          await api.duplicateTask(task.id)
          await loadBoard()
          contextMenu.hide()
        } catch (e) {
          console.error('Failed to duplicate task:', e)
        }
      }
    },
    {
      label: t('board.contextMenu.move'),
      icon: 'folder',
      action: () => {
        // Show column submenu
        showColumnSubmenu(event, task)
      }
    },
    {
      label: t('board.contextMenu.convertToIncident'),
      icon: 'zap',
      action: async () => {
        try {
          // Create incident from task
          await api.createIncident({
            title: task.title,
            description: task.description || `Converted from task: ${task.title}`,
            severity: 'medium',
            status: 'open'
          })
          contextMenu.hide()
        } catch (e) {
          console.error('Failed to convert to incident:', e)
        }
      }
    },
    {
      label: t('board.contextMenu.changePriority'),
      icon: 'priority-high',
      action: async () => {
        try {
          // Cycle through priorities: low -> medium -> high -> critical -> low
          const priorities = ['low', 'medium', 'high', 'critical']
          const currentIndex = priorities.indexOf(task.priority)
          const nextPriority = priorities[(currentIndex + 1) % priorities.length]

          await api.updateTask(task.id, { priority: nextPriority })
          await loadBoard()
          contextMenu.hide()
        } catch (e) {
          console.error('Failed to change priority:', e)
        }
      }
    },
    {
      divider: true,
      label: '',
      action: () => {}
    },
    {
      label: task.archived ? t('board.contextMenu.unarchive') : t('board.contextMenu.archive'),
      icon: 'file-archive',
      action: async () => {
        try {
          await api.archiveTask(task.id)
          await loadBoard()
          contextMenu.hide()
        } catch (e) {
          console.error('Failed to archive task:', e)
        }
      }
    },
    {
      label: t('board.contextMenu.delete'),
      icon: 'trash',
      danger: true,
      action: async () => {
        if (!confirm(t('board.deleteConfirm', { title: task.title }))) {
          contextMenu.hide()
          return
        }
        try {
          await api.deleteTask(task.id)
          await loadBoard()
          contextMenu.hide()
        } catch (e) {
          console.error('Failed to delete task:', e)
        }
      }
    }
  ]

  contextMenu.show(event, menuItems)
}

function showColumnSubmenu(event: MouseEvent, task: Task) {
  const columnMenuItems = displayColumns.value.map(column => ({
    label: translateColumn(column.name),
    icon: 'folder',
    action: async () => {
      try {
        await api.moveTask(task.id, column.id, 0)
        await loadBoard()
        contextMenu.hide()
      } catch (e) {
        console.error('Failed to move task:', e)
      }
    }
  }))

  contextMenu.show(event, columnMenuItems)
}

onMounted(async () => {
  await loadProjects()
  await loadBoard()
  await loadAllColumns()
})
</script>

<template>
  <div class="board-view">
    <header class="page-header">
      <h1>{{ $t('board.title') }}</h1>
      <button class="primary" @click="openNewTaskModal">
        + {{ $t('board.newTask') }}
      </button>
    </header>

    <!-- Task Modal -->
    <TaskModal
      ref="taskModalRef"
      :show="showTaskModal"
      :columns="allColumns"
      :projects="projects"
      :current-project-id="currentProjectId"
      :task="editingTask"
      @close="showTaskModal = false"
      @save="handleTaskSave"
      @create-project="handleCreateProject"
    />

    <div v-if="loading" class="loading">{{ $t('board.loading') }}</div>

    <!-- Project Tabs (only in "all projects" mode) -->
    <div v-if="isAllProjectsMode && projects.length > 1" class="project-tabs">
      <button
        v-for="project in projects"
        :key="project.id"
        class="project-tab"
        :class="{ active: activeProjectId === project.id }"
        :style="{ '--project-color': project.color }"
        @click="selectProject(project.id)"
      >
        <span class="tab-indicator" :style="{ backgroundColor: project.color }"></span>
        {{ project.name }}
        <span class="tab-count">{{ tasks.filter(t => t.project_id === project.id).length }}</span>
      </button>
    </div>

    <!-- Kanban Board -->
    <div v-if="!loading" class="kanban-board">
      <div
        v-for="column in displayColumns"
        :key="column.id"
        class="kanban-column"
        @dragover.prevent
        @drop="onDrop(column.id, getTasksForColumn(column.id).length)"
      >
        <div class="column-header" :style="{ borderTopColor: column.color }">
          <span class="column-name">{{ translateColumn(column.name) }}</span>
          <span class="column-count">{{ getTasksForColumn(column.id).length }}</span>
        </div>

        <div class="column-tasks">
          <div
            v-for="(task, index) in getTasksForColumn(column.id)"
            :key="task.id"
            class="task-card"
            :class="{ completed: task.completed, dragging: draggedTask?.id === task.id }"
            draggable="true"
            @dragstart="onDragStart(task)"
            @dragend="onDragEnd"
            @dragover.prevent
            @drop.stop="onDrop(column.id, index)"
            @contextmenu.prevent="showContextMenu($event, task)"
          >
            <div class="task-header">
              <input
                type="checkbox"
                :checked="task.completed"
                @change="toggleTaskComplete(task)"
              />
              <span :class="['task-priority', getPriorityClass(task.priority)]">●</span>
              <PointsBadge :points="task.points" size="small" variant="minimal" />
              <span v-if="getTaskAttachments(task.id).length > 0" class="task-attachment-badge">
                <AppIcon name="paperclip" :size="12" /> {{ getTaskAttachments(task.id).length }}
              </span>
              <span v-if="task.assigned_to" class="task-assigned-badge" :title="`Assigned to ${task.assigned_to}`">
                <AppIcon name="user" :size="12" />
              </span>
            </div>
            <div class="task-title" @click="openEditTaskModal(task)">{{ task.title }}</div>
            <div v-if="task.description" class="task-description">
              {{ task.description }}
            </div>
            <div class="task-footer">
              <span v-if="task.due_date" class="task-due">
                {{ task.due_date }}
              </span>
              <button class="task-delete" @click="deleteTask(task)">✕</button>
            </div>

            <!-- Attachment previews -->
            <div v-if="getTaskAttachments(task.id).length > 0" class="task-attachments">
              <div class="attachments-preview">
                <template v-for="attachment in getTaskAttachments(task.id).slice(0, 3)" :key="attachment.id">
                  <!-- Image preview -->
                  <div v-if="isImageAttachment(attachment)" class="attachment-thumb image-thumb">
                    <img :src="getAttachmentUrl(attachment)" :alt="attachment.original_name" />
                  </div>
                  <!-- File icon preview -->
                  <div v-else class="attachment-thumb file-thumb">
                    <AppIcon :name="getFileIcon(attachment.file_type)" :size="16" class="file-icon" />
                    <span class="file-ext">{{ attachment.file_type }}</span>
                  </div>
                </template>
                <!-- More indicator -->
                <div v-if="getTaskAttachments(task.id).length > 3" class="attachment-more">
                  +{{ getTaskAttachments(task.id).length - 3 }}
                </div>
              </div>
            </div>
          </div>

          <!-- Drop zone for empty column -->
          <div
            v-if="getTasksForColumn(column.id).length === 0"
            class="empty-column"
            @dragover.prevent
            @drop="onDrop(column.id, 0)"
          >
            {{ $t('board.dropTasksHere') }}
          </div>
        </div>
      </div>
    </div>

    <!-- Context Menu -->
    <Teleport to="body">
      <div
        v-if="contextMenu.isVisible.value"
        class="context-menu"
        :style="{
          left: contextMenu.x.value + 'px',
          top: contextMenu.y.value + 'px'
        }"
        @click.stop
      >
        <template v-for="(item, index) in contextMenu.items.value" :key="index">
          <div v-if="item.divider" class="context-divider" />
          <div
            v-else
            class="context-item"
            :class="{ danger: item.danger }"
            @click="item.action"
          >
            <AppIcon v-if="item.icon" :name="item.icon" :size="16" class="context-icon" />
            <span class="context-label">{{ item.label }}</span>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.board-view {
  height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}

.page-header h1 {
  margin: 0;
}

.loading {
  text-align: center;
  color: var(--text-muted);
  padding: 4rem;
}

/* Project Tabs */
.project-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: var(--bg-lighter);
  border-radius: 12px;
  overflow-x: auto;
  flex-shrink: 0;
}

.project-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.project-tab:hover {
  background: var(--bg-highlight);
  color: var(--text-primary);
}

.project-tab.active {
  background: var(--bg-dark);
  border-color: var(--project-color, var(--accent-blue));
  color: var(--text-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.tab-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tab-count {
  background: var(--bg-darker);
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.project-tab.active .tab-count {
  background: var(--project-color, var(--accent-blue));
  color: var(--bg-dark);
}

.kanban-board {
  display: flex;
  gap: 1.5rem;
  overflow-x: auto;
  flex: 1;
  padding-bottom: 1rem;
}

.kanban-column {
  flex: 0 0 300px;
  background: var(--bg-lighter);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  max-height: 100%;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-top: 3px solid var(--accent-blue);
  border-radius: 12px 12px 0 0;
  background: var(--bg-highlight);
}

.column-name {
  font-weight: 600;
  color: var(--text-primary);
}

.column-count {
  background: var(--bg-darker);
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.column-tasks {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-card {
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0.75rem;
  cursor: grab;
  transition: all 0.2s;
}

.task-card:hover {
  border-color: var(--accent-blue);
}

.task-card.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.task-card.completed {
  opacity: 0.6;
}

.task-card.completed .task-title {
  text-decoration: line-through;
  color: var(--text-muted);
}

.task-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.task-header input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.task-priority {
  font-size: 0.5rem;
}

.task-attachment-badge {
  margin-left: auto;
  font-size: 0.7rem;
  color: var(--text-muted);
  background: var(--bg-lighter);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.task-assigned-badge {
  font-size: 0.7rem;
  margin-left: auto;
  opacity: 0.7;
}

.task-title {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
}

.task-title:hover {
  color: var(--accent-blue);
}

.task-description {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.75rem;
}

.task-due {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.task-delete {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.task-card:hover .task-delete {
  opacity: 1;
}

.task-delete:hover {
  color: var(--accent-red);
}

.empty-column {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.875rem;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  min-height: 100px;
}

/* Task Attachments Preview */
.task-attachments {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.attachments-preview {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.attachment-thumb {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  background: var(--bg-lighter);
  flex-shrink: 0;
}

.image-thumb {
  cursor: pointer;
}

.image-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-thumb:hover {
  border-color: var(--accent-blue);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.file-thumb {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.125rem;
}

.file-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.file-ext {
  font-size: 0.5rem;
  color: var(--text-muted);
  text-transform: uppercase;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-more {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: var(--bg-highlight);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
}

/* Responsive styles */
@media (max-width: 1024px) {
  .kanban-column {
    flex: 0 0 260px;
  }

  .column-tasks {
    padding: 0.75rem;
  }

  .task-card {
    padding: 0.625rem;
  }
}

@media (max-width: 768px) {
  .board-view {
    height: auto;
    min-height: calc(100vh - 8rem);
  }

  .page-header {
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .page-header h1 {
    font-size: 1.25rem;
    flex: 1;
  }

  .page-header .primary {
    font-size: 0.8rem;
    padding: 0.5rem 0.75rem;
  }

  /* Project tabs - horizontal scroll */
  .project-tabs {
    padding: 0.375rem;
    gap: 0.375rem;
    margin-bottom: 0.75rem;
    -webkit-overflow-scrolling: touch;
  }

  .project-tab {
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
  }

  .tab-indicator {
    width: 6px;
    height: 6px;
  }

  .tab-count {
    font-size: 0.7rem;
    padding: 0.1rem 0.375rem;
  }

  /* Kanban board - horizontal scroll with snap */
  .kanban-board {
    gap: 0.75rem;
    padding-bottom: 0.5rem;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
  }

  .kanban-column {
    flex: 0 0 85vw;
    max-width: 320px;
    scroll-snap-align: start;
    max-height: calc(100vh - 14rem);
  }

  .column-header {
    padding: 0.75rem;
  }

  .column-name {
    font-size: 0.9rem;
  }

  .column-tasks {
    padding: 0.5rem;
    gap: 0.5rem;
  }

  .task-card {
    padding: 0.5rem;
  }

  .task-title {
    font-size: 0.8rem;
  }

  .task-description {
    font-size: 0.7rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .task-footer {
    margin-top: 0.5rem;
  }

  .task-due {
    font-size: 0.7rem;
  }

  .task-delete {
    opacity: 1;
    padding: 0.375rem;
  }

  .empty-column {
    min-height: 80px;
    font-size: 0.8rem;
  }

  /* Attachments - smaller on mobile */
  .task-attachments {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
  }

  .attachment-thumb {
    width: 36px;
    height: 36px;
  }

  .attachment-more {
    width: 36px;
    height: 36px;
    font-size: 0.7rem;
  }

  .file-icon {
    font-size: 1rem;
  }

  .file-ext {
    display: none;
  }
}

@media (max-width: 480px) {
  .kanban-column {
    flex: 0 0 90vw;
  }

  .project-tab {
    padding: 0.375rem 0.625rem;
    font-size: 0.75rem;
  }

  .tab-count {
    display: none;
  }

  .task-attachment-badge {
    font-size: 0.65rem;
  }

  .task-attachments {
    display: none;
  }
}

/* Touch device optimizations */
@media (hover: none) and (pointer: coarse) {
  .task-card {
    cursor: default;
  }

  .task-delete {
    opacity: 1;
  }

  .task-card:active {
    transform: scale(0.98);
    border-color: var(--accent-blue);
  }

  /* Larger touch targets */
  .task-header input[type="checkbox"] {
    width: 20px;
    height: 20px;
  }
}

/* Context Menu - Tokyo Night Theme */
.context-menu {
  position: fixed;
  background: #1a1b26;
  border: 1px solid #414868;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(122, 162, 247, 0.1);
  min-width: 200px;
  padding: 4px;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.context-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #c0caf5;
  transition: all 0.2s ease;
  user-select: none;
}

.context-item:hover {
  background: #24283b;
  color: #7aa2f7;
}

.context-item.danger {
  color: #f7768e;
}

.context-item.danger:hover {
  background: rgba(247, 118, 142, 0.15);
  color: #f7768e;
}

.context-icon {
  font-size: 1rem;
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.context-label {
  flex: 1;
  white-space: nowrap;
}

.context-divider {
  height: 1px;
  background: #414868;
  margin: 4px 8px;
}
</style>
