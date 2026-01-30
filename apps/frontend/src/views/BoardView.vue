<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi, type Task, type Column } from '../composables/useApi'

const api = useApi()
const columns = ref<Column[]>([])
const tasks = ref<Task[]>([])
const loading = ref(true)

const newTaskTitle = ref('')
const newTaskColumnId = ref<number | null>(null)
const showNewTaskForm = ref(false)

const draggedTask = ref<Task | null>(null)

async function loadBoard() {
  loading.value = true
  try {
    const [cols, allTasks] = await Promise.all([
      api.getColumns(),
      api.getTasks(),
    ])
    columns.value = cols
    tasks.value = allTasks
    if (cols.length > 0 && !newTaskColumnId.value) {
      newTaskColumnId.value = cols[0]?.id ?? null
    }
  } catch (e) {
    console.error('Failed to load board:', e)
  } finally {
    loading.value = false
  }
}

function getTasksForColumn(columnId: number) {
  return tasks.value
    .filter((t) => t.column_id === columnId)
    .sort((a, b) => a.position - b.position)
}

async function createTask() {
  if (!newTaskTitle.value.trim() || !newTaskColumnId.value) return
  try {
    await api.createTask({
      title: newTaskTitle.value,
      column_id: newTaskColumnId.value,
    })
    newTaskTitle.value = ''
    showNewTaskForm.value = false
    await loadBoard()
  } catch (e) {
    console.error('Failed to create task:', e)
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
  if (!confirm(`Delete "${task.title}"?`)) return
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

onMounted(loadBoard)
</script>

<template>
  <div class="board-view">
    <header class="page-header">
      <h1>Kanban Board</h1>
      <button class="primary" @click="showNewTaskForm = !showNewTaskForm">
        {{ showNewTaskForm ? '✕ Cancel' : '+ New Task' }}
      </button>
    </header>

    <!-- New Task Form -->
    <div v-if="showNewTaskForm" class="new-task-form card">
      <input
        v-model="newTaskTitle"
        type="text"
        placeholder="Task title"
        @keyup.enter="createTask"
      />
      <select v-model="newTaskColumnId">
        <option v-for="col in columns" :key="col.id" :value="col.id">
          {{ col.name }}
        </option>
      </select>
      <button class="primary" @click="createTask">Add Task</button>
    </div>

    <div v-if="loading" class="loading">Loading board...</div>

    <!-- Kanban Board -->
    <div v-else class="kanban-board">
      <div
        v-for="column in columns"
        :key="column.id"
        class="kanban-column"
        @dragover.prevent
        @drop="onDrop(column.id, getTasksForColumn(column.id).length)"
      >
        <div class="column-header" :style="{ borderTopColor: column.color }">
          <span class="column-name">{{ column.name }}</span>
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
          >
            <div class="task-header">
              <input
                type="checkbox"
                :checked="task.completed"
                @change="toggleTaskComplete(task)"
              />
              <span :class="['task-priority', getPriorityClass(task.priority)]">●</span>
            </div>
            <div class="task-title">{{ task.title }}</div>
            <div v-if="task.description" class="task-description">
              {{ task.description }}
            </div>
            <div class="task-footer">
              <span v-if="task.due_date" class="task-due">
                📅 {{ task.due_date }}
              </span>
              <button class="task-delete" @click="deleteTask(task)">✕</button>
            </div>
          </div>

          <!-- Drop zone for empty column -->
          <div
            v-if="getTasksForColumn(column.id).length === 0"
            class="empty-column"
            @dragover.prevent
            @drop="onDrop(column.id, 0)"
          >
            Drop tasks here
          </div>
        </div>
      </div>
    </div>
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

.new-task-form {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}

.new-task-form input {
  flex: 1;
}

.new-task-form select {
  width: 150px;
}

.loading {
  text-align: center;
  color: var(--text-muted);
  padding: 4rem;
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

.task-title {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.875rem;
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
</style>
