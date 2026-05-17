#!/bin/bash
set -e

# Restore Script for Parallelizer Deployment
# Restores deployment state from backup

NAMESPACE="${1:-parallelizer-staging}"
BACKUP_ARCHIVE="${2:-.}"
DRY_RUN="${3:-false}"

echo "📂 Starting restore from backup..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validate inputs
if [ ! -f "$BACKUP_ARCHIVE" ] && [ "$BACKUP_ARCHIVE" != "." ]; then
  echo -e "${RED}❌ Backup archive not found: $BACKUP_ARCHIVE${NC}"
  exit 1
fi

# Handle directory as backup source
RESTORE_DIR="$BACKUP_ARCHIVE"
if [ -f "$BACKUP_ARCHIVE" ]; then
  # Extract archive
  RESTORE_DIR="/tmp/restore-$RANDOM"
  mkdir -p "$RESTORE_DIR"

  echo "1️⃣  Extracting backup archive..."
  tar -xzf "$BACKUP_ARCHIVE" -C "$RESTORE_DIR"
  # Get the actual backup directory
  RESTORE_DIR=$(find "$RESTORE_DIR" -maxdepth 2 -name "k8s" -type d | xargs dirname)
  echo "   Extracted to: $RESTORE_DIR"
else
  echo "1️⃣  Using backup directory: $RESTORE_DIR"
fi

# Validate restore directory
if [ ! -d "$RESTORE_DIR/k8s" ]; then
  echo -e "${RED}❌ Invalid backup format: k8s directory not found${NC}"
  exit 1
fi

echo ""

# 1. Pre-restore checks
echo "2️⃣  Pre-restore checks..."

if ! kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
  echo "   Creating namespace $NAMESPACE..."
  kubectl create namespace "$NAMESPACE"
else
  echo "   Namespace exists: $NAMESPACE"
fi

# Show backup info
if [ -f "$RESTORE_DIR/BACKUP_INFO.txt" ]; then
  echo ""
  echo "3️⃣  Backup Information:"
  cat "$RESTORE_DIR/BACKUP_INFO.txt" | head -15
  echo ""
fi

# Confirmation
if [ "$DRY_RUN" != "true" ]; then
  echo -e "${YELLOW}⚠️  WARNING: This will restore the deployment state from backup${NC}"
  echo "   Namespace: $NAMESPACE"
  echo ""
  read -p "   Continue with restore? (yes/no): " -r CONFIRM

  if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
  fi
fi

# 2. Create pre-restore snapshot
echo ""
echo "4️⃣  Creating pre-restore snapshot..."

SNAPSHOT_DIR="/tmp/parallelizer-snapshot-$(date +%s)"
mkdir -p "$SNAPSHOT_DIR"

kubectl get deployment -n $NAMESPACE -o yaml > "$SNAPSHOT_DIR/deployments-before.yaml" 2>/dev/null || true
kubectl get svc -n $NAMESPACE -o yaml > "$SNAPSHOT_DIR/services-before.yaml" 2>/dev/null || true

echo "   Snapshot saved to: $SNAPSHOT_DIR"

# 3. Restore Kubernetes resources
echo ""
echo "5️⃣  Restoring Kubernetes resources..."

if [ "$DRY_RUN" = "true" ]; then
  echo "   [DRY RUN] Would restore the following resources:"
  echo "   - Deployments"
  echo "   - Services"
  echo "   - ConfigMaps"
  echo "   - Secrets"
  echo "   - Ingress"
else
  # Restore in order
  echo "   - Secrets (first, dependencies)..."
  kubectl apply -f "$RESTORE_DIR/k8s/secrets.yaml" --namespace=$NAMESPACE 2>/dev/null || echo "     ⚠️  Secrets not found or error"

  echo "   - ConfigMaps..."
  kubectl apply -f "$RESTORE_DIR/k8s/configmaps.yaml" --namespace=$NAMESPACE 2>/dev/null || echo "     ⚠️  ConfigMaps not found or error"

  echo "   - Services..."
  kubectl apply -f "$RESTORE_DIR/k8s/services.yaml" --namespace=$NAMESPACE

  echo "   - Deployments..."
  kubectl apply -f "$RESTORE_DIR/k8s/deployments.yaml" --namespace=$NAMESPACE

  echo "   - Ingress..."
  kubectl apply -f "$RESTORE_DIR/k8s/ingress.yaml" --namespace=$NAMESPACE 2>/dev/null || echo "     ⚠️  Ingress not found or error"

  echo "   - RBAC..."
  kubectl apply -f "$RESTORE_DIR/k8s/rbac.yaml" --namespace=$NAMESPACE 2>/dev/null || echo "     ⚠️  RBAC not found or error"

  # Restore PVCs separately (might need special handling)
  if [ -f "$RESTORE_DIR/k8s/pvcs.yaml" ]; then
    echo "   - PVCs..."
    kubectl apply -f "$RESTORE_DIR/k8s/pvcs.yaml" --namespace=$NAMESPACE 2>/dev/null || echo "     ⚠️  PVCs not found or error"
  fi

  echo -e "${GREEN}✅${NC} Kubernetes resources restored"
