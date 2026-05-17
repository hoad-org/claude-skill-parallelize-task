# Parallelize-Task REST API - Complete Endpoint Reference

## Quick Stats
- **Total Endpoints**: 27
- **Functional Endpoints**: 24
- **Documentation Endpoints**: 3
- **HTTP Methods**: GET, POST, DELETE
- **WebSocket Endpoints**: 3

## Endpoint Categories

### 1. Health & Status (3 endpoints)

#### GET /health
- **Description**: Basic health check
- **Response**: 200 OK
- **Returns**: `{status: "healthy", timestamp: ISO8601, uptime_seconds: float, version: "1.1.0"}`
- **Use**: Liveness probe

#### GET /health/detailed
- **Description**: Detailed system health
- **Response**: 200 OK
- **Returns**: Detailed health with components, memory, CPU, active workflows
- **Use**: Comprehensive health monitoring

#### GET /health/detailed
- **Description**: System component status
- **Components**: api, monitoring, performance
- **Use**: Component health verification

---

### 2. Workflow Management (4 endpoints)

#### POST /workflows
- **Description**: Create new workflow
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "tasks": [{"id": "string", "name": "string", ...}],
    "dependencies": [{"source_task_id": "string", "target_task_id": "string", ...}],
    "metadata": {}
  }
  ```
- **Response**: 200 OK
- **Returns**: `{workflow_id: "uuid", status: "created"}`

#### GET /workflows
- **Description**: List all workflows
- **Query Parameters**:
  - `status`: Filter by status (optional)
  - `limit`: Max results (1-1000, default 100)
  - `offset`: Pagination offset (default 0)
- **Response**: 200 OK
- **Returns**: `{total: int, offset: int, limit: int, workflows: [...]}`

#### GET /workflows/{workflow_id}
- **Description**: Get workflow details
- **Path Parameters**: `workflow_id` (UUID)
- **Response**: 200 OK or 404 Not Found
- **Returns**: Complete workflow object with tasks and dependencies

#### DELETE /workflows/{workflow_id}
- **Description**: Delete workflow
- **Path Parameters**: `workflow_id` (UUID)
- **Response**: 200 OK or 404 Not Found
- **Returns**: `{status: "deleted"}`

---

### 3. Analysis (2 endpoints)

#### POST /analyze
- **Description**: Run complexity analysis on workflow
- **Request Body**:
  ```json
  {
    "workflow_id": "uuid",
    "include_complexity": true,
    "include_feasibility": true
  }
  ```
- **Response**: 200 OK or 404 Not Found
- **Returns**: `{analysis_id: "uuid", status: "completed"}`

#### GET /analyze/{analysis_id}
- **Description**: Get analysis results
- **Path Parameters**: `analysis_id` (UUID)
- **Response**: 200 OK or 404 Not Found
- **Returns**: Complete analysis with complexity scores, critical path, etc.

---

### 4. Decision Generation (2 endpoints)

#### POST /decide
- **Description**: Generate execution strategy
- **Request Body**:
  ```json
  {
    "analysis_id": "uuid",
    "prefer_parallel": true,
    "resource_constraints": {}
  }
  ```
- **Response**: 200 OK or 404 Not Found
- **Returns**: `{decision_id: "uuid", status: "completed"}`

#### GET /decide/{decision_id}
- **Description**: Get decision results
- **Path Parameters**: `decision_id` (UUID)
- **Response**: 200 OK or 404 Not Found
- **Returns**: Complete execution plan with efficiency metrics

---

### 5. Execution (3 endpoints)

#### POST /execute
- **Description**: Execute workflow
- **Request Body**:
  ```json
  {
    "workflow_id": "uuid",
    "plan_id": "uuid (optional)",
    "dry_run": false,
    "max_workers": 5 (optional)
  }
  ```
- **Response**: 200 OK or 404 Not Found
- **Returns**: `{execution_id: "uuid", status: "running"}`

#### GET /execute/{execution_id}
- **Description**: Get execution status
- **Path Parameters**: `execution_id` (UUID)
- **Response**: 200 OK or 404 Not Found
- **Returns**: Complete execution result with task counts and status

#### GET /execute/{execution_id}/metrics
- **Description**: Get execution metrics
- **Path Parameters**: `execution_id` (UUID)
- **Response**: 200 OK or 404 Not Found
- **Returns**: Performance metrics, task completion, efficiency data

---

### 6. Monitoring (2 endpoints)

#### GET /metrics
- **Description**: Get Prometheus-compatible metrics
- **Response**: 200 OK
- **Returns**: 
  ```json
  {
    "workflows_total": int,
    "workflows_active": int,
    "tasks_completed_total": int,
    "tasks_failed_total": int,
    "average_parallelization_gain": float,
    "cache_hit_rate": float,
    "cache_misses_total": int
  }
  ```

#### GET /alerts
- **Description**: Get active alerts
- **Query Parameters**:
  - `resolved`: Filter by resolution status (optional)
  - `limit`: Max results (1-1000, default 100)
- **Response**: 200 OK
- **Returns**: `{total: int, alerts: [...]}`

---

### 7. Performance (2 endpoints)

#### GET /performance/stats
- **Description**: Get performance statistics
- **Response**: 200 OK
- **Returns**:
  ```json
  {
    "total_workflows": int,
    "total_tasks": int,
    "average_task_duration": float,
    "average_workflow_duration": float,
    "parallelization_success_rate": float,
    "resource_utilization": {},
    "optimization_improvements": {}
  }
  ```

#### GET /performance/cache
- **Description**: Get cache statistics
- **Response**: 200 OK
- **Returns**:
  ```json
  {
    "total_caches": int,
    "cache_hits": int,
    "cache_misses": int,
    "hit_rate": float,
    "most_accessed_workflows": [],
    "cache_size_mb": float
  }
  ```

---

### 8. WebSocket (3 endpoints)

#### WS /ws/workflows/{workflow_id}
- **Description**: Real-time workflow status updates
- **Path Parameters**: `workflow_id` (UUID)
- **Message Format**: `{type: "workflow_update", workflow_id: "uuid", status: "string", timestamp: ISO8601}`
- **Frequency**: Every 1 second

#### WS /ws/metrics
- **Description**: Real-time metrics stream
- **Message Format**: `{type: "metrics", workflows_total: int, workflows_active: int, cache_hit_rate: float, timestamp: ISO8601}`
- **Frequency**: Every 5 seconds

#### WS /ws/alerts
- **Description**: Real-time alert notifications
- **Message Format**: `{type: "alerts", count: int, alerts: [...], timestamp: ISO8601}`
- **Frequency**: Every 10 seconds

---

### 9. Documentation (3 endpoints)

#### GET /docs
- **Description**: Swagger UI interactive documentation
- **Response**: HTML page with interactive API explorer

#### GET /redoc
- **Description**: ReDoc API documentation
- **Response**: HTML page with formatted API reference

#### GET /openapi.json
- **Description**: OpenAPI schema in JSON format
- **Response**: JSON schema for API specification
- **Use**: Tool integration, code generation

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 404 | Not Found | Workflow/Analysis/Decision/Execution not found |
| 405 | Method Not Allowed | Wrong HTTP method for endpoint |
| 422 | Unprocessable Entity | Invalid request body |

---

## Request/Response Examples

### Create Workflow
```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Pipeline",
    "description": "Extract, transform, load",
    "tasks": [
      {
        "id": "task1",
        "name": "Extract",
        "estimated_duration": 10,
        "parallelizable": true,
        "priority": "normal"
      }
    ],
    "dependencies": []
  }'
