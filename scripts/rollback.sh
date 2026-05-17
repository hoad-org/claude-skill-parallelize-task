#!/bin/bash
set -e

# Rollback Script for Parallelizer Deployment
# Performs safe rollback with pre-checks and health verification

NAMESPACE="${1:-parallelizer-staging}"
REVISION="${2:-0}"  # 0 = previous revision
DRY_RUN="${3:-false}"

echo "⏮️  Starting rollback for $NAMESPACE..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validate inputs
if ! kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
  echo -e "${RED}❌ Namespace $NAMESPACE does not exist${NC}"
  exit 1
fi

# 1. Capture current state before rollback
echo "1️⃣  Capturing current deployment state..."

CURRENT_REVISION=$(kubectl rollout history deployment/parallelizer-api -n $NAMESPACE | tail -1 | awk '{print $1}')
CURRENT_IMAGE=$(kubectl get deployment parallelizer-api -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')

echo "   Current revision: $CURRENT_REVISION"
echo "   Current image: $CURRENT_IMAGE"

# 2. Show deployment history
echo ""
echo "2️⃣  Deployment History"
kubectl rollout history deployment/parallelizer-api -n $NAMESPACE || true

# 3. Determine target revision
echo ""
echo "3️⃣  Determining rollback target..."

if [ "$REVISION" = "0" ]; then
  # Find previous revision (one before current)
  PREV_REVISION=$(kubectl rollout history deployment/parallelizer-api -n $NAMESPACE | tail -2 | head -1 | awk '{print $1}')
  if [ -z "$PREV_REVISION" ]; then
    echo -e "${RED}❌ No previous revision found${NC}"
    exit 1
  fi
  TARGET_REVISION=$PREV_REVISION
else
  TARGET_REVISION=$REVISION
fi

echo "   Target revision: $TARGET_REVISION"

# 4. Get details of target revision
echo ""
echo "4️⃣  Target Revision Details"

# Try to get the revision details
kubectl rollout history deployment/parallelizer-api -n $NAMESPACE --revision=$TARGET_REVISION || true

# 5. Create backup of current state
echo ""
echo "5️⃣  Creating backup of current state..."

BACKUP_DIR="/tmp/parallelizer-backup-$(date +%s)"
mkdir -p "$BACKUP_DIR"

# Export current deployment
kubectl get deployment parallelizer-api -n $NAMESPACE -o yaml > "$BACKUP_DIR/deployment-current.yaml"

# Export current replicaset
kubectl get replicaset -n $NAMESPACE -l app=parallelizer -o yaml > "$BACKUP_DIR/replicaset-current.yaml"

# Export services
kubectl get svc -n $NAMESPACE -l app=parallelizer -o yaml > "$BACKUP_DIR/services.yaml" || true

# Export ingress
kubectl get ingress -n $NAMESPACE -o yaml > "$BACKUP_DIR/ingress.yaml" 2>/dev/null || true

echo "   Backup saved to: $BACKUP_DIR"

# 6. Health check before rollback
echo ""
echo "6️⃣  Pre-rollback health check..."

RUNNING_PODS=$(kubectl get pods -n $NAMESPACE -l app=parallelizer --field-selector=status.phase=Running -q | wc -l)
echo "   Running pods: $RUNNING_PODS"

# 7. Perform rollback
echo ""
echo "7️⃣  Performing rollback..."

if [ "$DRY_RUN" = "true" ]; then
  echo "   [DRY RUN] Would rollback to revision $TARGET_REVISION"
  echo "   Use 'rollback.sh $NAMESPACE $TARGET_REVISION false' to execute"
else
  echo "   Executing rollback to revision $TARGET_REVISION..."

  kubectl rollout undo deployment/parallelizer-api -n $NAMESPACE --to-revision=$TARGET_REVISION

  echo -e "${GREEN}✅${NC} Rollback command executed"
fi

# 8. Wait for rollout
echo ""
echo "8️⃣  Waiting for rollout to complete..."

if [ "$DRY_RUN" != "true" ]; then
  if kubectl rollout status deployment/parallelizer-api -n $NAMESPACE --timeout=5m; then
    echo -e "${GREEN}✅${NC} Rollout completed successfully"
  else
    echo -e "${RED}❌${NC} Rollout failed"
    exit 1
  fi
fi

# 9. Post-rollback verification
echo ""
echo "9️⃣  Post-rollback verification..."

NEW_IMAGE=$(kubectl get deployment parallelizer-api -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')
NEW_RUNNING_PODS=$(kubectl get pods -n $NAMESPACE -l app=parallelizer --field-selector=status.phase=Running -q | wc -l)

echo "   New image: $NEW_IMAGE"
echo "   Running pods: $NEW_RUNNING_PODS"

# 10. Port forward and health check
echo ""
echo "🔟 API Health Check"

if [ "$DRY_RUN" != "true" ]; then
  kubectl port-forward -n $NAMESPACE svc/parallelizer-api 8000:8000 &> /tmp/pf.log &
  PF_PID=$!

  sleep 2

  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Health endpoint: OK"
  else
    echo -e "${RED}❌${NC} Health endpoint: Failed"
  fi

  kill $PF_PID 2>/dev/null || true
fi

# Summary
echo ""
echo "════════════════════════════════════"
echo "📊 Rollback Summary"
echo "════════════════════════════════════"
echo "Namespace: $NAMESPACE"
echo "From revision: $CURRENT_REVISION"
echo "To revision: $TARGET_REVISION"
echo "Dry run: $DRY_RUN"
echo "Backup location: $BACKUP_DIR"
echo "Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════"

if [ "$DRY_RUN" != "true" ]; then
  echo ""
  echo -e "${GREEN}✅ Rollback completed successfully${NC}"
  echo ""
  echo "To restore the previous version if needed:"
  echo "  kubectl apply -f $BACKUP_DIR/deployment-current.yaml"
else
  echo ""
  echo -e "${YELLOW}ℹ️  Dry run mode - no changes made${NC}"
fi
