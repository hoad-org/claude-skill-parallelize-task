# Phase 5: Monitoring and Observability

Production-grade monitoring, observability, and alerting system for the parallelize-task skill. Real-time metrics, structured logging, execution tracing, health monitoring, and intelligent alerting.

## Overview

Phase 5 monitoring provides complete visibility into workflow execution through metrics collection, event logging, execution tracing, health monitoring, and alert generation. The system is designed for production operation with high-cardinality metrics and low-latency alerting.

### Monitoring Goals

- **Event Collection**: Capture all significant workflow events
- **Metrics Accuracy**: >99.9% metric accuracy
- **Alert Latency**: <1 second from event to alert
- **Data Retention**: 7-30 days configurable history
- **Observability**: Complete request tracing with decision points

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│         Monitoring & Observability System                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Event Logger (Structured Logging)                     │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  • 39 event types (workflow, phase, task, decision)    │  │
│  │  • 4 severity levels (INFO, WARNING, ERROR, CRITICAL)  │  │
│  │  • Circular buffer (10K events default)                │  │
│  │  • Filtering & correlation IDs                          │  │
│  └────────────────────────────────────────────────────────┘  │
│           ↓                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Trace Collector (Execution Tracing)                   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  • Distributed tracing (parent-child relationships)    │  │
│  │  • Decision point recording                             │  │
│  │  • Execution path tracking                              │  │
│  │  • Timeline reconstruction                              │  │
│  └────────────────────────────────────────────────────────┘  │
│           ↓                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Metrics Aggregation                                   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  • Workflow-level metrics                               │  │
│  │  • Phase-level metrics                                  │  │
│  │  • Task-level metrics                                   │  │
│  │  • Real-time aggregation                                │  │
│  └────────────────────────────────────────────────────────┘  │
│           ↓                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Health Monitor (Status Transitions)                   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  • Cache health scoring                                 │  │
│  │  • Escalation frequency tracking                        │  │
│  │  • Failure rate analysis                                │  │
│  │  • Resource availability                                │  │
│  │  • Status transitions: HEALTHY → DEGRADED → UNHEALTHY  │  │
│  └────────────────────────────────────────────────────────┘  │
│           ↓                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Alert Manager (Threshold-based Alerting)             │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  • 6 alert types with thresholds                        │  │
│  │  • Deduplication (60s cooldown)                         │  │
│  │  • Severity assignment (INFO, WARN, ERROR, CRITICAL)   │  │
│  │  • Recommended actions                                  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 1. Event Logging System

### 1.1 Event Types

Complete list of 39 trackable events:

**Workflow Events**:
- `WORKFLOW_STARTED` — Workflow execution begins
- `WORKFLOW_COMPLETED` — Workflow execution finished

**Phase Events**:
- `PHASE_STARTED` — Phase begins execution
- `PHASE_COMPLETED` — Phase finishes execution

**Task Events**:
- `TASK_STARTED` — Task execution begins
- `TASK_COMPLETED` — Task execution succeeds
- `TASK_FAILED` — Task execution fails

**Decision Events**:
- `DECISION_MADE` — Strategic decision created

**Cache Events**:
- `CACHE_HIT` — Cache lookup succeeds
- `CACHE_MISS` — Cache lookup fails

**System Events**:
- `ESCALATION_TRIGGERED` — Error escalation occurs
- `RECOVERY_ATTEMPTED` — Recovery process begins
- `RESOURCE_CONSTRAINT` — Resource limit encountered
- `PERFORMANCE_DEGRADATION` — Performance below baseline

### 1.2 Severity Levels

Four severity levels for event classification:

| Level | Usage | Examples |
|-------|-------|----------|
| INFO | Normal operations | Task started, Cache hit |
| WARNING | Degraded operation | Cache miss pattern, Escalation |
| ERROR | Failure with recovery | Task failed, Recovery attempted |
| CRITICAL | Complete failure | Workflow failed, Resource exhausted |

