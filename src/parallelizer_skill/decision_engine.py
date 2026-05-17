"""Decision Engine with Q1-Q6 decision trees for strategy recommendations (Phase 3)."""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from parallelizer_skill.models import Task, TaskDependency
from parallelizer_skill.complexity import ComplexityScorer, ComplexityLevel, FeasibilityRating
from parallelizer_skill.config import get_config


class ParallelizationGoal(str, Enum):
    """Q1: Primary parallelization goal."""

    PERFORMANCE = "performance"  # Minimize execution time
    COST = "cost"  # Minimize resource consumption
    RELIABILITY = "reliability"  # Maximize success rate


class TaskComplexityClass(str, Enum):
    """Q2: Task complexity classification."""

    SIMPLE = "simple"  # TRIVIAL, SIMPLE
    MODERATE = "moderate"  # MODERATE
    COMPLEX = "complex"  # COMPLEX, VERY_COMPLEX


class ResourceConstraint(str, Enum):
    """Q3: Primary resource constraint."""

    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    NONE = "none"


class DependencyDensity(str, Enum):
    """Q4: Dependency structure."""

    SPARSE = "sparse"  # 0-1 deps per task
    MODERATE = "moderate"  # 2-3 deps per task
    DENSE = "dense"  # 4+ deps per task


class FailureTolerance(str, Enum):
    """Q5: Failure handling strategy."""

    FAIL_FAST = "fail_fast"  # Stop on first failure
    RETRY = "retry"  # Retry with backoff
    FALLBACK = "fallback"  # Use fallback mechanisms


class PriorityMetric(str, Enum):
    """Q6: Decision priority."""

    SPEED = "speed"  # Minimize latency
    COST = "cost"  # Minimize cost
    RELIABILITY = "reliability"  # Maximize availability


@dataclass
class DecisionContext:
    """Q1-Q6 decision context."""

    q1_goal: ParallelizationGoal
    q2_complexity: TaskComplexityClass
    q3_resource_constraint: ResourceConstraint
    q4_dependency_density: DependencyDensity
    q5_failure_tolerance: FailureTolerance
    q6_priority_metric: PriorityMetric


@dataclass
class DecisionRecommendation:
    """Recommendation from decision engine."""

    strategy_type: str  # "aggressive", "balanced", "conservative"
    max_parallel_tasks: int
    recommended_batch_size: int
    recommended_retry_count: int
    recommended_checkpoint_interval: int  # Minutes
    parallel_execution: bool
    resource_aware: bool
    monitoring_intensity: str  # "minimal", "normal", "intensive"
    escalation_level: str  # "none", "warning", "critical"
    rationale: str


