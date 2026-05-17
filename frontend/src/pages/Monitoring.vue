<template>
  <div class="monitoring-page">
    <h1>System Monitoring</h1>

    <!-- Health Status -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">System Health</h2>
        <span :class="`status-badge status-${monitoringStore.health.overall_status}`">
          {{ monitoringStore.health.overall_status.toUpperCase() }}
        </span>
      </div>

      <div class="grid grid-3">
        <div class="metric-box">
          <h3 class="metric-label">Uptime</h3>
          <div class="metric-value">{{ formatUptime(monitoringStore.health.uptime_seconds) }}</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Memory Usage</h3>
          <div class="metric-value">{{ monitoringStore.health.memory_usage_mb.toFixed(1) }} MB</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">CPU Usage</h3>
          <div class="metric-value">{{ monitoringStore.health.cpu_usage_percent.toFixed(1) }}%</div>
        </div>
      </div>

      <div class="grid grid-3">
        <div class="metric-box">
          <h3 class="metric-label">Active Workflows</h3>
          <div class="metric-value">{{ monitoringStore.health.active_workflows }}</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Queued Tasks</h3>
          <div class="metric-value">{{ monitoringStore.health.queued_tasks }}</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">API Status</h3>
          <div class="status-badge" style="margin-top: 0.5rem;">✓ Running</div>
        </div>
      </div>
    </div>

    <!-- Component Status -->
    <div class="card">
      <h2 class="card-title">Component Status</h2>
      <table class="table">
        <thead>
          <tr>
            <th>Component</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(status, component) in monitoringStore.health.components" :key="component">
            <td><strong>{{ formatComponentName(component) }}</strong></td>
            <td><span :class="`status-badge status-${status}`">{{ status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Metrics -->
    <div class="card">
      <h2 class="card-title">Key Metrics</h2>
      <div class="grid grid-2">
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
        <div class="metric-box">
          <h3 class="metric-label">Avg Parallelization</h3>
          <div class="metric-value">{{ monitoringStore.metrics.average_parallelization_gain.toFixed(1) }}%</div>
        </div>
      </div>
    </div>

    <!-- Active Alerts -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Active Alerts</h2>
        <span v-if="monitoringStore.activeAlerts.length > 0" class="status-badge status-failed">
          {{ monitoringStore.activeAlerts.length }}
        </span>
        <span v-else class="status-badge status-completed">
          None
        </span>
      </div>

      <div v-if="monitoringStore.activeAlerts.length === 0" class="empty-state">
        <p>✓ No active alerts</p>
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
          <tr v-for="alert in monitoringStore.activeAlerts" :key="alert.alert_id">
            <td>{{ alert.alert_type }}</td>
            <td><span :class="`status-badge status-${alert.severity}`">{{ alert.severity }}</span></td>
            <td>{{ alert.message }}</td>
            <td>{{ formatDate(alert.timestamp) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { useMonitoringStore } from '../stores/monitoringStore'

const monitoringStore = useMonitoringStore()

const formatUptime = (seconds) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

const formatComponentName = (name) => {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleString()
}
</script>

<style scoped>
.monitoring-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}
</style>