### 1.3 Event Logger Interface

```python
logger = EventLogger(buffer_size=10000)

# Log an event
event_id = logger.log_event(
    event_type=EventType.TASK_COMPLETED,
    severity=Severity.INFO,
    workflow_id="wf-001",
    task_id="task_1",
    source="executor",
    details={
        "duration_seconds": 2.5,
        "result": "success"
    },
    correlation_id="corr-123"
)

# Retrieve events with filtering
events = logger.get_events(
    event_type=EventType.TASK_FAILED,
    severity=Severity.ERROR,
    workflow_id="wf-001",
    limit=100
)

# Get event summary
summary = logger.get_event_summary()
# {EventType.TASK_COMPLETED: 120, EventType.TASK_FAILED: 3, ...}
```

### 1.4 Event Correlation

Track related events using correlation IDs:

```python
# Root event
root_event_id = logger.log_event(
    EventType.WORKFLOW_STARTED,
    workflow_id="wf-001"
)

# Correlated events
logger.log_event(
    EventType.PHASE_STARTED,
    workflow_id="wf-001",
    correlation_id=root_event_id
)

# Find all correlated events
correlated = logger.get_events(
    workflow_id="wf-001",
    limit=1000
)
```

## 2. Execution Tracing

### 2.1 Trace Collector

Distributed tracing with parent-child relationships:

```python
tracer = TraceCollector()

# Start root trace
root_trace_id = tracer.start_trace("analyze_workflow")

# Start child trace
analyze_trace = tracer.start_trace(
    "complexity_analysis",
    parent_trace_id=root_trace_id
)

# Record decision point
tracer.add_decision_point(
    analyze_trace,
    decision="parallelize_group_2",
    outcome="approved"
)

# Record execution step
tracer.add_execution_step(analyze_trace, "compute_critical_path")
tracer.add_execution_step(analyze_trace, "identify_bottlenecks")

# End trace
tracer.end_trace(analyze_trace, status="completed")
tracer.end_trace(root_trace_id, status="completed")

# Retrieve trace timeline
timeline = tracer.get_trace_timeline(root_trace_id)
# Returns: [root, child1, child2, ...] in execution order
```

### 2.2 Trace Structure

```python
@dataclass
class ExecutionTrace:
    trace_id: str                          # Unique identifier
    operation_name: str                    # Operation description
    start_time: datetime                   # Start timestamp
    end_time: Optional[datetime]           # End timestamp
    duration_seconds: float                # Computed duration
    status: str                            # pending, completed, failed
    parent_trace_id: Optional[str]         # Parent trace ID
    children_trace_ids: List[str]          # Child trace IDs
    decision_points: List[Dict]            # Decisions made
    execution_path: List[str]              # Steps executed
```

### 2.3 Trace Analysis

Analyze traces for performance bottlenecks:

```python
timeline = tracer.get_trace_timeline(root_trace_id)

# Find slowest operations
slowest = sorted(
    timeline,
    key=lambda t: t.duration_seconds,
    reverse=True
)[:5]

for trace in slowest:
    print(f"{trace.operation_name}: {trace.duration_seconds}s")
    
# Find decision points
for trace in timeline:
    if trace.decision_points:
        print(f"{trace.operation_name} decisions:")
        for decision in trace.decision_points:
            print(f"  - {decision['decision']}: {decision['outcome']}")
```

## 3. Metrics Collection

### 3.1 Workflow Metrics

High-level metrics for complete workflow execution:

```python
@dataclass
class WorkflowMetrics:
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_seconds: float
    
    # Execution stats
    phases_executed: int
    tasks_completed: int
    tasks_failed: int
    tasks_skipped: int
    
    # Efficiency metrics
    parallelization_speedup: float        # vs serial
    resource_utilization_percent: float   # CPU/memory
    cache_hit_rate: float                 # Cache performance
    
    # Reliability metrics
    escalations_count: int
    recovery_events: int
    success: bool
    error_message: Optional[str]
```

