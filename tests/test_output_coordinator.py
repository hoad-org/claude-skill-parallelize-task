"""Unit tests for output coordination (GAP 4)."""

import pytest
from parallelizer_skill.output_coordinator import OutputPattern, OutputSection, ScratchpadCoordinator, OutputCoordinator


@pytest.mark.unit
class TestOutputPattern:
    """Test output pattern enum."""

    def test_output_pattern_scratchpad(self):
        """Test SCRATCHPAD pattern value."""
        assert OutputPattern.SCRATCHPAD.value == "scratchpad_model"

    def test_output_pattern_pr(self):
        """Test PR pattern value."""
        assert OutputPattern.PR.value == "pr_model"

    def test_output_pattern_hierarchical(self):
        """Test HIERARCHICAL pattern value."""
        assert OutputPattern.HIERARCHICAL.value == "hierarchical_model"

    def test_output_pattern_api(self):
        """Test API pattern value."""
        assert OutputPattern.API.value == "api_model"

    def test_output_pattern_file(self):
        """Test FILE pattern value."""
        assert OutputPattern.FILE.value == "file_model"

    def test_output_pattern_streaming(self):
        """Test STREAMING pattern value."""
        assert OutputPattern.STREAMING.value == "streaming_model"


@pytest.mark.unit
class TestOutputSection:
    """Test output section dataclass."""

    def test_section_creation(self):
        """Test creating an output section."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")

        assert section.agent_id == "agent_1"
        assert section.task_id == "task_1"
        assert section.status == "pending"
        assert section.content == ""
        assert section.checksum is None

    def test_section_compute_checksum(self):
        """Test checksum computation."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")
        section.content = "test content"

        checksum = section.compute_checksum()
        assert checksum is not None
        assert len(checksum) == 32  # MD5 hash length

    def test_section_checksum_consistency(self):
        """Test checksum is consistent for same content."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")
        section.content = "test content"

        checksum1 = section.compute_checksum()
        checksum2 = section.compute_checksum()

        assert checksum1 == checksum2

    def test_section_checksum_differs_for_different_content(self):
        """Test checksum differs for different content."""
        section1 = OutputSection(agent_id="agent_1", task_id="task_1")
        section1.content = "content 1"

        section2 = OutputSection(agent_id="agent_1", task_id="task_1")
        section2.content = "content 2"

        assert section1.compute_checksum() != section2.compute_checksum()

    def test_section_mark_complete(self):
        """Test marking section as complete."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")

        section.mark_complete("final content")

        assert section.content == "final content"
        assert section.status == "complete"
        assert section.checksum is not None
        assert section.updated_at is not None

    def test_section_mark_failed(self):
        """Test marking section as failed."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")

        section.mark_failed("Connection error")

        assert section.content == "Connection error"
        assert section.status == "failed"
        assert section.updated_at is not None

    def test_section_is_valid_complete(self):
        """Test validation of complete section."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")
        section.mark_complete("content")

        assert section.is_valid()

    def test_section_is_valid_no_checksum(self):
        """Test validation fails without checksum."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")
        section.content = "content"

        assert not section.is_valid()

    def test_section_is_valid_corrupted(self):
        """Test validation fails with mismatched checksum."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")
        section.mark_complete("original content")

        # Corrupt the content
        section.content = "modified content"

        assert not section.is_valid()

    def test_section_is_valid_empty_content(self):
        """Test validation fails with empty content."""
        section = OutputSection(agent_id="agent_1", task_id="task_1")
        section.checksum = "somehash"
        section.content = ""

        assert not section.is_valid()


