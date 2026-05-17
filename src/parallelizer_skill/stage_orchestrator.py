"""Stage orchestration and dependency enforcement (GAP 3)."""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from parallelizer_skill.config import get_config


class GatePolicy(str, Enum):
    """Stage gate policies."""
    ALL_PASS = "all_pass"  # All tasks must succeed
    ALL_COMPLETE = "all_complete"  # All tasks must finish (pass or fail)
    MAJORITY = "majority"  # 80% of tasks must pass


@dataclass
class StageTask:
    """Task in a stage."""
    task_id: str
    agent_id: Optional[str] = None
    status: str = "pending"  # pending, running, complete, failed
    error: Optional[str] = None


@dataclass
class Stage:
    """Execution stage with tasks and gate policy."""
    stage_number: int
    name: str
    tasks: List[StageTask] = field(default_factory=list)
    gate_policy: GatePolicy = GatePolicy.ALL_PASS
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def is_complete(self) -> bool:
        """Check if all tasks completed (pass or fail)."""
        return all(t.status in ("complete", "failed") for t in self.tasks)

    def is_passed(self) -> bool:
        """Check if stage passed gate policy."""
        if self.gate_policy == GatePolicy.ALL_PASS:
            return all(t.status == "complete" for t in self.tasks)
        elif self.gate_policy == GatePolicy.ALL_COMPLETE:
            return self.is_complete()
        elif self.gate_policy == GatePolicy.MAJORITY:
            completed = sum(1 for t in self.tasks if t.status == "complete")
            return completed >= (len(self.tasks) * 0.8)
        return False

    def failed_tasks(self) -> List[StageTask]:
        """Get list of failed tasks."""
        return [t for t in self.tasks if t.status == "failed"]


class StageOrchestrator:
    """Orchestrate stage execution with dependency enforcement (GAP 3)."""

    def __init__(self):
        """Initialize stage orchestrator."""
        self.config = get_config()
        self.stages: Dict[int, Stage] = {}
        self.stage_order: List[int] = []
        self.current_stage: int = -1

    def add_stage(self, stage_number: int, name: str, tasks: List[str], gate_policy: GatePolicy = GatePolicy.ALL_PASS) -> None:
        """Add a stage with tasks."""
        if stage_number in self.stages:
            raise ValueError(f"Stage {stage_number} already exists")

        stage = Stage(
            stage_number=stage_number,
            name=name,
            tasks=[StageTask(task_id=t) for t in tasks],
            gate_policy=gate_policy,
        )
        self.stages[stage_number] = stage
        self.stage_order.append(stage_number)
        self.stage_order.sort()

    def start_stage(self, stage_number: int) -> None:
        """Start a stage (check dependencies)."""
        if stage_number not in self.stages:
            raise ValueError(f"Unknown stage: {stage_number}")

        stage = self.stages[stage_number]

        # Check that all prior stages completed
        for prior_stage_num in self.stage_order:
            if prior_stage_num >= stage_number:
                break

            prior_stage = self.stages[prior_stage_num]

            if not prior_stage.is_complete():
                raise RuntimeError(
                    f"Cannot start stage {stage_number}: prior stage {prior_stage_num} not complete"
                )

            if not prior_stage.is_passed():
                raise RuntimeError(
                    f"Cannot start stage {stage_number}: prior stage {prior_stage_num} did not pass gate"
                )

        # Stage can start
        self.current_stage = stage_number
        stage.started_at = datetime.utcnow()

    def update_task_status(self, stage_number: int, task_id: str, agent_id: str, status: str, error: Optional[str] = None) -> None:
        """Update task status in a stage."""
        if stage_number not in self.stages:
            raise ValueError(f"Unknown stage: {stage_number}")

        stage = self.stages[stage_number]
        task = next((t for t in stage.tasks if t.task_id == task_id), None)

        if task is None:
            raise ValueError(f"Unknown task in stage {stage_number}: {task_id}")

        task.status = status
        task.agent_id = agent_id
        task.error = error

    def check_stage_ready(self, stage_number: int) -> bool:
        """Check if stage can proceed (all tasks complete)."""
        if stage_number not in self.stages:
            return False

        stage = self.stages[stage_number]
        return stage.is_complete()

    def check_stage_passed(self, stage_number: int) -> bool:
        """Check if stage passed its gate policy."""
        if stage_number not in self.stages:
            return False

        stage = self.stages[stage_number]
        return stage.is_passed()

    def complete_stage(self, stage_number: int) -> None:
        """Mark stage as complete."""
        if stage_number not in self.stages:
            raise ValueError(f"Unknown stage: {stage_number}")

        stage = self.stages[stage_number]
        if not stage.is_complete():
            raise RuntimeError(f"Stage {stage_number} not all tasks complete")

        stage.completed_at = datetime.utcnow()

    def get_next_stage(self) -> Optional[int]:
        """Get next stage to execute."""
        for stage_num in self.stage_order:
            if stage_num > self.current_stage:
                return stage_num
        return None

    def get_stage_status(self, stage_number: int) -> Dict:
        """Get status of a stage."""
        if stage_number not in self.stages:
            raise ValueError(f"Unknown stage: {stage_number}")

        stage = self.stages[stage_number]
        return {
            "number": stage.stage_number,
            "name": stage.name,
            "tasks_total": len(stage.tasks),
            "tasks_complete": sum(1 for t in stage.tasks if t.status == "complete"),
            "tasks_failed": len(stage.failed_tasks()),
            "status": "complete" if stage.is_complete() else "running",
            "passed": stage.is_passed(),
            "gate_policy": stage.gate_policy.value,
        }

    def get_all_status(self) -> Dict:
        """Get status of all stages."""
        return {
            "current_stage": self.current_stage,
            "total_stages": len(self.stages),
            "stages": {
                num: self.get_stage_status(num)
                for num in self.stage_order
            }
        }

    def reset(self) -> None:
        """Reset all stages (for testing)."""
        self.stages.clear()
        self.stage_order.clear()
        self.current_stage = -1
