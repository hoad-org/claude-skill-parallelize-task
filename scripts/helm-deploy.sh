#!/bin/bash
# Deploy using Helm chart
# Usage: ./scripts/helm-deploy.sh [release-name] [namespace] [values-file]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION=$(grep '^version = ' "$PROJECT_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2)
RELEASE_NAME="${1:-parallelizer}"
NAMESPACE="${2:-default}"
VALUES_FILE="${3:-${PROJECT_ROOT}/helm/parallelizer/values.yaml}"
CHART_DIR="${PROJECT_ROOT}/helm/parallelizer"

echo "=================================="
echo "Deploying with Helm"
echo "=================================="
echo "Release: $RELEASE_NAME"
echo "Namespace: $NAMESPACE"
echo "Chart: $CHART_DIR"
echo "Values: $VALUES_FILE"
echo ""

# Check helm installed
if ! command -v helm &>/dev/null; then
  echo "❌ helm not found. Install Helm to use this script."
  exit 1
fi

# Check kubectl installed
if ! command -v kubectl &>/dev/null; then
  echo "❌ kubectl not found. Install kubectl first."
  exit 1
fi

# Verify chart directory
if [ ! -d "$CHART_DIR" ]; then
  echo "❌ Chart directory not found: $CHART_DIR"
  exit 1
fi

# Verify Chart.yaml exists
if [ ! -f "$CHART_DIR/Chart.yaml" ]; then
  echo "❌ Chart.yaml not found at $CHART_DIR"
  exit 1
fi

# Verify values file
if [ ! -f "$VALUES_FILE" ]; then
  echo "❌ Values file not found: $VALUES_FILE"
  exit 1
fi

# Check Kubernetes context
CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "")
if [ -z "$CURRENT_CONTEXT" ]; then
  echo "❌ No Kubernetes context configured"
  exit 1
fi
echo "📍 Current context: $CURRENT_CONTEXT"

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
  echo "📁 Creating namespace: $NAMESPACE"
  kubectl create namespace "$NAMESPACE"
fi

# Add Helm repositories (if using sub-charts)
echo "📚 Adding Helm repositories..."
helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update || true

# Validate chart
echo "✓ Validating Helm chart..."
helm lint "$CHART_DIR" || {
  echo "⚠️  Chart validation had warnings"
}

# Dry run to verify configuration
echo "🔍 Running Helm dry-run..."
helm install "$RELEASE_NAME" "$CHART_DIR" \
  --namespace "$NAMESPACE" \
  --values "$VALUES_FILE" \
  --dry-run --debug \
  > /tmp/helm-dry-run.yaml 2>&1 || {
  echo "⚠️  Dry-run generated output (may contain warnings)"
}

# Check if release already exists
RELEASE_EXISTS=$(helm list -n "$NAMESPACE" | grep "^$RELEASE_NAME" || true)

if [ -n "$RELEASE_EXISTS" ]; then
  # Upgrade existing release
  echo ""
  echo "🔄 Upgrading existing release: $RELEASE_NAME"
  helm upgrade "$RELEASE_NAME" "$CHART_DIR" \
    --namespace "$NAMESPACE" \
    --values "$VALUES_FILE" \
    --wait \
    --timeout 10m \
    --cleanup-on-fail || {
    echo "❌ Helm upgrade failed"
    exit 1
  }
else
  # Install new release
  echo ""
  echo "📦 Installing new release: $RELEASE_NAME"
  helm install "$RELEASE_NAME" "$CHART_DIR" \
    --namespace "$NAMESPACE" \
    --values "$VALUES_FILE" \
    --wait \
    --timeout 10m || {
    echo "❌ Helm install failed"
    exit 1
  }
fi

echo ""
echo "✅ Helm deployment complete!"
echo ""
echo "Release status:"
helm status "$RELEASE_NAME" -n "$NAMESPACE"
echo ""
echo "View release details:"
echo "  helm get values $RELEASE_NAME -n $NAMESPACE"
echo "  helm get manifest $RELEASE_NAME -n $NAMESPACE"
echo ""
echo "View pod status:"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "View logs:"
echo "  kubectl logs -n $NAMESPACE -l app=parallelizer --tail=100 -f"
echo ""
echo "Rollback if needed:"
echo "  helm rollback $RELEASE_NAME -n $NAMESPACE"
