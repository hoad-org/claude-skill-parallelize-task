"""Shared fixtures for integration tests."""

import tempfile
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

import pytest

from parallelizer_skill.models import (
    Task,
    TaskDependency,
    DependencyType,
    TaskPriority,
    WorkflowAnalysis,
    ExecutionPlan,
    ExecutionPhase,
    TaskGroup,
)
from parallelizer_skill.decision_engine import DecisionRecommendation, ParallelizationGoal
from parallelizer_skill.config import reset_config


@pytest.fixture(autouse=True)
def _reset_config():
    """Reset config before each test."""
    reset_config()
    yield
    reset_config()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# SIMPLE WORKFLOW FIXTURES
# ============================================================================


@pytest.fixture
def simple_tasks() -> List[Task]:
    """Create 5 simple tasks with minimal dependencies."""
    return [
        Task(
            id="t1",
            name="Task 1",
            description="First task",
            estimated_duration=1.0,
            parallelizable=True,
            priority=TaskPriority.NORMAL,
        ),
        Task(
            id="t2",
            name="Task 2",
            description="Second task",
            estimated_duration=2.0,
            parallelizable=True,
            priority=TaskPriority.NORMAL,
        ),
        Task(
            id="t3",
            name="Task 3",
            description="Third task",
            estimated_duration=1.5,
            parallelizable=True,
            priority=TaskPriority.NORMAL,
        ),
        Task(
            id="t4",
            name="Task 4",
            description="Fourth task",
            estimated_duration=1.0,
            parallelizable=True,
            priority=TaskPriority.NORMAL,
        ),
        Task(
            id="t5",
            name="Task 5",
            description="Fifth task",
            estimated_duration=2.5,
            parallelizable=True,
            priority=TaskPriority.NORMAL,
        ),
    ]


@pytest.fixture
def simple_dependencies() -> List[TaskDependency]:
    """Create 2 soft dependencies for simple workflow."""
    return [
        TaskDependency(
            source_task_id="t1",
            target_task_id="t2",
            dependency_type=DependencyType.SOFT,
            condition="t1.status == SUCCESS",
        ),
        TaskDependency(
            source_task_id="t2",
            target_task_id="t3",
            dependency_type=DependencyType.SOFT,
        ),
    ]


# ============================================================================
# COMPLEX WORKFLOW FIXTURES
# ============================================================================


@pytest.fixture
def complex_tasks() -> List[Task]:
    """Create 10 complex tasks with various characteristics."""
    return [
        Task(id="a1", name="Data Ingestion", estimated_duration=5.0, parallelizable=False, priority=TaskPriority.CRITICAL),
        Task(id="a2", name="Validation", estimated_duration=3.0, parallelizable=False, priority=TaskPriority.HIGH),
        Task(
            id="b1",
            name="Processing A",
            estimated_duration=4.0,
            parallelizable=True,
            resource_type="cpu",
            max_concurrent=2,
            priority=TaskPriority.HIGH,
        ),
        Task(
            id="b2",
            name="Processing B",
            estimated_duration=4.0,
            parallelizable=True,
            resource_type="cpu",
            max_concurrent=2,
            priority=TaskPriority.HIGH,
        ),
        Task(
            id="b3",
            name="Processing C",
            estimated_duration=3.5,
            parallelizable=True,
            resource_type="cpu",
            max_concurrent=2,
            priority=TaskPriority.NORMAL,
        ),
        Task(
            id="c1",
            name="GPU Transform",
            estimated_duration=8.0,
            parallelizable=False,
            resource_type="gpu",
            priority=TaskPriority.CRITICAL,
        ),
        Task(id="d1", name="Aggregation", estimated_duration=2.0, parallelizable=False, priority=TaskPriority.HIGH),
        Task(id="d2", name="Analytics", estimated_duration=3.0, parallelizable=True, priority=TaskPriority.NORMAL),
        Task(id="d3", name="Reporting", estimated_duration=2.5, parallelizable=True, priority=TaskPriority.NORMAL),
        Task(
            id="e1",
            name="Output Export",
            estimated_duration=4.0,
            parallelizable=False,
            resource_type="network",
            priority=TaskPriority.NORMAL,
        ),
    ]


