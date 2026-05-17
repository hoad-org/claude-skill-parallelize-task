import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../services/api'

export const useWorkflowStore = defineStore('workflow', () => {
  const workflows = ref([])
  const analyses = ref([])
  const decisions = ref([])
  const executions = ref([])
  const loading = ref(false)
  const error = ref(null)

  const activeWorkflows = computed(() =>
    workflows.value.filter(w => w.status === 'running')
  )

  const completedWorkflows = computed(() =>
    workflows.value.filter(w => w.status === 'completed')
  )

  const failedWorkflows = computed(() =>
    workflows.value.filter(w => w.status === 'failed')
  )

  async function fetchWorkflows(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.listWorkflows(params)
      workflows.value = response.data.workflows || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createWorkflow(data) {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.createWorkflow(data)
      await fetchWorkflows()
      return response.data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function getWorkflow(id) {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.getWorkflow(id)
      const index = workflows.value.findIndex(w => w.id === id)
      if (index !== -1) {
        workflows.value[index] = response.data
      } else {
        workflows.value.push(response.data)
      }
      return response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function deleteWorkflow(id) {
    loading.value = true
    error.value = null
    try {
      await apiService.deleteWorkflow(id)
      workflows.value = workflows.value.filter(w => w.id !== id)
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function analyzeWorkflow(workflowId) {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.analyzeWorkflow({
        workflow_id: workflowId,
        include_complexity: true,
        include_feasibility: true
      })
      analyses.value.push(response.data)
      return response.data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function generateDecision(analysisId) {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.generateDecision({
        analysis_id: analysisId,
        prefer_parallel: true
      })
      decisions.value.push(response.data)
      return response.data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function executeWorkflow(workflowId, planId = null) {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.executeWorkflow({
        workflow_id: workflowId,
        plan_id: planId,
        dry_run: false
      })
      executions.value.push(response.data)
      return response.data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    workflows,
    analyses,
    decisions,
    executions,
    loading,
    error,
    activeWorkflows,
    completedWorkflows,
    failedWorkflows,
    fetchWorkflows,
    createWorkflow,
    getWorkflow,
    deleteWorkflow,
    analyzeWorkflow,
    generateDecision,
    executeWorkflow
  }
})
