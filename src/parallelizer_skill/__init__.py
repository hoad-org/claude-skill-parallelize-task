"""Claude skill for intelligent task parallelization and workflow optimization."""

__version__ = "1.1.0"

from parallelizer_skill.models import Task, TaskDependency, ExecutionPlan, TaskGroup
from parallelizer_skill.optimizer import TaskOrchestrator
from parallelizer_skill.dag_analyzer import DAGAnalyzer
from parallelizer_skill.execution_planner import ExecutionPlanner

__all__ = [
    "Task",
    "TaskDependency",
    "ExecutionPlan",
    "TaskGroup",
    "TaskOrchestrator",
    "DAGAnalyzer",
    "ExecutionPlanner",
]
