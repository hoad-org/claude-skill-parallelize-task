---
name: parallelize-task
displayName: Parallelize Task (Task Orchestration)
version: 1.0.0
phase: Phase 4 (Orchestration Core)
description: Enterprise-grade workflow orchestration and intelligent task parallelization. Complete lifecycle management from analysis through execution with state persistence, error recovery, and strategy documentation.
author: Claude Code
license: MIT
repository: https://github.com/hoad-org/claude-skill-parallelize-task
keywords:
  - workflow-orchestration
  - task-parallelization
  - dependency-analysis
  - dag
  - execution-planning
  - state-persistence
  - error-recovery
  - agentic
  - enterprise
---

# Parallelize Task - Workflow Orchestration & Task Parallelization

Enterprise-grade orchestration for complex task workflows. Analyze parallelization potential, determine optimal strategies, create execution plans, manage execution, and recover from failures.

## Phase 4 Features

### New in Phase 4 (Orchestration Core)
- **Central Orchestrator**: Unified coordination of all workflow phases
- **Complete Lifecycle**: Analyze → Decide → Plan → Execute → Document
- **State Persistence**: Save and recover from workflow interruptions
- **Stage Gates**: Enforce execution order with configurable success policies
- **Error Recovery**: Automatic escalation and recovery from failures
- **CLI Interface**: 6 composable commands for workflow automation
- **Strategy Documentation**: Auto-generated strategy documents and reports

## Quick Start

Complete workflow:
```bash
parallelize-task analyze tasks.json -d deps.json -o analysis.json
parallelize-task decide analysis.json -g speed -o decision.json
parallelize-task plan tasks.json -d deps.json -a analysis.json -c decision.json -o plan.json
parallelize-task execute plan.json -t tasks.json -d deps.json
parallelize-task document workflow-001 -a analysis.json -c decision.json -p plan.json -e execution.json -f markdown
```

Or just analyze:
```bash
parallelize-task analyze tasks.json -d deps.json
```

## Features

### Phase 4: Orchestration Core

#### 1. Workflow Analysis
- Complexity scoring of each task
- Feasibility ratings for parallelization
- Critical path identification
- Bottleneck detection
- Resource conflict analysis
- Circular dependency detection

#### 2. Strategy Decision
- Q1-Q6 strategic questions
- Goal-based optimization (speed/cost/reliability/balanced)
- Confidence scoring
- Risk factor identification
- Batch size recommendations

#### 3. Execution Planning
- Phased execution design
- Task grouping and ordering
- Efficiency gain calculation
- Resource allocation
- Safety validation

#### 4. Workflow Execution
- Stage-based execution enforcement
- Gate policy enforcement (ALL_PASS, ALL_COMPLETE, MAJORITY)
- Progress tracking
- Agent coordination
- Real-time monitoring

#### 5. Error Recovery
- Automatic escalation (INFO→WARN→ERROR→CRITICAL)
- Failure analysis
- Recovery strategies
- State restoration
- Retry handling

#### 6. Strategy Documentation
- Executive summaries
- Detailed analysis reports
- Recommendations
- Multi-format output (JSON, Markdown, HTML)

## Configuration

Configure at 4 levels (in order of precedence):

1. **Code Defaults** - Standard parallelization rules
2. **Master Config** - `~/.claude/parallelize-task/` (user preferences)
3. **Repo Config** - `./.claude/parallelize-task.json` (project overrides)
4. **Environment Variables** - Override anything

## Example Output

### Analysis Phase
```json
{
  "total_tasks": 12,
  "parallelizable_tasks": 8,
  "critical_path": ["task-a", "task-b", "task-k", "task-l"],
  "critical_path_duration": 70.0,
  "total_serial_duration": 200.0
}
```

### Decision Phase
```json
{
  "strategy": "parallel_with_batching",
  "goal": "speed",
  "confidence_level": 0.85,
  "recommended_batch_size": 4
}
```

### Execution Plan
```json
{
  "phases": 5,
  "serial_duration": 200.0,
  "parallel_duration": 110.0,
  "efficiency_gain": 45.0
}
```

### Full Pipeline Result
```
Analysis:    12 tasks, 8 parallelizable, 70s critical path
Decision:    Speed optimization, 85% confidence
Plan:        5 phases, 45% efficiency gain
Execution:   11 tasks completed, 1 failed (recovered)
Duration:    110s actual (planned 110s, 100% efficiency)
Document:    Strategy document generated
Status:      ✅ SUCCESS
```

## When to Use

Use **Parallelize Task** when:
- Running multiple independent tasks
- Optimizing workflow execution time
- Coordinating agentic task execution
- Understanding task dependencies
- Setting up parallel CI/CD workflows

## Phase 4 Documentation

### User Guides
- **PHASE4_CLI_GUIDE.md** — Complete CLI reference with all 6 commands and examples
- **PHASE4_EXAMPLES.md** — 7 real-world scenarios from simple analysis to complex recovery

### Developer Guides
- **PHASE4_ARCHITECTURE.md** — Technical architecture, integration points, design patterns
- **PHASE4_ORCHESTRATOR.md** — Python API reference for WorkflowOrchestrator and StageOrchestrator
- **PHASE4_INTEGRATION_TESTS.md** — Test suite overview, coverage, and testing guide
- **.claude/PHASE4.md** — Development guide, decisions, optimizations, future improvements

### Quick Links
- Configuration: `.claude/parallelize-task/`
- Project Structure: `/src/parallelizer_skill/`
- Tests: `/tests/` (414 tests, 89.17% coverage)
- Examples: See `docs/PHASE4_EXAMPLES.md`
