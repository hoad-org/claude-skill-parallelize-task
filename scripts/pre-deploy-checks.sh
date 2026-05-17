#!/bin/bash
set -e

# Pre-deployment Checks Script
# Validates all prerequisites before deployment

echo "🔍 Running pre-deployment checks..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
check_pass() {
  echo -e "${GREEN}✅${NC} $1"
  PASSED=$((PASSED + 1))
}

check_fail() {
  echo -e "${RED}❌${NC} $1"
  FAILED=$((FAILED + 1))
}

check_warn() {
  echo -e "${YELLOW}⚠️${NC} $1"
  WARNINGS=$((WARNINGS + 1))
}

# 1. Environment checks
echo "1️⃣  Environment Checks"
echo "━━━━━━━━━━━━━━━━━━━━"

# Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
if [[ "$PYTHON_VERSION" == 3.12* ]] || [[ "$PYTHON_VERSION" == 3.13* ]]; then
  check_pass "Python version: $PYTHON_VERSION"
else
  check_fail "Python version: $PYTHON_VERSION (requires 3.12+)"
fi

# Required tools
for tool in pip pytest black ruff mypy docker kubectl helm; do
  if command -v "$tool" &> /dev/null; then
    check_pass "$tool installed"
  else
    check_fail "$tool not found"
  fi
done

# 2. Code quality checks
echo ""
echo "2️⃣  Code Quality"
echo "━━━━━━━━━━━━━━━━━━━━"

# Linting
if python -m ruff check src/ > /tmp/ruff-check.log 2>&1; then
  check_pass "Ruff linting passed"
else
  check_fail "Ruff linting failed"
  tail -5 /tmp/ruff-check.log
fi

# Type checking
if python -m mypy src/ > /tmp/mypy-check.log 2>&1; then
  check_pass "Type checking passed"
else
  check_fail "Type checking failed"
  tail -5 /tmp/mypy-check.log
fi

# Format checking
if python -m black src/ tests/ --check > /tmp/black-check.log 2>&1; then
  check_pass "Code formatting correct"
else
  check_warn "Code needs formatting (run: black src/ tests/)"
fi

# 3. Testing
echo ""
echo "3️⃣  Testing"
echo "━━━━━━━━━━━━━━━━━━━━"

# Run tests with coverage
if python -m pytest tests/ -v --cov=src/parallelizer_skill --cov-report=term-missing > /tmp/pytest.log 2>&1; then
  check_pass "All tests passed"

  # Extract coverage
  COVERAGE=$(grep "TOTAL" /tmp/pytest.log | awk '{print $NF}' | sed 's/%//')
  if (( $(echo "$COVERAGE >= 85" | bc -l) )); then
    check_pass "Code coverage: ${COVERAGE}%"
  else
    check_warn "Code coverage: ${COVERAGE}% (target: 85%)"
  fi
else
  check_fail "Tests failed"
  tail -20 /tmp/pytest.log
fi

# 4. Security checks
echo ""
echo "4️⃣  Security"
echo "━━━━━━━━━━━━━━━━━━━━"

# Bandit security scan
if python -m bandit -r src/ -q > /tmp/bandit-check.log 2>&1; then
  check_pass "Security scan passed (no issues)"
else
  ISSUES=$(grep -c ">> Issue" /tmp/bandit-check.log 2>/dev/null || echo "0")
  if [ "$ISSUES" -eq 0 ]; then
    check_pass "Security scan passed"
  else
    check_warn "Security scan found $ISSUES potential issues"
  fi
fi

# Check for secrets in code
if ! grep -r "password" src/ | grep -v "^Binary" > /dev/null 2>&1; then
  check_pass "No hardcoded secrets detected"
else
  check_warn "Potential secrets in code (manual review needed)"
fi

# Check .gitignore
if grep -q ".env" .gitignore 2>/dev/null; then
  check_pass ".env files ignored"
else
  check_warn ".env not in .gitignore"
fi

# 5. Docker checks
echo ""
echo "5️⃣  Docker"
echo "━━━━━━━━━━━━━━━━━━━━"

if [ -f "Dockerfile" ]; then
  check_pass "Dockerfile exists"

  # Try to build (without push)
  if docker build -t parallelizer:check . > /tmp/docker-build.log 2>&1; then
    check_pass "Docker image builds successfully"

    # Get image size
    SIZE=$(docker image inspect parallelizer:check --format='{{.Size}}' | numfmt --to=iec-i --suffix=B 2>/dev/null || echo "unknown")
    echo "  Image size: $SIZE"
  else
    check_fail "Docker build failed"
    tail -10 /tmp/docker-build.log
  fi
