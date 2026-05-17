# Phase 6: Deployment Automation Guide

Comprehensive guide for automating deployments using GitHub Actions and deployment scripts.

## Table of Contents
1. [GitHub Actions Workflows](#github-actions-workflows)
2. [Deployment Scripts](#deployment-scripts)
3. [Pre-Deployment Validation](#pre-deployment-validation)
4. [Health Checks & Monitoring](#health-checks--monitoring)
5. [Rollback Procedures](#rollback-procedures)
6. [Load Testing](#load-testing)
7. [Release Management](#release-management)

---

## GitHub Actions Workflows

### CI/CD Pipeline

**File**: `.github/workflows/ci-cd.yml`
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
      
      - name: Lint
        run: ruff check src/ tests/
      
      - name: Type checking
        run: mypy src/ --strict

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha
      
      - name: Build and push backend
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          file: ./docker/Dockerfile.frontend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/dashboard:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/dashboard:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  security-scan:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  deploy-staging:
    needs: [build, security-scan]
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to staging
        run: |
          ./scripts/deploy.sh staging ${{ github.sha }}
      
      - name: Run smoke tests
        run: |
          ./scripts/smoke-tests.sh staging
      
      - name: Notify deployment
        if: success()
        run: |
          echo "Staging deployment successful"

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Create deployment
        uses: actions/github-script@v6
        with:
          script: |
            const deployment = await github.rest.repos.createDeployment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              ref: context.sha,
              environment: 'production',
              auto_merge: false,
              required_contexts: []
            });
      
      - name: Deploy to production
        run: |
          ./scripts/deploy.sh production ${{ github.sha }}
      
      - name: Run health checks
        run: |
          ./scripts/health-check.sh production
      
      - name: Run integration tests
        run: |
          ./scripts/integration-tests.sh production
      
      - name: Create release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release ${{ github.run_number }}
          body: |
            Deployed to production
            Commit: ${{ github.sha }}
            Image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

### Scheduled Deployment

**File**: `.github/workflows/scheduled-deploy.yml`
```yaml
name: Scheduled Deployment Check

on:
  schedule:
    # Run every day at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check production health
        run: |
          curl -f https://api.example.com/health || exit 1
      
      - name: Check API endpoints
        run: |
          ./scripts/endpoint-check.sh
      
      - name: Performance metrics
        run: |
          ./scripts/performance-check.sh
      
      - name: Alert if unhealthy
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Production Health Check Failed',
              body: 'Automated health check detected issues'
            })
```

---

## Deployment Scripts

### deploy.sh

```bash
#!/bin/bash
set -e

ENVIRONMENT=$1
COMMIT_SHA=$2

echo "Deploying to $ENVIRONMENT..."

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validate inputs
if [ -z "$ENVIRONMENT" ] || [ -z "$COMMIT_SHA" ]; then
    echo -e "${RED}Usage: deploy.sh <environment> <commit_sha>${NC}"
    exit 1
fi

# Load environment configuration
source "./scripts/config/${ENVIRONMENT}.env"

# Step 1: Pre-deployment checks
echo -e "${YELLOW}[1/6] Running pre-deployment checks...${NC}"
./scripts/pre-deploy-checks.sh "$ENVIRONMENT"

# Step 2: Pull latest code
echo -e "${YELLOW}[2/6] Pulling latest code...${NC}"
git fetch origin
git checkout "$COMMIT_SHA"

# Step 3: Build and push images
echo -e "${YELLOW}[3/6] Building and pushing Docker images...${NC}"
docker build -t parallelize-task:"$COMMIT_SHA" .
docker push parallelize-task:"$COMMIT_SHA"

# Step 4: Update deployment
echo -e "${YELLOW}[4/6] Updating Kubernetes deployment...${NC}"
if [ "$ENVIRONMENT" = "production" ]; then
    REPLICAS=5
    MAX_REPLICAS=20
else
    REPLICAS=2
    MAX_REPLICAS=5
fi

kubectl set image deployment/parallelize-api \
    api=parallelize-task:"$COMMIT_SHA" \
    -n parallelize-task

kubectl rollout status deployment/parallelize-api \
    -n parallelize-task \
    --timeout=5m

# Step 5: Run smoke tests
echo -e "${YELLOW}[5/6] Running smoke tests...${NC}"
./scripts/smoke-tests.sh "$ENVIRONMENT"

# Step 6: Verification
echo -e "${YELLOW}[6/6] Verifying deployment...${NC}"
./scripts/post-deploy-verify.sh "$ENVIRONMENT"

echo -e "${GREEN}Deployment to $ENVIRONMENT completed successfully!${NC}"
```

### health-check.sh

```bash
#!/bin/bash
set -e

ENVIRONMENT=$1
API_URL="${API_URL:-http://localhost:8000}"
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:3000}"
TIMEOUT=30

echo "Running health checks for $ENVIRONMENT..."

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    
    for i in {1..10}; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✓ OK"
            return 0
        fi
        echo -n "."
        sleep 3
    done
    
    echo "✗ FAILED"
    return 1
}

# Health checks
check_endpoint "$API_URL/health" "API Health"
check_endpoint "$API_URL/health/detailed" "API Detailed Health"
check_endpoint "$API_URL/docs" "API Documentation"
check_endpoint "$DASHBOARD_URL/" "Dashboard"

# Database connectivity check
echo -n "Checking Redis connectivity... "
if kubectl exec -n parallelize-task redis-0 -- redis-cli ping > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    exit 1
fi

# Prometheus check
echo -n "Checking Prometheus metrics... "
if curl -s -f "$API_URL/metrics" > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    exit 1
fi

echo "All health checks passed!"
```

### rollback.sh

```bash
#!/bin/bash
set -e

ENVIRONMENT=$1
REVISION=$2

echo "Rolling back $ENVIRONMENT to revision $REVISION..."

# Get current deployment
DEPLOYMENT=$(kubectl get deployment \
    -n parallelize-task \
    -l app=parallelize-api \
    -o jsonpath='{.items[0].metadata.name}')

if [ -z "$REVISION" ]; then
    # Rollback to previous revision
    kubectl rollout undo deployment/"$DEPLOYMENT" -n parallelize-task
    echo "Rolled back to previous revision"
else
    # Rollback to specific revision
    kubectl rollout undo deployment/"$DEPLOYMENT" \
        --to-revision="$REVISION" \
        -n parallelize-task
    echo "Rolled back to revision $REVISION"
fi

# Wait for rollout to complete
kubectl rollout status deployment/"$DEPLOYMENT" \
    -n parallelize-task \
    --timeout=5m

# Verify health
./scripts/health-check.sh "$ENVIRONMENT"

echo "Rollback completed successfully!"
```

---

## Pre-Deployment Validation

### pre-deploy-checks.sh

```bash
#!/bin/bash
set -e

ENVIRONMENT=$1

echo "Running pre-deployment checks..."

# Check 1: Verify Kubernetes cluster access
echo "✓ Checking Kubernetes cluster access..."
kubectl cluster-info > /dev/null || exit 1

# Check 2: Verify namespace exists
echo "✓ Checking namespace..."
kubectl get namespace parallelize-task > /dev/null || exit 1

# Check 3: Verify persistent volumes
echo "✓ Checking persistent volumes..."
kubectl get pvc -n parallelize-task > /dev/null || exit 1

# Check 4: Verify Redis is healthy
echo "✓ Checking Redis..."
kubectl exec -n parallelize-task redis-0 -- redis-cli ping > /dev/null || exit 1

# Check 5: Verify Prometheus is running
echo "✓ Checking Prometheus..."
kubectl get pod -n parallelize-task -l app=prometheus > /dev/null || exit 1

# Check 6: Verify required secrets
echo "✓ Checking secrets..."
kubectl get secret redis-credentials -n parallelize-task > /dev/null || exit 1

# Check 7: Disk space
echo "✓ Checking disk space..."
AVAILABLE=$(df / | awk 'NR==2 {print $4}')
if [ "$AVAILABLE" -lt 1000000 ]; then
    echo "WARNING: Low disk space (${AVAILABLE}KB available)"
fi

# Check 8: CPU/Memory availability
echo "✓ Checking node resources..."
kubectl top nodes > /dev/null 2>&1 || echo "WARNING: Metrics not available"

echo "All pre-deployment checks passed!"
```

---

## Health Checks & Monitoring

### Integration Test Suite

**File**: `scripts/integration-tests.sh`
```bash
#!/bin/bash
set -e

ENVIRONMENT=$1
API_URL="${API_URL:-http://localhost:8000}"

echo "Running integration tests on $ENVIRONMENT..."

# Test 1: Create workflow
echo "Test 1: Create workflow..."
WORKFLOW=$(curl -s -X POST "$API_URL/workflows" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "test-workflow",
        "description": "Integration test",
        "tasks": [{"id": "task-1", "name": "Task 1"}],
        "dependencies": []
    }')

WORKFLOW_ID=$(echo "$WORKFLOW" | jq -r '.workflow_id')
echo "✓ Created workflow: $WORKFLOW_ID"

# Test 2: Analyze workflow
echo "Test 2: Analyze workflow..."
ANALYSIS=$(curl -s -X POST "$API_URL/analyze" \
    -H "Content-Type: application/json" \
    -d "{\"workflow_id\": \"$WORKFLOW_ID\"}")

ANALYSIS_ID=$(echo "$ANALYSIS" | jq -r '.analysis_id')
echo "✓ Analysis completed: $ANALYSIS_ID"

# Test 3: Generate decision
echo "Test 3: Generate decision..."
DECISION=$(curl -s -X POST "$API_URL/decide" \
    -H "Content-Type: application/json" \
    -d "{\"analysis_id\": \"$ANALYSIS_ID\"}")

DECISION_ID=$(echo "$DECISION" | jq -r '.decision_id')
echo "✓ Decision generated: $DECISION_ID"

# Test 4: Execute workflow
echo "Test 4: Execute workflow..."
EXECUTION=$(curl -s -X POST "$API_URL/execute" \
    -H "Content-Type: application/json" \
    -d "{\"workflow_id\": \"$WORKFLOW_ID\", \"dry_run\": true}")

EXECUTION_ID=$(echo "$EXECUTION" | jq -r '.execution_id')
echo "✓ Execution started: $EXECUTION_ID"

# Test 5: Get metrics
echo "Test 5: Fetch metrics..."
METRICS=$(curl -s "$API_URL/metrics")
if [ -z "$METRICS" ]; then
    echo "✗ Failed to fetch metrics"
    exit 1
fi
echo "✓ Metrics retrieved"

# Test 6: Cleanup
echo "Test 6: Cleanup..."
curl -s -X DELETE "$API_URL/workflows/$WORKFLOW_ID"
echo "✓ Workflow deleted"

echo "All integration tests passed!"
```

---

## Rollback Procedures

### Automatic Rollback on Failure

```yaml
# In deploy job
- name: Deploy and monitor
  run: |
    ./scripts/deploy.sh production ${{ github.sha }}
    
    # If health checks fail, rollback
    if ! ./scripts/health-check.sh production; then
      echo "Deployment failed health checks, rolling back..."
      ./scripts/rollback.sh production
      exit 1
    fi
```

---

## Load Testing

### Load Test Script

**File**: `scripts/load-test.sh`
```bash
#!/bin/bash

API_URL="${API_URL:-http://localhost:8000}"
CONCURRENT_USERS=100
DURATION=300  # 5 minutes

echo "Starting load test: $CONCURRENT_USERS users for ${DURATION}s"

# Install Apache Bench if needed
if ! command -v ab &> /dev/null; then
    echo "Installing Apache Bench..."
    sudo apt-get install apache2-utils
fi

# Run load test
ab -n 10000 -c "$CONCURRENT_USERS" -t "$DURATION" \
    "$API_URL/health"

echo "Load test completed"
```

---

## Release Management

### Create Release

```bash
#!/bin/bash

VERSION=$1
CHANGELOG=$2

git tag -a "v$VERSION" -m "$CHANGELOG"
git push origin "v$VERSION"

gh release create "v$VERSION" \
    --title "Release v$VERSION" \
    --notes "$CHANGELOG"
```

---

## Deployment Checklist

- [ ] All tests passing (unit, integration, end-to-end)
- [ ] Code review approved
- [ ] Security scan passed
- [ ] Database migrations tested
- [ ] Backup created
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Staging deployment successful
- [ ] Smoke tests passed
- [ ] Health checks verified
- [ ] Load test acceptable
- [ ] Production deployment executed
- [ ] Post-deployment verification passed
- [ ] Team notified
- [ ] Documentation updated

---

## Summary

Phase 6 deployment automation provides:
- Complete GitHub Actions CI/CD pipeline
- Docker image building and pushing
- Kubernetes deployment automation
- Health check and monitoring integration
- Automated rollback procedures
- Load testing capabilities
- Integration test suite
- Release management workflows
