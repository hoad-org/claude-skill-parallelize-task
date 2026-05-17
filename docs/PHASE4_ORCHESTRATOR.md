# Phase 4 Orchestrator API Reference

Complete reference for the WorkflowOrchestrator and StageOrchestrator classes.

## WorkflowOrchestrator

Central coordination hub for parallelization workflows.

### Initialization

```python
from parallelizer_skill.orchestrator import WorkflowOrchestrator

# Create orchestrator with default persistence
orch = WorkflowOrchestrator()

# Create with custom persistence path
orch = WorkflowOrchestrator(persistence_path="/path/to/state")
```

### analyze_workflow()

Analyze a workflow's parallelization potential.

```python
analysis = orch.analyze_workflow(
    workflow_id="workflow-001",
    tasks=[task1, task2, task3],
    dependencies=[dep1, dep2]
)
```

**Parameters:**
- `workflow_id` (str): Unique workflow identifier
- `tasks` (List[Task]): Tasks to analyze
- `dependencies` (List[TaskDependency]): Task dependencies

**Returns:** `WorkflowAnalysis` with:
- `complexity_scores`: Dict of task_id -> complexity score (0-1)
- `feasibility_ratings`: Dict of task_id -> feasibility ("high"/"medium"/"low")
- `critical_path`: List of task IDs on critical path
- `critical_path_duration`: Total duration of critical path
- `total_serial_duration`: Time if all tasks run sequentially
- `parallelizable_tasks`: Task IDs that can run in parallel
- `sequential_bottlenecks`: Task IDs that are sequential
- `resource_conflicts`: Detected resource constraints
- `warnings`: List of issues found

### make_decision()

Determine optimal parallelization strategy.

```python
decision = orch.make_decision(
    workflow_id="workflow-001",
    analysis=analysis,
    goal=ParallelizationGoal.SPEED
)
```

**Parameters:**
- `workflow_id` (str): Workflow identifier
- `analysis` (WorkflowAnalysis): Result from analyze_workflow()
- `goal` (ParallelizationGoal): Optimization goal
  - `SPEED`: Minimize execution time
  - `COST`: Minimize resource cost
  - `RELIABILITY`: Maximize success probability
  - `BALANCED`: Balance all factors

**Returns:** `DecisionRecommendation` with:
- `strategy`: Recommended parallelization strategy
- `questions_answered`: Dict of Q1-Q6 answers
- `confidence_level`: Confidence in recommendation (0-1)
- `recommended_batch_size`: Suggested task batch size
- `monitoring_intensity`: Monitoring level ("low"/"medium"/"high")
- `risk_factors`: Identified risks

### plan_execution()

Create execution plan from tasks and decision.

```python
plan = orch.plan_execution(
    tasks=tasks,
    dependencies=dependencies,
    decision=decision,
    workflow_id="workflow-001"
)
```

**Parameters:**
- `tasks` (List[Task]): Tasks to plan
- `dependencies` (List[TaskDependency]): Task dependencies
- `decision` (DecisionRecommendation): Strategy from make_decision()
- `workflow_id` (str): Workflow identifier

**Returns:** `ExecutionPlan` with:
- `id`: Plan identifier
- `total_tasks`: Number of tasks
- `serial_duration`: Sequential execution time
- `parallel_duration`: Parallel execution time
- `efficiency_gain`: Speedup percentage (0-100)
- `phases`: List of ExecutionPhase
- `critical_path`: Task IDs on critical path
- `parallelizable_groups`: Task groups that run together
- `resource_conflicts`: Detected conflicts
- `safety_issues`: Issues found during planning
- `optimization_notes`: Human-readable notes

### execute_workflow()

Run the execution plan.

```python
result = orch.execute_workflow(
    workflow_id="workflow-001",
    plan=plan,
    agent_executor=executor_callback,
    callbacks=callback_handlers
)
```

**Parameters:**
- `workflow_id` (str): Workflow identifier
- `plan` (ExecutionPlan): Execution plan
- `agent_executor` (Callable): Async function to execute agents
- `callbacks` (Optional[List[Callback]]): Progress callbacks

**Returns:** `ExecutionResult` with:
- `id`: Result identifier
- `workflow_id`: Original workflow ID
- `status`: Final status ("completed"/"failed")
- `tasks_completed`: Number of successful tasks
- `tasks_failed`: Number of failed tasks
- `total_duration`: Actual execution time
- `planned_duration`: Planned execution time
- `efficiency`: Actual efficiency gain
- `failed_tasks`: List of failed task details
- `recovered_tasks`: Tasks recovered by escalation
- `execution_log`: Detailed execution timeline

### generate_strategy_document()

Create documentation of the strategy.

```python
document = orch.generate_strategy_document(
    workflow_id="workflow-001",
    analysis=analysis,
    decision=decision,
    plan=plan,
    execution_result=result
)
```

**Parameters:**
- `workflow_id` (str): Workflow identifier
- `analysis` (WorkflowAnalysis): Analysis results
- `decision` (DecisionRecommendation): Decision made
- `plan` (ExecutionPlan): Execution plan
- `execution_result` (ExecutionResult): Execution results

**Returns:** `StrategyDocument` with:
- `id`: Document identifier
- `workflow_id`: Original workflow ID
- `generated_at`: Timestamp
- `summary`: Executive summary
- `sections`: Detailed sections
- `recommendations`: Future recommendations
- `warnings`: Issues and warnings

### handle_failure()

Handle workflow failures and attempt recovery.

