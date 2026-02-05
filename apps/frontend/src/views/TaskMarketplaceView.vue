<script setup lang="ts">
import { ref, computed, onMounted, inject, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type Task, type Project } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import AppIcon from '../components/AppIcon.vue'

const { t } = useI18n()
const api = useApi()
const { user } = useAuth()
const currentProjectId = inject<Ref<number | null>>('currentProjectId', ref(null))

const tasks = ref<Task[]>([])
const projects = ref<Project[]>([])
const loading = ref(true)
const claimingTaskId = ref<number | null>(null)
const sortBy = ref<'points' | 'newest'>('points')

const currentUserId = computed(() => user.value?.id || 'user_petr')

// Filter by project
const filteredTasks = computed(() => {
  let filtered = tasks.value

  if (currentProjectId.value !== null) {
    filtered = filtered.filter(t => t.project_id === currentProjectId.value)
  }

  // Sort
  if (sortBy.value === 'points') {
    return [...filtered].sort((a, b) => (b.points || 0) - (a.points || 0))
  } else {
    return [...filtered].sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }
})

async function loadProjects() {
  try {
    projects.value = await api.getProjects()
  } catch (e) {
    console.error('Failed to load projects:', e)
  }
}

async function loadMarketplace() {
  loading.value = true
  try {
    const projectId = currentProjectId.value ?? undefined
    tasks.value = await api.getMarketplaceTasks(projectId)
  } catch (e) {
    console.error('Failed to load marketplace:', e)
  } finally {
    loading.value = false
  }
}

async function claimTask(task: Task) {
  if (claimingTaskId.value) return

  claimingTaskId.value = task.id
  try {
    await api.assignTaskToMe(task.id, currentUserId.value, user.value?.name || undefined, user.value?.email || undefined, user.value?.image_url || undefined)
    // Remove from marketplace
    tasks.value = tasks.value.filter(t => t.id !== task.id)
  } catch (e) {
    console.error('Failed to claim task:', e)
    alert(t('marketplace.claimError'))
  } finally {
    claimingTaskId.value = null
  }
}

function getProjectName(projectId: number | null): string {
  if (!projectId) return ''
  const project = projects.value.find(p => p.id === projectId)
  return project?.name || ''
}

function getProjectColor(projectId: number | null): string {
  if (!projectId) return '#7aa2f7'
  const project = projects.value.find(p => p.id === projectId)
  return project?.color || '#7aa2f7'
}

function getPriorityIconName(priority: string): string {
  switch (priority) {
    case 'critical': return 'priority-critical'
    case 'high': return 'priority-high'
    case 'medium': return 'priority-medium'
    case 'low': return 'priority-low'
    default: return 'priority-low'
  }
}

function formatEstimate(minutes: number | null): string {
  if (!minutes) return ''
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
}

watch(currentProjectId, loadMarketplace)

onMounted(async () => {
  await loadProjects()
  await loadMarketplace()
})
</script>