@pytest.fixture
def complex_dependencies() -> List[TaskDependency]:
    """Create 15 hard dependencies for complex workflow."""
    return [
        # Data preparation chain
        TaskDependency(source_task_id="a1", target_task_id="a2", dependency_type=DependencyType.HARD),
        # Parallel processing depends on validation
        TaskDependency(source_task_id="a2", target_task_id="b1", dependency_type=DependencyType.HARD),
        TaskDependency(source_task_id="a2", target_task_id="b2", dependency_type=DependencyType.HARD),
        TaskDependency(source_task_id="a2", target_task_id="b3", dependency_type=DependencyType.HARD),
        # GPU depends on some processing
        TaskDependency(source_task_id="b1", target_task_id="c1", dependency_type=DependencyType.HARD),
        TaskDependency(source_task_id="b2", target_task_id="c1", dependency_type=DependencyType.HARD),
        # Aggregation depends on GPU
        TaskDependency(source_task_id="c1", target_task_id="d1", dependency_type=DependencyType.HARD),
        # Analytics depends on processing
        TaskDependency(source_task_id="b3", target_task_id="d2", dependency_type=DependencyType.HARD),
        # Reporting depends on aggregation
        TaskDependency(source_task_id="d1", target_task_id="d3", dependency_type=DependencyType.HARD),
        # Export depends on all downstream
        TaskDependency(source_task_id="d1", target_task_id="e1", dependency_type=DependencyType.HARD),
        TaskDependency(source_task_id="d2", target_task_id="e1", dependency_type=DependencyType.HARD),
        TaskDependency(source_task_id="d3", target_task_id="e1", dependency_type=DependencyType.HARD),
        # Soft data flow dependencies
        TaskDependency(source_task_id="b1", target_task_id="b2", dependency_type=DependencyType.SOFT),
        TaskDependency(source_task_id="b2", target_task_id="b3", dependency_type=DependencyType.SOFT),
        TaskDependency(source_task_id="c1", target_task_id="d2", dependency_type=DependencyType.DATA),
    ]


# ============================================================================
# REAL-WORLD SCENARIO FIXTURES
# ============================================================================


@pytest.fixture
def data_pipeline_tasks() -> List[Task]:
    """Create 20 tasks representing a data pipeline."""
    tasks = []

    # Ingestion layer (3 tasks)
    for i in range(1, 4):
        tasks.append(
            Task(
                id=f"ingest_{i}",
                name=f"Data Ingest {i}",
                estimated_duration=2.0,
                parallelizable=False,
                priority=TaskPriority.CRITICAL,
            )
        )

    # Validation layer (4 tasks)
    for i in range(1, 5):
        tasks.append(
            Task(
                id=f"validate_{i}",
                name=f"Validate {i}",
                estimated_duration=1.5,
                parallelizable=True,
                priority=TaskPriority.HIGH,
            )
        )

    # Transformation layer (6 tasks)
    for i in range(1, 7):
        tasks.append(
            Task(
                id=f"transform_{i}",
                name=f"Transform {i}",
                estimated_duration=3.0,
                parallelizable=True,
                resource_type="cpu",
                max_concurrent=3,
                priority=TaskPriority.HIGH,
            )
        )

    # Enrichment layer (4 tasks)
    for i in range(1, 5):
        tasks.append(
            Task(
                id=f"enrich_{i}",
                name=f"Enrich {i}",
                estimated_duration=2.5,
                parallelizable=True,
                priority=TaskPriority.NORMAL,
            )
        )

    # Output layer (3 tasks)
    for i in range(1, 4):
        tasks.append(
            Task(
                id=f"output_{i}",
                name=f"Output {i}",
                estimated_duration=2.0,
                parallelizable=True,
                resource_type="network",
                priority=TaskPriority.NORMAL,
            )
        )

    return tasks


@pytest.fixture
def data_pipeline_dependencies(data_pipeline_tasks) -> List[TaskDependency]:
    """Create data dependencies for pipeline workflow."""
    deps = []

    # Validation depends on ingestion
    for i in range(1, 5):
        deps.append(TaskDependency(source_task_id="ingest_1", target_task_id=f"validate_{i}", dependency_type=DependencyType.HARD))

    # Transformation depends on validation
    for i in range(1, 7):
        # Each transform depends on at least one validation
        validate_idx = ((i - 1) % 4) + 1
        deps.append(TaskDependency(source_task_id=f"validate_{validate_idx}", target_task_id=f"transform_{i}", dependency_type=DependencyType.HARD))

    # Enrichment depends on transformation
    for i in range(1, 5):
        transform_idx = ((i - 1) % 6) + 1
        deps.append(TaskDependency(source_task_id=f"transform_{transform_idx}", target_task_id=f"enrich_{i}", dependency_type=DependencyType.HARD))

    # Output depends on enrichment
    for i in range(1, 4):
        enrich_idx = ((i - 1) % 4) + 1
        deps.append(TaskDependency(source_task_id=f"enrich_{enrich_idx}", target_task_id=f"output_{i}", dependency_type=DependencyType.HARD))

    return deps


@pytest.fixture
def microservices_deployment_tasks() -> List[Task]:
    """Create 15 tasks for microservices deployment."""
    services = [
        "auth", "api", "database", "cache", "queue",
        "worker1", "worker2", "worker3", "analytics", "scheduler",
        "gateway", "config", "monitoring", "logging", "backup",
    ]

    tasks = []
    for service in services:
        tasks.append(
            Task(
                id=f"deploy_{service}",
                name=f"Deploy {service}",
                estimated_duration=5.0 if service in ["database", "cache"] else 3.0,
                parallelizable=True,
                priority=TaskPriority.HIGH if service in ["auth", "api", "database"] else TaskPriority.NORMAL,
                resource_type="kubernetes",
            )
        )

    return tasks


