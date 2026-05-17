# System Architecture Overview

**Purpose**: Understand the parallelization system design, components, and data flow

---

## High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                              │
│  (Tasks + Dependencies JSON, Parallelization Goal)              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1-3: ANALYSIS                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Models     │  │  Complexity  │  │ Decision Engine (Q1-6)│ │
│  │ (Pydantic)   │  │   Scorer     │  │ Questionnaire        │ │
│  │              │  │              │  │ → Strategy Selection │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 4: ORCHESTRATION                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ DAG Analyzer │  │ Execution    │  │ WorkflowOrchestrator │ │
│  │ (Topological)│  │ Planner      │  │ (Coordinator)        │ │
│  │              │  │              │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 5: OPTIMIZATION                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Decision     │  │ Analysis     │  │ Performance Manager  │ │
│  │ Cache (LRU)  │  │ Cache (LRU)  │  │ + Monitoring         │ │
│  │ (3600s TTL)  │  │ (7200s TTL)  │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 6: DEPLOYMENT                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ REST API     │  │ Web Dashboard│  │ Kubernetes + Helm    │ │
│  │ (FastAPI)    │  │ (Vue.js 3)   │  │ Orchestration        │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTION OUTPUT                              │
│  (ExecutionResult, Metrics, Events, WebSocket Updates)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Layer 1: Data Models (models.py)

**Core Data Structures**:
```python
Task                      # Unit of work (parallelizable, duration, resources)
TaskDependency           # Hard/Soft/Data/Resource dependencies
TaskPriority             # HIGH/MEDIUM/LOW priority levels
TaskStatus               # PENDING/RUNNING/COMPLETED/FAILED/SKIPPED
ExecutionStatus          # Overall workflow status

WorkflowAnalysis         # Result of analysis phase (complexity, feasibility)
ComplexityScore          # Per-task complexity metrics
FeasibilityRating        # Feasibility assessment result

DecisionContext          # Q1-Q6 responses for decision engine
DecisionRecommendation   # Strategy output (aggressive/conservative/moderate)

ExecutionPlan            # DAG-based execution phases
ExecutionResult          # Final execution metrics
```

**Key Principle**: All data is Pydantic models with validation.

---

### Layer 2: Configuration (config.py)

**4-Level Hierarchy** (lowest to highest priority):
```
Level 1: Code Defaults
  ↓ (can be overridden by)
Level 2: Master Config (~/.claude/parallelizer-task/)
  ↓ (can be overridden by)
Level 3: Repo Config (.claude/parallelizer-task.json)
  ↓ (can be overridden by)
Level 4: Environment Variables
```

**Example Usage**:
```python
config = get_config()
cache_ttl = config.cache_ttl        # From hierarchy above
```

---

### Layer 3: Decision Engine (decision_engine.py)

**Q1-Q6 Questionnaire**:

| Question | Purpose | Response |
|----------|---------|----------|
| Q1 | Parallelization goal | PERFORMANCE / COST / RELIABILITY |
| Q2 | Task complexity | SIMPLE / MODERATE / COMPLEX |
| Q3 | Resource constraints | NONE / CPU / MEMORY / NETWORK |
| Q4 | Dependency density | SPARSE / MODERATE / DENSE |
| Q5 | Failure tolerance | FAIL_FAST / RETRY / FALLBACK |
| Q6 | Priority metric | SPEED / COST / RELIABILITY |

**Output**: DecisionRecommendation with:
- Strategy type (aggressive/conservative/moderate)
- Max parallel tasks (2-256)
- Batch size
- Retry count
- Checkpoint interval
- Monitoring intensity

---

### Layer 4: Complexity & Scoring (complexity.py)

**Scoring Factors**:
```
Duration Score        (30s→100, 1h→20)
Parallelizability     (bool: 100 if parallel, 30 if not)
Resource Requirements (none→100, network→70, gpu→40)
Concurrency Limits    (per max_concurrent setting)
Dependency Complexity (0 deps→100, 10+ deps→20)
```

