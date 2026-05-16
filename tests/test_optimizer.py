"""Tests for task orchestrator."""

import pytest
from orchestration_skill.optimizer import TaskOrchestrator
from orchestration_skill.models import TaskPriority


@pytest.fixture
def orchestrator() -> TaskOrchestrator:
    """Create a task orchestrator."""
    return TaskOrchestrator()


@pytest.mark.unit
def test_add_task(orchestrator: TaskOrchestrator):
    """Test adding a task."""
    orchestrator.add_task("task1", "Task 1", estimated_duration=1.0)
    assert "task1" in orchestrator.tasks
    assert orchestrator.tasks["task1"].name == "Task 1"


@pytest.mark.unit
def test_add_multiple_tasks(orchestrator: TaskOrchestrator):
    """Test adding multiple tasks."""
    orchestrator.add_task("task1", "Task 1")
    orchestrator.add_task("task2", "Task 2")
    orchestrator.add_task("task3", "Task 3")
    assert len(orchestrator.tasks) == 3


@pytest.mark.unit
def test_add_dependency(orchestrator: TaskOrchestrator):
    """Test adding dependencies."""
    orchestrator.add_task("task1", "Task 1")
    orchestrator.add_task("task2", "Task 2")
    orchestrator.add_dependency("task1", "task2")
    assert len(orchestrator.dependencies) == 1


@pytest.mark.unit
def test_add_dependency_missing_task(orchestrator: TaskOrchestrator):
    """Test adding dependency with missing task."""
    orchestrator.add_task("task1", "Task 1")
    with pytest.raises(ValueError):
        orchestrator.add_dependency("task1", "task2")


@pytest.mark.optimization
def test_linear_workflow_optimization(orchestrator: TaskOrchestrator):
    """Test optimization of linear workflow."""
    orchestrator.add_task("task1", "Task 1", estimated_duration=1.0)
    orchestrator.add_task("task2", "Task 2", estimated_duration=2.0)
    orchestrator.add_task("task3", "Task 3", estimated_duration=1.5)
    orchestrator.add_dependency("task1", "task2")
    orchestrator.add_dependency("task2", "task3")

    plan = orchestrator.optimize()
    assert plan.serial_duration == 4.5
    assert plan.parallel_duration == 4.5
    assert plan.efficiency_gain == 0.0


@pytest.mark.optimization
def test_parallel_workflow_optimization(orchestrator: TaskOrchestrator):
    """Test optimization of parallel workflow."""
    orchestrator.add_task("task1", "Task 1", estimated_duration=1.0, parallelizable=True)
    orchestrator.add_task("task2", "Task 2", estimated_duration=1.0, parallelizable=True)
    orchestrator.add_task("task3", "Task 3", estimated_duration=1.0)
    orchestrator.add_dependency("task1", "task3")
    orchestrator.add_dependency("task2", "task3")

    plan = orchestrator.optimize()
    assert plan.serial_duration == 3.0
    assert plan.parallel_duration == 2.0


@pytest.mark.unit
def test_analyze_workflow(orchestrator: TaskOrchestrator):
    """Test workflow analysis."""
    orchestrator.add_task("task1", "Task 1")
    orchestrator.add_task("task2", "Task 2")
    orchestrator.add_dependency("task1", "task2")

    analysis = orchestrator.analyze()
    assert analysis["total_tasks"] == 2
    assert not analysis["has_cycles"]
    assert "task1" in analysis["source_tasks"]


@pytest.mark.unit
def test_get_task_info(orchestrator: TaskOrchestrator):
    """Test getting task information."""
    orchestrator.add_task("task1", "Task 1", priority=TaskPriority.HIGH)
    orchestrator.add_task("task2", "Task 2")
    orchestrator.add_dependency("task1", "task2")

    info = orchestrator.get_task_info("task1")
    assert info["name"] == "Task 1"
    assert info["direct_dependents"] == ["task2"]
    assert info["is_on_critical_path"]


@pytest.mark.unit
def test_validate_valid_workflow(orchestrator: TaskOrchestrator):
    """Test validation of valid workflow."""
    orchestrator.add_task("task1", "Task 1")
    orchestrator.add_task("task2", "Task 2")
    orchestrator.add_dependency("task1", "task2")

    validation = orchestrator.validate()
    assert validation["is_valid"]


@pytest.mark.unit
def test_validate_cyclic_workflow(orchestrator: TaskOrchestrator):
    """Test validation of cyclic workflow."""
    orchestrator.add_task("task1", "Task 1")
    orchestrator.add_task("task2", "Task 2")
    orchestrator.add_task("task3", "Task 3")
    orchestrator.add_dependency("task1", "task2")
    orchestrator.add_dependency("task2", "task3")
    orchestrator.add_dependency("task3", "task1")

    validation = orchestrator.validate()
    assert not validation["is_valid"]
    assert len(validation["issues"]) > 0


@pytest.mark.unit
def test_optimize_empty_orchestrator(orchestrator: TaskOrchestrator):
    """Test optimization with no tasks."""
    with pytest.raises(ValueError):
        orchestrator.optimize()
