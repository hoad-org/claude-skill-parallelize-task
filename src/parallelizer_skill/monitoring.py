"""Production-grade monitoring and observability (Phase 5).

Provides metrics tracking, event logging, execution tracing, health monitoring,
and alerting for the parallelize-task skill.
"""

import json
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from collections import OrderedDict, deque


# ============================================================================
# Enums & Configuration
# ============================================================================


class EventType(str, Enum):
    """Types of events that can be logged."""

    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    DECISION_MADE = "decision_made"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    ESCALATION_TRIGGERED = "escalation_triggered"
    RECOVERY_ATTEMPTED = "recovery_attempted"
    RESOURCE_CONSTRAINT = "resource_constraint"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class Severity(str, Enum):
    """Event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts that can be generated."""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    HIGH_FAILURE_RATE = "high_failure_rate"
    EXCESSIVE_ESCALATIONS = "excessive_escalations"
    CACHE_THRASHING = "cache_thrashing"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    HEALTH_CHECK_FAILED = "health_check_failed"


class HealthStatus(str, Enum):
    """Health status of the system."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and observability."""

    monitoring_enabled: bool = True
    event_buffer_size: int = 10000
    trace_enabled: bool = True
    health_check_interval: int = 300  # seconds
    alert_enabled: bool = True
    cache_health_threshold: float = 0.7  # min hit rate
    escalation_frequency_threshold: int = 5  # per workflow
    failure_rate_threshold: float = 0.2  # 20% failure rate
    performance_degradation_threshold: float = 1.5  # 1.5x baseline


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class WorkflowMetrics:
    """Metrics for a complete workflow execution."""

    workflow_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    phases_executed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_skipped: int = 0
    parallelization_speedup: float = 1.0
    resource_utilization_percent: float = 0.0
    cache_hit_rate: float = 0.0
    escalations_count: int = 0
    recovery_events: int = 0
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": self.total_duration_seconds,
            "phases_executed": self.phases_executed,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_skipped": self.tasks_skipped,
            "parallelization_speedup": self.parallelization_speedup,
            "resource_utilization_percent": self.resource_utilization_percent,
            "cache_hit_rate": self.cache_hit_rate,
            "escalations_count": self.escalations_count,
            "recovery_events": self.recovery_events,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class PhaseMetrics:
    """Metrics for a single phase of execution."""

    phase_number: int
    workflow_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    task_count: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = 1.0
    is_critical_path: bool = False
    bottleneck_identified: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "phase_number": self.phase_number,
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "task_count": self.task_count,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": self.success_rate,
            "is_critical_path": self.is_critical_path,
            "bottleneck_identified": self.bottleneck_identified,
        }


@dataclass
class WorkflowEvent:
    """Structured event representing a significant occurrence."""

    event_id: str
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: Severity = Severity.INFO
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    source: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "source": self.source,
            "details": self.details,
            "correlation_id": self.correlation_id,
        }


@dataclass
class ExecutionTrace:
    """Trace of execution flow for a single operation."""

    trace_id: str
    operation_name: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    status: str = "pending"
    parent_trace_id: Optional[str] = None
    children_trace_ids: List[str] = field(default_factory=list)
    decision_points: List[Dict[str, Any]] = field(default_factory=list)
    execution_path: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "trace_id": self.trace_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "parent_trace_id": self.parent_trace_id,
            "children_trace_ids": self.children_trace_ids,
            "decision_points": self.decision_points,
            "execution_path": self.execution_path,
        }


@dataclass
class HealthCheck:
    """Result of a system health check."""

    check_id: str
    check_time: datetime = field(default_factory=datetime.utcnow)
    cache_health: float = 1.0  # 0-1 score
    escalation_frequency: int = 0
    failure_rate: float = 0.0  # 0-1
    resource_available: bool = True
    overall_status: HealthStatus = HealthStatus.HEALTHY
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "check_id": self.check_id,
            "check_time": self.check_time.isoformat(),
            "cache_health": self.cache_health,
            "escalation_frequency": self.escalation_frequency,
            "failure_rate": self.failure_rate,
            "resource_available": self.resource_available,
            "overall_status": self.overall_status.value,
            "issues": self.issues,
        }


