"""Directed Acyclic Graph analysis for task dependencies."""

from typing import Dict, List, Set, Tuple
import networkx as nx

from orchestration_skill.models import Task, TaskDependency, DependencyType


class DAGAnalyzer:
    """Analyzes task dependencies as a DAG."""

    def __init__(self, tasks: List[Task], dependencies: List[TaskDependency]) -> None:
        """Initialize analyzer with tasks and dependencies."""
        self.tasks = {task.id: task for task in tasks}
        self.dependencies = dependencies
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        """Build networkx directed graph from dependencies."""
        graph: nx.DiGraph = nx.DiGraph()

        for task in self.tasks.values():
            graph.add_node(task.id, task=task)

        for dep in self.dependencies:
            if dep.dependency_type == DependencyType.HARD:
                graph.add_edge(dep.source_task_id, dep.target_task_id, type="hard")
            elif dep.dependency_type == DependencyType.DATA:
                graph.add_edge(dep.source_task_id, dep.target_task_id, type="data")

        return graph

    def has_cycles(self) -> bool:
        """Check if graph contains cycles (invalid for task orchestration)."""
        return not nx.is_directed_acyclic_graph(self.graph)

    def get_cycles(self) -> List[List[str]]:
        """Get all cycles in the graph."""
        try:
            return list(nx.simple_cycles(self.graph))
        except:
            return []

    def get_critical_path(self) -> List[str]:
        """Find the critical path (longest path from start to end)."""
        if not nx.nodes(self.graph):
            return []

        longest_path: List[str] = []
        max_length = 0

        for source in self._get_source_tasks():
            for target in self._get_sink_tasks():
                try:
                    paths = list(nx.all_simple_paths(self.graph, source, target))
                    for path in paths:
                        path_length = sum(self.tasks[task_id].estimated_duration for task_id in path)
                        if path_length > max_length:
                            max_length = path_length
                            longest_path = path
                except nx.NetworkXNoPath:
                    pass

        return longest_path

    def get_source_tasks(self) -> List[str]:
        """Get tasks with no dependencies (sources)."""
        return self._get_source_tasks()

    def get_sink_tasks(self) -> List[str]:
        """Get tasks with no dependents (sinks)."""
        return self._get_sink_tasks()

    def _get_source_tasks(self) -> List[str]:
        """Internal method to get source tasks."""
        return [node for node in self.graph.nodes() if self.graph.in_degree(node) == 0]

    def _get_sink_tasks(self) -> List[str]:
        """Internal method to get sink tasks."""
        return [node for node in self.graph.nodes() if self.graph.out_degree(node) == 0]

    def get_dependencies(self, task_id: str) -> List[str]:
        """Get direct dependencies of a task."""
        return list(self.graph.predecessors(task_id))

    def get_dependents(self, task_id: str) -> List[str]:
        """Get tasks that depend on this task."""
        return list(self.graph.successors(task_id))

    def get_all_dependencies(self, task_id: str) -> Set[str]:
        """Get all transitive dependencies of a task."""
        return set(nx.ancestors(self.graph, task_id))

    def get_all_dependents(self, task_id: str) -> Set[str]:
        """Get all tasks that transitively depend on this task."""
        return set(nx.descendants(self.graph, task_id))

    def get_levels(self) -> Dict[int, List[str]]:
        """Get tasks organized by dependency level (topological sort)."""
        levels: Dict[int, List[str]] = {}

        if not self.has_cycles():
            for level, tasks in enumerate(nx.topological_generations(self.graph)):
                levels[level] = list(tasks)

        return levels

    def get_parallelizable_groups(self) -> List[List[str]]:
        """Identify groups of tasks that can run in parallel."""
        groups: List[List[str]] = []
        levels = self.get_levels()

        for level_tasks in levels.values():
            parallelizable = []
            for task_id in level_tasks:
                task = self.tasks[task_id]
                if task.parallelizable:
                    parallelizable.append(task_id)

            if parallelizable:
                groups.append(parallelizable)

        return groups

    def get_bottlenecks(self) -> List[str]:
        """Identify tasks that are bottlenecks (many downstream dependencies)."""
        bottlenecks = []

        for task_id in self.graph.nodes():
            dependents = self.get_all_dependents(task_id)
            if len(dependents) > 2:
                bottlenecks.append(task_id)

        return sorted(bottlenecks, key=lambda t: len(self.get_all_dependents(t)), reverse=True)
