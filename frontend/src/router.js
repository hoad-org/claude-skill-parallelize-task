import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './pages/Dashboard.vue'
import Workflows from './pages/Workflows.vue'
import Analysis from './pages/Analysis.vue'
import Decisions from './pages/Decisions.vue'
import Execution from './pages/Execution.vue'
import Monitoring from './pages/Monitoring.vue'
import Performance from './pages/Performance.vue'

const routes = [
  { path: '/', component: Dashboard, name: 'Dashboard' },
  { path: '/workflows', component: Workflows, name: 'Workflows' },
  { path: '/analysis', component: Analysis, name: 'Analysis' },
  { path: '/decisions', component: Decisions, name: 'Decisions' },
  { path: '/execution', component: Execution, name: 'Execution' },
  { path: '/monitoring', component: Monitoring, name: 'Monitoring' },
  { path: '/performance', component: Performance, name: 'Performance' },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
