"""Unit tests for strategy document generator (Phase 3)."""

import pytest
from datetime import datetime
from parallelizer_skill.strategy_document import (
    StrategyDocumentGenerator, StrategyDocument
)
from parallelizer_skill.decision_engine import (
    DecisionRecommendation, ParallelizationGoal, TaskComplexityClass,
    ResourceConstraint, DependencyDensity, FailureTolerance, PriorityMetric
)
from parallelizer_skill.models import (
    Task, TaskDependency, ExecutionPlan, DependencyType, ExecutionPhase, TaskGroup
)
from parallelizer_skill.complexity import ComplexityScore, ComplexityLevel, FeasibilityRating
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestStrategyDocumentGenerator:
    """Test strategy document generator."""

    @pytest.fixture
    def generator(self):
        """Create fresh generator for each test."""
        reset_config()
        return StrategyDocumentGenerator()

    @pytest.fixture
    def sample_recommendation(self):
        """Create sample recommendation."""
        return DecisionRecommendation(
            strategy_type="balanced",
            max_parallel_tasks=8,
            recommended_batch_size=4,
            recommended_retry_count=2,
            recommended_checkpoint_interval=30,
            parallel_execution=True,
            resource_aware=True,
            monitoring_intensity="normal",
            escalation_level="warning",
            rationale="Balanced strategy with resource awareness",
        )

    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks."""
        return [
            Task(id="t1", name="Task 1", estimated_duration=5.0),
            Task(id="t2", name="Task 2", estimated_duration=3.0),
            Task(id="t3", name="Task 3", estimated_duration=4.0),
        ]

    @pytest.fixture
    def sample_dependencies(self):
        """Create sample dependencies."""
        return [
            TaskDependency(source_task_id="t1", target_task_id="t2", dependency_type=DependencyType.HARD),
            TaskDependency(source_task_id="t2", target_task_id="t3", dependency_type=DependencyType.HARD),
        ]

    @pytest.fixture
    def sample_complexity_scores(self):
        """Create sample complexity scores."""
        return {
            "t1": ComplexityScore(
                task_id="t1",
                complexity_level=ComplexityLevel.SIMPLE,
                feasibility_rating=FeasibilityRating.FEASIBLE,
                score=80.0,
                factors={},
                warnings=[],
                recommendations=[],
            ),
            "t2": ComplexityScore(
                task_id="t2",
                complexity_level=ComplexityLevel.MODERATE,
                feasibility_rating=FeasibilityRating.FEASIBLE,
                score=60.0,
                factors={},
                warnings=[],
                recommendations=[],
            ),
            "t3": ComplexityScore(
                task_id="t3",
                complexity_level=ComplexityLevel.SIMPLE,
                feasibility_rating=FeasibilityRating.FEASIBLE,
                score=75.0,
                factors={},
                warnings=[],
                recommendations=[],
            ),
        }

    @pytest.fixture
    def sample_execution_plan(self):
        """Create sample execution plan."""
        phase1 = ExecutionPhase(
            phase_number=1,
            task_groups=[TaskGroup(id="g1", tasks=["t1"], estimated_duration=5.0)],
            is_parallel=False,
            estimated_duration=5.0,
            sync_point_required=True,
        )
        phase2 = ExecutionPhase(
            phase_number=2,
            task_groups=[TaskGroup(id="g2", tasks=["t2", "t3"], estimated_duration=7.0)],
            is_parallel=True,
            estimated_duration=7.0,
            sync_point_required=False,
        )
        
        return ExecutionPlan(
            id="plan_1",
            total_tasks=3,
            serial_duration=12.0,
            parallel_duration=9.0,
            efficiency_gain=25.0,
            phases=[phase1, phase2],
            critical_path=["t1", "t2"],
            parallelizable_groups={"phase2": ["t2", "t3"]},
            resource_conflicts=[],
            safety_issues=[],
        )

    def test_generator_creation(self, generator):
        """Test creating generator."""
        assert generator is not None
        assert len(generator.documents) == 0

    def test_generate_document(
        self, generator, sample_recommendation, sample_tasks, sample_dependencies,
        sample_complexity_scores, sample_execution_plan
    ):
        """Test generating a strategy document."""
        doc = generator.generate(
            document_id="doc_1",
            title="Parallelization Strategy",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
            execution_plan=sample_execution_plan,
        )

        assert doc.document_id == "doc_1"
        assert doc.title == "Parallelization Strategy"
        assert doc.executive_summary is not None
        assert doc.analysis_summary is not None
        assert doc.recommendations is not None

    def test_executive_summary(self, generator, sample_recommendation, sample_tasks, sample_dependencies,
        sample_complexity_scores
    ):
        """Test executive summary generation."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test Strategy",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
        )

        summary = doc.executive_summary
        assert "Test Strategy" in summary
        assert "BALANCED" in summary
        assert "8" in summary  # max_parallel_tasks

    def test_analysis_summary(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores, sample_execution_plan
    ):
        """Test analysis summary generation."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
            execution_plan=sample_execution_plan,
        )

        analysis = doc.analysis_summary
        assert analysis["total_tasks"] == 3
        assert analysis["dependency_count"] == 2
        assert "1.3x" in analysis["potential_speedup"]  # 12.0 / 9.0 ≈ 1.3x

    def test_recommendations_section(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores
    ):
        """Test recommendations section."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
        )

        recs = doc.recommendations
        assert recs["strategy_type"] == "balanced"
        assert recs["max_parallel_tasks"] == 8
        assert len(recs["key_actions"]) > 0

    def test_implementation_plan(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores
    ):
        """Test implementation plan generation."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
        )

        plan = doc.implementation_plan
        assert len(plan) > 0
        assert any("PREPARATION" in step for step in plan)
        assert any("EXECUTION" in step for step in plan)
        assert any("RESILIENCE" in step for step in plan)

    def test_risk_assessment(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores
    ):
        """Test risk assessment generation."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
        )

        risk = doc.risk_assessment
        assert "high_complexity_tasks" in risk
        assert "dependency_risk" in risk
        assert "mitigation_strategies" in risk

    def test_performance_projections_with_plan(self, generator, sample_recommendation,
        sample_tasks, sample_dependencies, sample_complexity_scores, sample_execution_plan
    ):
        """Test performance projections with execution plan."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
            execution_plan=sample_execution_plan,
        )

        perf = doc.performance_projections
        assert "12.0s" in perf["projected_serial_duration"]
        assert "9.0s" in perf["projected_parallel_duration"]
        assert "1.3x" in perf["expected_speedup"]

    def test_performance_projections_without_plan(self, generator, sample_recommendation,
        sample_tasks, sample_dependencies, sample_complexity_scores
    ):
        """Test performance projections without execution plan."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
            execution_plan=None,
        )

        perf = doc.performance_projections
        assert perf["projected_serial_duration"] == "Unknown"
        assert perf["projected_parallel_duration"] == "Unknown"

    def test_get_document(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores
    ):
        """Test retrieving a document."""
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
        )

        retrieved = generator.get_document("doc_1")
        assert retrieved is not None
        assert retrieved.document_id == "doc_1"

    def test_get_nonexistent_document(self, generator):
        """Test retrieving nonexistent document."""
        retrieved = generator.get_document("unknown")
        assert retrieved is None

    def test_render_markdown(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores, sample_execution_plan
    ):
        """Test Markdown rendering."""
        doc = generator.generate(
            document_id="doc_1",
            title="Parallelization Strategy",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
            execution_plan=sample_execution_plan,
        )

        md = generator.render_markdown(doc)
        assert "# Parallelization Strategy" in md
        assert "## Executive Summary" in md
        assert "## Analysis" in md
        assert "## Recommendations" in md
        assert "## Implementation Plan" in md
        assert "## Risk Assessment" in md
        assert "## Performance Projections" in md

    def test_reset(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores
    ):
        """Test reset."""
        generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
        )

        assert len(generator.documents) == 1

        generator.reset()

        assert len(generator.documents) == 0

    def test_multiple_documents(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores
    ):
        """Test generating multiple documents."""
        for i in range(3):
            generator.generate(
                document_id=f"doc_{i}",
                title=f"Strategy {i}",
                tasks=sample_tasks,
                dependencies=sample_dependencies,
                complexity_scores=sample_complexity_scores,
                decision_recommendation=sample_recommendation,
            )

        assert len(generator.documents) == 3
        assert generator.get_document("doc_0") is not None
        assert generator.get_document("doc_1") is not None
        assert generator.get_document("doc_2") is not None

    def test_document_timestamp(self, generator, sample_recommendation, sample_tasks,
        sample_dependencies, sample_complexity_scores
    ):
        """Test document has timestamp."""
        before = datetime.utcnow()
        
        doc = generator.generate(
            document_id="doc_1",
            title="Test",
            tasks=sample_tasks,
            dependencies=sample_dependencies,
            complexity_scores=sample_complexity_scores,
            decision_recommendation=sample_recommendation,
        )

        after = datetime.utcnow()
        
        assert before <= doc.generated_at <= after