@dataclass
class Alert:
    """Alert generated when threshold conditions are met."""

    alert_id: str
    alert_type: AlertType
    severity: Severity
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message: str = ""
    threshold: float = 0.0
    current_value: float = 0.0
    recommended_action: Optional[str] = None
    workflow_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "recommended_action": self.recommended_action,
            "workflow_id": self.workflow_id,
        }


# ============================================================================
# Core Monitoring Components
# ============================================================================


class EventLogger:
    """Centralized event collection with filtering and history management."""

    def __init__(self, buffer_size: int = 10000):
        """Initialize event logger."""
        self.buffer_size = buffer_size
        self.events: deque = deque(maxlen=buffer_size)
        self.event_counts: Dict[EventType, int] = {et: 0 for et in EventType}
        self._lock = threading.RLock()
        self._next_event_id = 0

    def log_event(
        self,
        event_type: EventType,
        severity: Severity = Severity.INFO,
        workflow_id: Optional[str] = None,
        task_id: Optional[str] = None,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Log an event and return its ID."""
        with self._lock:
            event_id = f"evt_{self._next_event_id:08d}"
            self._next_event_id += 1

            event = WorkflowEvent(
                event_id=event_id,
                event_type=event_type,
                severity=severity,
                workflow_id=workflow_id,
                task_id=task_id,
                source=source,
                details=details or {},
                correlation_id=correlation_id,
            )

            self.events.append(event)
            self.event_counts[event_type] += 1
            return event_id

    def get_events(
        self,
        event_type: Optional[EventType] = None,
        severity: Optional[Severity] = None,
        workflow_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[WorkflowEvent]:
        """Filter events by criteria."""
        with self._lock:
            events = list(self.events)

        filtered = events
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        if workflow_id:
            filtered = [e for e in filtered if e.workflow_id == workflow_id]

        return filtered[-limit:]

    def get_event_summary(self) -> Dict[str, int]:
        """Get count of events by type."""
        with self._lock:
            return dict(self.event_counts)

    def clear_old_events(self, older_than_seconds: int = 86400) -> int:
        """Remove events older than specified duration. Returns count removed."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(seconds=older_than_seconds)
            initial_len = len(self.events)

            # Create new deque without old events
            new_events = deque(
                (e for e in self.events if e.timestamp > cutoff),
                maxlen=self.buffer_size,
            )
            self.events = new_events

            return initial_len - len(self.events)


class TraceCollector:
    """Collect and aggregate execution traces."""

    def __init__(self):
        """Initialize trace collector."""
        self.traces: Dict[str, ExecutionTrace] = {}
        self.trace_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        self._lock = threading.RLock()
        self._next_trace_id = 0

    def start_trace(
        self,
        operation_name: str,
        parent_trace_id: Optional[str] = None,
    ) -> str:
        """Start a new trace and return its ID."""
        with self._lock:
            trace_id = f"tr_{self._next_trace_id:08d}"
            self._next_trace_id += 1

            trace = ExecutionTrace(
                trace_id=trace_id,
                operation_name=operation_name,
                parent_trace_id=parent_trace_id,
            )

            self.traces[trace_id] = trace

            if parent_trace_id:
                if parent_trace_id not in self.trace_hierarchy:
                    self.trace_hierarchy[parent_trace_id] = []
                self.trace_hierarchy[parent_trace_id].append(trace_id)
                parent = self.traces.get(parent_trace_id)
                if parent:
                    parent.children_trace_ids.append(trace_id)

            return trace_id

    def end_trace(self, trace_id: str, status: str = "completed") -> None:
        """Mark a trace as completed."""
        with self._lock:
            if trace_id in self.traces:
                trace = self.traces[trace_id]
                trace.end_time = datetime.utcnow()
                trace.duration_seconds = (
                    trace.end_time - trace.start_time
                ).total_seconds()
                trace.status = status

    def add_decision_point(
        self, trace_id: str, decision: str, outcome: str
    ) -> None:
        """Record a decision point in the trace."""
        with self._lock:
            if trace_id in self.traces:
                self.traces[trace_id].decision_points.append(
                    {"decision": decision, "outcome": outcome}
                )

    def add_execution_step(self, trace_id: str, step: str) -> None:
        """Add a step to the execution path."""
        with self._lock:
            if trace_id in self.traces:
                self.traces[trace_id].execution_path.append(step)

    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """Retrieve a trace by ID."""
        with self._lock:
            return self.traces.get(trace_id)

    def get_trace_timeline(self, trace_id: str) -> List[ExecutionTrace]:
        """Get ordered timeline of trace and all children."""
        def collect_traces(tid: str) -> List[ExecutionTrace]:
            traces = [self.traces[tid]]
            for child_id in self.trace_hierarchy.get(tid, []):
                traces.extend(collect_traces(child_id))
            return traces

        with self._lock:
            if trace_id not in self.traces:
                return []
            return collect_traces(trace_id)

    def clear_old_traces(self, older_than_seconds: int = 86400) -> int:
        """Remove traces older than specified duration. Returns count removed."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(seconds=older_than_seconds)
            to_delete = [
                tid
                for tid, trace in self.traces.items()
                if trace.start_time < cutoff
            ]

            for tid in to_delete:
                del self.traces[tid]

            # Clean up hierarchy
            self.trace_hierarchy = {
                parent: [
                    child for child in children if child not in to_delete
                ]
                for parent, children in self.trace_hierarchy.items()
                if parent not in to_delete
            }

            return len(to_delete)


class HealthMonitor:
    """Continuous health monitoring with status transitions."""

    def __init__(self, config: MonitoringConfig):
        """Initialize health monitor."""
        self.config = config
        self.health_checks: deque = deque(maxlen=1000)
        self.current_status = HealthStatus.HEALTHY
        self.status_history: List[tuple] = []
        self._lock = threading.RLock()
        self._next_check_id = 0
        self.last_check_time = datetime.utcnow()

    def perform_check(
        self,
        cache_health: float,
        escalation_frequency: int,
        failure_rate: float,
        resource_available: bool,
    ) -> HealthCheck:
        """Perform a health check and determine status."""
        with self._lock:
            check_id = f"hc_{self._next_check_id:08d}"
            self._next_check_id += 1

            issues = []
            if cache_health < self.config.cache_health_threshold:
                issues.append("cache_health_low")
            if escalation_frequency > self.config.escalation_frequency_threshold:
                issues.append("excessive_escalations")
            if failure_rate > self.config.failure_rate_threshold:
                issues.append("high_failure_rate")
            if not resource_available:
                issues.append("resource_unavailable")

            if issues:
                status = (
                    HealthStatus.UNHEALTHY
                    if len(issues) > 2
                    else HealthStatus.DEGRADED
                )
            else:
                status = HealthStatus.HEALTHY

            check = HealthCheck(
                check_id=check_id,
                cache_health=cache_health,
                escalation_frequency=escalation_frequency,
                failure_rate=failure_rate,
                resource_available=resource_available,
                overall_status=status,
                issues=issues,
            )

            self.health_checks.append(check)
            self._update_status(status)
            self.last_check_time = datetime.utcnow()

            return check

    def _update_status(self, new_status: HealthStatus) -> None:
        """Update health status and record transition."""
        if new_status != self.current_status:
            self.status_history.append(
                (self.current_status, new_status, datetime.utcnow())
            )
            self.current_status = new_status

    def get_status_history(
        self, limit: int = 100
    ) -> List[tuple]:
        """Get recent status transitions."""
        with self._lock:
            return self.status_history[-limit:]

    def get_latest_check(self) -> Optional[HealthCheck]:
        """Get the most recent health check."""
        with self._lock:
            return self.health_checks[-1] if self.health_checks else None


class AlertManager:
    """Alert generation, deduplication, and management."""

    def __init__(self, config: MonitoringConfig):
        """Initialize alert manager."""
        self.config = config
        self.alerts: deque = deque(maxlen=5000)
        self.alert_history: Dict[AlertType, int] = {at: 0 for at in AlertType}
        self.active_alerts: Set[str] = set()
        self._lock = threading.RLock()
        self._next_alert_id = 0
        self._last_alert_time: Dict[AlertType, datetime] = {}

    def generate_alert(
        self,
        alert_type: AlertType,
        severity: Severity,
        message: str,
        threshold: float,
        current_value: float,
        recommended_action: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> Optional[str]:
        """Generate alert with deduplication. Returns alert ID if created, None if deduplicated."""
        with self._lock:
            # Deduplication: don't create duplicate alerts within 60 seconds
            if alert_type in self._last_alert_time:
                time_since_last = (
                    datetime.utcnow() - self._last_alert_time[alert_type]
                ).total_seconds()
                if time_since_last < 60:
                    return None

            alert_id = f"alt_{self._next_alert_id:08d}"
            self._next_alert_id += 1

            alert = Alert(
                alert_id=alert_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                threshold=threshold,
                current_value=current_value,
                recommended_action=recommended_action,
                workflow_id=workflow_id,
            )

            self.alerts.append(alert)
            self.alert_history[alert_type] += 1
            self.active_alerts.add(alert_id)
            self._last_alert_time[alert_type] = datetime.utcnow()

            return alert_id

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        with self._lock:
            if alert_id in self.active_alerts:
                self.active_alerts.discard(alert_id)
                return True
            return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all currently active alerts."""
        with self._lock:
            return [a for a in self.alerts if a.alert_id in self.active_alerts]

    def get_alert_history(
        self, alert_type: Optional[AlertType] = None, limit: int = 1000
    ) -> List[Alert]:
        """Get alert history, optionally filtered by type."""
        with self._lock:
            alerts = list(self.alerts)
            if alert_type:
                alerts = [a for a in alerts if a.alert_type == alert_type]
            return alerts[-limit:]

    def get_alert_summary(self) -> Dict[str, int]:
        """Get count of alerts by type."""
        with self._lock:
            return dict(self.alert_history)


# ============================================================================
# Integrated Monitoring Manager
# ============================================================================


class MonitoringManager:
    """Integrated monitoring system combining all components."""

    def __init__(self, config: Optional[MonitoringConfig] = None):
        """Initialize monitoring manager."""
        self.config = config or MonitoringConfig()
        self.enabled = self.config.monitoring_enabled

        self.event_logger = EventLogger(self.config.event_buffer_size)
        self.trace_collector = TraceCollector()
        self.health_monitor = HealthMonitor(self.config)
        self.alert_manager = AlertManager(self.config)

        self.workflow_metrics: Dict[str, WorkflowMetrics] = {}
        self.phase_metrics: Dict[str, PhaseMetrics] = {}
        self._lock = threading.RLock()

    def start_workflow(self, workflow_id: str) -> WorkflowMetrics:
        """Record workflow start."""
        if not self.enabled:
            return WorkflowMetrics(workflow_id=workflow_id)

        with self._lock:
            metrics = WorkflowMetrics(workflow_id=workflow_id)
            self.workflow_metrics[workflow_id] = metrics

        self.event_logger.log_event(
            EventType.WORKFLOW_STARTED,
            severity=Severity.INFO,
            workflow_id=workflow_id,
            source="monitoring",
        )

        return metrics

    def end_workflow(
        self,
        workflow_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> Optional[WorkflowMetrics]:
        """Record workflow completion."""
        if not self.enabled:
            return None

        with self._lock:
            metrics = self.workflow_metrics.get(workflow_id)
            if not metrics:
                return None

            metrics.end_time = datetime.utcnow()
            metrics.total_duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()
            metrics.success = success
            metrics.error_message = error_message

        severity = Severity.INFO if success else Severity.ERROR
        self.event_logger.log_event(
            EventType.WORKFLOW_COMPLETED,
            severity=severity,
            workflow_id=workflow_id,
            source="monitoring",
            details={"duration": metrics.total_duration_seconds, "success": success},
        )

        return metrics

    def start_phase(self, workflow_id: str, phase_number: int) -> PhaseMetrics:
        """Record phase start."""
        if not self.enabled:
            return PhaseMetrics(phase_number=phase_number, workflow_id=workflow_id)

        phase_key = f"{workflow_id}:phase:{phase_number}"
        metrics = PhaseMetrics(phase_number=phase_number, workflow_id=workflow_id)

        with self._lock:
            self.phase_metrics[phase_key] = metrics

        self.event_logger.log_event(
            EventType.PHASE_STARTED,
            severity=Severity.INFO,
            workflow_id=workflow_id,
            source="monitoring",
            details={"phase_number": phase_number},
        )

        return metrics

    def end_phase(
        self, workflow_id: str, phase_number: int, success: bool = True
    ) -> Optional[PhaseMetrics]:
        """Record phase completion."""
        if not self.enabled:
            return None

        phase_key = f"{workflow_id}:phase:{phase_number}"

        with self._lock:
            metrics = self.phase_metrics.get(phase_key)
            if not metrics:
                return None

            metrics.end_time = datetime.utcnow()
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()

        self.event_logger.log_event(
            EventType.PHASE_COMPLETED,
            severity=Severity.INFO if success else Severity.ERROR,
            workflow_id=workflow_id,
            source="monitoring",
            details={"phase_number": phase_number, "duration": metrics.duration_seconds},
        )

        return metrics

    def record_task_completion(
        self,
        workflow_id: str,
        task_id: str,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Record task completion."""
        if not self.enabled:
            return

        event_type = (
            EventType.TASK_COMPLETED if success else EventType.TASK_FAILED
        )
        severity = Severity.INFO if success else Severity.WARNING

        self.event_logger.log_event(
            event_type,
            severity=severity,
            workflow_id=workflow_id,
            task_id=task_id,
            source="monitoring",
            details={"error": error} if error else {},
        )

        with self._lock:
            for metrics in self.workflow_metrics.values():
                if metrics.workflow_id == workflow_id:
                    if success:
                        metrics.tasks_completed += 1
                    else:
                        metrics.tasks_failed += 1

    def get_workflow_metrics(self, workflow_id: str) -> Optional[WorkflowMetrics]:
        """Retrieve workflow metrics."""
        with self._lock:
            return self.workflow_metrics.get(workflow_id)

    def get_phase_metrics(
        self, workflow_id: str, phase_number: int
    ) -> Optional[PhaseMetrics]:
        """Retrieve phase metrics."""
        phase_key = f"{workflow_id}:phase:{phase_number}"
        with self._lock:
            return self.phase_metrics.get(phase_key)

    def export_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Export all metrics for a workflow as JSON-serializable dict."""
        with self._lock:
            workflow = self.workflow_metrics.get(workflow_id)
            if not workflow:
                return {}

            phases = [
                self.phase_metrics[k].to_dict()
                for k in self.phase_metrics
                if k.startswith(f"{workflow_id}:phase:")
            ]

        return {
            "workflow": workflow.to_dict(),
            "phases": phases,
            "events": [e.to_dict() for e in self.event_logger.get_events(workflow_id=workflow_id)],
        }

    def cleanup_old_data(self, older_than_seconds: int = 86400) -> Dict[str, int]:
        """Clean up old monitoring data. Returns counts of items removed."""
        removed = {
            "events": self.event_logger.clear_old_events(older_than_seconds),
            "traces": self.trace_collector.clear_old_traces(older_than_seconds),
        }

        with self._lock:
            cutoff = datetime.utcnow() - timedelta(seconds=older_than_seconds)
            old_workflows = [
                wid
                for wid, metrics in self.workflow_metrics.items()
                if metrics.start_time < cutoff
            ]
            for wid in old_workflows:
                del self.workflow_metrics[wid]
            removed["workflows"] = len(old_workflows)

        return removed
