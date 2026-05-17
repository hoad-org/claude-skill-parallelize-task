"""Agent failure escalation and recovery strategies (Phase 2, Resilience)."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime
from parallelizer_skill.config import get_config


class EscalationLevel(str, Enum):
    """Escalation severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EscalationAction(str, Enum):
    """Actions to take on escalation."""
    RETRY = "retry"
    REASSIGN = "reassign"
    DECOMPOSE = "decompose"
    FALLBACK = "fallback"
    ABORT = "abort"


@dataclass
class EscalationEvent:
    """Record of an escalation event."""
    escalation_id: str
    agent_id: str
    task_id: str
    level: EscalationLevel
    cause: str
    action: EscalationAction
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    details: Dict = field(default_factory=dict)


@dataclass
class EscalationPolicy:
    """Policy for handling escalations."""
    level: EscalationLevel
    max_retries: int = 3
    retry_delay_seconds: int = 5
    backoff_multiplier: float = 2.0
    max_backoff_seconds: int = 300
    actions: List[EscalationAction] = field(default_factory=list)
    notify_handlers: List[str] = field(default_factory=list)


class EscalationManager:
    """Manage agent failure escalation and recovery (Phase 2)."""

    def __init__(self):
        """Initialize escalation manager."""
        self.config = get_config()
        self.events: Dict[str, List[EscalationEvent]] = {}
        self.policies: Dict[EscalationLevel, EscalationPolicy] = self._default_policies()
        self.handlers: Dict[str, Callable] = {}
        self.recovery_attempts: Dict[str, int] = {}

    def _default_policies(self) -> Dict[EscalationLevel, EscalationPolicy]:
        """Create default escalation policies."""
        return {
            EscalationLevel.INFO: EscalationPolicy(
                level=EscalationLevel.INFO,
                max_retries=1,
                retry_delay_seconds=2,
                actions=[EscalationAction.RETRY],
            ),
            EscalationLevel.WARNING: EscalationPolicy(
                level=EscalationLevel.WARNING,
                max_retries=2,
                retry_delay_seconds=5,
                actions=[EscalationAction.RETRY, EscalationAction.REASSIGN],
            ),
            EscalationLevel.CRITICAL: EscalationPolicy(
                level=EscalationLevel.CRITICAL,
                max_retries=3,
                retry_delay_seconds=10,
                actions=[EscalationAction.RETRY, EscalationAction.DECOMPOSE],
            ),
            EscalationLevel.EMERGENCY: EscalationPolicy(
                level=EscalationLevel.EMERGENCY,
                max_retries=0,
                retry_delay_seconds=0,
                actions=[EscalationAction.FALLBACK, EscalationAction.ABORT],
            ),
        }

    def register_handler(self, name: str, handler: Callable) -> None:
        """Register a handler for escalation actions."""
        self.handlers[name] = handler

    def record_failure(
        self,
        agent_id: str,
        task_id: str,
        level: EscalationLevel,
        cause: str,
    ) -> EscalationEvent:
        """Record an agent failure and escalate."""
        escalation_id = f"{agent_id}:{task_id}:{datetime.utcnow().timestamp()}"

        if agent_id not in self.events:
            self.events[agent_id] = []

        policy = self.policies[level]
        event = EscalationEvent(
            escalation_id=escalation_id,
            agent_id=agent_id,
            task_id=task_id,
            level=level,
            cause=cause,
            action=policy.actions[0] if policy.actions else EscalationAction.ABORT,
        )

        self.events[agent_id].append(event)
        self.recovery_attempts[escalation_id] = 0

        # Execute escalation actions
        self._execute_escalation(event, policy)

        return event

    def _execute_escalation(self, event: EscalationEvent, policy: EscalationPolicy) -> None:
        """Execute escalation actions."""
        for action in policy.actions:
            if action in self.handlers:
                self.handlers[action](event)

    def can_retry(self, escalation_id: str) -> bool:
        """Check if escalation can be retried."""
        if escalation_id not in self.recovery_attempts:
            return False

        agent_id = escalation_id.split(":")[0]
        if agent_id not in self.events:
            return False

        agent_events = self.events[agent_id]
        matching = [e for e in agent_events if e.escalation_id == escalation_id]

        if not matching:
            return False

        event = matching[-1]
        policy = self.policies[event.level]

        return self.recovery_attempts[escalation_id] < policy.max_retries

    def record_recovery(self, escalation_id: str) -> bool:
        """Record successful recovery from escalation."""
        if escalation_id not in self.recovery_attempts:
            return False

        self.recovery_attempts[escalation_id] += 1
        return True

    def get_retry_delay(self, escalation_id: str) -> int:
        """Get delay before next retry."""
        agent_id = escalation_id.split(":")[0]
        if agent_id not in self.events:
            return 0

        agent_events = self.events[agent_id]
        matching = [e for e in agent_events if e.escalation_id == escalation_id]

        if not matching:
            return 0

        event = matching[-1]
        policy = self.policies[event.level]
        retry_count = self.recovery_attempts.get(escalation_id, 0)

        delay = policy.retry_delay_seconds * (policy.backoff_multiplier ** retry_count)
        return min(int(delay), policy.max_backoff_seconds)

    def get_agent_failures(self, agent_id: str) -> List[EscalationEvent]:
        """Get all failures for an agent."""
        return self.events.get(agent_id, [])

    def get_failure_summary(self, agent_id: str) -> Dict:
        """Get summary of agent failures."""
        events = self.get_agent_failures(agent_id)

        return {
            "agent_id": agent_id,
            "total_failures": len(events),
            "by_level": {
                level.value: len([e for e in events if e.level == level])
                for level in EscalationLevel
            },
            "last_failure": events[-1].timestamp if events else None,
            "most_common_cause": self._most_common_cause(events),
        }

    def _most_common_cause(self, events: List[EscalationEvent]) -> Optional[str]:
        """Find most common failure cause."""
        if not events:
            return None

        cause_counts = {}
        for event in events:
            cause_counts[event.cause] = cause_counts.get(event.cause, 0) + 1

        return max(cause_counts.keys(), key=lambda k: cause_counts[k])

    def set_policy(self, level: EscalationLevel, policy: EscalationPolicy) -> None:
        """Update escalation policy."""
        self.policies[level] = policy

    def reset(self) -> None:
        """Reset escalation state (for testing)."""
        self.events.clear()
        self.recovery_attempts.clear()