@pytest.mark.unit
class TestScratchpadCoordinator:
    """Test scratchpad coordinator."""

    @pytest.fixture
    def coordinator(self):
        """Create fresh coordinator for each test."""
        return ScratchpadCoordinator(orchestration_id="orch_1")

    def test_coordinator_creation(self, coordinator):
        """Test creating coordinator."""
        assert coordinator.orchestration_id == "orch_1"
        assert len(coordinator.sections) == 0

    def test_reserve_section(self, coordinator):
        """Test reserving a section."""
        section = coordinator.reserve_section("agent_1", "task_1")

        assert section is not None
        assert section.agent_id == "agent_1"
        assert section.task_id == "task_1"
        assert "agent_1:task_1" in coordinator.sections

    def test_reserve_section_duplicate_raises_error(self, coordinator):
        """Test reserving duplicate section raises error."""
        coordinator.reserve_section("agent_1", "task_1")

        with pytest.raises(ValueError):
            coordinator.reserve_section("agent_1", "task_1")

    def test_start_write(self, coordinator):
        """Test starting write operation."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.start_write("agent_1", "task_1")

        section = coordinator.get_section("agent_1", "task_1")
        assert section.status == "in_progress"

    def test_start_write_unknown_section(self, coordinator):
        """Test starting write on unknown section raises error."""
        with pytest.raises(ValueError):
            coordinator.start_write("agent_1", "task_1")

    def test_complete_write(self, coordinator):
        """Test completing write operation."""
        coordinator.reserve_section("agent_1", "task_1")
        success = coordinator.complete_write("agent_1", "task_1", "output content")

        assert success
        section = coordinator.get_section("agent_1", "task_1")
        assert section.status == "complete"
        assert section.content == "output content"

    def test_complete_write_unknown_section(self, coordinator):
        """Test completing write on unknown section raises error."""
        with pytest.raises(ValueError):
            coordinator.complete_write("agent_1", "task_1", "content")

    def test_complete_write_atomicity(self, coordinator):
        """Test atomic nature of complete_write."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.complete_write("agent_1", "task_1", "content")

        section = coordinator.get_section("agent_1", "task_1")
        assert section.content == "content"
        assert section.checksum is not None
        assert section.is_valid()

    def test_fail_write(self, coordinator):
        """Test failing a write operation."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.fail_write("agent_1", "task_1", "Timeout error")

        section = coordinator.get_section("agent_1", "task_1")
        assert section.status == "failed"
        assert section.content == "Timeout error"

    def test_fail_write_unknown_section(self, coordinator):
        """Test failing unknown section raises error."""
        with pytest.raises(ValueError):
            coordinator.fail_write("agent_1", "task_1", "error")

    def test_get_section(self, coordinator):
        """Test getting a section."""
        coordinator.reserve_section("agent_1", "task_1")
        section = coordinator.get_section("agent_1", "task_1")

        assert section is not None
        assert section.agent_id == "agent_1"

    def test_get_section_unknown(self, coordinator):
        """Test getting unknown section returns None."""
        section = coordinator.get_section("agent_1", "task_1")
        assert section is None

    def test_wait_for_section_immediate(self, coordinator):
        """Test waiting for already complete section."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.complete_write("agent_1", "task_1", "content")

        content = coordinator.wait_for_section("agent_1", "task_1", timeout_seconds=1)

        assert content == "content"

    def test_wait_for_section_timeout(self, coordinator):
        """Test wait timeout."""
        coordinator.reserve_section("agent_1", "task_1")

        with pytest.raises(TimeoutError):
            coordinator.wait_for_section("agent_1", "task_1", timeout_seconds=1)

    def test_wait_for_section_unknown(self, coordinator):
        """Test waiting on unknown section raises error."""
        with pytest.raises(ValueError):
            coordinator.wait_for_section("agent_1", "task_1", timeout_seconds=1)

    def test_wait_for_section_corrupted(self, coordinator):
        """Test waiting for corrupted section raises error."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.complete_write("agent_1", "task_1", "original")

        # Corrupt it
        coordinator.sections["agent_1:task_1"].content = "corrupted"

        with pytest.raises(ValueError):
            coordinator.wait_for_section("agent_1", "task_1", timeout_seconds=1)

    def test_wait_for_section_failed(self, coordinator):
        """Test waiting for failed section raises error."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.fail_write("agent_1", "task_1", "Connection error")

        with pytest.raises(RuntimeError):
            coordinator.wait_for_section("agent_1", "task_1", timeout_seconds=1)

    def test_all_complete_empty(self, coordinator):
        """Test all_complete with no sections."""
        assert not coordinator.all_complete()

    def test_all_complete_some_pending(self, coordinator):
        """Test all_complete with pending sections."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.reserve_section("agent_2", "task_2")
        coordinator.complete_write("agent_1", "task_1", "content")

        assert not coordinator.all_complete()

    def test_all_complete_all_done(self, coordinator):
        """Test all_complete when all sections done."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.reserve_section("agent_2", "task_2")
        coordinator.complete_write("agent_1", "task_1", "content1")
        coordinator.complete_write("agent_2", "task_2", "content2")

        assert coordinator.all_complete()

    def test_get_summary_empty(self, coordinator):
        """Test summary with no sections."""
        summary = coordinator.get_summary()

        assert summary["total_sections"] == 0
        assert summary["complete"] == 0
        assert summary["failed"] == 0

    def test_get_summary_mixed_states(self, coordinator):
        """Test summary with mixed section states."""
        coordinator.reserve_section("agent_1", "task_1")
        coordinator.reserve_section("agent_2", "task_2")
        coordinator.reserve_section("agent_3", "task_3")

        coordinator.complete_write("agent_1", "task_1", "content")
        coordinator.fail_write("agent_2", "task_2", "error")

        summary = coordinator.get_summary()

        assert summary["total_sections"] == 3
        assert summary["complete"] == 1
        assert summary["failed"] == 1