**Classification**:
```
Score ≥95  → TRIVIAL
Score ≥80  → SIMPLE
Score ≥50  → MODERATE
Score ≥25  → COMPLEX
Score <25  → VERY_COMPLEX
```

**Feasibility Assessment**:
```
HIGHLY_FEASIBLE  (85+ score, 0 risk factors)
FEASIBLE         (65+ score, ≤1 risk factors)
CHALLENGING      (40+ score, ≤2 risk factors)
HIGH_RISK        (20+ score, ≤3 risk factors)
INFEASIBLE       (<20 score or ≥4 risk factors)
```

---

### Layer 5: Orchestration (orchestrator.py)

**Workflow Coordination**:

```python
class WorkflowOrchestrator:
    def analyze_workflow(tasks, dependencies) → WorkflowAnalysis
    def generate_strategy(goal, analysis) → DecisionRecommendation
    def plan_execution(recommendation) → ExecutionPlan
    def execute_workflow(plan) → ExecutionResult
```

**ExecutionPlan Structure**:
```
ExecutionPlan
├── Phases[]              # Sequential execution phases
│   ├── TaskGroups[]      # Parallel groups within phase
│   │   ├── Tasks[]       # Parallelizable tasks
│   │   ├── Duration estimate
│   │   └── Resource needs
│   └── Phase duration
└── Metadata (timestamps, IDs)
```

---

### Layer 6: DAG Analysis (dag_analyzer.py)

**Graph Operations**:
```python
analyze_dependencies(tasks, dependencies) → DAG
topological_sort(dag) → ExecutionPhases
detect_cycles(dag) → bool
find_critical_path(dag) → Path
```

**Topological Sort**:
- Groups independent tasks into phases
- Respects Hard/Soft/Data/Resource dependencies
- Calculates critical path (longest dependency chain)
- Identifies bottlenecks

---

### Layer 7: Performance Optimization (performance.py)

**Caching Strategy**:
```
DecisionCache          # LRU cache, 3600s TTL, max 1000 entries
  → Caches decision engine results
  → Hit rate: >90% for repeated decisions

AnalysisCache          # LRU cache, 7200s TTL, max 500 entries
  → Caches complexity analysis results
  → Memoization: 3-100x speedup on repeated queries

Decorators:
  @memoize_decision    # Cache decision engine calls
  @memoize_analysis    # Cache analysis calls
  @memoize_planning    # Cache execution planning
```

**Performance Manager**:
```python
estimate_speedup()     # Estimate parallelization gain (2-8x)
optimize_batch_size()  # Recommend batch size (1-256)
calculate_metrics()    # Collect performance stats
```

---

### Layer 8: Monitoring (monitoring.py)

**Metrics Collection**:
```python
WorkflowMetrics
├── Total duration
├── Phases completed/failed
├── Tasks completed/failed
├── Parallelization speedup (2-8x)
└── Resource utilization

PhaseMetrics
├── Per-phase duration
├── Success rates
└── Bottleneck detection
```

**Event Logging** (39 event types):
```
INFO           # Normal operations
WARNING        # Potential issues
ERROR          # Failures requiring attention
CRITICAL       # System degradation
```

**Alert System** (6 alert types):
```
PERFORMANCE_DEGRADATION    # Speedup <2x
HIGH_FAILURE_RATE          # >30% tasks failed
EXCESSIVE_ESCALATIONS      # >5 escalations
CACHE_THRASHING            # Hit rate <50%
RESOURCE_EXHAUSTION        # >90% utilization
HEALTH_CHECK_FAILED        # System unhealthy
```

**Health Monitoring**:
```
HEALTHY       (all systems nominal)
DEGRADED      (some performance issues)
UNHEALTHY     (critical failures)
```

---

### Layer 9: REST API (api.py)

**27 Endpoints** organized by function:

**Health** (2):
- GET /health → HealthCheckResponse
- GET /health/detailed → DetailedHealthResponse

**Workflows** (4):
- POST /workflows → Create workflow
- GET /workflows → List workflows
- GET /workflows/{id} → Get workflow
- DELETE /workflows/{id} → Delete workflow

**Analysis** (2):
- POST /analyze → Analyze workflow
- GET /analyze/{id} → Get analysis result