class DecisionEngine:
    """Decision engine for parallelization strategy (Phase 3)."""

    def __init__(self):
        """Initialize decision engine."""
        self.config = get_config()
        self.complexity_scorer = ComplexityScorer()
        self.decisions: Dict[str, DecisionRecommendation] = {}

    def answer_q1(self, goal: ParallelizationGoal) -> ParallelizationGoal:
        """Q1: What is your parallelization goal?"""
        return goal

    def answer_q2(self, complexity_level: ComplexityLevel) -> TaskComplexityClass:
        """Q2: What is your task complexity?"""
        if complexity_level in (ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE):
            return TaskComplexityClass.SIMPLE
        elif complexity_level == ComplexityLevel.MODERATE:
            return TaskComplexityClass.MODERATE
        else:  # COMPLEX, VERY_COMPLEX
            return TaskComplexityClass.COMPLEX

    def answer_q3(self, resource_type: Optional[str]) -> ResourceConstraint:
        """Q3: What resource is constrained?"""
        if resource_type is None:
            return ResourceConstraint.NONE
        if resource_type == "cpu":
            return ResourceConstraint.CPU
        if resource_type == "memory":
            return ResourceConstraint.MEMORY
        if resource_type == "io":
            return ResourceConstraint.IO
        if resource_type == "network":
            return ResourceConstraint.NETWORK
        return ResourceConstraint.NONE

    def answer_q4(
        self, dependencies: Optional[List[TaskDependency]], tasks: Optional[List[Task]] = None
    ) -> DependencyDensity:
        """Q4: What is dependency density?"""
        if not dependencies or not tasks:
            return DependencyDensity.SPARSE

        total_deps = len(dependencies)
        task_count = len(tasks) if tasks else 1

        if task_count == 0:
            return DependencyDensity.SPARSE

        avg_deps_per_task = total_deps / task_count

        if avg_deps_per_task < 1.5:
            return DependencyDensity.SPARSE
        elif avg_deps_per_task < 3.0:
            return DependencyDensity.MODERATE
        else:
            return DependencyDensity.DENSE

    def answer_q5(self, failure_tolerance: FailureTolerance) -> FailureTolerance:
        """Q5: What is failure tolerance?"""
        return failure_tolerance

    def answer_q6(self, priority: PriorityMetric) -> PriorityMetric:
        """Q6: What is priority metric?"""
        return priority

    def make_decision(self, context: DecisionContext, feasibility: FeasibilityRating) -> DecisionRecommendation:
        """Make parallelization recommendation based on Q1-Q6 answers."""
        # Decision tree logic
        strategy_type = self._determine_strategy(context, feasibility)

        max_parallel = self._calculate_max_parallel(context)
        batch_size = self._calculate_batch_size(context, max_parallel)
        retry_count = self._calculate_retry_count(context)
        checkpoint_interval = self._calculate_checkpoint_interval(context)
        parallel_execution = self._should_parallelize(context, feasibility)
        resource_aware = context.q3_resource_constraint != ResourceConstraint.NONE
        monitoring_intensity = self._determine_monitoring(context, feasibility)
        escalation_level = self._determine_escalation(context, feasibility)
        rationale = self._generate_rationale(context, feasibility, strategy_type)

        recommendation = DecisionRecommendation(
            strategy_type=strategy_type,
            max_parallel_tasks=max_parallel,
            recommended_batch_size=batch_size,
            recommended_retry_count=retry_count,
            recommended_checkpoint_interval=checkpoint_interval,
            parallel_execution=parallel_execution,
            resource_aware=resource_aware,
            monitoring_intensity=monitoring_intensity,
            escalation_level=escalation_level,
            rationale=rationale,
        )

        return recommendation

    def _determine_strategy(self, context: DecisionContext, feasibility: FeasibilityRating) -> str:
        """Determine strategy type based on context and feasibility."""
        # Feasibility check
        if feasibility in (FeasibilityRating.INFEASIBLE, FeasibilityRating.HIGH_RISK):
            return "conservative"

        # Goal-driven strategy
        if context.q1_goal == ParallelizationGoal.PERFORMANCE:
            if context.q2_complexity == TaskComplexityClass.SIMPLE:
                return "aggressive"
            elif context.q2_complexity == TaskComplexityClass.MODERATE:
                return "balanced"
            else:
                return "conservative"

        elif context.q1_goal == ParallelizationGoal.COST:
            if context.q3_resource_constraint == ResourceConstraint.NONE:
                return "aggressive"
            else:
                return "conservative"

        elif context.q1_goal == ParallelizationGoal.RELIABILITY:
            return "conservative"

        return "balanced"

    def _calculate_max_parallel(self, context: DecisionContext) -> int:
        """Calculate maximum parallel tasks."""
        # Base on complexity
        base = {
            TaskComplexityClass.SIMPLE: 32,
            TaskComplexityClass.MODERATE: 16,
            TaskComplexityClass.COMPLEX: 4,
        }[context.q2_complexity]

        # Reduce based on resource constraints
        if context.q3_resource_constraint != ResourceConstraint.NONE:
            base = base // 2

        # Reduce based on dependency density
        if context.q4_dependency_density == DependencyDensity.DENSE:
            base = max(1, base // 2)

        return max(1, base)

    def _calculate_batch_size(self, context: DecisionContext, max_parallel: int) -> int:
        """Calculate recommended batch size."""
        if context.q1_goal == ParallelizationGoal.PERFORMANCE:
            return max_parallel
        elif context.q1_goal == ParallelizationGoal.COST:
            return max(1, max_parallel // 2)
        else:  # RELIABILITY
            return max(1, max_parallel // 4)

    def _calculate_retry_count(self, context: DecisionContext) -> int:
        """Calculate recommended retry count."""
        retry_map = {
            FailureTolerance.FAIL_FAST: 0,
            FailureTolerance.RETRY: 3,
            FailureTolerance.FALLBACK: 5,
        }
        return retry_map[context.q5_failure_tolerance]

    def _calculate_checkpoint_interval(self, context: DecisionContext) -> int:
        """Calculate checkpoint interval in minutes."""
        if context.q2_complexity == TaskComplexityClass.SIMPLE:
            return 60  # Long running tasks
        elif context.q2_complexity == TaskComplexityClass.MODERATE:
            return 30
        else:
            return 10

    def _should_parallelize(self, context: DecisionContext, feasibility: FeasibilityRating) -> bool:
        """Determine if parallelization is recommended."""
        if feasibility in (FeasibilityRating.INFEASIBLE, FeasibilityRating.HIGH_RISK):
            return False

        if context.q4_dependency_density == DependencyDensity.DENSE:
            return False

        if context.q1_goal == ParallelizationGoal.COST:
            return context.q3_resource_constraint == ResourceConstraint.NONE

        return True

    def _determine_monitoring(self, context: DecisionContext, feasibility: FeasibilityRating) -> str:
        """Determine monitoring intensity."""
        if feasibility in (FeasibilityRating.INFEASIBLE, FeasibilityRating.HIGH_RISK):
            return "intensive"
        elif context.q5_failure_tolerance == FailureTolerance.RETRY:
            return "normal"
        else:
            return "minimal"

    def _determine_escalation(self, context: DecisionContext, feasibility: FeasibilityRating) -> str:
        """Determine escalation level."""
        if feasibility == FeasibilityRating.INFEASIBLE:
            return "critical"
        elif feasibility == FeasibilityRating.HIGH_RISK:
            return "critical"
        elif feasibility == FeasibilityRating.CHALLENGING:
            return "warning"
        else:
            return "none"

    def _generate_rationale(self, context: DecisionContext, feasibility: FeasibilityRating, strategy_type: str) -> str:
        """Generate human-readable rationale for recommendation."""
        rationale = f"Strategy: {strategy_type.upper()}. "

        # Goal rationale
        rationale += f"Goal is {context.q1_goal.value}. "

        # Complexity rationale
        rationale += f"Complexity is {context.q2_complexity.value}. "

        # Resource rationale
        if context.q3_resource_constraint != ResourceConstraint.NONE:
            rationale += f"Resource constraint: {context.q3_resource_constraint.value}. "

        # Dependency rationale
        if context.q4_dependency_density != DependencyDensity.SPARSE:
            rationale += f"Dependency density is {context.q4_dependency_density.value}. "

        # Feasibility rationale
        rationale += f"Feasibility: {feasibility.value}. "

        return rationale

    def reset(self) -> None:
        """Reset decision engine."""
        self.decisions.clear()
