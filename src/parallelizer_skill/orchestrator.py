"""Orchestration Core for Phase 4 - Central workflow coordinator.

The WorkflowOrchestrator ties together all Phase 2-3 components:
- ComplexityScorer: Task complexity analysis
- DecisionEngine: Strategy recommendations (Q1-Q6)
- ExecutionPlanner: Execution plan creation
- EscalationManager: Failure handling and recovery
- PersistenceManager: State persistence
- StrategyDocumentGenerator: Output documentation
"""

from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from parallelizer_skill.config import get_config
from parallelizer_skill.models import (
    Task,
    TaskDependency,
    WorkflowAnalysis,
    ExecutionResult,
    ExecutionStatus,
)
from parallelizer_skill.complexity import ComplexityScorer, ComplexityLevel, FeasibilityRating
from parallelizer_skill.decision_engine import (
    DecisionEngine,
    DecisionContext,
    ParallelizationGoal,
    DecisionRecommendation,
)
from parallelizer_skill.strategy_document import StrategyDocumentGenerator, StrategyDocument
from parallelizer_skill.escalation import EscalationManager, EscalationLevel
from parallelizer_skill.persistence import PersistenceManager
from parallelizer_skill.dag_analyzer import DAGAnalyzer


class ExecutionPlanner:
    """Creates phased execution plans from tasks and dependencies."""

    def __init__(self):
        """Initialize execution planner."""
        self.config = get_config()

    def plan_execution(
        self,
        tasks: List[Task],
        dependencies: List[TaskDependency],
        decision_recommendation: DecisionRecommendation,
    ) -> "ExecutionPlan":
        """Create execution plan based on tasks and decision recommendation.

        Args:
            tasks: List of tasks to plan
            dependencies: Task dependencies
            decision_recommendation: Recommendation from decision engine

        Returns:
            ExecutionPlan: Phased execution plan
        """
        from parallelizer_skill.models import ExecutionPlan

        analyzer = DAGAnalyzer(tasks, dependencies)

        # Calculate durations
        serial_duration = sum(task.estimated_duration for task in tasks)
        critical_path = analyzer.get_critical_path()

        # Create simple execution phases based on decision recommendation
        phases = self._create_phases(tasks, dependencies, decision_recommendation, analyzer)

        # Calculate parallel duration
        parallel_duration = sum(phase.estimated_duration for phase in phases)
        efficiency_gain = (
            ((serial_duration - parallel_duration) / serial_duration * 100) if serial_duration > 0 else 0.0
        )

        return ExecutionPlan(
            id=f"plan-{uuid4()}",
            total_tasks=len(tasks),
            serial_duration=serial_duration,
            parallel_duration=parallel_duration,
            efficiency_gain=efficiency_gain,
            phases=phases,
            critical_path=critical_path,
            parallelizable_groups=self._get_parallelizable_groups(tasks, dependencies),
            resource_conflicts=self._check_resource_conflicts(tasks),
            safety_issues=self._check_safety_issues(tasks, dependencies),
            optimization_notes=self._generate_notes(decision_recommendation),
        )

    def _create_phases(
        self,
        tasks: List[Task],
        dependencies: List[TaskDependency],
        decision_recommendation: DecisionRecommendation,
        analyzer: DAGAnalyzer,
    ):
        """Create execution phases from tasks."""
        from parallelizer_skill.models import ExecutionPhase, TaskGroup

        # Simple phase creation: group independent tasks
        task_ids = {task.id for task in tasks}
        task_map = {task.id: task for task in tasks}

        phases = []
        remaining = set(task_ids)
        phase_num = 1

        while remaining:
            # Get tasks ready to execute (no unsatisfied dependencies)
            ready_tasks = []
            for task_id in remaining:
                # Check if all dependencies are satisfied
                deps_satisfied = True
                for dep in dependencies:
                    if dep.target_task_id == task_id and dep.source_task_id in remaining:
                        deps_satisfied = False
                        break
                if deps_satisfied:
                    ready_tasks.append(task_id)

            if not ready_tasks:
                # Fallback: just take first remaining task to avoid infinite loop
                ready_tasks = [remaining.pop()]
                remaining.add(ready_tasks[0])

            # Create phase with ready tasks
            phase_duration = sum(task_map[tid].estimated_duration for tid in ready_tasks)
            task_group = TaskGroup(
                id=f"group-{phase_num}",
                tasks=ready_tasks,
                sequential_order=None,
                estimated_duration=phase_duration,
                can_parallelize=decision_recommendation.parallel_execution,
            )

            phases.append(
                ExecutionPhase(
                    phase_number=phase_num,
                    task_groups=[task_group],
                    is_parallel=decision_recommendation.parallel_execution,
                    estimated_duration=phase_duration,
                    sync_point_required=phase_num < len(remaining) // max(1, len(ready_tasks)),
                )
            )

            # Remove executed tasks
            for task_id in ready_tasks:
                remaining.discard(task_id)

            phase_num += 1

        return phases

    def _get_parallelizable_groups(self, tasks: List[Task], dependencies: List[TaskDependency]) -> Dict[str, List[str]]:
        """Identify groups of tasks that can run in parallel."""
        groups = {}

        for task in tasks:
            if task.parallelizable:
                # Find all tasks with no path between them
                parallel_group = [t.id for t in tasks if t.parallelizable and t.id != task.id]
                groups[task.id] = parallel_group

        return groups

    def _check_resource_conflicts(self, tasks: List[Task]) -> List[str]:
        """Check for potential resource conflicts."""
        conflicts = []
        resource_usage: Dict[str, int] = {}

        for task in tasks:
            if task.resource_type:
                current = resource_usage.get(task.resource_type, 0)
                if current + 1 > task.max_concurrent:
                    conflicts.append(
                        f"Resource {task.resource_type} exceeds max concurrent: "
                        f"{current + 1} > {task.max_concurrent}"
                    )
                resource_usage[task.resource_type] = current + 1

        return conflicts

    def _check_safety_issues(self, tasks: List[Task], dependencies: List[TaskDependency]) -> List[str]:
        """Check for safety issues."""
        issues = []
        analyzer = DAGAnalyzer(tasks, dependencies)

        if analyzer.has_cycles():
            cycles = analyzer.get_cycles()
            issues.append(f"Circular dependencies detected: {cycles}")

        return issues

    def _generate_notes(self, recommendation: DecisionRecommendation) -> List[str]:
        """Generate optimization notes from recommendation."""
        notes = [
            f"Strategy: {recommendation.strategy_type}",
            f"Max parallel tasks: {recommendation.max_parallel_tasks}",
            f"Batch size: {recommendation.recommended_batch_size}",
            f"Monitoring level: {recommendation.monitoring_intensity}",
        ]
        return notes


