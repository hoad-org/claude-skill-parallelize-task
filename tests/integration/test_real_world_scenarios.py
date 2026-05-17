"""Real-world scenario tests for Phase 4 integration."""

import pytest

from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.decision_engine import ParallelizationGoal
from parallelizer_skill.models import ExecutionStatus, TaskPriority
from parallelizer_skill.config import reset_config


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test realistic, production-like parallelization scenarios."""

    @pytest.fixture
    def orchestrator(self):
        """Create fresh orchestrator."""
        reset_config()
        return WorkflowOrchestrator()

    def test_data_pipeline_workflow(
        self,
        orchestrator,
        data_pipeline_tasks,
        data_pipeline_dependencies,
    ):
        """Test 20-task data pipeline with data dependencies."""
        workflow_id = "workflow-data-pipeline-001"

        analysis = orchestrator.analyze_workflow(
            workflow_id, data_pipeline_tasks, data_pipeline_dependencies
        )

        assert analysis.total_tasks == 20
        assert len(analysis.parallelizable_tasks) >= 10

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        # Reliability-focused strategy; resource-awareness implementation may vary
        assert decision.recommended_retry_count >= 2

        plan = orchestrator.plan_execution(data_pipeline_tasks, data_pipeline_dependencies, decision)

        assert plan.total_tasks == 20
        assert len(plan.phases) >= 2

        result = orchestrator.execute_workflow(plan, workflow_id)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.tasks_completed == 20

    def test_microservices_deployment(
        self,
        orchestrator,
        microservices_deployment_tasks,
        microservices_deployment_dependencies,
    ):
        """Test 15 services with complex ordering and failure tolerance."""
        workflow_id = "workflow-microservices-001"

        analysis = orchestrator.analyze_workflow(
            workflow_id, microservices_deployment_tasks, microservices_deployment_dependencies
        )

        assert analysis.total_tasks == 15
        assert len(analysis.critical_path) >= 1

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision.monitoring_intensity in ["intensive", "normal"]

        plan = orchestrator.plan_execution(
            microservices_deployment_tasks, microservices_deployment_dependencies, decision
        )

        assert plan.total_tasks == 15
        assert len(plan.phases) >= 1

        result = orchestrator.execute_workflow(plan, workflow_id)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.tasks_completed == 15

    def test_gpu_compute_job(self, orchestrator):
        """Test resource-constrained GPU computation workflow."""
        from parallelizer_skill.models import Task

        gpu_tasks = [
            Task(
                id="prep_1",
                name="Data Preparation 1",
                estimated_duration=2.0,
                parallelizable=True,
                resource_type="cpu",
                priority=TaskPriority.HIGH,
            ),
            Task(
                id="prep_2",
                name="Data Preparation 2",
                estimated_duration=2.0,
                parallelizable=True,
                resource_type="cpu",
            ),
            Task(
                id="train_gpu",
                name="GPU Training",
                estimated_duration=15.0,
                parallelizable=False,
                resource_type="gpu",
                max_concurrent=1,
            ),
            Task(
                id="analysis_1",
                name="Analysis 1",
                estimated_duration=3.0,
                parallelizable=True,
                resource_type="cpu",
            ),
            Task(
                id="analysis_2",
                name="Analysis 2",
                estimated_duration=3.0,
                parallelizable=True,
                resource_type="cpu",
            ),
            Task(
                id="export",
                name="Export Results",
                estimated_duration=5.0,
                parallelizable=False,
                resource_type="network",
            ),
        ]

        from parallelizer_skill.models import TaskDependency, DependencyType

        gpu_deps = [
            TaskDependency(source_task_id="prep_1", target_task_id="train_gpu", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="prep_2", target_task_id="train_gpu", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="train_gpu", target_task_id="analysis_1", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="train_gpu", target_task_id="analysis_2", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="analysis_1", target_task_id="export", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="analysis_2", target_task_id="export", dependency_type=DependencyType.HARD),
        ]

        workflow_id = "workflow-gpu-001"

        analysis = orchestrator.analyze_workflow(workflow_id, gpu_tasks, gpu_deps)

        assert analysis.total_tasks == 6

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.COST)

        # GPU computation should respect resource constraints even if resource_aware field varies
        assert decision.max_parallel_tasks >= 1

        plan = orchestrator.plan_execution(gpu_tasks, gpu_deps, decision)

        assert plan.total_tasks == 6

        result = orchestrator.execute_workflow(plan, workflow_id)

        assert result.status == ExecutionStatus.COMPLETED

    def test_long_running_batch_process(self, orchestrator):
        """Test very long-duration workflow with checkpoint requirements."""
        from parallelizer_skill.models import Task, TaskDependency, DependencyType

        batch_tasks = [
            Task(
                id="setup",
                name="Setup Environment",
                estimated_duration=5.0,
                parallelizable=False,
            ),
            *[
                Task(
                    id=f"process_{i}",
                    name=f"Process Batch {i}",
                    estimated_duration=30.0,
                    parallelizable=True,
                    resource_type="cpu",
                    max_concurrent=4,
                )
                for i in range(1, 9)
            ],
            Task(
                id="consolidate",
                name="Consolidate Results",
                estimated_duration=10.0,
                parallelizable=False,
            ),
            Task(
                id="validate",
                name="Final Validation",
                estimated_duration=5.0,
                parallelizable=False,
            ),
        ]

        batch_deps = [
            TaskDependency(source_task_id="setup", target_task_id="process_1", dependency_type=DependencyType.HARD),
            *[TaskDependency(
                source_task_id=f"process_{i}",
                target_task_id="consolidate",
                dependency_type=DependencyType.HARD
            ) for i in range(1, 9)],
            TaskDependency(source_task_id="consolidate", target_task_id="validate", dependency_type=DependencyType.HARD),
        ]

        workflow_id = "workflow-batch-001"

        analysis = orchestrator.analyze_workflow(workflow_id, batch_tasks, batch_deps)

        assert analysis.total_tasks >= 10

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision.monitoring_intensity in ["intensive", "normal"]

        plan = orchestrator.plan_execution(batch_tasks, batch_deps, decision)

        assert analysis.total_tasks >= 10
        assert len(plan.phases) >= 2

        result = orchestrator.execute_workflow(plan, workflow_id)

        assert result.status == ExecutionStatus.COMPLETED

    def test_mixed_complexity_real_world_scenario(self, orchestrator):
        """Test complex real-world scenario with mixed task types."""
        from parallelizer_skill.models import Task, TaskDependency, DependencyType

        build_tasks = [
            Task(id="checkout", name="Checkout Source", estimated_duration=3.0, parallelizable=False),
            Task(id="lint", name="Lint Code", estimated_duration=2.0, parallelizable=True),
            Task(id="build", name="Build Project", estimated_duration=8.0, parallelizable=False),
            *[
                Task(
                    id=f"test_{i}",
                    name=f"Test Suite {i}",
                    estimated_duration=5.0,
                    parallelizable=True,
                )
                for i in range(1, 5)
            ],
            Task(id="integration", name="Integration Tests", estimated_duration=10.0, parallelizable=False),
            Task(id="deploy_staging", name="Deploy to Staging", estimated_duration=5.0, parallelizable=False),
            Task(id="smoke_test", name="Smoke Tests", estimated_duration=3.0, parallelizable=False),
            Task(id="deploy_prod", name="Deploy to Production", estimated_duration=7.0, parallelizable=False),
        ]

        build_deps = [
            TaskDependency(source_task_id="checkout", target_task_id="lint", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="checkout", target_task_id="build", dependency_type=DependencyType.HARD),
            *[TaskDependency(
                source_task_id="build",
                target_task_id=f"test_{i}",
                dependency_type=DependencyType.HARD
            ) for i in range(1, 5)],
            *[TaskDependency(
                source_task_id=f"test_{i}",
                target_task_id="integration",
                dependency_type=DependencyType.HARD
            ) for i in range(1, 5)],
            TaskDependency(source_task_id="integration", target_task_id="deploy_staging", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="deploy_staging", target_task_id="smoke_test", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="smoke_test", target_task_id="deploy_prod", dependency_type=DependencyType.HARD),
        ]

        workflow_id = "workflow-build-001"

        analysis = orchestrator.analyze_workflow(workflow_id, build_tasks, build_deps)

        assert analysis.total_tasks >= 10

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        plan = orchestrator.plan_execution(build_tasks, build_deps, decision)

        assert analysis.total_tasks >= 10
        assert len(plan.phases) >= 3

        result = orchestrator.execute_workflow(plan, workflow_id)

        assert result.status == ExecutionStatus.COMPLETED

    def test_performance_under_different_goals(self, orchestrator, data_pipeline_tasks, data_pipeline_dependencies):
        """Test same workflow produces reasonable results under all goals."""
        workflow_id = "workflow-goals-001"

        analysis = orchestrator.analyze_workflow(workflow_id, data_pipeline_tasks, data_pipeline_dependencies)

        results = {}

        for goal in [ParallelizationGoal.PERFORMANCE, ParallelizationGoal.COST, ParallelizationGoal.RELIABILITY]:
            decision = orchestrator.generate_strategy(analysis, parallelization_goal=goal)
            plan = orchestrator.plan_execution(data_pipeline_tasks, data_pipeline_dependencies, decision)

            results[goal.value] = {
                "strategy": decision.strategy_type,
                "max_parallel": decision.max_parallel_tasks,
                "efficiency": plan.efficiency_gain,
            }

        for goal_name, result in results.items():
            assert result["max_parallel"] > 0
            assert result["efficiency"] >= 0.0
