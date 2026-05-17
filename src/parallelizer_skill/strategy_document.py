"""Strategy Document generator for parallelization recommendations (Phase 3)."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from parallelizer_skill.models import Task, TaskDependency, ExecutionPlan
from parallelizer_skill.complexity import ComplexityScore
from parallelizer_skill.decision_engine import DecisionRecommendation, DecisionContext
from parallelizer_skill.config import get_config


@dataclass
class StrategyDocument:
    """A structured strategy document."""
    document_id: str
    title: str
    generated_at: datetime
    executive_summary: str
    analysis_summary: Dict[str, Any]
    recommendations: Dict[str, Any]
    implementation_plan: List[str]
    risk_assessment: Dict[str, Any]
    performance_projections: Dict[str, Any]


class StrategyDocumentGenerator:
    """Generate strategy documents for parallelization (Phase 3)."""

    def __init__(self):
        """Initialize strategy document generator."""
        self.config = get_config()
        self.documents: Dict[str, StrategyDocument] = {}

    def generate(
        self,
        document_id: str,
        title: str,
        tasks: List[Task],
        dependencies: List[TaskDependency],
        complexity_scores: Dict[str, ComplexityScore],
        decision_recommendation: DecisionRecommendation,
        execution_plan: Optional[ExecutionPlan] = None,
    ) -> StrategyDocument:
        """Generate a strategy document."""
        # Generate sections
        executive_summary = self._generate_executive_summary(
            title, decision_recommendation, len(tasks)
        )
        analysis_summary = self._generate_analysis_summary(
            tasks, dependencies, complexity_scores, execution_plan
        )
        recommendations = self._generate_recommendations_section(decision_recommendation)
        implementation_plan = self._generate_implementation_plan(
            tasks, dependencies, decision_recommendation
        )
        risk_assessment = self._generate_risk_assessment(
            complexity_scores, dependencies, decision_recommendation
        )
        performance_projections = self._generate_performance_projections(
            execution_plan, decision_recommendation
        )

        document = StrategyDocument(
            document_id=document_id,
            title=title,
            generated_at=datetime.utcnow(),
            executive_summary=executive_summary,
            analysis_summary=analysis_summary,
            recommendations=recommendations,
            implementation_plan=implementation_plan,
            risk_assessment=risk_assessment,
            performance_projections=performance_projections,
        )

        self.documents[document_id] = document
        return document

    def _generate_executive_summary(
        self, title: str, recommendation: DecisionRecommendation, task_count: int
    ) -> str:
        """Generate executive summary."""
        summary = f"{title}\n\n"
        summary += f"Total Tasks: {task_count}\n"
        summary += f"Recommended Strategy: {recommendation.strategy_type.upper()}\n"
        summary += f"Parallelization: {'ENABLED' if recommendation.parallel_execution else 'DISABLED'}\n"
        summary += f"Max Concurrent Tasks: {recommendation.max_parallel_tasks}\n\n"
        summary += f"Rationale:\n{recommendation.rationale}"
        return summary

    def _generate_analysis_summary(
        self,
        tasks: List[Task],
        dependencies: List[TaskDependency],
        complexity_scores: Dict[str, ComplexityScore],
        execution_plan: Optional[ExecutionPlan] = None,
    ) -> Dict[str, Any]:
        """Generate analysis summary."""
        total_duration = sum(t.estimated_duration for t in tasks)
        critical_path = execution_plan.critical_path if execution_plan else []
        
        # Find most complex task
        most_complex = max(
            complexity_scores.values(),
            key=lambda s: s.score if hasattr(s, 'score') else 0,
            default=None
        )
        most_complex_id = most_complex.task_id if most_complex else None

        return {
            "total_tasks": len(tasks),
            "total_duration": total_duration,
            "dependency_count": len(dependencies),
            "critical_path": critical_path,
            "critical_path_length": len(critical_path),
            "most_complex_task": most_complex_id,
            "parallel_phases": execution_plan.phases if execution_plan else [],
            "potential_speedup": f"{execution_plan.serial_duration / execution_plan.parallel_duration:.1f}x"
            if execution_plan and execution_plan.parallel_duration > 0
            else "N/A",
        }

    def _generate_recommendations_section(
        self, recommendation: DecisionRecommendation
    ) -> Dict[str, Any]:
        """Generate recommendations section."""
        return {
            "strategy_type": recommendation.strategy_type,
            "max_parallel_tasks": recommendation.max_parallel_tasks,
            "batch_size": recommendation.recommended_batch_size,
            "retry_count": recommendation.recommended_retry_count,
            "checkpoint_interval_minutes": recommendation.recommended_checkpoint_interval,
            "resource_aware": recommendation.resource_aware,
            "monitoring_level": recommendation.monitoring_intensity,
            "escalation_level": recommendation.escalation_level,
            "key_actions": [
                f"Execute maximum {recommendation.max_parallel_tasks} tasks in parallel",
                f"Process tasks in batches of {recommendation.recommended_batch_size}",
                f"Implement retry logic with {recommendation.recommended_retry_count} attempts",
                f"Create checkpoints every {recommendation.recommended_checkpoint_interval} minutes",
                f"Enable {recommendation.monitoring_intensity} monitoring and alerting",
            ],
        }

    def _generate_implementation_plan(
        self,
        tasks: List[Task],
        dependencies: List[TaskDependency],
        recommendation: DecisionRecommendation,
    ) -> List[str]:
        """Generate implementation plan."""
        plan = [
            "1. PREPARATION",
            f"   - Configure max concurrency to {recommendation.max_parallel_tasks}",
            f"   - Set retry policy to {recommendation.recommended_retry_count} attempts",
            f"   - Enable {recommendation.monitoring_intensity} monitoring",
            "",
            "2. EXECUTION",
            f"   - Deploy {len(tasks)} tasks across {recommendation.max_parallel_tasks} worker streams",
            f"   - Process in batches of {recommendation.recommended_batch_size}",
            "   - Monitor resource utilization in real-time",
            "",
            "3. RESILIENCE",
            f"   - Checkpoint every {recommendation.recommended_checkpoint_interval} minutes",
            f"   - Retry failed tasks up to {recommendation.recommended_retry_count} times",
            f"   - Escalate to {recommendation.escalation_level} on critical failures",
            "",
            "4. MONITORING",
            f"   - Log at {recommendation.monitoring_intensity} verbosity",
            "   - Track execution metrics and performance",
            "   - Alert on threshold violations",
            "",
            "5. VALIDATION",
            "   - Verify all tasks complete successfully",
            "   - Compare actual vs projected performance",
            "   - Document lessons learned",
        ]
        return plan

    def _generate_risk_assessment(
        self,
        complexity_scores: Dict[str, ComplexityScore],
        dependencies: List[TaskDependency],
        recommendation: DecisionRecommendation,
    ) -> Dict[str, Any]:
        """Generate risk assessment."""
        # Count high-complexity tasks
        high_complexity_count = sum(
            1 for s in complexity_scores.values()
            if hasattr(s, 'score') and s.score < 40
        )

        # Calculate dependency risk
        dependency_risk = "low" if len(dependencies) < 5 else "medium" if len(dependencies) < 10 else "high"

        return {
            "high_complexity_tasks": high_complexity_count,
            "dependency_risk": dependency_risk,
            "failure_risk": recommendation.escalation_level,
            "resource_bottlenecks": "possible" if recommendation.resource_aware else "unlikely",
            "mitigation_strategies": [
                "Implement comprehensive error handling and logging",
                "Create recovery checkpoints at critical stages",
                "Use resource-aware scheduling to prevent bottlenecks",
                "Enable proactive monitoring for early issue detection",
                "Maintain rollback procedures for failed phases",
            ],
        }

    def _generate_performance_projections(
        self,
        execution_plan: Optional[ExecutionPlan],
        recommendation: DecisionRecommendation,
    ) -> Dict[str, Any]:
        """Generate performance projections."""
        if not execution_plan:
            return {
                "projected_serial_duration": "Unknown",
                "projected_parallel_duration": "Unknown",
                "expected_speedup": "Unknown",
                "efficiency_gain": "Unknown",
            }

        return {
            "projected_serial_duration": f"{execution_plan.serial_duration:.1f}s",
            "projected_parallel_duration": f"{execution_plan.parallel_duration:.1f}s",
            "expected_speedup": f"{execution_plan.serial_duration / execution_plan.parallel_duration:.1f}x"
            if execution_plan.parallel_duration > 0
            else "∞",
            "efficiency_gain": f"{execution_plan.efficiency_gain:.1f}%",
            "resource_utilization": "high" if recommendation.max_parallel_tasks > 8 else "medium" if recommendation.max_parallel_tasks > 4 else "low",
        }

    def get_document(self, document_id: str) -> Optional[StrategyDocument]:
        """Retrieve a generated document."""
        return self.documents.get(document_id)

    def render_markdown(self, document: StrategyDocument) -> str:
        """Render strategy document as Markdown."""
        md = f"# {document.title}\n\n"
        md += f"**Generated**: {document.generated_at.isoformat()}\n\n"

        md += "## Executive Summary\n\n"
        md += f"{document.executive_summary}\n\n"

        md += "## Analysis\n\n"
        for key, value in document.analysis_summary.items():
            md += f"- **{key.replace('_', ' ').title()}**: {value}\n"
        md += "\n"

        md += "## Recommendations\n\n"
        for key, value in document.recommendations.items():
            if isinstance(value, list):
                md += f"### {key.replace('_', ' ').title()}\n\n"
                for item in value:
                    md += f"- {item}\n"
                md += "\n"
            else:
                md += f"- **{key.replace('_', ' ').title()}**: {value}\n"
        md += "\n"

        md += "## Implementation Plan\n\n"
        for step in document.implementation_plan:
            md += f"{step}\n"
        md += "\n"

        md += "## Risk Assessment\n\n"
        for key, value in document.risk_assessment.items():
            if isinstance(value, list):
                md += f"### {key.replace('_', ' ').title()}\n\n"
                for item in value:
                    md += f"- {item}\n"
                md += "\n"
            else:
                md += f"- **{key.replace('_', ' ').title()}**: {value}\n"
        md += "\n"

        md += "## Performance Projections\n\n"
        for key, value in document.performance_projections.items():
            md += f"- **{key.replace('_', ' ').title()}**: {value}\n"

        return md

    def reset(self) -> None:
        """Reset document generator."""
        self.documents.clear()
