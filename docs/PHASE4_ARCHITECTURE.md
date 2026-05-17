# Phase 4 Architecture - Orchestration Core

## Overview

Phase 4 introduces the **Orchestration Core**, a central coordination layer that ties together all Phase 2-3 components into a unified workflow engine. The orchestrator manages the complete lifecycle of parallelization workflows from analysis through execution and recovery.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLI Layer (Phase 4)                           │
│  6 Commands: analyze, decide, plan, execute, document, reset   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│              WorkflowOrchestrator (Central Hub)                  │
│  • orchestrator.py: Main orchestration coordinator              │
│  • stage_orchestrator.py: Stage gate enforcement                │
└─────┬───────────────┬──────────────┬──────────────┬──────────────┘
      │               │              │              │
      ▼               ▼              ▼              ▼
┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐
│Complexity    │ │Decision    │ │Execution   │ │Escalation      │
│Scorer        │ │Engine      │ │Planner     │ │Manager         │
│(Phase 2)     │ │(Phase 2)   │ │(Phase 2)   │ │(Phase 3)       │
└──────────────┘ └────────────┘ └────────────┘ └────────────────┘
      │               │              │              │
      └───────────────┴──────────────┴──────────────┘
                      │
                      ▼
            ┌────────────────────┐
            │ Supporting Services│
            ├────────────────────┤
            │ Persistence Mgr    │ (State)
            │ Output Coordinator │ (Documentation)
            │ Token Budget       │ (Resource Control)
            │ DAG Analyzer       │ (Dependency Analysis)
            │ Agent Monitor      │ (Execution Tracking)
            └────────────────────┘
```

## Core Components

### WorkflowOrchestrator
Central coordination hub that manages the complete workflow lifecycle.

**Key Methods:**
- `analyze_workflow()` - Analyze task complexity and dependencies
- `make_decision()` - Determine optimal parallelization strategy
- `plan_execution()` - Create phased execution plan
- `execute_workflow()` - Run the execution plan
- `generate_strategy_document()` - Document the workflow strategy
- `handle_failure()` - Manage failures and recovery

**State Management:**
- Maintains workflow state throughout execution
- Tracks analysis, decision, planning, and execution phases
- Persists state to disk for recovery
- Manages workflow metadata and timestamps

### StageOrchestrator
Enforces stage gate policies and manages sequential execution of stages.

**Key Methods:**
- `add_stage()` - Define execution stages
- `start_stage()` - Initialize a stage (checks dependencies)
- `update_task_status()` - Track task progress
- `check_stage_ready()` - Verify all tasks complete
- `check_stage_passed()` - Verify stage passes gate policy
- `complete_stage()` - Mark stage as finished

**Gate Policies:**
- `ALL_PASS` - All tasks must succeed
- `ALL_COMPLETE` - All tasks must finish (pass or fail)
- `MAJORITY` - 80% of tasks must pass

## Workflow Execution Flow

```
┌─────────────┐
│  Workflow   │ (Tasks + Dependencies)
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ 1. ANALYZE Phase     │
│ ├─ Score complexity  │
│ └─ Analyze DAG       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 2. DECIDE Phase      │
│ ├─ Answer Q1-Q6      │
│ └─ Get recommendation│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 3. PLAN Phase        │
│ ├─ Create phases     │
│ └─ Define stages     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 4. EXECUTE Phase     │
│ ├─ Run stages        │
│ ├─ Enforce gates     │
│ └─ Track progress    │
└──────┬───────────────┘
       │ (Failure)
       ├──────────────────────┐
       │                      ▼
       │            ┌──────────────────┐
       │            │ ESCALATE Phase   │
       │            │ ├─ Assess        │
       │            │ ├─ Recover       │
       │            │ └─ Re-execute    │
       │            └──────────────────┘
       │
       ▼
