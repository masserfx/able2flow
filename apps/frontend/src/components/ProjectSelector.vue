<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

onMounted(loadProjects)
</script>

<template>
  <div class="project-selector">
    <label class="selector-label">{{ t('projects.selectProject') }}</label>
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
  </div>
</template>

<style scoped>
.project-selector {
  padding: 0 1.5rem;
  margin-bottom: 1.5rem;
}

.selector-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
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
}

.selector-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.selector-select option {
  background: var(--bg-darker);
  color: var(--text-primary);
}
</style>
