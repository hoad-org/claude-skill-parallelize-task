# Phase 6: Web Dashboard Guide

Complete guide for the Vue.js 3 Web Dashboard component of Parallelize-Task.

## Table of Contents
1. [Dashboard Architecture](#dashboard-architecture)
2. [REST API Endpoints](#rest-api-endpoints)
3. [WebSocket Real-Time Updates](#websocket-real-time-updates)
4. [Vue.js Components](#vuejs-components)
5. [State Management](#state-management)
6. [Authentication & CORS](#authentication--cors)
7. [Frontend Development](#frontend-development)

---

## Dashboard Architecture

### Frontend Stack

```
┌─────────────────────────────────────────┐
│    Browser                              │
├─────────────────────────────────────────┤
│ ┌───────────────────────────────────┐   │
│ │  Vue.js 3 Application             │   │
│ ├───────────────────────────────────┤   │
│ │ Pages (7):                        │   │
│ │ ├── Dashboard                     │   │
│ │ ├── Workflows                     │   │
│ │ ├── Analysis                      │   │
│ │ ├── Decisions                     │   │
│ │ ├── Execution                     │   │
│ │ ├── Monitoring                    │   │
│ │ └── Performance                   │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ Components (Reusable):            │   │
│ │ ├── Cards                         │   │
│ │ ├── Tables                        │   │
│ │ ├── Forms                         │   │
│ │ ├── Charts                        │   │
│ │ └── Alerts                        │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ State (Pinia):                    │   │
│ │ ├── Workflow Store                │   │
│ │ └── Monitoring Store              │   │
│ └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
         │ (REST + WebSocket)
┌────────▼────────────────────────────────┐
│    FastAPI Backend (Port 8000)          │
│    ├── 24 Functional Endpoints          │
│    ├── 3 WebSocket Channels             │
│    └── Pydantic Validation              │
└─────────────────────────────────────────┘
```

### Project Structure

```
frontend/
├── src/
│   ├── pages/                      # 7 main pages
│   │   ├── Dashboard.vue           # Home/overview
│   │   ├── Workflows.vue           # Workflow management
│   │   ├── Analysis.vue            # Analysis results
│   │   ├── Decisions.vue           # Execution strategies
│   │   ├── Execution.vue           # Active executions
│   │   ├── Monitoring.vue          # System health
│   │   └── Performance.vue         # Performance stats
│   │
│   ├── components/                 # Reusable components
│   │   ├── Navbar.vue              # Navigation bar
│   │   ├── Card.vue                # Card component
│   │   ├── Table.vue               # Table component
│   │   ├── Form.vue                # Form component
│   │   ├── Alert.vue               # Alert component
│   │   ├── Badge.vue               # Status badge
│   │   ├── Loading.vue             # Loading spinner
│   │   ├── Modal.vue               # Modal dialog
│   │   ├── Chart.vue               # Chart wrapper
│   │   └── Metric.vue              # Metric display
│   │
│   ├── services/
│   │   ├── api.js                  # API client
│   │   └── websocket.js            # WebSocket handler
│   │
│   ├── stores/
│   │   ├── workflowStore.js        # Workflow state
│   │   └── monitoringStore.js      # Monitoring state
│   │
│   ├── assets/
│   │   ├── css/
│   │   │   ├── main.css            # Global styles
│   │   │   ├── variables.css       # CSS variables
│   │   │   └── responsive.css      # Media queries
│   │   └── images/
│   │       └── logos/
│   │
│   ├── App.vue                     # Root component
│   ├── main.js                     # Entry point
│   └── router.js                   # Route configuration
│
├── index.html                      # HTML template
├── package.json                    # Dependencies
├── vite.config.js                  # Build configuration
└── README.md                       # Frontend docs
```

---

## REST API Endpoints

### Health & Status Endpoints

**GET /health**
```bash
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2024-05-17T14:30:00Z",
  "uptime_seconds": 3600,
  "version": "1.1.0"
}
```

**GET /health/detailed**
```bash
curl http://localhost:8000/health/detailed

# Response
{
  "status": "healthy",
  "timestamp": "2024-05-17T14:30:00Z",
  "uptime_seconds": 3600,
  "version": "1.1.0",
  "components": {
    "api": "healthy",
    "monitoring": "healthy",
    "performance": "healthy"
  },
  "memory_usage_mb": 256,
  "cpu_usage_percent": 15,
  "active_workflows": 5
}
```

### Workflow Management Endpoints

**POST /workflows** - Create workflow
```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-pipeline",
    "description": "ETL pipeline",
    "tasks": [
      {"id": "extract", "name": "Extract Data"},
      {"id": "transform", "name": "Transform Data"},
      {"id": "load", "name": "Load Data"}
    ],
    "dependencies": [
      {"source_task_id": "extract", "target_task_id": "transform"},
      {"source_task_id": "transform", "target_task_id": "load"}
    ]
  }'

# Response
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created"
}
```

**GET /workflows** - List workflows
```bash
curl "http://localhost:8000/workflows?status=active&limit=50&offset=0"

# Response
{
  "total": 125,
  "offset": 0,
  "limit": 50,
  "workflows": [
    {
      "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "data-pipeline",
      "status": "running",
      "task_count": 3,
      "created_at": "2024-05-17T14:30:00Z"
    }
  ]
}
```

**GET /workflows/{workflow_id}** - Get workflow details
```bash
curl http://localhost:8000/workflows/550e8400-e29b-41d4-a716-446655440000

# Response (full workflow with all details)
```

**DELETE /workflows/{workflow_id}** - Delete workflow
```bash
curl -X DELETE http://localhost:8000/workflows/550e8400-e29b-41d4-a716-446655440000

# Response
{
  "status": "deleted"
}
```

### Analysis Endpoints

**POST /analyze** - Run analysis
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "include_complexity": true,
    "include_feasibility": true
  }'

# Response
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "completed"
}
```

**GET /analyze/{analysis_id}** - Get analysis results
```bash
curl http://localhost:8000/analyze/550e8400-e29b-41d4-a716-446655440001

# Response
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440001",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "complexity_score": 42,
  "parallelization_factor": 2.5,
  "critical_path_length": 3,
  "resource_conflicts": [],
  "recommendations": ["Increase parallelization", "Optimize task order"]
}
```

### Decision Generation Endpoints

**POST /decide** - Generate execution strategy
```bash
curl -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "550e8400-e29b-41d4-a716-446655440001",
    "prefer_parallel": true,
    "resource_constraints": {}
  }'

# Response
{
  "decision_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "completed"
}
```

**GET /decide/{decision_id}** - Get decision results
```bash
curl http://localhost:8000/decide/550e8400-e29b-41d4-a716-446655440002

# Response
{
  "decision_id": "550e8400-e29b-41d4-a716-446655440002",
  "analysis_id": "550e8400-e29b-41d4-a716-446655440001",
  "execution_plan": {
    "parallel_groups": [[...], [...], [...]],
    "estimated_duration_serial": 150,
    "estimated_duration_parallel": 60,
    "efficiency_gain_percent": 60
  }
}
```

### Execution Endpoints

**POST /execute** - Execute workflow
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "plan_id": "550e8400-e29b-41d4-a716-446655440002",
    "dry_run": false,
    "max_workers": 5
  }'

# Response
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "running"
}
```

**GET /execute/{execution_id}** - Get execution status
```bash
curl http://localhost:8000/execute/550e8400-e29b-41d4-a716-446655440003

# Response
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440003",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "total_tasks": 3,
  "completed_tasks": 2,
  "failed_tasks": 0,
  "start_time": "2024-05-17T14:30:00Z",
  "estimated_completion": "2024-05-17T14:31:00Z"
}
```

**GET /execute/{execution_id}/metrics** - Get execution metrics
```bash
curl http://localhost:8000/execute/550e8400-e29b-41d4-a716-446655440003/metrics

# Response
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440003",
  "duration_seconds": 60,
  "efficiency_gain_percent": 55,
  "resource_utilization": {
    "cpu_percent": 75,
    "memory_mb": 512
  },
  "task_metrics": [...]
}
```

### Monitoring Endpoints

**GET /metrics** - Prometheus metrics
```bash
curl http://localhost:8000/metrics

# Response (Prometheus format)
# TYPE parallelize_workflows_total counter
# HELP parallelize_workflows_total Total number of workflows
parallelize_workflows_total 125
```

**GET /alerts** - List active alerts
```bash
curl "http://localhost:8000/alerts?limit=50"

# Response
{
  "total": 3,
  "alerts": [
    {
      "alert_id": "alert-001",
      "severity": "warning",
      "message": "High memory usage",
      "timestamp": "2024-05-17T14:30:00Z"
    }
  ]
}
```

### Performance Endpoints

**GET /performance/stats** - Performance statistics
```bash
curl http://localhost:8000/performance/stats

# Response
{
  "avg_efficiency_gain": 52,
  "total_time_saved_seconds": 45000,
  "workflows_optimized": 125,
  "cpu_efficiency": 82,
  "memory_efficiency": 75
}
```

**GET /performance/cache** - Cache statistics
```bash
curl http://localhost:8000/performance/cache

# Response
{
  "cache_hits": 1245,
  "cache_misses": 312,
  "hit_rate_percent": 79.9,
  "total_queries": 1557
}
```

---

## WebSocket Real-Time Updates

### WebSocket Channels

**1. Workflow Updates** (`ws://localhost:8000/ws/workflows/{workflow_id}`)

```javascript
// Client code
const ws = new WebSocket('ws://localhost:8000/ws/workflows/550e8400...');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
  // {
  //   "type": "workflow_update",
  //   "workflow_id": "550e8400...",
  //   "status": "running",
  //   "completed_tasks": 2,
  //   "total_tasks": 3
  // }
};
```

**2. Metrics Streaming** (`ws://localhost:8000/ws/metrics`)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/metrics');

ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  // {
  //   "type": "metrics",
  //   "cpu_usage": 45.2,
  //   "memory_usage": 512,
  //   "active_workflows": 5,
  //   "timestamp": "2024-05-17T14:30:00Z"
  // }
};
```

**3. Alert Notifications** (`ws://localhost:8000/ws/alerts`)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts');

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  // {
  //   "type": "alert",
  //   "severity": "warning",
  //   "message": "High memory usage detected",
  //   "alert_id": "alert-001"
  // }
};
```

### Connection Management

```javascript
class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = {};
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('Connected');
      this.emit('connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.emit('message', data);
    };

    this.ws.onerror = (error) => {
      console.error('Error:', error);
      this.emit('error', error);
    };

    this.ws.onclose = () => {
      console.log('Disconnected');
      this.emit('disconnected');
      this.reconnect();
    };
  }

  reconnect() {
    setTimeout(() => {
      console.log('Reconnecting...');
      this.connect();
    }, 3000);
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
```

---

## Vue.js Components

### Page Components

#### Dashboard.vue
```vue
<template>
  <div class="dashboard">
    <h1>Dashboard</h1>
    
    <!-- Key Metrics -->
    <div class="metrics-grid">
      <MetricCard title="Active Workflows" :value="activeWorkflows" />
      <MetricCard title="Efficiency Gain" :value="efficiencyGain + '%'" />
      <MetricCard title="Success Rate" :value="successRate + '%'" />
      <MetricCard title="Avg Duration" :value="avgDuration + 's'" />
    </div>

    <!-- Recent Workflows -->
    <div class="card">
      <h2>Recent Workflows</h2>
      <WorkflowTable :workflows="recentWorkflows" />
    </div>

    <!-- System Health -->
    <div class="card">
      <h2>System Health</h2>
      <HealthStatus :health="systemHealth" />
    </div>

    <!-- Active Alerts -->
    <div class="card">
      <h2>Active Alerts</h2>
      <AlertsList :alerts="activeAlerts" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { workflowStore } from '@/stores/workflowStore';
import { monitoringStore } from '@/stores/monitoringStore';

const activeWorkflows = ref(0);
const efficiencyGain = ref(0);
const successRate = ref(0);
const avgDuration = ref(0);
const recentWorkflows = ref([]);
const systemHealth = ref(null);
const activeAlerts = ref([]);

onMounted(async () => {
  await monitoringStore.fetchMetrics();
  activeWorkflows.value = monitoringStore.activeCount;
  efficiencyGain.value = monitoringStore.avgEfficiency;
  successRate.value = monitoringStore.successRate;
});
</script>

<style scoped>
.dashboard {
  padding: 2rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}
</style>
```

#### Workflows.vue
```vue
<template>
  <div class="workflows">
    <h1>Workflows</h1>
    
    <!-- Create Workflow Form -->
    <div class="card create-form">
      <h2>Create Workflow</h2>
      <form @submit.prevent="createWorkflow">
        <input v-model="form.name" placeholder="Workflow name" required />
        <input v-model="form.description" placeholder="Description" />
        <button type="submit">Create</button>
      </form>
    </div>

    <!-- Workflows List -->
    <div class="card">
      <h2>All Workflows</h2>
      <div class="filters">
        <select v-model="filterStatus">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Tasks</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="workflow in filteredWorkflows" :key="workflow.workflow_id">
            <td>{{ workflow.name }}</td>
            <td><Badge :status="workflow.status" /></td>
            <td>{{ workflow.task_count }}</td>
            <td>{{ formatDate(workflow.created_at) }}</td>
            <td>
              <button @click="analyzeWorkflow(workflow)">Analyze</button>
              <button @click="deleteWorkflow(workflow)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { workflowStore } from '@/stores/workflowStore';

const form = ref({ name: '', description: '' });
const filterStatus = ref('');

const filteredWorkflows = computed(() => {
  if (!filterStatus.value) return workflowStore.workflows;
  return workflowStore.workflows.filter(w => w.status === filterStatus.value);
});

const createWorkflow = async () => {
  await workflowStore.createWorkflow(form.value);
  form.value = { name: '', description: '' };
};

const analyzeWorkflow = (workflow) => {
  workflowStore.analyzeWorkflow(workflow.workflow_id);
};

const deleteWorkflow = (workflow) => {
  if (confirm('Delete this workflow?')) {
    workflowStore.deleteWorkflow(workflow.workflow_id);
  }
};

const formatDate = (date) => new Date(date).toLocaleDateString();
</script>
```

#### Analysis.vue, Decisions.vue, Execution.vue, Monitoring.vue, Performance.vue
(Follow similar patterns with appropriate data and interactions)

---

## State Management

### Pinia Stores

**workflowStore.js**:
```javascript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from '@/services/api';

export const useWorkflowStore = defineStore('workflow', () => {
  const workflows = ref([]);
  const analyses = ref([]);
  const decisions = ref([]);
  const executions = ref([]);

  const activeCount = computed(() =>
    workflows.value.filter(w => w.status === 'running').length
  );

  const createWorkflow = async (data) => {
    const response = await api.createWorkflow(data);
    await fetchWorkflows();
    return response;
  };

  const fetchWorkflows = async () => {
    const response = await api.getWorkflows();
    workflows.value = response.workflows;
  };

  const analyzeWorkflow = async (workflowId) => {
    const response = await api.analyzeWorkflow(workflowId);
    await fetchAnalyses();
    return response;
  };

  const deleteWorkflow = async (workflowId) => {
    await api.deleteWorkflow(workflowId);
    workflows.value = workflows.value.filter(w => w.workflow_id !== workflowId);
  };

  return {
    workflows,
    analyses,
    decisions,
    executions,
    activeCount,
    createWorkflow,
    fetchWorkflows,
    analyzeWorkflow,
    deleteWorkflow
  };
});
```

---

## Authentication & CORS

### CORS Configuration (Backend)

```python
# In api.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Development
        "http://localhost:5173",       # Vite dev server
        "https://dashboard.example.com" # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend CORS Handling

```javascript
// services/api.js
import axios from 'axios';

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle authentication error
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## Frontend Development

### Setup

```bash
# Install dependencies
cd frontend
npm install

# Development server (Vite)
npm run dev
# Server running at http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Tips

**Hot Module Replacement (HMR)**: Changes automatically reload without page refresh
**Vue DevTools**: Browser extension for debugging Vue state
**Network Tab**: Monitor API calls and WebSocket messages
**Console**: Log debugging and error tracking

### Environment Configuration

**`.env.development`**:
```
VITE_API_URL=http://localhost:8000
VITE_LOG_LEVEL=debug
```

**`.env.production`**:
```
VITE_API_URL=https://api.example.com
VITE_LOG_LEVEL=error
```

---

## Summary

The Phase 6 Web Dashboard provides:
- Modern Vue.js 3 interface with 7 main pages
- 27 REST API endpoints (24 functional + 3 docs)
- 3 WebSocket channels for real-time updates
- Comprehensive state management with Pinia
- Responsive, accessible UI components
- Full CORS and authentication support
- Complete API documentation and examples
