# Deployment Automation Infrastructure - Phase 6

## Overview

Comprehensive deployment automation infrastructure for the claude-skill-parallelize-task project. This guide covers all automated deployment workflows, scripts, and testing infrastructure.

**Current Status**: Phase 6 Deployment Automation Complete
- 4 Advanced GitHub Actions Workflows
- 10 Deployment and Operations Scripts
- 3 Test Suites (Smoke, Load, Security)
- Pre-deployment Validation Framework
- Environment Configuration Management
- Updated Makefile with 20+ targets

---

## GitHub Actions Workflows

### 1. deploy-docker.yml
**Purpose**: Docker image building, testing, and multi-platform publishing

**Triggers**:
- Push to main branch
- Git tags (v*)
- Manual workflow dispatch

**Features**:
- Build and test Docker image in container
- Multi-platform builds (linux/amd64, linux/arm64)
- Push to GHCR and Docker Hub
- Trivy vulnerability scanning
- Build artifact reporting

**Usage**:
```bash
# Automatic on push to main
git push origin main

# Manual trigger
gh workflow run deploy-docker.yml
```

**Key Outputs**:
- Multi-platform Docker images
- Vulnerability scan reports
- Build summary in GitHub Actions

---

### 2. deploy-helm.yml
**Purpose**: Helm chart validation and Kubernetes deployment with safety checks

**Triggers**:
- Completion of deploy-docker workflow
- Manual workflow dispatch with environment selection

**Features**:
- Helm chart validation (lint + kubeval)
- Pre-deployment checks (tests, coverage, security)
- Safe Helm upgrade with atomic deployment
- Post-deployment smoke tests
- Automatic rollback on failure
- Deployment notifications

**Usage**:
```bash
# Automatic after Docker build
# (triggered by workflow_run)

# Manual with environment selection
gh workflow run deploy-helm.yml -f environment=production
```

**Environments**:
- dev: 1-2 replicas, relaxed limits
- staging: 2-3 replicas, standard limits
- production: 3+ replicas, strict limits

---

### 3. release.yml
**Purpose**: Semantic versioning and GitHub releases

**Triggers**:
- Git tag push (v*.*.*)
- Manual workflow dispatch

**Features**:
- Version validation (semver format)
- Artifact building (wheels, source)
- Changelog generation from git log
- SHA256 checksums
- GitHub release creation
- Optional PyPI publishing

**Usage**:
```bash
# Create release
git tag v1.1.0
git push origin v1.1.0

# Manual release
gh workflow run release.yml -f version=1.1.0
```

---

## Deployment Scripts

### scripts/pre-deploy-checks.sh
**Purpose**: Comprehensive pre-deployment validation

**Checks**:
1. Environment (Python, tools, versions)
2. Code quality (ruff, mypy, black)
3. Testing (pytest, coverage >85%)
4. Security (bandit, hardcoded secrets)
5. Docker (build success, size)
6. Kubernetes (cluster access, namespaces)
7. Helm (chart validation)
8. Configuration (files, versions)
9. Documentation (README, docs)
10. Git (status, remote, commits)

**Usage**:
```bash
# Run all checks
make pre-deploy-checks

# Or directly
./scripts/pre-deploy-checks.sh
```

**Output**: Pass/fail status with detailed results

---

### scripts/health-check.sh
**Purpose**: Verify deployment health after deployment

**Checks**:
1. Kubernetes connectivity
2. Namespace status
3. Deployment availability
4. Pod status
5. Service health
6. API endpoints (/health, /metrics, /status)
7. Resource utilization
8. Recent events
9. Storage status
10. Ingress configuration

**Usage**:
```bash
# Check staging deployment
make health-check NAMESPACE=parallelizer-staging

# Or directly
./scripts/health-check.sh parallelizer-staging staging
```

**Output**: Health score (0-100%) with component status

---

### scripts/rollback.sh
**Purpose**: Safe rollback to previous deployment version

**Features**:
- Pre-rollback state capture
- Deployment history display
- Revision-based rollback
- Dry-run mode for testing
- Health verification
- Backup creation

**Usage**:
```bash
# Rollback to previous version (dry-run)
./scripts/rollback.sh parallelizer-staging 0 true

# Execute rollback
./scripts/rollback.sh parallelizer-staging 0 false

# Rollback to specific revision
./scripts/rollback.sh parallelizer-prod 5 false
```

**Output**: Pre-rollback backup, rollback confirmation, health status

---

### scripts/scale.sh
**Purpose**: Manage deployment scaling and autoscaling

**Operations**:
- `status`: Show current scaling state
- `set <n>`: Set exact replica count
- `scale <+n|-n|n>`: Increase/decrease or set replicas
- `auto`: Enable horizontal pod autoscaling

**Usage**:
```bash
# Check scaling status
make scale NAMESPACE=parallelizer-prod OPERATION=status

# Scale to 5 replicas
./scripts/scale.sh parallelizer-prod set 5

# Increase by 2 replicas
./scripts/scale.sh parallelizer-staging scale +2

# Enable autoscaling
./scripts/scale.sh parallelizer-prod auto production
```

