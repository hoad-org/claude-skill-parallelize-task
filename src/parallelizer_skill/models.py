"""Core models for task orchestration."""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DependencyType(str, Enum):
    """Types of task dependencies."""

    HARD = "hard"  # Must complete before dependent starts
    SOFT = "soft"  # Preferred but not required
    DATA = "data"  # Output of one feeds input of another


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    """Task execution priority."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Task(BaseModel):
    """Represents a single task in the workflow."""

    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Human-readable task name")
    description: Optional[str] = Field(None, description="Task description")
    estimated_duration: float = Field(1.0, description="Estimated duration in seconds")
    parallelizable: bool = Field(True, description="Can run in parallel with others")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="Task priority")
    resource_type: Optional[str] = Field(None, description="Type of resource needed (e.g., 'gpu', 'network')")
    max_concurrent: int = Field(1, description="Max instances of this task type that can run concurrently")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = False


class TaskDependency(BaseModel):
    """Represents a dependency between two tasks."""

    source_task_id: str = Field(..., description="ID of the task that must complete")
    target_task_id: str = Field(..., description="ID of the task that depends on source")
    dependency_type: DependencyType = Field(DependencyType.HARD, description="Type of dependency")
    condition: Optional[str] = Field(None, description="Optional condition for soft dependencies")

    class Config:
        use_enum_values = False


class TaskGroup(BaseModel):
    """A group of tasks that can run in parallel."""

    id: str = Field(..., description="Unique group identifier")
    tasks: List[str] = Field(..., description="Task IDs in this group")
    sequential_order: Optional[List[str]] = Field(None, description="If specified, tasks run in this order")
    estimated_duration: float = Field(..., description="Estimated time for group completion")
    can_parallelize: bool = Field(True, description="Whether this group can be parallelized")

    class Config:
        use_enum_values = False


class ExecutionPhase(BaseModel):
    """A phase of execution containing groups of tasks."""

    phase_number: int = Field(..., description="Phase number (starting at 1)")
    task_groups: List[TaskGroup] = Field(..., description="Task groups in this phase")
    is_parallel: bool = Field(..., description="Whether groups in this phase run in parallel")
    estimated_duration: float = Field(..., description="Estimated time for entire phase")
    sync_point_required: bool = Field(True, description="Whether to sync before next phase")

    class Config:
        use_enum_values = False


class ExecutionPlan(BaseModel):
    """Complete execution plan for a workflow."""

    id: str = Field(..., description="Plan identifier")
    total_tasks: int = Field(..., description="Total number of tasks")
    serial_duration: float = Field(..., description="Estimated duration if all tasks run serially")
    parallel_duration: float = Field(..., description="Estimated duration with optimal parallelization")
    efficiency_gain: float = Field(..., description="Percentage improvement from parallelization")
    phases: List[ExecutionPhase] = Field(..., description="Execution phases")
    critical_path: List[str] = Field(..., description="Task IDs on the critical path")
    parallelizable_groups: Dict[str, List[str]] = Field(
        default_factory=dict, description="Groups of parallelizable tasks"
    )
    resource_conflicts: List[str] = Field(default_factory=list, description="Identified resource conflicts")
    safety_issues: List[str] = Field(default_factory=list, description="Safety warnings/issues")
    optimization_notes: List[str] = Field(default_factory=list, description="Notes on optimization strategy")

    class Config:
        use_enum_values = False


class ExecutionStatus(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    RECOVERED = "recovered"


class WorkflowAnalysis(BaseModel):
    """Analysis of a workflow's parallelization potential."""

    analysis_id: str = Field(..., description="Unique analysis identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    total_tasks: int = Field(..., description="Total number of tasks in workflow")
    total_dependencies: int = Field(..., description="Total number of dependencies")
    complexity_scores: Dict[str, float] = Field(..., description="Complexity scores per task (0-100)")
    feasibility_ratings: Dict[str, str] = Field(..., description="Feasibility ratings per task")
    critical_path: List[str] = Field(..., description="Task IDs on critical path")
    critical_path_duration: float = Field(..., description="Estimated critical path duration")
    total_serial_duration: float = Field(..., description="Total duration if all tasks run serially")
    parallelizable_tasks: List[str] = Field(default_factory=list, description="Tasks that can be parallelized")
    sequential_bottlenecks: List[str] = Field(default_factory=list, description="Tasks creating sequential bottlenecks")
    resource_conflicts: List[str] = Field(default_factory=list, description="Identified resource conflicts")
    warnings: List[str] = Field(default_factory=list, description="Analysis warnings")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When analysis was performed")

    class Config:
        use_enum_values = False


class ExecutionResult(BaseModel):
    """Result of workflow execution."""

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow being executed")
    status: ExecutionStatus = Field(..., description="Execution status")
    start_time: datetime = Field(..., description="When execution started")
    end_time: Optional[datetime] = Field(None, description="When execution completed")
    duration_seconds: float = Field(0.0, description="Total execution duration")
    tasks_completed: int = Field(0, description="Number of completed tasks")
    tasks_failed: int = Field(0, description="Number of failed tasks")
    tasks_skipped: int = Field(0, description="Number of skipped tasks")
    phases_executed: int = Field(0, description="Number of execution phases completed")
    total_phases: int = Field(0, description="Total number of phases in plan")
    efficiency_achieved: float = Field(0.0, description="Actual efficiency gain achieved (0-100)")
    recovery_events: int = Field(0, description="Number of recovery events during execution")
    escalation_events: int = Field(0, description="Number of escalation events")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Execution metrics")

    class Config:
        use_enum_values = False
