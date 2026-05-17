"""Agent state machine, monitoring, and heartbeat management (GAP 1)."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from parallelizer_skill.config import get_config


class AgentState(str, Enum):
    """Agent lifecycle states."""
    PENDING = "pending"
    SPAWNED = "spawned"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CRASHED = "crashed"


@dataclass
class AgentHeartbeat:
    """Heartbeat from a running agent."""
    agent_id: str
    task_id: str
    status: AgentState
    tokens_consumed: int
    last_action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentStatus:
    """Track state and health of a single agent."""
    agent_id: str
    task_id: str
    state: AgentState = AgentState.PENDING
    tokens_consumed: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None
    heartbeat_count: int = 0
    error_message: Optional[str] = None

    def is_alive(self, heartbeat_timeout: int = 30) -> bool:
        """Check if agent is still alive (recent heartbeat)."""
        if self.last_heartbeat is None:
            return False
        age = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return age < heartbeat_timeout

    def record_heartbeat(self, heartbeat: AgentHeartbeat) -> None:
        """Record incoming heartbeat."""
        self.last_heartbeat = heartbeat.timestamp
        self.tokens_consumed = heartbeat.tokens_consumed
        self.heartbeat_count += 1
        self.state = heartbeat.status

    def execution_time(self) -> timedelta:
        """Get execution time since agent started."""
        return datetime.utcnow() - self.created_at


class AgentMonitor:
    """Monitor agent states, detect failures, enforce timeouts (GAP 1)."""

    def __init__(self):
        """Initialize agent monitor."""
        self.config = get_config()
        self.agents: Dict[str, AgentStatus] = {}
        self.heartbeat_timeout = self.config.orchestration.heartbeat_timeout_seconds
        self.max_agents = self.config.orchestration.max_concurrent_agents

    def spawn_agent(self, agent_id: str, task_id: str) -> None:
        """Record new agent spawn."""
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already exists")
        if len([a for a in self.agents.values() if a.state == AgentState.RUNNING]) >= self.max_agents:
            raise RuntimeError(f"Max concurrent agents ({self.max_agents}) reached")

        self.agents[agent_id] = AgentStatus(
            agent_id=agent_id,
            task_id=task_id,
            state=AgentState.SPAWNED,
        )

    def record_heartbeat(self, heartbeat: AgentHeartbeat) -> None:
        """Record heartbeat from running agent."""
        if heartbeat.agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {heartbeat.agent_id}")

        agent = self.agents[heartbeat.agent_id]
        agent.record_heartbeat(heartbeat)

    def check_agent_health(self, agent_id: str) -> AgentState:
        """Check health of specific agent, update state if needed."""
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")

        agent = self.agents[agent_id]

        # Check timeout
        if agent.state == AgentState.RUNNING:
            max_age = self.config.orchestration.per_task_timeout_minutes * 60
            if agent.execution_time().total_seconds() > max_age:
                agent.state = AgentState.TIMEOUT
                agent.error_message = f"Exceeded {self.config.orchestration.per_task_timeout_minutes}min timeout"
                return agent.state

        # Check heartbeat (for RUNNING agents)
        if agent.state == AgentState.RUNNING and not agent.is_alive(self.heartbeat_timeout):
            agent.state = AgentState.CRASHED
            agent.error_message = f"No heartbeat for {self.heartbeat_timeout}s"
            return agent.state

        return agent.state

    def check_all_agent_health(self) -> Dict[str, AgentState]:
        """Check health of all agents, return state changes."""
        states = {}
        for agent_id in list(self.agents.keys()):
            states[agent_id] = self.check_agent_health(agent_id)
        return states

    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """Get status of specific agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        return self.agents[agent_id]

    def get_running_agents(self) -> List[str]:
        """Get list of currently running agent IDs."""
        return [
            agent_id for agent_id, status in self.agents.items()
            if status.state == AgentState.RUNNING
        ]

    def get_failed_agents(self) -> List[str]:
        """Get list of failed/crashed/timeout agent IDs."""
        return [
            agent_id for agent_id, status in self.agents.items()
            if status.state in (AgentState.FAILED, AgentState.CRASHED, AgentState.TIMEOUT)
        ]

    def get_available_slots(self) -> int:
        """Get number of available agent slots."""
        running = len(self.get_running_agents())
        return self.max_agents - running

    def mark_complete(self, agent_id: str, tokens_consumed: int) -> None:
        """Mark agent as complete."""
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        agent = self.agents[agent_id]
        agent.state = AgentState.COMPLETE
        agent.tokens_consumed = tokens_consumed

    def mark_failed(self, agent_id: str, error: str) -> None:
        """Mark agent as failed."""
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        agent = self.agents[agent_id]
        agent.state = AgentState.FAILED
        agent.error_message = error

    def reset(self) -> None:
        """Reset all agent tracking (for testing)."""
        self.agents.clear()
