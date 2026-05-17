<template>
  <div class="workflows-page">
    <div class="page-header">
      <h1>Workflows</h1>
      <button class="btn btn-success" @click="showCreateForm = !showCreateForm">
        {{ showCreateForm ? 'Cancel' : '+ New Workflow' }}
      </button>
    </div>

    <!-- Create Workflow Form -->
    <div v-if="showCreateForm" class="card">
      <h2 class="card-title">Create New Workflow</h2>
      <form @submit.prevent="submitWorkflow">
        <div class="grid">
          <div class="form-group">
            <label class="form-label">Workflow Name</label>
            <input v-model="newWorkflow.name" type="text" class="form-input" required>
          </div>
          <div class="form-group">
            <label class="form-label">Description</label>
            <input v-model="newWorkflow.description" type="text" class="form-input">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Tasks (JSON)</label>
          <textarea v-model="newWorkflow.tasksJson" class="form-textarea" placeholder="[{&quot;id&quot;:&quot;task1&quot;,&quot;name&quot;:&quot;Task 1&quot;}]"></textarea>
        </div>
        <button type="submit" class="btn btn-success">Create Workflow</button>
        <span v-if="error" class="error-message">{{ error }}</span>
      </form>
    </div>

    <!-- Workflows List -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">All Workflows</h2>
        <div class="filters">
          <select v-model="filterStatus" class="form-select">
            <option value="">All Statuses</option>
            <option value="created">Created</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      <div v-if="workflowStore.loading" class="loading"></div>
      <div v-else-if="filteredWorkflows.length === 0" class="empty-state">
        <div class="empty-state-icon">📋</div>
        <h3 class="empty-state-title">No Workflows</h3>
        <p>Create a new workflow to get started</p>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Status</th>
            <th>Tasks</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="workflow in filteredWorkflows" :key="workflow.id">
            <td><strong>{{ workflow.name }}</strong></td>
            <td>{{ workflow.description || '-' }}</td>
            <td><span :class="`status-badge status-${workflow.status}`">{{ workflow.status }}</span></td>
            <td>{{ workflow.tasks?.length || 0 }}</td>
            <td>{{ formatDate(workflow.created_at) }}</td>
            <td>
              <button class="btn btn-small" @click="analyzeWorkflow(workflow.id)">Analyze</button>
              <button class="btn btn-small btn-danger" @click="confirmDelete(workflow.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWorkflowStore } from '../stores/workflowStore'

const workflowStore = useWorkflowStore()
const showCreateForm = ref(false)
const filterStatus = ref('')
const error = ref(null)
const newWorkflow = ref({
  name: '',
  description: '',
  tasksJson: '[]'
})

const filteredWorkflows = computed(() => {
  let items = workflowStore.workflows
  if (filterStatus.value) {
    items = items.filter(w => w.status === filterStatus.value)
  }
  return items
})

onMounted(() => {
  workflowStore.fetchWorkflows()
})

const submitWorkflow = async () => {
  try {
    error.value = null
    const tasks = JSON.parse(newWorkflow.value.tasksJson)
    await workflowStore.createWorkflow({
      name: newWorkflow.value.name,
      description: newWorkflow.value.description,
      tasks: tasks,
      dependencies: []
    })
    showCreateForm.value = false
    newWorkflow.value = { name: '', description: '', tasksJson: '[]' }
  } catch (e) {
    error.value = e.message
  }
}

const analyzeWorkflow = async (workflowId) => {
  try {
    const result = await workflowStore.analyzeWorkflow(workflowId)
    alert(`Analysis ${result.analysis_id} created`)
  } catch (e) {
    alert(`Error: ${e.message}`)
  }
}

const confirmDelete = (workflowId) => {
  if (confirm('Are you sure you want to delete this workflow?')) {
    workflowStore.deleteWorkflow(workflowId)
  }
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString() + ' ' + new Date(date).toLocaleTimeString()
}
</script>

<style scoped>
.workflows-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.filters {
  display: flex;
  gap: 1rem;
}

.form-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}
</style>