**Example**:
```python
metrics = {
    "workflow_id": "wf-001",
    "total_duration_seconds": 15.3,
    "phases_executed": 3,
    "tasks_completed": 10,
    "tasks_failed": 0,
    "parallelization_speedup": 4.2,
    "resource_utilization_percent": 65.0,
    "cache_hit_rate": 0.72,
    "escalations_count": 0,
    "recovery_events": 0,
    "success": True
}
```

### 3.2 Phase Metrics

Phase-level execution metrics:

```python
@dataclass
class PhaseMetrics:
    phase_number: int
    workflow_id: str
    duration_seconds: float
    task_count: int
    tasks_completed: int
    tasks_failed: int
    success_rate: float                   # 0-1
    is_critical_path: bool
    bottleneck_identified: Optional[str]
```

### 3.3 Metrics Aggregation

Real-time metrics aggregation:

```python
monitor = MonitoringManager(config=MonitoringConfig())

# Start tracking workflow
metrics = monitor.start_workflow("wf-001")

# Track phase progress
phase_metrics = monitor.start_phase("wf-001", phase_number=1)

# Record task completion
monitor.record_task_completion(
    workflow_id="wf-001",
    task_id="task_1",
    success=True
)

# End phase and workflow
monitor.end_phase("wf-001", phase_number=1, success=True)
final_metrics = monitor.end_workflow("wf-001", success=True)

# Export all metrics
export = monitor.export_metrics("wf-001")
# {
#   "workflow": {...},
#   "phases": [{...}, ...],
#   "events": [{...}, ...]
# }
```

## 4. Health Monitoring

### 4.1 Health Check System

Continuous health assessment with status transitions:

```python
health_monitor = HealthMonitor(config=MonitoringConfig())

# Perform health check
check = health_monitor.perform_check(
    cache_health=0.72,           # Cache hit rate
    escalation_frequency=2,      # Escalations per workflow
    failure_rate=0.05,           # Task failure rate
    resource_available=True      # Resource availability
)

# Check includes status determination
# HEALTHY: All metrics normal
# DEGRADED: 1-2 metrics concerning
# UNHEALTHY: 3+ metrics concerning

assert check.overall_status == HealthStatus.HEALTHY
```

### 4.2 Health Status Transitions

Track health status changes:

```python
# Health history
history = health_monitor.get_status_history(limit=100)
# [
#   (HEALTHY, DEGRADED, timestamp_1),
#   (DEGRADED, UNHEALTHY, timestamp_2),
#   (UNHEALTHY, DEGRADED, timestamp_3),
# ]

# Current status
current = health_monitor.current_status  # DEGRADED
```

### 4.3 Health Metrics

Individual health metrics:

| Metric | Threshold | Status If Below |
|--------|-----------|-----------------|
| Cache Health | 70% hit rate | Low |
| Escalation Freq | 5 per workflow | High |
| Failure Rate | 20% | High |
| Resource Available | True | False |

## 5. Alert Management

### 5.1 Alert Types

Six alert types with configurable thresholds:

| Type | Trigger | Severity |
|------|---------|----------|
| `PERFORMANCE_DEGRADATION` | 1.5x baseline execution time | WARNING |
| `HIGH_FAILURE_RATE` | >20% task failure rate | ERROR |
| `EXCESSIVE_ESCALATIONS` | >5 per workflow | WARNING |
| `CACHE_THRASHING` | <50% hit rate with high misses | WARNING |
| `RESOURCE_EXHAUSTION` | Memory or CPU limit reached | CRITICAL |
| `HEALTH_CHECK_FAILED` | System health UNHEALTHY | ERROR |

### 5.2 Alert Manager Interface

