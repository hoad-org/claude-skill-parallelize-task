# Phase 6: Production Deployment & Operations Guide

Complete guide for running Parallelize-Task in production environments.

## Table of Contents
1. [Production Deployment Checklist](#production-deployment-checklist)
2. [Performance Tuning](#performance-tuning)
3. [Security Hardening](#security-hardening)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Backup & Disaster Recovery](#backup--disaster-recovery)
6. [Troubleshooting Guide](#troubleshooting-guide)

---

## Production Deployment Checklist

### Infrastructure Requirements

- [ ] **Compute**: Min 3 nodes, 4GB RAM each, 2 vCPU
- [ ] **Storage**: 10GB persistent volume, SSD preferred
- [ ] **Database**: Redis 7.0+ with replication
- [ ] **Network**: Load balancer, TLS certificates
- [ ] **Monitoring**: Prometheus + Grafana stack
- [ ] **Logging**: Centralized log aggregation

### Application Configuration

- [ ] Environment set to `production`
- [ ] Log level set to `WARNING`
- [ ] All secrets configured via environment variables
- [ ] Database connections pooled
- [ ] Cache enabled and configured
- [ ] Rate limiting enabled
- [ ] Request timeout configured (30s API, 60s WebSocket)

### Kubernetes Cluster

- [ ] **Namespace**: `parallelize-task` created
- [ ] **RBAC**: Service accounts configured
- [ ] **Network Policies**: Ingress/egress rules configured
- [ ] **Pod Security**: Non-root users enforced
- [ ] **Resource Quotas**: Set per namespace
- [ ] **Ingress Controller**: Nginx with TLS

### Secrets Management

- [ ] Redis password (minimum 32 characters)
- [ ] TLS certificates (Let's Encrypt recommended)
- [ ] Database credentials
- [ ] API keys (if applicable)
- [ ] All stored in Kubernetes Secrets or external vault

### Health & Monitoring

- [ ] Health checks: liveness, readiness, startup
- [ ] Prometheus scrape targets configured
- [ ] Grafana dashboards deployed
- [ ] Alert rules created for critical metrics
- [ ] Log aggregation configured
- [ ] Distributed tracing (optional)

### Backup & Disaster Recovery

- [ ] Database backup schedule configured (daily)
- [ ] Backup retention: 30 days minimum
- [ ] Disaster recovery plan documented
- [ ] RTO/RPO targets defined
- [ ] Backup restoration tested
- [ ] Off-site backup replication

### Security Audit

- [ ] TLS 1.2+ enforced
- [ ] Certificate pinning enabled (optional)
- [ ] CORS properly configured
- [ ] CSRF protection enabled
- [ ] Input validation enforced
- [ ] SQL injection prevention verified
- [ ] Vulnerability scanning passed
- [ ] Security headers configured

---

## Performance Tuning

### Database (Redis) Tuning

```bash
# Redis configuration
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
appendonly yes
appendfsync everysec

# Monitor Redis performance
redis-cli INFO stats
redis-cli LATENCY LATEST
redis-cli SLOWLOG GET 10
```

### Application Tuning

```python
# In config or environment
CACHE_TTL = 3600           # 1 hour cache
MAX_WORKERS = 10           # Parallel workers
CONNECTION_POOL_SIZE = 20  # Database connections
REQUEST_TIMEOUT = 30       # 30 second timeout
BATCH_SIZE = 1000          # Processing batches
```

### Kubernetes Resource Optimization

**Requests** (guaranteed minimum):
```yaml
requests:
  memory: "512Mi"    # Per pod
  cpu: "500m"        # Per pod
```

**Limits** (hard maximum):
```yaml
limits:
  memory: "1Gi"      # Max memory
  cpu: "1000m"       # Max CPU
```

**Auto-scaling**:
```bash
# Scale up when CPU > 70% or Memory > 80%
# Scale down when CPU < 50% and Memory < 60%
kubectl autoscale deployment parallelize-api \
  --min=5 --max=20 \
  --cpu-percent=70 \
  -n parallelize-task
```

### Load Balancing

**Sticky Sessions** (if stateful):
```nginx
upstream backend {
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
    
    # Sticky sessions for WebSocket
    ip_hash;
}
```

**Connection Pooling**:
```python
# Redis pool with 20 connections
redis_pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    db=0,
    max_connections=20
)
```

---

## Security Hardening

### TLS/SSL Configuration

```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    # TLS 1.2+
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Certificate
    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

### Input Validation

```python
from pydantic import BaseModel, validator

class WorkflowCreate(BaseModel):
    name: str
    description: str
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or len(v) > 255:
            raise ValueError('Invalid name')
        return v
    
    @validator('description')
    def description_length(cls, v):
        if len(v) > 1000:
            raise ValueError('Description too long')
        return v
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/workflows")
@limiter.limit("100/minute")
async def create_workflow(request: Request, workflow: WorkflowCreate):
    # Endpoint limited to 100 requests per minute
    pass
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: parallelize-security
  namespace: parallelize-task
spec:
  podSelector:
    matchLabels:
      app: parallelize-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
```

---

## Monitoring & Alerting

### Prometheus Metrics

```yaml
# Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: parallelize-api
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Key Metrics to Monitor

**Application Metrics**:
```
parallelize_workflows_total          # Total workflows
parallelize_tasks_completed_total     # Completed tasks
parallelize_execution_duration_ms     # Execution time
parallelize_efficiency_gain_percent   # Optimization gain
parallelize_cache_hits_total          # Cache hit count
parallelize_cache_misses_total        # Cache misses
parallelize_errors_total              # Error count
```

**System Metrics**:
```
node_cpu_usage_percent                # CPU usage
node_memory_usage_bytes               # Memory usage
node_disk_free_bytes                  # Disk space
node_network_io_bytes                 # Network I/O
```

### Alert Rules

```yaml
# alert.rules.yaml
groups:
  - name: parallelize
    rules:
    - alert: HighErrorRate
      expr: rate(parallelize_errors_total[5m]) > 0.05
      for: 5m
      annotations:
        summary: "High error rate detected"
    
    - alert: HighMemoryUsage
      expr: node_memory_usage_bytes / node_memory_total > 0.9
      for: 5m
      annotations:
        summary: "Memory usage above 90%"
    
    - alert: APILatencyHigh
      expr: histogram_quantile(0.95, parallelize_api_latency_ms) > 1000
      for: 5m
      annotations:
        summary: "API latency above 1 second"
    
    - alert: PodRestartingFrequently
      expr: rate(kube_pod_container_status_restarts_total[15m]) > 0.1
      annotations:
        summary: "Pod restarting frequently"
```

### Grafana Dashboards

**Dashboard JSON**:
```json
{
  "dashboard": {
    "title": "Parallelize-Task Production",
    "panels": [
      {
        "title": "Workflow Execution Rate",
        "targets": [
          {"expr": "rate(parallelize_workflows_total[5m])"}
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {"expr": "rate(parallelize_errors_total[5m])"}
        ]
      },
      {
        "title": "Resource Usage",
        "targets": [
          {"expr": "node_cpu_usage_percent"},
          {"expr": "node_memory_usage_bytes"}
        ]
      }
    ]
  }
}
```

---

## Backup & Disaster Recovery

### Database Backup

```bash
# Automated daily backup
0 2 * * * /scripts/backup-redis.sh

# Backup script
#!/bin/bash
BACKUP_DIR="/backups/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
kubectl exec -n parallelize-task redis-0 -- \
  redis-cli BGSAVE

# Copy to persistent storage
kubectl cp parallelize-task/redis-0:/data/dump.rdb \
  "$BACKUP_DIR/dump-$TIMESTAMP.rdb"

# Upload to cloud storage
aws s3 cp "$BACKUP_DIR/dump-$TIMESTAMP.rdb" \
  s3://backups/parallelize-redis/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -type f -mtime +30 -delete
```

### Configuration Backup

```bash
# Export all Kubernetes resources
kubectl get all -n parallelize-task -o yaml > \
  backup-$(date +%Y%m%d_%H%M%S).yaml

# Store in git (for IaC)
git add backup.yaml
git commit -m "Backup: $(date)"
```

### Disaster Recovery Procedure

**RTO: 15 minutes | RPO: 1 hour**

1. **Assess Damage** (5 min)
   - Identify what data is lost
   - Check backup integrity

2. **Provision Infrastructure** (5 min)
   - Create new Kubernetes cluster
   - Create persistent volumes

3. **Restore Data** (3 min)
   - Restore Redis from latest backup
   - Verify data integrity

4. **Deploy Application** (2 min)
   - Deploy latest image
   - Verify health checks

5. **Verify & Test** (varies)
   - Run integration tests
   - Verify all endpoints
   - Update DNS

### Backup Restoration Test

```bash
#!/bin/bash

# Monthly backup restoration drill
echo "Testing backup restoration..."

# 1. Create temporary namespace
kubectl create namespace restore-test

# 2. Deploy test Redis
helm install redis-test bitnami/redis \
  -n restore-test

# 3. Restore backup
kubectl cp backups/redis-latest.rdb \
  restore-test/redis-0:/data/dump.rdb

kubectl exec restore-test/redis-0 -- \
  redis-cli SHUTDOWN

# 4. Start Redis and verify
kubectl restart pod -n restore-test redis-0

sleep 30

# 5. Verify data
kubectl exec restore-test/redis-0 -- \
  redis-cli DBSIZE

# 6. Cleanup
kubectl delete namespace restore-test

echo "Restoration test completed successfully"
```

---

## Troubleshooting Guide

### Pod CrashLoopBackOff

```bash
# Check pod logs
kubectl logs pod/parallelize-api-0 -n parallelize-task

# Check events
kubectl describe pod parallelize-api-0 -n parallelize-task

# Check resource limits
kubectl get pod parallelize-api-0 -o yaml | grep -A 10 "resources:"

# Temporary fix: increase memory limit
kubectl set resources deployment parallelize-api \
  -n parallelize-task \
  --limits=memory=1Gi --requests=memory=512Mi
```

### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n parallelize-task

# Check for memory leaks
kubectl logs deployment/parallelize-api -n parallelize-task | \
  grep -i "memory\|leak"

# Restart pods
kubectl rollout restart deployment/parallelize-api \
  -n parallelize-task

# Scale up if needed
kubectl scale deployment parallelize-api \
  --replicas=10 \
  -n parallelize-task
```

### Slow Queries

```bash
# Monitor slow queries
redis-cli SLOWLOG GET 10

# Analyze Prometheus metrics
curl -s http://prometheus:9090/api/v1/query?query=\
histogram_quantile\(0.95,parallelize_query_duration_ms\)

# Enable query caching
# Increase CACHE_TTL environment variable
```

### Network Connectivity Issues

```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup api-service.parallelize-task.svc.cluster.local

# Test connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://api-service:8000/health

# Check network policies
kubectl get networkpolicy -n parallelize-task

# Test external connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- https://www.google.com
```

### Database Connection Issues

```bash
# Check Redis status
kubectl exec redis-0 -n parallelize-task -- redis-cli ping

# Monitor connections
kubectl exec redis-0 -n parallelize-task -- \
  redis-cli INFO stats | grep "connected_clients"

# Increase connection pool
# In config: CONNECTION_POOL_SIZE = 50

# Monitor connection timing
kubectl logs deployment/parallelize-api -n parallelize-task | \
  grep -i "connection\|timeout"
```

---

## Production Readiness Checklist

- [ ] Monitoring and alerting configured
- [ ] Backup and restore procedures tested
- [ ] Disaster recovery plan documented
- [ ] Security audit completed
- [ ] Load testing passed
- [ ] Capacity planning completed
- [ ] Runbooks created for common issues
- [ ] On-call rotation established
- [ ] Incident response plan documented
- [ ] Communication plan for outages
- [ ] Performance baselines established
- [ ] SLA targets defined

---

## Summary

Phase 6 production guide provides:
- Complete deployment checklist
- Performance tuning guidelines
- Security hardening procedures
- Comprehensive monitoring and alerting
- Backup and disaster recovery processes
- Detailed troubleshooting guide
- Production readiness verification
