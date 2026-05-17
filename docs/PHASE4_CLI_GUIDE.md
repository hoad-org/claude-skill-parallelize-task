# Phase 4 CLI User Guide

Complete guide to using the parallelize-task CLI for workflow orchestration.

## Overview

The Phase 4 CLI provides 6 commands that compose into a complete workflow orchestration pipeline:

```
analyze → decide → plan → execute → document → reset
```

Each command can be used independently or chained together.

## Commands

### 1. analyze

Analyze a workflow's parallelization potential.

**Usage:**
```bash
parallelize-task analyze <tasks-file> [options]
```

**Options:**
- `-d, --dependencies`: Path to dependencies JSON file
- `-o, --output`: Output file for results
- `-f, --format`: Output format: "json" or "text" (default: json)
- `-v, --verbose`: Verbose output

**Input Format (tasks-file):**
```json
[
  {
    "id": "task1",
    "name": "Load Data",
    "estimated_duration": 2.0,
    "parallelizable": true,
    "priority": "normal"
  },
  {
    "id": "task2",
    "name": "Process A",
    "estimated_duration": 3.0,
    "parallelizable": true,
    "priority": "normal"
  }
]
```

**Dependencies Format:**
```json
[
  {
    "source_task_id": "task1",
    "target_task_id": "task2",
    "dependency_type": "hard"
  }
]
```

**Output (JSON):**
```json
{
  "analysis_id": "analysis-123",
  "total_tasks": 4,
  "parallelizable_tasks": 3,
  "sequential_bottlenecks": 1,
  "critical_path": ["task1", "task2", "task4"],
  "critical_path_duration": 6.0,
  "total_serial_duration": 9.0,
  "complexity_scores": {
    "task1": 0.4,
    "task2": 0.6,
    "task3": 0.5,
    "task4": 0.3
  },
  "warnings": []
}
```

**Example:**
```bash
# Simple analysis
parallelize-task analyze tasks.json -d deps.json -o analysis.json

# With verbose output
parallelize-task analyze tasks.json -d deps.json -f text -v

# Just print to console
parallelize-task analyze tasks.json
```

### 2. decide

Determine optimal parallelization strategy.

**Usage:**
```bash
parallelize-task decide <analysis-file> [options]
```

**Options:**
- `-g, --goal`: Optimization goal: "speed", "cost", "reliability", "balanced"
  - Default: "balanced"
- `-o, --output`: Output file for results
- `-f, --format`: Output format: "json" or "text" (default: json)
- `-v, --verbose`: Verbose output

**Output (JSON):**
```json
{
  "decision_id": "decision-456",
  "strategy": "parallel_with_batching",
  "goal": "speed",
  "confidence_level": 0.85,
  "questions_answered": {
    "q1_parallelizable": true,
    "q2_io_bound": true,
    "q3_resource_conflicts": false,
    "q4_dependencies": true,
    "q5_failure_impact": false,
    "q6_cost_sensitive": false
  },
  "recommended_batch_size": 4,
  "monitoring_intensity": "medium",
  "risk_factors": ["bottleneck_at_task4"]
}
```

**Example:**
```bash
# Speed optimization
parallelize-task decide analysis.json -g speed -o decision.json

# Balanced strategy
parallelize-task decide analysis.json -g balanced

# Text summary
parallelize-task decide analysis.json -f text -v
```

### 3. plan

Create phased execution plan.

**Usage:**
```bash
parallelize-task plan <tasks-file> [options]
```

**Options:**
- `-d, --dependencies`: Path to dependencies JSON file
- `-a, --analysis`: Path to analysis results file
- `-c, --decision`: Path to decision results file
- `-o, --output`: Output file for results
- `-f, --format`: Output format: "json" or "text" (default: json)
- `-v, --verbose`: Verbose output