```python
alert_mgr = AlertManager(config=MonitoringConfig())

# Generate alert
alert_id = alert_mgr.generate_alert(
    alert_type=AlertType.PERFORMANCE_DEGRADATION,
    severity=Severity.WARNING,
    message="Execution 1.8x slower than baseline",
    threshold=1.5,
    current_value=1.8,
    recommended_action="Check resource utilization",
    workflow_id="wf-001"
)

# Get active alerts
active = alert_mgr.get_active_alerts()
# [Alert(...), Alert(...), ...]

# Resolve alert
resolved = alert_mgr.resolve_alert(alert_id)

# Get alert history
history = alert_mgr.get_alert_history(
    alert_type=AlertType.PERFORMANCE_DEGRADATION,
    limit=100
)

# Get summary
summary = alert_mgr.get_alert_summary()
# {
#   AlertType.PERFORMANCE_DEGRADATION: 12,
#   AlertType.HIGH_FAILURE_RATE: 3,
#   ...
# }
```

### 5.3 Alert Deduplication

Prevent alert spam with intelligent deduplication:

```python
# Alerts of same type within 60s are deduplicated
alert_id_1 = alert_mgr.generate_alert(
    alert_type=AlertType.PERFORMANCE_DEGRADATION,
    ...
)  # Returns "alt_00000001"

# Immediately generate same alert type
alert_id_2 = alert_mgr.generate_alert(
    alert_type=AlertType.PERFORMANCE_DEGRADATION,
    ...
)  # Returns None (deduplicated)

# After 60s, generate same alert type
time.sleep(61)
alert_id_3 = alert_mgr.generate_alert(
    alert_type=AlertType.PERFORMANCE_DEGRADATION,
    ...
)  # Returns "alt_00000002" (new alert)
```

## 6. Configuration Reference

### MonitoringConfig

```python
@dataclass
class MonitoringConfig:
    monitoring_enabled: bool = True
    event_buffer_size: int = 10000
    
    # Tracing
    trace_enabled: bool = True
    
    # Health monitoring
    health_check_interval: int = 300      # seconds
    
    # Alerting
    alert_enabled: bool = True
    
    # Thresholds
    cache_health_threshold: float = 0.7   # min hit rate
    escalation_frequency_threshold: int = 5
    failure_rate_threshold: float = 0.2   # 20%
    performance_degradation_threshold: float = 1.5
```

### Environment Variables

```bash
# Enable/disable
export PARALLELIZE_TASK_MONITORING_ENABLED=true
export PARALLELIZE_TASK_TRACE_ENABLED=true
export PARALLELIZE_TASK_ALERT_ENABLED=true

# Buffer sizes
export PARALLELIZE_TASK_EVENT_BUFFER_SIZE=10000

# Intervals
export PARALLELIZE_TASK_HEALTH_CHECK_INTERVAL=300

# Thresholds
export PARALLELIZE_TASK_CACHE_HEALTH_THRESHOLD=0.7
export PARALLELIZE_TASK_ESCALATION_FREQUENCY_THRESHOLD=5
export PARALLELIZE_TASK_FAILURE_RATE_THRESHOLD=0.2
export PARALLELIZE_TASK_PERFORMANCE_DEGRADATION_THRESHOLD=1.5
```

## 7. Integration Patterns

### 7.1 Workflow Monitoring

Monitor complete workflow execution:

```python
monitor = MonitoringManager()
orchestrator = WorkflowOrchestrator()

# Start monitoring
metrics = monitor.start_workflow("wf-001")

try:
    # Execute workflow
    result = orchestrator.execute_workflow(
        tasks=task_list,
        dependencies=dep_list
    )
    
    # Record phase execution
    for phase_num in range(len(result.phases)):
        phase_metrics = monitor.start_phase("wf-001", phase_num)
        # ... phase execution ...
        monitor.end_phase("wf-001", phase_num, success=True)
    
    # Record task completion
    for task_result in result.task_results:
        monitor.record_task_completion(
            workflow_id="wf-001",
            task_id=task_result.task_id,
            success=task_result.success
        )
    
    # End workflow monitoring
    final_metrics = monitor.end_workflow("wf-001", success=True)
    
except Exception as e:
    monitor.end_workflow("wf-001", success=False, 
                        error_message=str(e))
    raise
```

