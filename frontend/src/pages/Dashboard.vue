<template>
  <div class="dashboard-page">
    <h1>Dashboard</h1>

    <!-- Key Metrics -->
    <div class="grid grid-3">
      <div class="metric-box">
        <h3 class="metric-label">Total Workflows</h3>
        <div class="metric-value">{{ monitoringStore.metrics.workflows_total }}</div>
      </div>
      <div class="metric-box">
        <h3 class="metric-label">Active Workflows</h3>
        <div class="metric-value">{{ monitoringStore.metrics.workflows_active }}</div>
      </div>
      <div class="metric-box">
        <h3 class="metric-label">Success Rate</h3>
        <div class="metric-value">{{ monitoringStore.taskSuccessRate }}%</div>
      </div>
    </div>

    <div class="grid grid-3">
      <div class="metric-box">
        <h3 class="metric-label">Tasks Completed</h3>
        <div class="metric-value">{{ monitoringStore.metrics.tasks_completed_total }}</div>
      </div>
      <div class="metric-box">
        <h3 class="metric-label">Tasks Failed</h3>
        <div class="metric-value">{{ monitoringStore.metrics.tasks_failed_total }}</div>
      </div>
      <div class="metric-box">
        <h3 class="metric-label">Cache Hit Rate</h3>
        <div class="metric-value">{{ (monitoringStore.metrics.cache_hit_rate * 100).toFixed(1) }}%</div>
      </div>
    </div>

    <!-- Active Alerts -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Active Alerts</h2>
        <span v-if="monitoringStore.activeAlerts.length > 0" class="status-badge status-failed">
          {{ monitoringStore.activeAlerts.length }} Alert{{ monitoringStore.activeAlerts.length > 1 ? 's' : '' }}
        </span>
      </div>
      <div v-if="monitoringStore.activeAlerts.length === 0" class="empty-state">
        <div class="empty-state-icon">✓</div>
        <h3 class="empty-state-title">No Active Alerts</h3>
        <p>System is operating normally</p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Severity</th>
            <th>Message</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in monitoringStore.activeAlerts.slice(0, 5)" :key="alert.alert_id">
            <td>{{ alert.alert_type }}</td>
            <td><span :class="`status-badge status-${alert.severity}`">{{ alert.severity }}</span></td>
            <td>{{ alert.message }}</td>
            <td>{{ formatDate(alert.timestamp) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Recent Workflows -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Recent Workflows</h2>
        <router-link to="/workflows" class="btn btn-small">View All</router-link>
      </div>
      <div v-if="workflowStore.workflows.length === 0" class="empty-state">
        <div class="empty-state-icon">📋</div>
        <h3 class="empty-state-title">No Workflows</h3>
        <p><router-link to="/workflows">Create your first workflow</router-link></p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Tasks</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="workflow in workflowStore.workflows.slice(0, 5)" :key="workflow.id">
            <td>
              <router-link :to="`/workflows`">{{ workflow.name }}</router-link>
            </td>
            <td><span :class="`status-badge status-${workflow.status}`">{{ workflow.status }}</span></td>
            <td>{{ workflow.tasks?.length || 0 }}</td>
            <td>{{ formatDate(workflow.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- System Health -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">System Health</h2>
        <span :class="`status-badge status-${monitoringStore.health.overall_status}`">
          {{ monitoringStore.health.overall_status }}
        </span>
      </div>
      <div class="grid grid-2">
        <div>
          <p><strong>Uptime:</strong> {{ formatUptime(monitoringStore.health.uptime_seconds) }}</p>
          <p><strong>Active Workflows:</strong> {{ monitoringStore.health.active_workflows }}</p>
          <p><strong>Queued Tasks:</strong> {{ monitoringStore.health.queued_tasks }}</p>
        </div>
        <div>
          <p><strong>Memory:</strong> {{ monitoringStore.health.memory_usage_mb.toFixed(1) }} MB</p>
          <p><strong>CPU:</strong> {{ monitoringStore.health.cpu_usage_percent.toFixed(1) }}%</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useWorkflowStore } from '../stores/workflowStore'
import { useMonitoringStore } from '../stores/monitoringStore'

const workflowStore = useWorkflowStore()
const monitoringStore = useMonitoringStore()

onMounted(() => {
  workflowStore.fetchWorkflows()
  monitoringStore.fetchMetrics()
  monitoringStore.fetchHealth()
  monitoringStore.fetchAlerts()
})

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString() + ' ' + new Date(date).toLocaleTimeString()
}

const formatUptime = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
}
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.dark-mode h1 {
  color: #e0e0e0;
}
</style>