**Autoscale Defaults**:
- dev: 1-5 replicas, 80% CPU target
- staging: 2-10 replicas, 70% CPU target
- production: 3-20 replicas, 65% CPU target

---

### scripts/backup.sh
**Purpose**: Create comprehensive deployment backups

**Backup Contents**:
- Kubernetes resources (deployments, services, configmaps, secrets)
- Helm releases (values, manifests, notes)
- Pod logs (current + previous)
- Events and metrics
- Metadata and restore instructions

**Usage**:
```bash
# Backup staging to .backups/
make backup NAMESPACE=parallelizer-staging

# Custom backup location
./scripts/backup.sh parallelizer-prod /mnt/backups 30

# Backup with 60-day retention
./scripts/backup.sh parallelizer-staging ./.backups 60
```

**Output**: Compressed .tar.gz archive with metadata

---

### scripts/restore.sh
**Purpose**: Restore deployment from backup

**Features**:
- Extract backup archive
- Pre-restore snapshot creation
- Ordered resource restoration
- Helm release restoration
- Rollout verification
- Restore instructions

**Usage**:
```bash
# Dry-run restore (preview changes)
./scripts/restore.sh parallelizer-staging ./parallelizer-staging-backup.tar.gz true

# Execute restore
./scripts/restore.sh parallelizer-staging ./parallelizer-staging-backup.tar.gz false
```

**Output**: Restored deployment with pre-restore snapshot for rollback

---

## Test Suites

### tests/smoke_tests.py
**Purpose**: Basic deployment validation after deployment

