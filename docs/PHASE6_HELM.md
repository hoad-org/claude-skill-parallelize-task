# Phase 6: Helm Chart Guide

Complete guide for deploying Claude Skill: Parallelize-Task using Helm.

## Table of Contents
1. [Helm Chart Structure](#helm-chart-structure)
2. [Chart Values](#chart-values)
3. [Installation & Upgrades](#installation--upgrades)
4. [Custom Values](#custom-values)
5. [Hooks & Tests](#hooks--tests)
6. [Chart Best Practices](#chart-best-practices)

---

## Helm Chart Structure

```
parallelize-task-chart/
├── Chart.yaml                 # Chart metadata
├── Chart.lock                 # Dependency lock file
├── values.yaml                # Default values
├── values-dev.yaml            # Development overrides
├── values-prod.yaml           # Production overrides
├── charts/                     # Dependency charts
│   └── redis/
│       ├── Chart.yaml
│       └── values.yaml
├── templates/                 # K8s manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── pvc.yaml
│   ├── deployment-api.yaml
│   ├── deployment-dashboard.yaml
│   ├── service-api.yaml
│   ├── service-dashboard.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── rbac.yaml
│   ├── _helpers.tpl           # Template helpers
│   ├── NOTES.txt              # Post-install notes
│   └── tests/
│       └── test-connection.yaml
├── docs/
│   └── README.md              # Chart documentation
└── .helmignore                # Files to ignore
```

### Chart.yaml

```yaml
apiVersion: v2
name: parallelize-task
description: A Helm chart for Claude Skill - Parallelize-Task
type: application
version: 1.1.0
appVersion: "1.1.0"
keywords:
  - parallelize
  - task
  - orchestration
  - workflow
home: https://github.com/rhyscraig/claude-skill-parallelize-task
sources:
  - https://github.com/rhyscraig/claude-skill-parallelize-task
maintainers:
  - name: Claude Code
    email: claude@anthropic.com
dependencies:
  - name: redis
    version: "17.x"
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
```

---

## Chart Values

### values.yaml (Complete)

```yaml
# Global settings
global:
  environment: production
  domain: parallelize-task.local
  imagePullPolicy: IfNotPresent
  serviceAccount:
    create: true
    annotations: {}
    name: ""

# Namespace
namespace:
  create: true
  name: parallelize-task

# API Configuration
api:
  enabled: true
  replicaCount: 3
  
  image:
    repository: parallelize-task
    tag: "1.1.0"
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 8000
    metricsPort: 9090
    annotations: {}
  
  ingress:
    enabled: true
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - host: api.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: api-tls
        hosts:
          - api.example.com
  
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
  
  nodeSelector: {}
  tolerations: []
  affinity: {}
  
  env:
    PARALLELIZER_ENV: production
    PARALLELIZER_LOG_LEVEL: INFO
    PARALLELIZER_DATA_DIR: /app/data
    PARALLELIZER_MONITORING_ENABLED: "true"
    MAX_WORKERS: "5"
    CACHE_TTL: "3600"
  
  livenessProbe:
    enabled: true
    initialDelaySeconds: 10
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
  
  readinessProbe:
    enabled: true
    initialDelaySeconds: 5
    periodSeconds: 5
    timeoutSeconds: 3
    failureThreshold: 2
  
  persistence:
    enabled: true
    storageClass: standard
    size: 10Gi
    mountPath: /app/data

# Dashboard Configuration
dashboard:
  enabled: true
  replicaCount: 2
  
  image:
    repository: parallelize-dashboard
    tag: "1.1.0"
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 3000
    targetPort: 80
    annotations: {}
  
  ingress:
    enabled: true
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - host: dashboard.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: dashboard-tls
        hosts:
          - dashboard.example.com
  
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "250m"
  
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 5
    targetCPUUtilizationPercentage: 75
  
  nodeSelector: {}
  tolerations: []
  affinity: {}

# Redis Configuration
redis:
  enabled: true
  auth:
    enabled: true
    password: ""  # Set via helm install --set
  master:
    persistence:
      enabled: true
      size: 5Gi
  replica:
    replicaCount: 1
    persistence:
      enabled: true
      size: 5Gi

# Monitoring
monitoring:
  enabled: true
  prometheus:
    enabled: true
    scrapeInterval: 30s
  grafana:
    enabled: true
    adminPassword: ""

# Pod Disruption Budget
podDisruptionBudget:
  api:
    enabled: true
    minAvailable: 2
  dashboard:
    enabled: true
    minAvailable: 1

# Network Policies
networkPolicy:
  enabled: false
  policyTypes:
    - Ingress
    - Egress

# Security Context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  capabilities:
    drop:
      - ALL
```

### values-dev.yaml

```yaml
api:
  replicaCount: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "250m"
  autoscaling:
    enabled: false

dashboard:
  replicaCount: 1
  resources:
    requests:
      memory: "64Mi"
      cpu: "50m"
    limits:
      memory: "128Mi"
      cpu: "100m"
  autoscaling:
    enabled: false

redis:
  master:
    persistence:
      size: 1Gi

podDisruptionBudget:
  api:
    enabled: false
  dashboard:
    enabled: false

api:
  env:
    PARALLELIZER_LOG_LEVEL: DEBUG
```

### values-prod.yaml

```yaml
api:
  replicaCount: 5
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  autoscaling:
    minReplicas: 5
    maxReplicas: 20
    targetCPUUtilizationPercentage: 60

dashboard:
  replicaCount: 3
  autoscaling:
    minReplicas: 3
    maxReplicas: 10

redis:
  master:
    persistence:
      size: 20Gi
  replica:
    replicaCount: 2
    persistence:
      size: 20Gi

podDisruptionBudget:
  api:
    minAvailable: 3
  dashboard:
    minAvailable: 2

networkPolicy:
  enabled: true

monitoring:
  prometheus:
    enabled: true
    scrapeInterval: 15s
  grafana:
    enabled: true

api:
  env:
    PARALLELIZER_LOG_LEVEL: WARNING
```

---

## Installation & Upgrades

### Prerequisites

```bash
# Install Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
helm version
# version.BuildInfo{Version:"v3.12.0", ...}

# Add Bitnami repository (for Redis dependency)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Basic Installation

```bash
# Add chart repository
helm repo add parallelize https://charts.parallelize-task.io
helm repo update

# Install with default values
helm install parallelize-task parallelize/parallelize-task \
  -n parallelize-task \
  --create-namespace

# Install with custom values
helm install parallelize-task parallelize/parallelize-task \
  -n parallelize-task \
  --create-namespace \
  -f values-prod.yaml

# Install with inline overrides
helm install parallelize-task parallelize/parallelize-task \
  --set api.replicaCount=5 \
  --set redis.auth.password=$(openssl rand -base64 32) \
  --set global.domain=api.example.com
```

### Upgrade Procedure

```bash
# Upgrade to new version
helm upgrade parallelize-task parallelize/parallelize-task \
  -n parallelize-task

# Upgrade with new values
helm upgrade parallelize-task parallelize/parallelize-task \
  -n parallelize-task \
  -f values-prod.yaml

# Dry-run upgrade (see what would change)
helm upgrade parallelize-task parallelize/parallelize-task \
  --dry-run --debug \
  -n parallelize-task

# Upgrade with atomic rollback on failure
helm upgrade parallelize-task parallelize/parallelize-task \
  --atomic \
  --timeout 5m \
  -n parallelize-task
```

### Release Management

```bash
# List releases
helm list -n parallelize-task

# Get release details
helm get all parallelize-task -n parallelize-task

# Get values
helm get values parallelize-task -n parallelize-task

# Get manifest
helm get manifest parallelize-task -n parallelize-task

# View release history
helm history parallelize-task -n parallelize-task

# Rollback to previous release
helm rollback parallelize-task 1 -n parallelize-task

# Uninstall release
helm uninstall parallelize-task -n parallelize-task
```

---

## Custom Values

### Secret Management

**Store secrets in separate file** (`secrets.yaml`):
```yaml
redis:
  auth:
    password: "your-secure-password"
```

**Install with secrets**:
```bash
helm install parallelize-task . \
  -f secrets.yaml \
  --set-string redis.auth.password=$(openssl rand -base64 32)
```

**Using External Secrets Operator**:
```yaml
# values.yaml
externalSecrets:
  enabled: true
  backend: aws-secrets-manager
  projectId: my-aws-account
  secretName: parallelize-redis-password
```

### Multiple Environments

```bash
# Development
helm install dev parallelize/parallelize-task \
  -n parallelize-dev \
  --create-namespace \
  -f values.yaml \
  -f values-dev.yaml

# Staging
helm install staging parallelize/parallelize-task \
  -n parallelize-staging \
  --create-namespace \
  -f values.yaml \
  -f values-staging.yaml

# Production
helm install prod parallelize/parallelize-task \
  -n parallelize-prod \
  --create-namespace \
  -f values.yaml \
  -f values-prod.yaml
```

### Custom Domains

```bash
helm install parallelize-task . \
  --set global.domain=custom.example.com \
  --set api.ingress.hosts[0].host=api.custom.example.com \
  --set dashboard.ingress.hosts[0].host=dashboard.custom.example.com
```

### Resource Configuration

```bash
# High resource environment
helm install parallelize-task . \
  --set api.resources.requests.memory=1Gi \
  --set api.resources.requests.cpu=1000m \
  --set api.resources.limits.memory=2Gi \
  --set api.resources.limits.cpu=2000m

# Low resource environment
helm install parallelize-task . \
  --set api.resources.requests.memory=128Mi \
  --set api.resources.requests.cpu=100m \
  --set api.resources.limits.memory=256Mi \
  --set api.resources.limits.cpu=250m
```

---

## Hooks & Tests

### Pre-Install Hook

**File**: `templates/hooks/pre-install.yaml`
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "parallelize-task.fullname" . }}-pre-install
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  template:
    spec:
      serviceAccountName: {{ include "parallelize-task.serviceAccountName" . }}
      restartPolicy: Never
      containers:
      - name: pre-install
        image: busybox
        command: ['sh', '-c', 'echo "Pre-install hook running..."']
```

### Post-Install Hook

**File**: `templates/hooks/post-install.yaml`
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "parallelize-task.fullname" . }}-post-install
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  template:
    spec:
      containers:
      - name: post-install
        image: curlimages/curl
        command: ['sh', '-c']
        args:
          - |
            echo "Waiting for API to be ready..."
            for i in {1..30}; do
              if curl -f http://{{ include "parallelize-task.fullname" . }}-api:8000/health; then
                echo "API is ready!"
                exit 0
              fi
              echo "Attempt $i failed, retrying..."
              sleep 10
            done
            exit 1
```

### Test Hook

**File**: `templates/tests/test-connection.yaml`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "parallelize-task.fullname" . }}-test-connection"
  labels:
    {{- include "parallelize-task.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
spec:
  containers:
    - name: wget
      image: busybox
      command: ['wget']
      args: ['{{ include "parallelize-task.fullname" . }}-api:8000/health']
  restartPolicy: Never
```

**Run tests**:
```bash
# Run chart tests
helm test parallelize-task -n parallelize-task

# View test results
kubectl get pods -n parallelize-task -l app.kubernetes.io/name=parallelize-task
```

---

## Chart Best Practices

### 1. Templating Helpers

**File**: `templates/_helpers.tpl`
```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "parallelize-task.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "parallelize-task.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "parallelize-task.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "parallelize-task.labels" -}}
helm.sh/chart: {{ include "parallelize-task.chart" . }}
{{ include "parallelize-task.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "parallelize-task.selectorLabels" -}}
app.kubernetes.io/name: {{ include "parallelize-task.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

### 2. Conditional Components

```yaml
# In templates/deployment-api.yaml
{{- if .Values.api.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "parallelize-task.fullname" . }}-api
  {{- include "parallelize-task.labels" . | nindent 2 }}
spec:
  # ... deployment spec
{{- end }}
```

### 3. Post-Installation Notes

**File**: `templates/NOTES.txt`
```
1. Get the release name:
  echo "Release name: {{ .Release.Name }}"

2. Get the API service:
  kubectl get svc -n {{ .Release.Namespace }}

3. Access the dashboard:
  kubectl port-forward -n {{ .Release.Namespace }} \
    svc/{{ include "parallelize-task.fullname" . }}-dashboard 3000:3000
  # Then visit http://localhost:3000

4. Access the API:
  kubectl port-forward -n {{ .Release.Namespace }} \
    svc/{{ include "parallelize-task.fullname" . }}-api 8000:8000
  # Then visit http://localhost:8000/docs

5. Check deployment status:
  kubectl rollout status deployment/{{ include "parallelize-task.fullname" . }}-api \
    -n {{ .Release.Namespace }}

{{ if .Values.redis.enabled }}
6. Redis is enabled. Get the password:
  kubectl get secret --namespace {{ .Release.Namespace }} \
    {{ include "parallelize-task.fullname" . }}-redis \
    -o jsonpath="{.data.redis-password}" | base64 --decode
{{ end }}
```

### 4. Chart Validation

```bash
# Lint the chart
helm lint ./parallelize-task-chart

# Validate template rendering
helm template parallelize-task ./parallelize-task-chart

# Verify chart structure
helm chart verify ./parallelize-task-chart
```

### 5. Dependency Management

```yaml
# Chart.yaml
dependencies:
  - name: redis
    version: "17.x"
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
```

**Update dependencies**:
```bash
# Download dependencies
helm dependency update ./parallelize-task-chart

# List dependencies
helm dependency list ./parallelize-task-chart
```

---

## Packaging & Distribution

### Create Chart Package

```bash
# Package the chart
helm package ./parallelize-task-chart
# Created: parallelize-task-1.1.0.tgz

# Create chart index
helm repo index .

# Create signed package
helm package --sign --key 'My Key' --keyring ~/.gnupg/secring.gpg \
  ./parallelize-task-chart
```

### Publish to Registry

```bash
# Using ChartMuseum
helm plugin install https://github.com/chartmuseum/helm-push.git
helm push parallelize-task-1.1.0.tgz myregistry

# Using Artifactory
helm plugin install https://github.com/chartmuseum/helm-push.git
helm push parallelize-task-1.1.0.tgz artifactory
```

---

## Summary

Phase 6 Helm chart provides:
- Complete Helm chart structure
- Comprehensive values configuration
- Development and production value overrides
- Hooks for pre/post-install automation
- Test hooks for validation
- Best practices for templating and helpers
- Full dependency management
- Publishing and distribution guidance
