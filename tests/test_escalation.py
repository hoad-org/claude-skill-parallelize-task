"""Unit tests for escalation management (Phase 2)."""

import pytest
from parallelizer_skill.escalation import EscalationManager, EscalationLevel, EscalationAction, EscalationEvent
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestEscalationEvent:
    """Test escalation event."""

    def test_event_creation(self):
        """Test creating an escalation event."""
        event = EscalationEvent(
            escalation_id="esc_1",
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.WARNING,
            cause="Timeout",
            action=EscalationAction.RETRY,
        )

        assert event.escalation_id == "esc_1"
        assert event.agent_id == "agent_1"
        assert event.task_id == "task_1"
        assert event.level == EscalationLevel.WARNING
        assert event.retry_count == 0


@pytest.mark.unit
class TestEscalationManager:
    """Test escalation manager."""

    @pytest.fixture
    def manager(self):
        """Create fresh manager for each test."""
        reset_config()
        return EscalationManager()

    def test_manager_creation(self, manager):
        """Test creating manager."""
        assert manager is not None
        assert len(manager.events) == 0
        assert len(manager.policies) == 4  # 4 severity levels

    def test_record_failure_info_level(self, manager):
        """Test recording info-level failure."""
        event = manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.INFO,
            cause="Minor issue",
        )

        assert event.agent_id == "agent_1"
        assert event.level == EscalationLevel.INFO
        assert "agent_1" in manager.events

    def test_record_failure_critical_level(self, manager):
        """Test recording critical-level failure."""
        event = manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.CRITICAL,
            cause="Major failure",
        )

        assert event.level == EscalationLevel.CRITICAL
        assert event.action == EscalationAction.RETRY

    def test_policy_max_retries(self, manager):
        """Test policy max retries."""
        info_policy = manager.policies[EscalationLevel.INFO]
        assert info_policy.max_retries == 1

        critical_policy = manager.policies[EscalationLevel.CRITICAL]
        assert critical_policy.max_retries == 3

        emergency_policy = manager.policies[EscalationLevel.EMERGENCY]
        assert emergency_policy.max_retries == 0

    def test_can_retry_within_limits(self, manager):
        """Test retrying within limits."""
        event = manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.INFO,
            cause="Timeout",
        )

        assert manager.can_retry(event.escalation_id)

    def test_can_retry_exceeds_limits(self, manager):
        """Test retry exceeds limits."""
        event = manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.EMERGENCY,
            cause="Critical error",
        )

        # Emergency allows 0 retries
        assert not manager.can_retry(event.escalation_id)

    def test_record_recovery(self, manager):
        """Test recording recovery."""
        event = manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.WARNING,
            cause="Temporary failure",
        )

        success = manager.record_recovery(event.escalation_id)
        assert success

    def test_get_retry_delay(self, manager):
        """Test retry delay calculation."""
        event = manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.WARNING,
            cause="Timeout",
        )

        delay = manager.get_retry_delay(event.escalation_id)
        assert delay == 5  # Base delay for WARNING

    def test_get_retry_delay_with_backoff(self, manager):
        """Test retry delay with exponential backoff."""
        event = manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.CRITICAL,
            cause="Error",
        )

        # First retry
        manager.record_recovery(event.escalation_id)
        delay1 = manager.get_retry_delay(event.escalation_id)

        # Second retry
        manager.record_recovery(event.escalation_id)
        delay2 = manager.get_retry_delay(event.escalation_id)

        assert delay2 > delay1  # Exponential backoff

    def test_get_agent_failures(self, manager):
        """Test getting agent failures."""
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.INFO,
            cause="Issue 1",
        )
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_2",
            level=EscalationLevel.WARNING,
            cause="Issue 2",
        )

        failures = manager.get_agent_failures("agent_1")
        assert len(failures) == 2

    def test_get_failure_summary(self, manager):
        """Test failure summary."""
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.INFO,
            cause="Timeout",
        )
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_2",
            level=EscalationLevel.CRITICAL,
            cause="Timeout",
        )

        summary = manager.get_failure_summary("agent_1")

        assert summary["agent_id"] == "agent_1"
        assert summary["total_failures"] == 2
        assert summary["most_common_cause"] == "Timeout"

    def test_register_handler(self, manager):
        """Test registering escalation handler."""

        def my_handler(event):
            return "handled"

        manager.register_handler("my_handler", my_handler)
        assert "my_handler" in manager.handlers

    def test_set_policy(self, manager):
        """Test setting custom policy."""
        from parallelizer_skill.escalation import EscalationPolicy

        custom_policy = EscalationPolicy(
            level=EscalationLevel.INFO,
            max_retries=5,
            retry_delay_seconds=10,
        )

        manager.set_policy(EscalationLevel.INFO, custom_policy)
        assert manager.policies[EscalationLevel.INFO].max_retries == 5

    def test_reset(self, manager):
        """Test reset."""
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.WARNING,
            cause="Error",
        )

        manager.reset()

        assert len(manager.events) == 0
        assert len(manager.recovery_attempts) == 0

    def test_unknown_escalation_no_retry(self, manager):
        """Test unknown escalation returns False for retry."""
        assert not manager.can_retry("unknown_id")

    def test_record_recovery_unknown(self, manager):
        """Test recovery on unknown escalation."""
        success = manager.record_recovery("unknown_id")
        assert not success

    def test_most_common_cause_with_multiple_failures(self, manager):
        """Test identifying most common cause."""
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_1",
            level=EscalationLevel.INFO,
            cause="Timeout",
        )
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_2",
            level=EscalationLevel.INFO,
            cause="Timeout",
        )
        manager.record_failure(
            agent_id="agent_1",
            task_id="task_3",
            level=EscalationLevel.INFO,
            cause="Connection",
        )

        summary = manager.get_failure_summary("agent_1")
        assert summary["most_common_cause"] == "Timeout"
