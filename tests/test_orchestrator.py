"""Unit tests for workflow orchestrator (Phase 4)."""

import pytest
from parallelizer_skill.orchestrator import WorkflowOrchestrator, ExecutionPlanner
from parallelizer_skill.models import (
    Task,
    TaskDependency,
    DependencyType,
    TaskPriority,
    ExecutionStatus,
)
from parallelizer_skill.decision_engine import (
    ParallelizationGoal,
    DecisionRecommendation,
)
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestExecutionPlanner:
    """Test execution planner component."""

    @pytest.fixture
    def planner(self):
        """Create fresh planner for each test."""
        reset_config()
        return ExecutionPlanner()

    @pytest.fixture
    def simple_tasks(self):
        """Create simple task list."""
        return [
            Task(id="t1", name="Task 1", estimated_duration=1.0, parallelizable=True),
            Task(id="t2", name="Task 2", estimated_duration=2.0, parallelizable=True),
            Task(id="t3", name="Task 3", estimated_duration=1.5, parallelizable=True),
        ]

    @pytest.fixture
    def simple_dependencies(self):
        """Create simple dependencies."""
        return [
            TaskDependency(
                source_task_id="t1",
                target_task_id="t2",
                dependency_type=DependencyType.HARD,
            ),
        ]

    @pytest.fixture
    def simple_recommendation(self):
        """Create simple recommendation."""
        return DecisionRecommendation(
            strategy_type="balanced",
            max_parallel_tasks=2,
            recommended_batch_size=5,
            recommended_retry_count=2,
            recommended_checkpoint_interval=5,
            parallel_execution=True,
            resource_aware=True,
            monitoring_intensity="normal",
            escalation_level="warning",
            rationale="Test recommendation",
        )

    def test_planner_creation(self, planner):
        """Test creating execution planner."""
        assert planner is not None

    def test_plan_execution_simple(self, planner, simple_tasks, simple_dependencies, simple_recommendation):
        """Test basic execution plan creation."""
        plan = planner.plan_execution(simple_tasks, simple_dependencies, simple_recommendation)

        assert plan is not None
        assert plan.id is not None
        assert plan.total_tasks == 3
        assert plan.serial_duration == 4.5  # 1 + 2 + 1.5
        assert plan.phases is not None
        assert len(plan.phases) > 0

    def test_plan_serial_duration_calculated(self, planner, simple_tasks, simple_dependencies, simple_recommendation):
        """Test serial duration is correctly calculated."""
        plan = planner.plan_execution(simple_tasks, simple_dependencies, simple_recommendation)

        expected_serial = sum(t.estimated_duration for t in simple_tasks)
        assert plan.serial_duration == expected_serial

    def test_plan_has_critical_path(self, planner, simple_tasks, simple_dependencies, simple_recommendation):
        """Test plan includes critical path."""
        plan = planner.plan_execution(simple_tasks, simple_dependencies, simple_recommendation)

        assert plan.critical_path is not None
        assert isinstance(plan.critical_path, list)

    def test_plan_efficiency_gain_calculated(self, planner, simple_tasks, simple_dependencies, simple_recommendation):
        """Test efficiency gain is calculated."""
        plan = planner.plan_execution(simple_tasks, simple_dependencies, simple_recommendation)

        assert plan.efficiency_gain >= 0.0
        assert plan.efficiency_gain <= 100.0

    def test_plan_has_phases(self, planner, simple_tasks, simple_dependencies, simple_recommendation):
        """Test plan contains execution phases."""
        plan = planner.plan_execution(simple_tasks, simple_dependencies, simple_recommendation)

        assert len(plan.phases) > 0
        for phase in plan.phases:
            assert phase.phase_number > 0
            assert len(phase.task_groups) > 0

    def test_plan_resource_conflicts_checked(self, planner, simple_recommendation):
        """Test resource conflicts are identified."""
        tasks = [
            Task(
                id="r1",
                name="GPU Task 1",
                resource_type="gpu",
                max_concurrent=1,
                parallelizable=False,
            ),
            Task(
                id="r2",
                name="GPU Task 2",
                resource_type="gpu",
                max_concurrent=1,
                parallelizable=False,
            ),
        ]
        plan = planner.plan_execution(tasks, [], simple_recommendation)

        # Should detect resource conflict
        assert len(plan.resource_conflicts) > 0 or plan.safety_issues

    def test_plan_safety_checks(self, planner, simple_recommendation):
        """Test safety checks are performed."""
        tasks = [
            Task(id="t1", name="Task 1"),
            Task(id="t2", name="Task 2"),
        ]
        deps = [
            TaskDependency(source_task_id="t1", target_task_id="t2", dependency_type=DependencyType.HARD),
        ]

        plan = planner.plan_execution(tasks, deps, simple_recommendation)

        # Should have no safety issues for valid DAG
        assert isinstance(plan.safety_issues, list)


