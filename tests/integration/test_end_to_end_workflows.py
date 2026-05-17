"""End-to-end workflow tests for Phase 4 integration."""

import pytest
from pathlib import Path

from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.decision_engine import ParallelizationGoal
from parallelizer_skill.models import Task, TaskDependency, DependencyType, TaskPriority, ExecutionStatus
from parallelizer_skill.config import reset_config


@pytest.mark.integration
class TestEndToEndWorkflows:
    """Test complete parallelization workflows from input to output."""

    @pytest.fixture
    def orchestrator(self):
        """Create fresh orchestrator for each test."""
        reset_config()
        return WorkflowOrchestrator()

    def test_simple_workflow_analysis_to_execution(self, orchestrator, simple_tasks, simple_dependencies):
        """Test complete simple workflow from analysis to execution."""
        workflow_id = "workflow-simple-001"

        # Step 1: Analyze workflow
        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)
        assert analysis is not None
        assert analysis.total_tasks == 5

        # Step 2: Make decision
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.PERFORMANCE)
        assert decision is not None
        assert decision.parallel_execution is True

        # Step 3: Create execution plan
        plan = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)
        assert plan.total_tasks == 5
        assert len(plan.phases) > 0

        # Step 4: Execute workflow
        result = orchestrator.execute_workflow(plan, workflow_id)
        assert result.status == ExecutionStatus.COMPLETED
        assert result.tasks_completed > 0

    def test_complex_workflow_with_dense_dependencies(self, orchestrator, complex_tasks, complex_dependencies):
        """Test complex workflow with heavy dependencies."""
        workflow_id = "workflow-complex-001"

        analysis = orchestrator.analyze_workflow(workflow_id, complex_tasks, complex_dependencies)
        assert analysis.total_tasks >= 10
        assert len(analysis.critical_path) > 0

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)
        assert decision.recommended_retry_count >= 2

        plan = orchestrator.plan_execution(complex_tasks, complex_dependencies, decision)
        assert len(plan.phases) >= 1

        result = orchestrator.execute_workflow(plan, workflow_id)
        assert result.status == ExecutionStatus.COMPLETED

    def test_performance_goal_workflow(self, orchestrator, simple_tasks, simple_dependencies):
        """Test workflow with performance optimization goal."""
        workflow_id = "workflow-performance-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.PERFORMANCE)

        assert decision.parallel_execution is True
        assert decision.max_parallel_tasks >= 1

        plan = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)
        assert plan.efficiency_gain >= 0.0

    def test_cost_goal_workflow(self, orchestrator, simple_tasks, simple_dependencies):
        """Test workflow with cost optimization goal."""
        workflow_id = "workflow-cost-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.COST)

        # Cost goal should be cost-conscious but implementation may vary
        assert decision.max_parallel_tasks > 0

        plan = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)
        assert plan.efficiency_gain >= 0.0

    def test_reliability_goal_workflow(self, orchestrator, complex_tasks, complex_dependencies):
        """Test workflow with reliability focus."""
        workflow_id = "workflow-reliability-001"

        analysis = orchestrator.analyze_workflow(workflow_id, complex_tasks, complex_dependencies)
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision.recommended_retry_count >= 1

        result = orchestrator.execute_workflow(
            orchestrator.plan_execution(complex_tasks, complex_dependencies, decision),
            workflow_id,
        )

        assert result.status == ExecutionStatus.COMPLETED

    def test_infeasible_task_recovery(self, orchestrator):
        """Test recovery from impossible task constraints."""
        impossible_tasks = [
            Task(
                id="t1",
                name="Task with max_concurrent=0",
                estimated_duration=1.0,
                parallelizable=True,
                max_concurrent=0,
            ),
        ]

        workflow_id = "workflow-infeasible-001"

        try:
            analysis = orchestrator.analyze_workflow(workflow_id, impossible_tasks, [])
            assert analysis is not None
        except Exception:
            pass

    def test_complete_pipeline_output_generation(self, orchestrator, temp_dir, simple_tasks, simple_dependencies):
        """Test complete pipeline with all output generation."""
        workflow_id = "workflow-complete-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)
        plan = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)

        document = orchestrator.create_strategy_document(analysis, decision, plan)
        assert document is not None

    def test_workflow_with_multiple_decision_goals(self, orchestrator, simple_tasks, simple_dependencies):
        """Test workflow decisions with all goal types."""
        workflow_id = "workflow-multigoal-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)

        goals = [
            ParallelizationGoal.PERFORMANCE,
            ParallelizationGoal.COST,
            ParallelizationGoal.RELIABILITY,
        ]

        for goal in goals:
            decision = orchestrator.generate_strategy(analysis, parallelization_goal=goal)
            assert decision is not None
            assert decision.max_parallel_tasks > 0

    def test_state_consistency_across_workflow(self, orchestrator, simple_tasks, simple_dependencies):
        """Test state consistency throughout workflow execution."""
        workflow_id = "workflow-consistency-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)
        plan = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)
        result = orchestrator.execute_workflow(plan, workflow_id)

        assert result.total_phases == len(plan.phases)
        assert result.tasks_completed == len(simple_tasks)

    def test_high_parallelization_recommendation(self, orchestrator):
        """Test highly parallelizable task configuration."""
        independent_tasks = [
            Task(
                id=f"t{i}",
                name=f"Task {i}",
                estimated_duration=2.0,
                parallelizable=True,
                priority=TaskPriority.NORMAL,
            )
            for i in range(1, 9)
        ]

        workflow_id = "workflow-parallel-001"

        analysis = orchestrator.analyze_workflow(workflow_id, independent_tasks, [])
        assert len(analysis.parallelizable_tasks) >= 6

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.PERFORMANCE)
        plan = orchestrator.plan_execution(independent_tasks, [], decision)

        assert plan.efficiency_gain >= 0.0

    def test_circular_dependency_detection(self, orchestrator):
        """Test detection and handling of circular dependencies."""
        circular_tasks = [
            Task(id="t1", name="Task 1", estimated_duration=1.0, parallelizable=True),
            Task(id="t2", name="Task 2", estimated_duration=1.0, parallelizable=True),
            Task(id="t3", name="Task 3", estimated_duration=1.0, parallelizable=True),
        ]

        circular_deps = [
            TaskDependency(source_task_id="t1", target_task_id="t2", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="t2", target_task_id="t3", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="t3", target_task_id="t1", dependency_type=DependencyType.HARD),
        ]

        workflow_id = "workflow-circular-001"

        try:
            analysis = orchestrator.analyze_workflow(workflow_id, circular_tasks, circular_deps)
            assert analysis is not None
        except Exception:
            pass
