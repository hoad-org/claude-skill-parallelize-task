"""State persistence and recovery (Phase 2, Resilience)."""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from parallelizer_skill.config import get_config


class PersistenceFormat(str, Enum):
    """Format for persisting state."""
    JSON = "json"
    JSONL = "jsonl"  # JSON Lines (one object per line)


@dataclass
class PersistenceSnapshot:
    """A snapshot of state at a point in time."""
    snapshot_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    state_type: str = ""  # "orchestration", "stage", "agent", etc.
    source_id: str = ""  # orchestration_id, stage_id, agent_id, etc.
    data: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None  # MD5 of data for integrity


@dataclass
class RecoveryPoint:
    """A point in execution that can be recovered from."""
    recovery_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stage_number: int = 0
    task_id: str = ""
    agent_id: str = ""
    status: str = ""  # "pending", "in_progress", "complete", "failed"
    context: Dict[str, Any] = field(default_factory=dict)


class PersistenceManager:
    """Manage state persistence and recovery (Phase 2)."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize persistence manager."""
        self.config = get_config()
        self.storage_path = Path(storage_path or f"./{self.config.orchestration.state_dir}")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.snapshots: Dict[str, PersistenceSnapshot] = {}
        self.recovery_points: Dict[str, RecoveryPoint] = {}
        self.format = PersistenceFormat.JSON

    def save_snapshot(
        self,
        snapshot_id: str,
        state_type: str,
        source_id: str,
        data: Dict[str, Any],
    ) -> PersistenceSnapshot:
        """Save a state snapshot."""
        import hashlib

        snapshot = PersistenceSnapshot(
            snapshot_id=snapshot_id,
            state_type=state_type,
            source_id=source_id,
            data=data,
        )

        # Calculate checksum
        data_str = json.dumps(data, sort_keys=True, default=str)
        snapshot.checksum = hashlib.md5(data_str.encode()).hexdigest()

        self.snapshots[snapshot_id] = snapshot

        # Persist to disk
        self._write_snapshot(snapshot)

        return snapshot

    def load_snapshot(self, snapshot_id: str) -> Optional[PersistenceSnapshot]:
        """Load a snapshot from storage."""
        if snapshot_id in self.snapshots:
            return self.snapshots[snapshot_id]

        # Try to load from disk
        snapshot = self._read_snapshot(snapshot_id)
        if snapshot:
            self.snapshots[snapshot_id] = snapshot
            return snapshot

        return None

    def save_recovery_point(
        self,
        recovery_id: str,
        stage_number: int,
        task_id: str,
        agent_id: str,
        status: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RecoveryPoint:
        """Save a recovery point."""
        recovery = RecoveryPoint(
            recovery_id=recovery_id,
            stage_number=stage_number,
            task_id=task_id,
            agent_id=agent_id,
            status=status,
            context=context or {},
        )

        self.recovery_points[recovery_id] = recovery
        self._write_recovery_point(recovery)

        return recovery

    def load_recovery_point(self, recovery_id: str) -> Optional[RecoveryPoint]:
        """Load a recovery point from storage."""
        if recovery_id in self.recovery_points:
            return self.recovery_points[recovery_id]

        recovery = self._read_recovery_point(recovery_id)
        if recovery:
            self.recovery_points[recovery_id] = recovery
            return recovery

        return None

    def get_latest_recovery_point(self, source_id: str) -> Optional[RecoveryPoint]:
        """Get the most recent recovery point for a source."""
        matching = [
            r for r in self.recovery_points.values()
            if r.agent_id == source_id or r.task_id == source_id
        ]

        if not matching:
            return None

        return max(matching, key=lambda r: r.timestamp)

    def get_snapshots_by_type(self, state_type: str) -> List[PersistenceSnapshot]:
        """Get all snapshots of a specific type."""
        return [s for s in self.snapshots.values() if s.state_type == state_type]

    def get_snapshots_by_source(self, source_id: str) -> List[PersistenceSnapshot]:
        """Get all snapshots for a specific source."""
        return [s for s in self.snapshots.values() if s.source_id == source_id]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        if snapshot_id not in self.snapshots:
            return False

        del self.snapshots[snapshot_id]
        self._delete_snapshot_file(snapshot_id)
        return True

    def delete_recovery_point(self, recovery_id: str) -> bool:
        """Delete a recovery point."""
        if recovery_id not in self.recovery_points:
            return False

        del self.recovery_points[recovery_id]
        self._delete_recovery_point_file(recovery_id)
        return True

    def cleanup_old_snapshots(self, max_age_hours: int = 24) -> int:
        """Delete snapshots older than specified age."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_snapshots = [
            sid for sid, s in self.snapshots.items()
            if s.timestamp < cutoff
        ]

        for snapshot_id in old_snapshots:
            self.delete_snapshot(snapshot_id)

        return len(old_snapshots)

    def cleanup_old_recovery_points(self, max_age_hours: int = 72) -> int:
        """Delete recovery points older than specified age."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_points = [
            rid for rid, r in self.recovery_points.items()
            if r.timestamp < cutoff
        ]

        for recovery_id in old_points:
            self.delete_recovery_point(recovery_id)

        return len(old_points)

    def _write_snapshot(self, snapshot: PersistenceSnapshot) -> None:
        """Write snapshot to disk."""
        file_path = self.storage_path / f"snapshot_{snapshot.snapshot_id}.{self.format.value}"
        data = {
            "snapshot_id": snapshot.snapshot_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "state_type": snapshot.state_type,
            "source_id": snapshot.source_id,
            "data": snapshot.data,
            "checksum": snapshot.checksum,
        }

        with open(file_path, "w") as f:
            json.dump(data, f)

    def _read_snapshot(self, snapshot_id: str) -> Optional[PersistenceSnapshot]:
        """Read snapshot from disk."""
        file_path = self.storage_path / f"snapshot_{snapshot_id}.{self.format.value}"

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = json.load(f)

        return PersistenceSnapshot(
            snapshot_id=data["snapshot_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            state_type=data["state_type"],
            source_id=data["source_id"],
            data=data["data"],
            checksum=data.get("checksum"),
        )

    def _write_recovery_point(self, recovery: RecoveryPoint) -> None:
        """Write recovery point to disk."""
        file_path = self.storage_path / f"recovery_{recovery.recovery_id}.{self.format.value}"
        data = {
            "recovery_id": recovery.recovery_id,
            "timestamp": recovery.timestamp.isoformat(),
            "stage_number": recovery.stage_number,
            "task_id": recovery.task_id,
            "agent_id": recovery.agent_id,
            "status": recovery.status,
            "context": recovery.context,
        }

        with open(file_path, "w") as f:
            json.dump(data, f)

    def _read_recovery_point(self, recovery_id: str) -> Optional[RecoveryPoint]:
        """Read recovery point from disk."""
        file_path = self.storage_path / f"recovery_{recovery_id}.{self.format.value}"

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = json.load(f)

        return RecoveryPoint(
            recovery_id=data["recovery_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            stage_number=data["stage_number"],
            task_id=data["task_id"],
            agent_id=data["agent_id"],
            status=data["status"],
            context=data["context"],
        )

    def _delete_snapshot_file(self, snapshot_id: str) -> None:
        """Delete snapshot file from disk."""
        file_path = self.storage_path / f"snapshot_{snapshot_id}.{self.format.value}"
        if file_path.exists():
            file_path.unlink()

    def _delete_recovery_point_file(self, recovery_id: str) -> None:
        """Delete recovery point file from disk."""
        file_path = self.storage_path / f"recovery_{recovery_id}.{self.format.value}"
        if file_path.exists():
            file_path.unlink()

    def get_statistics(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        return {
            "total_snapshots": len(self.snapshots),
            "total_recovery_points": len(self.recovery_points),
            "snapshot_types": list(set(s.state_type for s in self.snapshots.values())),
            "storage_path": str(self.storage_path),
            "format": self.format.value,
        }

    def reset(self) -> None:
        """Reset persistence state (for testing)."""
        self.snapshots.clear()
        self.recovery_points.clear()
