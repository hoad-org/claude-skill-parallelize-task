#!/usr/bin/env python3
"""CLI interface for parallelize-task skill."""

import argparse
import sys
from typing import Any

from parallelizer_skill import __version__
from parallelizer_skill.execution_planner import ExecutionPlanner
from parallelizer_skill.models import Task


def main() -> int:
    """Main CLI entry point."""
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

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze task dependencies and generate execution plan",
    )
    analyze_parser.add_argument(
        "tasks_json",
        help="JSON file with task definitions",
    )
    analyze_parser.add_argument(
        "--output",
        default="execution_plan.json",
        help="Output file for execution plan",
    )

    # version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information",
    )

    args = parser.parse_args()

    if args.command == "version" or not args.command:
        print(f"parallelize-task {__version__}")
        return 0

    if args.command == "analyze":
        try:
            import json
            with open(args.tasks_json) as f:
                tasks_data = json.load(f)

            planner = ExecutionPlanner()
            plan = planner.plan([Task(**t) for t in tasks_data])

            with open(args.output, "w") as f:
                json.dump(plan.model_dump(), f, indent=2)

            if args.verbose:
                print(f"✅ Execution plan generated: {args.output}")

            return 0
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