fi

# 4. Wait for rollout if not dry run
if [ "$DRY_RUN" != "true" ]; then
  echo ""
  echo "6️⃣  Waiting for deployments to be ready..."

  # Get all deployments in namespace
  DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE -o name 2>/dev/null | cut -d'/' -f2 || echo "")

  if [ -n "$DEPLOYMENTS" ]; then
    for deployment in $DEPLOYMENTS; do
      echo "   - $deployment..."
      kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=5m || echo "     ⚠️  Timeout waiting for $deployment"
    done
  else
    echo "   No deployments found"
  fi
fi

# 5. Restore Helm releases (if available)
if [ -d "$RESTORE_DIR/helm" ] && [ "$(ls -A $RESTORE_DIR/helm)" ]; then
  echo ""
  echo "7️⃣  Restoring Helm releases..."

  if [ "$DRY_RUN" = "true" ]; then
    echo "   [DRY RUN] Would restore Helm releases from:"
    ls -la "$RESTORE_DIR/helm/"
  else
    for values_file in "$RESTORE_DIR/helm"/*-values.yaml; do
      if [ -f "$values_file" ]; then
        RELEASE_NAME=$(basename "$values_file" -values.yaml)
        echo "   - Release: $RELEASE_NAME..."

        helm upgrade --install "$RELEASE_NAME" \
          --namespace=$NAMESPACE \
          -f "$values_file" \
          --wait \
          --timeout=5m \
          2>/dev/null || echo "     ⚠️  Error restoring release $RELEASE_NAME"
      fi
    done
    echo -e "${GREEN}✅${NC} Helm releases restored"
  fi
fi

# 6. Restore logs (informational only)
echo ""
echo "8️⃣  Backup logs available in: $RESTORE_DIR/logs/"

# 7. Verification
if [ "$DRY_RUN" != "true" ]; then
  echo ""
  echo "9️⃣  Verifying restoration..."

  DEPLOYMENT_COUNT=$(kubectl get deployments -n $NAMESPACE 2>/dev/null | wc -l)
  SERVICE_COUNT=$(kubectl get svc -n $NAMESPACE 2>/dev/null | wc -l)
  POD_COUNT=$(kubectl get pods -n $NAMESPACE 2>/dev/null | wc -l)

  echo "   Deployments: $((DEPLOYMENT_COUNT - 1))"
  echo "   Services: $((SERVICE_COUNT - 1))"
  echo "   Pods: $((POD_COUNT - 1))"

  echo ""
  echo "🔟 Resource status:"
  kubectl get all -n $NAMESPACE 2>/dev/null | head -10 || true
fi

# Summary
echo ""
echo "════════════════════════════════════"
echo "📂 Restore Summary"
echo "════════════════════════════════════"
echo "Namespace: $NAMESPACE"
echo "Backup source: $BACKUP_ARCHIVE"
echo "Dry run: $DRY_RUN"
echo "Pre-restore snapshot: $SNAPSHOT_DIR"
echo "Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════"

if [ "$DRY_RUN" = "true" ]; then
  echo ""
  echo -e "${YELLOW}ℹ️  Dry run mode - no changes made${NC}"
  echo "To execute restore:"
  echo "  ./scripts/restore.sh $NAMESPACE $BACKUP_ARCHIVE false"
else
  echo ""
  echo -e "${GREEN}✅ Restore completed${NC}"
  echo ""
  echo "Pre-restore state saved to: $SNAPSHOT_DIR"
  echo "If rollback is needed:"
  echo "  kubectl apply -f $SNAPSHOT_DIR/deployments-before.yaml"
fi
