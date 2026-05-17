<template>
  <div class="performance-page">
    <h1>Performance Analytics</h1>

    <!-- Performance Statistics -->
    <div class="card">
      <h2 class="card-title">Performance Statistics</h2>
      <div class="grid grid-3">
        <div class="metric-box">
          <h3 class="metric-label">Total Workflows</h3>
          <div class="metric-value">{{ performanceStats.total_workflows }}</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Total Tasks</h3>
          <div class="metric-value">{{ performanceStats.total_tasks }}</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Avg Task Duration</h3>
          <div class="metric-value">{{ performanceStats.average_task_duration.toFixed(1) }}s</div>
        </div>
      </div>

      <div class="grid grid-3">
        <div class="metric-box">
          <h3 class="metric-label">Avg Workflow Duration</h3>
          <div class="metric-value">{{ performanceStats.average_workflow_duration.toFixed(1) }}s</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Parallelization Success</h3>
          <div class="metric-value">{{ (performanceStats.parallelization_success_rate * 100).toFixed(1) }}%</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Resource Efficiency</h3>
          <div class="metric-value">{{ performanceStats.optimization_improvements.resource_efficiency.toFixed(1) }}%</div>
        </div>
      </div>
    </div>

    <!-- Resource Utilization -->
    <div class="card">
      <h2 class="card-title">Resource Utilization</h2>
      <div class="grid grid-3">
        <div v-for="(usage, resource) in performanceStats.resource_utilization" :key="resource">
          <div class="metric-box">
            <h3 class="metric-label">{{ formatResourceName(resource) }}</h3>
            <div class="metric-value">{{ usage.toFixed(1) }}%</div>
            <div class="progress-bar">
              <div class="progress" :style="{ width: usage + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Optimization Improvements -->
    <div class="card">
      <h2 class="card-title">Optimization Improvements</h2>
      <table class="table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Improvement</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(value, metric) in performanceStats.optimization_improvements" :key="metric">
            <td><strong>{{ formatMetricName(metric) }}</strong></td>
            <td class="metric-value">{{ value.toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Cache Statistics -->
    <div class="card">
      <h2 class="card-title">Cache Performance</h2>
      <div class="grid grid-2">
        <div class="metric-box">
          <h3 class="metric-label">Cache Hits</h3>
          <div class="metric-value">{{ cacheStats.cache_hits }}</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Cache Misses</h3>
          <div class="metric-value">{{ cacheStats.cache_misses }}</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Hit Rate</h3>
          <div class="metric-value">{{ (cacheStats.hit_rate * 100).toFixed(1) }}%</div>
        </div>
        <div class="metric-box">
          <h3 class="metric-label">Cache Size</h3>
          <div class="metric-value">{{ cacheStats.cache_size_mb.toFixed(1) }} MB</div>
        </div>
      </div>
    </div>

    <!-- Most Accessed Workflows -->
    <div class="card">
      <h2 class="card-title">Most Accessed Workflows</h2>
      <div v-if="cacheStats.most_accessed_workflows.length === 0" class="empty-state">
        <p>No cached workflows yet</p>
      </div>
      <ol v-else>
        <li v-for="(workflowId, idx) in cacheStats.most_accessed_workflows" :key="workflowId">
          <code>{{ workflowId.substring(0, 8) }}...</code> ({{ cacheStats.cache_hits - idx }} accesses)
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiService } from '../services/api'

const performanceStats = ref({
  total_workflows: 0,
  total_tasks: 0,
  average_task_duration: 0,
  average_workflow_duration: 0,
  parallelization_success_rate: 0,
  resource_utilization: {},
  optimization_improvements: {}
})

const cacheStats = ref({
  total_caches: 0,
  cache_hits: 0,
  cache_misses: 0,
  hit_rate: 0,
  most_accessed_workflows: [],
  cache_size_mb: 0
})

onMounted(async () => {
  try {
    const perfResponse = await apiService.getPerformanceStats()
    performanceStats.value = perfResponse.data

    const cacheResponse = await apiService.getCacheStats()
    cacheStats.value = cacheResponse.data
  } catch (error) {
    console.error('Error loading performance data:', error)
  }
})

const formatResourceName = (name) => {
  return name.charAt(0).toUpperCase() + name.slice(1)
}

const formatMetricName = (name) => {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}
</script>

<style scoped>
.performance-page {
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

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transition: width 0.3s ease;
}

ol {
  list-style: none;
  padding: 0;
  counter-reset: item;
}

li {
  display: block;
  counter-increment: item;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f0f0f0;
}

li:before {
  content: counter(item) '. ';
  font-weight: bold;
  color: #3498db;
  margin-right: 0.5rem;
}

li:last-child {
  border-bottom: none;
}

.metric-value {
  color: #27ae60;
  font-weight: bold;
}
</style>