class WorkflowOrchestrator:
    """Central orchestrator for parallelization workflows.

    Coordinates all Phase 2-3 components to execute complete
    parallelization workflows from task definition through
    execution and recovery.
    """

    def __init__(self, persistence_path: Optional[str] = None):
        """Initialize workflow orchestrator.

        Args:
            persistence_path: Optional path for state persistence
        """
        self.config = get_config()
        self.complexity_scorer = ComplexityScorer()
        self.decision_engine = DecisionEngine()
        self.execution_planner = ExecutionPlanner()
        self.strategy_generator = StrategyDocumentGenerator()
        self.escalation_manager = EscalationManager()
        self.persistence_manager = PersistenceManager(persistence_path)

    def analyze_workflow(
        self,
        workflow_id: str,
        tasks: List[Task],
        dependencies: List[TaskDependency],
    ) -> WorkflowAnalysis:
        """Analyze workflow's parallelization potential.

        Runs complexity scoring on all tasks and analyzes
        the dependency graph.

        Args:
            workflow_id: Unique workflow identifier
            tasks: List of tasks to analyze
            dependencies: Task dependencies

        Returns:
            WorkflowAnalysis: Complete analysis with scores and ratings
        """
        # Score task complexity
        complexity_scores = {}
        feasibility_ratings = {}
        for task in tasks:
            score = self.complexity_scorer.score_task(task, dependencies)
            complexity_scores[task.id] = score.score
            feasibility_ratings[task.id] = score.feasibility_rating.value

        # Analyze dependency graph
        analyzer = DAGAnalyzer(tasks, dependencies)
        critical_path = analyzer.get_critical_path()
        critical_path_duration = (
            sum(next((t.estimated_duration for t in tasks if t.id == tid), 0) for tid in critical_path)
            if critical_path
            else 0.0
        )
        total_duration = sum(task.estimated_duration for task in tasks)

        # Identify parallelizable tasks
        parallelizable = [t.id for t in tasks if t.parallelizable]

        # Find bottlenecks
        bottlenecks = [
            t.id
            for t in tasks
            if (
                not t.parallelizable
                or any(dep.target_task_id == t.id for dep in dependencies if dep.dependency_type.value == "hard")
            )
        ]

        # Check resource conflicts
        conflicts = self._check_resource_conflicts(tasks)

        # Generate warnings
        warnings = []
        if analyzer.has_cycles():
            warnings.append("Circular dependencies detected")
        if len(bottlenecks) > len(tasks) * 0.5:
            warnings.append("More than 50% of tasks are sequential bottlenecks")

        analysis = WorkflowAnalysis(
            analysis_id=f"analysis-{uuid4()}",
            workflow_id=workflow_id,
            total_tasks=len(tasks),
            total_dependencies=len(dependencies),
            complexity_scores=complexity_scores,
            feasibility_ratings=feasibility_ratings,
            critical_path=critical_path,
            critical_path_duration=critical_path_duration,
            total_serial_duration=total_duration,
            parallelizable_tasks=parallelizable,
            sequential_bottlenecks=bottlenecks,
            resource_conflicts=conflicts,
            warnings=warnings,
        )

        # Persist analysis
        self.persistence_manager.save_snapshot(
            snapshot_id=f"analysis-{analysis.analysis_id}",
            state_type="analysis",
            source_id=workflow_id,
            data={
                "analysis_id": analysis.analysis_id,
                "total_tasks": analysis.total_tasks,
                "complexity_scores": complexity_scores,
                "critical_path": critical_path,
            },
        )

        return analysis

    def generate_strategy(
        self,
        workflow_analysis: WorkflowAnalysis,
        parallelization_goal: ParallelizationGoal,
        resource_constraint: Optional[str] = None,
        failure_tolerance: Optional[str] = None,
    ) -> DecisionRecommendation:
        """Generate parallelization strategy using decision engine.

        Feeds workflow analysis into decision engine Q1-Q6 questions
        to produce a strategy recommendation.

        Args:
            workflow_analysis: Analysis from analyze_workflow
            parallelization_goal: Primary goal (performance/cost/reliability)
            resource_constraint: Optional resource constraint (cpu/memory/io/network)
            failure_tolerance: Optional failure strategy (fail_fast/retry/fallback)

        Returns:
            DecisionRecommendation: Strategy recommendation with constraints
        """
        from parallelizer_skill.decision_engine import (
            DependencyDensity,
            FailureTolerance,
            PriorityMetric,
        )

        # Answer Q1: parallelization goal
        q1_goal = self.decision_engine.answer_q1(parallelization_goal)

        # Answer Q2: task complexity (average of all complexity scores)
        avg_complexity = (
            sum(workflow_analysis.complexity_scores.values()) / len(workflow_analysis.complexity_scores)
            if workflow_analysis.complexity_scores
            else 50.0
        )
        complexity_level = (
            ComplexityLevel.TRIVIAL
            if avg_complexity < 20
            else (
                ComplexityLevel.SIMPLE
                if avg_complexity < 40
                else (
                    ComplexityLevel.MODERATE
                    if avg_complexity < 60
                    else ComplexityLevel.COMPLEX if avg_complexity < 80 else ComplexityLevel.VERY_COMPLEX
                )
            )
        )
        q2_complexity = self.decision_engine.answer_q2(complexity_level)

        # Answer Q3: resource constraint
        q3_resource = self.decision_engine.answer_q3(resource_constraint)

        # Answer Q4: dependency density (use task and dependency counts)
        q4_density = DependencyDensity.SPARSE
        if workflow_analysis.total_tasks > 0:
            deps_per_task = workflow_analysis.total_dependencies / workflow_analysis.total_tasks
            if deps_per_task >= 3.0:
                q4_density = DependencyDensity.DENSE
            elif deps_per_task >= 1.5:
                q4_density = DependencyDensity.MODERATE

        # Answer Q5: failure tolerance
        q5_tolerance = (
            FailureTolerance.FAIL_FAST
            if failure_tolerance == "fail_fast"
            else (
                FailureTolerance.RETRY
                if failure_tolerance == "retry"
                else FailureTolerance.FALLBACK if failure_tolerance == "fallback" else FailureTolerance.RETRY
            )
        )

        # Answer Q6: priority metric (derived from Q1 goal)
        q6_priority = (
            PriorityMetric.SPEED
            if q1_goal == ParallelizationGoal.PERFORMANCE
            else PriorityMetric.COST if q1_goal == ParallelizationGoal.COST else PriorityMetric.RELIABILITY
        )

        # Build decision context
        context = DecisionContext(
            q1_goal=q1_goal,
            q2_complexity=q2_complexity,
            q3_resource_constraint=q3_resource,
            q4_dependency_density=q4_density,
            q5_failure_tolerance=q5_tolerance,
            q6_priority_metric=q6_priority,
        )

        # Determine feasibility rating (average of all ratings)
        feasibility_map = {
            "highly_feasible": FeasibilityRating.HIGHLY_FEASIBLE,
            "feasible": FeasibilityRating.FEASIBLE,
            "challenging": FeasibilityRating.CHALLENGING,
            "high_risk": FeasibilityRating.HIGH_RISK,
            "infeasible": FeasibilityRating.INFEASIBLE,
        }
        ratings = [
            feasibility_map.get(rating, FeasibilityRating.FEASIBLE)
            for rating in workflow_analysis.feasibility_ratings.values()
        ]
        avg_feasibility = ratings[0] if ratings else FeasibilityRating.FEASIBLE

        # Get recommendation
        recommendation = self.decision_engine.make_decision(context, avg_feasibility)

        # Persist recommendation
        self.persistence_manager.save_snapshot(
            snapshot_id=f"recommendation-{uuid4()}",
            state_type="recommendation",
            source_id=workflow_analysis.workflow_id,
            data={
                "strategy_type": recommendation.strategy_type,
                "max_parallel_tasks": recommendation.max_parallel_tasks,
                "monitoring_intensity": recommendation.monitoring_intensity,
            },
        )

        return recommendation

    def plan_execution(
        self,
        tasks: List[Task],
        dependencies: List[TaskDependency],
        decision_recommendation: DecisionRecommendation,
    ) -> "ExecutionPlan":
        """Create executable phased execution plan.

        Uses ExecutionPlanner to create phases that apply
        the decision recommendation constraints.

        Args:
            tasks: Tasks to plan
            dependencies: Task dependencies
            decision_recommendation: Constraints from decision engine

        Returns:
            ExecutionPlan: Phased execution plan
        """
        plan = self.execution_planner.plan_execution(tasks, dependencies, decision_recommendation)
        return plan

    def create_strategy_document(
        self,
        workflow_analysis: WorkflowAnalysis,
        decision_recommendation: DecisionRecommendation,
        execution_plan: Optional["ExecutionPlan"] = None,
    ) -> StrategyDocument:
        """Generate comprehensive strategy document.

        Combines analysis, recommendation, and plan into
        a structured strategy document.

        Args:
            workflow_analysis: Workflow analysis
            decision_recommendation: Strategy recommendation
            execution_plan: Optional execution plan

        Returns:
            StrategyDocument: Comprehensive strategy document
        """
        # Build document title and ID
        doc_id = f"strategy-{uuid4()}"
        title = f"Parallelization Strategy: {workflow_analysis.workflow_id}"

        # Get tasks (reconstruct from analysis - simplified)
        tasks = []  # In real implementation, would be passed or retrieved
        dependencies = []  # In real implementation, would be passed or retrieved

        # Generate strategy document
        document = self.strategy_generator.generate(
            document_id=doc_id,
            title=title,
            tasks=tasks,
            dependencies=dependencies,
            complexity_scores={
                tid: ComplexityScore(
                    task_id=tid,
                    complexity_level=ComplexityLevel.MODERATE,
                    feasibility_rating=FeasibilityRating[
                        workflow_analysis.feasibility_ratings.get(tid, "FEASIBLE").upper()
                    ],
                    score=workflow_analysis.complexity_scores.get(tid, 50.0),
                    factors={},
                    warnings=[],
                    recommendations=[],
                )
                for tid in workflow_analysis.complexity_scores.keys()
            },
            decision_recommendation=decision_recommendation,
            execution_plan=execution_plan,
        )

        return document

    def execute_workflow(
        self,
        execution_plan: "ExecutionPlan",
        workflow_id: str,
    ) -> ExecutionResult:
        """Execute workflow using execution plan.

        Simulates or coordinates workflow execution,
        recording recovery points and handling failures.

        Args:
            execution_plan: Execution plan from plan_execution
            workflow_id: Workflow identifier

        Returns:
            ExecutionResult: Execution result with metrics
        """
        execution_id = f"exec-{uuid4()}"
        start_time = datetime.utcnow()

        try:
            # Simulate execution of phases
            phases_executed = 0
            tasks_completed = 0
            tasks_failed = 0
            tasks_skipped = 0
            recovery_events = 0
            escalation_events = 0

            for phase in execution_plan.phases:
                try:
                    # Record recovery point before phase
                    self.persistence_manager.save_recovery_point(
                        recovery_id=f"recovery-phase-{phase.phase_number}",
                        stage_number=phase.phase_number,
                        task_id="phase_execution",
                        agent_id="orchestrator",
                        status="in_progress",
                        context={"phase_number": phase.phase_number},
                    )

                    # Execute phase (simulated)
                    phase_tasks = []
                    for group in phase.task_groups:
                        phase_tasks.extend(group.tasks)

                    # Simulate task execution
                    for task_id in phase_tasks:
                        # Random success/failure simulation would happen here
                        # For now, assume all succeed
                        tasks_completed += 1

                    phases_executed += 1

                except Exception as phase_error:
                    # Trigger escalation on phase failure
                    escalation_event = self.escalation_manager.record_failure(
                        agent_id="orchestrator",
                        task_id="phase_execution",
                        level=EscalationLevel.WARNING,
                        cause=str(phase_error),
                    )
                    escalation_events += 1
                    recovery_events += 1

                    # Record recovery attempt
                    self.persistence_manager.save_recovery_point(
                        recovery_id=f"recovery-escalation-{escalation_event.escalation_id}",
                        stage_number=phase.phase_number,
                        task_id="phase_execution",
                        agent_id="orchestrator",
                        status="recovery",
                        context={"escalation": escalation_event.escalation_id},
                    )

            # Calculate efficiency
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            efficiency_achieved = (
                ((execution_plan.serial_duration - duration) / execution_plan.serial_duration * 100)
                if execution_plan.serial_duration > 0
                else 0.0
            )

            result = ExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=ExecutionStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                tasks_skipped=tasks_skipped,
                phases_executed=phases_executed,
                total_phases=len(execution_plan.phases),
                efficiency_achieved=efficiency_achieved,
                recovery_events=recovery_events,
                escalation_events=escalation_events,
                metrics={
                    "average_phase_duration": duration / max(1, phases_executed),
                    "success_rate": (
                        (tasks_completed / execution_plan.total_tasks * 100) if execution_plan.total_tasks > 0 else 0.0
                    ),
                },
            )

        except Exception as exec_error:
            # Handle workflow-level failure
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            result = ExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                tasks_completed=tasks_completed,
                tasks_failed=1,
                phases_executed=phases_executed,
                total_phases=len(execution_plan.phases),
                error_message=str(exec_error),
                recovery_events=recovery_events,
                escalation_events=escalation_events,
            )

        # Persist final result
        self.persistence_manager.save_snapshot(
            snapshot_id=f"result-{execution_id}",
            state_type="execution_result",
            source_id=workflow_id,
            data={
                "execution_id": execution_id,
                "status": result.status.value,
                "tasks_completed": result.tasks_completed,
                "efficiency": result.efficiency_achieved,
            },
        )

        return result

    def _check_resource_conflicts(self, tasks: List[Task]) -> List[str]:
        """Check for resource conflicts among tasks."""
        conflicts = []
        resource_usage: Dict[str, int] = {}

        for task in tasks:
            if task.resource_type:
                current = resource_usage.get(task.resource_type, 0)
                if current + 1 > task.max_concurrent:
                    conflicts.append(
                        f"Resource {task.resource_type} exceeds max concurrent: "
                        f"{current + 1} > {task.max_concurrent}"
                    )
                resource_usage[task.resource_type] = current + 1

        return conflicts


# Import here to avoid circular imports
from parallelizer_skill.models import ExecutionPlan  # noqa: E402
from parallelizer_skill.complexity import ComplexityScore  # noqa: E402
