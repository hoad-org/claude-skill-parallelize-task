<template>
  <div class="decisions-page">
    <h1>Execution Strategies</h1>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Generated Decisions</h2>
      </div>

      <div v-if="workflowStore.decisions.length === 0" class="empty-state">
        <div class="empty-state-icon">🎯</div>
        <h3 class="empty-state-title">No Decisions</h3>
        <p>Generate a decision from an analysis to see execution strategies</p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Decision ID</th>
            <th>Total Tasks</th>
            <th>Serial Duration</th>
            <th>Parallel Duration</th>
            <th>Efficiency Gain</th>
            <th>Critical Path</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="decision in workflowStore.decisions" :key="decision.id">
            <td><code>{{ decision.id.substring(0, 8) }}...</code></td>
            <td>{{ decision.total_tasks }}</td>
            <td>{{ decision.serial_duration.toFixed(1) }}s</td>
            <td>{{ decision.parallel_duration.toFixed(1) }}s</td>
            <td class="metric-value">{{ decision.efficiency_gain.toFixed(1) }}%</td>
            <td>{{ decision.critical_path.length }} tasks</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Optimization Notes -->
    <div class="card" v-if="workflowStore.decisions.length > 0">
      <h2 class="card-title">Optimization Notes</h2>
      <ul>
        <li v-for="(note, idx) in workflowStore.decisions[0].optimization_notes" :key="idx">
          {{ note }}
        </li>
      </ul>
    </div>

    <!-- Safety Issues -->
    <div class="card" v-if="workflowStore.decisions.length > 0">
      <h2 class="card-title">Safety Issues</h2>
      <div v-if="workflowStore.decisions[0].safety_issues.length === 0" class="empty-state">
        <p>✓ No safety issues detected</p>
      </div>
      <ul v-else>
        <li v-for="(issue, idx) in workflowStore.decisions[0].safety_issues" :key="idx">
          {{ issue }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { useWorkflowStore } from '../stores/workflowStore'

const workflowStore = useWorkflowStore()
</script>

<style scoped>
.decisions-page {
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

.metric-value {
  color: #27ae60;
  font-weight: bold;
}
</style>
