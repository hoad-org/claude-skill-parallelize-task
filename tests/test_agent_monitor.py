"""Unit tests for agent monitoring (GAP 1)."""

import pytest
from datetime import datetime, timedelta
from parallelizer_skill.agent_monitor import AgentMonitor, AgentState, AgentHeartbeat
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestAgentMonitor:
    """Test agent state machine and monitoring."""

    @pytest.fixture
    def monitor(self):
        """Create fresh monitor for each test."""
        reset_config()
        return AgentMonitor()

    def test_spawn_agent_creates_status(self, monitor):
        """Test spawning new agent creates status."""
        monitor.spawn_agent("agent_1", "task_1")
        assert "agent_1" in monitor.agents
        assert monitor.agents["agent_1"].state == AgentState.SPAWNED

    def test_spawn_agent_duplicate_raises_error(self, monitor):
        """Test spawning duplicate agent raises error."""
        monitor.spawn_agent("agent_1", "task_1")
        with pytest.raises(ValueError):
            monitor.spawn_agent("agent_1", "task_2")

    def test_spawn_agent_max_agents_respected(self, monitor):
        """Test max agents limit is enforced."""
        max_agents = monitor.config.orchestration.max_concurrent_agents
        # Spawn max agents (not running yet)
        for i in range(max_agents):
            monitor.spawn_agent(f"agent_{i}", f"task_{i}")

        # Try to spawn beyond limit (while agents are running)
        for i in range(max_agents):
            agent = monitor.agents[f"agent_{i}"]
            agent.state = AgentState.RUNNING

        with pytest.raises(RuntimeError):
            monitor.spawn_agent("extra", "task_extra")

    def test_record_heartbeat_updates_status(self, monitor):
        """Test heartbeat updates agent status."""
        monitor.spawn_agent("agent_1", "task_1")
        heartbeat = AgentHeartbeat(
            agent_id="agent_1",
            task_id="task_1",
            status=AgentState.RUNNING,
            tokens_consumed=500,
            last_action="processing",
        )
        monitor.record_heartbeat(heartbeat)
        agent = monitor.agents["agent_1"]
        assert agent.state == AgentState.RUNNING
        assert agent.tokens_consumed == 500

    def test_agent_is_alive_with_recent_heartbeat(self, monitor):
        """Test agent is alive with recent heartbeat."""
        monitor.spawn_agent("agent_1", "task_1")
        monitor.agents["agent_1"].last_heartbeat = datetime.utcnow()
        assert monitor.agents["agent_1"].is_alive()

    def test_agent_is_dead_with_old_heartbeat(self, monitor):
        """Test agent is dead with stale heartbeat."""
        monitor.spawn_agent("agent_1", "task_1")
        old_time = datetime.utcnow() - timedelta(seconds=60)
        monitor.agents["agent_1"].last_heartbeat = old_time
        assert not monitor.agents["agent_1"].is_alive(heartbeat_timeout=30)

    def test_check_agent_health_detects_crash(self, monitor):
        """Test health check detects crashed agent."""
        monitor.spawn_agent("agent_1", "task_1")
        agent = monitor.agents["agent_1"]
        agent.state = AgentState.RUNNING
        agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)

        state = monitor.check_agent_health("agent_1")
        assert state == AgentState.CRASHED
        assert agent.error_message is not None

    def test_check_agent_health_detects_timeout(self, monitor):
        """Test health check detects timeout."""
        monitor.spawn_agent("agent_1", "task_1")
        agent = monitor.agents["agent_1"]
        agent.state = AgentState.RUNNING
        # Simulate long execution
        agent.created_at = datetime.utcnow() - timedelta(minutes=20)

        state = monitor.check_agent_health("agent_1")
        assert state == AgentState.TIMEOUT
        assert agent.error_message is not None

    def test_get_running_agents(self, monitor):
        """Test getting list of running agents."""
        monitor.spawn_agent("agent_1", "task_1")
        monitor.spawn_agent("agent_2", "task_2")

        monitor.agents["agent_1"].state = AgentState.RUNNING
        monitor.agents["agent_2"].state = AgentState.COMPLETE

        running = monitor.get_running_agents()
        assert len(running) == 1
        assert "agent_1" in running

    def test_get_failed_agents(self, monitor):
        """Test getting list of failed agents."""
        monitor.spawn_agent("agent_1", "task_1")
        monitor.spawn_agent("agent_2", "task_2")

        monitor.agents["agent_1"].state = AgentState.CRASHED
        monitor.agents["agent_2"].state = AgentState.COMPLETE

        failed = monitor.get_failed_agents()
        assert len(failed) == 1
        assert "agent_1" in failed

    def test_get_available_slots(self, monitor):
        """Test available agent slots calculation."""
        max_agents = monitor.config.orchestration.max_concurrent_agents

        monitor.spawn_agent("agent_1", "task_1")
        monitor.agents["agent_1"].state = AgentState.RUNNING

        available = monitor.get_available_slots()
        assert available == max_agents - 1

    def test_mark_complete_updates_status(self, monitor):
        """Test marking agent as complete."""
        monitor.spawn_agent("agent_1", "task_1")
        monitor.mark_complete("agent_1", 2500)

        agent = monitor.agents["agent_1"]
        assert agent.state == AgentState.COMPLETE
        assert agent.tokens_consumed == 2500

    def test_mark_failed_updates_status(self, monitor):
        """Test marking agent as failed."""
        monitor.spawn_agent("agent_1", "task_1")
        monitor.mark_failed("agent_1", "Connection timeout")

        agent = monitor.agents["agent_1"]
        assert agent.state == AgentState.FAILED
        assert "timeout" in agent.error_message.lower()

    def test_execution_time_calculation(self, monitor):
        """Test execution time calculation."""
        monitor.spawn_agent("agent_1", "task_1")
        agent = monitor.agents["agent_1"]
        agent.created_at = datetime.utcnow() - timedelta(seconds=30)

        exec_time = agent.execution_time()
        assert 29 <= exec_time.total_seconds() <= 31
