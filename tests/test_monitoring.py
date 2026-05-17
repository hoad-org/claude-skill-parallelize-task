"""Unit tests for monitoring and observability module (Phase 5)."""

import pytest
import time
import json
from datetime import datetime, timedelta
from parallelizer_skill.monitoring import (
    EventType,
    Severity,
    AlertType,
    HealthStatus,
    MonitoringConfig,
    WorkflowMetrics,
    PhaseMetrics,
    WorkflowEvent,
    ExecutionTrace,
    HealthCheck,
    Alert,
    EventLogger,
    TraceCollector,
    HealthMonitor,
    AlertManager,
    MonitoringManager,
)


# ============================================================================
# Test Configuration
# ============================================================================


@pytest.mark.unit
class TestMonitoringConfig:
    """Test monitoring configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MonitoringConfig()
        assert config.monitoring_enabled is True
        assert config.event_buffer_size == 10000
        assert config.trace_enabled is True
        assert config.health_check_interval == 300
        assert config.alert_enabled is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = MonitoringConfig(
            monitoring_enabled=False,
            event_buffer_size=5000,
            health_check_interval=600,
        )
        assert config.monitoring_enabled is False
        assert config.event_buffer_size == 5000
        assert config.health_check_interval == 600


# ============================================================================
# Test Metrics Data Models
# ============================================================================


@pytest.mark.unit
class TestWorkflowMetrics:
    """Test workflow metrics tracking."""

    def test_workflow_metrics_creation(self):
        """Test creating workflow metrics."""
        metrics = WorkflowMetrics(workflow_id="wf_001")
        assert metrics.workflow_id == "wf_001"
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.success is True

    def test_workflow_metrics_to_dict(self):
        """Test serializing workflow metrics."""
        metrics = WorkflowMetrics(
            workflow_id="wf_001",
            tasks_completed=5,
            tasks_failed=1,
            parallelization_speedup=2.5,
        )
        data = metrics.to_dict()

        assert data["workflow_id"] == "wf_001"
        assert data["tasks_completed"] == 5
        assert data["tasks_failed"] == 1
        assert data["parallelization_speedup"] == 2.5
        assert "start_time" in data
        assert isinstance(data["start_time"], str)

    def test_phase_metrics_creation(self):
        """Test creating phase metrics."""
        metrics = PhaseMetrics(phase_number=1, workflow_id="wf_001", task_count=10)
        assert metrics.phase_number == 1
        assert metrics.task_count == 10
        assert metrics.success_rate == 1.0

    def test_phase_metrics_to_dict(self):
        """Test serializing phase metrics."""
        metrics = PhaseMetrics(
            phase_number=2, workflow_id="wf_001", task_count=10, tasks_completed=9
        )
        data = metrics.to_dict()

        assert data["phase_number"] == 2
        assert data["task_count"] == 10
        assert data["tasks_completed"] == 9


# ============================================================================
# Test Event Logging
# ============================================================================


@pytest.mark.unit
class TestEventLogger:
    """Test event logging functionality."""

    def test_event_logger_creation(self):
        """Test creating event logger."""
        logger = EventLogger(buffer_size=1000)
        assert logger.buffer_size == 1000
        assert len(logger.events) == 0

    def test_log_event_basic(self):
        """Test logging a basic event."""
        logger = EventLogger()
        event_id = logger.log_event(
            EventType.WORKFLOW_STARTED,
            severity=Severity.INFO,
            workflow_id="wf_001",
        )

        assert event_id.startswith("evt_")
        assert len(logger.events) == 1

    def test_log_event_with_details(self):
        """Test logging event with details."""
        logger = EventLogger()
        event_id = logger.log_event(
            EventType.TASK_COMPLETED,
            severity=Severity.INFO,
            workflow_id="wf_001",
            task_id="task_001",
            source="test_source",
            details={"duration": 1.5, "success": True},
            correlation_id="corr_001",
        )

        events = logger.get_events()
        assert len(events) == 1
        event = events[0]
        assert event.event_id == event_id
        assert event.event_type == EventType.TASK_COMPLETED
        assert event.workflow_id == "wf_001"
        assert event.task_id == "task_001"
        assert event.details["duration"] == 1.5

    def test_event_filtering_by_type(self):
        """Test filtering events by type."""
        logger = EventLogger()
        logger.log_event(EventType.WORKFLOW_STARTED, workflow_id="wf_001")
        logger.log_event(EventType.TASK_STARTED, workflow_id="wf_001")
        logger.log_event(EventType.TASK_COMPLETED, workflow_id="wf_001")

        started_events = logger.get_events(event_type=EventType.TASK_STARTED)
        assert len(started_events) == 1
        assert started_events[0].event_type == EventType.TASK_STARTED

    def test_event_filtering_by_severity(self):
        """Test filtering events by severity."""
        logger = EventLogger()
        logger.log_event(EventType.WORKFLOW_STARTED, severity=Severity.INFO)
        logger.log_event(EventType.TASK_FAILED, severity=Severity.ERROR)

        errors = logger.get_events(severity=Severity.ERROR)
        assert len(errors) == 1
        assert errors[0].event_type == EventType.TASK_FAILED

    def test_event_filtering_by_workflow(self):
        """Test filtering events by workflow ID."""
        logger = EventLogger()
        logger.log_event(EventType.WORKFLOW_STARTED, workflow_id="wf_001")
        logger.log_event(EventType.TASK_STARTED, workflow_id="wf_002")

        wf1_events = logger.get_events(workflow_id="wf_001")
        assert len(wf1_events) == 1
        assert wf1_events[0].workflow_id == "wf_001"

    def test_event_summary(self):
        """Test event count summary."""
        logger = EventLogger()
        logger.log_event(EventType.WORKFLOW_STARTED)
        logger.log_event(EventType.TASK_STARTED)
        logger.log_event(EventType.TASK_STARTED)
        logger.log_event(EventType.TASK_COMPLETED)

        summary = logger.get_event_summary()
        assert summary[EventType.WORKFLOW_STARTED] == 1
        assert summary[EventType.TASK_STARTED] == 2
        assert summary[EventType.TASK_COMPLETED] == 1

    def test_clear_old_events(self):
        """Test clearing old events."""
        logger = EventLogger()
        logger.log_event(EventType.WORKFLOW_STARTED)

        # Manually set old timestamp
        old_event = list(logger.events)[0]
        old_event.timestamp = datetime.utcnow() - timedelta(days=2)

        # Clear events older than 1 day
        removed = logger.clear_old_events(older_than_seconds=86400)
        assert removed == 1
        assert len(logger.events) == 0

    def test_buffer_overflow(self):
        """Test buffer overflow behavior."""
        logger = EventLogger(buffer_size=10)

        for i in range(20):
            logger.log_event(EventType.WORKFLOW_STARTED)

        assert len(logger.events) == 10

    def test_event_to_dict(self):
        """Test event serialization."""
        logger = EventLogger()
        logger.log_event(
            EventType.WORKFLOW_STARTED,
            severity=Severity.INFO,
            workflow_id="wf_001",
            details={"key": "value"},
        )

        event = list(logger.events)[0]
        data = event.to_dict()

        assert data["event_type"] == "workflow_started"
        assert data["severity"] == "info"
        assert data["workflow_id"] == "wf_001"
        assert data["details"]["key"] == "value"


# ============================================================================
# Test Execution Tracing
# ============================================================================


@pytest.mark.unit
class TestTraceCollector:
    """Test execution trace collection."""

    def test_trace_collector_creation(self):
        """Test creating trace collector."""
        collector = TraceCollector()
        assert len(collector.traces) == 0

    def test_start_trace(self):
        """Test starting a trace."""
        collector = TraceCollector()
        trace_id = collector.start_trace("operation_1")

        assert trace_id.startswith("tr_")
        assert trace_id in collector.traces
        trace = collector.traces[trace_id]
        assert trace.operation_name == "operation_1"
        assert trace.status == "pending"

    def test_trace_hierarchy(self):
        """Test trace parent-child relationships."""
        collector = TraceCollector()
        parent_id = collector.start_trace("parent_op")
        child1_id = collector.start_trace("child_op_1", parent_trace_id=parent_id)
        child2_id = collector.start_trace("child_op_2", parent_trace_id=parent_id)

        parent = collector.traces[parent_id]
        assert len(parent.children_trace_ids) == 2
        assert child1_id in parent.children_trace_ids
        assert child2_id in parent.children_trace_ids

    def test_end_trace(self):
        """Test ending a trace."""
        collector = TraceCollector()
        trace_id = collector.start_trace("operation_1")

        time.sleep(0.01)  # Small delay to measure duration
        collector.end_trace(trace_id, status="completed")

        trace = collector.traces[trace_id]
        assert trace.status == "completed"
        assert trace.end_time is not None
        assert trace.duration_seconds > 0

    def test_decision_points(self):
        """Test recording decision points."""
        collector = TraceCollector()
        trace_id = collector.start_trace("operation_1")

        collector.add_decision_point(trace_id, "choose_model", "haiku")
        collector.add_decision_point(trace_id, "escalate", "yes")

        trace = collector.traces[trace_id]
        assert len(trace.decision_points) == 2
        assert trace.decision_points[0]["decision"] == "choose_model"
        assert trace.decision_points[1]["outcome"] == "yes"

    def test_execution_path(self):
        """Test recording execution path."""
        collector = TraceCollector()
        trace_id = collector.start_trace("operation_1")

        collector.add_execution_step(trace_id, "step_1_analyze")
        collector.add_execution_step(trace_id, "step_2_plan")
        collector.add_execution_step(trace_id, "step_3_execute")

        trace = collector.traces[trace_id]
        assert len(trace.execution_path) == 3
        assert trace.execution_path[0] == "step_1_analyze"

    def test_trace_timeline(self):
        """Test getting trace timeline."""
        collector = TraceCollector()
        parent_id = collector.start_trace("parent")
        child_id = collector.start_trace("child", parent_trace_id=parent_id)

        timeline = collector.get_trace_timeline(parent_id)
        assert len(timeline) == 2
        assert timeline[0].operation_name == "parent"
        assert timeline[1].operation_name == "child"

    def test_get_trace(self):
        """Test retrieving a trace."""
        collector = TraceCollector()
        trace_id = collector.start_trace("operation_1")

        trace = collector.get_trace(trace_id)
        assert trace is not None
        assert trace.operation_name == "operation_1"

    def test_clear_old_traces(self):
        """Test clearing old traces."""
        collector = TraceCollector()
        trace_id = collector.start_trace("operation_1")

        # Manually set old timestamp
        trace = collector.traces[trace_id]
        trace.start_time = datetime.utcnow() - timedelta(days=2)

        removed = collector.clear_old_traces(older_than_seconds=86400)
        assert removed == 1
        assert len(collector.traces) == 0


# ============================================================================
# Test Health Monitoring
# ============================================================================


@pytest.mark.unit
class TestHealthMonitor:
    """Test health monitoring functionality."""

    def test_health_monitor_creation(self):
        """Test creating health monitor."""
        config = MonitoringConfig()
        monitor = HealthMonitor(config)
        assert monitor.current_status == HealthStatus.HEALTHY

    def test_perform_health_check_healthy(self):
        """Test health check with healthy status."""
        config = MonitoringConfig()
        monitor = HealthMonitor(config)

        check = monitor.perform_check(
            cache_health=0.95,
            escalation_frequency=2,
            failure_rate=0.05,
            resource_available=True,
        )

        assert check.overall_status == HealthStatus.HEALTHY
        assert len(check.issues) == 0

    def test_perform_health_check_degraded(self):
        """Test health check with degraded status."""
        config = MonitoringConfig()
        monitor = HealthMonitor(config)

        check = monitor.perform_check(
            cache_health=0.5,  # Below threshold
            escalation_frequency=2,
            failure_rate=0.05,
            resource_available=True,
        )

        assert check.overall_status == HealthStatus.DEGRADED
        assert "cache_health_low" in check.issues

    def test_perform_health_check_unhealthy(self):
        """Test health check with unhealthy status."""
        config = MonitoringConfig()
        monitor = HealthMonitor(config)

        check = monitor.perform_check(
            cache_health=0.5,  # Below threshold
            escalation_frequency=10,  # Excessive
            failure_rate=0.3,  # High failure
            resource_available=False,
        )

        assert check.overall_status == HealthStatus.UNHEALTHY
        assert len(check.issues) >= 3

    def test_status_transitions(self):
        """Test status transition history."""
        config = MonitoringConfig()
        monitor = HealthMonitor(config)

        monitor.perform_check(
            cache_health=0.95,
            escalation_frequency=1,
            failure_rate=0.01,
            resource_available=True,
        )
        assert monitor.current_status == HealthStatus.HEALTHY

        monitor.perform_check(
            cache_health=0.5,
            escalation_frequency=2,
            failure_rate=0.05,
            resource_available=True,
        )
        assert monitor.current_status == HealthStatus.DEGRADED

        history = monitor.get_status_history()
        assert len(history) == 1
        assert history[0][0] == HealthStatus.HEALTHY
        assert history[0][1] == HealthStatus.DEGRADED

    def test_get_latest_check(self):
        """Test getting latest health check."""
        config = MonitoringConfig()
        monitor = HealthMonitor(config)

        assert monitor.get_latest_check() is None

        check1 = monitor.perform_check(0.9, 1, 0.01, True)
        assert monitor.get_latest_check() == check1

        check2 = monitor.perform_check(0.5, 2, 0.05, True)
        assert monitor.get_latest_check() == check2

    def test_health_check_to_dict(self):
        """Test health check serialization."""
        config = MonitoringConfig()
        monitor = HealthMonitor(config)

        check = monitor.perform_check(0.85, 3, 0.1, True)
        data = check.to_dict()

        assert data["cache_health"] == 0.85
        assert data["escalation_frequency"] == 3
        assert data["overall_status"] == "healthy"


# ============================================================================
# Test Alert Management
# ============================================================================


@pytest.mark.unit
class TestAlertManager:
    """Test alert management."""

    def test_alert_manager_creation(self):
        """Test creating alert manager."""
        config = MonitoringConfig()
        manager = AlertManager(config)
        assert len(manager.alerts) == 0
        assert len(manager.active_alerts) == 0

    def test_generate_alert(self):
        """Test generating an alert."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        alert_id = manager.generate_alert(
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            severity=Severity.WARNING,
            message="Performance degraded",
            threshold=1.5,
            current_value=2.1,
            recommended_action="Check cache",
            workflow_id="wf_001",
        )

        assert alert_id is not None
        assert alert_id in manager.active_alerts

    def test_alert_deduplication(self):
        """Test alert deduplication."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        alert_id_1 = manager.generate_alert(
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            severity=Severity.WARNING,
            message="Performance degraded",
            threshold=1.5,
            current_value=2.1,
        )

        # Try to create same alert immediately (should be deduplicated)
        alert_id_2 = manager.generate_alert(
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            severity=Severity.WARNING,
            message="Performance degraded",
            threshold=1.5,
            current_value=2.1,
        )

        assert alert_id_1 is not None
        assert alert_id_2 is None  # Deduplicated

    def test_resolve_alert(self):
        """Test resolving an alert."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        alert_id = manager.generate_alert(
            alert_type=AlertType.CACHE_THRASHING,
            severity=Severity.WARNING,
            message="Cache thrashing detected",
            threshold=0.7,
            current_value=0.5,
        )

        assert alert_id in manager.active_alerts
        assert manager.resolve_alert(alert_id)
        assert alert_id not in manager.active_alerts

    def test_get_active_alerts(self):
        """Test retrieving active alerts."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        manager.generate_alert(
            AlertType.PERFORMANCE_DEGRADATION, Severity.WARNING, "msg", 1.5, 2.1
        )
        manager.generate_alert(
            AlertType.HIGH_FAILURE_RATE, Severity.ERROR, "msg", 0.2, 0.4
        )

        active = manager.get_active_alerts()
        assert len(active) == 2

    def test_get_alert_history(self):
        """Test retrieving alert history."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        manager.generate_alert(
            AlertType.PERFORMANCE_DEGRADATION, Severity.WARNING, "msg", 1.5, 2.1
        )
        manager.generate_alert(
            AlertType.HIGH_FAILURE_RATE, Severity.ERROR, "msg", 0.2, 0.4
        )

        history = manager.get_alert_history()
        assert len(history) == 2

    def test_get_alert_history_by_type(self):
        """Test filtering alert history by type."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        manager.generate_alert(
            AlertType.PERFORMANCE_DEGRADATION, Severity.WARNING, "msg", 1.5, 2.1
        )
        manager.generate_alert(
            AlertType.PERFORMANCE_DEGRADATION, Severity.WARNING, "msg", 1.5, 2.1
        )
        time.sleep(0.1)
        manager.generate_alert(
            AlertType.HIGH_FAILURE_RATE, Severity.ERROR, "msg", 0.2, 0.4
        )

        perf_alerts = manager.get_alert_history(
            alert_type=AlertType.PERFORMANCE_DEGRADATION
        )
        assert len(perf_alerts) == 1

    def test_alert_summary(self):
        """Test alert count summary."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        manager.generate_alert(
            AlertType.PERFORMANCE_DEGRADATION, Severity.WARNING, "msg", 1.5, 2.1
        )
        manager.generate_alert(
            AlertType.HIGH_FAILURE_RATE, Severity.ERROR, "msg", 0.2, 0.4
        )
        manager.generate_alert(
            AlertType.PERFORMANCE_DEGRADATION, Severity.WARNING, "msg", 1.5, 2.1
        )

        summary = manager.get_alert_summary()
        assert summary[AlertType.PERFORMANCE_DEGRADATION] == 1
        assert summary[AlertType.HIGH_FAILURE_RATE] == 1

    def test_alert_to_dict(self):
        """Test alert serialization."""
        config = MonitoringConfig()
        manager = AlertManager(config)

        alert_id = manager.generate_alert(
            AlertType.PERFORMANCE_DEGRADATION,
            Severity.WARNING,
            "Perf degraded",
            1.5,
            2.1,
            "Optimize cache",
            "wf_001",
        )

        alerts = manager.get_alert_history()
        alert = alerts[0]
        data = alert.to_dict()

        assert data["alert_type"] == "performance_degradation"
        assert data["severity"] == "warning"
        assert data["message"] == "Perf degraded"
        assert data["workflow_id"] == "wf_001"


