# Phase 6: Kubernetes Deployment Guide

Comprehensive guide for deploying Claude Skill: Parallelize-Task on Kubernetes.

## Table of Contents
1. [Kubernetes Architecture](#kubernetes-architecture)
2. [Manifest Files](#manifest-files)
3. [Deployment Strategies](#deployment-strategies)
4. [Scaling & Resource Management](#scaling--resource-management)
5. [Health Checks & Monitoring](#health-checks--monitoring)
6. [Production Considerations](#production-considerations)
7. [Troubleshooting](#troubleshooting)

---

## Kubernetes Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│         Kubernetes Cluster                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────┐    ┌──────────────────┐  │
│  │  API Service     │    │ Dashboard Service│  │
│  │  Port: 8000      │    │ Port: 3000       │  │
│  └────────┬─────────┘    └────────┬─────────┘  │
│           │ (ClusterIP)           │            │
│  ┌────────▼─────────┐    ┌────────▼─────────┐  │
│  │  API Pods (3)    │    │Dashboard Pods(2) │  │
│  │  ├─ parallelize-0│    │├─ dashboard-0    │  │
│  │  ├─ parallelize-1│    │└─ dashboard-1    │  │
│  │  └─ parallelize-2│    │                  │  │
│  └────────┬─────────┘    └──────────────────┘  │
│           │ (shared storage)                   │
│  ┌────────▼──────────────────────────────────┐ │
│  │  Redis StatefulSet (1 replica)            │ │
│  │  ├─ Redis Master                          │ │
│  │  └─ Persistent Volume Claim (10Gi)        │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  ConfigMaps & Secrets                    │  │
│  │  ├─ api-config                           │  │
│  │  ├─ prometheus-config                    │  │
│  │  └─ redis-credentials (Secret)           │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
         │ (Ingress)
         │
    ┌────▼────┐
    │ External│
    │ Traffic │
    └─────────┘
```

### Namespace Structure

```
parallelize-task/
├── api-deployment      (3 replicas)
├── dashboard-deployment (2 replicas)
├── redis-statefulset   (1 replica)
├── services            (ClusterIP)
├── configmaps          (settings)
├── secrets             (credentials)
├── ingress             (external access)
├── hpa                 (autoscaling)
└── pdb                 (disruption budget)
```

---

## Manifest Files

### 1. Namespace

**File**: `k8s/namespace.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: parallelize-task
  labels:
    app: parallelize-task
    version: "1.1.0"
```

### 2. ConfigMap (API Configuration)

**File**: `k8s/configmap-api.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: parallelize-task
data:
  PARALLELIZER_ENV: "production"
  PARALLELIZER_LOG_LEVEL: "INFO"
  PARALLELIZER_DATA_DIR: "/app/data"
  PARALLELIZER_MONITORING_ENABLED: "true"
  PARALLELIZER_METRICS_PORT: "9090"
  REDIS_HOST: "redis-service.parallelize-task.svc.cluster.local"
  REDIS_PORT: "6379"
  REDIS_DB: "0"
  MAX_WORKERS: "5"
  CACHE_TTL: "3600"
```

### 3. Secret (Redis Credentials)

**File**: `k8s/secret-redis.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: redis-credentials
  namespace: parallelize-task
type: Opaque
stringData:
  redis-password: "your-secure-password-here"
  redis-url: "redis://:your-secure-password-here@redis-service:6379/0"
```

**Generate from command line**:
```bash
# Create secret
kubectl create secret generic redis-credentials \
  --from-literal=redis-password=$(openssl rand -base64 32) \
  -n parallelize-task

# Create from existing .env
kubectl create secret generic redis-credentials \
  --from-file=.env \
  -n parallelize-task
```

### 4. Persistent Volume Claim

**File**: `k8s/pvc-data.yaml`
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: parallelize-data-pvc
  namespace: parallelize-task
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

### 5. Redis StatefulSet

**File**: `k8s/redis-statefulset.yaml`
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: parallelize-task
spec:
  serviceName: redis-service
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: redis
        command:
          - redis-server
          - "--appendonly"
          - "yes"
          - "--requirepass"
          - "$(REDIS_PASSWORD)"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: redis-password
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 10
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 5Gi
```

### 6. API Deployment

**File**: `k8s/deployment-api.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: parallelize-api
  namespace: parallelize-task
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: parallelize-api
  template:
    metadata:
      labels:
        app: parallelize-api
        version: "1.1.0"
    spec:
      serviceAccountName: parallelize-api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: api
        image: parallelize-task:1.1.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        envFrom:
        - configMapRef:
            name: api-config
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          capabilities:
            drop:
            - ALL
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: parallelize-data-pvc
      - name: logs
        emptyDir:
          sizeLimit: 1Gi
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - parallelize-api
              topologyKey: kubernetes.io/hostname
```

### 7. Dashboard Deployment

**File**: `k8s/deployment-dashboard.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: parallelize-dashboard
  namespace: parallelize-task
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: parallelize-dashboard
  template:
    metadata:
      labels:
        app: parallelize-dashboard
        version: "1.1.0"
    spec:
      serviceAccountName: parallelize-dashboard
      securityContext:
        runAsNonRoot: true
        runAsUser: 101  # nginx user
        fsGroup: 101
      containers:
      - name: dashboard
        image: parallelize-dashboard:1.1.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 80
          name: http
          protocol: TCP
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

### 8. Services

**File**: `k8s/service-api.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: parallelize-task
  labels:
    app: parallelize-api
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: metrics
  selector:
    app: parallelize-api
```

**File**: `k8s/service-dashboard.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: dashboard-service
  namespace: parallelize-task
  labels:
    app: parallelize-dashboard
spec:
  type: ClusterIP
  ports:
  - port: 3000
    targetPort: 80
    protocol: TCP
    name: http
  selector:
    app: parallelize-dashboard
```

**File**: `k8s/service-redis.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: parallelize-task
spec:
  clusterIP: None  # Headless service for StatefulSet
  ports:
  - port: 6379
    targetPort: 6379
    protocol: TCP
  selector:
    app: redis
```

### 9. Ingress

**File**: `k8s/ingress.yaml`
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: parallelize-ingress
  namespace: parallelize-task
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/websocket-services: "api-service"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    - dashboard.example.com
    secretName: parallelize-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
  - host: dashboard.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dashboard-service
            port:
              number: 3000
```

### 10. Horizontal Pod Autoscaler

**File**: `k8s/hpa.yaml`
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: parallelize-api-hpa
  namespace: parallelize-task
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: parallelize-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

### 11. Pod Disruption Budget

**File**: `k8s/pdb.yaml`
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: parallelize-api-pdb
  namespace: parallelize-task
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: parallelize-api
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: parallelize-dashboard-pdb
  namespace: parallelize-task
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: parallelize-dashboard
```

### 12. RBAC (Role-Based Access Control)

**File**: `k8s/rbac.yaml`
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: parallelize-api
  namespace: parallelize-task
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: parallelize-dashboard
  namespace: parallelize-task
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: parallelize-api
  namespace: parallelize-task
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: parallelize-api
  namespace: parallelize-task
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: parallelize-api
subjects:
- kind: ServiceAccount
  name: parallelize-api
  namespace: parallelize-task
```

---

## Deployment Strategies

### Rolling Update (Default)

**Configuration**:
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # One extra pod during update
      maxUnavailable: 0    # Zero pods down during update
```

**Process**:
```
Replicas: 3, MaxSurge: 1, MaxUnavailable: 0

Step 1: [Old-1] [Old-2] [Old-3]
Step 2: [Old-1] [Old-2] [Old-3] [New-1]  (4 pods total)
Step 3: [Old-1] [Old-2] [New-1] [New-2]  (terminate Old-3)
Step 4: [Old-1] [New-1] [New-2] [New-3]  (terminate Old-2)
Step 5: [New-1] [New-2] [New-3]          (terminate Old-1)
```

**Advantages**:
- Zero downtime
- Easy rollback
- Progressive validation

**Deployment**:
```bash
# Deploy new version
kubectl set image deployment/parallelize-api \
  api=parallelize-task:1.2.0 \
  -n parallelize-task

# Monitor rollout
kubectl rollout status deployment/parallelize-api -n parallelize-task

# Rollback if needed
kubectl rollout undo deployment/parallelize-api -n parallelize-task
```

### Canary Deployment

**Configure with 10% traffic**:
```yaml
# Deployed as a separate deployment with lower replicas
spec:
  replicas: 1  # Canary: 1 of 3 total replicas
  template:
    metadata:
      labels:
        app: parallelize-api
        version: v1.2.0-canary
```

**Monitor with metrics**:
```bash
# Track error rate for canary version
kubectl get pods -n parallelize-task \
  -l app=parallelize-api,version=v1.2.0-canary

# Check metrics via Prometheus
# error_rate{version="v1.2.0-canary"}
```

### Blue-Green Deployment

**Deploy new version alongside current**:
```bash
# Blue deployment (current)
kubectl create deployment parallelize-api-blue \
  --image=parallelize-task:1.1.0 \
  -n parallelize-task

# Green deployment (new)
kubectl create deployment parallelize-api-green \
  --image=parallelize-task:1.2.0 \
  -n parallelize-task

# Switch service to green
kubectl patch service api-service -n parallelize-task \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Delete blue after verification
kubectl delete deployment parallelize-api-blue -n parallelize-task
```

---

## Scaling & Resource Management

### Resource Requests & Limits

```yaml
resources:
  requests:
    memory: "256Mi"  # Guaranteed minimum
    cpu: "250m"      # 1/4 CPU
  limits:
    memory: "512Mi"  # Maximum allowed
    cpu: "500m"      # 1/2 CPU
```

**Resource Classes**:
- **Small**: 256Mi memory, 250m CPU
- **Medium**: 512Mi memory, 500m CPU
- **Large**: 1Gi memory, 1000m CPU

### Horizontal Pod Autoscaling

```bash
# Create HPA
kubectl autoscale deployment parallelize-api \
  --min=3 --max=10 \
  --cpu-percent=70 \
  -n parallelize-task

# Check HPA status
kubectl get hpa -n parallelize-task

# View scaling events
kubectl describe hpa parallelize-api-hpa -n parallelize-task
```

### Vertical Pod Autoscaling

**Install VPA**:
```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh
```

**Configure VPA**:
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: parallelize-vpa
  namespace: parallelize-task
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: parallelize-api
  updatePolicy:
    updateMode: "Auto"  # or "Off", "Initial", "Recreate"
```

### Cluster Scaling

```bash
# Scale cluster nodes (if using cloud provider)
# AWS EKS
aws eks update-nodegroup-config \
  --cluster-name parallelize-cluster \
  --nodegroup-name parallelize-nodes \
  --scaling-config minSize=3,maxSize=10,desiredSize=5

# GKE
gcloud container clusters resize parallelize-cluster --num-nodes=5

# Azure AKS
az aks scale --resource-group parallelize-rg \
  --name parallelize-cluster \
  --node-count 5
```

---

## Health Checks & Monitoring

### Liveness Probe

Determines if pod should be restarted:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10    # Wait 10s before first check
  periodSeconds: 10          # Check every 10s
  timeoutSeconds: 5          # Timeout after 5s
  failureThreshold: 3        # Restart after 3 failures
```

### Readiness Probe

Determines if pod should receive traffic:

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2        # Remove from service after 2 failures
```

### Startup Probe

For slow-starting applications:

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  failureThreshold: 30
  periodSeconds: 10           # 300 seconds total before declaring failure
```

### Prometheus Monitoring

**ServiceMonitor (for Prometheus Operator)**:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: parallelize-api
  namespace: parallelize-task
spec:
  selector:
    matchLabels:
      app: parallelize-api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Logging

**View logs**:
```bash
# Current pod logs
kubectl logs deployment/parallelize-api -n parallelize-task

# Previous pod logs
kubectl logs deployment/parallelize-api --previous -n parallelize-task

# Tail logs
kubectl logs -f deployment/parallelize-api -n parallelize-task

# Multiple containers
kubectl logs deployment/parallelize-api -c api -n parallelize-task
```

---

## Production Considerations

### Security

**Network Policies**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: parallelize-network-policy
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
    - podSelector:
        matchLabels:
          app: parallelize-dashboard
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

**Pod Security Policy** (deprecated, use Pod Security Standards):
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: parallelize-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: MustRunAs
    seLinuxOptions:
      level: "s0:c123,c456"
  fsGroup:
    rule: MustRunAs
```

### Backup & Disaster Recovery

**StatefulSet Backup**:
```bash
# Backup Redis data
kubectl exec redis-0 -n parallelize-task -- \
  redis-cli BGSAVE

# Copy backup file
kubectl cp parallelize-task/redis-0:/data/dump.rdb \
  ./redis-backup-$(date +%Y%m%d).rdb
```

**ConfigMap/Secret Backup**:
```bash
# Export all manifests
kubectl get all -n parallelize-task -o yaml > backup.yaml

# Export secrets (encrypted)
kubectl get secret -n parallelize-task -o yaml > secrets-backup.yaml
```

### Update Procedures

**Update API version**:
```bash
# Update image
kubectl set image deployment/parallelize-api \
  api=parallelize-task:1.2.0 \
  -n parallelize-task

# Monitor rollout
watch kubectl rollout status deployment/parallelize-api -n parallelize-task

# Check events
kubectl describe deployment parallelize-api -n parallelize-task
```

---

## Troubleshooting

### Pod Won't Start

```bash
# Check pod status
kubectl describe pod <pod-name> -n parallelize-task

# Check events
kubectl get events -n parallelize-task --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n parallelize-task
kubectl logs <pod-name> --previous -n parallelize-task
```

### Pod CrashLoopBackOff

```bash
# Check startup probe timeout
kubectl get pod <pod-name> -n parallelize-task -o yaml | grep startup

# Enter pod for debugging
kubectl debug <pod-name> -it -n parallelize-task

# Check resource limits
kubectl describe pod <pod-name> -n parallelize-task | grep -A 5 "Limits"
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints api-service -n parallelize-task

# Test DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup api-service.parallelize-task.svc.cluster.local

# Test connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://api-service:8000/health
```

### Persistent Volume Issues

```bash
# Check PVC status
kubectl get pvc -n parallelize-task

# Describe PVC
kubectl describe pvc parallelize-data-pvc -n parallelize-task

# List PVs
kubectl get pv

# Check available storage
kubectl describe pv <pv-name>
```

---

## Deployment Checklist

- [ ] Cluster prepared and accessible
- [ ] Namespace created
- [ ] Secrets configured
- [ ] ConfigMaps created
- [ ] PVC created and bound
- [ ] Redis StatefulSet deployed
- [ ] API Deployment deployed
- [ ] Dashboard Deployment deployed
- [ ] Services created
- [ ] Ingress configured
- [ ] HPA configured
- [ ] PDB configured
- [ ] Health checks verified
- [ ] Monitoring configured
- [ ] Logging verified
- [ ] Security policies applied
- [ ] Backup procedures tested
- [ ] Load tests passed

## Summary

Phase 6 Kubernetes deployment provides:
- Complete manifest files for all components
- Rolling, canary, and blue-green deployment strategies
- Horizontal and vertical pod autoscaling
- Comprehensive health checking
- Production-ready security and monitoring
- Disaster recovery procedures
- Detailed troubleshooting guide
