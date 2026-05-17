import axios from 'axios'

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
})

export const apiService = {
  // Health endpoints
  async getHealth() {
    return api.get('/health')
  },

  async getDetailedHealth() {
    return api.get('/health/detailed')
  },

  // Workflow endpoints
  async createWorkflow(data) {
    return api.post('/workflows', data)
  },

  async listWorkflows(params = {}) {
    return api.get('/workflows', { params })
  },

  async getWorkflow(id) {
    return api.get(`/workflows/${id}`)
  },

  async deleteWorkflow(id) {
    return api.delete(`/workflows/${id}`)
  },

  // Analysis endpoints
  async analyzeWorkflow(data) {
    return api.post('/analyze', data)
  },

  async getAnalysis(id) {
    return api.get(`/analyze/${id}`)
  },

  // Decision endpoints
  async generateDecision(data) {
    return api.post('/decide', data)
  },

  async getDecision(id) {
    return api.get(`/decide/${id}`)
  },

  // Execution endpoints
  async executeWorkflow(data) {
    return api.post('/execute', data)
  },

  async getExecutionStatus(id) {
    return api.get(`/execute/${id}`)
  },

  async getExecutionMetrics(id) {
    return api.get(`/execute/${id}/metrics`)
  },

  // Monitoring endpoints
  async getMetrics() {
    return api.get('/metrics')
  },

  async getAlerts(params = {}) {
    return api.get('/alerts', { params })
  },

  // Performance endpoints
  async getPerformanceStats() {
    return api.get('/performance/stats')
  },

  async getCacheStats() {
    return api.get('/performance/cache')
  },
}

export default api
