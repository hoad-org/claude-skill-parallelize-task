#!/usr/bin/env python3
"""CLI interface for parallelize-task skill."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from parallelizer_skill import __version__
from parallelizer_skill.config import get_config
from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.models import Task, TaskDependency, DependencyType
from parallelizer_skill.decision_engine import ParallelizationGoal


def _load_json_file(file_path: str) -> dict:
    """Load JSON file with error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)


def _save_json_file(file_path: str, data: dict) -> None:
    """Save data to JSON file.

    Args:
        file_path: Path to output file
        data: Data to save
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _format_json_output(data: dict) -> str:
    """Format data as JSON string.

    Args:
        data: Data to format

    Returns:
        JSON string
    """
    return json.dumps(data, indent=2, default=str)


def _format_text_summary(title: str, data: dict) -> str:
    """Format data as human-readable text.

    Args:
        title: Section title
        data: Data to format

    Returns:
        Formatted text
    """
    lines = [f"\n{'=' * 60}", f"{title}", f"{'=' * 60}"]

    for key, value in data.items():
        if isinstance(value, (dict, list)):
            lines.append(f"  {key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    lines.append(f"    {k}: {v}")
            else:
                for item in value:
                    lines.append(f"    - {item}")
        else:
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def analyze(
    tasks_file: str,
    dependencies_file: Optional[str] = None,
    output_file: Optional[str] = None,
    output_format: str = "json",
    verbose: bool = False,
) -> int:
    """Analyze workflow complexity.

    Args:
        tasks_file: Path to tasks JSON file
        dependencies_file: Path to dependencies JSON file
        output_file: Path to output file (optional)
        output_format: Output format (json or text)
        verbose: Enable verbose output

    Returns:
        Exit code (0 success, 1 error)
    """
    try:
        # Load tasks
        tasks_data = _load_json_file(tasks_file)
        if not isinstance(tasks_data, list):
            raise ValueError("Tasks file must contain a JSON array")

        tasks = [Task(**t) for t in tasks_data]

        # Load dependencies if provided
        dependencies = []
        if dependencies_file:
            deps_data = _load_json_file(dependencies_file)
            if not isinstance(deps_data, list):
                raise ValueError("Dependencies file must contain a JSON array")
            dependencies = [TaskDependency(**d) for d in deps_data]

        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()

        # Analyze workflow
        workflow_id = f"workflow-{tasks_file}"
        analysis = orchestrator.analyze_workflow(workflow_id, tasks, dependencies)

        # Prepare output
        output_data = {
            "analysis_id": analysis.analysis_id,
            "workflow_id": analysis.workflow_id,
            "total_tasks": analysis.total_tasks,
            "total_dependencies": analysis.total_dependencies,
            "complexity_scores": analysis.complexity_scores,
            "feasibility_ratings": analysis.feasibility_ratings,
            "critical_path": analysis.critical_path,
            "critical_path_duration": analysis.critical_path_duration,
            "total_serial_duration": analysis.total_serial_duration,
            "parallelizable_tasks": analysis.parallelizable_tasks,
            "sequential_bottlenecks": analysis.sequential_bottlenecks,
            "resource_conflicts": analysis.resource_conflicts,
            "warnings": analysis.warnings,
        }

        # Output results
        if output_format == "json":
            output_text = _format_json_output(output_data)
        else:
            output_text = _format_text_summary("Workflow Analysis", output_data)

        if output_file:
            _save_json_file(output_file, output_data)
            if verbose:
                print(f"✅ Analysis saved to {output_file}")
        else:
            print(output_text)

        if verbose:
            print(f"✅ Analysis complete: {analysis.total_tasks} tasks, "
                  f"{len(analysis.parallelizable_tasks)} parallelizable")

        return 0

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"❌ Analysis error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def decide(
    goal: str,
    tasks_file: Optional[str] = None,
    dependencies_file: Optional[str] = None,
    analysis_file: Optional[str] = None,
    output_file: Optional[str] = None,
    output_format: str = "json",
    verbose: bool = False,
) -> int:
    """Generate parallelization strategy.

    Args:
        goal: Parallelization goal (performance/cost/reliability)
        tasks_file: Path to tasks JSON file
        dependencies_file: Path to dependencies JSON file
        analysis_file: Path to analysis JSON file (alternative to tasks/deps)
        output_file: Path to output file (optional)
        output_format: Output format (json or text)
        verbose: Enable verbose output

    Returns:
        Exit code (0 success, 1 error)
    """
    try:
        # Validate goal
        valid_goals = ["performance", "cost", "reliability"]
        if goal.lower() not in valid_goals:
            raise ValueError(f"Goal must be one of: {', '.join(valid_goals)}")

        parallelization_goal = ParallelizationGoal[goal.upper()]

        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()

        # Load analysis or generate it
        if analysis_file:
            analysis_data = _load_json_file(analysis_file)
            # Reconstruct WorkflowAnalysis from data
            from parallelizer_skill.models import WorkflowAnalysis
            analysis = WorkflowAnalysis(**analysis_data)
        elif tasks_file:
            # Generate analysis
            tasks_data = _load_json_file(tasks_file)
            tasks = [Task(**t) for t in tasks_data]

            dependencies = []
            if dependencies_file:
                deps_data = _load_json_file(dependencies_file)
                dependencies = [TaskDependency(**d) for d in deps_data]

            workflow_id = f"workflow-{tasks_file}"
            analysis = orchestrator.analyze_workflow(workflow_id, tasks, dependencies)
        else:
            raise ValueError("Must provide either --analysis-file or --tasks-file")

        # Generate strategy
        recommendation = orchestrator.generate_strategy(analysis, parallelization_goal)

        # Prepare output
        output_data = {
            "strategy_type": recommendation.strategy_type,
            "goal": goal,
            "parallel_execution": recommendation.parallel_execution,
            "max_parallel_tasks": recommendation.max_parallel_tasks,
            "recommended_batch_size": recommendation.recommended_batch_size,
            "recommended_retry_count": recommendation.recommended_retry_count,
            "monitoring_intensity": recommendation.monitoring_intensity,
            "escalation_level": recommendation.escalation_level,
            "resource_aware": recommendation.resource_aware,
            "rationale": recommendation.rationale,
        }

        # Output results
        if output_format == "json":
            output_text = _format_json_output(output_data)
        else:
            output_text = _format_text_summary("Parallelization Strategy", output_data)

        if output_file:
            _save_json_file(output_file, output_data)
            if verbose:
                print(f"✅ Strategy saved to {output_file}")
        else:
            print(output_text)

        if verbose:
            print(f"✅ Strategy generated: {recommendation.strategy_type}")

        return 0

    except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"❌ Strategy error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def plan(
    tasks_file: str,
    dependencies_file: Optional[str] = None,
    strategy_file: Optional[str] = None,
    output_file: Optional[str] = None,
    output_format: str = "json",
    verbose: bool = False,
) -> int:
    """Create execution plan.

    Args:
        tasks_file: Path to tasks JSON file
        dependencies_file: Path to dependencies JSON file
        strategy_file: Path to strategy JSON file
        output_file: Path to output file (optional)
        output_format: Output format (json or text)
        verbose: Enable verbose output

    Returns:
        Exit code (0 success, 1 error)
    """
    try:
        # Load tasks
        tasks_data = _load_json_file(tasks_file)
        tasks = [Task(**t) for t in tasks_data]

        # Load dependencies
        dependencies = []
        if dependencies_file:
            deps_data = _load_json_file(dependencies_file)
            dependencies = [TaskDependency(**d) for d in deps_data]

        # Load strategy or use defaults
        from parallelizer_skill.decision_engine import DecisionRecommendation
        if strategy_file:
            strategy_data = _load_json_file(strategy_file)
            recommendation = DecisionRecommendation(**strategy_data)
        else:
            # Create default recommendation
            recommendation = DecisionRecommendation(
                strategy_type="balanced",
                max_parallel_tasks=4,
                recommended_batch_size=10,
                recommended_retry_count=2,
                recommended_checkpoint_interval=5,
                parallel_execution=True,
                resource_aware=True,
                monitoring_intensity="normal",
                escalation_level="warning",
                rationale="Default strategy",
            )

        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()

        # Create plan
        plan_result = orchestrator.plan_execution(tasks, dependencies, recommendation)

        # Prepare output
        output_data = {
            "id": plan_result.id,
            "total_tasks": plan_result.total_tasks,
            "serial_duration": plan_result.serial_duration,
            "parallel_duration": plan_result.parallel_duration,
            "efficiency_gain": plan_result.efficiency_gain,
            "critical_path": plan_result.critical_path,
            "phases": [
                {
                    "phase_number": phase.phase_number,
                    "is_parallel": phase.is_parallel,
                    "estimated_duration": phase.estimated_duration,
                    "sync_point_required": phase.sync_point_required,
                    "task_groups": [
                        {
                            "id": group.id,
                            "tasks": group.tasks,
                            "can_parallelize": group.can_parallelize,
                            "estimated_duration": group.estimated_duration,
                        }
                        for group in phase.task_groups
                    ],
                }
                for phase in plan_result.phases
            ],
            "parallelizable_groups": plan_result.parallelizable_groups,
            "resource_conflicts": plan_result.resource_conflicts,
            "safety_issues": plan_result.safety_issues,
            "optimization_notes": plan_result.optimization_notes,
        }

        # Output results
        if output_format == "json":
            output_text = _format_json_output(output_data)
        else:
            output_text = _format_text_summary("Execution Plan", output_data)

        if output_file:
            _save_json_file(output_file, output_data)
            if verbose:
                print(f"✅ Plan saved to {output_file}")
        else:
            print(output_text)

        if verbose:
            print(f"✅ Plan created: {len(plan_result.phases)} phases, "
                  f"{plan_result.efficiency_gain:.1f}% efficiency gain")

        return 0

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"❌ Plan error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def execute(
    plan_file: str,
    output_file: Optional[str] = None,
    output_format: str = "json",
    simulate: bool = False,
    verbose: bool = False,
) -> int:
    """Execute workflow plan.

    Args:
        plan_file: Path to execution plan JSON file
        output_file: Path to output file (optional)
        output_format: Output format (json or text)
        simulate: Run in simulation mode
        verbose: Enable verbose output

    Returns:
        Exit code (0 success, 1 error)
    """
    try:
        # Load plan
        plan_data = _load_json_file(plan_file)

        from parallelizer_skill.models import ExecutionPlan
        plan = ExecutionPlan(**plan_data)

        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()

        # Execute plan
        workflow_id = f"workflow-execution-{plan.id}"
        result = orchestrator.execute_workflow(plan, workflow_id)

        # Prepare output
        output_data = {
            "execution_id": result.execution_id,
            "workflow_id": result.workflow_id,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "tasks_completed": result.tasks_completed,
            "tasks_failed": result.tasks_failed,
            "tasks_skipped": result.tasks_skipped,
            "phases_executed": result.phases_executed,
            "total_phases": result.total_phases,
            "efficiency_achieved": result.efficiency_achieved,
            "recovery_events": result.recovery_events,
            "escalation_events": result.escalation_events,
            "metrics": result.metrics,
            "simulated": simulate,
        }

        if result.error_message:
            output_data["error_message"] = result.error_message

        # Output results
        if output_format == "json":
            output_text = _format_json_output(output_data)
        else:
            output_text = _format_text_summary("Execution Result", output_data)

        if output_file:
            _save_json_file(output_file, output_data)
            if verbose:
                print(f"✅ Result saved to {output_file}")
        else:
            print(output_text)

        if verbose:
            print(f"✅ Execution complete: {result.status.value}, "
                  f"{result.tasks_completed}/{plan.total_tasks} tasks")

        return 0 if result.status.value == "completed" else 1

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"❌ Execution error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def document(
    analysis_file: str,
    recommendation_file: str,
    plan_file: str,
    output_file: Optional[str] = None,
    output_format: str = "markdown",
    verbose: bool = False,
) -> int:
    """Generate strategy document.

    Args:
        analysis_file: Path to analysis JSON file
        recommendation_file: Path to recommendation JSON file
        plan_file: Path to plan JSON file
        output_file: Path to output file (optional)
        output_format: Output format (markdown or json)
        verbose: Enable verbose output

    Returns:
        Exit code (0 success, 1 error)
    """
    try:
        # Load all files
        analysis_data = _load_json_file(analysis_file)
        recommendation_data = _load_json_file(recommendation_file)
        plan_data = _load_json_file(plan_file)

        # Reconstruct objects
        from parallelizer_skill.models import WorkflowAnalysis, ExecutionPlan
        from parallelizer_skill.decision_engine import DecisionRecommendation

        analysis = WorkflowAnalysis(**analysis_data)
        recommendation = DecisionRecommendation(**recommendation_data)
        plan = ExecutionPlan(**plan_data)

        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()

        # Generate document
        document = orchestrator.create_strategy_document(analysis, recommendation, plan)

        # Helper to serialize objects for JSON
        def serialize_for_json(obj: Any) -> Any:
            """Recursively serialize objects for JSON output."""
            if isinstance(obj, dict):
                return {k: serialize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_for_json(item) for item in obj]
            elif hasattr(obj, 'model_dump'):  # Pydantic model
                return serialize_for_json(obj.model_dump())
            elif hasattr(obj, '__dict__'):
                return serialize_for_json(obj.__dict__)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj

        # Prepare output data - ensure full serialization
        impl_plan_list = document.implementation_plan
        if isinstance(impl_plan_list, str):
            impl_plan_list = [impl_plan_list]
        elif not isinstance(impl_plan_list, list):
            impl_plan_list = list(impl_plan_list) if hasattr(impl_plan_list, '__iter__') else [str(impl_plan_list)]

        output_data = {
            "document_id": document.document_id,
            "title": document.title,
            "executive_summary": document.executive_summary,
            "analysis_summary": serialize_for_json(document.analysis_summary),
            "recommendations": serialize_for_json(document.recommendations),
            "implementation_plan": [str(step) for step in impl_plan_list],
            "risk_assessment": serialize_for_json(document.risk_assessment),
            "performance_projections": serialize_for_json(document.performance_projections),
            "generated_at": str(document.generated_at),
        }

        # Generate markdown if requested
        markdown_text = ""
        if output_format == "markdown":
            impl_plan_str = "\n".join([f"- {step}" for step in impl_plan_list])

            markdown_text = f"""# {document.title}