<template>
  <div class="marketplace-view">
    <header class="page-header">
      <div class="header-content">
        <h1><AppIcon name="target" :size="28" /> {{ $t('marketplace.title') }}</h1>
        <p class="subtitle">{{ $t('marketplace.subtitle') }}</p>
      </div>

      <div class="header-controls">
        <div class="sort-buttons">
          <button
            :class="['sort-btn', { active: sortBy === 'points' }]"
            @click="sortBy = 'points'"
          >
            <AppIcon name="gem" :size="16" /> {{ $t('marketplace.byPoints') }}
          </button>
          <button
            :class="['sort-btn', { active: sortBy === 'newest' }]"
            @click="sortBy = 'newest'"
          >
            <AppIcon name="clock" :size="16" /> {{ $t('marketplace.newest') }}
          </button>
        </div>
        <button class="refresh-btn" @click="loadMarketplace">
          <AppIcon name="refresh" :size="16" /> {{ $t('common.refresh') }}
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading">
      {{ $t('common.loading') }}
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredTasks.length === 0" class="empty-state">
      <AppIcon name="target" :size="64" class="empty-icon" />
      <h3>{{ $t('marketplace.noTasks') }}</h3>
      <p>{{ $t('marketplace.noTasksDesc') }}</p>
    </div>

    <!-- Task Grid -->
    <div v-else class="marketplace-grid">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="marketplace-card"
      >
        <!-- Points Badge -->
        <div class="points-badge">
          <span class="points-value">{{ task.points || 1 }}</span>
          <span class="points-label">{{ $t('marketplace.points') }}</span>
        </div>

        <!-- Priority Icon -->
        <div class="priority-badge">
          <AppIcon :name="getPriorityIconName(task.priority)" :size="22" />
        </div>

        <!-- Task Content -->
        <div class="task-content">
          <h3 class="task-title">{{ task.title }}</h3>

          <p v-if="task.description" class="task-description">
            {{ task.description }}
          </p>

          <!-- Meta Info -->
          <div class="task-meta">
            <span
              v-if="task.project_id"
              class="meta-item project-tag"
              :style="{
                borderColor: getProjectColor(task.project_id),
                color: getProjectColor(task.project_id)
              }"
            >
              <AppIcon name="folder" :size="14" /> {{ getProjectName(task.project_id) }}
            </span>

            <span v-if="task.estimated_minutes" class="meta-item">
              <AppIcon name="timer" :size="14" /> {{ formatEstimate(task.estimated_minutes) }}
            </span>

            <span v-if="task.due_date" class="meta-item">
              <AppIcon name="calendar" :size="14" /> {{ task.due_date }}
            </span>
          </div>
        </div>

        <!-- Claim Button -->
        <button
          class="claim-btn"
          :disabled="claimingTaskId === task.id"
          @click="claimTask(task)"
        >
          <AppIcon v-if="claimingTaskId === task.id" name="clock" :size="18" />
          <AppIcon v-else name="target" :size="18" />
          {{ claimingTaskId === task.id ? $t('marketplace.claiming') : $t('marketplace.claim') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.marketplace-view {
  padding: 0;
  min-height: calc(100vh - 4rem);
}

.page-header {
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.header-content h1 {
  margin: 0;
  font-size: 2rem;
  background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0.5rem 0 0 0;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.header-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.sort-buttons {
  display: flex;
  gap: 0.5rem;
  background: var(--bg-lighter);
  padding: 0.25rem;
  border-radius: 8px;
}

.sort-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.sort-btn:hover {
  background: var(--bg-highlight);
  color: var(--text-primary);
}

.sort-btn.active {
  background: var(--accent-blue);
  color: var(--bg-dark);
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: var(--bg-highlight);
  border-color: var(--accent-blue);
  color: var(--text-primary);
}

.loading {
  text-align: center;
  color: var(--text-muted);
  padding: 4rem;
  font-size: 1.125rem;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-secondary);
  font-size: 1.25rem;
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
}

/* Marketplace Grid */
.marketplace-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
  padding-bottom: 2rem;
}

.marketplace-card {
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.25rem;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow: hidden;
}

.marketplace-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #7aa2f7, #bb9af7);
  opacity: 0;
  transition: opacity 0.3s;
}

.marketplace-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
}

.marketplace-card:hover::before {
  opacity: 1;
}

/* Points Badge */
.points-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 100%);
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4px 12px rgba(122, 162, 247, 0.3);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.points-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--bg-dark);
  line-height: 1;
}

.points-label {
  font-size: 0.625rem;
  color: var(--bg-dark);
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.125rem;
}

/* Priority Badge */
.priority-badge {
  position: absolute;
  top: 1rem;
  left: 1rem;
  font-size: 1.25rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

/* Task Content */
.task-content {
  margin-top: 2rem;
  flex: 1;
}

.task-title {
  margin: 0 0 0.75rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.task-description {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
  color: var(--text-muted);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.625rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.project-tag {
  font-weight: 500;
}

/* Claim Button */
.claim-btn {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, #7aa2f7 0%, #7dcfff 100%);
  border: none;
  border-radius: 8px;
  color: var(--bg-dark);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(122, 162, 247, 0.2);
}

.claim-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(122, 162, 247, 0.4);
}

.claim-btn:active:not(:disabled) {
  transform: translateY(0);
}

.claim-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .marketplace-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .header-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .sort-buttons {
    width: 100%;
  }

  .sort-btn {
    flex: 1;
  }

  .refresh-btn {
    width: 100%;
  }

  .header-content h1 {
    font-size: 1.5rem;
  }

  .marketplace-card {
    padding: 1rem;
  }

  .points-badge {
    top: 0.75rem;
    right: 0.75rem;
    padding: 0.375rem 0.625rem;
  }

  .points-value {
    font-size: 1.25rem;
  }

  .priority-badge {
    top: 0.75rem;
    left: 0.75rem;
    font-size: 1rem;
  }

  .task-content {
    margin-top: 1.5rem;
  }

  .task-title {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .header-content h1 {
    font-size: 1.25rem;
  }

  .subtitle {
    font-size: 0.8rem;
  }

  .sort-btn, .refresh-btn {
    font-size: 0.8rem;
  }

  .task-description {
    -webkit-line-clamp: 2;
  }
}
</style>
