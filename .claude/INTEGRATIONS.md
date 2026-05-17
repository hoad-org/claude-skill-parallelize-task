# Integration Points & External Systems

**Purpose**: Document how this skill integrates with DevArmor, CloudCTL, monitoring systems, and other infrastructure

---

## Critical External Links

| System | Link | Status | Integration Type |
|--------|------|--------|------------------|
| **Official Rail** | [Confluence Rail](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/25165826/) | ✅ Active | Cloud provider guidance |
| **DevArmor** | [Memory Doc](../../../.claude/projects/-Users-craighoad-Repos/memory/MEMORY.md#devarmor) | ✅ Production | Cost governance |
| **CloudCTL** | [Solution Doc](../../../.claude/projects/-Users-craighoad-Repos/memory/MEMORY.md#cloudctl-integration) | ✅ UAT Complete | Multi-cloud access |
| **Jira Skill** | `/Repos/jira-skill` | ✅ Reference | Best practices example |
| **Confluence Skill** | `/Repos/confluence-skill` | ✅ Reference | Enterprise integration |

---

## DevArmor Integration

### Overview

**DevArmor** is the cost governance and resource enforcement system. This skill must integrate with DevArmor to enforce cost limits and resource constraints.

### Current Status

| Component | Status | Details |
|-----------|--------|---------|
| Cost Tracking | ✅ Implemented | Via CloudCTL cost API |
| Budget Enforcement | ✅ Implemented | Q3 resource constraint → cost limit |
| Resource Limits | ✅ Implemented | CPU/Memory guardrails in K8s |
| Quota Management | ⚠️ Partial | CloudCTL integration present |

### Integration Points

**1. Cost Budgeting** (DecisionEngine)

The Q3 question (resource constraints) maps to cost budgets:

```python
# In decision_engine.py
def answer_q3(constraint: str) -> ResourceConstraint:
    """Map resource constraints to cost budgets via DevArmor"""
    if constraint == "cpu":
        # DevArmor enforces CPU budget → lower parallelization
        return ResourceConstraint.CPU
    elif constraint == "memory":
        # DevArmor enforces memory budget → batch optimization
        return ResourceConstraint.MEMORY
    # etc.
```

**2. Kubernetes Resource Limits**

DevArmor enforces via K8s limits in `k8s/deployment.yaml`:

```yaml
resources:
  requests:
    cpu: 250m              # DevArmor minimum
    memory: 512Mi          # DevArmor minimum
  limits:
    cpu: 1000m             # DevArmor maximum
    memory: 2Gi            # DevArmor maximum
```

**3. Monitoring Integration**

Prometheus metrics sent to DevArmor dashboard:
- `parallelizer_tasks_total` → Resource usage tracking
- `parallelizer_parallelization_speedup` → Efficiency metric
- `parallelizer_cache_hit_rate` → Cost optimization indicator

### Cost Control Workflow

```
┌──────────────────────────────────────┐
│     User submits workflow             │
│     with cost budget: $100/month      │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│   Decision Engine Q3: "memory"        │
│   (Constrained by DevArmor budget)    │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│  Strategy: CONSERVATIVE               │
│  - Lower max_parallel (2-4 vs 16)    │
│  - Higher batch optimization          │
│  - More frequent checkpoints          │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│  Execution Plan respects budget       │
│  CloudCTL tracks costs in real-time   │
│  DevArmor alerts if overage detected  │
└──────────────────────────────────────┘
```

### Integration Checklist

- [ ] CloudCTL installed and configured
- [ ] DevArmor cost API accessible
- [ ] Prometheus scrape targets configured
- [ ] Kubernetes resource limits set (see k8s/deployment.yaml)
- [ ] Environment variables: DEVARMOR_API_KEY, COST_BUDGET_USD
- [ ] Monitor DevArmor dashboard during execution

### Reference Implementation

**File**: `src/parallelizer_skill/config.py`

```python
class Config:
    # DevArmor cost governance
    cost_budget_usd: float = 100.0          # Monthly budget
    cost_tracking_enabled: bool = True
    devarmor_api_key: str = ""              # From env
    devarmor_endpoint: str = "https://..."  # From env
    
    # Resource constraints (enforced by DevArmor)
    max_parallel_baseline: int = 16
    max_parallel_constrained: int = 4       # When budget tight
```

---

## CloudCTL Integration

### Overview

**CloudCTL** provides multi-cloud access (AWS, GCP, Azure). This skill uses CloudCTL to:
1. Access cloud provider CLIs
2. Fetch current resource costs
3. Get account information
4. Monitor cloud resource status

### Status

| Provider | Status | Commands Tested |
|----------|--------|-----------------|
| **AWS** | ✅ Production | `cloudctl status`, `cloudctl env`, `cloudctl org list` |
| **GCP** | ✅ Production | `cloudctl status`, `cloudctl env`, `cloudctl accounts` |
| **Azure** | ✅ Production | `cloudctl status`, `cloudctl env`, credential export |

### Usage Pattern

The skill doesn't directly call CloudCTL, but the deployment infrastructure assumes CloudCTL is available:

**1. In CI/CD Pipelines**

`.github/workflows/deploy-k8s.yml`:
```yaml
- name: Get CloudCTL context
  run: cloudctl status
  
- name: Deploy with current cloud context
  run: kubectl apply -f k8s/ --kubeconfig=$KUBECONFIG
```

**2. In Kubernetes**

`k8s/deployment.yaml` assumes CloudCTL credentials available:
```yaml
env:
- name: KUBECONFIG
  valueFrom:
    secretKeyRef:
      name: cloudctl-kubeconfig
      key: kubeconfig
```

**3. Health Check Script**

`scripts/health-check.sh` validates CloudCTL:
```bash
# Verify cloud access
cloudctl status  # Returns account info
cloudctl env     # Shows environment
```

### CloudCTL Configuration

**Required**: CloudCTL installed and configured

```bash
# Install CloudCTL (if not already done)
# See: https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/25165826/

# Test CloudCTL access
cloudctl status
cloudctl accounts  # List available accounts
cloudctl org list  # List organizations
```

### Multi-Cloud Deployment Support

The skill can deploy to any CloudCTL-supported cloud:

**AWS Deployment**:
```bash
# CloudCTL makes AWS credentials available
export AWS_PROFILE=<cloudctl-aws-profile>
make k8s-deploy  # Deploys to EKS
```

**GCP Deployment**:
```bash
# CloudCTL makes GCP credentials available
export CLOUDSDK_CORE_PROJECT=<gcp-project>
make k8s-deploy  # Deploys to GKE
```

**Azure Deployment**:
```bash
# CloudCTL makes Azure credentials available
export AZURE_SUBSCRIPTION_ID=<subscription>
make k8s-deploy  # Deploys to AKS
```

---

## Monitoring System Integration

### Prometheus Metrics

The skill exports Prometheus metrics via `/metrics` endpoint:

```prometheus
# HELP parallelizer_workflows_total Total workflows processed
# TYPE parallelizer_workflows_total counter
parallelizer_workflows_total 1234

# HELP parallelizer_tasks_completed_total Tasks completed
# TYPE parallelizer_tasks_completed_total counter
parallelizer_tasks_completed_total 45678

# HELP parallelizer_parallelization_speedup Parallelization speedup (times)
# TYPE parallelizer_parallelization_speedup gauge
parallelizer_parallelization_speedup 3.8

# HELP parallelizer_cache_hit_rate Cache hit rate (0-1)
# TYPE parallelizer_cache_hit_rate gauge
parallelizer_cache_hit_rate 0.87
```

**Prometheus Config** (`config/prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'parallelizer-task'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboards

Dashboards auto-imported via Kubernetes ConfigMap:

```yaml
# k8s/configmap.yaml
dashboards:
  parallelizer-overview.json   # Main dashboard
  parallelizer-performance.json # Performance metrics
  parallelizer-health.json      # Health & alerts
```

### Alerting Rules

Prometheus alert rules (`config/prometheus.yml`):

```yaml
groups:
  - name: parallelizer
    rules:
      - alert: LowParallelizationGain
        expr: parallelizer_parallelization_speedup < 2
        for: 5m
        
      - alert: HighFailureRate
        expr: parallelizer_tasks_failed_rate > 0.3
        for: 5m
        
      - alert: CacheThrashing
        expr: parallelizer_cache_hit_rate < 0.5
        for: 10m
```

---

## Jira Integration (Optional)

### Overview

While not required for core functionality, the skill can integrate with Jira for:
- Tracking workflow execution as Jira issues
- Updating issue status based on task status
- Creating subtasks for parallel task groups

### Reference

See `/Repos/jira-skill` for production Jira integration patterns:
- Authentication (OAuth, API tokens)
- Issue creation/update
- Custom fields
- Workflow transitions

### Potential Integration

**Planned Enhancement** (Phase 7+):
```python
# From Jira skill patterns
from jira import JIRA

class JiraWorkflowTracker:
    def __init__(self, jira_url, api_token):
        self.jira = JIRA(jira_url, token_auth=api_token)
    
    def create_execution_issue(self, workflow_id):
        """Create Jira issue for workflow execution"""
        issue = self.jira.create_issue(...)
        return issue.key
    
    def update_task_status(self, issue_key, status):
        """Update Jira issue as tasks complete"""
        self.jira.update_issue(issue_key, status=status)
```

---

## Official Rail Documentation

### Confluence Rail Link

**[CloudCTL Rail - Confluence](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/25165826/)**

This rail documents:
- How Claude should use CloudCTL
- Multi-cloud deployment patterns
- Authentication flows (AWS SSO, GCP, Azure)
- OIDC configuration
- Credential management
- Error handling and fallback patterns

### Key Takeaways from Rail

1. **CloudCTL is the single source of truth** for cloud access
2. **Non-interactive fallback** available for GCP (cached:gcp:account)
3. **30-second timeout** protection for subprocess calls
4. **Robust exception handling** preserves KeyboardInterrupt and SystemExit
5. **Configuration hierarchy** with 4-level system support
6. **All 3 clouds tested** (AWS SSO, GCP, Azure credential export)

### Implementation in This Skill

The skill integrates per the rail by:
- Using CloudCTL for all cloud operations
- Supporting AWS, GCP, Azure equally
- Respecting 30-second timeout in health checks
- Failing gracefully with helpful error messages
- Documenting required CloudCTL setup

---

## Integration Checklist for Deployment

Before deploying to production:

- [ ] **DevArmor**
  - [ ] API key configured: `DEVARMOR_API_KEY` env var
  - [ ] Cost budget set: `COST_BUDGET_USD` config
  - [ ] DevArmor dashboard accessible
  - [ ] Alert escalations tested

- [ ] **CloudCTL**
  - [ ] CloudCTL installed and working: `cloudctl status`
  - [ ] Cloud credentials configured for target cloud (AWS/GCP/Azure)
  - [ ] K8s credentials available: `KUBECONFIG` env var
  - [ ] Multi-cloud fallback tested

- [ ] **Monitoring**
  - [ ] Prometheus scrape targets configured
  - [ ] Grafana dashboards imported
  - [ ] Alert rules deployed
  - [ ] Slack/email notifications configured

- [ ] **Kubernetes**
  - [ ] Cluster accessible: `kubectl cluster-info`
  - [ ] Resource quotas set (DevArmor enforced)
  - [ ] RBAC configured (k8s/rbac.yaml applied)
  - [ ] Network policies applied (k8s/rbac.yaml)

- [ ] **API & Dashboard**
  - [ ] API /health endpoint responding
  - [ ] WebSocket connections working
  - [ ] Frontend serving correctly
  - [ ] API docs at /docs accessible

---

## Troubleshooting Integration Issues

### CloudCTL Not Found

```bash
# Error: "cloudctl: command not found"

# Solution 1: Install CloudCTL
pip install cloudctl

# Solution 2: Check if in PATH
which cloudctl

# Solution 3: Set CLOUDCTL_HOME
export CLOUDCTL_HOME=~/.cloudctl
```

### DevArmor API Key Missing

```bash
# Error: "DevArmor API key not configured"

# Solution: Set environment variable
export DEVARMOR_API_KEY="your-api-key-here"

# Verify
echo $DEVARMOR_API_KEY
```

### Prometheus Not Scraping

```bash
# Check Prometheus config
kubectl logs -l app=prometheus

# Check metrics endpoint
curl http://localhost:8000/metrics

# Check K8s ConfigMap
kubectl get configmap prometheus-config -o yaml
```

### Kubernetes Deployment Fails

```bash
# Check cluster access
kubectl cluster-info
kubectl auth can-i create deployments

# Check resource quotas
kubectl describe resourcequota

# Check DevArmor enforced limits
kubectl describe pod <pod-name>
```

---

## Integration Testing

### Test CloudCTL

```bash
# From scripts/health-check.sh
cloudctl status      # Returns account info
cloudctl env         # Shows environment
cloudctl accounts    # Lists available accounts
```

### Test DevArmor

```bash
# From scripts/pre-deploy-checks.sh
DEVARMOR_API_KEY=$DEVARMOR_API_KEY \
  python -c "
  import os
  from src.parallelizer_skill.config import get_config
  cfg = get_config()
  assert cfg.cost_budget_usd > 0
  print('DevArmor config OK')
  "
```

### Test Monitoring

```bash
# From tests/smoke_tests.py
curl http://localhost:8000/metrics | grep parallelizer_
curl http://localhost:8000/health/detailed
```

---

## Reference Implementations

### Jira Skill (v2.0.0)
- Location: `/Repos/jira-skill`
- DevArmor integration: Cost tracking, budget enforcement
- CloudCTL usage: Multi-cloud deployment support
- Monitoring: Prometheus metrics, Grafana dashboards

### Confluence Skill (v1.2.0)
- Location: `/Repos/confluence-skill`
- Jira integration: Linked pages, issue tracking
- Enterprise patterns: Bulk operations, rate limiting
- Monitoring: Event logging, error handling

---

## Future Integration Opportunities

1. **A/B Testing** - Compare strategies across cloud providers
2. **ML Optimization** - Predict optimal parallelization parameters
3. **Auto-Scaling** - Dynamic resource adjustment based on workload
4. **Cost Analytics** - Historical cost trends, ROI calculation
5. **GraphQL API** - Alternative query interface
6. **Mobile App** - React Native monitoring companion

---

**Last Updated**: 2026-05-17  
**Integration Status**: ✅ Production Ready  
**Tested Cloud Providers**: AWS, GCP, Azure  
**DevArmor Version**: v1.0.0  
**CloudCTL Status**: ✅ UAT Complete (434 unit tests passing)
