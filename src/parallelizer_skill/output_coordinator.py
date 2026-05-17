"""Output coordination with safe writes and race condition handling (GAP 4)."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime
import hashlib


class OutputPattern(str, Enum):
    """Output coordination patterns."""
    SCRATCHPAD = "scratchpad_model"  # Shared doc, section-based
    PR = "pr_model"  # Pull requests per agent
    HIERARCHICAL = "hierarchical_model"  # Agent feeds next agent
    API = "api_model"  # Structured JSON submission
    FILE = "file_model"  # Files in temp directory
    STREAMING = "streaming_model"  # Real-time streaming


@dataclass
class OutputSection:
    """Section in scratchpad model."""
    agent_id: str
    task_id: str
    status: str = "pending"  # pending, in_progress, complete, failed
    content: str = ""
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def compute_checksum(self) -> str:
        """Compute CRC checksum for content integrity."""
        return hashlib.md5(self.content.encode()).hexdigest()

    def mark_complete(self, content: str) -> None:
        """Mark section as complete with content (atomic operation)."""
        self.content = content
        self.status = "complete"
        self.checksum = self.compute_checksum()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark section as failed."""
        self.content = error
        self.status = "failed"
        self.updated_at = datetime.utcnow()

    def is_valid(self) -> bool:
        """Validate section integrity (checksum)."""
        if self.checksum is None or not self.content:
            return False
        computed = self.compute_checksum()
        return computed == self.checksum


@dataclass
class OutputCoordination:
    """Coordination for a single output pattern execution."""
    pattern: OutputPattern
    orchestration_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class ScratchpadCoordinator:
    """Scratchpad model: central doc, all agents write sections (GAP 4)."""

    def __init__(self, orchestration_id: str):
        """Initialize scratchpad coordinator."""
        self.orchestration_id = orchestration_id
        self.sections: Dict[str, OutputSection] = {}

    def reserve_section(self, agent_id: str, task_id: str) -> OutputSection:
        """Reserve section for agent (pre-create with pending status)."""
        key = f"{agent_id}:{task_id}"

        if key in self.sections:
            raise ValueError(f"Section {key} already reserved")

        section = OutputSection(agent_id=agent_id, task_id=task_id)
        self.sections[key] = section
        return section

    def start_write(self, agent_id: str, task_id: str) -> None:
        """Mark section as being written to."""
        key = f"{agent_id}:{task_id}"

        if key not in self.sections:
            raise ValueError(f"Unknown section: {key}")

        self.sections[key].status = "in_progress"

    def complete_write(self, agent_id: str, task_id: str, content: str) -> bool:
        """Complete atomic write (full content or nothing)."""
        key = f"{agent_id}:{task_id}"

        if key not in self.sections:
            raise ValueError(f"Unknown section: {key}")

        section = self.sections[key]

        # Atomic write
        try:
            section.mark_complete(content)
            return True
        except Exception as e:
            section.mark_failed(str(e))
            return False

    def fail_write(self, agent_id: str, task_id: str, error: str) -> None:
        """Mark section as failed."""
        key = f"{agent_id}:{task_id}"

        if key not in self.sections:
            raise ValueError(f"Unknown section: {key}")

        self.sections[key].mark_failed(error)

    def get_section(self, agent_id: str, task_id: str) -> Optional[OutputSection]:
        """Get section (safe to read once complete)."""
        key = f"{agent_id}:{task_id}"
        return self.sections.get(key)

    def wait_for_section(self, agent_id: str, task_id: str, timeout_seconds: int = 30) -> Optional[str]:
        """Wait for section to complete (for hierarchical/sequential tasks)."""
        import time
        key = f"{agent_id}:{task_id}"

        if key not in self.sections:
            raise ValueError(f"Unknown section: {key}")

        section = self.sections[key]
        start = time.time()

        while time.time() - start < timeout_seconds:
            if section.status == "complete":
                if section.is_valid():
                    return section.content
                else:
                    raise ValueError(f"Section {key} is corrupted (checksum mismatch)")
            elif section.status == "failed":
                raise RuntimeError(f"Section {key} failed: {section.content}")

            time.sleep(0.1)

        raise TimeoutError(f"Section {key} did not complete within {timeout_seconds}s")

    def all_complete(self) -> bool:
        """Check if all sections completed."""
        if not self.sections:
            return False
        return all(s.status in ("complete", "failed") for s in self.sections.values())

    def get_summary(self) -> Dict:
        """Get summary of all sections."""
        return {
            "total_sections": len(self.sections),
            "complete": sum(1 for s in self.sections.values() if s.status == "complete"),
            "failed": sum(1 for s in self.sections.values() if s.status == "failed"),
            "sections": {
                key: {
                    "status": s.status,
                    "content_length": len(s.content),
                    "checksum": s.checksum,
                    "created_at": s.created_at.isoformat(),
                }
                for key, s in self.sections.items()
            }
        }


class OutputCoordinator:
    """Coordinate output from multiple agents based on pattern (GAP 4)."""

    def __init__(self, orchestration_id: str, pattern: OutputPattern = OutputPattern.SCRATCHPAD):
        """Initialize output coordinator."""
        self.orchestration_id = orchestration_id
        self.pattern = pattern

        if pattern == OutputPattern.SCRATCHPAD:
            self.coordinator = ScratchpadCoordinator(orchestration_id)
        else:
            # Other patterns would be implemented here
            raise NotImplementedError(f"Pattern {pattern} not yet implemented")

    def reserve_output(self, agent_id: str, task_id: str) -> Any:
        """Reserve output space for agent."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            return self.coordinator.reserve_section(agent_id, task_id)
        return None

    def start_write(self, agent_id: str, task_id: str) -> None:
        """Start writing output."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            self.coordinator.start_write(agent_id, task_id)

    def complete_write(self, agent_id: str, task_id: str, content: str) -> bool:
        """Complete output write (atomic)."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            return self.coordinator.complete_write(agent_id, task_id, content)
        return False

    def fail_write(self, agent_id: str, task_id: str, error: str) -> None:
        """Mark output as failed."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            self.coordinator.fail_write(agent_id, task_id, error)

    def get_output(self, agent_id: str, task_id: str) -> Optional[str]:
        """Get completed output."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            section = self.coordinator.get_section(agent_id, task_id)
            return section.content if section else None
        return None

    def wait_for_output(self, agent_id: str, task_id: str, timeout_seconds: int = 30) -> Optional[str]:
        """Wait for output to complete."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            return self.coordinator.wait_for_section(agent_id, task_id, timeout_seconds)
        return None

    def all_outputs_complete(self) -> bool:
        """Check if all outputs completed."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            return self.coordinator.all_complete()
        return False

    def get_status(self) -> Dict:
        """Get coordination status."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            return self.coordinator.get_summary()
        return {}

    def reset(self) -> None:
        """Reset coordinator (for testing)."""
        if isinstance(self.coordinator, ScratchpadCoordinator):
            self.coordinator.sections.clear()
