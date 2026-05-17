# Phase 4 Real-World Examples

Complete real-world examples showing Phase 4 usage patterns.

## Example 1: Simple Analysis

Analyze a basic data processing pipeline.

### Scenario
You have 3 independent data processing tasks that need to run. Want to understand parallelization opportunities.

### Tasks

```json
[
  {
    "id": "fetch_users",
    "name": "Fetch User Data",
    "estimated_duration": 5.0,
    "parallelizable": true,
    "priority": "high"
  },
  {
    "id": "fetch_orders",
    "name": "Fetch Order Data",
    "estimated_duration": 4.0,
    "parallelizable": true,
    "priority": "high"
  },
  {
    "id": "merge_data",
    "name": "Merge Datasets",
    "estimated_duration": 2.0,
    "parallelizable": false,
    "priority": "normal"
  }
]
```

### Dependencies

```json
[
  {
    "source_task_id": "fetch_users",
    "target_task_id": "merge_data",
    "dependency_type": "hard"
  },
  {
    "source_task_id": "fetch_orders",
    "target_task_id": "merge_data",
    "dependency_type": "hard"
  }
]
```

### Execution

```bash
# Save files
cat > tasks.json << 'EOF'
[... tasks above ...]
EOF

cat > deps.json << 'EOF'
[... dependencies above ...]
EOF

# Analyze
parallelize-task analyze tasks.json -d deps.json -f text
```

### Output

```
Analysis Results
===========================================
  total_tasks: 3
  parallelizable_tasks: 2
  sequential_bottlenecks: 1
  critical_path: fetch_users, merge_data
  critical_path_duration: 7.0
  total_serial_duration: 11.0

Parallelization Potential:
  - fetch_users and fetch_orders can run in parallel (5.0s total)
  - merge_data must wait for both (2.0s)
  - Total parallel time: 7.0s (saves 4.0s vs 11.0s serial)
```

## Example 2: Optimize for Speed

Complete pipeline optimizing for maximum performance.

### Scenario
You have a complex data science workflow with 12 tasks. Want the fastest possible execution.

### Full Pipeline Execution

```bash
# Step 1: Analyze
parallelize-task analyze tasks.json -d deps.json -o analysis.json
# Output: Identifies 10 parallelizable tasks, 2 bottlenecks

# Step 2: Decide for speed optimization
parallelize-task decide analysis.json -g speed -o decision.json
# Output: Recommends parallel execution with aggressive batching

# Step 3: Create execution plan
parallelize-task plan tasks.json -d deps.json \
  -a analysis.json -c decision.json -o plan.json -f text
# Output: 4-phase execution plan with 33% efficiency gain

# Step 4: View plan summary
cat plan.json | jq '.phases'
```

### Plan Output

```json
{
  "plan_id": "plan-123",
  "total_tasks": 12,
  "serial_duration": 60.0,
  "parallel_duration": 40.0,
  "efficiency_gain": 33.33,
  "phases": [
    {
      "phase_number": 1,
      "task_groups": [{"tasks": ["load_data", "fetch_config"], "duration": 5.0}],
      "estimated_duration": 5.0
    },
    {
      "phase_number": 2,
      "task_groups": [
        {"tasks": ["process_a", "process_b", "process_c", "process_d"], "duration": 15.0}
      ],
      "estimated_duration": 15.0
    },
    {
      "phase_number": 3,
      "task_groups": [{"tasks": ["aggregate", "validate"], "duration": 10.0}],
      "estimated_duration": 10.0
    },
    {
      "phase_number": 4,
      "task_groups": [{"tasks": ["export_results", "notify"], "duration": 10.0}],
      "estimated_duration": 10.0
    }
  ]
}
```

## Example 3: Programmatic Integration

Use CLI output in Python for intelligent decision-making.

### Scenario
Build an automated workflow executor that analyzes and optimizes before running.

### Python Code