else
  check_fail "Dockerfile not found"
fi

# 6. Kubernetes checks
echo ""
echo "6️⃣  Kubernetes"
echo "━━━━━━━━━━━━━━━━━━━━"

# kubectl access
if kubectl cluster-info > /dev/null 2>&1; then
  check_pass "kubectl cluster access"

  # Get cluster info
  CLUSTER=$(kubectl config current-context)
  echo "  Current context: $CLUSTER"

  # Check namespaces
  if kubectl get namespace parallelizer-dev > /dev/null 2>&1; then
    check_pass "Dev namespace exists"
  else
    check_warn "Dev namespace not found"
  fi

  if kubectl get namespace parallelizer-staging > /dev/null 2>&1; then
    check_pass "Staging namespace exists"
  else
    check_warn "Staging namespace not found"
  fi
else
  check_fail "kubectl cluster access failed"
fi

# 7. Helm checks
echo ""
echo "7️⃣  Helm"
echo "━━━━━━━━━━━━━━━━━━━━"

if [ -f "helm/parallelizer/Chart.yaml" ]; then
  check_pass "Helm chart exists"

  if helm lint helm/parallelizer > /tmp/helm-lint.log 2>&1; then
    check_pass "Helm chart validation passed"
  else
    check_fail "Helm chart validation failed"
    cat /tmp/helm-lint.log
  fi

  # Check chart version
  CHART_VERSION=$(grep "^version:" helm/parallelizer/Chart.yaml | awk '{print $2}')
  echo "  Chart version: $CHART_VERSION"
else
  check_fail "Helm chart not found"
fi

# 8. Configuration checks
echo ""
echo "8️⃣  Configuration"
echo "━━━━━━━━━━━━━━━━━━━━"

if [ -f "pyproject.toml" ]; then
  check_pass "pyproject.toml exists"

  # Extract version
  PROJ_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
  echo "  Project version: $PROJ_VERSION"

  # Check dependencies
  if grep -q "fastapi" pyproject.toml; then
    check_pass "FastAPI dependency declared"
  else
    check_warn "FastAPI not in dependencies"
  fi
else
  check_fail "pyproject.toml not found"
fi

# Check environment files
if [ -f ".env.example" ]; then
  check_pass ".env.example exists"
else
  check_warn ".env.example not found"
fi

# 9. Documentation checks
echo ""
echo "9️⃣  Documentation"
echo "━━━━━━━━━━━━━━━━━━━━"

for doc in README.md DEPLOYMENT_QUICK_REFERENCE.md SKILL.md; do
  if [ -f "$doc" ]; then
    check_pass "$doc exists"
  else
    check_warn "$doc not found"
  fi
done

# 10. Git checks
echo ""
echo "🔟 Git"
echo "━━━━━━━━━━━━━━━━━━━━"

if [ -d ".git" ]; then
  check_pass "Git repository initialized"

  # Check git status
  if git status > /dev/null 2>&1; then
    UNCOMMITTED=$(git status --porcelain | wc -l)
    if [ "$UNCOMMITTED" -eq 0 ]; then
      check_pass "No uncommitted changes"
    else
      check_warn "$UNCOMMITTED uncommitted files"
    fi
  fi

  # Check remote
  if git remote -v | grep -q "origin"; then
    check_pass "Remote 'origin' configured"
  else
    check_warn "Remote 'origin' not configured"
  fi
else
  check_warn "Not a git repository"
fi

# Summary
echo ""
echo "════════════════════════════════════"
echo "📊 Pre-Deployment Check Summary"
echo "════════════════════════════════════"
echo "✅ Passed:  $PASSED"
echo "❌ Failed:  $FAILED"
echo "⚠️  Warnings: $WARNINGS"
echo ""
echo "Total checks: $((PASSED + FAILED + WARNINGS))"
echo "Success rate: $((PASSED * 100 / (PASSED + FAILED + WARNINGS)))%"
echo "════════════════════════════════════"

# Final verdict
echo ""
if [ $FAILED -eq 0 ]; then
  if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All pre-deployment checks PASSED${NC}"
    echo ""
    echo "Ready for deployment!"
    exit 0
  else
    echo -e "${YELLOW}⚠️  Pre-deployment checks PASSED with warnings${NC}"
    echo ""
    echo "Review warnings above before deploying"
    exit 0
  fi
else
  echo -e "${RED}❌ Pre-deployment checks FAILED${NC}"
  echo ""
  echo "Fix the failures above before deploying"
  exit 1
fi
