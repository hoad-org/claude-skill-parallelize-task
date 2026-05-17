# Claude Skill: Parallelize Task (Phase 4)

Enterprise-grade workflow orchestration and intelligent task parallelization. Complete lifecycle management from analysis through execution with state persistence, error recovery, and strategy documentation.

## Status: Phase 4 Complete ✓

- **Tests**: 414 passing (100% pass rate)
- **Coverage**: 89.17% (target: 75%)
- **Documentation**: Complete (5 guides + SKILL.md + README.md)
- **Examples**: 7 real-world scenarios
- **CLI Commands**: 6 (analyze, decide, plan, execute, document, reset)

## Features (Phase 4)

- **Workflow Orchestration** — Central coordinator for complete workflow lifecycle
- **Complexity Analysis** — Score task parallelization potential with feasibility ratings
- **Strategic Decisions** — Determine optimal strategy using Q1-Q6 decision framework
- **Execution Planning** — Create phased, staged execution plans with efficiency metrics
- **Stage Management** — Enforce execution order with configurable gate policies
- **Error Recovery** — Automatic escalation and recovery from failures
- **State Persistence** — Save and recover from workflow interruptions
- **Strategy Documentation** — Auto-generate reports in JSON, Markdown, or HTML
- **CLI Interface** — 6 composable commands for workflow automation
- **Python API** — Full programmatic access via WorkflowOrchestrator class

## Installation

### Private Index (Recommended)
```bash
export GITHUB_TOKEN=your_github_token
pip install --index-url https://__token__:${GITHUB_TOKEN}@github.com/hoad-org/python-packages-private/simple/ claude-skill-parallelize-task==1.0.0
```

### Public Index
```bash
pip install --index-url https://hoad-org.github.io/python-packages claude-skill-parallelize-task==1.0.0
```

### From Source
```bash
git clone https://github.com/hoad-org/claude-skill-parallelize-task.git
cd claude-skill-parallelize-task
pip install -e .
```

## Quick Start

### CLI (Recommended for Most Users)

Complete workflow in 5 commands:

```bash
# 1. Analyze parallelization potential
parallelize-task analyze tasks.json -d deps.json -o analysis.json

# 2. Determine strategy
parallelize-task decide analysis.json -g speed -o decision.json

# 3. Create execution plan
parallelize-task plan tasks.json -d deps.json -a analysis.json -c decision.json -o plan.json

# 4. Execute workflow
parallelize-task execute plan.json -t tasks.json -d deps.json -o execution.json

# 5. Generate documentation
parallelize-task document workflow-001 -a analysis.json -c decision.json \
  -p plan.json -e execution.json -f markdown -o strategy.md
```

### Python API

```python
from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.models import Task, TaskDependency
from parallelizer_skill.decision_engine import ParallelizationGoal

# Create orchestrator
orch = WorkflowOrchestrator()

# Define tasks
tasks = [
    Task(id="t1", name="Load Data", estimated_duration=2.0),
    Task(id="t2", name="Process A", estimated_duration=3.0),
    Task(id="t3", name="Process B", estimated_duration=3.0),
    Task(id="t4", name="Aggregate", estimated_duration=1.0),
]

# Define dependencies
deps = [
    TaskDependency("t1", "t2"),
    TaskDependency("t1", "t3"),
    TaskDependency("t2", "t4"),
    TaskDependency("t3", "t4"),
]

# Analyze workflow
analysis = orch.analyze_workflow("wf-001", tasks, deps)
print(f"Parallelizable: {len(analysis.parallelizable_tasks)} tasks")
print(f"Critical path: {' → '.join(analysis.critical_path)}")

# Determine strategy
decision = orch.make_decision("wf-001", analysis, ParallelizationGoal.SPEED)
print(f"Strategy: {decision.strategy}")
print(f"Confidence: {decision.confidence_level*100:.1f}%")

# Create execution plan
plan = orch.plan_execution(tasks, deps, decision, "wf-001")
print(f"Serial: {plan.serial_duration}s → Parallel: {plan.parallel_duration}s")
print(f"Efficiency gain: {plan.efficiency_gain:.1f}%")

# Execute workflow (requires Phase 5 agent implementation)
# result = orch.execute_workflow("wf-001", plan, executor_callback)
```

## Core Concepts

### Phase-Based Workflow

```
Analyze → Decide → Plan → Execute → Document
   ↓         ↓       ↓       ↓         ↓
  Score    Strategy  Phases  Run    Report
  Tasks    Selection  Order   Tasks  Results
```

### Task
A unit of work with:
- **ID and Name** - Unique identifier and display name
- **Duration** - Estimated execution time in seconds
- **Parallelizable** - Can run concurrently with others (boolean)
- **Priority** - Critical, High, Normal, Low
- **Resources** - Type and max concurrent instances
- **Metadata** - Custom attributes

