"""Creates optimal execution plans for task workflows."""

from typing import Dict, List, Set
from parallelizer_skill.models import (
    Task,
    TaskDependency,
    ExecutionPlan,
    ExecutionPhase,
    TaskGroup,
)
from parallelizer_skill.dag_analyzer import DAGAnalyzer


class ExecutionPlanner:
    """Plans optimal execution of tasks."""

    def __init__(self, tasks: List[Task], dependencies: List[TaskDependency]) -> None:
        """Initialize planner."""
        self.tasks = {task.id: task for task in tasks}
        self.dependencies = dependencies
        self.analyzer = DAGAnalyzer(tasks, dependencies)

    def create_plan(self) -> ExecutionPlan:
        """Create optimal execution plan."""
        if self.analyzer.has_cycles():
            raise ValueError(f"Circular dependency detected: {self.analyzer.get_cycles()}")

        phases = self._create_phases()
        critical_path = self.analyzer.get_critical_path()
        parallelizable_groups = self._identify_parallelizable_groups()

        serial_duration = sum(task.estimated_duration for task in self.tasks.values())
        parallel_duration = self._calculate_parallel_duration(phases)
        efficiency_gain = ((serial_duration - parallel_duration) / serial_duration * 100) if serial_duration > 0 else 0

        return ExecutionPlan(
            id="plan-001",
            total_tasks=len(self.tasks),
            serial_duration=serial_duration,
            parallel_duration=parallel_duration,
            efficiency_gain=efficiency_gain,
            phases=phases,
            critical_path=critical_path,
            parallelizable_groups=parallelizable_groups,
            resource_conflicts=self._detect_resource_conflicts(),
            safety_issues=self._identify_safety_issues(),
            optimization_notes=self._generate_optimization_notes(parallel_duration, serial_duration),
        )

    def _create_phases(self) -> List[ExecutionPhase]:
        """Create execution phases from task levels."""
        phases: List[ExecutionPhase] = []
        levels = self.analyzer.get_levels()

        for phase_num, (level, task_ids) in enumerate(sorted(levels.items()), 1):
            groups = self._group_tasks_for_phase(task_ids)
            phase_duration = self._calculate_phase_duration(groups)

            phase = ExecutionPhase(
                phase_number=phase_num,
                task_groups=groups,
                is_parallel=len(groups) > 1,
                estimated_duration=phase_duration,
                sync_point_required=True,
            )
            phases.append(phase)

        return phases

    def _group_tasks_for_phase(self, task_ids: List[str]) -> List[TaskGroup]:
        """Group tasks in a phase optimally."""
        groups: List[TaskGroup] = []
        grouped_tasks: Set[str] = set()

        for task_id in sorted(task_ids):
            if task_id in grouped_tasks:
                continue

            task = self.tasks[task_id]

            if task.parallelizable:
                compatible_tasks = self._find_compatible_tasks(task_id, task_ids, grouped_tasks)
                all_tasks = [task_id] + compatible_tasks

                duration = sum(self.tasks[t].estimated_duration for t in all_tasks)
                group = TaskGroup(
                    id=f"group-{task_id}",
                    tasks=all_tasks,
                    estimated_duration=duration,
                    can_parallelize=True,
                )
                groups.append(group)
                grouped_tasks.update(all_tasks)
            else:
                duration = task.estimated_duration
                group = TaskGroup(
                    id=f"group-{task_id}",
                    tasks=[task_id],
                    estimated_duration=duration,
                    can_parallelize=False,
                )
                groups.append(group)
                grouped_tasks.add(task_id)

        return groups

    def _find_compatible_tasks(self, base_task_id: str, available_tasks: List[str], grouped_tasks: Set[str]) -> List[str]:
        """Find tasks that can run in parallel with base task."""
        compatible = []
        base_task = self.tasks[base_task_id]

        for task_id in available_tasks:
            if task_id == base_task_id or task_id in grouped_tasks:
                continue

            task = self.tasks[task_id]

            if not task.parallelizable:
                continue

            if base_task.resource_type and task.resource_type == base_task.resource_type:
                continue

            compatible.append(task_id)

        return compatible

    def _identify_parallelizable_groups(self) -> Dict[str, List[str]]:
        """Identify groups of tasks that can be parallelized."""
        groups: Dict[str, List[str]] = {}
        levels = self.analyzer.get_levels()

        for level, task_ids in levels.items():
            parallelizable = [t for t in task_ids if self.tasks[t].parallelizable]
            if len(parallelizable) > 1:
                groups[f"level-{level}"] = parallelizable

        return groups

    def _detect_resource_conflicts(self) -> List[str]:
        """Detect potential resource conflicts."""
        conflicts: List[str] = []
        resource_tasks: Dict[str, List[str]] = {}

        for task_id, task in self.tasks.items():
            if task.resource_type:
                if task.resource_type not in resource_tasks:
                    resource_tasks[task.resource_type] = []
                resource_tasks[task.resource_type].append(task_id)

        for resource_type, task_ids in resource_tasks.items():
            if len(task_ids) > self.tasks[task_ids[0]].max_concurrent:
                conflicts.append(f"Resource '{resource_type}' conflict: {len(task_ids)} tasks need {resource_type}")

        return conflicts

    def _identify_safety_issues(self) -> List[str]:
        """Identify safety issues in the execution plan."""
        issues: List[str] = []

        if self.analyzer.has_cycles():
            issues.append("Circular dependency detected - cannot execute")

        return issues

    def _calculate_phase_duration(self, groups: List[TaskGroup]) -> float:
        """Calculate estimated duration for a phase."""
        if groups:
            return max(group.estimated_duration for group in groups)
        return 0.0

    def _calculate_parallel_duration(self, phases: List[ExecutionPhase]) -> float:
        """Calculate total parallel execution duration."""
        return sum(phase.estimated_duration for phase in phases)

    def _generate_optimization_notes(self, parallel_duration: float, serial_duration: float) -> List[str]:
        """Generate notes on optimization strategy."""
        notes: List[str] = []

        if parallel_duration >= serial_duration:
            notes.append("No parallelization benefit - task dependencies create serialization bottleneck")
        else:
            speedup = serial_duration / parallel_duration
            notes.append(f"Optimal parallelization achieves {speedup:.1f}x speedup")

        bottlenecks = self.analyzer.get_bottlenecks()
        if bottlenecks:
            notes.append(f"Critical bottlenecks: {', '.join(bottlenecks[:3])}")

        critical_path = self.analyzer.get_critical_path()
        if critical_path:
            notes.append(f"Critical path length: {len(critical_path)} tasks")

        return notes