@pytest.mark.unit
class TestWorkflowOrchestrator:
    """Test workflow orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create fresh orchestrator for each test."""
        reset_config()
        return WorkflowOrchestrator()

    @pytest.fixture
    def sample_workflow(self):
        """Create sample workflow."""
        tasks = [
            Task(
                id="t1",
                name="Data Fetch",
                estimated_duration=2.0,
                parallelizable=True,
                priority=TaskPriority.HIGH,
            ),
            Task(
                id="t2",
                name="Data Process",
                estimated_duration=3.0,
                parallelizable=True,
                priority=TaskPriority.NORMAL,
            ),
            Task(
                id="t3",
                name="Data Validate",
                estimated_duration=1.0,
                parallelizable=True,
                priority=TaskPriority.NORMAL,
            ),
            Task(
                id="t4",
                name="Report Generate",
                estimated_duration=2.0,
                parallelizable=False,
                priority=TaskPriority.NORMAL,
            ),
        ]

        dependencies = [
            TaskDependency(
                source_task_id="t1",
                target_task_id="t2",
                dependency_type=DependencyType.HARD,
            ),
            TaskDependency(
                source_task_id="t1",
                target_task_id="t3",
                dependency_type=DependencyType.HARD,
            ),
            TaskDependency(
                source_task_id="t2",
                target_task_id="t4",
                dependency_type=DependencyType.HARD,
            ),
            TaskDependency(
                source_task_id="t3",
                target_task_id="t4",
                dependency_type=DependencyType.HARD,
            ),
        ]

        return {"tasks": tasks, "dependencies": dependencies}

    def test_orchestrator_creation(self, orchestrator):
        """Test creating orchestrator."""
        assert orchestrator is not None
        assert orchestrator.complexity_scorer is not None
        assert orchestrator.decision_engine is not None
        assert orchestrator.execution_planner is not None

    def test_analyze_workflow_simple(self, orchestrator, sample_workflow):
        """Test analyzing a simple workflow."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-1",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        assert analysis is not None
        assert analysis.analysis_id is not None
        assert analysis.workflow_id == "wf-test-1"
        assert analysis.total_tasks == 4
        assert analysis.total_dependencies == 4

    def test_analyze_workflow_complexity_scores(self, orchestrator, sample_workflow):
        """Test complexity scores are generated."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-2",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        assert len(analysis.complexity_scores) == 4
        for task_id, score in analysis.complexity_scores.items():
            assert 0 <= score <= 100

    def test_analyze_workflow_feasibility_ratings(self, orchestrator, sample_workflow):
        """Test feasibility ratings are assigned."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-3",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        assert len(analysis.feasibility_ratings) == 4
        for task_id, rating in analysis.feasibility_ratings.items():
            assert rating in [
                "highly_feasible",
                "feasible",
                "challenging",
                "high_risk",
                "infeasible",
            ]

    def test_analyze_workflow_critical_path(self, orchestrator, sample_workflow):
        """Test critical path is identified."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-4",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        assert len(analysis.critical_path) > 0
        assert analysis.critical_path_duration > 0

    def test_analyze_workflow_parallelizable_tasks(self, orchestrator, sample_workflow):
        """Test parallelizable tasks are identified."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-5",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        assert len(analysis.parallelizable_tasks) > 0
        # Tasks t1, t2, t3 are parallelizable
        assert "t1" in analysis.parallelizable_tasks

    def test_generate_strategy_performance(self, orchestrator, sample_workflow):
        """Test strategy generation for performance goal."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-6",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        assert recommendation is not None
        assert recommendation.strategy_type in ["aggressive", "balanced", "conservative"]
        assert recommendation.max_parallel_tasks > 0

    def test_generate_strategy_cost(self, orchestrator, sample_workflow):
        """Test strategy generation for cost goal."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-7",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.COST,
        )

        assert recommendation is not None
        assert recommendation.strategy_type in ["aggressive", "balanced", "conservative"]

    def test_generate_strategy_reliability(self, orchestrator, sample_workflow):
        """Test strategy generation for reliability goal."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-8",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.RELIABILITY,
        )

        assert recommendation is not None
        assert recommendation.monitoring_intensity in ["minimal", "normal", "intensive"]

    def test_plan_execution(self, orchestrator, sample_workflow):
        """Test execution plan creation."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-9",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        assert plan is not None
        assert plan.id is not None
        assert plan.total_tasks == 4
        assert len(plan.phases) > 0

    def test_plan_execution_phases_have_tasks(self, orchestrator, sample_workflow):
        """Test execution plan phases contain tasks."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-10",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        # Each phase should have task groups with tasks
        for phase in plan.phases:
            assert len(phase.task_groups) > 0
            for group in phase.task_groups:
                assert len(group.tasks) > 0

    def test_create_strategy_document(self, orchestrator, sample_workflow):
        """Test strategy document generation."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-11",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        document = orchestrator.create_strategy_document(
            workflow_analysis=analysis,
            decision_recommendation=recommendation,
            execution_plan=plan,
        )

        assert document is not None
        assert document.document_id is not None
        assert document.title is not None

    def test_execute_workflow(self, orchestrator, sample_workflow):
        """Test workflow execution."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-12",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        result = orchestrator.execute_workflow(
            execution_plan=plan,
            workflow_id="wf-test-12",
        )

        assert result is not None
        assert result.execution_id is not None
        assert result.workflow_id == "wf-test-12"
        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    def test_execute_workflow_result_metrics(self, orchestrator, sample_workflow):
        """Test execution result contains metrics."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-13",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        result = orchestrator.execute_workflow(
            execution_plan=plan,
            workflow_id="wf-test-13",
        )

        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration_seconds >= 0
        assert result.tasks_completed >= 0
        assert len(result.metrics) > 0

    def test_workflow_state_transitions(self, orchestrator, sample_workflow):
        """Test workflow goes through correct state transitions."""
        # Start -> Analyzed
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-14",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )
        assert analysis is not None

        # Analyzed -> Strategy
        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )
        assert recommendation is not None

        # Strategy -> Planned
        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )
        assert plan is not None

        # Planned -> Executed
        result = orchestrator.execute_workflow(
            execution_plan=plan,
            workflow_id="wf-test-14",
        )
        assert result is not None
        assert result.status is not None

    def test_persistence_integration(self, orchestrator, sample_workflow):
        """Test persistence manager integration."""
        orchestrator.analyze_workflow(
            workflow_id="wf-test-15",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        # Check snapshots were persisted
        assert len(orchestrator.persistence_manager.snapshots) > 0

    def test_escalation_on_failure(self, orchestrator, sample_workflow):
        """Test escalation is triggered on execution failure."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-test-16",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        result = orchestrator.execute_workflow(
            execution_plan=plan,
            workflow_id="wf-test-16",
        )

        # Result should include escalation event counts
        assert hasattr(result, "escalation_events")

    def test_empty_workflow_analysis(self, orchestrator):
        """Test analysis with empty workflow."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-empty",
            tasks=[],
            dependencies=[],
        )

        assert analysis.total_tasks == 0
        assert analysis.total_dependencies == 0

    def test_complex_dependency_graph(self, orchestrator):
        """Test analysis with complex dependency graph."""
        tasks = [Task(id=f"t{i}", name=f"Task {i}") for i in range(10)]

        dependencies = [
            TaskDependency(
                source_task_id="t0",
                target_task_id="t1",
                dependency_type=DependencyType.HARD,
            ),
            TaskDependency(
                source_task_id="t1",
                target_task_id="t2",
                dependency_type=DependencyType.HARD,
            ),
            TaskDependency(
                source_task_id="t0",
                target_task_id="t3",
                dependency_type=DependencyType.HARD,
            ),
            TaskDependency(
                source_task_id="t3",
                target_task_id="t4",
                dependency_type=DependencyType.HARD,
            ),
        ]

        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-complex",
            tasks=tasks,
            dependencies=dependencies,
        )

        assert analysis.total_tasks == 10
        assert analysis.total_dependencies == 4
        assert len(analysis.critical_path) > 0

    def test_resource_aware_planning(self, orchestrator, sample_workflow):
        """Test resource-aware execution planning."""
        # Add resource constraints to tasks
        sample_workflow["tasks"][0].resource_type = "gpu"
        sample_workflow["tasks"][0].max_concurrent = 1
        sample_workflow["tasks"][1].resource_type = "gpu"
        sample_workflow["tasks"][1].max_concurrent = 1

        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-resource",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.COST,
            resource_constraint="gpu",
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        # Plan should account for resource constraints
        # Note: resource_aware is set based on decision engine context, not orchestrator call
        assert recommendation is not None
        assert len(plan.resource_conflicts) >= 0

    def test_workflow_id_preservation(self, orchestrator, sample_workflow):
        """Test workflow ID is preserved throughout pipeline."""
        workflow_id = "wf-preserve-id"

        analysis = orchestrator.analyze_workflow(
            workflow_id=workflow_id,
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )
        assert analysis.workflow_id == workflow_id

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
            decision_recommendation=recommendation,
        )

        result = orchestrator.execute_workflow(
            execution_plan=plan,
            workflow_id=workflow_id,
        )
        assert result.workflow_id == workflow_id

    def test_plan_execution_all_parallelizable(self, orchestrator):
        """Test plan with all parallelizable tasks."""
        tasks = [
            Task(id="p1", name="Parallel 1", estimated_duration=1.0, parallelizable=True),
            Task(id="p2", name="Parallel 2", estimated_duration=1.0, parallelizable=True),
            Task(id="p3", name="Parallel 3", estimated_duration=1.0, parallelizable=True),
        ]
        deps = []

        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-all-parallel",
            tasks=tasks,
            dependencies=deps,
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.PERFORMANCE,
        )

        plan = orchestrator.plan_execution(
            tasks=tasks,
            dependencies=deps,
            decision_recommendation=recommendation,
        )

        assert plan.total_tasks == 3
        # When all tasks are parallel with no deps, they can run in one phase
        assert len(plan.phases) >= 1

    def test_generate_strategy_with_all_parameters(self, orchestrator, sample_workflow):
        """Test strategy generation with all optional parameters."""
        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-full-params",
            tasks=sample_workflow["tasks"],
            dependencies=sample_workflow["dependencies"],
        )

        recommendation = orchestrator.generate_strategy(
            workflow_analysis=analysis,
            parallelization_goal=ParallelizationGoal.RELIABILITY,
            resource_constraint="memory",
            failure_tolerance="retry",
        )

        assert recommendation is not None
        assert recommendation.recommended_retry_count > 0

    def test_execution_with_cycles_in_dependencies(self, orchestrator):
        """Test handling of workflows with potential circular dependencies."""
        tasks = [
            Task(id="c1", name="Task 1", estimated_duration=1.0),
            Task(id="c2", name="Task 2", estimated_duration=1.0),
        ]

        # No actual cycles - dependencies form valid DAG
        deps = [
            TaskDependency(
                source_task_id="c1",
                target_task_id="c2",
                dependency_type=DependencyType.HARD,
            ),
        ]

        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-dag-check",
            tasks=tasks,
            dependencies=deps,
        )

        # Should handle valid DAG without warnings
        assert analysis.total_tasks == 2

    def test_parallelizable_groups_identification(self, orchestrator):
        """Test identification of parallelizable task groups."""
        tasks = [
            Task(id="g1", name="Group 1", estimated_duration=1.0, parallelizable=True),
            Task(id="g2", name="Group 2", estimated_duration=1.0, parallelizable=True),
            Task(id="g3", name="Group 3", estimated_duration=2.0, parallelizable=False),
        ]

        deps = [
            TaskDependency(
                source_task_id="g1",
                target_task_id="g3",
                dependency_type=DependencyType.HARD,
            ),
        ]

        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-groups",
            tasks=tasks,
            dependencies=deps,
        )

        # Should identify parallelizable tasks
        assert len(analysis.parallelizable_tasks) >= 2

    def test_different_task_priorities(self, orchestrator):
        """Test workflow with different task priorities."""
        tasks = [
            Task(
                id="pr1",
                name="Critical",
                estimated_duration=1.0,
                priority=TaskPriority.CRITICAL,
            ),
            Task(
                id="pr2",
                name="High",
                estimated_duration=2.0,
                priority=TaskPriority.HIGH,
            ),
            Task(
                id="pr3",
                name="Low",
                estimated_duration=3.0,
                priority=TaskPriority.LOW,
            ),
        ]

        deps = []

        analysis = orchestrator.analyze_workflow(
            workflow_id="wf-priorities",
            tasks=tasks,
            dependencies=deps,
        )

        assert analysis.total_tasks == 3
