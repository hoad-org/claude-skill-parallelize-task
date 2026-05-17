# Phase 4 Development Guide

Architecture decisions, component interactions, design patterns, and implementation notes for Phase 4 Orchestration Core.

## Overview

Phase 4 introduces the **Orchestration Core**, a central coordination layer that:
- Unifies Phase 2-3 components into coherent workflows
- Manages complete workflow lifecycle from analysis through execution
- Provides both programmatic (Python) and CLI interfaces
- Implements stateful orchestration with persistence and recovery

## Architecture Decisions

### Decision 1: Unified Orchestrator Pattern
**Why**: Single coordination hub reduces coupling between components
- **Alternative**: Event-driven architecture (rejected: adds complexity)
- **Trade-off**: Slightly more coupled, but much simpler
- **Implementation**: `WorkflowOrchestrator` class coordinates all operations

### Decision 2: Phase-Based Workflow
**Why**: Clear separation of concerns, linear progression
- **Alternative**: Directed graph of operations (rejected: over-engineered)
- **Trade-off**: Less flexible, but intuitive and predictable
- **Phases**: Analyze → Decide → Plan → Execute → Document

### Decision 3: Stage-Based Execution
**Why**: Enforces dependencies and gate policies
- **Alternative**: Free-form task execution (rejected: harder to coordinate)
- **Trade-off**: More rigid, but guarantees safety
- **Implementation**: `StageOrchestrator` class with gate policies

