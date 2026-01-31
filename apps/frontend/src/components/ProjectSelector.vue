<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type Project } from '../composables/useApi'

const { t } = useI18n()
const api = useApi()

const props = defineProps<{
  modelValue: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
  change: [value: number | null]
}>()

const projects = ref<Project[]>([])
const loading = ref(true)
const showNewForm = ref(false)
const showDeleteConfirm = ref(false)
const newProjectName = ref('')
const newProjectColor = ref('#7aa2f7')

const selectedProject = computed(() => {
  if (!props.modelValue) return null
  return projects.value.find(p => p.id === props.modelValue) || null
})

async function loadProjects() {
  loading.value = true
  try {
    projects.value = await api.getProjects()
  } catch (e) {
    console.error('Failed to load projects:', e)
  } finally {
    loading.value = false
  }
}

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement
  const value = target.value === '' ? null : Number(target.value)
  emit('update:modelValue', value)
  emit('change', value)
}

function getProjectColor(projectId: number | null): string {
  if (!projectId) return 'var(--text-muted)'
  const project = projects.value.find(p => p.id === projectId)
  return project?.color || 'var(--accent-blue)'
}

async function createProject() {
  if (!newProjectName.value.trim()) return
  try {
    const project = await api.createProject({
      name: newProjectName.value.trim(),
      color: newProjectColor.value,
    })
    projects.value.push(project)
    emit('update:modelValue', project.id)
    emit('change', project.id)
    newProjectName.value = ''
    showNewForm.value = false
  } catch (e) {
    console.error('Failed to create project:', e)
  }
}

async function deleteProject() {
  if (!props.modelValue) return
  try {
    await api.deleteProject(props.modelValue)
    projects.value = projects.value.filter(p => p.id !== props.modelValue)
    emit('update:modelValue', null)
    emit('change', null)
    showDeleteConfirm.value = false
  } catch (e) {
    console.error('Failed to delete project:', e)
  }
}

onMounted(loadProjects)
</script>

<template>
  <div class="project-selector">
    <div class="selector-header">
      <label class="selector-label">{{ t('projects.selectProject') }}</label>
      <div class="header-actions">
        <button
          class="icon-btn add-btn"
          @click="showNewForm = !showNewForm"
          :title="t('projects.newProject')"
        >
          {{ showNewForm ? '✕' : '+' }}
        </button>
        <button
          v-if="modelValue"
          class="icon-btn delete-btn"
          @click="showDeleteConfirm = true"
          :title="t('projects.delete')"
        >
          🗑
        </button>
      </div>
    </div>

    <div class="selector-wrapper">
      <span
        class="color-indicator"
        :style="{ backgroundColor: getProjectColor(modelValue) }"
      />
      <select
        :value="modelValue ?? ''"
        @change="onChange"
        :disabled="loading"
        class="selector-select"
      >
        <option value="">{{ t('projects.allProjects') }}</option>
        <option
          v-for="project in projects"
          :key="project.id"
          :value="project.id"
        >
          {{ project.name }}
        </option>
      </select>
    </div>

    <!-- New Project Form -->
    <div v-if="showNewForm" class="new-form">
      <div class="form-row">
        <input
          v-model="newProjectName"
          type="text"
          :placeholder="t('projects.projectName')"
          class="new-input"
          @keyup.enter="createProject"
        />
        <input
          v-model="newProjectColor"
          type="color"
          class="color-picker"
          :title="t('projects.color')"
        />
      </div>
      <button class="create-btn" @click="createProject">
        {{ t('projects.create') }}
      </button>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="showDeleteConfirm" class="delete-confirm">
      <p class="confirm-text">{{ t('projects.deleteConfirm', { name: selectedProject?.name }) }}</p>
      <div class="confirm-actions">
        <button class="cancel-btn" @click="showDeleteConfirm = false">
          {{ t('common.cancel') }}
        </button>
        <button class="danger-btn" @click="deleteProject">
          {{ t('projects.delete') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.project-selector {
  padding: 0 1rem;
  margin-bottom: 1.5rem;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.selector-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.header-actions {
  display: flex;
  gap: 0.25rem;
}

.selector-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-highlight);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  transition: border-color 0.2s;
}

.selector-wrapper:hover {
  border-color: var(--accent-blue);
}

.color-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.selector-select {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  outline: none;
  min-width: 0;
}

.selector-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.selector-select option {
  background: var(--bg-darker);
  color: var(--text-primary);
}

.icon-btn {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-highlight);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  transition: all 0.2s;
  flex-shrink: 0;
}

.icon-btn:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.delete-btn:hover {
  border-color: var(--accent-red);
  color: var(--accent-red);
}

.new-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-highlight);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.form-row {
  display: flex;
  gap: 0.5rem;
}

.new-input {
  flex: 1;
  min-width: 0;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 0.8rem;
}

.new-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.color-picker {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  padding: 2px;
  background: var(--bg-card);
  flex-shrink: 0;
}

.create-btn {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--accent-blue);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
}

.create-btn:hover {
  opacity: 0.9;
}

.delete-confirm {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-highlight);
  border: 1px solid var(--accent-red);
  border-radius: 8px;
}

.confirm-text {
  margin: 0 0 0.75rem 0;
  font-size: 0.8rem;
  color: var(--text-primary);
  line-height: 1.4;
  word-wrap: break-word;
}

.confirm-actions {
  display: flex;
  gap: 0.5rem;
}

.cancel-btn {
  flex: 1;
  padding: 0.375rem 0.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.75rem;
}

.cancel-btn:hover {
  border-color: var(--text-muted);
}

.danger-btn {
  flex: 1;
  padding: 0.375rem 0.5rem;
  background: var(--accent-red);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 0.75rem;
}

.danger-btn:hover {
  opacity: 0.9;
}
</style>
