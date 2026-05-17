<template>
  <div class="analysis-page">
    <h1>Complexity Analysis</h1>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Analysis Results</h2>
      </div>

      <div v-if="workflowStore.analyses.length === 0" class="empty-state">
        <div class="empty-state-icon">📊</div>
        <h3 class="empty-state-title">No Analyses</h3>
        <p>Go to <router-link to="/workflows">Workflows</router-link> to analyze a workflow</p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Analysis ID</th>
            <th>Workflow ID</th>
            <th>Total Tasks</th>
            <th>Parallelizable</th>
            <th>Critical Path</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="analysis in workflowStore.analyses" :key="analysis.analysis_id">
            <td><code>{{ analysis.analysis_id.substring(0, 8) }}...</code></td>
            <td><code>{{ analysis.workflow_id.substring(0, 8) }}...</code></td>
            <td>{{ analysis.total_tasks }}</td>
            <td>{{ analysis.parallelizable_tasks.length }}</td>
            <td>{{ analysis.critical_path_duration.toFixed(1) }}s</td>
            <td>{{ formatDate(analysis.analysis_timestamp) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Complexity Scores -->
    <div class="card" v-if="workflowStore.analyses.length > 0">
      <h2 class="card-title">Complexity Scores</h2>
      <div class="grid grid-2">
        <div v-for="(score, taskId) in workflowStore.analyses[0].complexity_scores" :key="taskId">
          <p><strong>{{ taskId }}:</strong> {{ score.toFixed(1) }}/100</p>
        </div>
      </div>
    </div>

    <!-- Resource Conflicts -->
    <div class="card" v-if="workflowStore.analyses.length > 0">
      <h2 class="card-title">Resource Conflicts</h2>
      <div v-if="workflowStore.analyses[0].resource_conflicts.length === 0" class="empty-state">
        <p>✓ No resource conflicts detected</p>
      </div>
      <ul v-else>
        <li v-for="(conflict, idx) in workflowStore.analyses[0].resource_conflicts" :key="idx">
          {{ conflict }}
        </li>
      </ul>
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
</script>

<style scoped>
.analysis-page {
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
  font-size: 0.9rem;
}

ul {
  list-style: none;
  padding: 0;
}

li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

li:last-child {
  border-bottom: none;
}
</style>