**Output (JSON):**
```json
{
  "plan_id": "plan-789",
  "total_tasks": 4,
  "serial_duration": 9.0,
  "parallel_duration": 6.0,
  "efficiency_gain": 33.33,
  "phases": [
    {
      "phase_number": 1,
      "task_groups": [
        {
          "id": "group-1",
          "tasks": ["task1"],
          "estimated_duration": 2.0
        }
      ],
      "estimated_duration": 2.0
    },
    {
      "phase_number": 2,
      "task_groups": [
        {
          "id": "group-2",
          "tasks": ["task2", "task3"],
          "estimated_duration": 3.0
        }
      ],
      "estimated_duration": 3.0
    },
    {
      "phase_number": 3,
      "task_groups": [
        {
          "id": "group-3",
          "tasks": ["task4"],
          "estimated_duration": 1.0
        }
      ],
      "estimated_duration": 1.0
    }
  ],
  "critical_path": ["task1", "task2", "task4"],
  "parallelizable_groups": 2,
  "resource_conflicts": [],
  "safety_issues": []
}
```

**Example:**
```bash
# Plan from tasks only
parallelize-task plan tasks.json -d deps.json -o plan.json

# Plan with analysis and decision
parallelize-task plan tasks.json -d deps.json -a analysis.json -c decision.json

# View plan summary
parallelize-task plan tasks.json -d deps.json -f text
```

### 4. execute

Execute the workflow plan.

**Usage:**
```bash
parallelize-task execute <plan-file> [options]
```

**Options:**
- `-t, --tasks`: Path to tasks JSON file
- `-d, --dependencies`: Path to dependencies JSON file
- `-o, --output`: Output file for results
- `-f, --format`: Output format: "json" or "text" (default: json)
- `-v, --verbose`: Verbose output
- `--dry-run`: Show what would execute without running

**Output (JSON):**
```json
{
  "execution_id": "execution-999",
  "status": "completed",
  "tasks_completed": 4,
  "tasks_failed": 0,
  "total_duration": 5.8,
  "planned_duration": 6.0,
  "efficiency": 96.67,
  "failed_tasks": [],
  "recovered_tasks": [],
  "execution_log": [
    {
      "timestamp": "2026-05-17T12:00:00",
      "phase": 1,
      "event": "phase_started"
    },
    {
      "timestamp": "2026-05-17T12:00:02",
      "phase": 1,
      "event": "task_completed",
      "task_id": "task1",
      "duration": 2.0
    }
  ]
}
```

**Example:**
```bash
# Execute plan
parallelize-task execute plan.json -t tasks.json -d deps.json

# Dry run to see what would happen
parallelize-task execute plan.json --dry-run

# Verbose execution
parallelize-task execute plan.json -t tasks.json -d deps.json -v
```

### 5. document

Generate strategy documentation.

**Usage:**
```bash
parallelize-task document <workflow-id> [options]
```

**Options:**
- `-a, --analysis`: Path to analysis results file
- `-c, --decision`: Path to decision results file
- `-p, --plan`: Path to plan results file
- `-e, --execution`: Path to execution results file
- `-o, --output`: Output file for documentation
- `-f, --format`: Output format: "json", "markdown", or "html" (default: markdown)
- `-v, --verbose`: Verbose output

**Output (Markdown):**
```markdown
# Workflow Strategy Document

## Executive Summary
This document describes the parallelization strategy for workflow-001.

## Analysis Summary
- Total tasks: 4
- Parallelizable: 3 (75%)
- Critical path: 6.0s
- Serial duration: 9.0s

## Strategy Recommendation
Goal: Speed
Strategy: Parallel with batching
Confidence: 85%

## Execution Plan
Phase 1: task1 (2.0s)
Phase 2: task2, task3 (3.0s)
Phase 3: task4 (1.0s)

Total time: 6.0s (33% improvement)

## Recommendations
...
```

**Example:**
```bash
# Generate markdown document
parallelize-task document wf-001 -a analysis.json -c decision.json -p plan.json -e execution.json

# Generate HTML report
parallelize-task document wf-001 -f html -o report.html

# JSON output for programmatic use
parallelize-task document wf-001 -f json -o doc.json
```

### 6. reset

Clear workflow state and history.

**Usage:**
```bash
parallelize-task reset [options]
```

**Options:**
- `-w, --workflow`: Specific workflow ID to reset (optional)
- `-f, --force`: Skip confirmation prompt
- `-v, --verbose`: Verbose output

**Effect:**
- Deletes state files for specified workflow (or all if none specified)
- Clears orchestration_state directory
- Removes cached analysis, decisions, plans

**Example:**
```bash
# Reset specific workflow
parallelize-task reset -w workflow-001

# Reset all workflows (with confirmation)
parallelize-task reset

# Force reset without confirmation
parallelize-task reset --force
```

