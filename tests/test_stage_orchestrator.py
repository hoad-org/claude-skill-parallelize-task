"""Unit tests for stage orchestration (GAP 3)."""

import pytest
from parallelizer_skill.stage_orchestrator import StageOrchestrator, Stage, StageTask, GatePolicy
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestGatePolicy:
    """Test gate policy enum."""

    def test_gate_policy_all_pass(self):
        """Test ALL_PASS policy value."""
        assert GatePolicy.ALL_PASS.value == "all_pass"

    def test_gate_policy_all_complete(self):
        """Test ALL_COMPLETE policy value."""
        assert GatePolicy.ALL_COMPLETE.value == "all_complete"

    def test_gate_policy_majority(self):
        """Test MAJORITY policy value."""
        assert GatePolicy.MAJORITY.value == "majority"


@pytest.mark.unit
class TestStageTask:
    """Test stage task dataclass."""

    def test_task_creation(self):
        """Test creating a stage task."""
        task = StageTask(task_id="task_1", status="pending")
        assert task.task_id == "task_1"
        assert task.status == "pending"
        assert task.agent_id is None
        assert task.error is None

    def test_task_with_agent(self):
        """Test task with agent assignment."""
        task = StageTask(task_id="task_1", agent_id="agent_1")
        assert task.agent_id == "agent_1"

    def test_task_with_error(self):
        """Test task with error message."""
        task = StageTask(task_id="task_1", error="Connection timeout")
        assert task.error == "Connection timeout"


@pytest.mark.unit
class TestStage:
    """Test stage dataclass."""

    def test_stage_creation(self):
        """Test creating a stage."""
        stage = Stage(stage_number=1, name="Phase 1")
        assert stage.stage_number == 1
        assert stage.name == "Phase 1"
        assert stage.gate_policy == GatePolicy.ALL_PASS
        assert len(stage.tasks) == 0

    def test_stage_with_tasks(self):
        """Test creating stage with tasks."""
        tasks = [StageTask(task_id=f"task_{i}") for i in range(3)]
        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks)
        assert len(stage.tasks) == 3

    def test_stage_is_complete_empty(self):
        """Test is_complete on empty stage."""
        stage = Stage(stage_number=1, name="Phase 1")
        assert stage.is_complete()

    def test_stage_is_complete_all_done(self):
        """Test is_complete when all tasks finished."""
        tasks = [
            StageTask(task_id="task_1", status="complete"),
            StageTask(task_id="task_2", status="failed"),
        ]
        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks)
        assert stage.is_complete()

    def test_stage_is_complete_pending(self):
        """Test is_complete with pending tasks."""
        tasks = [
            StageTask(task_id="task_1", status="complete"),
            StageTask(task_id="task_2", status="pending"),
        ]
        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks)
        assert not stage.is_complete()

    def test_stage_is_passed_all_pass_success(self):
        """Test is_passed with ALL_PASS policy when all complete."""
        tasks = [
            StageTask(task_id="task_1", status="complete"),
            StageTask(task_id="task_2", status="complete"),
        ]
        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks, gate_policy=GatePolicy.ALL_PASS)
        assert stage.is_passed()

    def test_stage_is_passed_all_pass_failure(self):
        """Test is_passed with ALL_PASS policy when any fails."""
        tasks = [
            StageTask(task_id="task_1", status="complete"),
            StageTask(task_id="task_2", status="failed"),
        ]
        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks, gate_policy=GatePolicy.ALL_PASS)
        assert not stage.is_passed()

    def test_stage_is_passed_all_complete(self):
        """Test is_passed with ALL_COMPLETE policy."""
        tasks = [
            StageTask(task_id="task_1", status="complete"),
            StageTask(task_id="task_2", status="failed"),
        ]
        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks, gate_policy=GatePolicy.ALL_COMPLETE)
        assert stage.is_passed()

    def test_stage_is_passed_majority_success(self):
        """Test is_passed with MAJORITY policy success."""
        tasks = [StageTask(task_id=f"task_{i}", status="complete") for i in range(8)]
        tasks.append(StageTask(task_id="task_8", status="failed"))
        tasks.append(StageTask(task_id="task_9", status="failed"))

        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks, gate_policy=GatePolicy.MAJORITY)
        assert stage.is_passed()

    def test_stage_is_passed_majority_failure(self):
        """Test is_passed with MAJORITY policy failure."""
        tasks = [StageTask(task_id=f"task_{i}", status="complete") for i in range(7)]
        tasks.extend(
            [
                StageTask(task_id="task_7", status="failed"),
                StageTask(task_id="task_8", status="failed"),
                StageTask(task_id="task_9", status="failed"),
            ]
        )

        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks, gate_policy=GatePolicy.MAJORITY)
        assert not stage.is_passed()

    def test_stage_failed_tasks(self):
        """Test getting list of failed tasks."""
        tasks = [
            StageTask(task_id="task_1", status="complete"),
            StageTask(task_id="task_2", status="failed"),
            StageTask(task_id="task_3", status="failed"),
        ]
        stage = Stage(stage_number=1, name="Phase 1", tasks=tasks)

        failed = stage.failed_tasks()
        assert len(failed) == 2
        assert all(t.status == "failed" for t in failed)


