"""Unit tests for state persistence (Phase 2)."""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from parallelizer_skill.persistence import (
    PersistenceManager, PersistenceSnapshot, RecoveryPoint, PersistenceFormat
)
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestPersistenceSnapshot:
    """Test persistence snapshot."""

    def test_snapshot_creation(self):
        """Test creating a snapshot."""
        snapshot = PersistenceSnapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={"status": "running"},
        )

        assert snapshot.snapshot_id == "snap_1"
        assert snapshot.state_type == "orchestration"
        assert snapshot.data["status"] == "running"

    def test_snapshot_has_timestamp(self):
        """Test snapshot has timestamp."""
        snapshot = PersistenceSnapshot(
            snapshot_id="snap_1",
            state_type="agent",
            source_id="agent_1",
        )

        assert snapshot.timestamp is not None
        assert isinstance(snapshot.timestamp, datetime)


@pytest.mark.unit
class TestRecoveryPoint:
    """Test recovery point."""

    def test_recovery_point_creation(self):
        """Test creating a recovery point."""
        recovery = RecoveryPoint(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="in_progress",
        )

        assert recovery.recovery_id == "rec_1"
        assert recovery.stage_number == 1
        assert recovery.status == "in_progress"


@pytest.mark.unit
class TestPersistenceManager:
    """Test persistence manager."""

    @pytest.fixture
    def manager(self):
        """Create fresh manager with temp storage."""
        reset_config()
        temp_dir = tempfile.mkdtemp()
        return PersistenceManager(storage_path=temp_dir)

    def test_manager_creation(self, manager):
        """Test creating manager."""
        assert manager is not None
        assert manager.storage_path.exists()

    def test_save_snapshot(self, manager):
        """Test saving a snapshot."""
        snapshot = manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={"status": "running", "stage": 1},
        )

        assert snapshot.snapshot_id == "snap_1"
        assert snapshot.checksum is not None

    def test_load_snapshot(self, manager):
        """Test loading a snapshot."""
        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={"status": "running"},
        )

        loaded = manager.load_snapshot("snap_1")

        assert loaded is not None
        assert loaded.snapshot_id == "snap_1"
        assert loaded.data["status"] == "running"

    def test_load_unknown_snapshot(self, manager):
        """Test loading unknown snapshot."""
        loaded = manager.load_snapshot("unknown")
        assert loaded is None

    def test_save_recovery_point(self, manager):
        """Test saving a recovery point."""
        recovery = manager.save_recovery_point(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="in_progress",
        )

        assert recovery.recovery_id == "rec_1"
        assert recovery.stage_number == 1

    def test_load_recovery_point(self, manager):
        """Test loading a recovery point."""
        manager.save_recovery_point(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="in_progress",
        )

        loaded = manager.load_recovery_point("rec_1")

        assert loaded is not None
        assert loaded.recovery_id == "rec_1"
        assert loaded.stage_number == 1

    def test_load_unknown_recovery_point(self, manager):
        """Test loading unknown recovery point."""
        loaded = manager.load_recovery_point("unknown")
        assert loaded is None

    def test_get_latest_recovery_point(self, manager):
        """Test getting latest recovery point."""
        manager.save_recovery_point(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="pending",
        )

        manager.save_recovery_point(
            recovery_id="rec_2",
            stage_number=2,
            task_id="task_2",
            agent_id="agent_1",
            status="in_progress",
        )

        latest = manager.get_latest_recovery_point("agent_1")

        assert latest is not None
        assert latest.recovery_id == "rec_2"

    def test_get_snapshots_by_type(self, manager):
        """Test getting snapshots by type."""
        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={},
        )

        manager.save_snapshot(
            snapshot_id="snap_2",
            state_type="agent",
            source_id="agent_1",
            data={},
        )

        orch_snapshots = manager.get_snapshots_by_type("orchestration")

        assert len(orch_snapshots) == 1
        assert orch_snapshots[0].state_type == "orchestration"

    def test_get_snapshots_by_source(self, manager):
        """Test getting snapshots by source."""
        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={},
        )

        manager.save_snapshot(
            snapshot_id="snap_2",
            state_type="orchestration",
            source_id="orch_1",
            data={},
        )

        snapshots = manager.get_snapshots_by_source("orch_1")

        assert len(snapshots) == 2

    def test_delete_snapshot(self, manager):
        """Test deleting a snapshot."""
        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={},
        )

        success = manager.delete_snapshot("snap_1")

        assert success
        assert manager.load_snapshot("snap_1") is None

    def test_delete_unknown_snapshot(self, manager):
        """Test deleting unknown snapshot."""
        success = manager.delete_snapshot("unknown")
        assert not success

    def test_delete_recovery_point(self, manager):
        """Test deleting a recovery point."""
        manager.save_recovery_point(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="pending",
        )

        success = manager.delete_recovery_point("rec_1")

        assert success
        assert manager.load_recovery_point("rec_1") is None

    def test_cleanup_old_snapshots(self, manager):
        """Test cleaning up old snapshots."""
        # Save a snapshot with old timestamp
        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={},
        )

        # Manually set timestamp to 48 hours ago
        manager.snapshots["snap_1"].timestamp = datetime.utcnow() - timedelta(hours=48)

        cleaned = manager.cleanup_old_snapshots(max_age_hours=24)

        assert cleaned == 1
        assert "snap_1" not in manager.snapshots

    def test_cleanup_old_recovery_points(self, manager):
        """Test cleaning up old recovery points."""
        manager.save_recovery_point(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="pending",
        )

        # Manually set timestamp to 96 hours ago
        manager.recovery_points["rec_1"].timestamp = datetime.utcnow() - timedelta(hours=96)

        cleaned = manager.cleanup_old_recovery_points(max_age_hours=72)

        assert cleaned == 1
        assert "rec_1" not in manager.recovery_points

    def test_snapshot_checksum(self, manager):
        """Test snapshot checksum calculation."""
        data = {"key": "value", "number": 42}

        snapshot1 = manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="test",
            source_id="test_1",
            data=data,
        )

        snapshot2 = manager.save_snapshot(
            snapshot_id="snap_2",
            state_type="test",
            source_id="test_2",
            data=data,
        )

        # Same data should produce same checksum
        assert snapshot1.checksum == snapshot2.checksum

    def test_snapshot_different_checksum(self, manager):
        """Test different data produces different checksum."""
        snapshot1 = manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="test",
            source_id="test_1",
            data={"key": "value1"},
        )

        snapshot2 = manager.save_snapshot(
            snapshot_id="snap_2",
            state_type="test",
            source_id="test_2",
            data={"key": "value2"},
        )

        assert snapshot1.checksum != snapshot2.checksum

    def test_statistics(self, manager):
        """Test persistence statistics."""
        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="orchestration",
            source_id="orch_1",
            data={},
        )

        manager.save_recovery_point(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="pending",
        )

        stats = manager.get_statistics()

        assert stats["total_snapshots"] == 1
        assert stats["total_recovery_points"] == 1
        assert "orchestration" in stats["snapshot_types"]

    def test_reset(self, manager):
        """Test reset."""
        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="test",
            source_id="test_1",
            data={},
        )

        manager.save_recovery_point(
            recovery_id="rec_1",
            stage_number=1,
            task_id="task_1",
            agent_id="agent_1",
            status="pending",
        )

        manager.reset()

        assert len(manager.snapshots) == 0
        assert len(manager.recovery_points) == 0

    def test_persistence_format_json(self, manager):
        """Test JSON persistence format."""
        assert manager.format == PersistenceFormat.JSON

        manager.save_snapshot(
            snapshot_id="snap_1",
            state_type="test",
            source_id="test_1",
            data={"key": "value"},
        )

        # Check file exists with .json extension
        json_file = manager.storage_path / "snapshot_snap_1.json"
        assert json_file.exists()
