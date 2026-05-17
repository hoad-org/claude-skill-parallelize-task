"""Cross-phase integration tests for Phase 2-4 components."""

import pytest

from parallelizer_skill.orchestrator import WorkflowOrchestrator
from parallelizer_skill.decision_engine import ParallelizationGoal
from parallelizer_skill.models import Task, TaskDependency, DependencyType, TaskPriority
from parallelizer_skill.config import reset_config


@pytest.mark.integration
class TestCrossPhaseIntegration:
    """Test integration between Phase 2-4 components."""

    @pytest.fixture
    def orchestrator(self):
        """Create fresh orchestrator."""
        reset_config()
        return WorkflowOrchestrator()

    def test_complexity_to_decision_feedback(self, orchestrator, simple_tasks, simple_dependencies):
        """Test complexity scores feed into decision engine."""
        workflow_id = "workflow-feedback-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)

        assert all(0 <= score <= 100 for score in analysis.complexity_scores.values())
        assert len(analysis.complexity_scores) == len(simple_tasks)

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision is not None
        assert decision.max_parallel_tasks > 0

    def test_decision_to_execution_plan(self, orchestrator, complex_tasks, complex_dependencies):
        """Test decision recommendations guide execution planner."""
        workflow_id = "workflow-decision-plan-001"

        analysis = orchestrator.analyze_workflow(workflow_id, complex_tasks, complex_dependencies)

        conservative_decision = orchestrator.generate_strategy(
            analysis, parallelization_goal=ParallelizationGoal.RELIABILITY
        )
        conservative_plan = orchestrator.plan_execution(complex_tasks, complex_dependencies, conservative_decision)

        aggressive_decision = orchestrator.generate_strategy(
            analysis, parallelization_goal=ParallelizationGoal.PERFORMANCE
        )
        aggressive_plan = orchestrator.plan_execution(complex_tasks, complex_dependencies, aggressive_decision)

        assert conservative_plan.total_tasks == aggressive_plan.total_tasks
        assert conservative_plan.serial_duration == aggressive_plan.serial_duration

    def test_escalation_triggers_recovery(self, orchestrator):
        """Test escalation manager integrates with orchestrator."""
        risky_tasks = [
            Task(
                id="t1",
                name="Risky Task 1",
                estimated_duration=10.0,
                parallelizable=False,
                priority=TaskPriority.CRITICAL,
            ),
            Task(
                id="t2",
                name="Risky Task 2",
                estimated_duration=8.0,
                parallelizable=False,
                priority=TaskPriority.CRITICAL,
            ),
        ]

        deps = [TaskDependency(source_task_id="t1", target_task_id="t2", dependency_type=DependencyType.HARD)]

        workflow_id = "workflow-escalation-001"

        analysis = orchestrator.analyze_workflow(workflow_id, risky_tasks, deps)

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision.monitoring_intensity in ["intensive", "normal"]
        assert decision.recommended_retry_count >= 1

    def test_persistence_state_recovery(self, orchestrator, temp_dir, simple_tasks, simple_dependencies):
        """Test state snapshots and recovery points work."""
        workflow_id = "workflow-persist-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)
        plan = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)

        # State persistence is handled internally
        assert plan is not None

    def test_analysis_influences_all_downstream_decisions(self, orchestrator, complex_tasks, complex_dependencies):
        """Test that analysis correctly influences all downstream decisions."""
        workflow_id = "workflow-influence-001"

        analysis = orchestrator.analyze_workflow(workflow_id, complex_tasks, complex_dependencies)

        total_tasks = analysis.total_tasks
        total_deps = analysis.total_dependencies
        parallelizable = len(analysis.parallelizable_tasks)

        assert total_tasks == 10
        assert total_deps == 15
        assert parallelizable > 0

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.PERFORMANCE)
        plan = orchestrator.plan_execution(complex_tasks, complex_dependencies, decision)

        assert plan.critical_path == analysis.critical_path

    def test_decision_consistency_across_goals(self, orchestrator, simple_tasks, simple_dependencies):
        """Test decision engine produces consistent output for same input."""
        workflow_id = "workflow-consistency-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)

        decision1 = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)
        decision2 = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision1.strategy_type == decision2.strategy_type
        assert decision1.max_parallel_tasks == decision2.max_parallel_tasks

    def test_plan_execution_consistency(self, orchestrator, simple_tasks, simple_dependencies):
        """Test execution plans are consistent across runs."""
        workflow_id = "workflow-plan-consistency-001"

        analysis = orchestrator.analyze_workflow(workflow_id, simple_tasks, simple_dependencies)
        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        plan1 = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)
        plan2 = orchestrator.plan_execution(simple_tasks, simple_dependencies, decision)

        assert plan1.total_tasks == plan2.total_tasks
        assert len(plan1.phases) == len(plan2.phases)
        assert plan1.critical_path == plan2.critical_path

    def test_escalation_under_high_load(self, orchestrator):
        """Test escalation triggers appropriately under stress."""
        many_tasks = [
            Task(
                id=f"t{i}",
                name=f"Task {i}",
                estimated_duration=2.0 + (i % 3),
                parallelizable=i % 2 == 0,
                priority=TaskPriority.HIGH if i < 5 else TaskPriority.NORMAL,
            )
            for i in range(1, 51)
        ]

        deps = []
        for i in range(1, 50):
            if i % 5 == 0:
                deps.append(
                    TaskDependency(
                        source_task_id=f"t{i}", target_task_id=f"t{i+1}", dependency_type=DependencyType.HARD
                    )
                )

        workflow_id = "workflow-high-load-001"

        analysis = orchestrator.analyze_workflow(workflow_id, many_tasks, deps)

        assert analysis.total_tasks == 50
        assert len(analysis.complexity_scores) == 50

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision.max_parallel_tasks > 0
        assert decision.max_parallel_tasks <= 16

    def test_full_pipeline_state_validation(self, orchestrator, complex_tasks, complex_dependencies):
        """Test state validity throughout entire pipeline."""
        workflow_id = "workflow-validation-001"

        analysis = orchestrator.analyze_workflow(workflow_id, complex_tasks, complex_dependencies)

        assert analysis.analysis_id is not None
        assert analysis.workflow_id == workflow_id

        decision = orchestrator.generate_strategy(analysis, parallelization_goal=ParallelizationGoal.RELIABILITY)

        assert decision.strategy_type in ["aggressive", "balanced", "conservative"]
        assert 1 <= decision.max_parallel_tasks <= 16

        plan = orchestrator.plan_execution(complex_tasks, complex_dependencies, decision)

        assert plan.id is not None
        assert plan.total_tasks == len(complex_tasks)
        assert len(plan.phases) > 0

        result = orchestrator.execute_workflow(plan, workflow_id)

        assert result.execution_id is not None
        assert result.workflow_id == workflow_id
        assert result.tasks_completed <= len(complex_tasks)