```python
recovery = orch.handle_failure(
    workflow_id="workflow-001",
    error=exception,
    plan=plan,
    execution_result=result
)
```

**Parameters:**
- `workflow_id` (str): Workflow identifier
- `error` (Exception): Error that occurred
- `plan` (ExecutionPlan): Execution plan
- `execution_result` (ExecutionResult): Partial results

**Returns:** Recovery action or raises exception if unrecoverable.

## StageOrchestrator

Enforces stage execution order and gate policies.

### Initialization

```python
from parallelizer_skill.stage_orchestrator import StageOrchestrator, GatePolicy

stage_orch = StageOrchestrator()
```

### add_stage()

Define an execution stage.

```python
stage_orch.add_stage(
    stage_number=1,
    name="Data Preparation",
    tasks=["load_data", "validate_data", "clean_data"],
    gate_policy=GatePolicy.ALL_PASS
)
```

**Parameters:**
- `stage_number` (int): Numeric stage identifier
- `name` (str): Human-readable stage name
- `tasks` (List[str]): Task IDs in this stage
- `gate_policy` (GatePolicy): Success criteria
  - `ALL_PASS`: All tasks must succeed
  - `ALL_COMPLETE`: All tasks must finish
  - `MAJORITY`: 80% must pass

### start_stage()

Begin execution of a stage.

```python
stage_orch.start_stage(stage_number=1)
```

**Parameters:**
- `stage_number` (int): Stage number to start

**Raises:**
- `RuntimeError` if prior stages incomplete or failed

### update_task_status()

Update progress of a task.

```python
stage_orch.update_task_status(
    stage_number=1,
    task_id="load_data",
    agent_id="agent-001",
    status="complete",
    error=None
)
```

**Parameters:**
- `stage_number` (int): Stage number
- `task_id` (str): Task identifier
- `agent_id` (str): Agent running task
- `status` (str): Task status
  - "pending", "running", "complete", "failed"
- `error` (Optional[str]): Error message if failed

### check_stage_ready()

Check if all tasks in stage completed.

```python
if stage_orch.check_stage_ready(stage_number=1):
    # All tasks finished
    pass
```

**Parameters:**
- `stage_number` (int): Stage number

**Returns:** True if all tasks completed (pass or fail)

### check_stage_passed()

Check if stage passed its gate policy.

```python
if stage_orch.check_stage_passed(stage_number=1):
    # Stage succeeded
    can_advance = True
```

**Parameters:**
- `stage_number` (int): Stage number

**Returns:** True if stage meets success criteria

### complete_stage()

Mark stage as finished.

```python
stage_orch.complete_stage(stage_number=1)
```

**Parameters:**
- `stage_number` (int): Stage number

**Raises:**
- `RuntimeError` if not all tasks completed

## Usage Patterns

### Pattern 1: Simple Analysis

```python
orch = WorkflowOrchestrator()

# Analyze workflow
analysis = orch.analyze_workflow(
    workflow_id="wf1",
    tasks=tasks,
    dependencies=deps
)

print(f"Critical path: {analysis.critical_path}")
print(f"Parallelizable: {len(analysis.parallelizable_tasks)} tasks")
```

### Pattern 2: Full Workflow

```python
orch = WorkflowOrchestrator()

# Step 1: Analyze
analysis = orch.analyze_workflow("wf1", tasks, deps)

# Step 2: Decide
decision = orch.make_decision("wf1", analysis, ParallelizationGoal.SPEED)

# Step 3: Plan
plan = orch.plan_execution(tasks, deps, decision, "wf1")

# Step 4: Execute
result = orch.execute_workflow(
    "wf1", plan, executor_func,
    callbacks=[progress_callback]
)

# Step 5: Document
doc = orch.generate_strategy_document("wf1", analysis, decision, plan, result)
```

### Pattern 3: Stage-Based Execution

```python
stage_orch = StageOrchestrator()

# Define stages
stage_orch.add_stage(1, "Load Data", ["task1", "task2"])
stage_orch.add_stage(2, "Process", ["task3", "task4"], GatePolicy.ALL_PASS)

# Execute stages
stage_orch.start_stage(1)
# ... run stage 1 tasks ...
stage_orch.update_task_status(1, "task1", "agent-1", "complete")
stage_orch.update_task_status(1, "task2", "agent-2", "complete")
stage_orch.complete_stage(1)

# Check before advancing
if stage_orch.check_stage_passed(1):
    stage_orch.start_stage(2)
    # ... run stage 2 tasks ...
```

### Pattern 4: Error Recovery

```python
try:
    result = orch.execute_workflow("wf1", plan, executor)
except Exception as e:
    # Handle failure
    recovery = orch.handle_failure("wf1", e, plan, result)
    if recovery.is_recoverable:
        # Retry with modified plan
        result = orch.execute_workflow("wf1", recovery.modified_plan, executor)
```

## Error Handling

All methods validate inputs and raise appropriate exceptions:

- `ValueError`: Invalid inputs or configuration
- `RuntimeError`: Invalid state transitions
- `FileNotFoundError`: Missing state files
- `json.JSONDecodeError`: Invalid JSON in state

## Performance

- **Overhead**: ~10ms per workflow (analysis + decision)
- **State Persistence**: ~1KB per task
- **Memory**: ~1MB for 1000-task workflows

## Configuration

Orchestrator respects the 4-level configuration hierarchy:

```python
# Use custom config
from parallelizer_skill.config import get_config

config = get_config()
orch = WorkflowOrchestrator(
    persistence_path=config.get("persistence_path")
)
```
