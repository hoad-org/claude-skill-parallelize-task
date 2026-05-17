#!/bin/bash
set -e

# Backup Script for Parallelizer Deployment
# Creates comprehensive backups of deployment state and configuration

NAMESPACE="${1:-parallelizer-staging}"
BACKUP_DIR="${2:-./.backups}"
RETENTION="${3:-30}"  # days to keep backups

echo "💾 Starting backup for $NAMESPACE..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create backup directory structure
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FULL_BACKUP_DIR="$BACKUP_DIR/$NAMESPACE/$TIMESTAMP"

mkdir -p "$FULL_BACKUP_DIR"

echo "📁 Backup directory: $FULL_BACKUP_DIR"
echo ""

# Validate namespace
if ! kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
  echo -e "${RED}❌ Namespace $NAMESPACE does not exist${NC}"
  exit 1
fi

# 1. Export all Kubernetes resources
echo "1️⃣  Backing up Kubernetes resources..."

mkdir -p "$FULL_BACKUP_DIR/k8s"

# Deployments
echo "   - Deployments..."
kubectl get deployment -n $NAMESPACE -o yaml > "$FULL_BACKUP_DIR/k8s/deployments.yaml"

# Services
echo "   - Services..."
kubectl get svc -n $NAMESPACE -o yaml > "$FULL_BACKUP_DIR/k8s/services.yaml"

# Configmaps
echo "   - ConfigMaps..."
kubectl get configmap -n $NAMESPACE -o yaml > "$FULL_BACKUP_DIR/k8s/configmaps.yaml"

# Secrets (note: secrets are base64 encoded, not encrypted)
echo "   - Secrets..."
kubectl get secret -n $NAMESPACE -o yaml > "$FULL_BACKUP_DIR/k8s/secrets.yaml"

# PVC
echo "   - Persistent Volume Claims..."
kubectl get pvc -n $NAMESPACE -o yaml > "$FULL_BACKUP_DIR/k8s/pvcs.yaml" 2>/dev/null || true

# Ingress
echo "   - Ingress..."
kubectl get ingress -n $NAMESPACE -o yaml > "$FULL_BACKUP_DIR/k8s/ingress.yaml" 2>/dev/null || true

# RBAC
echo "   - RBAC..."
kubectl get role,rolebinding -n $NAMESPACE -o yaml > "$FULL_BACKUP_DIR/k8s/rbac.yaml" 2>/dev/null || true

# 2. Export Helm releases
echo ""
echo "2️⃣  Backing up Helm releases..."

mkdir -p "$FULL_BACKUP_DIR/helm"

# Get Helm releases
RELEASES=$(helm list -n $NAMESPACE -q 2>/dev/null || echo "")

if [ -n "$RELEASES" ]; then
  for release in $RELEASES; do
    echo "   - Release: $release..."
    helm get values $release -n $NAMESPACE > "$FULL_BACKUP_DIR/helm/$release-values.yaml"
    helm get manifest $release -n $NAMESPACE > "$FULL_BACKUP_DIR/helm/$release-manifest.yaml"
    helm get notes $release -n $NAMESPACE > "$FULL_BACKUP_DIR/helm/$release-notes.txt" 2>/dev/null || true
  done
else
  echo "   No Helm releases found"
fi

# 3. Export pod logs (last 100 lines)
echo ""
echo "3️⃣  Backing up pod logs..."

mkdir -p "$FULL_BACKUP_DIR/logs"

PODS=$(kubectl get pods -n $NAMESPACE -l app=parallelizer -o name 2>/dev/null || echo "")

if [ -n "$PODS" ]; then
  for pod in $PODS; do
    POD_NAME=$(echo $pod | cut -d'/' -f2)
    echo "   - Pod: $POD_NAME..."
    kubectl logs $pod -n $NAMESPACE --tail=100 > "$FULL_BACKUP_DIR/logs/$POD_NAME.log" 2>/dev/null || true

    # Previous logs if pod crashed
    kubectl logs $pod -n $NAMESPACE --previous --tail=100 > "$FULL_BACKUP_DIR/logs/$POD_NAME-previous.log" 2>/dev/null || true
  done
else
  echo "   No pods found"
fi

# 4. Export events
echo ""
echo "4️⃣  Backing up events..."

kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' > "$FULL_BACKUP_DIR/events.txt"

# 5. Export metrics (if available)
echo ""
echo "5️⃣  Backing up metrics snapshot..."

mkdir -p "$FULL_BACKUP_DIR/metrics"

# Node metrics
kubectl top nodes > "$FULL_BACKUP_DIR/metrics/nodes.txt" 2>/dev/null || echo "Node metrics not available" > "$FULL_BACKUP_DIR/metrics/nodes.txt"

# Pod metrics
kubectl top pods -n $NAMESPACE > "$FULL_BACKUP_DIR/metrics/pods.txt" 2>/dev/null || echo "Pod metrics not available" > "$FULL_BACKUP_DIR/metrics/pods.txt"

