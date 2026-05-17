"""Unit tests for complexity scoring (Phase 2)."""

import pytest
from parallelizer_skill.complexity import ComplexityScorer, ComplexityLevel, FeasibilityRating
from parallelizer_skill.models import Task, TaskDependency, DependencyType
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestComplexityScorer:
    """Test complexity scoring."""

    @pytest.fixture
    def scorer(self):
        """Create fresh scorer for each test."""
        reset_config()
        return ComplexityScorer()

    def test_scorer_creation(self, scorer):
        """Test creating scorer."""
        assert scorer is not None
        assert len(scorer.scores) == 0

    def test_score_trivial_task(self, scorer):
        """Test scoring trivial task."""
        task = Task(
            id="task_1",
            name="Simple task",
            estimated_duration=0.5,
            parallelizable=True,
        )

        score = scorer.score_task(task)

        assert score.task_id == "task_1"
        assert score.complexity_level in (ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE)
        assert score.score >= 80

    def test_score_complex_task(self, scorer):
        """Test scoring complex task."""
        task = Task(
            id="task_1",
            name="Complex task",
            estimated_duration=3600,
            parallelizable=False,
            resource_type="gpu",
        )

        score = scorer.score_task(task)

        assert score.complexity_level in (ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX)
        assert score.score < 50

    def test_score_with_dependencies(self, scorer):
        """Test scoring task with dependencies."""
        task = Task(id="task_2", name="Task 2")
        dependencies = [
            TaskDependency(
                source_task_id="task_1",
                target_task_id="task_2",
                dependency_type=DependencyType.HARD,
            ),
            TaskDependency(
                source_task_id="task_3",
                target_task_id="task_2",
                dependency_type=DependencyType.SOFT,
            ),
        ]

        score = scorer.score_task(task, dependencies)

        assert "dependencies" in score.factors
        assert score.factors["dependencies"] < 100

    def test_task_duration_factor(self, scorer):
        """Test duration factor scoring."""
        short_task = Task(id="task_1", name="Short", estimated_duration=0.5)
        long_task = Task(id="task_2", name="Long", estimated_duration=5000)

        short_score = scorer.score_task(short_task)
        long_score = scorer.score_task(long_task)

        assert short_score.factors["duration"] > long_score.factors["duration"]

    def test_parallelizability_factor(self, scorer):
        """Test parallelizability factor."""
        parallel_task = Task(id="task_1", name="Parallel", parallelizable=True)
        sequential_task = Task(id="task_2", name="Sequential", parallelizable=False)

        parallel_score = scorer.score_task(parallel_task)
        sequential_score = scorer.score_task(sequential_task)

        assert parallel_score.factors["parallelizability"] > sequential_score.factors["parallelizability"]

    def test_resource_requirements_factor(self, scorer):
        """Test resource requirements factor."""
        no_resource = Task(id="task_1", name="None")
        gpu_task = Task(id="task_2", name="GPU", resource_type="gpu")
        network_task = Task(id="task_3", name="Network", resource_type="network")

        no_resource_score = scorer.score_task(no_resource)
        gpu_score = scorer.score_task(gpu_task)
        network_score = scorer.score_task(network_task)

        assert no_resource_score.factors["resources"] > gpu_score.factors["resources"]
        assert no_resource_score.factors["resources"] > network_score.factors["resources"]

    def test_feasibility_highly_feasible(self, scorer):
        """Test highly feasible task."""
        task = Task(
            id="task_1",
            name="Simple",
            estimated_duration=1,
            parallelizable=True,
        )

        score = scorer.score_task(task)

        assert score.feasibility_rating in (FeasibilityRating.HIGHLY_FEASIBLE, FeasibilityRating.FEASIBLE)

    def test_feasibility_infeasible(self, scorer):
        """Test infeasible task."""
        task = Task(
            id="task_1",
            name="Infeasible",
            estimated_duration=10000,
            parallelizable=False,
            resource_type="gpu",
            max_concurrent=0,  # Invalid
        )

        score = scorer.score_task(task)

        assert score.feasibility_rating in (FeasibilityRating.HIGH_RISK, FeasibilityRating.INFEASIBLE)

    def test_warnings_on_high_complexity(self, scorer):
        """Test warnings for high complexity."""
        task = Task(
            id="task_1",
            name="Complex",
            estimated_duration=2000,
            parallelizable=False,
        )

        score = scorer.score_task(task)

        assert len(score.warnings) > 0

    def test_recommendations_for_complex_task(self, scorer):
        """Test recommendations for complex task."""
        task = Task(
            id="task_1",
            name="Complex",
            estimated_duration=5000,
            parallelizable=False,
            resource_type="gpu",
        )

        score = scorer.score_task(task)

        assert len(score.recommendations) > 0
        # Either subtask or checkpoint recommendation should be present
        assert any(
            keyword in r.lower() for r in score.recommendations for keyword in ["subtask", "checkpoint", "monitoring"]
        )

    def test_score_workflow(self, scorer):
        """Test scoring entire workflow."""
        tasks = [
            Task(id="task_1", name="Task 1", estimated_duration=1),
            Task(id="task_2", name="Task 2", estimated_duration=10),
            Task(id="task_3", name="Task 3", estimated_duration=100),
        ]

        dependencies = [
            TaskDependency(
                source_task_id="task_1",
                target_task_id="task_2",
                dependency_type=DependencyType.HARD,
            ),
        ]

        workflow_score = scorer.score_workflow(tasks, dependencies)

        assert workflow_score["total_tasks"] == 3
        assert "average_complexity_score" in workflow_score
        assert "task_scores" in workflow_score

    def test_get_score(self, scorer):
        """Test retrieving calculated score."""
        task = Task(id="task_1", name="Task 1")
        scorer.score_task(task)

        score = scorer.get_score("task_1")
        assert score is not None
        assert score.task_id == "task_1"

    def test_get_unknown_score(self, scorer):
        """Test getting unknown score."""
        score = scorer.get_score("unknown")
        assert score is None

    def test_reset(self, scorer):
        """Test reset."""
        task = Task(id="task_1", name="Task 1")
        scorer.score_task(task)

        scorer.reset()

        assert len(scorer.scores) == 0
        assert scorer.get_score("task_1") is None

    def test_high_duration_warning(self, scorer):
        """Test warning for long duration."""
        task = Task(id="task_1", name="Long", estimated_duration=4000)

        score = scorer.score_task(task)

        assert any("30 minutes" in w for w in score.warnings)

    def test_concurrency_validation_warning(self, scorer):
        """Test warning for invalid concurrency."""
        task = Task(id="task_1", name="Invalid", max_concurrent=0)

        score = scorer.score_task(task)

        assert any("concurrency" in w.lower() for w in score.warnings)

    def test_parallelizable_conflict_recommendation(self, scorer):
        """Test recommendation for parallelizable conflict."""
        task = Task(
            id="task_1",
            name="Conflict",
            parallelizable=False,
            max_concurrent=5,
        )

        score = scorer.score_task(task)

        assert any("parallelizable" in r.lower() for r in score.recommendations)

    def test_moderate_complexity_classification(self, scorer):
        """Test moderate complexity classification."""
        task = Task(
            id="task_1",
            name="Moderate",
            estimated_duration=50,
            parallelizable=True,
        )

        score = scorer.score_task(task)

        assert score.complexity_level == ComplexityLevel.MODERATE
