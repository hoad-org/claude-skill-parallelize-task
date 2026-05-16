"""Main orchestrator for task optimization."""

from typing import Dict, List, Any, Optional
from orchestration_skill.models import (
    Task,
    TaskDependency,
    ExecutionPlan,
    TaskPriority,
)
from orchestration_skill.execution_planner import ExecutionPlanner
from orchestration_skill.dag_analyzer import DAGAnalyzer


class TaskOrchestrator:
    """Main orchestrator for analyzing and optimizing task execution."""

    def __init__(self) -> None:
        """Initialize orchestrator."""
        self.tasks: Dict[str, Task] = {}
        self.dependencies: List[TaskDependency] = []

    def add_task(
        self,
        task_id: str,
        name: str,
        estimated_duration: float = 1.0,
        parallelizable: bool = True,
        priority: TaskPriority = TaskPriority.NORMAL,
        resource_type: Optional[str] = None,
        max_concurrent: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a task to the orchestrator."""
        task = Task(
            id=task_id,
            name=name,
            estimated_duration=estimated_duration,
            parallelizable=parallelizable,
            priority=priority,
            resource_type=resource_type,
            max_concurrent=max_concurrent,
            metadata=metadata or {},
        )
        self.tasks[task_id] = task

    def add_dependency(
        self,
        source_task_id: str,
        target_task_id: str,
        dependency_type: str = "hard",
    ) -> None:
        """Add a dependency between tasks."""
        if source_task_id not in self.tasks or target_task_id not in self.tasks:
            raise ValueError("Both source and target tasks must be added first")

        dependency = TaskDependency(
            source_task_id=source_task_id,
            target_task_id=target_task_id,
            dependency_type=dependency_type,
        )
        self.dependencies.append(dependency)

    def optimize(self) -> ExecutionPlan:
        """Generate optimal execution plan."""
        if not self.tasks:
            raise ValueError("No tasks added to orchestrator")

        planner = ExecutionPlanner(list(self.tasks.values()), self.dependencies)
        return planner.create_plan()

    def analyze(self) -> Dict[str, Any]:
        """Analyze task workflow."""
        analyzer = DAGAnalyzer(list(self.tasks.values()), self.dependencies)

        return {
            "total_tasks": len(self.tasks),
            "has_cycles": analyzer.has_cycles(),
            "cycles": analyzer.get_cycles() if analyzer.has_cycles() else [],
            "source_tasks": analyzer.get_source_tasks(),
            "sink_tasks": analyzer.get_sink_tasks(),
            "critical_path": analyzer.get_critical_path(),
            "parallelizable_groups": analyzer.get_parallelizable_groups(),
            "bottlenecks": analyzer.get_bottlenecks(),
            "levels": analyzer.get_levels(),
        }

    def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """Get detailed information about a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        analyzer = DAGAnalyzer(list(self.tasks.values()), self.dependencies)
        task = self.tasks[task_id]

        return {
            "id": task.id,
            "name": task.name,
            "duration": task.estimated_duration,
            "parallelizable": task.parallelizable,
            "priority": task.priority,
            "direct_dependencies": analyzer.get_dependencies(task_id),
            "all_dependencies": list(analyzer.get_all_dependencies(task_id)),
            "direct_dependents": analyzer.get_dependents(task_id),
            "all_dependents": list(analyzer.get_all_dependents(task_id)),
            "is_on_critical_path": task_id in analyzer.get_critical_path(),
        }

    def validate(self) -> Dict[str, Any]:
        """Validate the workflow for issues."""
        analyzer = DAGAnalyzer(list(self.tasks.values()), self.dependencies)
        issues: List[str] = []
        warnings: List[str] = []

        if analyzer.has_cycles():
            issues.append(f"Circular dependency detected: {analyzer.get_cycles()}")

        bottlenecks = analyzer.get_bottlenecks()
        if bottlenecks:
            warnings.append(f"Bottleneck tasks: {', '.join(bottlenecks[:3])}")

        critical_path = analyzer.get_critical_path()
        if len(critical_path) == len(self.tasks):
            warnings.append("All tasks are on critical path - minimal parallelization opportunity")

        resource_conflicts = {}
        for task_id, task in self.tasks.items():
            if task.resource_type:
                if task.resource_type not in resource_conflicts:
                    resource_conflicts[task.resource_type] = []
                resource_conflicts[task.resource_type].append(task_id)

        for resource_type, task_ids in resource_conflicts.items():
            if len(task_ids) > 2:
                warnings.append(f"Many tasks require resource '{resource_type}': {len(task_ids)} tasks")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_validations": len(issues) + len(warnings),
        }
