# Deployment Quick Reference

Fast lookup for common deployment tasks.

## File Structure

```
project-root/
├── Dockerfile                          # Multi-stage production image
├── .dockerignore                       # Docker build exclusions
├── docker-compose.yml                  # Local development stack
├── k8s/                               # Kubernetes manifests
│   ├── deployment.yaml                # Pod deployment (3 replicas)
│   ├── service.yaml                   # Service definitions (3 types)
│   ├── configmap.yaml                 # Configuration management
│   ├── secrets.yaml                   # Sensitive data
│   ├── rbac.yaml                      # Service account & policies
│   └── ingress.yaml                   # HTTP ingress & autoscaling
├── helm/parallelizer/                 # Helm chart
│   ├── Chart.yaml                     # Chart metadata
│   ├── values.yaml                    # Default configuration
│   └── templates/                     # Helm templates
├── scripts/                           # Deployment automation
│   ├── build.sh                       # Docker build script
│   ├── push.sh                        # Docker push script
│   ├── deploy.sh                      # Kubernetes deploy script
│   └── helm-deploy.sh                 # Helm deploy script
├── config/                            # Configuration files
│   ├── prometheus.yml                 # Prometheus scrape config
│   └── grafana/                       # Grafana dashboards
├── .env.example                       # Environment template
├── docs/DEPLOYMENT.md                 # Full deployment guide
└── Makefile                           # Build targets
```

## Quick Commands

### Local Development (Docker Compose)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f parallelizer

# Stop services
docker-compose down

# Clean everything
docker-compose down -v
```

### Docker Image

```bash
# Build
make docker-build

# Build custom
./scripts/build.sh 1.1.0 docker.io

# Push
make docker-push

# Run locally
docker run -p 8000:8000 parallelizer:latest
```

### Kubernetes

```bash
# Deploy
make k8s-deploy

# Verify
make k8s-verify

# Port forward
kubectl port-forward svc/parallelizer-api 8000:8000

# View logs
kubectl logs -f -l app=parallelizer

# Delete
kubectl delete -f k8s/
```

### Helm

```bash
# Deploy
make helm-deploy

# Check status
make helm-status

# Upgrade
helm upgrade parallelizer ./helm/parallelizer

# Rollback
helm rollback parallelizer

# Uninstall
helm uninstall parallelizer
```

## Services & Ports

| Service    | Port  | Purpose           | URL              |
|-----------|-------|-------------------|------------------|
| Parallelizer API | 8000  | Main service      | http://localhost:8000 |
| Metrics   | 9090  | Prometheus metrics | http://localhost:9090/metrics |
| Prometheus | 9091  | Metrics database  | http://localhost:9091 |
| Grafana   | 3000  | Dashboard         | http://localhost:3000 |
| Redis     | 6379  | Cache             | localhost:6379 |

## Health Checks

```bash
# Liveness
curl http://localhost:8000/health

# Readiness
curl http://localhost:8000/ready

# Startup
curl http://localhost:8000/startup
```

## Configuration

### Environment Variables

```bash
PARALLELIZER_ENV=production
PARALLELIZER_LOG_LEVEL=INFO
REDIS_URL=redis://redis:6379/0
API_TOKEN=your-token-here
```

See `.env.example` for all available options.

### Secrets Management

Update before production in `k8s/secrets.yaml`:
- `redis_url` — Redis connection
- `api_token` — Authentication token
- `db_password` — Database password
- `aws_*` — AWS credentials

## Monitoring

### Prometheus

Query key metrics:
```
parallelizer_tasks_total
parallelizer_tasks_duration_seconds
parallelizer_errors_total
parallelizer_cache_hits_total
```

### Grafana

Access at: http://localhost:3000
Default login: admin/admin

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Health check failing
```bash
kubectl port-forward pod/<pod-name> 8000:8000
curl http://localhost:8000/health
```

### Scale up
```bash
kubectl scale deployment parallelizer-api --replicas=5
```

### View logs
```bash
# Docker Compose
docker-compose logs -f parallelizer

# Kubernetes
kubectl logs -f <pod-name>

# All pods
kubectl logs -f -l app=parallelizer
```

## Production Checklist

Before deploying to production:

- [ ] Update secrets in k8s/secrets.yaml
- [ ] Set appropriate resource limits
- [ ] Enable TLS in ingress
- [ ] Configure monitoring alerts
- [ ] Test failover/recovery
- [ ] Set up log aggregation
- [ ] Document runbooks
- [ ] Run load tests

## Key Files & What They Do

| File | Purpose |
|------|---------|
| Dockerfile | Multi-stage production image with security hardening |
| docker-compose.yml | Local dev: API, Redis, Prometheus, Grafana |
| k8s/deployment.yaml | 3-replica deployment with health checks |
| k8s/service.yaml | ClusterIP, LoadBalancer, headless services |
| k8s/configmap.yaml | App config, Prometheus config, health checks |
| k8s/secrets.yaml | Database, Redis, API tokens, AWS creds |
| k8s/rbac.yaml | ServiceAccount, Role, RoleBinding, NetworkPolicy |
| k8s/ingress.yaml | HTTP ingress, autoscaling, pod disruption budgets |
| helm/parallelizer/values.yaml | 70+ configurable parameters |
| .github/workflows/docker-build.yml | Build, push, scan Docker image |
| .github/workflows/deploy-k8s.yml | Deploy to K8s, rollback on failure |

## Performance Guidelines

- **CPU requests**: 250m per pod, 1000m limit
- **Memory requests**: 512Mi per pod, 2Gi limit
- **Min replicas**: 2 (production: 3+)
- **Max replicas**: 10 (adjust per workload)
- **Target CPU**: 70% utilization
- **Target memory**: 80% utilization

## Security Notes

- Non-root user (UID 1000)
- Read-only root filesystem
- Capability drop (NET_BIND_SERVICE only)
- Network policies enabled
- RBAC enforced
- Secrets externalized
- TLS/SSL ready
- Health probes configured

## Recovery

### Rollback Docker
```bash
docker rollback <container-id>
```

### Rollback Kubernetes
```bash
kubectl rollout undo deployment/parallelizer-api
```

### Rollback Helm
```bash
helm rollback parallelizer
```

## Need Help?

- Full guide: See `docs/DEPLOYMENT.md`
- Scripts: Check `scripts/` with `--help` flags
- Examples: See `docker-compose.yml` and `k8s/`
- Config: See `k8s/configmap.yaml` for full config