**Decisions** (2):
- POST /decide → Generate strategy
- GET /decide/{id} → Get decision

**Execution** (3):
- POST /execute → Execute workflow
- GET /execute/{id} → Get execution status
- GET /execute/{id}/metrics → Get execution metrics

**Monitoring** (2):
- GET /metrics → Prometheus metrics
- GET /alerts → Active alerts

**Performance** (2):
- GET /performance/stats → Performance statistics
- GET /performance/cache → Cache statistics

**WebSocket** (3):
- /ws/workflows/{id} → Real-time workflow updates
- /ws/metrics → Real-time metrics stream
- /ws/alerts → Real-time alerts stream

---

### Layer 10: Web Dashboard (frontend/)

**7 Vue.js Pages**:

| Page | Purpose | Features |
|------|---------|----------|
| Dashboard | Overview | Metrics summary, active alerts, workflows count |
| Workflows | CRUD | Create/list/view/delete workflows, dependency viz |
| Analysis | Results | Complexity heatmaps, feasibility ratings, warnings |
| Decisions | Strategies | Strategy comparison, parameter recommendations |
| Execution | Monitor | Live task progress, phase tracking, metrics |
| Monitoring | Health | System health, component status, event log |
| Performance | Optimization | Cache stats, hit rates, optimization gains |

**State Management** (Pinia):
```
WorkflowStore        # Workflows, analyses, decisions
MonitoringStore      # Metrics, alerts, events
```

**Services**:
```
APIService          # Axios HTTP client for REST API
WebSocketService    # Real-time updates via WebSocket
```

---

## Data Flow Example

### Scenario: Analyze and Execute a 10-Task Workflow

```
1. USER INPUT
   Tasks: [t0, t1, ..., t9]
   Dependencies: [t0→t1, t1→t2, t2→{t3,t4}, ...]
   Goal: PERFORMANCE

2. ANALYSIS PHASE
   ComplexityScorer.score_task() → 10 ComplexityScore objects
   DAGAnalyzer.analyze() → DAG representation
   WorkflowAnalysis created

3. DECISION PHASE
   DecisionEngine.answer_q1() → PERFORMANCE
   DecisionEngine.answer_q2() → MODERATE
   DecisionEngine.answer_q3() → NONE
   DecisionEngine.answer_q4() → SPARSE
   DecisionEngine.answer_q5() → FAIL_FAST
   DecisionEngine.answer_q6() → SPEED
   
   DecisionEngine.make_decision() → AGGRESSIVE strategy
   Result: max_parallel=16, batch_size=16, retry=0

4. PLANNING PHASE
   ExecutionPlanner.create_execution_plan()
   → Phase 1: [t0] (1 task)
   → Phase 2: [t1, t2] (2 parallel tasks)
   → Phase 3: [t3, t4, t5] (3 parallel tasks)
   → Phase 4: [t6..t9] (4 parallel tasks)
   
   Expected speedup: ~4x (4 phases vs 10 serial)

5. EXECUTION PHASE
   WorkflowOrchestrator.execute_workflow(plan)
   Metrics collected: duration, parallelization gain, resource usage
   Events logged: phase starts/stops, task completions, alerts

6. OUTPUT
   ExecutionResult: success=true, speedup=3.8x, duration=2.4s
   WebSocket updates sent to dashboard in real-time
   Metrics recorded for future ML optimization
```

---

## Key Algorithms

### Topological Sort (O(V + E))
```
1. Build in-degree count for each task
2. Queue all tasks with in-degree 0
3. Process queue:
   - Add task to current phase
   - Decrement in-degree of dependents
   - Add new zero-degree tasks to next phase
4. Repeat until queue empty
```

**Result**: Minimum number of phases (critical path length)

### Complexity Scoring (O(N))
```
1. Calculate 5 factors (duration, parallelizable, resources, concurrency, deps)
2. Average the factors → composite score
3. Classify: TRIVIAL/SIMPLE/MODERATE/COMPLEX/VERY_COMPLEX
4. Assess feasibility based on score + risk factors
```

**Result**: ComplexityScore with recommendations