@pytest.mark.unit
class TestStageOrchestrator:
    """Test stage orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create fresh orchestrator for each test."""
        reset_config()
        return StageOrchestrator()

    def test_add_stage(self, orchestrator):
        """Test adding a stage."""
        orchestrator.add_stage(1, "Phase 1", ["task_1", "task_2"])

        assert 1 in orchestrator.stages
        assert len(orchestrator.stages[1].tasks) == 2

    def test_add_stage_duplicate_raises_error(self, orchestrator):
        """Test adding duplicate stage raises error."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])

        with pytest.raises(ValueError):
            orchestrator.add_stage(1, "Phase 1 Duplicate", ["task_2"])

    def test_add_stage_maintains_order(self, orchestrator):
        """Test stages are ordered correctly."""
        orchestrator.add_stage(3, "Phase 3", ["task_3"])
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.add_stage(2, "Phase 2", ["task_2"])

        assert orchestrator.stage_order == [1, 2, 3]

    def test_start_stage_first_stage(self, orchestrator):
        """Test starting first stage."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.start_stage(1)

        assert orchestrator.current_stage == 1
        assert orchestrator.stages[1].started_at is not None

    def test_start_stage_requires_prior_completion(self, orchestrator):
        """Test starting stage fails if prior stage not complete."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.add_stage(2, "Phase 2", ["task_2"])

        orchestrator.start_stage(1)

        # Try to start stage 2 without completing stage 1
        with pytest.raises(RuntimeError):
            orchestrator.start_stage(2)

    def test_start_stage_requires_prior_pass(self, orchestrator):
        """Test starting stage fails if prior stage didn't pass."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"], GatePolicy.ALL_PASS)
        orchestrator.add_stage(2, "Phase 2", ["task_2"])

        orchestrator.start_stage(1)
        # Mark task as failed
        orchestrator.stages[1].tasks[0].status = "failed"

        with pytest.raises(RuntimeError):
            orchestrator.start_stage(2)

    def test_update_task_status(self, orchestrator):
        """Test updating task status."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.update_task_status(1, "task_1", "agent_1", "complete")

        task = orchestrator.stages[1].tasks[0]
        assert task.status == "complete"
        assert task.agent_id == "agent_1"

    def test_update_task_status_unknown_stage(self, orchestrator):
        """Test updating task in unknown stage raises error."""
        with pytest.raises(ValueError):
            orchestrator.update_task_status(99, "task_1", "agent_1", "complete")

    def test_update_task_status_unknown_task(self, orchestrator):
        """Test updating unknown task raises error."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])

        with pytest.raises(ValueError):
            orchestrator.update_task_status(1, "task_99", "agent_1", "complete")

    def test_update_task_status_with_error(self, orchestrator):
        """Test updating task status with error message."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.update_task_status(1, "task_1", "agent_1", "failed", "Timeout")

        task = orchestrator.stages[1].tasks[0]
        assert task.status == "failed"
        assert task.error == "Timeout"

    def test_check_stage_ready(self, orchestrator):
        """Test checking if stage is ready."""
        orchestrator.add_stage(1, "Phase 1", ["task_1", "task_2"])

        # Not ready yet
        assert not orchestrator.check_stage_ready(1)

        # Mark all tasks complete
        for task in orchestrator.stages[1].tasks:
            task.status = "complete"

        assert orchestrator.check_stage_ready(1)

    def test_check_stage_ready_unknown_stage(self, orchestrator):
        """Test checking unknown stage returns false."""
        assert not orchestrator.check_stage_ready(99)

    def test_check_stage_passed(self, orchestrator):
        """Test checking if stage passed gate."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"], GatePolicy.ALL_PASS)

        # Not passed yet
        assert not orchestrator.check_stage_passed(1)

        # Mark task complete
        orchestrator.stages[1].tasks[0].status = "complete"

        assert orchestrator.check_stage_passed(1)

    def test_check_stage_passed_unknown_stage(self, orchestrator):
        """Test checking unknown stage returns false."""
        assert not orchestrator.check_stage_passed(99)

    def test_complete_stage(self, orchestrator):
        """Test completing a stage."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.stages[1].tasks[0].status = "complete"

        orchestrator.complete_stage(1)

        assert orchestrator.stages[1].completed_at is not None

    def test_complete_stage_not_all_tasks_complete(self, orchestrator):
        """Test completing stage fails if not all tasks complete."""
        orchestrator.add_stage(1, "Phase 1", ["task_1", "task_2"])
        orchestrator.stages[1].tasks[0].status = "complete"

        with pytest.raises(RuntimeError):
            orchestrator.complete_stage(1)

    def test_get_next_stage(self, orchestrator):
        """Test getting next stage."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.add_stage(2, "Phase 2", ["task_2"])
        orchestrator.add_stage(3, "Phase 3", ["task_3"])

        orchestrator.start_stage(1)
        assert orchestrator.get_next_stage() == 2

    def test_get_next_stage_no_more(self, orchestrator):
        """Test get_next_stage returns None when all stages done."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.start_stage(1)
        orchestrator.current_stage = 1

        assert orchestrator.get_next_stage() is None

    def test_get_stage_status(self, orchestrator):
        """Test getting stage status."""
        orchestrator.add_stage(1, "Phase 1", ["task_1", "task_2"])
        orchestrator.stages[1].tasks[0].status = "complete"

        status = orchestrator.get_stage_status(1)

        assert status["number"] == 1
        assert status["name"] == "Phase 1"
        assert status["tasks_total"] == 2
        assert status["tasks_complete"] == 1
        assert status["tasks_failed"] == 0

    def test_get_stage_status_unknown_stage(self, orchestrator):
        """Test getting unknown stage status raises error."""
        with pytest.raises(ValueError):
            orchestrator.get_stage_status(99)

    def test_get_all_status(self, orchestrator):
        """Test getting all status."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.add_stage(2, "Phase 2", ["task_2"])
        orchestrator.start_stage(1)

        status = orchestrator.get_all_status()

        assert status["current_stage"] == 1
        assert status["total_stages"] == 2
        assert 1 in status["stages"]
        assert 2 in status["stages"]

    def test_reset_clears_all(self, orchestrator):
        """Test reset clears all stages."""
        orchestrator.add_stage(1, "Phase 1", ["task_1"])
        orchestrator.add_stage(2, "Phase 2", ["task_2"])
        orchestrator.start_stage(1)

        orchestrator.reset()

        assert len(orchestrator.stages) == 0
        assert orchestrator.stage_order == []
        assert orchestrator.current_stage == -1

    def test_multi_stage_workflow(self, orchestrator):
        """Test complete multi-stage workflow."""
        # Setup 3 stages
        orchestrator.add_stage(1, "Analysis", ["analyze"], GatePolicy.ALL_PASS)
        orchestrator.add_stage(2, "Implementation", ["impl"], GatePolicy.ALL_PASS)
        orchestrator.add_stage(3, "Testing", ["test"], GatePolicy.ALL_PASS)

        # Start and complete stage 1
        orchestrator.start_stage(1)
        assert orchestrator.current_stage == 1

        orchestrator.update_task_status(1, "analyze", "agent_1", "complete")
        orchestrator.complete_stage(1)

        # Move to stage 2
        next_stage = orchestrator.get_next_stage()
        assert next_stage == 2
        orchestrator.start_stage(2)
        assert orchestrator.current_stage == 2

        orchestrator.update_task_status(2, "impl", "agent_2", "complete")
        orchestrator.complete_stage(2)

        # Move to stage 3
        next_stage = orchestrator.get_next_stage()
        assert next_stage == 3
        orchestrator.start_stage(3)
        assert orchestrator.current_stage == 3
