"""Unit tests for callback management (Phase 2)."""

import pytest
from parallelizer_skill.callbacks import CallbackManager, EventType, CallbackPriority, CallbackEvent
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestCallbackManager:
    """Test callback management."""

    @pytest.fixture
    def manager(self):
        """Create fresh manager for each test."""
        reset_config()
        return CallbackManager()

    def test_manager_creation(self, manager):
        """Test creating manager."""
        assert manager is not None
        assert len(manager.handlers) == 15  # EventType enum count

    def test_register_handler(self, manager):
        """Test registering a handler."""

        def handler(event):
            return "handled"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        handlers = manager.get_handlers(EventType.AGENT_SPAWNED)
        assert len(handlers) == 1
        assert handlers[0].handler_id == "handler_1"

    def test_unregister_handler(self, manager):
        """Test unregistering a handler."""

        def handler(event):
            return "handled"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        success = manager.unregister("handler_1", EventType.AGENT_SPAWNED)
        assert success

        handlers = manager.get_handlers(EventType.AGENT_SPAWNED)
        assert len(handlers) == 0

    def test_emit_event_success(self, manager):
        """Test emitting event with successful handler."""
        called = []

        def handler(event):
            called.append(event)
            return "success"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        results = manager.emit(event)

        assert len(results) == 1
        assert results[0].success
        assert len(called) == 1

    def test_emit_event_failure(self, manager):
        """Test emitting event with failing handler."""

        def handler(event):
            raise ValueError("Handler error")

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        results = manager.emit(event)

        assert len(results) == 1
        assert not results[0].success
        assert "Handler error" in results[0].error

    def test_handler_priority_execution_order(self, manager):
        """Test handlers execute in priority order."""
        execution_order = []

        def critical_handler(event):
            execution_order.append("critical")
            return "critical"

        def low_handler(event):
            execution_order.append("low")
            return "low"

        manager.register(
            handler_id="low",
            event_type=EventType.AGENT_SPAWNED,
            callback=low_handler,
            priority=CallbackPriority.LOW,
        )

        manager.register(
            handler_id="critical",
            event_type=EventType.AGENT_SPAWNED,
            callback=critical_handler,
            priority=CallbackPriority.CRITICAL,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)

        assert execution_order == ["critical", "low"]

    def test_error_on_failure_stops_processing(self, manager):
        """Test error_on_failure stops processing."""
        executed = []

        def failing_handler(event):
            executed.append("failing")
            raise ValueError("Error")

        def normal_handler(event):
            executed.append("normal")
            return "ok"

        manager.register(
            handler_id="fail",
            event_type=EventType.AGENT_SPAWNED,
            callback=failing_handler,
            priority=CallbackPriority.CRITICAL,
            error_on_failure=True,
        )

        manager.register(
            handler_id="normal",
            event_type=EventType.AGENT_SPAWNED,
            callback=normal_handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        with pytest.raises(ValueError):
            manager.emit(event)

        assert executed == ["failing"]

    def test_disable_handler(self, manager):
        """Test disabling a handler."""
        called = []

        def handler(event):
            called.append(event)
            return "ok"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        manager.disable_handler("handler_1", EventType.AGENT_SPAWNED)

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)

        assert len(called) == 0

    def test_enable_handler(self, manager):
        """Test enabling a handler."""
        called = []

        def handler(event):
            called.append(event)
            return "ok"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        manager.disable_handler("handler_1", EventType.AGENT_SPAWNED)
        manager.enable_handler("handler_1", EventType.AGENT_SPAWNED)

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)

        assert len(called) == 1

    def test_execution_history(self, manager):
        """Test execution history tracking."""

        def handler(event):
            return "ok"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)
        manager.emit(event)

        history = manager.get_execution_history()
        assert len(history) == 2

    def test_execution_history_filtered_by_event(self, manager):
        """Test filtering execution history by event type."""

        def handler(event):
            return "ok"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        manager.register(
            handler_id="handler_2",
            event_type=EventType.TASK_STARTED,
            callback=handler,
        )

        spawned_event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        task_event = CallbackEvent(
            event_type=EventType.TASK_STARTED,
            source_id="task_1",
        )

        manager.emit(spawned_event)
        manager.emit(task_event)

        spawned_history = manager.get_execution_history(event_type=EventType.AGENT_SPAWNED)
        assert len(spawned_history) == 1
        assert spawned_history[0].event_type == EventType.AGENT_SPAWNED

    def test_failed_callbacks_tracking(self, manager):
        """Test tracking failed callbacks."""

        def failing_handler(event):
            raise ValueError("Error")

        manager.register(
            handler_id="failing",
            event_type=EventType.AGENT_SPAWNED,
            callback=failing_handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)
        manager.emit(event)

        failed = manager.get_failed_callbacks()
        assert failed["failing"] == 2

    def test_statistics(self, manager):
        """Test callback statistics."""

        def handler(event):
            return "ok"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)

        stats = manager.get_statistics()

        assert stats["total_executions"] == 1
        assert stats["successful"] == 1
        assert stats["failed"] == 0

    def test_statistics_with_failures(self, manager):
        """Test statistics with failures."""

        def failing_handler(event):
            raise ValueError("Error")

        manager.register(
            handler_id="failing",
            event_type=EventType.AGENT_SPAWNED,
            callback=failing_handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)

        stats = manager.get_statistics()

        assert stats["total_executions"] == 1
        assert stats["failed"] == 1
        assert stats["successful"] == 0

    def test_reset(self, manager):
        """Test reset."""

        def handler(event):
            return "ok"

        manager.register(
            handler_id="handler_1",
            event_type=EventType.AGENT_SPAWNED,
            callback=handler,
        )

        event = CallbackEvent(
            event_type=EventType.AGENT_SPAWNED,
            source_id="agent_1",
        )

        manager.emit(event)

        manager.reset()

        assert len(manager.execution_history) == 0
        assert len(manager.failed_callbacks) == 0
