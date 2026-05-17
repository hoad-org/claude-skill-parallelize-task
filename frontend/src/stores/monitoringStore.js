import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../services/api'

export const useMonitoringStore = defineStore('monitoring', () => {
  const metrics = ref({
    workflows_total: 0,
    workflows_active: 0,
    tasks_completed_total: 0,
    tasks_failed_total: 0,
    average_parallelization_gain: 0,
    cache_hit_rate: 0,
    cache_misses_total: 0
  })

  const health = ref({
    status: 'healthy',
    uptime_seconds: 0,
    components: {},
    active_workflows: 0,
    queued_tasks: 0,
    memory_usage_mb: 0,
    cpu_usage_percent: 0
  })

  const alerts = ref([])
  const loading = ref(false)
  const error = ref(null)

  const taskSuccessRate = computed(() => {
    const total = metrics.value.tasks_completed_total + metrics.value.tasks_failed_total
    return total > 0 ? (metrics.value.tasks_completed_total / total * 100).toFixed(2) : 0
  })

  const activeAlerts = computed(() =>
    alerts.value.filter(a => !a.resolved)
  )

  async function fetchMetrics() {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.getMetrics()
      metrics.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchHealth() {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.getDetailedHealth()
      health.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchAlerts() {
    loading.value = true
    error.value = null
    try {
      const response = await apiService.getAlerts({ resolved: false })
      alerts.value = response.data.alerts || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function startPeriodicFetch(interval = 5000) {
    await fetchMetrics()
    await fetchHealth()
    await fetchAlerts()

    setInterval(() => {
      fetchMetrics()
      fetchHealth()
      fetchAlerts()
    }, interval)
  }

  return {
    metrics,
    health,
    alerts,
    loading,
    error,
    taskSuccessRate,
    activeAlerts,
    fetchMetrics,
    fetchHealth,
    fetchAlerts,
    startPeriodicFetch
  }
})
