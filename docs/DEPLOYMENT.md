# Deployment Guide — Parallelizer Task Skill

Comprehensive guide for deploying the Parallelizer Task skill using Docker, Kubernetes, and Helm.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Deployment](#docker-deployment)
3. [Docker Compose](#docker-compose)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Helm Deployment](#helm-deployment)
6. [Configuration](#configuration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Health Checks](#health-checks)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)
11. [Production Checklist](#production-checklist)

---

## Quick Start

### Using Docker Compose (Recommended for Local Development)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f parallelizer

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

### Using Kubernetes

```bash
# Deploy to cluster
./scripts/deploy.sh 1.1.0

# Verify deployment
kubectl get pods -l app=parallelizer
kubectl logs -l app=parallelizer

# Access the service
kubectl port-forward svc/parallelizer-api 8000:8000
```

### Using Helm

```bash
# Install release
./scripts/helm-deploy.sh parallelizer default

# Verify release
helm status parallelizer
helm get values parallelizer

# Upgrade release
helm upgrade parallelizer ./helm/parallelizer -n default

# Rollback if needed
helm rollback parallelizer -n default
```

---

## Docker Deployment

### Building the Image

```bash
# Build with default tag (uses version from pyproject.toml)
./scripts/build.sh

# Build with custom tag
./scripts/build.sh 1.1.0 docker.io

# Build locally without pushing
docker build -t parallelizer:latest .
```

### Running the Container

```bash
# Basic run
docker run -p 8000:8000 parallelizer:latest

# With environment variables
docker run \
  -p 8000:8000 \
  -e PARALLELIZER_ENV=production \
  -e PARALLELIZER_LOG_LEVEL=INFO \
  -e REDIS_URL=redis://redis:6379/0 \
  parallelizer:latest

# With volume mounts
docker run \
  -p 8000:8000 \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  parallelizer:latest

# Run in background
docker run -d \
  --name parallelizer-api \
  -p 8000:8000 \
  parallelizer:latest
```

### Pushing to Registry

```bash
# Push to Docker Hub
./scripts/push.sh 1.1.0 docker.io

# Push to GitHub Container Registry
./scripts/push.sh 1.1.0 ghcr.io

# Verify image in registry
docker pull docker.io/parallelizer:1.1.0
docker inspect docker.io/parallelizer:1.1.0
```

---

## Docker Compose

### Starting Services

```bash
# Build and start in foreground
docker-compose up

# Start in background
docker-compose up -d

# Only start specific services
docker-compose up -d parallelizer redis

# Rebuild images
docker-compose up -d --build
```

### Managing Services

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs                    # All services
docker-compose logs -f parallelizer    # Follow parallelizer logs
docker-compose logs --tail=100         # Last 100 lines

# Stop services
docker-compose stop

# Remove containers (keep volumes)
docker-compose rm

# Complete cleanup
docker-compose down -v
```

### Service Configuration

The docker-compose.yml includes:

- **parallelizer**: Main API service (port 8000, metrics 9090)
- **redis**: Distributed cache (port 6379)
- **prometheus**: Metrics collection (port 9091)
- **grafana**: Visualization dashboard (port 3000)

All services have health checks configured and automatic restart policies.

---

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### Deployment

```bash
# Deploy all manifests
./scripts/deploy.sh 1.1.0 default

# Or deploy manually
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### Verification

```bash
# Check pod status
kubectl get pods -l app=parallelizer
kubectl describe pod <pod-name>

# View logs
kubectl logs -l app=parallelizer
kubectl logs -f <pod-name>

# Check services
kubectl get svc
kubectl describe svc parallelizer-api

# Check ingress
kubectl get ingress
kubectl describe ingress parallelizer-ingress
```

### Port Forwarding

```bash
# Forward API port
kubectl port-forward svc/parallelizer-api 8000:8000

# Forward metrics port
kubectl port-forward svc/parallelizer-api 9090:9090

# Forward Prometheus
kubectl port-forward svc/prometheus 9091:9090

# Forward Grafana
kubectl port-forward svc/grafana 3000:3000
```

### Accessing the Application

```bash
# Via port-forward
curl http://localhost:8000/health

# Via LoadBalancer (if configured)
curl http://<external-ip>:80/health

# Via Ingress
curl https://parallelizer.example.com/health
```

---

## Helm Deployment

### Installation

```bash
# Verify Helm chart
helm lint helm/parallelizer

# Install release
helm install parallelizer helm/parallelizer -n default --values helm/parallelizer/values.yaml

# Install to specific namespace
kubectl create namespace parallelizer-prod
helm install parallelizer helm/parallelizer -n parallelizer-prod

# Dry-run to verify
helm install parallelizer helm/parallelizer --dry-run --debug
```

### Upgrade

```bash
# Upgrade to new version
helm upgrade parallelizer helm/parallelizer

# Upgrade with custom values
helm upgrade parallelizer helm/parallelizer --values custom-values.yaml

# Upgrade specific parameters
helm upgrade parallelizer helm/parallelizer --set replicaCount=5
```

### Management

```bash
# View release status
helm status parallelizer

# View release values
helm get values parallelizer

# View rendered manifests
helm get manifest parallelizer

# View release history
helm history parallelizer

# Rollback to previous version
helm rollback parallelizer

# Uninstall release
helm uninstall parallelizer
```

### Custom Values

Create a custom values file:

```yaml
# custom-values.yaml
replicaCount: 5

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60

application:
  logLevel: "DEBUG"
  maxParallelTasks: 200
```

Then deploy:

```bash
helm upgrade parallelizer helm/parallelizer --values custom-values.yaml
```

---

## Configuration

### Environment Variables

Key environment variables for deployment:

```bash
# Application
PARALLELIZER_ENV=production              # Environment name
PARALLELIZER_LOG_LEVEL=INFO              # Logging level
PARALLELIZER_DATA_DIR=/app/data          # Data directory

# Monitoring
PARALLELIZER_MONITORING_ENABLED=true     # Enable metrics
PARALLELIZER_METRICS_PORT=9090           # Metrics port

# Redis
REDIS_URL=redis://redis:6379/0           # Redis connection
REDIS_PASSWORD=password                  # Redis auth

# API
API_HOST=0.0.0.0                         # API host
API_PORT=8000                            # API port
API_WORKERS=4                            # Worker processes
```

### Configuration Files

#### ConfigMap (k8s/configmap.yaml)

Contains application configuration:
- `app_config.yaml` — Application settings
- `prometheus_config.yaml` — Prometheus scrape config
- `settings.json` — Feature flags
- `health_config.yaml` — Health check endpoints

#### Secrets (k8s/secrets.yaml)

Contains sensitive data:
- `redis_url` — Redis connection string
- `api_token` — API authentication token
- `db_*` — Database credentials
- `aws_*` — AWS credentials
- Monitoring credentials

**Important**: Replace all default values in secrets before deployment to production.

---

## Monitoring & Observability

### Prometheus

Metrics are exported on port 9090 at `/metrics` endpoint.

```bash
# Access Prometheus
curl http://localhost:9091/graph

# Query metrics
curl 'http://localhost:9091/api/v1/query?query=parallelizer_tasks_total'
```

### Grafana

Visualization dashboard available on port 3000.

```bash
# Access Grafana
open http://localhost:3000
# Default: admin/admin
```

### Key Metrics

- `parallelizer_tasks_total` — Total tasks processed
- `parallelizer_tasks_duration_seconds` — Task execution time
- `parallelizer_dag_size` — Dependency graph size
- `parallelizer_optimization_ratio` — Parallelization improvement
- `parallelizer_errors_total` — Total errors
- `parallelizer_cache_hits_total` — Cache hit rate

---

## Health Checks

### Endpoints

#### Liveness Probe
```bash
curl http://localhost:8000/health
# Returns: 200 OK
```

#### Readiness Probe
```bash
curl http://localhost:8000/ready
# Returns: 200 OK if dependencies are available
```

#### Startup Probe
```bash
curl http://localhost:8000/startup
# Returns: 200 OK once initialization is complete
```

### Kubernetes Configuration

Health checks are configured in the deployment:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Scaling

### Horizontal Scaling (More Replicas)

```bash
# Scale deployment
kubectl scale deployment parallelizer-api --replicas=5

# Verify scaling
kubectl get pods -l app=parallelizer

# Autoscaling (using HPA)
kubectl get hpa
kubectl describe hpa parallelizer-hpa
```

### Vertical Scaling (More Resources)

Update resource requests/limits in deployment or Helm values:

```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using hey
go install github.com/rakyll/hey@latest
hey -n 1000 -c 50 http://localhost:8000/health
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# View logs
kubectl logs <pod-name>

# Check events
kubectl get events

# Check resource availability
kubectl top nodes
kubectl top pods
```

### Failed Liveness Probe

```bash
# Check application logs
kubectl logs <pod-name>

# Port forward and test manually
kubectl port-forward pod/<pod-name> 8000:8000
curl http://localhost:8000/health

# Increase initial delay if startup is slow
kubectl patch deployment parallelizer-api -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"parallelizer","livenessProbe":{"initialDelaySeconds":30}}]}}}}'
```

### Memory Issues

```bash
# Check pod memory usage
kubectl top pods

# View memory limits
kubectl describe pod <pod-name> | grep -A 5 Limits

# Increase memory limit
kubectl set resources deployment parallelizer-api --limits=memory=4Gi
```

### Network Issues

```bash
# Test connectivity within cluster
kubectl exec -it <pod-name> -- bash
curl http://redis:6379   # Test Redis connectivity
curl http://prometheus:9090  # Test Prometheus

# Check service endpoints
kubectl get endpoints
kubectl describe svc parallelizer-api
```

### Volume Issues

```bash
# Check PVC status
kubectl get pvc
kubectl describe pvc parallelizer-data-pvc

# Check volume mounts
kubectl describe pod <pod-name> | grep -A 10 Mounts

# View volume size
kubectl exec -it <pod-name> -- df -h /app/data
```

---

## Production Checklist

Before deploying to production:

### Security
- [ ] All secrets changed from defaults (see k8s/secrets.yaml)
- [ ] TLS/SSL certificates configured in ingress
- [ ] RBAC policies reviewed and applied
- [ ] Network policies in place
- [ ] Container image scanned for vulnerabilities
- [ ] Non-root user enforced in Pod security context

### Configuration
- [ ] Environment variables set correctly
- [ ] Redis password secured
- [ ] API token generated and secured
- [ ] Database credentials configured
- [ ] Monitoring credentials set
- [ ] Log levels appropriate for production

### Monitoring
- [ ] Prometheus configured and scraping metrics
- [ ] Grafana dashboards created
- [ ] Alert rules configured
- [ ] Logging aggregation set up
- [ ] Performance baselines established

### Availability
- [ ] Multiple replicas configured (min 3)
- [ ] Autoscaling policies in place
- [ ] Pod disruption budgets configured
- [ ] Health checks verified
- [ ] Resource limits set appropriately
- [ ] Backup strategy implemented

### Deployment
- [ ] Ingress configured with valid domain
- [ ] DNS records pointing to load balancer
- [ ] TLS certificates valid
- [ ] Deployment pipeline tested
- [ ] Rollback procedures documented
- [ ] Load testing completed

### Testing
- [ ] Smoke tests pass
- [ ] Integration tests pass
- [ ] Load tests completed
- [ ] Failover tested
- [ ] Disaster recovery tested

### Documentation
- [ ] Runbooks created
- [ ] On-call procedures documented
- [ ] Escalation paths defined
- [ ] Known issues documented

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Guide](https://prometheus.io/docs/introduction/overview/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)

For issues or questions, refer to the main README.md or project documentation.