┌──────────────────────┐
│ 5. DOCUMENT Phase    │
│ ├─ Generate strategy │
│ ├─ Export results    │
│ └─ Save analysis     │
└──────────────────────┘
```

## Integration Points

### Phase 2 Components (Decision & Planning)
- **ComplexityScorer**: Scores each task's parallelization potential
- **DecisionEngine**: Answers Q1-Q6 questions to determine strategy
- **ExecutionPlanner**: Creates phased execution plan

### Phase 3 Components (Resilience)
- **EscalationManager**: Handles failures and recovery
- **StrategyDocumentGenerator**: Generates strategy documentation

### Supporting Services
- **PersistenceManager**: Loads/saves workflow state
- **OutputCoordinator**: Formats and exports results
- **DAGAnalyzer**: Analyzes task dependencies
- **AgentMonitor**: Tracks agent execution
- **TokenBudget**: Manages resource constraints

## State Management & Persistence

### Workflow State
Orchestrator maintains complete workflow state including:
- Workflow metadata (id, timestamps, configuration)
- Analysis results (scores, ratings, bottlenecks)
- Decision recommendation (strategy, goal, confidence)
- Execution plan (phases, groups, efficiency metrics)
- Execution results (status, outcomes, timing)
- Recovery state (escalation level, attempts, recovery actions)

### State Persistence
- Automatically saves after each phase
- Persists to configurable location (default: `orchestration_state/`)
- Supports recovery from interrupted workflows
- Enables state inspection and debugging

### State File Structure
```
orchestration_state/
├── workflow-{id}/
│   ├── metadata.json
│   ├── analysis.json
│   ├── decision.json
│   ├── plan.json
│   ├── execution.json
│   └── recovery.json
```

## Error Handling & Recovery

### Error Detection
- Validates input tasks and dependencies
- Checks for circular dependencies
- Detects resource conflicts
- Monitors execution for failures

### Recovery Mechanisms
1. **Assessment** - Analyze failure root cause
2. **Escalation** - Determine escalation level (INFO → CRITICAL)
3. **Recovery** - Apply recovery strategy
4. **Re-execution** - Attempt workflow restart with modifications

### Escalation Levels
- **INFO**: Advisory, no action needed
- **WARN**: Warning, monitor situation
- **ERROR**: Error occurred, requires intervention
- **CRITICAL**: Critical failure, halt execution

## Configuration Integration

### 4-Level Configuration Hierarchy
1. **Code Defaults** - Built-in defaults
2. **Master Config** - `~/.claude/parallelize-task/`
3. **Repo Config** - `.claude/parallelize-task.json`
4. **Environment Variables** - Override anything

### Configuration Options
- Persistence path
- Output format (JSON/text)
- Logging level
- Performance thresholds
- Resource constraints
- Recovery policies

## Performance Characteristics

### Time Complexity
- **Analysis**: O(V + E) for V tasks, E dependencies
- **Decision**: O(V) for scoring, O(1) for strategy
- **Planning**: O(V²) worst-case topological sort
- **Execution**: O(V) for stage management

### Space Complexity
- **State Storage**: O(V + E) for task/dependency graphs
- **Persistence**: ~1KB per task in state files
- **Memory**: ~1MB for workflows with 1000+ tasks

### Scalability
- Tested with 1000+ task workflows
- Handles deep dependency chains (100+ levels)
- Supports complex resource constraints
- Efficient state persistence

## Design Patterns

### Pattern: Phase-Based Workflow
Breaks complex operations into distinct phases:
1. Analyze (understand problem)
2. Decide (determine strategy)
3. Plan (create schedule)
4. Execute (run workflow)
5. Document (record results)

### Pattern: Stage Gates
Enforces execution order with configurable success criteria:
- Gate policies control stage advancement
- Failed tasks recorded and analyzed
- Recovery possible with modified plans

### Pattern: Stateful Orchestration
Maintains complete state throughout lifecycle:
- Enables recovery from interruptions
- Supports state inspection and debugging
- Allows workflow resumption

### Pattern: Separated Concerns
Each component has single responsibility:
- CLI: Input/output handling
- Orchestrator: Workflow coordination
- Phase components: Specific operations
- Supporting services: Cross-cutting concerns

## Configuration Example

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
  }
}
```

## Next Steps

- See `PHASE4_ORCHESTRATOR.md` for detailed API reference
- See `PHASE4_CLI_GUIDE.md` for CLI usage
- See `PHASE4_EXAMPLES.md` for real-world examples
- See `PHASE4_INTEGRATION_TESTS.md` for test coverage
