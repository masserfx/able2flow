import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: () => import('../views/LandingView.vue'),
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/board',
    name: 'board',
    component: () => import('../views/BoardView.vue'),
  },
  {
    path: '/monitors',
    name: 'monitors',
    component: () => import('../views/MonitorsView.vue'),
  },
  {
    path: '/incidents',
    name: 'incidents',
    component: () => import('../views/IncidentsView.vue'),
  },
  {
    path: '/audit',
    name: 'audit',
    component: () => import('../views/AuditView.vue'),
  },
  {
    path: '/marketplace',
    name: 'marketplace',
    component: () => import('../views/TaskMarketplaceView.vue'),
  },
  {
    path: '/leaderboard',
    name: 'leaderboard',
    component: () => import('../views/LeaderboardView.vue'),
  },
  {
    path: '/guide',
    name: 'guide',
    component: () => import('../views/GuideView.vue'),
  },
  {
    path: '/settings/integrations',
    name: 'integrations',
    component: () => import('../views/IntegrationsView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