# 6. Create metadata file
echo ""
echo "6️⃣  Creating backup metadata..."

cat > "$FULL_BACKUP_DIR/BACKUP_INFO.txt" << EOF
===========================================
Backup Information
===========================================

Backup Timestamp: $TIMESTAMP
Namespace: $NAMESPACE
Cluster: $(kubectl config current-context 2>/dev/null || echo "Unknown")

Kubernetes Version: $(kubectl version --short 2>/dev/null | grep Server || echo "Unknown")
Helm Version: $(helm version --short 2>/dev/null || echo "Not installed")

Resources Backed Up:
  - Deployments
  - Services
  - ConfigMaps
  - Secrets
  - PVCs
  - Ingress
  - RBAC
  - Helm releases
  - Pod logs
  - Events
  - Metrics

Backup Location: $FULL_BACKUP_DIR
Size: $(du -sh $FULL_BACKUP_DIR 2>/dev/null | awk '{print $1}')

===========================================
EOF

# 7. Compress backup
echo ""
echo "7️⃣  Compressing backup..."

BACKUP_ARCHIVE="$BACKUP_DIR/$NAMESPACE-backup-$TIMESTAMP.tar.gz"

tar -czf "$BACKUP_ARCHIVE" -C "$BACKUP_DIR/$NAMESPACE" "$TIMESTAMP" 2>/dev/null

SIZE=$(du -h "$BACKUP_ARCHIVE" | awk '{print $1}')
echo "Archive: $BACKUP_ARCHIVE ($SIZE)"

# 8. Clean up old backups based on retention
echo ""
echo "8️⃣  Cleaning up old backups (retention: $RETENTION days)..."

find "$BACKUP_DIR" -name "$NAMESPACE-backup-*.tar.gz" -mtime +$RETENTION -delete 2>/dev/null || true
find "$BACKUP_DIR/$NAMESPACE" -maxdepth 1 -type d -mtime +$RETENTION -exec rm -rf {} \; 2>/dev/null || true

BACKUP_COUNT=$(find "$BACKUP_DIR" -name "$NAMESPACE-backup-*.tar.gz" 2>/dev/null | wc -l)
echo "   Backups kept: $BACKUP_COUNT"

# 9. Generate restore instructions
echo ""
echo "9️⃣  Creating restore instructions..."

cat > "$FULL_BACKUP_DIR/RESTORE.md" << 'EOF'
# Restore Instructions

## Prerequisites
- kubectl configured with access to the target cluster
- Helm installed and configured

## Restore Procedure

### Option 1: Full Restore (Recommended)

```bash
# Extract backup
tar -xzf <backup-archive>

# Restore all Kubernetes resources
kubectl apply -f <backup-dir>/k8s/deployments.yaml
kubectl apply -f <backup-dir>/k8s/services.yaml
kubectl apply -f <backup-dir>/k8s/configmaps.yaml
kubectl apply -f <backup-dir>/k8s/secrets.yaml

# Restore Helm releases (if applicable)
cd <backup-dir>/helm
helm upgrade --install parallelizer . -f parallelizer-values.yaml
```

### Option 2: Selective Restore

```bash
# Restore specific resource types
kubectl apply -f <backup-dir>/k8s/deployments.yaml
kubectl apply -f <backup-dir>/k8s/services.yaml
```

### Option 3: Restore from Kubernetes Resources

```bash
# Extract backup
tar -xzf <backup-archive>

# Restore the entire namespace
kubectl apply -f <backup-dir>/k8s/
```

## Verification

```bash
# Verify deployment status
kubectl get deployment -n <namespace>

# Check pod status
kubectl get pods -n <namespace>

# Verify services
kubectl get svc -n <namespace>
```

## Troubleshooting

If pods don't start:
1. Check logs: `kubectl logs <pod-name> -n <namespace>`
2. Check events: `kubectl get events -n <namespace>`
3. Verify secrets exist: `kubectl get secrets -n <namespace>`
4. Verify configmaps exist: `kubectl get configmap -n <namespace>`

## Important Notes

- Secrets are base64 encoded in backups. Do not commit backups to version control.
- Some resources may need adjustment (e.g., LoadBalancer service IPs)
- Persistent volume data is NOT included in this backup
- Verify the configuration before restoring to production
EOF

# Summary
echo ""
echo "════════════════════════════════════"
echo "💾 Backup Summary"
echo "════════════════════════════════════"
echo "Namespace: $NAMESPACE"
echo "Timestamp: $TIMESTAMP"
echo "Archive: $BACKUP_ARCHIVE"
echo "Size: $SIZE"
echo "Retention: $RETENTION days"
echo "Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════"

echo ""
echo -e "${GREEN}✅ Backup completed successfully${NC}"
echo ""
echo "Restore with:"
echo "  ./scripts/restore.sh $NAMESPACE $BACKUP_ARCHIVE"