## Executive Summary
{document.executive_summary}

## Analysis
{json.dumps(output_data['analysis_summary'], indent=2)}

## Recommendations
{json.dumps(output_data['recommendations'], indent=2)}

## Implementation Plan
{impl_plan_str}

## Risk Assessment
{json.dumps(output_data['risk_assessment'], indent=2)}

## Performance Projections
{json.dumps(output_data['performance_projections'], indent=2)}

---
Generated: {output_data['generated_at']}
"""

        # Output results
        if output_format == "markdown":
            output_text = markdown_text
        else:
            output_text = _format_json_output(output_data)

        if output_file:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(output_text)
            if verbose:
                print(f"✅ Document saved to {output_file}")
        else:
            print(output_text)

        if verbose:
            print(f"✅ Document generated: {document.title}")

        return 0

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"❌ Document error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def reset(verbose: bool = False) -> int:
    """Reset internal state.

    Args:
        verbose: Enable verbose output

    Returns:
        Exit code (0 success, 1 error)
    """
    try:
        # Get config and reset it
        from parallelizer_skill.config import reset_config
        reset_config()

        if verbose:
            print("✅ State cleared")

        return 0

    except Exception as e:
        print(f"❌ Reset error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="parallelize-task",
        description="Intelligent task parallelization with dependency analysis",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"parallelize-task {__version__}",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--format",
        default="json",
        choices=["json", "text"],
        help="Output format (default: json)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze workflow complexity and parallelization potential",
    )
    analyze_parser.add_argument(
        "--tasks-file",
        required=True,
        help="Path to tasks JSON file",
    )
    analyze_parser.add_argument(
        "--dependencies-file",
        help="Path to dependencies JSON file",
    )
    analyze_parser.add_argument(
        "--output",
        help="Output file for analysis results",
    )

    # decide command
    decide_parser = subparsers.add_parser(
        "decide",
        help="Generate parallelization strategy",
    )
    decide_parser.add_argument(
        "--goal",
        required=True,
        choices=["performance", "cost", "reliability"],
        help="Parallelization goal",
    )
    decide_parser.add_argument(
        "--tasks-file",
        help="Path to tasks JSON file",
    )
    decide_parser.add_argument(
        "--dependencies-file",
        help="Path to dependencies JSON file",
    )
    decide_parser.add_argument(
        "--analysis-file",
        help="Path to analysis JSON file (alternative to tasks/deps)",
    )
    decide_parser.add_argument(
        "--output",
        help="Output file for strategy",
    )

    # plan command
    plan_parser = subparsers.add_parser(
        "plan",
        help="Create execution plan",
    )
    plan_parser.add_argument(
        "--tasks-file",
        required=True,
        help="Path to tasks JSON file",
    )
    plan_parser.add_argument(
        "--dependencies-file",
        help="Path to dependencies JSON file",
    )
    plan_parser.add_argument(
        "--strategy-file",
        help="Path to strategy JSON file",
    )
    plan_parser.add_argument(
        "--output",
        help="Output file for execution plan",
    )

    # execute command
    execute_parser = subparsers.add_parser(
        "execute",
        help="Execute workflow plan",
    )
    execute_parser.add_argument(
        "--plan-file",
        required=True,
        help="Path to execution plan JSON file",
    )
    execute_parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulation mode",
    )
    execute_parser.add_argument(
        "--output",
        help="Output file for execution results",
    )

    # document command
    document_parser = subparsers.add_parser(
        "document",
        help="Generate strategy document",
    )
    document_parser.add_argument(
        "--analysis-file",
        required=True,
        help="Path to analysis JSON file",
    )
    document_parser.add_argument(
        "--recommendation-file",
        required=True,
        help="Path to recommendation JSON file",
    )
    document_parser.add_argument(
        "--plan-file",
        required=True,
        help="Path to plan JSON file",
    )
    document_parser.add_argument(
        "--output",
        help="Output file for document",
    )
    document_parser.add_argument(
        "--doc-format",
        default="markdown",
        choices=["markdown", "json"],
        help="Document format (default: markdown)",
    )

    # reset command
    reset_parser = subparsers.add_parser(
        "reset",
        help="Reset internal state",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Route to command handlers
    if args.command == "analyze":
        return analyze(
            tasks_file=args.tasks_file,
            dependencies_file=args.dependencies_file,
            output_file=args.output,
            output_format=args.format,
            verbose=args.verbose,
        )
    elif args.command == "decide":
        return decide(
            goal=args.goal,
            tasks_file=args.tasks_file,
            dependencies_file=args.dependencies_file,
            analysis_file=args.analysis_file,
            output_file=args.output,
            output_format=args.format,
            verbose=args.verbose,
        )
    elif args.command == "plan":
        return plan(
            tasks_file=args.tasks_file,
            dependencies_file=args.dependencies_file,
            strategy_file=args.strategy_file,
            output_file=args.output,
            output_format=args.format,
            verbose=args.verbose,
        )
    elif args.command == "execute":
        return execute(
            plan_file=args.plan_file,
            output_file=args.output,
            output_format=args.format,
            simulate=args.simulate,
            verbose=args.verbose,
        )
    elif args.command == "document":
        return document(
            analysis_file=args.analysis_file,
            recommendation_file=args.recommendation_file,
            plan_file=args.plan_file,
            output_file=args.output,
            output_format=args.doc_format,
            verbose=args.verbose,
        )
    elif args.command == "reset":
        return reset(verbose=args.verbose)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
