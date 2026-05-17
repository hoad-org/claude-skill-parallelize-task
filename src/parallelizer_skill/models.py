"""Core models for task orchestration."""

from enum import Enum
from typing import Optional, List, Dict, Any
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
