<template>
  <div class="execution-page">
    <h1>Workflow Execution</h1>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Active Executions</h2>
      </div>

      <div v-if="workflowStore.executions.length === 0" class="empty-state">
        <div class="empty-state-icon">▶️</div>
        <h3 class="empty-state-title">No Executions</h3>
        <p>Execute a workflow to see execution details</p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Execution ID</th>
            <th>Workflow ID</th>
            <th>Status</th>
            <th>Tasks Completed</th>
            <th>Tasks Failed</th>
            <th>Duration</th>
            <th>Efficiency</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="execution in workflowStore.executions" :key="execution.execution_id">
            <td><code>{{ execution.execution_id.substring(0, 8) }}...</code></td>
            <td><code>{{ execution.workflow_id.substring(0, 8) }}...</code></td>
            <td><span :class="`status-badge status-${execution.status}`">{{ execution.status }}</span></td>
            <td>{{ execution.tasks_completed }}</td>
            <td>{{ execution.tasks_failed }}</td>
            <td>{{ execution.duration_seconds.toFixed(1) }}s</td>
            <td class="metric-value">{{ execution.efficiency_achieved.toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Execution Details -->
    <div class="card" v-if="workflowStore.executions.length > 0">
      <h2 class="card-title">Latest Execution Details</h2>
      <div class="grid grid-2">
        <div>
          <p><strong>Start Time:</strong> {{ formatDate(workflowStore.executions[0].start_time) }}</p>
          <p><strong>End Time:</strong> {{ formatDate(workflowStore.executions[0].end_time) || 'In Progress' }}</p>
          <p><strong>Phases Executed:</strong> {{ workflowStore.executions[0].phases_executed }} / {{ workflowStore.executions[0].total_phases }}</p>
        </div>
        <div>
          <p><strong>Recovery Events:</strong> {{ workflowStore.executions[0].recovery_events }}</p>
          <p><strong>Escalation Events:</strong> {{ workflowStore.executions[0].escalation_events }}</p>
          <p><strong>Tasks Skipped:</strong> {{ workflowStore.executions[0].tasks_skipped }}</p>
        </div>
      </div>
    </div>

    <!-- Error Information -->
    <div class="card alert alert-danger" v-if="workflowStore.executions.length > 0 && workflowStore.executions[0].error_message">
      <h3>Execution Error</h3>
      <p>{{ workflowStore.executions[0].error_message }}</p>
    </div>

    <!-- Execution Metrics -->
    <div class="card" v-if="workflowStore.executions.length > 0">
      <h2 class="card-title">Execution Metrics</h2>
      <div class="grid grid-3">
        <div class="metric-box">
          <h3 class="metric-label">Success Rate</h3>
          <div class="metric-value">{{ getSuccessRate().toFixed(1) }}%</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Avg Task Time</h3>
          <div class="metric-value">{{ getAvgTaskTime().toFixed(2) }}s</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Phases Completed</h3>
          <div class="metric-value">{{ workflowStore.executions[0].phases_executed }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useWorkflowStore } from '../stores/workflowStore'

const workflowStore = useWorkflowStore()

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString() + ' ' + new Date(date).toLocaleTimeString()
}

const getSuccessRate = () => {
  if (workflowStore.executions.length === 0) return 0
  const exec = workflowStore.executions[0]
  const total = exec.tasks_completed + exec.tasks_failed
  return total > 0 ? (exec.tasks_completed / total * 100) : 0
}

const getAvgTaskTime = () => {
  if (workflowStore.executions.length === 0) return 0
  const exec = workflowStore.executions[0]
  const totalTasks = exec.tasks_completed + exec.tasks_failed + exec.tasks_skipped
  return totalTasks > 0 ? (exec.duration_seconds / totalTasks) : 0
}
</script>

<style scoped>
.execution-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

code {
  background: #f5f5f5;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: monospace;
}

.metric-value {
  color: #27ae60;
  font-weight: bold;
}

h3 {
  margin-bottom: 0.5rem;
}

p {
  margin: 0.25rem 0;
}
</style>
