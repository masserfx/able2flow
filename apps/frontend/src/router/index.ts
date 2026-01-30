import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
