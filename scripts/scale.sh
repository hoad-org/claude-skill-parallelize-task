#!/bin/bash
set -e

# Scaling Script for Parallelizer Deployment
# Manages horizontal pod autoscaling and replica count

NAMESPACE="${1:-parallelizer-staging}"
OPERATION="${2:-status}"  # status, set, scale, auto
REPLICAS="${3:-3}"
ENVIRONMENT="${4:-staging}"

echo "⚙️  Starting scale operation: $OPERATION"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validate namespace
if ! kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
  echo -e "${RED}❌ Namespace $NAMESPACE does not exist${NC}"
  exit 1
fi

# Helper function
print_status() {
  local NAME=$1
  local DESIRED=$(kubectl get deployment $NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
  local CURRENT=$(kubectl get deployment $NAME -n $NAMESPACE -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
  local READY=$(kubectl get deployment $NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
  local UPDATED=$(kubectl get deployment $NAME -n $NAMESPACE -o jsonpath='{.status.updatedReplicas}' 2>/dev/null || echo "0")

  echo "Deployment: $NAME"
  echo "  Desired replicas: $DESIRED"
  echo "  Current replicas: $CURRENT"
  echo "  Ready replicas: $READY"
  echo "  Updated replicas: $UPDATED"
}

# Operations
case "$OPERATION" in
  status)
    echo "1️⃣  Checking current scaling status..."
    echo ""
    print_status "parallelizer-api"
    echo ""

    # Show HPA status if exists
    echo "2️⃣  Checking autoscaling status..."
    HPA_EXISTS=$(kubectl get hpa -n $NAMESPACE -l app=parallelizer 2>/dev/null | wc -l)

    if [ "$HPA_EXISTS" -gt 1 ]; then
      kubectl get hpa -n $NAMESPACE -l app=parallelizer
    else
      echo "No HPA configured"
    fi
    ;;

  set)
    # Set exact replica count
    echo "1️⃣  Setting replica count to $REPLICAS..."

    # Disable HPA if it exists
    HPA_EXISTS=$(kubectl get hpa -n $NAMESPACE -l app=parallelizer 2>/dev/null | wc -l)
    if [ "$HPA_EXISTS" -gt 1 ]; then
      echo "Disabling HPA..."
      kubectl delete hpa -n $NAMESPACE -l app=parallelizer --ignore-not-found
    fi

    # Scale deployment
    kubectl scale deployment parallelizer-api -n $NAMESPACE --replicas=$REPLICAS

    echo -e "${GREEN}✅${NC} Scaled to $REPLICAS replicas"

    # Wait for scaling
    echo "2️⃣  Waiting for new replicas to be ready..."
    kubectl rollout status deployment/parallelizer-api -n $NAMESPACE --timeout=5m

    echo ""
    print_status "parallelizer-api"
    ;;

  scale)
    # Calculate new replica count
    CURRENT=$(kubectl get deployment parallelizer-api -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")

    if [[ "$REPLICAS" == "+"* ]]; then
      # Increase
      INCREASE=${REPLICAS#+}
      NEW_COUNT=$((CURRENT + INCREASE))
    elif [[ "$REPLICAS" == "-"* ]]; then
      # Decrease
      DECREASE=${REPLICAS#-}
      NEW_COUNT=$((CURRENT - DECREASE))
      if [ "$NEW_COUNT" -lt 1 ]; then
        NEW_COUNT=1
      fi
    else
      NEW_COUNT=$REPLICAS
    fi

    echo "1️⃣  Scaling from $CURRENT to $NEW_COUNT replicas..."

    kubectl scale deployment parallelizer-api -n $NAMESPACE --replicas=$NEW_COUNT

    echo -e "${GREEN}✅${NC} Scaling operation initiated"

    echo "2️⃣  Waiting for scaling to complete..."
    kubectl rollout status deployment/parallelizer-api -n $NAMESPACE --timeout=5m

    echo ""
    print_status "parallelizer-api"
    ;;

  auto)
    # Enable horizontal pod autoscaling
    echo "1️⃣  Configuring horizontal pod autoscaling..."

    # Set default values based on environment
    MIN_REPLICAS=2
    MAX_REPLICAS=10
    CPU_THRESHOLD=70

    case "$ENVIRONMENT" in
      production)
        MIN_REPLICAS=3
        MAX_REPLICAS=20
        CPU_THRESHOLD=65
        ;;
      staging)
        MIN_REPLICAS=2
        MAX_REPLICAS=10
        CPU_THRESHOLD=70
        ;;
      dev)
        MIN_REPLICAS=1
        MAX_REPLICAS=5
        CPU_THRESHOLD=80
        ;;
    esac

    echo "Environment: $ENVIRONMENT"
    echo "Min replicas: $MIN_REPLICAS"
    echo "Max replicas: $MAX_REPLICAS"
    echo "CPU threshold: ${CPU_THRESHOLD}%"

    # Create or update HPA
    kubectl autoscale deployment parallelizer-api \
      -n $NAMESPACE \
      --min=$MIN_REPLICAS \
      --max=$MAX_REPLICAS \
      --cpu-percent=$CPU_THRESHOLD \
      --name=parallelizer-api-hpa \
      --save-config 2>/dev/null || kubectl patch hpa parallelizer-api-hpa \
      -n $NAMESPACE \
      -p '{"spec":{"minReplicas":'$MIN_REPLICAS',"maxReplicas":'$MAX_REPLICAS'}}'

    echo -e "${GREEN}✅${NC} HPA configured"

    echo "2️⃣  Verifying HPA status..."
    sleep 2
    kubectl get hpa -n $NAMESPACE -l app=parallelizer || true

    echo ""
    echo "3️⃣  Current metrics:"
    kubectl top nodes 2>/dev/null || echo "Metrics not available"
    kubectl top pods -n $NAMESPACE -l app=parallelizer 2>/dev/null || echo "Pod metrics not available"
    ;;

  *)
    echo -e "${RED}❌ Unknown operation: $OPERATION${NC}"
    echo ""
    echo "Usage: scale.sh <namespace> <operation> [args]"
    echo ""
    echo "Operations:"
    echo "  status              - Show current scaling status"
    echo "  set <replicas>      - Set exact replica count"
    echo "  scale <+n|-n|n>     - Increase/decrease by n or set to n"
    echo "  auto                - Enable horizontal pod autoscaling"
    echo ""
    echo "Examples:"
    echo "  scale.sh parallelizer-staging status"
    echo "  scale.sh parallelizer-prod set 5"
    echo "  scale.sh parallelizer-staging scale +2"
    echo "  scale.sh parallelizer-prod scale -1"
    echo "  scale.sh parallelizer-prod auto production"
    exit 1
    ;;
esac

# Summary
echo ""
echo "════════════════════════════════════"
echo "📊 Scaling Operation Summary"
echo "════════════════════════════════════"
echo "Namespace: $NAMESPACE"
echo "Operation: $OPERATION"
echo "Environment: $ENVIRONMENT"
echo "Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════"

echo ""
echo -e "${GREEN}✅ Operation completed${NC}"