### 7.2 Health-Based Actions

Respond to health status changes:

```python
monitor = MonitoringManager()

def check_health():
    """Check health and take corrective actions."""
    latest_check = monitor.health_monitor.get_latest_check()
    
    if latest_check.overall_status == HealthStatus.UNHEALTHY:
        # Trigger recovery actions
        logger.critical("System unhealthy, initiating recovery")
        # - Reduce parallelization
        # - Clear cache
        # - Reduce batch sizes
    
    elif latest_check.overall_status == HealthStatus.DEGRADED:
        # Reduce performance
        logger.warning("System degraded, reducing load")
        # - Reduce max_workers
        # - Increase batch sizes
        # - Add delays between phases
    
    elif latest_check.overall_status == HealthStatus.HEALTHY:
        # Resume normal operation
        logger.info("System healthy, resuming normal operation")

# Run periodic health checks
health_check_thread = threading.Thread(
    target=lambda: [check_health() for _ in range(1000)],
    daemon=True
)
health_check_thread.start()
```

### 7.3 Metrics Export

Export metrics for external systems:

```python
monitor = MonitoringManager()

# Get all metrics
export = monitor.export_metrics("wf-001")

# Export to JSON
import json
json_export = json.dumps(export, default=str)

# Send to monitoring backend
requests.post(
    "https://monitoring.example.com/metrics",
    json=json_export,
    headers={"Authorization": "Bearer token"}
)

# Or save locally
with open(f"metrics_{workflow_id}.json", "w") as f:
    json.dump(export, f, indent=2, default=str)
```

## 8. Data Retention and Cleanup

### 8.1 Automatic Cleanup

Remove old monitoring data:

```python
monitor = MonitoringManager()

# Clean up data older than 24 hours
removed = monitor.cleanup_old_data(older_than_seconds=86400)

print(f"Removed {removed['events']} old events")
print(f"Removed {removed['traces']} old traces")
print(f"Removed {removed['workflows']} old workflows")
```

### 8.2 Retention Policy

Configure retention based on requirements:

| Data Type | Recommended | Min | Max |
|-----------|------------|-----|-----|
| Events | 7 days | 1 day | 30 days |
| Traces | 7 days | 1 day | 30 days |
| Workflows | 30 days | 7 days | 90 days |
| Metrics | 30 days | 7 days | 90 days |

## 9. Best Practices

1. **Enable Correlation IDs**
   - Use for distributed tracing
   - Trace complete request flow

2. **Monitor Health Continuously**
   - Check every 300 seconds
   - React to status transitions

3. **Set Appropriate Thresholds**
   - Cache health: 70%+
   - Failure rate: <20%
   - Escalations: <5 per workflow

4. **Clean Up Old Data**
   - Run cleanup daily
   - Retain 7-30 days based on volume

5. **Respond to Alerts**
   - Page on CRITICAL alerts
   - Investigate ERROR alerts
   - Log WARNING alerts

## 10. Troubleshooting

### Missing Events

**Symptom**: Events not logged

**Causes**:
- Monitoring disabled in config
- Event logger not initialized
- Buffer full and not flushed

**Solutions**:
1. Check `MonitoringConfig.monitoring_enabled = True`
2. Verify logger initialization
3. Increase event_buffer_size

### High Memory Usage

**Symptom**: Memory grows over time

**Causes**:
- Event buffer not cleaned
- Old traces not removed
- Metrics accumulating

**Solutions**:
1. Run `cleanup_old_data()` regularly
2. Reduce event_buffer_size
3. Decrease trace retention period

### Alert Spam

**Symptom**: Too many alerts of same type

**Causes**:
- Threshold too sensitive
- Deduplication cooldown too short
- Recurring issue

**Solutions**:
1. Increase threshold value
2. Increase deduplication cooldown
3. Fix underlying issue