@pytest.fixture
def microservices_deployment_dependencies(microservices_deployment_tasks) -> List[TaskDependency]:
    """Create ordering dependencies for microservices deployment."""
    deps = []

    # Critical dependencies
    critical_order = [
        ("deploy_config", "deploy_database"),
        ("deploy_database", "deploy_cache"),
        ("deploy_cache", "deploy_queue"),
        ("deploy_queue", "deploy_auth"),
        ("deploy_auth", "deploy_api"),
        ("deploy_api", "deploy_gateway"),
    ]

    for source, target in critical_order:
        deps.append(TaskDependency(source_task_id=source, target_task_id=target, dependency_type=DependencyType.HARD))

    # Worker dependencies
    for i in range(1, 4):
        deps.append(TaskDependency(source_task_id="deploy_queue", target_task_id=f"deploy_worker{i}", dependency_type=DependencyType.HARD))

    # Analytics and scheduler after workers
    deps.append(TaskDependency(source_task_id="deploy_worker1", target_task_id="deploy_analytics", dependency_type=DependencyType.SOFT))
    deps.append(TaskDependency(source_task_id="deploy_worker1", target_task_id="deploy_scheduler", dependency_type=DependencyType.SOFT))

    # Monitoring and logging can run in parallel with deployment
    deps.append(TaskDependency(source_task_id="deploy_api", target_task_id="deploy_monitoring", dependency_type=DependencyType.SOFT))
    deps.append(TaskDependency(source_task_id="deploy_api", target_task_id="deploy_logging", dependency_type=DependencyType.SOFT))

    # Backup after all services up
    deps.append(TaskDependency(source_task_id="deploy_database", target_task_id="deploy_backup", dependency_type=DependencyType.HARD))

    return deps


# ============================================================================
# DECISION RECOMMENDATION FIXTURES
# ============================================================================


@pytest.fixture
def aggressive_recommendation() -> DecisionRecommendation:
    """Create aggressive parallelization recommendation."""
    return DecisionRecommendation(
        strategy_type="aggressive",
        max_parallel_tasks=8,
        recommended_batch_size=10,
        recommended_retry_count=1,
        recommended_checkpoint_interval=10,
        parallel_execution=True,
        resource_aware=False,
        monitoring_intensity="low",
        escalation_level="critical",
        rationale="Performance-focused strategy with high parallelization",
    )


@pytest.fixture
def balanced_recommendation() -> DecisionRecommendation:
    """Create balanced strategy recommendation."""
    return DecisionRecommendation(
        strategy_type="balanced",
        max_parallel_tasks=4,
        recommended_batch_size=5,
        recommended_retry_count=2,
        recommended_checkpoint_interval=5,
        parallel_execution=True,
        resource_aware=True,
        monitoring_intensity="normal",
        escalation_level="warning",
        rationale="Balanced approach between speed and reliability",
    )


@pytest.fixture
def conservative_recommendation() -> DecisionRecommendation:
    """Create conservative strategy recommendation."""
    return DecisionRecommendation(
        strategy_type="conservative",
        max_parallel_tasks=2,
        recommended_batch_size=3,
        recommended_retry_count=3,
        recommended_checkpoint_interval=2,
        parallel_execution=True,
        resource_aware=True,
        monitoring_intensity="intensive",
        escalation_level="info",
        rationale="Reliability-focused with intensive monitoring",
    )


# ============================================================================
# FILE FIXTURES
# ============================================================================


@pytest.fixture
def simple_tasks_file(temp_dir, simple_tasks) -> str:
    """Create temporary tasks JSON file."""
    file_path = temp_dir / "tasks.json"
    with open(file_path, "w") as f:
        json.dump([t.model_dump() for t in simple_tasks], f)
    return str(file_path)


@pytest.fixture
def simple_dependencies_file(temp_dir, simple_dependencies) -> str:
    """Create temporary dependencies JSON file."""
    file_path = temp_dir / "dependencies.json"
    with open(file_path, "w") as f:
        json.dump([d.model_dump() for d in simple_dependencies], f)
    return str(file_path)


@pytest.fixture
def complex_tasks_file(temp_dir, complex_tasks) -> str:
    """Create temporary complex tasks JSON file."""
    file_path = temp_dir / "complex_tasks.json"
    with open(file_path, "w") as f:
        json.dump([t.model_dump() for t in complex_tasks], f)
    return str(file_path)


@pytest.fixture
def complex_dependencies_file(temp_dir, complex_dependencies) -> str:
    """Create temporary complex dependencies JSON file."""
    file_path = temp_dir / "complex_dependencies.json"
    with open(file_path, "w") as f:
        json.dump([d.model_dump() for d in complex_dependencies], f)
    return str(file_path)
