"""Event callbacks and handler management (Phase 2, Resilience)."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from parallelizer_skill.config import get_config


class EventType(str, Enum):
    """Types of events that trigger callbacks."""
    AGENT_SPAWNED = "agent_spawned"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_TIMEOUT = "agent_timeout"
    TASK_QUEUED = "task_queued"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    ORCHESTRATION_STARTED = "orchestration_started"
    ORCHESTRATION_COMPLETED = "orchestration_completed"
    ORCHESTRATION_FAILED = "orchestration_failed"


class CallbackPriority(str, Enum):
    """Priority for callback execution."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class CallbackEvent:
    """Event data passed to callbacks."""
    event_type: EventType
    source_id: str  # agent_id, task_id, or orchestration_id
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class CallbackHandler:
    """Registered callback handler."""
    handler_id: str
    event_type: EventType
    callback: Callable
    priority: CallbackPriority = CallbackPriority.NORMAL
    enabled: bool = True
    error_on_failure: bool = False  # If True, error in callback stops processing


@dataclass
class CallbackResult:
    """Result of callback execution."""
    handler_id: str
    event_type: EventType
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class CallbackManager:
    """Manage event callbacks and handlers (Phase 2)."""

    def __init__(self):
        """Initialize callback manager."""
        self.config = get_config()
        self.handlers: Dict[EventType, List[CallbackHandler]] = {e: [] for e in EventType}
        self.execution_history: List[CallbackResult] = []
        self.failed_callbacks: Dict[str, int] = {}

    def register(
        self,
        handler_id: str,
        event_type: EventType,
        callback: Callable,
        priority: CallbackPriority = CallbackPriority.NORMAL,
        error_on_failure: bool = False,
    ) -> None:
        """Register a callback handler for an event type."""
        handler = CallbackHandler(
            handler_id=handler_id,
            event_type=event_type,
            callback=callback,
            priority=priority,
            error_on_failure=error_on_failure,
        )

        self.handlers[event_type].append(handler)

        # Sort by priority (critical first)
        priority_order = {
            CallbackPriority.CRITICAL: 0,
            CallbackPriority.HIGH: 1,
            CallbackPriority.NORMAL: 2,
            CallbackPriority.LOW: 3,
        }
        self.handlers[event_type].sort(key=lambda h: priority_order[h.priority])

    def unregister(self, handler_id: str, event_type: EventType) -> bool:
        """Unregister a callback handler."""
        handlers = self.handlers[event_type]
        original_len = len(handlers)
        self.handlers[event_type] = [h for h in handlers if h.handler_id != handler_id]
        return len(self.handlers[event_type]) < original_len

    def emit(self, event: CallbackEvent) -> List[CallbackResult]:
        """Emit an event and execute all registered callbacks."""
        handlers = self.handlers[event.event_type]
        results = []

        for handler in handlers:
            if not handler.enabled:
                continue

            start_time = datetime.utcnow()
            result = CallbackResult(
                handler_id=handler.handler_id,
                event_type=event.event_type,
                success=False,
            )

            try:
                callback_result = handler.callback(event)
                result.success = True
                result.result = callback_result
            except Exception as e:
                result.error = str(e)
                self.failed_callbacks[handler.handler_id] = (
                    self.failed_callbacks.get(handler.handler_id, 0) + 1
                )

                if handler.error_on_failure:
                    raise

            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = elapsed

            results.append(result)
            self.execution_history.append(result)

        return results

    def enable_handler(self, handler_id: str, event_type: EventType) -> bool:
        """Enable a callback handler."""
        for handler in self.handlers[event_type]:
            if handler.handler_id == handler_id:
                handler.enabled = True
                return True
        return False

    def disable_handler(self, handler_id: str, event_type: EventType) -> bool:
        """Disable a callback handler."""
        for handler in self.handlers[event_type]:
            if handler.handler_id == handler_id:
                handler.enabled = False
                return True
        return False

    def get_handlers(self, event_type: EventType) -> List[CallbackHandler]:
        """Get all handlers for an event type."""
        return list(self.handlers[event_type])

    def get_execution_history(
        self,
        event_type: Optional[EventType] = None,
        handler_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CallbackResult]:
        """Get callback execution history."""
        history = self.execution_history

        if event_type:
            history = [r for r in history if r.event_type == event_type]

        if handler_id:
            history = [r for r in history if r.handler_id == handler_id]

        return history[-limit:]

    def get_failed_callbacks(self) -> Dict[str, int]:
        """Get count of failures per handler."""
        return dict(self.failed_callbacks)

    def get_statistics(self) -> Dict[str, Any]:
        """Get callback execution statistics."""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "average_execution_time_ms": 0.0,
                "by_event_type": {},
            }

        successful = sum(1 for r in self.execution_history if r.success)
        failed = len(self.execution_history) - successful
        avg_time = sum(r.execution_time_ms for r in self.execution_history) / len(
            self.execution_history
        )

        by_type = {}
        for event_type in EventType:
            matching = [r for r in self.execution_history if r.event_type == event_type]
            if matching:
                by_type[event_type.value] = {
                    "count": len(matching),
                    "successful": sum(1 for r in matching if r.success),
                    "failed": sum(1 for r in matching if not r.success),
                }

        return {
            "total_executions": len(self.execution_history),
            "successful": successful,
            "failed": failed,
            "average_execution_time_ms": avg_time,
            "by_event_type": by_type,
            "failed_handlers": self.failed_callbacks,
        }

    def reset(self) -> None:
        """Reset callback state (for testing)."""
        self.execution_history.clear()
        self.failed_callbacks.clear()
        for handlers in self.handlers.values():
            handlers.clear()
