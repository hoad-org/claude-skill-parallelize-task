"""Tests for DAG analyzer."""

import pytest
from parallelizer_skill.models import Task, TaskDependency, DependencyType
from parallelizer_skill.dag_analyzer import DAGAnalyzer


@pytest.fixture
def simple_tasks() -> list[Task]:
    """Create simple linear tasks."""
    return [
        Task(id="task1", name="Task 1", estimated_duration=1.0),
        Task(id="task2", name="Task 2", estimated_duration=2.0),
        Task(id="task3", name="Task 3", estimated_duration=1.5),
    ]


@pytest.fixture
def simple_dependencies(simple_tasks) -> list[TaskDependency]:
    """Create linear dependencies."""
    return [
        TaskDependency(source_task_id="task1", target_task_id="task2"),
        TaskDependency(source_task_id="task2", target_task_id="task3"),
    ]


@pytest.fixture
def parallel_tasks() -> list[Task]:
    """Create tasks that can run in parallel."""
    return [
        Task(id="task1", name="Task 1", estimated_duration=1.0),
        Task(id="task2", name="Task 2", estimated_duration=1.0),
        Task(id="task3", name="Task 3", estimated_duration=1.0),
        Task(id="task4", name="Task 4", estimated_duration=1.0),
    ]


@pytest.fixture
def parallel_dependencies(parallel_tasks) -> list[TaskDependency]:
    """Create parallel dependencies."""
    return [
        TaskDependency(source_task_id="task1", target_task_id="task3"),
        TaskDependency(source_task_id="task2", target_task_id="task4"),
    ]


@pytest.mark.unit
def test_acyclic_graph_detection(simple_tasks, simple_dependencies):
    """Test detection of acyclic graphs."""
    analyzer = DAGAnalyzer(simple_tasks, simple_dependencies)
    assert not analyzer.has_cycles()


@pytest.mark.unit
def test_cyclic_graph_detection(simple_tasks):
    """Test detection of cyclic dependencies."""
    cyclic_deps = [
        TaskDependency(source_task_id="task1", target_task_id="task2"),
        TaskDependency(source_task_id="task2", target_task_id="task3"),
        TaskDependency(source_task_id="task3", target_task_id="task1"),
    ]
    analyzer = DAGAnalyzer(simple_tasks, cyclic_deps)
    assert analyzer.has_cycles()
    assert len(analyzer.get_cycles()) > 0


@pytest.mark.unit
def test_source_tasks(simple_tasks, simple_dependencies):
    """Test identification of source tasks."""
    analyzer = DAGAnalyzer(simple_tasks, simple_dependencies)
    sources = analyzer.get_source_tasks()
    assert "task1" in sources
    assert "task2" not in sources


@pytest.mark.unit
def test_sink_tasks(simple_tasks, simple_dependencies):
    """Test identification of sink tasks."""
    analyzer = DAGAnalyzer(simple_tasks, simple_dependencies)
    sinks = analyzer.get_sink_tasks()
    assert "task3" in sinks
    assert "task1" not in sinks


@pytest.mark.dag
def test_critical_path(simple_tasks, simple_dependencies):
    """Test critical path calculation."""
    analyzer = DAGAnalyzer(simple_tasks, simple_dependencies)
    path = analyzer.get_critical_path()
    assert path == ["task1", "task2", "task3"]


@pytest.mark.dag
def test_dependencies_retrieval(simple_tasks, simple_dependencies):
    """Test dependency retrieval."""
    analyzer = DAGAnalyzer(simple_tasks, simple_dependencies)
    deps = analyzer.get_dependencies("task2")
    assert "task1" in deps
    assert len(deps) == 1


@pytest.mark.dag
def test_dependents_retrieval(simple_tasks, simple_dependencies):
    """Test dependents retrieval."""
    analyzer = DAGAnalyzer(simple_tasks, simple_dependencies)
    deps = analyzer.get_dependents("task2")
    assert "task3" in deps
    assert len(deps) == 1


@pytest.mark.dag
def test_parallelizable_groups(parallel_tasks, parallel_dependencies):
    """Test identification of parallelizable task groups."""
    analyzer = DAGAnalyzer(parallel_tasks, parallel_dependencies)
    groups = analyzer.get_parallelizable_groups()
    assert len(groups) > 0
    assert "task1" in groups[0] or "task2" in groups[0]


@pytest.mark.dag
def test_topological_levels(simple_tasks, simple_dependencies):
    """Test topological sorting."""
    analyzer = DAGAnalyzer(simple_tasks, simple_dependencies)
    levels = analyzer.get_levels()
    assert len(levels) == 3
    assert "task1" in levels[0]
    assert "task2" in levels[1]
    assert "task3" in levels[2]


@pytest.mark.unit
def test_bottleneck_detection(simple_tasks):
    """Test bottleneck identification."""
    deps = [
        TaskDependency(source_task_id="task1", target_task_id="task2"),
        TaskDependency(source_task_id="task1", target_task_id="task3"),
    ]
    analyzer = DAGAnalyzer(simple_tasks, deps)
    bottlenecks = analyzer.get_bottlenecks()
    assert "task1" in bottlenecks