```python
import json
import subprocess
from pathlib import Path

def run_workflow():
    """Run workflow with automatic optimization."""
    
    # 1. Analyze
    print("Analyzing workflow...")
    result = subprocess.run(
        ["parallelize-task", "analyze", "tasks.json", "-d", "deps.json"],
        capture_output=True,
        text=True
    )
    analysis = json.loads(result.stdout)
    
    # Check parallelization potential
    parallelizable = len(analysis["parallelizable_tasks"])
    total = analysis["total_tasks"]
    potential = parallelizable / total
    
    if potential < 0.3:
        print(f"WARNING: Only {potential*100:.1f}% parallelizable")
        goal = "cost"  # Use cost optimization for sequential workflows
    else:
        print(f"Good parallelization potential: {potential*100:.1f}%")
        goal = "speed"  # Use speed optimization
    
    # 2. Decide with chosen goal
    print(f"Making decision with goal: {goal}")
    result = subprocess.run(
        ["parallelize-task", "decide", "analysis.json", "-g", goal],
        capture_output=True,
        text=True
    )
    decision = json.loads(result.stdout)
    
    confidence = decision["confidence_level"]
    if confidence < 0.7:
        print(f"WARNING: Low confidence ({confidence}), review decision")
    
    # 3. Plan
    print("Creating execution plan...")
    result = subprocess.run(
        ["parallelize-task", "plan", "tasks.json", "-d", "deps.json",
         "-a", "analysis.json", "-c", "decision.json"],
        capture_output=True,
        text=True
    )
    plan = json.loads(result.stdout)
    
    # Check efficiency
    efficiency = plan["efficiency_gain"]
    print(f"Planned efficiency gain: {efficiency:.1f}%")
    print(f"Serial time: {plan['serial_duration']:.1f}s")
    print(f"Parallel time: {plan['parallel_duration']:.1f}s")
    
    # 4. Execute
    print("Executing workflow...")
    result = subprocess.run(
        ["parallelize-task", "execute", "plan.json",
         "-t", "tasks.json", "-d", "deps.json"],
        capture_output=True,
        text=True
    )
    execution = json.loads(result.stdout)
    
    # Report results
    print(f"Status: {execution['status']}")
    print(f"Completed: {execution['tasks_completed']}")
    print(f"Failed: {execution['tasks_failed']}")
    print(f"Actual duration: {execution['total_duration']:.1f}s")
    
    return execution["status"] == "completed"

if __name__ == "__main__":
    success = run_workflow()
    exit(0 if success else 1)
```

## Example 4: Error Recovery

Handle failures and recover gracefully.

### Scenario
A workflow partially fails. Need to identify issue and retry.

### Implementation

```python
from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.models import Task, TaskDependency, DependencyType
from parallelizer_skill.decision_engine import ParallelizationGoal

def run_with_recovery(tasks, dependencies, max_attempts=3):
    """Run workflow with error recovery."""
    
    orch = WorkflowOrchestrator()
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"Attempt {attempt}/{max_attempts}")
        
        try:
            # Analyze
            analysis = orch.analyze_workflow(
                f"wf-attempt-{attempt}",
                tasks,
                dependencies
            )
            print(f"  Analysis: {analysis.total_tasks} tasks")
            
            # Decide
            decision = orch.make_decision(
                f"wf-attempt-{attempt}",
                analysis,
                ParallelizationGoal.SPEED
            )
            print(f"  Decision: {decision.strategy}")
            
            # Plan
            plan = orch.plan_execution(tasks, dependencies, decision, f"wf-attempt-{attempt}")
            print(f"  Plan: {plan.efficiency_gain:.1f}% efficiency gain")
            
            # Execute
            result = orch.execute_workflow(
                f"wf-attempt-{attempt}",
                plan,
                execute_agent_callback
            )
            
            if result.status == "completed":
                print(f"SUCCESS on attempt {attempt}")
                return result
            else:
                # Partial failure - analyze for recovery
                failed = result.failed_tasks
                print(f"  Failed tasks: {[t.task_id for t in failed]}")
                
                if attempt < max_attempts:
                    # Try recovery
                    recovery = orch.handle_failure(
                        f"wf-attempt-{attempt}",
                        Exception("Partial failure"),
                        plan,
                        result
                    )
                    print(f"  Recovery strategy: {recovery.escalation_level}")
                    
                    # Modify plan for retry
                    tasks = [t for t in tasks if t.id not in [f.task_id for f in failed]]
                    print(f"  Retrying with {len(tasks)} remaining tasks")
        
        except Exception as e:
            print(f"  Error: {e}")
            if attempt == max_attempts:
                raise
    
    raise RuntimeError(f"Failed after {max_attempts} attempts")

def execute_agent_callback(tasks):
    """Callback to execute tasks."""
    # In real scenario, this would execute actual tasks
    pass
```

## Example 5: Complex Workflow with Monitoring

Production workflow with detailed monitoring.

### Scenario
Enterprise data pipeline with 50+ tasks, resource constraints, and monitoring.

### Setup

