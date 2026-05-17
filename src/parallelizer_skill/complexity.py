"""Task complexity scoring and feasibility validation (Phase 2, Resilience)."""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from parallelizer_skill.config import get_config
from parallelizer_skill.models import Task, TaskDependency, DependencyType


class ComplexityLevel(str, Enum):
    """Complexity classification levels."""

    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class FeasibilityRating(str, Enum):
    """Feasibility assessment."""

    HIGHLY_FEASIBLE = "highly_feasible"
    FEASIBLE = "feasible"
    CHALLENGING = "challenging"
    HIGH_RISK = "high_risk"
    INFEASIBLE = "infeasible"


@dataclass
class ComplexityScore:
    """Complete complexity assessment."""

    task_id: str
    complexity_level: ComplexityLevel
    feasibility_rating: FeasibilityRating
    score: float  # 0-100
    factors: Dict[str, float]  # Individual factor scores
    warnings: List[str]
    recommendations: List[str]


class ComplexityScorer:
    """Score task complexity and validate feasibility (Phase 2)."""

    def __init__(self):
        """Initialize complexity scorer."""
        self.config = get_config()
        self.scores: Dict[str, ComplexityScore] = {}

    def score_task(
        self,
        task: Task,
        dependencies: Optional[List[TaskDependency]] = None,
        other_tasks: Optional[List[Task]] = None,
    ) -> ComplexityScore:
        """Score complexity of a single task."""
        factors = {}
        warnings = []

        # Factor 1: Estimated duration
        duration_score = self._score_duration(task.estimated_duration)
        factors["duration"] = duration_score

        # Factor 2: Parallelizability
        parallel_score = 100 if task.parallelizable else 30
        factors["parallelizability"] = parallel_score

        # Factor 3: Resource requirements
        resource_score = self._score_resource_requirements(task.resource_type)
        factors["resources"] = resource_score

        # Factor 4: Concurrency limits
        concurrency_score = self._score_concurrency_limits(task.max_concurrent)
        factors["concurrency"] = concurrency_score

        # Factor 5: Dependency complexity
        dep_score = self._score_dependencies(task.id, dependencies)
        factors["dependencies"] = dep_score

        # Calculate composite score
        composite = sum(factors.values()) / len(factors)

        # Determine complexity level
        complexity_level = self._classify_complexity(composite)

        # Assess feasibility
        feasibility = self._assess_feasibility(task, dependencies, composite)

        # Generate warnings and recommendations
        if composite < 60:
            warnings.append("Task has high complexity score")
        if task.estimated_duration > 1800:
            warnings.append("Estimated duration exceeds 30 minutes")
        if task.max_concurrent < 1:
            warnings.append("Invalid concurrency limit (must be >= 1)")

        recommendations = self._generate_recommendations(task, complexity_level, feasibility)

        score = ComplexityScore(
            task_id=task.id,
            complexity_level=complexity_level,
            feasibility_rating=feasibility,
            score=composite,
            factors=factors,
            warnings=warnings,
            recommendations=recommendations,
        )

        self.scores[task.id] = score
        return score

    def _score_duration(self, estimated_duration: float) -> float:
        """Score based on estimated duration."""
        if estimated_duration <= 1:
            return 100
        elif estimated_duration <= 5:
            return 80
        elif estimated_duration <= 30:
            return 60
        elif estimated_duration <= 300:
            return 40
        else:
            return 20

    def _score_resource_requirements(self, resource_type: Optional[str]) -> float:
        """Score based on resource requirements."""
        if resource_type is None:
            return 100  # No special resources needed
        if resource_type in ("network", "disk"):
            return 70
        if resource_type in ("gpu", "memory"):
            return 40
        return 50  # Unknown resource type

    def _score_concurrency_limits(self, max_concurrent: int) -> float:
        """Score based on concurrency constraints."""
        if max_concurrent <= 0:
            return 0
        if max_concurrent >= 10:
            return 100
        return (max_concurrent / 10) * 100

    def _score_dependencies(
        self,
        task_id: str,
        dependencies: Optional[List[TaskDependency]] = None,
    ) -> float:
        """Score based on dependency complexity."""
        if not dependencies:
            return 100

        # Count dependencies on this task
        incoming = len([d for d in dependencies if d.target_task_id == task_id])
        outgoing = len([d for d in dependencies if d.source_task_id == task_id])

        # Count hard vs soft dependencies (for future use in detailed analysis)
        _hard_deps = len([d for d in dependencies if d.dependency_type == DependencyType.HARD])
        _soft_deps = len([d for d in dependencies if d.dependency_type == DependencyType.SOFT])

        # More dependencies = lower score
        total_deps = incoming + outgoing
        if total_deps == 0:
            return 100
        if total_deps <= 3:
            return 80
        if total_deps <= 6:
            return 60
        if total_deps <= 10:
            return 40
        return 20

    def _classify_complexity(self, score: float) -> ComplexityLevel:
        """Classify complexity based on score."""
        if score >= 95:
            return ComplexityLevel.TRIVIAL
        elif score >= 80:
            return ComplexityLevel.SIMPLE
        elif score >= 50:
            return ComplexityLevel.MODERATE
        elif score >= 25:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX

    def _assess_feasibility(
        self,
        task: Task,
        dependencies: Optional[List[TaskDependency]],
        complexity_score: float,
    ) -> FeasibilityRating:
        """Assess feasibility of task execution."""
        risk_factors = 0

        # High duration = higher risk
        if task.estimated_duration > 3600:
            risk_factors += 1

        # Many dependencies = higher risk
        if dependencies:
            dep_count = len([d for d in dependencies if d.target_task_id == task.id])
            if dep_count > 5:
                risk_factors += 1

        # Complex resource requirements = higher risk
        if task.resource_type and task.resource_type not in ("network", "disk"):
            risk_factors += 1

        # Non-parallelizable with dependencies = higher risk
        if not task.parallelizable and dependencies:
            dep_count = len([d for d in dependencies if d.target_task_id == task.id])
            if dep_count > 0:
                risk_factors += 1

        # Determine feasibility
        if complexity_score >= 85 and risk_factors == 0:
            return FeasibilityRating.HIGHLY_FEASIBLE
        elif complexity_score >= 65 and risk_factors <= 1:
            return FeasibilityRating.FEASIBLE
        elif complexity_score >= 40 and risk_factors <= 2:
            return FeasibilityRating.CHALLENGING
        elif complexity_score >= 20 and risk_factors <= 3:
            return FeasibilityRating.HIGH_RISK
        else:
            return FeasibilityRating.INFEASIBLE

    def _generate_recommendations(
        self,
        task: Task,
        complexity_level: ComplexityLevel,
        feasibility: FeasibilityRating,
    ) -> List[str]:
        """Generate recommendations based on assessment."""
        recommendations = []

        if complexity_level in (ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX):
            recommendations.append("Consider breaking this task into smaller subtasks")

        if feasibility in (FeasibilityRating.HIGH_RISK, FeasibilityRating.INFEASIBLE):
            recommendations.append("Enable enhanced monitoring and error handling")

        if task.estimated_duration > 1800:
            recommendations.append("Consider adding checkpoints for long-running tasks")

        if not task.parallelizable and task.max_concurrent > 1:
            recommendations.append("Task marked as non-parallelizable but has concurrency limits")

        if feasibility == FeasibilityRating.INFEASIBLE:
            recommendations.append("This task may not be feasible - consider alternative approach")

        return recommendations

    def score_workflow(self, tasks: List[Task], dependencies: List[TaskDependency]) -> Dict:
        """Score complexity of entire workflow."""
        individual_scores = []
        for task in tasks:
            score = self.score_task(task, dependencies, tasks)
            individual_scores.append(score)

        # Aggregate scores
        avg_complexity = sum(s.score for s in individual_scores) / len(individual_scores)

        # Determine worst feasibility (most severe rating)
        feasibility_order = {
            FeasibilityRating.HIGHLY_FEASIBLE: 0,
            FeasibilityRating.FEASIBLE: 1,
            FeasibilityRating.CHALLENGING: 2,
            FeasibilityRating.HIGH_RISK: 3,
            FeasibilityRating.INFEASIBLE: 4,
        }
        worst_feasibility = max(
            (s.feasibility_rating for s in individual_scores),
            key=lambda x: feasibility_order[x],
            default=FeasibilityRating.HIGHLY_FEASIBLE,
        )

        return {
            "total_tasks": len(tasks),
            "average_complexity_score": avg_complexity,
            "worst_feasibility": worst_feasibility,
            "task_scores": {s.task_id: s for s in individual_scores},
            "all_warnings": [w for s in individual_scores for w in s.warnings],
            "all_recommendations": [r for s in individual_scores for r in s.recommendations],
        }

    def get_score(self, task_id: str) -> Optional[ComplexityScore]:
        """Retrieve previously calculated score."""
        return self.scores.get(task_id)

    def reset(self) -> None:
        """Reset scores (for testing)."""
        self.scores.clear()