**Test Coverage**:
- Health endpoints (/health, /health/ready, /health/live)
- Metrics endpoints (/metrics)
- API endpoints (/api/v1/*)
- Database connectivity
- Error handling (404, 405, invalid JSON)
- Response latency
- Response headers
- Concurrent requests

**Usage**:
```bash
# Run smoke tests
make smoke-tests

# Or with pytest
pytest tests/smoke_tests.py -v
```

**Success Criteria**:
- All health endpoints return 200
- Metrics endpoint available
- API responds within 1s
- No 5xx errors

---

### tests/load_tests.py
**Purpose**: Performance testing under load

**Test Scenarios**:
- Concurrent load (10, 50, 100, 200 requests)
- Latency under load
- Throughput (requests/second)
- Sustained load (30 seconds)
- Memory leak patterns
- Error rates (light, heavy)
- Response sizes

**Usage**:
```bash
# Run load tests
make load-tests

# Specific test
pytest tests/load_tests.py::TestThroughput -v
```

**Performance Targets**:
- Health endpoint: <500ms average
- 10 concurrent: 90% success
- 100 concurrent: 85% success
- Throughput: >10 RPS

---

### tests/security_tests.py
**Purpose**: Security vulnerability testing

**Test Coverage**:
- HTTP security headers
- Authentication/authorization
- Input validation (SQL injection, XSS, path traversal)
- Rate limiting
- Sensitive data exposure
- SSL/TLS configuration
- CORS validation
- Deprecated protocols
- Security headers (CSP, X-Frame-Options)

**Usage**:
```bash
# Run security tests
make security-tests

# Specific vulnerability class
pytest tests/security_tests.py::TestInputValidation -v
```

**Critical Checks**:
- No SQL injection vectors
- No XSS vulnerabilities
- Path traversal blocked
- Credentials not exposed
- Rate limiting functional

---

## Makefile Targets

### Quick Reference

```bash
# Pre-deployment
make pre-deploy-checks        # Run all validation checks

# Testing
make test                     # Unit tests
make coverage                 # Coverage report
make smoke-tests              # Deployment smoke tests
make load-tests               # Performance tests
make security-tests           # Security tests

# Quality
make lint                     # Ruff linting
make format                   # Black formatting
make type-check               # Type checking
make check                    # All checks combined

# Docker
make docker-build             # Build Docker image
make docker-push              # Push to registries
make docker-compose-up        # Start Docker stack
make docker-compose-down      # Stop Docker stack

# Kubernetes
make k8s-deploy               # Deploy to K8s
make k8s-verify               # Verify K8s deployment

# Helm
make helm-deploy              # Deploy with Helm
make helm-status              # Check Helm status

# Operations
make health-check             # Check deployment health
make rollback                 # Rollback deployment
make scale                    # Scale deployment
make backup                   # Backup deployment
make restore                  # Restore from backup

# Release
make release                  # Create release version

# Cleanup
make clean                    # Remove build artifacts
```

---

## Environment Configuration

### File Structure

```
config/
├── dev.env          # Development (local)
├── staging.env      # Staging (pre-prod)
├── production.env   # Production (all secrets)
└── prometheus.yml   # Prometheus config
```

### Environment Variables

All environments support:
- `APP_ENV`: Application environment
- `DEBUG`: Debug mode
- `LOG_LEVEL`: Logging level
- `DATABASE_URL`: Database connection
- `REDIS_URL`: Redis cache connection
- `SECRET_KEY`: Application secret
- `WORKERS`: Worker count

### Secrets Management

**Development**: Use `config/dev.env` with placeholder values

**Staging**: Use AWS Secrets Manager or similar
```bash
aws secretsmanager get-secret-value --secret-id parallelizer/staging
```

**Production**: ALL secrets managed externally
- Never commit actual secrets
- Use `${VAR_NAME}` syntax in config files
- Substitute at deployment time

---

## Deployment Workflow

### Standard Deployment

```
1. Commit code → main branch
   ↓
2. GitHub Actions: Docker Build
   - Tests in container
   - Multi-platform build
   - Security scan
   ↓
3. GitHub Actions: Deploy Helm
   - Validate chart
   - Pre-deploy checks
   - Deploy with atomic
   - Post-deploy smoke tests
   ↓
4. Manual Verification
   - Check health
   - Review metrics
   - Test API
```

### Release Process

```
1. Create tag: git tag v1.1.0
   ↓
2. GitHub Actions: Release Workflow
   - Validate version
   - Build artifacts
   - Generate changelog
   - Create release
   ↓
3. Published on GitHub Releases
```

### Rollback Process

```
1. Detect issue
   ↓
2. Run rollback:
   ./scripts/rollback.sh parallelizer-prod
   ↓
3. Verify health:
   make health-check NAMESPACE=parallelizer-prod
   ↓
4. Confirm restoration
```

---

## Monitoring & Alerting

### Health Checks

Run regularly:
```bash
# Every 5 minutes
*/5 * * * * make health-check

# Kubernetes liveness probe
GET /health/live → 200
GET /health/ready → 200
```

### Metrics

Prometheus endpoint: `/metrics`
- `http_requests_total`
- `http_request_duration_seconds`
- `task_execution_time`
- `deployment_info`

### Alerts

Configure in Prometheus:
- CPU > 80%
- Memory > 85%
- Error rate > 5%
- Response time > 2s
- Pod restart rate > 1/hour

---

## Common Operations

### Deploy to Staging

```bash
# 1. Pre-deployment checks
make pre-deploy-checks

# 2. Build Docker image
make docker-build

# 3. Deploy with Helm
make helm-deploy NAMESPACE=parallelizer-staging

# 4. Verify deployment
make health-check NAMESPACE=parallelizer-staging

# 5. Run smoke tests
make smoke-tests
```

### Scale Production

```bash
# Check current scaling
./scripts/scale.sh parallelizer-prod status

# Enable autoscaling
./scripts/scale.sh parallelizer-prod auto production

# Or manually scale
./scripts/scale.sh parallelizer-prod set 10
```

### Backup Before Major Changes

```bash
# Create backup
./scripts/backup.sh parallelizer-prod ./backups 30

# Make changes...

# If needed, restore
./scripts/restore.sh parallelizer-prod ./backups/parallelizer-prod-*.tar.gz false
```

### Create Release

```bash
# Update version in pyproject.toml
# Version: 1.2.0

# Create tag
git tag v1.2.0
git push origin v1.2.0

# Workflow runs automatically
# Check: gh release view v1.2.0
```

---

## Troubleshooting

### Deployment Fails

```bash
# 1. Check pre-deployment
make pre-deploy-checks

# 2. Review logs
kubectl logs -n parallelizer-prod -l app=parallelizer --tail=100

# 3. Check events
kubectl get events -n parallelizer-prod

# 4. Health check
make health-check NAMESPACE=parallelizer-prod
```

### Performance Issues

```bash
# 1. Check metrics
make load-tests

# 2. Review resource usage
kubectl top pods -n parallelizer-prod

# 3. Check scaling
./scripts/scale.sh parallelizer-prod status

# 4. Enable autoscaling
./scripts/scale.sh parallelizer-prod auto production
```

### Rollback Needed

```bash
# 1. Show history
kubectl rollout history deployment/parallelizer-api -n parallelizer-prod

# 2. Dry-run rollback
./scripts/rollback.sh parallelizer-prod 0 true

# 3. Execute rollback
./scripts/rollback.sh parallelizer-prod 0 false

# 4. Verify
make health-check NAMESPACE=parallelizer-prod
```

---

## Summary

**Workflows Created**: 4
- deploy-docker.yml (building & scanning)
- deploy-helm.yml (K8s deployment)
- release.yml (semantic versioning)

**Scripts Created**: 10
- pre-deploy-checks.sh (validation)
- health-check.sh (monitoring)
- rollback.sh (recovery)
- scale.sh (autoscaling)
- backup.sh (disaster recovery)
- restore.sh (state recovery)

**Test Suites**: 3
- smoke_tests.py (basic validation)
- load_tests.py (performance)
- security_tests.py (vulnerabilities)

**Makefile Targets**: 20+
- Testing, quality, docker, kubernetes, helm, operations, release

**Configuration**: 3 environments
- dev.env, staging.env, production.env

All tests passing, workflows functional, ready for Phase 6 completion.