```python
from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.stage_orchestrator import StageOrchestrator, GatePolicy
from parallelizer_skill.agent_monitor import AgentMonitor
from parallelizer_skill.callbacks import ProgressCallback

class WorkflowMonitor(ProgressCallback):
    """Monitor workflow progress."""
    
    def on_phase_start(self, phase_number, tasks):
        print(f"\n--- Phase {phase_number} ---")
        print(f"Tasks: {tasks}")
    
    def on_task_complete(self, task_id, duration):
        print(f"  ✓ {task_id} ({duration:.2f}s)")
    
    def on_task_failed(self, task_id, error):
        print(f"  ✗ {task_id} - {error}")

def run_enterprise_workflow(tasks, dependencies):
    """Run production workflow with monitoring."""
    
    orch = WorkflowOrchestrator(persistence_path="./prod_workflows")
    stage_orch = StageOrchestrator()
    monitor = AgentMonitor()
    callback = WorkflowMonitor()
    
    # Step 1: Analyze
    print("Step 1: Analyzing workflow...")
    analysis = orch.analyze_workflow("prod-wf-001", tasks, dependencies)
    print(f"  - {len(analysis.parallelizable_tasks)} parallelizable tasks")
    print(f"  - {len(analysis.sequential_bottlenecks)} bottlenecks")
    print(f"  - Critical path: {' → '.join(analysis.critical_path)}")
    
    # Step 2: Decide
    print("\nStep 2: Determining strategy...")
    decision = orch.make_decision("prod-wf-001", analysis, ParallelizationGoal.BALANCED)
    print(f"  - Strategy: {decision.strategy}")
    print(f"  - Confidence: {decision.confidence_level*100:.1f}%")
    print(f"  - Batch size: {decision.recommended_batch_size}")
    
    # Step 3: Plan
    print("\nStep 3: Creating execution plan...")
    plan = orch.plan_execution(tasks, dependencies, decision, "prod-wf-001")
    print(f"  - Phases: {len(plan.phases)}")
    print(f"  - Serial: {plan.serial_duration:.1f}s → Parallel: {plan.parallel_duration:.1f}s")
    print(f"  - Efficiency: {plan.efficiency_gain:.1f}%")
    
    # Step 4: Setup stages
    print("\nStep 4: Setting up execution stages...")
    for phase in plan.phases:
        stage_orch.add_stage(
            phase.phase_number,
            f"Phase {phase.phase_number}",
            [t for g in phase.task_groups for t in g.tasks],
            gate_policy=GatePolicy.ALL_PASS
        )
    
    # Step 5: Execute with monitoring
    print("\nStep 5: Executing workflow...")
    result = orch.execute_workflow(
        "prod-wf-001",
        plan,
        execute_tasks_callback,
        callbacks=[callback]
    )
    
    # Step 6: Report
    print("\nExecution Summary:")
    print(f"  - Status: {result.status}")
    print(f"  - Completed: {result.tasks_completed}")
    print(f"  - Failed: {result.tasks_failed}")
    print(f"  - Duration: {result.total_duration:.1f}s (planned {plan.parallel_duration:.1f}s)")
    print(f"  - Efficiency: {result.efficiency:.1f}%")
    
    # Step 7: Document
    print("\nGenerating documentation...")
    doc = orch.generate_strategy_document(
        "prod-wf-001",
        analysis, decision, plan, result
    )
    print(f"  - Document: {doc.id}")
    print(f"  - Sections: {len(doc.sections)}")
    
    return result
```

## Example 6: Cost Optimization

Minimize execution cost.

### Scenario
You want to run a workflow but need to minimize cloud resource costs.

### Implementation

```bash
# Create cost-optimized workflow

# Step 1: Analyze - understand parallelization
parallelize-task analyze tasks.json -d deps.json -o analysis.json

# Step 2: Decide - optimize for cost
parallelize-task decide analysis.json -g cost -o decision.json

# Step 3: View recommendation
cat decision.json | jq '{
  strategy: .strategy,
  batch_size: .recommended_batch_size,
  monitoring: .monitoring_intensity,
  risks: .risk_factors
}'

# Output:
# {
#   "strategy": "sequential_batching",
#   "batch_size": 2,
#   "monitoring": "low",
#   "risks": ["reduced_parallelization"]
# }

# Step 4: Plan with cost optimization
parallelize-task plan tasks.json -d deps.json \
  -a analysis.json -c decision.json -o plan.json

# Step 5: Check resource usage
cat plan.json | jq '{
  phases: .phases | length,
  efficiency: .efficiency_gain,
  serial_duration: .serial_duration,
  parallel_duration: .parallel_duration
}'

# Step 6: Execute
parallelize-task execute plan.json -t tasks.json -d deps.json \
  -o execution.json
```

## Example 7: Analyzing Bottlenecks

Find and understand workflow bottlenecks.

### Scenario
Workflow is slower than expected. Need to identify bottlenecks.

### Analysis

```bash
# Run analysis
parallelize-task analyze tasks.json -d deps.json -o analysis.json -v

# Extract bottleneck information
cat analysis.json | jq '{
  bottlenecks: .sequential_bottlenecks,
  parallelizable: .parallelizable_tasks,
  critical_path: .critical_path,
  critical_duration: .critical_path_duration
}'

# Output example:
# {
#   "bottlenecks": ["merge_data", "aggregate"],
#   "parallelizable": ["fetch_users", "fetch_orders", "process_a", "process_b"],
#   "critical_path": ["fetch_users", "merge_data", "aggregate"],
#   "critical_duration": 12.0
# }

# Recommendations:
# - Focus optimization on critical path tasks
# - Parallelize "process_a" and "process_b" if possible
# - Consider reducing "merge_data" complexity to remove bottleneck
```

## Performance Tips

1. **Analyze First**: Always run analyze before other commands
2. **Incremental Optimization**: Try different goals to see trade-offs
3. **Batch Sizing**: Adjust batch size based on resource constraints
4. **Monitoring**: Use monitoring for production workflows
5. **State Management**: Keep state files for recovery and replay

## Next Steps

- See `PHASE4_ARCHITECTURE.md` for technical details
- See `PHASE4_CLI_GUIDE.md` for complete CLI reference
- See `PHASE4_ORCHESTRATOR.md` for Python API reference