### Decision Engine (O(1))
```
1. Answer Q1-Q6 based on user input or analysis
2. Map answers to decision rules
3. Determine strategy: AGGRESSIVE/MODERATE/CONSERVATIVE
4. Calculate parameters:
   - max_parallel_tasks: 2-256 based on complexity + goal
   - batch_size: matches max_parallel or 50% for cost-focused
   - retry_count: 0-5 based on failure tolerance
   - checkpoint_interval: 1-100 based on complexity
```

**Result**: DecisionRecommendation ready for execution

---

## Module Dependencies

```
models.py              (no dependencies)
    ↓
config.py            (uses models)
decision_engine.py   (uses models, config)
complexity.py        (uses models, config, DependencyType)
    ↓
dag_analyzer.py      (uses models)
orchestrator.py      (uses models, complexity, dag_analyzer, decision_engine)
    ↓
performance.py       (uses models, orchestrator)
monitoring.py        (uses models, performance)
    ↓
api.py              (uses all above, FastAPI)
    ↓
cli.py              (uses orchestrator, models)
```

---

## Testing Architecture

```
tests/
├── unit/
│   ├── test_models.py              → Pydantic validation
│   ├── test_config.py              → 4-level hierarchy
│   ├── test_complexity.py          → Scoring algorithms
│   ├── test_decision_engine.py     → Q1-Q6 logic
│   ├── test_dag_analyzer.py        → Topological sort
│   └── [15+ more unit tests]       → Coverage >85%
│
├── integration/
│   ├── test_end_to_end_workflows.py    → Full pipelines
│   └── test_cross_phase_integration.py → Component interaction
│
├── performance_benchmarks.py       → 32 benchmark cases
├── smoke_tests.py                  → Production checks
├── load_tests.py                   → Concurrency (10-200 req)
└── security_tests.py               → Security validations
```

**Coverage**: 89.78% (559 tests, >85% required)

---

## Design Principles

1. **Separation of Concerns**: Each module has single responsibility
2. **Testability**: All components independently testable
3. **Scalability**: Stateless services → horizontal scaling
4. **Observability**: Comprehensive logging, metrics, alerts
5. **Configuration**: 4-level hierarchy for flexibility
6. **Type Safety**: Pydantic models + MyPy strict checking
7. **Error Handling**: Explicit error types, recovery mechanisms
8. **Performance**: Caching, memoization, batch optimization

---

## Performance Characteristics

| Operation | Time | Cache | Notes |
|-----------|------|-------|-------|
| Decision engine | <1ms | ✅ LRU 3600s | Cached by input |
| Complexity analysis | <50ms | ✅ LRU 7200s | Cached by task set |
| DAG analysis (100 tasks) | <500ms | ❌ | Depends on dependency density |
| Execution planning | <100ms | ✅ Memoized | Cached by strategy |
| Orchestration overhead | <10ms | ❌ | Per workflow |
| API request | <100ms | ❌ | Depends on operation |

**Parallelization Speedup**: 2-8x (depends on dependency density)

---

## Configuration Defaults

```python
# Performance
cache_ttl = 3600              # Cache time-to-live (seconds)
cache_max_size = 1000         # Max cache entries
max_parallel_tasks = 256      # Maximum parallelizable tasks

# Complexity
min_complexity_score = 0      # Minimum score
max_complexity_score = 100    # Maximum score

# Monitoring
alert_cooldown = 60           # Alert deduplication (seconds)
max_events = 10000            # Event buffer size

# Execution
default_retry_count = 0       # Default retries
default_timeout = 3600        # Task timeout (seconds)
```

---

## Integration Points

- **Kubernetes**: Deployment, scaling, health checks
- **Prometheus**: Metrics collection via /metrics endpoint
- **Grafana**: Dashboard visualization
- **CloudCTL**: Multi-cloud provider integration
- **DevArmor**: Cost governance, resource enforcement
- **Jira**: Issue tracking integration (optional)

---

**Last Updated**: 2026-05-17  
**Architecture Version**: 1.1.0  
**Diagrams Format**: ASCII art (SVG available in docs/)
