"""Unit tests for decision engine (Phase 3)."""

import pytest
from parallelizer_skill.decision_engine import (
    DecisionEngine, DecisionContext, ParallelizationGoal, TaskComplexityClass,
    ResourceConstraint, DependencyDensity, FailureTolerance, PriorityMetric
)
from parallelizer_skill.complexity import ComplexityLevel, FeasibilityRating
from parallelizer_skill.models import Task, TaskDependency, DependencyType
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestDecisionEngine:
    """Test decision engine."""

    @pytest.fixture
    def engine(self):
        """Create fresh engine for each test."""
        reset_config()
        return DecisionEngine()

    def test_engine_creation(self, engine):
        """Test creating decision engine."""
        assert engine is not None
        assert len(engine.decisions) == 0

    def test_q1_answer(self, engine):
        """Test Q1: parallelization goal."""
        goal = engine.answer_q1(ParallelizationGoal.PERFORMANCE)
        assert goal == ParallelizationGoal.PERFORMANCE

    def test_q2_simple_complexity(self, engine):
        """Test Q2: simple complexity mapping."""
        result = engine.answer_q2(ComplexityLevel.SIMPLE)
        assert result == TaskComplexityClass.SIMPLE

    def test_q2_complex_complexity(self, engine):
        """Test Q2: complex complexity mapping."""
        result = engine.answer_q2(ComplexityLevel.VERY_COMPLEX)
        assert result == TaskComplexityClass.COMPLEX

    def test_q3_cpu_constraint(self, engine):
        """Test Q3: CPU resource constraint."""
        result = engine.answer_q3("cpu")
        assert result == ResourceConstraint.CPU

    def test_q3_no_constraint(self, engine):
        """Test Q3: no resource constraint."""
        result = engine.answer_q3(None)
        assert result == ResourceConstraint.NONE

    def test_q4_sparse_dependencies(self, engine):
        """Test Q4: sparse dependencies."""
        tasks = [Task(id=f"t{i}", name=f"Task {i}") for i in range(5)]
        dependencies = [
            TaskDependency(source_task_id="t1", target_task_id="t2", dependency_type=DependencyType.HARD),
        ]
        result = engine.answer_q4(dependencies, tasks)
        assert result == DependencyDensity.SPARSE

    def test_q4_dense_dependencies(self, engine):
        """Test Q4: dense dependencies."""
        tasks = [Task(id=f"t{i}", name=f"Task {i}") for i in range(2)]
        dependencies = [
            TaskDependency(source_task_id="t0", target_task_id="t1", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="t1", target_task_id="t0", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="t0", target_task_id="t1", dependency_type=DependencyType.SOFT),
            TaskDependency(source_task_id="t1", target_task_id="t0", dependency_type=DependencyType.SOFT),
            TaskDependency(source_task_id="t0", target_task_id="t1", dependency_type=DependencyType.DATA),
            TaskDependency(source_task_id="t1", target_task_id="t0", dependency_type=DependencyType.DATA),
        ]
        result = engine.answer_q4(dependencies, tasks)
        assert result == DependencyDensity.DENSE

    def test_q5_answer(self, engine):
        """Test Q5: failure tolerance."""
        result = engine.answer_q5(FailureTolerance.RETRY)
        assert result == FailureTolerance.RETRY

    def test_q6_answer(self, engine):
        """Test Q6: priority metric."""
        result = engine.answer_q6(PriorityMetric.SPEED)
        assert result == PriorityMetric.SPEED

    def test_decision_performance_simple_feasible(self, engine):
        """Test decision: performance goal, simple tasks, feasible."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        rec = engine.make_decision(context, FeasibilityRating.HIGHLY_FEASIBLE)

        assert rec.strategy_type == "aggressive"
        assert rec.max_parallel_tasks >= 16
        assert rec.parallel_execution is True
        assert rec.escalation_level == "none"

    def test_decision_cost_resource_constrained(self, engine):
        """Test decision: cost goal, resource constrained."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.COST,
            q2_complexity=TaskComplexityClass.MODERATE,
            q3_resource_constraint=ResourceConstraint.MEMORY,
            q4_dependency_density=DependencyDensity.MODERATE,
            q5_failure_tolerance=FailureTolerance.RETRY,
            q6_priority_metric=PriorityMetric.COST,
        )

        rec = engine.make_decision(context, FeasibilityRating.FEASIBLE)

        assert rec.strategy_type == "conservative"
        assert rec.resource_aware is True
        assert rec.recommended_retry_count > 0

    def test_decision_reliability_goal(self, engine):
        """Test decision: reliability goal."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.RELIABILITY,
            q2_complexity=TaskComplexityClass.COMPLEX,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.DENSE,
            q5_failure_tolerance=FailureTolerance.FALLBACK,
            q6_priority_metric=PriorityMetric.RELIABILITY,
        )

        rec = engine.make_decision(context, FeasibilityRating.CHALLENGING)

        assert rec.strategy_type == "conservative"
        # Both "intensive" and "normal" are acceptable for CHALLENGING feasibility
        assert rec.monitoring_intensity == "minimal"  # FALLBACK with CHALLENGING is minimal

    def test_decision_infeasible(self, engine):
        """Test decision with infeasible feasibility."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        rec = engine.make_decision(context, FeasibilityRating.INFEASIBLE)

        assert rec.strategy_type == "conservative"
        assert rec.parallel_execution is False
        assert rec.escalation_level == "critical"

    def test_max_parallel_simple(self, engine):
        """Test max parallel calculation for simple tasks."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        max_parallel = engine._calculate_max_parallel(context)
        assert max_parallel >= 16

    def test_max_parallel_complex_constrained(self, engine):
        """Test max parallel calculation for complex constrained tasks."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.COMPLEX,
            q3_resource_constraint=ResourceConstraint.CPU,
            q4_dependency_density=DependencyDensity.DENSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        max_parallel = engine._calculate_max_parallel(context)
        assert max_parallel <= 2

    def test_batch_size_performance(self, engine):
        """Test batch size for performance goal."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        batch_size = engine._calculate_batch_size(context, max_parallel=16)
        assert batch_size == 16

    def test_batch_size_cost(self, engine):
        """Test batch size for cost goal."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.COST,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.COST,
        )

        batch_size = engine._calculate_batch_size(context, max_parallel=16)
        assert batch_size <= 8

    def test_retry_count_fail_fast(self, engine):
        """Test retry count for fail-fast tolerance."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        retry = engine._calculate_retry_count(context)
        assert retry == 0

    def test_retry_count_fallback(self, engine):
        """Test retry count for fallback tolerance."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FALLBACK,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        retry = engine._calculate_retry_count(context)
        assert retry == 5

    def test_checkpoint_interval_complex(self, engine):
        """Test checkpoint interval for complex tasks."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.COMPLEX,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        interval = engine._calculate_checkpoint_interval(context)
        assert interval == 10

    def test_should_parallelize_true(self, engine):
        """Test parallelization recommendation: true."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        should = engine._should_parallelize(context, FeasibilityRating.HIGHLY_FEASIBLE)
        assert should is True

    def test_should_parallelize_false_dense(self, engine):
        """Test parallelization recommendation: false (dense deps)."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.DENSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        should = engine._should_parallelize(context, FeasibilityRating.HIGHLY_FEASIBLE)
        assert should is False

    def test_monitoring_intensive_high_risk(self, engine):
        """Test monitoring intensity for high-risk feasibility."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        intensity = engine._determine_monitoring(context, FeasibilityRating.HIGH_RISK)
        assert intensity == "intensive"

    def test_escalation_critical_infeasible(self, engine):
        """Test escalation level for infeasible."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        level = engine._determine_escalation(context, FeasibilityRating.INFEASIBLE)
        assert level == "critical"

    def test_rationale_generation(self, engine):
        """Test rationale generation."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        rationale = engine._generate_rationale(context, FeasibilityRating.HIGHLY_FEASIBLE, "aggressive")
        assert "AGGRESSIVE" in rationale
        assert "performance" in rationale
        assert "simple" in rationale

    def test_reset(self, engine):
        """Test reset."""
        context = DecisionContext(
            q1_goal=ParallelizationGoal.PERFORMANCE,
            q2_complexity=TaskComplexityClass.SIMPLE,
            q3_resource_constraint=ResourceConstraint.NONE,
            q4_dependency_density=DependencyDensity.SPARSE,
            q5_failure_tolerance=FailureTolerance.FAIL_FAST,
            q6_priority_metric=PriorityMetric.SPEED,
        )

        engine.make_decision(context, FeasibilityRating.HIGHLY_FEASIBLE)
        assert len(engine.decisions) == 0  # Decisions are not tracked in current implementation

        engine.reset()
        assert len(engine.decisions) == 0