### Decision 4: Stateful with Persistence
**Why**: Recovery from failures, inspection, replay
- **Alternative**: Stateless (rejected: can't recover)
- **Trade-off**: More state to manage, but enables recovery
- **Implementation**: `PersistenceManager` saves state after each phase

### Decision 5: CLI-First Design
**Why**: Accessible to non-Python users, composable commands
- **Alternative**: Python API only (rejected: limits accessibility)
- **Trade-off**: Extra layer to maintain, but much more useful
- **Implementation**: `cli.py` with 6 commands

## Component Interactions

### Data Flow

```
User Input
    ↓
CLI (validate input)
    ↓
WorkflowOrchestrator (coordinate)
    ├→ ComplexityScorer (analyze)
    ├→ DecisionEngine (decide)
    ├→ ExecutionPlanner (plan)
    ├→ StageOrchestrator (execute)
    ├→ EscalationManager (recover)
    └→ StrategyDocumentGenerator (document)
    ↓
PersistenceManager (save state)
    ↓
OutputCoordinator (format)
    ↓
User Output
```

### Component Responsibilities

- **WorkflowOrchestrator**: Top-level coordination, state management
- **ComplexityScorer**: Score task parallelization potential (Phase 2)
- **DecisionEngine**: Determine strategy (Phase 2)
- **ExecutionPlanner**: Create execution plan (Phase 2)
- **StageOrchestrator**: Enforce stage gates and ordering
- **EscalationManager**: Handle failures and recovery (Phase 3)
- **StrategyDocumentGenerator**: Generate documentation (Phase 3)
- **PersistenceManager**: Load/save workflow state
- **OutputCoordinator**: Format and export results
- **DAGAnalyzer**: Analyze task dependencies
- **AgentMonitor**: Track agent execution
- **TokenBudget**: Manage resource constraints

## Design Patterns

### Pattern 1: Phases as Methods
Each phase (analyze, decide, plan, execute) is a method on WorkflowOrchestrator.

```python
class WorkflowOrchestrator:
    def analyze_workflow(self, ...): ...
    def make_decision(self, ...): ...
    def plan_execution(self, ...): ...
    def execute_workflow(self, ...): ...
```

**Benefits**:
- Clear interface
- Obvious progression
- Easy to test

### Pattern 2: Immutable Results
Each phase returns immutable result object.

```python
analysis = orch.analyze_workflow(...)  # Returns WorkflowAnalysis
decision = orch.make_decision(analysis)  # Consumes analysis, returns DecisionRecommendation
plan = orch.plan_execution(..., decision)  # Consumes decision, returns ExecutionPlan
```

**Benefits**:
- No side effects
- Easy to reason about
- Good for state management

### Pattern 3: State Persistence Hooks
After each phase, state is automatically persisted.

```python
def analyze_workflow(self, ...):
    # ... perform analysis ...
    self.persistence_manager.save_analysis(analysis)
    return analysis
```

**Benefits**:
- Recovery from interruptions
- Enables state inspection
- Supports replay

### Pattern 4: Configuration Hierarchy
4-level configuration resolution.

```
Code Defaults
    ↓
Master Config (~/.claude/parallelize-task/)
    ↓
Repo Config (.claude/parallelize-task.json)
    ↓
Environment Variables
```

**Benefits**:
- User preferences respected
- Project overrides possible
- Environment-specific settings

### Pattern 5: Error Escalation
Failures escalate through severity levels.

```
INFO (advisory)
  ↓
WARN (needs attention)
  ↓
ERROR (intervention needed)
  ↓
CRITICAL (halt execution)
```

**Benefits**:
- Proportional response
- Clear severity
- Automated recovery possible

## Performance Optimizations

### Optimization 1: Lazy Complexity Scoring
Only score parallelizable tasks.

```python
# Before: Score all tasks
for task in tasks:
    score = scorer.score_task(task)

# After: Only parallelizable tasks
for task in tasks:
    if task.parallelizable:
        score = scorer.score_task(task)
```

**Benefit**: 50% faster for mostly sequential workflows

### Optimization 2: Early Dependency Validation
Check for cycles before analysis.

```python
def analyze_workflow(self, ...):
    # Check for cycles early
    if analyzer.has_cycles():
        raise ValueError("Circular dependencies")
    
    # Continue with analysis
    ...
```

**Benefit**: Fail fast, avoid wasted analysis time

### Optimization 3: Memoized DAG Analysis
Cache DAG results for reuse.

```python
class WorkflowOrchestrator:
    def __init__(self):
        self._dag_cache = {}  # Cache DAG results
```

**Benefit**: Avoid re-analyzing same dependencies

### Optimization 4: Batch State Persistence
Save state once per workflow, not per operation.

```python
def execute_workflow(self, ...):
    # Perform all execution...
    # Save state once at end
    self.persistence_manager.save_execution(result)
```

**Benefit**: Fewer file I/O operations

## Testing Strategy

### Test Categories

1. **Unit Tests**: Individual components in isolation
2. **Integration Tests**: Components working together
3. **CLI Tests**: CLI commands and piping
4. **Performance Tests**: Scalability and timing

### Coverage Targets

- **Code**: 85%+ total coverage (currently 89.17%)
- **Path**: Happy path + error paths
- **Edge Cases**: Empty inputs, large workflows, circular deps
- **Integration**: Full pipeline workflows

### Test Organization

```
tests/
├── test_orchestrator.py          # WorkflowOrchestrator tests
├── test_stage_orchestrator.py    # Stage gate tests
├── test_cli_integration.py       # CLI command tests
├── test_persistence.py           # State persistence tests
├── test_escalation.py            # Error recovery tests
└── conftest.py                   # Shared fixtures
```

## Known Limitations

### Limitation 1: CLI Does Not Execute Agents
CLI tests mock orchestrator instead of actually executing tasks.

**Reason**: Real execution requires Phase 5 agent integration
**Workaround**: Use Python API for actual execution

### Limitation 2: Single-Thread Execution Model
Current implementation is single-threaded.

**Reason**: Simplicity, easier testing, matches CLI constraints
**Future**: Phase 5 will add async execution

### Limitation 3: Limited Recovery Strategies
Escalation supports basic recovery only.

**Reason**: Limited by Phase 3 implementation
**Future**: Enhanced recovery in Phase 5

### Limitation 4: No Advanced Monitoring
Basic monitoring only, no dashboards or alerts.

**Reason**: Out of scope for Phase 4
**Future**: Phase 5 monitoring enhancements

## Future Improvements

### Improvement 1: Async Execution
```python
async def execute_workflow_async(self, ...):
    # Execute phases in parallel where possible
    await asyncio.gather(...)
```

### Improvement 2: Advanced Recovery
```python
class AdvancedRecovery:
    def intelligent_retry(self, failed_tasks):
        # Analyze failure, modify plan, retry
        pass
```

### Improvement 3: Real-Time Monitoring
```python
class RealtimeMonitor:
    async def stream_progress(self, workflow_id):
        # Stream progress updates to client
        pass
```

### Improvement 4: Distributed Execution
```python
class DistributedOrchestrator(WorkflowOrchestrator):
    def execute_remotely(self, plan):
        # Distribute execution to multiple agents
        pass
```

## Configuration Options

### Key Configuration Settings

```json
{
  "orchestrator": {
    "persistence_path": "./orchestration_state",
    "auto_escalation": true,
    "recovery_attempts": 3,
    "state_retention_days": 30
  },
  "execution": {
    "parallel_tasks": 10,
    "batch_size": 5,
    "timeout_seconds": 3600
  },
  "decision": {
    "confidence_threshold": 0.8,
    "risk_tolerance": "medium"
  },
  "cli": {
    "default_output_format": "json",
    "default_goal": "balanced"
  }
}
```

## Security Considerations

### 1. State File Security
State files may contain sensitive information.

**Mitigation**:
- Save to restricted directory (default: `./orchestration_state`)
- Set file permissions to 0600 (owner read/write only)
- Don't commit state files to git

### 2. Configuration Secrets
Configuration may contain API keys or credentials.

**Mitigation**:
- Use environment variables for secrets
- Document as examples only (no actual values)
- Never commit real credentials

### 3. Error Messages
Error messages may expose system details.

**Mitigation**:
- Generic error messages to users
- Detailed logs for debugging (local only)
- No stack traces in output

## Deployment Checklist

Before deploying Phase 4:

- [ ] All tests pass (414 tests)
- [ ] Coverage ≥ 85% (currently 89.17%)
- [ ] Code quality checks pass (lint, format, type-check)
- [ ] Documentation complete (5 docs + SKILL.md + README.md)
- [ ] Examples work end-to-end
- [ ] CLI commands work independently and chained
- [ ] State persistence tested and working
- [ ] Error recovery tested
- [ ] Performance acceptable for 1000+ task workflows
- [ ] No sensitive data in commits

## Debugging Guide

### Enable Debug Logging
```bash
export PARALLELIZE_VERBOSE=true
export PARALLELIZE_LOG_LEVEL=DEBUG
parallelize-task analyze tasks.json
```

### Inspect State Files
```bash
# View workflow state
cat orchestration_state/workflow-001/analysis.json | jq .

# List all workflows
ls -la orchestration_state/
```

### Test Specific Component
```bash
# Test orchestrator directly
pytest tests/test_orchestrator.py::TestWorkflowOrchestrator::test_analyze_workflow -v

# Test CLI command
parallelize-task analyze tasks.json --verbose
```

### Performance Profiling
```bash
# Time analysis phase
time parallelize-task analyze tasks.json -d deps.json

# Profile with Python
python -m cProfile -s cumulative run_workflow.py
```

## Release Checklist

Phase 4 v1.0.0 Release:

- [x] All Phase 1-3 components complete
- [x] Orchestration core implemented
- [x] CLI with 6 commands
- [x] 414 tests passing, 89.17% coverage
- [x] Documentation: 5 guides + SKILL.md + README.md
- [x] Examples: 7 real-world scenarios
- [x] Performance verified up to 1000+ tasks
- [x] State persistence working
- [x] Error recovery functional
- [ ] Version bump to 1.0.0
- [ ] GitHub release created
- [ ] Package published
- [ ] Announcement sent

## Version History

### v1.0.0 (Current - Phase 4)
- Orchestration Core
- CLI Interface
- State Persistence
- Error Recovery
- 414 tests, 89.17% coverage

### v0.3.0 (Phase 3)
- Escalation Manager
- Strategy Documentation
- Agent Monitoring

### v0.2.0 (Phase 2)
- Complexity Scoring
- Decision Engine
- Execution Planning

### v0.1.0 (Phase 1)
- Task Model
- Dependency Analysis
- DAG Support

## Contact & Support

For Phase 4 issues or questions:
- Create GitHub issue: https://github.com/hoad-org/claude-skill-parallelize-task/issues
- Check documentation: docs/PHASE4_*.md
- Review examples: docs/PHASE4_EXAMPLES.md