## Command Piping & Workflows

Commands output JSON by default, enabling composition:

### Workflow 1: Analyze Only
```bash
parallelize-task analyze tasks.json -d deps.json -f json
```

### Workflow 2: Analyze → Decide
```bash
parallelize-task analyze tasks.json -d deps.json -o analysis.json
parallelize-task decide analysis.json -g speed -o decision.json
```

### Workflow 3: Full Pipeline
```bash
# 1. Analyze
parallelize-task analyze tasks.json -d deps.json -o analysis.json

# 2. Decide
parallelize-task decide analysis.json -g speed -o decision.json

# 3. Plan
parallelize-task plan tasks.json -d deps.json -a analysis.json \
  -c decision.json -o plan.json

# 4. Execute
parallelize-task execute plan.json -t tasks.json -d deps.json \
  -o execution.json

# 5. Document
parallelize-task document workflow-001 -a analysis.json \
  -c decision.json -p plan.json -e execution.json -f markdown \
  -o strategy.md
```

### Workflow 4: Programmatic Integration
```bash
# Get analysis as JSON for processing
analysis=$(parallelize-task analyze tasks.json -d deps.json)
echo "$analysis" | jq '.critical_path'  # Extract critical path

# Get decision for specific goal
decision=$(parallelize-task decide analysis.json -g cost)
echo "$decision" | jq '.recommended_batch_size'  # Extract batch size
```

## Output Formats

### JSON Format
- Machine-readable output
- Programmatic integration
- Full detail preservation
- Default format for piping

### Text Format
- Human-readable summary
- Key metrics highlighted
- Reduced verbosity
- Use with `-f text`

### Markdown Format (documentation only)
- ReadMe-style formatting
- Sections and headers
- Readable in browsers
- Use with `document -f markdown`

### HTML Format (documentation only)
- Styled web pages
- Interactive tables
- Charts and visualizations
- Use with `document -f html`

## Common Workflows

### Workflow: Optimize for Speed
```bash
# Analyze for parallelization
parallelize-task analyze tasks.json -d deps.json -o analysis.json

# Get speed-optimized decision
parallelize-task decide analysis.json -g speed -o decision.json

# View the plan
parallelize-task plan tasks.json -d deps.json -c decision.json -f text
```

### Workflow: Optimize for Cost
```bash
parallelize-task analyze tasks.json -d deps.json -o analysis.json
parallelize-task decide analysis.json -g cost -o decision.json
parallelize-task plan tasks.json -d deps.json -c decision.json
```

### Workflow: Full Execution with Documentation
```bash
# Run through complete pipeline
parallelize-task analyze tasks.json -d deps.json -o 1-analysis.json
parallelize-task decide 1-analysis.json -g balanced -o 2-decision.json
parallelize-task plan tasks.json -d deps.json -a 1-analysis.json \
  -c 2-decision.json -o 3-plan.json
parallelize-task execute 3-plan.json -t tasks.json -d deps.json \
  -o 4-execution.json

# Generate documentation
parallelize-task document my-workflow -a 1-analysis.json \
  -c 2-decision.json -p 3-plan.json -e 4-execution.json \
  -f markdown -o strategy.md
```

## Troubleshooting

### File Not Found
```
Error: File not found: tasks.json
```
Solution: Verify file path exists and is correct

### Invalid JSON
```
Error: Invalid JSON in tasks.json
```
Solution: Validate JSON structure with `jq` or online tool

### Missing Dependencies
```
Error: Dependency file required for this command
```
Solution: Provide `-d/--dependencies` flag

### Invalid Goal
```
Error: Invalid goal: "maximum"
```
Solution: Use: speed, cost, reliability, or balanced

### Circular Dependencies
```
Warning: Circular dependencies detected
```
Solution: Review dependency definitions for cycles

## Environment Variables

Configure CLI behavior via environment:

```bash
# Set output format
export PARALLELIZE_OUTPUT_FORMAT=json

# Set persistence path
export PARALLELIZE_STATE_PATH=./orchestration_state

# Enable verbose logging
export PARALLELIZE_VERBOSE=true

# Run commands
parallelize-task analyze tasks.json
```

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Missing required argument
- `3` - Invalid input format
- `4` - File not found
- `5` - Invalid state transition
