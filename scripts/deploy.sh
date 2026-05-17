#!/bin/bash
# Deploy to Kubernetes cluster
# Usage: ./scripts/deploy.sh [tag] [namespace] [cluster]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION=$(grep '^version = ' "$PROJECT_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2)
TAG="${1:-$VERSION}"
NAMESPACE="${2:-default}"
CLUSTER="${3:-}"
DEPLOYMENT_NAME="parallelizer-api"

echo "=================================="
echo "Deploying to Kubernetes"
echo "=================================="
echo "Version: $VERSION"
echo "Tag: $TAG"
echo "Namespace: $NAMESPACE"
[ -n "$CLUSTER" ] && echo "Cluster: $CLUSTER"
echo ""

# Check kubectl installed
if ! command -v kubectl &>/dev/null; then
  echo "❌ kubectl not found. Install kubectl to deploy to Kubernetes."
  exit 1
fi

# Check Kubernetes context
CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "")
if [ -z "$CURRENT_CONTEXT" ]; then
  echo "❌ No Kubernetes context configured"
  echo "Run: kubectl config set-context <context>"
  exit 1
fi
echo "📍 Current context: $CURRENT_CONTEXT"

# Switch cluster if specified
if [ -n "$CLUSTER" ]; then
  echo "🔄 Switching to cluster: $CLUSTER"
  kubectl config use-context "$CLUSTER" || {
    echo "❌ Failed to switch to cluster: $CLUSTER"
    exit 1
  }
fi

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
  echo "📁 Creating namespace: $NAMESPACE"
  kubectl create namespace "$NAMESPACE" || {
    echo "⚠️  Namespace may already exist or permission denied"
  }
fi

# Apply RBAC
echo "🔐 Applying RBAC policies..."
kubectl apply -f "$PROJECT_ROOT/k8s/rbac.yaml" -n "$NAMESPACE" || {
  echo "⚠️  RBAC application had issues (may already exist)"
}

# Apply ConfigMap
echo "📋 Applying ConfigMaps..."
kubectl apply -f "$PROJECT_ROOT/k8s/configmap.yaml" -n "$NAMESPACE" || {
  echo "❌ Failed to apply ConfigMap"
  exit 1
}

# Apply Secrets
echo "🔑 Applying Secrets..."
kubectl apply -f "$PROJECT_ROOT/k8s/secrets.yaml" -n "$NAMESPACE" || {
  echo "⚠️  Secret application had issues"
}

# Apply Service
echo "🌐 Applying Services..."
kubectl apply -f "$PROJECT_ROOT/k8s/service.yaml" -n "$NAMESPACE" || {
  echo "❌ Failed to apply Service"
  exit 1
}

# Update image tag in deployment
echo "🎯 Updating deployment image tag: $TAG"
kubectl set image deployment/$DEPLOYMENT_NAME \
  parallelizer="parallelize-task:${TAG}" \
  -n "$NAMESPACE" || {
  echo "⚠️  Image update had issues (deployment may not exist yet)"
}

# Apply Deployment
echo "🚀 Applying Deployment..."
kubectl apply -f "$PROJECT_ROOT/k8s/deployment.yaml" -n "$NAMESPACE" || {
  echo "❌ Failed to apply Deployment"
  exit 1
}

# Apply Ingress
echo "📡 Applying Ingress..."
kubectl apply -f "$PROJECT_ROOT/k8s/ingress.yaml" -n "$NAMESPACE" || {
  echo "⚠️  Ingress application had issues"
}

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Verify deployment status:"
echo "  kubectl get pods -n $NAMESPACE -l app=parallelizer"
echo "  kubectl describe deployment $DEPLOYMENT_NAME -n $NAMESPACE"
echo "  kubectl logs -n $NAMESPACE -l app=parallelizer --tail=100"
echo ""
echo "Port forwarding for local testing:"
echo "  kubectl port-forward svc/parallelizer-api 8000:8000 -n $NAMESPACE"
echo ""
echo "Get service details:"
echo "  kubectl get svc -n $NAMESPACE"
echo "  kubectl get ingress -n $NAMESPACE"