### Dependency
Relationship between tasks:
- **Hard** — Must complete before dependent starts
- **Soft** — Preferred but not required
- **Data** — Output feeds into input

### Execution Plan
Optimal scheduling with:
- **Phases** - Groups of sequential stages
- **Stages** - Gates controlling advancement
- **Task Groups** - Tasks that run in parallel
- **Critical Path** - Longest execution path
- **Efficiency Metrics** - Speedup and gains

### State
Workflow state persisted across phases:
- **Metadata** - Workflow ID, timestamps, config
- **Analysis** - Scores, ratings, bottlenecks
- **Decision** - Strategy, confidence, recommendations
- **Plan** - Phases, stages, efficiency
- **Execution** - Status, timing, results

## Architecture (Phase 4)

```
┌─────────────────────────────────┐
│   CLI Layer (6 commands)        │
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│  WorkflowOrchestrator           │
│  (Central Coordination Hub)      │
└────┬────────┬────────┬──────────┘
     │        │        │
     ▼        ▼        ▼
  Analysis  Decision  Execution
  (Phase 2) (Phase 2) (Phase 2)
     │        │        │
     ▼        ▼        ▼
  Plan     Escalation  Stage
  (Phase 2) (Phase 3)  Gates
```

## API Reference

### WorkflowOrchestrator (Main Entry Point)

```python
from parallelizer_skill.orchestrator import WorkflowOrchestrator

orch = WorkflowOrchestrator(persistence_path="./state")

# Phase 1: Analyze
analysis = orch.analyze_workflow(
    workflow_id="wf-001",
    tasks=[...],
    dependencies=[...]
)

# Phase 2: Decide
decision = orch.make_decision(
    workflow_id="wf-001",
    analysis=analysis,
    goal=ParallelizationGoal.SPEED
)

# Phase 3: Plan
plan = orch.plan_execution(
    tasks=[...],
    dependencies=[...],
    decision=decision,
    workflow_id="wf-001"
)

# Phase 4: Execute
result = orch.execute_workflow(
    workflow_id="wf-001",
    plan=plan,
    agent_executor=executor_callback
)

# Phase 5: Document
doc = orch.generate_strategy_document(
    workflow_id="wf-001",
    analysis=analysis,
    decision=decision,
    plan=plan,
    execution_result=result
)

# Error Recovery
recovery = orch.handle_failure(
    workflow_id="wf-001",
    error=exception,
    plan=plan,
    execution_result=result
)
```

### StageOrchestrator (Stage Gate Enforcement)

```python
from parallelizer_skill.stage_orchestrator import StageOrchestrator, GatePolicy

stage_orch = StageOrchestrator()

# Define stages
stage_orch.add_stage(
    stage_number=1,
    name="Data Preparation",
    tasks=["task1", "task2"],
    gate_policy=GatePolicy.ALL_PASS
)

# Manage execution
stage_orch.start_stage(1)
stage_orch.update_task_status(1, "task1", "agent-1", "complete")
stage_orch.complete_stage(1)

# Check advancement
if stage_orch.check_stage_passed(1):
    stage_orch.start_stage(2)
```

## Examples

### Example 1: Simple Analysis

Analyze a 3-task pipeline:

```bash
parallelize-task analyze tasks.json -d deps.json

# Output:
# {
#   "total_tasks": 3,
#   "parallelizable_tasks": 2,
#   "critical_path": ["fetch_users", "merge_data"],
#   "critical_path_duration": 7.0,
#   "total_serial_duration": 11.0
# }
```

### Example 2: Speed Optimization

Complete pipeline optimized for speed:

```bash
# Analyze
parallelize-task analyze tasks.json -d deps.json -o analysis.json

# Optimize for speed
parallelize-task decide analysis.json -g speed -o decision.json

# View plan
parallelize-task plan tasks.json -d deps.json -a analysis.json \
  -c decision.json -f text

# Output:
# Serial: 60s → Parallel: 40s (33% efficiency gain)
# Phase 1: 5s
# Phase 2: 15s (4 parallel tasks)
# Phase 3: 10s (2 parallel tasks)
# Phase 4: 10s
```

### Example 3: Cost Optimization

Minimize resource usage:

```bash
# Analyze
parallelize-task analyze tasks.json -d deps.json -o analysis.json

# Optimize for cost
parallelize-task decide analysis.json -g cost -o decision.json

# View decision
cat decision.json | jq '.strategy, .recommended_batch_size'
# "sequential_batching"
# 2
```

### Example 4: Complex Workflow (Python)

