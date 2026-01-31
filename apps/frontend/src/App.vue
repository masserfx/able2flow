<script setup lang="ts">
import { computed, ref, provide, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import ProjectSelector from './components/ProjectSelector.vue'
import UserButton from './components/UserButton.vue'

const { t } = useI18n()
const route = useRoute()

const STORAGE_KEY = 'able2flow_current_project'

const currentProjectId = ref<number | null>(null)

function loadProjectFromStorage() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    const parsed = parseInt(stored, 10)
    currentProjectId.value = isNaN(parsed) ? null : parsed
  }
}

function onProjectChange(projectId: number | null) {
  currentProjectId.value = projectId
  if (projectId === null) {
    localStorage.removeItem(STORAGE_KEY)
  } else {
    localStorage.setItem(STORAGE_KEY, String(projectId))
  }
}

provide('currentProjectId', currentProjectId)

onMounted(loadProjectFromStorage)

const navItems = computed(() => [
  { path: '/dashboard', name: t('nav.dashboard'), icon: '◉' },
  { path: '/board', name: t('nav.board'), icon: '▦' },
  { path: '/monitors', name: t('nav.monitors'), icon: '◎' },
  { path: '/incidents', name: t('nav.incidents'), icon: '⚡' },
  { path: '/audit', name: t('nav.auditLog'), icon: '☰' },
  { path: '/settings/integrations', name: t('integrations.title'), icon: '⚙' },
])

const currentPath = computed(() => route.path)
const isLandingPage = computed(() => route.path === '/')
</script>

<template>
  <!-- Landing page without sidebar -->
  <div v-if="isLandingPage" class="landing-layout">
    <router-view />
  </div>

  <!-- App layout with sidebar -->
  <div v-else class="app-layout">
    <nav class="sidebar">
      <router-link to="/" class="logo">
        <span class="logo-icon">◈</span>
        <span class="logo-text">Able2Flow</span>
      </router-link>
      <ProjectSelector
        v-model="currentProjectId"
        @change="onProjectChange"
      />
      <ul class="nav-list">
        <li v-for="item in navItems" :key="item.path">
          <router-link
            :to="item.path"
            class="nav-link"
            :class="{ active: currentPath === item.path }"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-text">{{ item.name }}</span>
          </router-link>
        </li>
      </ul>
      <div class="sidebar-footer">
        <UserButton />
        <LanguageSwitcher />
        <span class="version">v0.3.0</span>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.landing-layout {
  min-height: 100vh;
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  min-width: 220px;
  background-color: var(--bg-darker);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 1rem;
  margin-bottom: 1.5rem;
  text-decoration: none;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

.logo-icon {
  font-size: 1.5rem;
  color: var(--accent-blue);
}

.logo-text {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.nav-link:hover {
  background-color: var(--bg-highlight);
  color: var(--text-primary);
}

.nav-link.active {
  background-color: rgba(122, 162, 247, 0.1);
  color: var(--accent-blue);
  border-left-color: var(--accent-blue);
}

.nav-icon {
  font-size: 1rem;
  width: 1.25rem;
  text-align: center;
  flex-shrink: 0;
}

.nav-text {
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0 1rem;
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.version {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.main-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  background-color: var(--bg-dark);
  min-width: 0;
}

/* Responsive styles */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    min-width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
    padding: 0.5rem;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    overflow-x: auto;
    gap: 0.5rem;
  }

  .logo {
    margin-bottom: 0;
    padding: 0.5rem;
  }

  .logo-text {
    display: none;
  }

  .nav-list {
    display: flex;
    gap: 0.25rem;
    flex: 1;
    overflow-x: auto;
  }

  .nav-link {
    padding: 0.5rem 0.75rem;
    border-left: none;
    border-bottom: 2px solid transparent;
    border-radius: 6px;
  }

  .nav-link.active {
    border-left-color: transparent;
    border-bottom-color: var(--accent-blue);
  }

  .nav-text {
    display: none;
  }

  .nav-icon {
    font-size: 1.25rem;
    width: auto;
  }

  .sidebar-footer {
    flex-direction: row;
    padding: 0;
    margin-top: 0;
    border-top: none;
    gap: 0.5rem;
    align-items: center;
  }

  .version {
    display: none;
  }

  .main-content {
    padding: 1rem;
  }
}

/* Project selector on mobile */
@media (max-width: 768px) {
  .sidebar :deep(.project-selector) {
    order: -1;
    margin-bottom: 0;
    padding: 0;
  }

  .sidebar :deep(.project-selector .selector-label),
  .sidebar :deep(.project-selector .new-form),
  .sidebar :deep(.project-selector .delete-confirm) {
    display: none;
  }

  .sidebar :deep(.project-selector .selector-header) {
    margin-bottom: 0;
  }

  .sidebar :deep(.project-selector .selector-wrapper) {
    padding: 0.375rem 0.5rem;
  }
}
</style>
