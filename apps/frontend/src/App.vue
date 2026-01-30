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
  { path: '/', name: t('nav.dashboard'), icon: '◉' },
  { path: '/board', name: t('nav.board'), icon: '▦' },
  { path: '/monitors', name: t('nav.monitors'), icon: '◎' },
  { path: '/incidents', name: t('nav.incidents'), icon: '⚡' },
  { path: '/audit', name: t('nav.auditLog'), icon: '☰' },
  { path: '/settings/integrations', name: t('integrations.title'), icon: '⚙' },
])

const currentPath = computed(() => route.path)
</script>

<template>
  <div class="app-layout">
    <nav class="sidebar">
      <div class="logo">
        <span class="logo-icon">◈</span>
        <span class="logo-text">Able2Flow</span>
      </div>
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
        <span class="version">v0.2.0</span>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background-color: var(--bg-darker);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 1.5rem;
  margin-bottom: 2rem;
}

.logo-icon {
  font-size: 1.5rem;
  color: var(--accent-blue);
}

.logo-text {
  font-size: 1.25rem;
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
  padding: 0.75rem 1.5rem;
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
  width: 1.5rem;
  text-align: center;
}

.nav-text {
  font-size: 0.875rem;
  font-weight: 500;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0 1.5rem;
  margin-top: auto;
}

.version {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.main-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  background-color: var(--bg-dark);
}
</style>
