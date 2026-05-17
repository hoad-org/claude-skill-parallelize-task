# Phase 6: Complete Deployment Examples

Practical examples for deploying and using Parallelize-Task in various environments.

## Table of Contents
1. [Local Docker Development](#local-docker-development)
2. [Kubernetes Deployment](#kubernetes-deployment)
3. [Helm Deployment](#helm-deployment)
4. [Multi-Environment Setup](#multi-environment-setup)
5. [Dashboard Usage Examples](#dashboard-usage-examples)
6. [API Integration Examples](#api-integration-examples)
7. [Monitoring Examples](#monitoring-examples)

---

## Local Docker Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/rhyscraig/claude-skill-parallelize-task.git
cd claude-skill-parallelize-task

# Start all services with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
# NAME                        STATUS
# parallelize-task-api        Up (healthy)
# parallelize-task-cache      Up (healthy)
# parallelize-task-prometheus Up
# parallelize-task-grafana    Up

# Access services
# API: http://localhost:8000
# Dashboard: http://localhost:3000
# Prometheus: http://localhost:9091
# Grafana: http://localhost:3000 (admin/admin)
```

### Create and Analyze Workflow

```bash
#!/bin/bash

API="http://localhost:8000"

# Step 1: Create workflow
echo "Creating workflow..."
WORKFLOW=$(curl -s -X POST "$API/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ETL Pipeline",
    "description": "Extract, Transform, Load",
    "tasks": [
      {"id": "extract", "name": "Extract Data", "duration": 30},
      {"id": "transform", "name": "Transform Data", "duration": 45},
      {"id": "load", "name": "Load to Warehouse", "duration": 20},
      {"id": "validate", "name": "Validate Data", "duration": 15}
    ],
    "dependencies": [
      {"source_task_id": "extract", "target_task_id": "transform"},
      {"source_task_id": "transform", "target_task_id": "load"},
      {"source_task_id": "load", "target_task_id": "validate"}
    ]
  }')

WORKFLOW_ID=$(echo "$WORKFLOW" | jq -r '.workflow_id')
echo "Created workflow: $WORKFLOW_ID"

# Step 2: Analyze workflow
echo "Analyzing workflow..."
ANALYSIS=$(curl -s -X POST "$API/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"workflow_id\": \"$WORKFLOW_ID\"}")

ANALYSIS_ID=$(echo "$ANALYSIS" | jq -r '.analysis_id')
echo "Analysis ID: $ANALYSIS_ID"

# Step 3: Get analysis results
echo "Analysis results:"
curl -s "$API/analyze/$ANALYSIS_ID" | jq '.'

# Step 4: Generate execution plan
echo "Generating execution strategy..."
DECISION=$(curl -s -X POST "$API/decide" \
  -H "Content-Type: application/json" \
  -d "{\"analysis_id\": \"$ANALYSIS_ID\"}")

DECISION_ID=$(echo "$DECISION" | jq -r '.decision_id')
echo "Decision ID: $DECISION_ID"

# Step 5: View decision
echo "Execution strategy:"
curl -s "$API/decide/$DECISION_ID" | jq '.'

# Step 6: Execute workflow (dry-run)
echo "Executing workflow (dry-run)..."
EXECUTION=$(curl -s -X POST "$API/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"workflow_id\": \"$WORKFLOW_ID\",
    \"plan_id\": \"$DECISION_ID\",
    \"dry_run\": true
  }")

EXECUTION_ID=$(echo "$EXECUTION" | jq -r '.execution_id')
echo "Execution ID: $EXECUTION_ID"

# Step 7: Get execution metrics
echo "Execution results:"
curl -s "$API/execute/$EXECUTION_ID/metrics" | jq '.'
```

### Docker Logs & Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f parallelize-api

# Enter container shell
docker exec -it parallelize-task-api bash

# Run CLI commands in container
docker exec parallelize-task-api parallelize-task --help
```

### Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (caution: deletes data)
docker-compose down -v

# Remove images
docker rmi parallelize-task parallelize-dashboard
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Connect to cluster
kubectl config use-context my-cluster
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace parallelize-task

# Create Redis secret
kubectl create secret generic redis-credentials \
  --from-literal=password=$(openssl rand -base64 32) \
  -n parallelize-task

# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap-api.yaml
kubectl apply -f k8s/secret-redis.yaml
kubectl apply -f k8s/pvc-data.yaml
kubectl apply -f k8s/redis-statefulset.yaml
kubectl apply -f k8s/service-redis.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/service-api.yaml
kubectl apply -f k8s/deployment-dashboard.yaml
kubectl apply -f k8s/service-dashboard.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment/parallelize-api -n parallelize-task
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n parallelize-task -w

# Check services
kubectl get svc -n parallelize-task

# Check ingress
kubectl get ingress -n parallelize-task

# View pod logs
kubectl logs deployment/parallelize-api -n parallelize-task

# Test API endpoint (port-forward)
kubectl port-forward svc/api-service 8000:8000 -n parallelize-task
curl http://localhost:8000/health

# Test Dashboard (port-forward)
kubectl port-forward svc/dashboard-service 3000:3000 -n parallelize-task
# Open http://localhost:3000 in browser
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment parallelize-api --replicas=5 -n parallelize-task

# Check HPA status
kubectl get hpa -n parallelize-task

# Watch autoscaling
kubectl describe hpa parallelize-api-hpa -n parallelize-task

# Generate load to trigger scaling
kubectl run -it --rm load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://api-service:8000/health; done"
```

### Update Deployment

```bash
# Update image
kubectl set image deployment/parallelize-api \
  api=parallelize-task:1.2.0 \
  -n parallelize-task

# Check rollout status
kubectl rollout status deployment/parallelize-api -n parallelize-task

# View rollout history
kubectl rollout history deployment/parallelize-api -n parallelize-task

# Rollback if needed
kubectl rollout undo deployment/parallelize-api -n parallelize-task
```

---

## Helm Deployment

### Install with Helm

```bash
# Add repository
helm repo add parallelize https://charts.parallelize-task.io
helm repo update

# Install with default values (development)
helm install parallelize-dev parallelize/parallelize-task \
  -n parallelize-dev \
  --create-namespace

# Install with production values
helm install parallelize-prod parallelize/parallelize-task \
  -n parallelize-prod \
  --create-namespace \
  -f values-prod.yaml

# Install with custom values
helm install parallelize-custom parallelize/parallelize-task \
  -n parallelize-task \
  --create-namespace \
  --set api.replicaCount=10 \
  --set api.image.tag=1.2.0 \
  --set redis.auth.password=$(openssl rand -base64 32)
```

### Verify Helm Installation

```bash
# List releases
helm list -n parallelize-task

# Get release values
helm get values parallelize-prod -n parallelize-prod

# Get release manifest
helm get manifest parallelize-prod -n parallelize-prod

# Test chart
helm test parallelize-prod -n parallelize-prod
```

### Upgrade Release

```bash
# Upgrade to new version
helm upgrade parallelize-prod parallelize/parallelize-task \
  -n parallelize-prod \
  -f values-prod.yaml

# Dry-run to preview changes
helm upgrade parallelize-prod parallelize/parallelize-task \
  --dry-run --debug \
  -n parallelize-prod

# Upgrade with atomic rollback on failure
helm upgrade parallelize-prod parallelize/parallelize-task \
  --atomic \
  --timeout 5m \
  -n parallelize-prod

# Check upgrade progress
helm status parallelize-prod -n parallelize-prod
```

### Rollback Release

```bash
# View release history
helm history parallelize-prod -n parallelize-prod

# Rollback to previous version
helm rollback parallelize-prod -n parallelize-prod

# Rollback to specific revision
helm rollback parallelize-prod 2 -n parallelize-prod

# Verify rollback
kubectl rollout status deployment/parallelize-api -n parallelize-prod
```

---

## Multi-Environment Setup

### Environment Configuration

**Development** (`values-dev.yaml`):
```yaml
api:
  replicaCount: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
  autoscaling:
    enabled: false

dashboard:
  replicaCount: 1

redis:
  master:
    persistence:
      size: 1Gi
```

**Staging** (`values-staging.yaml`):
```yaml
api:
  replicaCount: 2
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 5

redis:
  master:
    persistence:
      size: 5Gi
  replica:
    replicaCount: 1
```

**Production** (`values-prod.yaml`):
```yaml
api:
  replicaCount: 5
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
  autoscaling:
    enabled: true
    minReplicas: 5
    maxReplicas: 20

redis:
  master:
    persistence:
      size: 20Gi
  replica:
    replicaCount: 2
```

### Deploy to All Environments

```bash
#!/bin/bash

CHART="parallelize/parallelize-task"

echo "Deploying to all environments..."

# Development
echo "Deploying to development..."
helm upgrade --install parallelize-dev "$CHART" \
  -n parallelize-dev --create-namespace \
  -f values-dev.yaml

# Staging
echo "Deploying to staging..."
helm upgrade --install parallelize-staging "$CHART" \
  -n parallelize-staging --create-namespace \
  -f values-staging.yaml

# Production
echo "Deploying to production..."
helm upgrade --install parallelize-prod "$CHART" \
  -n parallelize-prod --create-namespace \
  -f values-prod.yaml

echo "Deployment complete!"
```

---

## Dashboard Usage Examples

### Creating a Workflow via Dashboard

1. Navigate to **Workflows** page
2. Fill in **Create Workflow** form:
   - Name: "Data Processing Pipeline"
   - Description: "Process and analyze data"
3. Click **Create**
4. On Workflows list, click **Analyze** for newly created workflow
5. Navigate to **Analysis** to view results

### Monitoring Execution

1. Navigate to **Dashboard** for overview
2. Check **Active Alerts** for any warnings
3. Navigate to **Execution** to monitor active jobs
4. View **Performance** metrics for optimization gains

### Performance Analysis

1. Navigate to **Performance** page
2. View **Performance Statistics**:
   - Average efficiency gain
   - Total time saved
   - Optimization metrics
3. Review **Cache Statistics** for hit rates

---

## API Integration Examples

### Python Client Example

```python
import requests
import json

API_URL = "http://localhost:8000"

class ParallelizeClient:
    def __init__(self, base_url=API_URL):
        self.base_url = base_url
    
    def create_workflow(self, name, description, tasks, dependencies):
        response = requests.post(
            f"{self.base_url}/workflows",
            json={
                "name": name,
                "description": description,
                "tasks": tasks,
                "dependencies": dependencies
            }
        )
        return response.json()
    
    def analyze_workflow(self, workflow_id):
        response = requests.post(
            f"{self.base_url}/analyze",
            json={"workflow_id": workflow_id}
        )
        return response.json()
    
    def get_analysis_results(self, analysis_id):
        response = requests.get(
            f"{self.base_url}/analyze/{analysis_id}"
        )
        return response.json()
    
    def execute_workflow(self, workflow_id, plan_id=None, dry_run=False):
        response = requests.post(
            f"{self.base_url}/execute",
            json={
                "workflow_id": workflow_id,
                "plan_id": plan_id,
                "dry_run": dry_run
            }
        )
        return response.json()

# Usage
client = ParallelizeClient()

# Create workflow
workflow = client.create_workflow(
    name="Data Pipeline",
    description="ETL pipeline",
    tasks=[
        {"id": "extract", "name": "Extract"},
        {"id": "transform", "name": "Transform"},
        {"id": "load", "name": "Load"}
    ],
    dependencies=[
        {"source_task_id": "extract", "target_task_id": "transform"},
        {"source_task_id": "transform", "target_task_id": "load"}
    ]
)

# Analyze workflow
analysis = client.analyze_workflow(workflow["workflow_id"])
results = client.get_analysis_results(analysis["analysis_id"])
print(f"Efficiency gain: {results['efficiency_gain_percent']}%")

# Execute workflow
execution = client.execute_workflow(
    workflow["workflow_id"],
    dry_run=True
)
print(f"Execution ID: {execution['execution_id']}")
```

### JavaScript/Node.js Client Example

```javascript
const axios = require('axios');

class ParallelizeClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.api = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  async createWorkflow(name, description, tasks, dependencies) {
    const response = await this.api.post('/workflows', {
      name, description, tasks, dependencies
    });
    return response.data;
  }

  async analyzeWorkflow(workflowId) {
    const response = await this.api.post('/analyze', {
      workflow_id: workflowId
    });
    return response.data;
  }

  async getAnalysisResults(analysisId) {
    const response = await this.api.get(`/analyze/${analysisId}`);
    return response.data;
  }

  async executeWorkflow(workflowId, planId = null, dryRun = false) {
    const response = await this.api.post('/execute', {
      workflow_id: workflowId,
      plan_id: planId,
      dry_run: dryRun
    });
    return response.data;
  }
}

// Usage
const client = new ParallelizeClient();

async function example() {
  // Create workflow
  const workflow = await client.createWorkflow(
    'Data Pipeline',
    'ETL pipeline',
    [
      { id: 'extract', name: 'Extract' },
      { id: 'transform', name: 'Transform' },
      { id: 'load', name: 'Load' }
    ],
    [
      { source_task_id: 'extract', target_task_id: 'transform' },
      { source_task_id: 'transform', target_task_id: 'load' }
    ]
  );

  // Analyze
  const analysis = await client.analyzeWorkflow(workflow.workflow_id);
  const results = await client.getAnalysisResults(analysis.analysis_id);
  console.log(`Efficiency gain: ${results.efficiency_gain_percent}%`);

  // Execute
  const execution = await client.executeWorkflow(workflow.workflow_id, null, true);
  console.log(`Execution ID: ${execution.execution_id}`);
}

example().catch(console.error);
```

---

## Monitoring Examples

### Prometheus Query Examples

```promql
# Workflow execution rate
rate(parallelize_workflows_total[5m])

# P95 API latency
histogram_quantile(0.95, parallelize_api_latency_ms)

# Error rate
rate(parallelize_errors_total[5m])

# Success rate
(1 - rate(parallelize_errors_total[5m])) * 100

# Pod restart count
rate(kube_pod_container_status_restarts_total[15m])

# Memory usage percentage
(node_memory_usage_bytes / node_memory_total) * 100
```

### Alert Examples

```yaml
# High error rate alert
alert: HighErrorRate
expr: rate(parallelize_errors_total[5m]) > 0.05
annotations:
  summary: "Error rate above 5% for {{ $labels.instance }}"

# Slow API response
alert: SlowAPIResponse
expr: histogram_quantile(0.95, parallelize_api_latency_ms) > 1000
annotations:
  summary: "API P95 latency above 1 second"

# Pod crashing
alert: PodCrashing
expr: rate(kube_pod_container_status_restarts_total[15m]) > 0.1
annotations:
  summary: "Pod {{ $labels.pod_name }} restarting frequently"
```

---

## Summary

Phase 6 examples provide:
- Complete local Docker setup guide
- Kubernetes deployment with verification
- Helm chart installation and upgrades
- Multi-environment configuration
- Real-world API integration examples
- Client library examples (Python, JavaScript)
- Monitoring and alerting examples
- Production-ready deployment workflows
