#!/bin/bash
set -e

# Health Check Script for Parallelizer Deployment
# Verifies deployment health across multiple dimensions

NAMESPACE="${1:-parallelizer-staging}"
ENVIRONMENT="${2:-staging}"
TIMEOUT="${3:-300}"

echo "🏥 Starting health check for $NAMESPACE..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Track health status
HEALTH_SCORE=0
TOTAL_CHECKS=0

# Helper function for checks
check_item() {
  local check_name=$1
  local check_cmd=$2
  local expected=$3

  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

  echo -n "Checking $check_name... "

  if eval "$check_cmd" > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
  else
    echo -e "${RED}❌${NC}"
  fi
}

# 1. Kubernetes cluster connectivity
echo "1️⃣  Kubernetes Connectivity"
check_item "Cluster access" "kubectl cluster-info" "success"
check_item "Current context" "kubectl config current-context" "success"

# 2. Namespace health
echo ""
echo "2️⃣  Namespace Status"
check_item "Namespace exists" "kubectl get namespace $NAMESPACE" "success"

# 3. Deployment status
echo ""
echo "3️⃣  Deployment Status"
DEPLOYMENT_STATUS=$(kubectl get deployment -n $NAMESPACE -l app=parallelizer -o jsonpath='{.items[0].status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "Unknown")
check_item "Deployment available" "[ \"$DEPLOYMENT_STATUS\" = \"True\" ]" "True"

# 4. Pod status
echo ""
echo "4️⃣  Pod Status"
POD_COUNT=$(kubectl get pods -n $NAMESPACE -l app=parallelizer --field-selector=status.phase=Running 2>/dev/null | wc -l)
POD_COUNT=$((POD_COUNT - 1))  # Subtract header

if [ "$POD_COUNT" -gt 0 ]; then
  echo "Running pods: $POD_COUNT"
  check_item "Running pods exist" "[ $POD_COUNT -gt 0 ]" "true"
else
  echo -e "${RED}❌ No running pods found${NC}"
fi

# 5. Service status
echo ""
echo "5️⃣  Service Status"
SERVICE_IP=$(kubectl get svc -n $NAMESPACE -l app=parallelizer -o jsonpath='{.items[0].spec.clusterIP}' 2>/dev/null || echo "")

if [ -n "$SERVICE_IP" ] && [ "$SERVICE_IP" != "<none>" ]; then
  echo "Service IP: $SERVICE_IP"
  check_item "Service exists" "[ -n \"$SERVICE_IP\" ]" "true"
else
  echo -e "${YELLOW}⚠️  Service not fully configured${NC}"
fi

# 6. Port forwarding and API health check
echo ""
echo "6️⃣  API Health Check"

# Start port forward in background
kubectl port-forward -n $NAMESPACE svc/parallelizer-api 8000:8000 &> /tmp/pf.log &
PF_PID=$!

# Wait for port forward to establish
sleep 2

# Check health endpoint
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo -e "${GREEN}✅${NC} Health endpoint: OK"
  HEALTH_SCORE=$((HEALTH_SCORE + 1))
else
  echo -e "${RED}❌${NC} Health endpoint: Failed"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check metrics endpoint
if curl -sf http://localhost:8000/metrics > /dev/null 2>&1; then
  echo -e "${GREEN}✅${NC} Metrics endpoint: OK"
  HEALTH_SCORE=$((HEALTH_SCORE + 1))
else
  echo -e "${RED}❌${NC} Metrics endpoint: Failed"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check API readiness
if curl -sf http://localhost:8000/api/v1/status > /dev/null 2>&1; then
  echo -e "${GREEN}✅${NC} API status: OK"
  HEALTH_SCORE=$((HEALTH_SCORE + 1))
else
  echo -e "${YELLOW}⚠️${NC} API status: Not available"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Clean up port forward
kill $PF_PID 2>/dev/null || true
sleep 1

# 7. Resource utilization
echo ""
echo "7️⃣  Resource Utilization"

MEMORY_USAGE=$(kubectl top pods -n $NAMESPACE -l app=parallelizer 2>/dev/null | tail -1 | awk '{print $2}' || echo "N/A")
CPU_USAGE=$(kubectl top pods -n $NAMESPACE -l app=parallelizer 2>/dev/null | tail -1 | awk '{print $3}' || echo "N/A")

echo "Memory usage: $MEMORY_USAGE"
echo "CPU usage: $CPU_USAGE"

# 8. Recent events
echo ""
echo "8️⃣  Recent Events"

EVENTS=$(kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' -l involvedObject.kind=Pod 2>/dev/null | tail -3 | awk '{print $4": "$6}' || echo "No events")

if [ "$EVENTS" != "No events" ]; then
  echo "$EVENTS"
  check_item "No error events" "! echo \"$EVENTS\" | grep -i error || true" "true"
else
  echo "No recent events"
fi

# 9. Storage and persistence
echo ""
echo "9️⃣  Storage Status"

PVC_STATUS=$(kubectl get pvc -n $NAMESPACE 2>/dev/null | grep -c "Bound" || echo "0")
if [ "$PVC_STATUS" -gt 0 ]; then
  echo -e "${GREEN}✅${NC} PVC status: Bound"
  HEALTH_SCORE=$((HEALTH_SCORE + 1))
else
  echo -e "${YELLOW}⚠️${NC} PVC status: Not found or unbound"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# 10. Ingress status
echo ""
echo "🔟 Ingress Status"

INGRESS_HOST=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

if [ -n "$INGRESS_HOST" ]; then
  echo -e "${GREEN}✅${NC} Ingress: $INGRESS_HOST"
  HEALTH_SCORE=$((HEALTH_SCORE + 1))
else
  echo -e "${YELLOW}⚠️${NC} Ingress: Not configured"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Summary
echo ""
echo "════════════════════════════════════"
echo "📊 Health Check Summary"
echo "════════════════════════════════════"
echo "Passed: $HEALTH_SCORE / $TOTAL_CHECKS"
echo "Score: $(( HEALTH_SCORE * 100 / TOTAL_CHECKS ))%"
echo "Environment: $ENVIRONMENT"
echo "Namespace: $NAMESPACE"
echo "Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════"

# Exit with appropriate code
if [ $HEALTH_SCORE -ge $((TOTAL_CHECKS * 7 / 10)) ]; then
  echo -e "${GREEN}✅ Health check PASSED${NC}"
  exit 0
else
  echo -e "${RED}❌ Health check FAILED${NC}"
  exit 1
fi