@pytest.mark.unit
class TestOutputCoordinator:
    """Test output coordinator."""

    def test_coordinator_creation_scratchpad(self):
        """Test creating coordinator with scratchpad pattern."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)

        assert coordinator.orchestration_id == "orch_1"
        assert coordinator.pattern == OutputPattern.SCRATCHPAD
        assert isinstance(coordinator.coordinator, ScratchpadCoordinator)

    def test_coordinator_unimplemented_pattern(self):
        """Test creating coordinator with unimplemented pattern."""
        with pytest.raises(NotImplementedError):
            OutputCoordinator("orch_1", OutputPattern.PR)

    def test_reserve_output(self):
        """Test reserving output."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        section = coordinator.reserve_output("agent_1", "task_1")

        assert section is not None
        assert section.agent_id == "agent_1"

    def test_start_write(self):
        """Test starting write."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")
        coordinator.start_write("agent_1", "task_1")

        section = coordinator.coordinator.get_section("agent_1", "task_1")
        assert section.status == "in_progress"

    def test_complete_write(self):
        """Test completing write."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")
        success = coordinator.complete_write("agent_1", "task_1", "output")

        assert success
        section = coordinator.coordinator.get_section("agent_1", "task_1")
        assert section.status == "complete"

    def test_fail_write(self):
        """Test failing write."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")
        coordinator.fail_write("agent_1", "task_1", "error")

        section = coordinator.coordinator.get_section("agent_1", "task_1")
        assert section.status == "failed"

    def test_get_output(self):
        """Test getting output."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")
        coordinator.complete_write("agent_1", "task_1", "result")

        output = coordinator.get_output("agent_1", "task_1")
        assert output == "result"

    def test_get_output_none(self):
        """Test getting unknown output."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        output = coordinator.get_output("agent_1", "task_1")

        assert output is None

    def test_wait_for_output(self):
        """Test waiting for output."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")
        coordinator.complete_write("agent_1", "task_1", "data")

        output = coordinator.wait_for_output("agent_1", "task_1", timeout_seconds=1)
        assert output == "data"

    def test_all_outputs_complete(self):
        """Test checking all outputs complete."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")
        coordinator.reserve_output("agent_2", "task_2")

        assert not coordinator.all_outputs_complete()

        coordinator.complete_write("agent_1", "task_1", "output1")
        coordinator.complete_write("agent_2", "task_2", "output2")

        assert coordinator.all_outputs_complete()

    def test_get_status(self):
        """Test getting status."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")

        status = coordinator.get_status()

        assert status["total_sections"] == 1
        assert status["complete"] == 0

    def test_reset(self):
        """Test reset."""
        coordinator = OutputCoordinator("orch_1", OutputPattern.SCRATCHPAD)
        coordinator.reserve_output("agent_1", "task_1")

        coordinator.reset()

        assert len(coordinator.coordinator.sections) == 0