```

### Analyze Workflow
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "abc123-def456",
    "include_complexity": true,
    "include_feasibility": true
  }'
```

### Execute Workflow
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "abc123-def456",
    "dry_run": false
  }'
```

### Get Metrics
```bash
curl http://localhost:8000/metrics
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/metrics');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Metrics update:', data);
};
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "timestamp": "2024-05-17T10:30:45.123456"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Production deployments should add:
- Per-IP rate limits
- Per-user rate limits
- Request throttling
- Burst allowances

---

## Authentication

Currently no authentication is required. Production deployments should add:
- API key authentication
- JWT token validation
- OAuth 2.0 integration
- Role-based access control

---

## CORS Configuration

Currently CORS allows all origins for development:
- `allow_origins=["*"]`
- `allow_credentials=True`
- `allow_methods=["*"]`
- `allow_headers=["*"]`

Production should restrict to specific domains.

---

## Pagination

List endpoints support pagination:
- **limit**: Number of results (1-1000, default 100)
- **offset**: Starting position (default 0)

Example:
```
GET /workflows?limit=10&offset=20
```

---

## Filtering

Some endpoints support filtering:
- **status**: Filter by workflow status (created, running, completed, failed)

Example:
```
GET /workflows?status=running&limit=50
```

---

## Field Types

### Task
```typescript
{
  id: string,
  name: string,
  description?: string,
  estimated_duration: number,
  parallelizable: boolean,
  priority: "critical" | "high" | "normal" | "low",
  resource_type?: string,
  max_concurrent: number,
  metadata: Record<string, any>
}
```

### TaskDependency
```typescript
{
  source_task_id: string,
  target_task_id: string,
  dependency_type: "hard" | "soft" | "data",
  condition?: string
}
```

---

## Testing Endpoints

### Health Check
```bash
# Should always respond with 200
curl -i http://localhost:8000/health
```

### Verify API
```bash
# Check OpenAPI schema
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

---

## Troubleshooting

### Endpoint Not Found
- Ensure API is running on correct port (default 8000)
- Check endpoint path for typos
- Verify request method (GET, POST, DELETE)

### Invalid Request
- Check Content-Type header is `application/json`
- Validate request body JSON syntax
- Ensure all required fields are present

### Workflow Not Found
- Verify workflow_id is correct UUID format
- Check workflow was created successfully
- List all workflows to confirm

### WebSocket Connection Failed
- Check WebSocket endpoint path
- Ensure firewall allows WebSocket connections
- Verify proxy/load balancer supports WebSockets

---

## API Version

Current API Version: **1.1.0**

Last Updated: May 17, 2026

For detailed documentation, see `API_DASHBOARD_README.md`
