---
name: parallelize-task
displayName: Parallelize Task (Task Parallelization)
version: 1.0.0
description: Intelligent task parallelization with dependency analysis. Automatically identify parallelizable tasks, create DAGs, optimize execution, and coordinate agentic workflows.
author: Claude Code
license: MIT
repository: https://github.com/hoad-org/claude-skill-parallelize-task
keywords:
  - parallelization
  - task-orchestration
  - dependency-analysis
  - dag
  - workflow-optimization
  - agentic
---

# Parallelize Task - Intelligent Task Parallelization

Automatically parallelize independent tasks, analyze dependencies, and optimize workflow execution.

## Quick Start

```
/parallelize-task run                    # Analyze and run tasks in parallel
/parallelize-task analyze <task>         # Analyze task dependencies
/parallelize-task show-dag               # Visualize task DAG
/parallelize-task optimize               # Get optimization suggestions
```

## Features

### Intelligent Task Analysis

Automatically detect dependencies and parallelizable tasks:

- **Dependency Detection** - Identify which tasks can run in parallel
- **DAG Construction** - Build directed acyclic graphs of task dependencies
- **Critical Path Analysis** - Find the longest execution path
- **Optimization Suggestions** - Recommend parallel execution strategy

### Task Execution

Run tasks efficiently:

```bash
/parallelize-task run        # Execute tasks respecting dependencies
```

Automatically:
- Runs independent tasks in parallel
- Respects task dependencies
- Coordinates agentic workflows
- Optimizes execution time

### Visualization

Understand task structure:

```bash
/parallelize-task show-dag   # Display task dependency graph
```

Shows:
- Task nodes and edges
- Dependency relationships
- Critical path
- Parallelization opportunities

## Configuration

Configure at 4 levels (in order of precedence):

1. **Code Defaults** - Standard parallelization rules
2. **Master Config** - `~/.claude/parallelize-task/` (user preferences)
3. **Repo Config** - `./.claude/parallelize-task.json` (project overrides)
4. **Environment Variables** - Override anything

## Example Output

```
Task Parallelization Analysis:

Tasks: 12 total
  ├─ Parallelizable: 8 tasks
  └─ Sequential: 4 tasks

Execution Plan:
  Phase 1 (parallel): task-a, task-b, task-c, task-d [4 tasks, ~30s]
  Phase 2 (parallel): task-e, task-f                 [2 tasks, ~45s]
  Phase 3 (parallel): task-g, task-h, task-i, task-j [4 tasks, ~20s]
  Phase 4 (depends on 3): task-k                     [1 task, ~10s]
  Phase 5 (depends on 4): task-l                     [1 task, ~5s]

Total Time: ~110s (sequential would be ~200s)
Speedup: 1.82x faster with parallelization ✅
```

## When to Use

Use **Parallelize Task** when:
- Running multiple independent tasks
- Optimizing workflow execution time
- Coordinating agentic task execution
- Understanding task dependencies
- Setting up parallel CI/CD workflows

## Documentation

- Configuration: `.claude/parallelize-task/`
- DAG Analysis: `docs/DAG_ANALYSIS.md`
- Examples: `docs/EXAMPLES.md`
- Architecture: `docs/ARCHITECTURE.md`