```python
from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.models import Task, TaskDependency
from parallelizer_skill.decision_engine import ParallelizationGoal

# Create many parallel tasks with resource constraints
orch = WorkflowOrchestrator()
tasks = [Task(id=f"t{i}", name=f"Task {i}") for i in range(20)]
deps = [TaskDependency(f"t{i}", f"t{i+5}") for i in range(15)]

# Analyze
analysis = orch.analyze_workflow("wf", tasks, deps)
print(f"Bottlenecks: {analysis.sequential_bottlenecks}")

# Decide with cost optimization
decision = orch.make_decision("wf", analysis, ParallelizationGoal.COST)
print(f"Batch size: {decision.recommended_batch_size}")

# Plan
plan = orch.plan_execution(tasks, deps, decision, "wf")
print(f"Efficiency: {plan.efficiency_gain:.1f}%")
```

See `docs/PHASE4_EXAMPLES.md` for 7 complete real-world examples.

## Testing

```bash
# Run all tests (414 tests)
pytest

# With coverage report
pytest --cov=src/parallelizer_skill --cov-report=html
# Coverage: 89.17% (target: 75%)

# Specific test categories
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m performance   # Performance tests

# Run specific test file
pytest tests/test_orchestrator.py -v
```

## Architecture (Phase 4)

```
src/parallelizer_skill/
├── __init__.py                # Exports
├── models.py                  # Data models
├── orchestrator.py            # WorkflowOrchestrator (NEW Phase 4)
├── stage_orchestrator.py      # StageOrchestrator (NEW Phase 4)
├── cli.py                     # CLI interface (NEW Phase 4)
├── complexity.py              # Scoring (Phase 2)
├── decision_engine.py         # Strategy (Phase 2)
├── execution_planner.py       # Planning (Phase 2)
├── escalation.py              # Recovery (Phase 3)
├── strategy_document.py       # Documentation (Phase 3)
├── persistence.py             # State persistence
├── dag_analyzer.py            # Dependency analysis
├── output_coordinator.py      # Output formatting
├── agent_monitor.py           # Execution tracking
├── callbacks.py               # Progress callbacks
├── token_budget.py            # Resource control
└── config.py                  # Configuration

tests/
├── test_orchestrator.py           # Phase 4
├── test_stage_orchestrator.py     # Phase 4
├── test_cli_integration.py        # Phase 4
├── test_escalation.py             # Phase 3
├── test_strategy_document.py      # Phase 3
├── test_complexity.py             # Phase 2
├── test_decision_engine.py        # Phase 2
├── test_execution_planner.py      # Phase 2
└── ... (11 more test files)
```

## Performance (Phase 4)

### Time Complexity
- **Analyze**: O(V + E) for V tasks and E dependencies
- **Decide**: O(V) for complexity scoring
- **Plan**: O(V²) worst-case for topological sort
- **Execute**: O(V) for stage management

### Scalability
- **Tested**: 1000+ task workflows
- **Depth**: 100+ level dependency chains
- **Concurrency**: Multiple parallel phases

### Benchmarks
| Operation | 100 Tasks | 1000 Tasks |
|-----------|-----------|-----------|
| Analyze   | 50ms      | 500ms     |
| Decide    | 10ms      | 10ms      |
| Plan      | 100ms     | 1000ms    |
| Execute   | Variable  | Variable  |

## Documentation

### User Guides
- **[PHASE4_CLI_GUIDE.md](docs/PHASE4_CLI_GUIDE.md)** — CLI commands, options, workflows
- **[PHASE4_EXAMPLES.md](docs/PHASE4_EXAMPLES.md)** — 7 real-world usage examples
- **[SKILL.md](SKILL.md)** — Feature overview and quick start

### Developer Guides
- **[PHASE4_ARCHITECTURE.md](docs/PHASE4_ARCHITECTURE.md)** — Technical architecture and design
- **[PHASE4_ORCHESTRATOR.md](docs/PHASE4_ORCHESTRATOR.md)** — Python API reference
- **[PHASE4_INTEGRATION_TESTS.md](docs/PHASE4_INTEGRATION_TESTS.md)** — Test suite documentation
- **[.claude/PHASE4.md](.claude/PHASE4.md)** — Development guide and decisions

## Requirements

- Python 3.12+
- NetworkX 3.2+
- Pydantic 2.5+

## Project Status

### Phase 1 ✓ (Complete)
- Task models and data structures
- Dependency analysis
- DAG support with NetworkX

### Phase 2 ✓ (Complete)
- Complexity scoring
- Decision engine (Q1-Q6)
- Execution planning

### Phase 3 ✓ (Complete)
- Escalation manager (error recovery)
- Strategy documentation
- Agent monitoring

### Phase 4 ✓ (Complete - Current)
- Orchestration core
- CLI interface (6 commands)
- State persistence
- Stage gate enforcement
- 414 tests, 89.17% coverage

### Phase 5 (Future)
- Real agent execution
- Async/await execution
- Advanced monitoring and dashboards
- Multi-agent coordination

## License

MIT

## Support

- **Issues**: https://github.com/hoad-org/claude-skill-parallelize-task/issues
- **Documentation**: See docs/ directory
- **Examples**: See docs/PHASE4_EXAMPLES.md
- **Development**: See .claude/PHASE4.md