# ============================================================================
# Test Integrated Monitoring Manager
# ============================================================================


@pytest.mark.unit
class TestMonitoringManager:
    """Test integrated monitoring manager."""

    def test_monitoring_manager_creation(self):
        """Test creating monitoring manager."""
        config = MonitoringConfig()
        manager = MonitoringManager(config)
        assert manager.enabled is True

    def test_workflow_lifecycle(self):
        """Test complete workflow monitoring."""
        manager = MonitoringManager()

        # Start workflow
        metrics = manager.start_workflow("wf_001")
        assert metrics.workflow_id == "wf_001"
        assert metrics.success is True

        # Complete workflow
        end_metrics = manager.end_workflow("wf_001", success=True)
        assert end_metrics is not None
        assert end_metrics.success is True
        assert end_metrics.total_duration_seconds > 0

    def test_phase_lifecycle(self):
        """Test phase monitoring."""
        manager = MonitoringManager()

        manager.start_workflow("wf_001")
        phase_metrics = manager.start_phase("wf_001", 1)

        assert phase_metrics.phase_number == 1
        assert phase_metrics.workflow_id == "wf_001"

        end_phase = manager.end_phase("wf_001", 1)
        assert end_phase is not None
        assert end_phase.duration_seconds > 0

    def test_task_completion_tracking(self):
        """Test task completion recording."""
        manager = MonitoringManager()

        manager.start_workflow("wf_001")
        manager.record_task_completion("wf_001", "task_001", success=True)
        manager.record_task_completion("wf_001", "task_002", success=False, error="Failed")

        workflow = manager.get_workflow_metrics("wf_001")
        assert workflow.tasks_completed == 1
        assert workflow.tasks_failed == 1

    def test_disabled_monitoring(self):
        """Test behavior when monitoring is disabled."""
        config = MonitoringConfig(monitoring_enabled=False)
        manager = MonitoringManager(config)

        assert manager.enabled is False

        metrics = manager.start_workflow("wf_001")
        assert metrics is not None

    def test_export_metrics(self):
        """Test exporting metrics as JSON."""
        manager = MonitoringManager()

        manager.start_workflow("wf_001")
        manager.start_phase("wf_001", 1)
        manager.end_phase("wf_001", 1)
        manager.record_task_completion("wf_001", "task_001", success=True)
        manager.end_workflow("wf_001")

        export = manager.export_metrics("wf_001")

        assert "workflow" in export
        assert "phases" in export
        assert "events" in export
        assert export["workflow"]["workflow_id"] == "wf_001"

    def test_cleanup_old_data(self):
        """Test cleanup of old monitoring data."""
        manager = MonitoringManager()

        manager.start_workflow("wf_001")
        manager.end_workflow("wf_001")

        # Manually set old timestamps
        workflow = manager.workflow_metrics["wf_001"]
        workflow.start_time = datetime.utcnow() - timedelta(days=2)

        removed = manager.cleanup_old_data(older_than_seconds=86400)
        assert removed["workflows"] == 1
        assert "wf_001" not in manager.workflow_metrics

    def test_thread_safety(self):
        """Test thread safety of monitoring operations."""
        import threading

        manager = MonitoringManager()

        def log_events():
            for i in range(100):
                manager.event_logger.log_event(EventType.TASK_COMPLETED)

        def record_tasks():
            for i in range(100):
                manager.record_task_completion("wf_001", f"task_{i}", success=True)

        threads = [
            threading.Thread(target=log_events),
            threading.Thread(target=log_events),
            threading.Thread(target=record_tasks),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(manager.event_logger.events) > 0


# ============================================================================
# Test Coverage & Integration
# ============================================================================


@pytest.mark.unit
class TestMonitoringCoverage:
    """Test monitoring coverage and edge cases."""

    def test_get_nonexistent_workflow_metrics(self):
        """Test getting non-existent workflow metrics."""
        manager = MonitoringManager()
        metrics = manager.get_workflow_metrics("nonexistent")
        assert metrics is None

    def test_get_nonexistent_phase_metrics(self):
        """Test getting non-existent phase metrics."""
        manager = MonitoringManager()
        metrics = manager.get_phase_metrics("nonexistent", 1)
        assert metrics is None

    def test_end_nonexistent_workflow(self):
        """Test ending non-existent workflow."""
        manager = MonitoringManager()
        metrics = manager.end_workflow("nonexistent")
        assert metrics is None

    def test_get_trace_nonexistent(self):
        """Test getting non-existent trace."""
        collector = TraceCollector()
        trace = collector.get_trace("nonexistent")
        assert trace is None

    def test_event_logger_json_serialization(self):
        """Test event logger produces valid JSON."""
        logger = EventLogger()
        logger.log_event(
            EventType.WORKFLOW_STARTED,
            severity=Severity.INFO,
            workflow_id="wf_001",
            details={"nested": {"key": "value"}},
        )

        events = logger.get_events()
        data = [e.to_dict() for e in events]

        # Should be JSON serializable
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

    def test_monitoring_overhead(self):
        """Test that monitoring has minimal overhead when disabled."""
        config = MonitoringConfig(monitoring_enabled=False)
        manager = MonitoringManager(config)

        start = time.time()
        for i in range(1000):
            manager.start_workflow(f"wf_{i}")
            manager.record_task_completion(f"wf_{i}", f"task_{i}", success=True)
            manager.end_workflow(f"wf_{i}")
        duration = time.time() - start

        # Should be very fast when disabled
        assert duration < 1.0
