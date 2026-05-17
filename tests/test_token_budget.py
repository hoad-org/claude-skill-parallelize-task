"""Unit tests for token budget management (GAP 2)."""

import pytest
from parallelizer_skill.token_budget import TokenAllocation, TokenBudgetManager
from parallelizer_skill.config import reset_config


@pytest.mark.unit
class TestTokenAllocation:
    """Test token allocation tracking."""

    def test_allocation_remaining_tokens(self):
        """Test remaining tokens calculation."""
        alloc = TokenAllocation(
            task_id="task_1",
            agent_id="agent_1",
            estimated_tokens=1000,
            allocated_tokens=1200,
            consumed_tokens=500,
        )
        assert alloc.remaining() == 700

    def test_allocation_remaining_zero(self):
        """Test remaining when fully consumed."""
        alloc = TokenAllocation(
            task_id="task_1",
            agent_id="agent_1",
            estimated_tokens=1000,
            allocated_tokens=1000,
            consumed_tokens=1000,
        )
        assert alloc.remaining() == 0

    def test_allocation_not_exceeded(self):
        """Test is_exceeded when within budget."""
        alloc = TokenAllocation(
            task_id="task_1",
            agent_id="agent_1",
            estimated_tokens=1000,
            allocated_tokens=1200,
            consumed_tokens=1000,
        )
        assert not alloc.is_exceeded()

    def test_allocation_exceeded(self):
        """Test is_exceeded when over budget."""
        alloc = TokenAllocation(
            task_id="task_1",
            agent_id="agent_1",
            estimated_tokens=1000,
            allocated_tokens=1000,
            consumed_tokens=1100,
        )
        assert alloc.is_exceeded()

    def test_utilization_percent(self):
        """Test utilization percentage calculation."""
        alloc = TokenAllocation(
            task_id="task_1",
            agent_id="agent_1",
            estimated_tokens=1000,
            allocated_tokens=1000,
            consumed_tokens=500,
        )
        assert alloc.utilization_percent() == 50.0

    def test_utilization_percent_over_100(self):
        """Test utilization when exceeded."""
        alloc = TokenAllocation(
            task_id="task_1",
            agent_id="agent_1",
            estimated_tokens=1000,
            allocated_tokens=1000,
            consumed_tokens=1500,
        )
        assert alloc.utilization_percent() == 150.0

    def test_utilization_percent_zero_allocation(self):
        """Test utilization with zero allocation."""
        alloc = TokenAllocation(
            task_id="task_1",
            agent_id="agent_1",
            estimated_tokens=0,
            allocated_tokens=0,
            consumed_tokens=0,
        )
        assert alloc.utilization_percent() == 0.0


@pytest.mark.unit
class TestTokenBudgetManager:
    """Test token budget management."""

    @pytest.fixture
    def manager(self):
        """Create fresh manager for each test."""
        reset_config()
        return TokenBudgetManager()

    def test_allocate_budget_within_limits(self, manager):
        """Test allocating budget within all limits."""
        allocated = manager.allocate_budget("task_1", "agent_1", 10000, "sonnet")
        assert allocated > 10000  # With safety margin
        assert "task_1:agent_1" in manager.allocations

    def test_allocate_budget_applies_safety_margin(self, manager):
        """Test that safety margin is applied."""
        estimated = 10000
        allocated = manager.allocate_budget("task_1", "agent_1", estimated, "sonnet")
        # Default safety margin is 20% (from config)
        expected = int(estimated * 1.20)
        assert allocated == expected

    def test_allocate_budget_exceeds_global_ceiling(self, manager):
        """Test allocation fails if exceeds global ceiling."""
        global_ceiling = manager.config.token_budget.global_ceiling_per_run
        with pytest.raises(ValueError):
            manager.allocate_budget("task_1", "agent_1", global_ceiling + 1, "sonnet")

    def test_allocate_budget_exceeds_per_agent_ceiling(self, manager):
        """Test allocation fails if exceeds per-agent ceiling."""
        per_agent_ceiling = manager.config.token_budget.per_agent_ceiling
        with pytest.raises(ValueError):
            manager.allocate_budget("task_1", "agent_1", per_agent_ceiling + 1, "sonnet")

    def test_allocate_budget_exceeds_daily_cost(self, manager):
        """Test allocation fails if exceeds daily cost limit when consuming."""
        # Allocate and consume multiple times to exceed daily limit
        # With opus at $15/1M tokens, daily limit of $1
        # 50k tokens * 1.2 margin = 60k tokens, cost = $0.90

        manager.allocate_budget("task_1", "agent_1", 50000, "opus")
        manager.record_consumption("task_1", "agent_1", 50000, "opus")
        # After consumption: total_cost_usd = $0.75

        # Try to allocate another 50k which would push total to $1.50
        # Note: allocate_budget checks total_cost_usd + estimated_cost
        with pytest.raises(ValueError):
            manager.allocate_budget("task_2", "agent_2", 50000, "opus")

    def test_record_consumption_updates_tokens(self, manager):
        """Test recording token consumption."""
        manager.allocate_budget("task_1", "agent_1", 10000, "sonnet")
        manager.record_consumption("task_1", "agent_1", 5000, "sonnet")

        alloc = manager.get_allocation_status("task_1", "agent_1")
        assert alloc.consumed_tokens == 5000
        assert manager.total_tokens_consumed == 5000

    def test_record_consumption_calculates_cost(self, manager):
        """Test that consumption updates cost."""
        manager.allocate_budget("task_1", "agent_1", 50000, "sonnet")
        manager.record_consumption("task_1", "agent_1", 50000, "sonnet")

        # Sonnet: 50k tokens = $0.15
        alloc = manager.get_allocation_status("task_1", "agent_1")
        assert abs(alloc.cost_usd - 0.15) < 0.01

    def test_record_consumption_unknown_allocation(self, manager):
        """Test consuming from unknown allocation raises error."""
        with pytest.raises(ValueError):
            manager.record_consumption("task_1", "agent_1", 1000, "sonnet")

    def test_check_budget_not_exceeded(self, manager):
        """Test budget check when within limits."""
        manager.allocate_budget("task_1", "agent_1", 10000, "sonnet")
        manager.record_consumption("task_1", "agent_1", 5000, "sonnet")

        exceeded, msg = manager.check_budget_exceeded("task_1", "agent_1")
        assert not exceeded
        assert msg is None

    def test_check_budget_exceeded(self, manager):
        """Test budget check when over limits."""
        manager.allocate_budget("task_1", "agent_1", 10000, "sonnet")
        manager.record_consumption("task_1", "agent_1", 15000, "sonnet")

        exceeded, msg = manager.check_budget_exceeded("task_1", "agent_1")
        assert exceeded
        assert msg is not None
        assert "15000" in msg

    def test_check_budget_unknown_allocation(self, manager):
        """Test budget check on unknown allocation."""
        exceeded, msg = manager.check_budget_exceeded("task_1", "agent_1")
        assert not exceeded
        assert msg is None

    def test_check_cost_limit_not_exceeded(self, manager):
        """Test cost limit check when within limits."""
        manager.allocate_budget("task_1", "agent_1", 1000, "haiku")

        exceeded, msg = manager.check_cost_limit()
        assert not exceeded
        assert msg is None

    def test_check_cost_limit_exceeded(self, manager):
        """Test cost limit check when exceeded."""
        # Simulate exceeding cost (directly set total_cost_usd)
        manager.total_cost_usd = 2.0  # Over $1 default limit

        exceeded, msg = manager.check_cost_limit()
        assert exceeded
        assert msg is not None
        assert "$1.00" in msg

    def test_get_remaining_budget(self, manager):
        """Test remaining budget calculation."""
        daily_limit = manager.config.token_budget.cost_limit_daily_usd

        # Allocate and consume to actually track cost
        manager.allocate_budget("task_1", "agent_1", 10000, "haiku")
        manager.record_consumption("task_1", "agent_1", 10000, "haiku")

        remaining = manager.get_remaining_budget()
        assert remaining < daily_limit
        assert remaining > 0

    def test_get_remaining_budget_after_consumption(self, manager):
        """Test remaining budget after consumption."""
        daily_limit = manager.config.token_budget.cost_limit_daily_usd
        manager.allocate_budget("task_1", "agent_1", 50000, "haiku")
        manager.record_consumption("task_1", "agent_1", 50000, "haiku")

        remaining = manager.get_remaining_budget()
        assert remaining >= 0
        assert remaining <= daily_limit

    def test_get_allocation_status(self, manager):
        """Test getting allocation status."""
        manager.allocate_budget("task_1", "agent_1", 10000, "sonnet")

        alloc = manager.get_allocation_status("task_1", "agent_1")
        assert alloc is not None
        assert alloc.task_id == "task_1"
        assert alloc.agent_id == "agent_1"

    def test_get_allocation_status_unknown(self, manager):
        """Test getting unknown allocation."""
        alloc = manager.get_allocation_status("task_1", "agent_1")
        assert alloc is None

    def test_get_total_status(self, manager):
        """Test getting total status."""
        manager.allocate_budget("task_1", "agent_1", 10000, "sonnet")
        manager.record_consumption("task_1", "agent_1", 5000, "sonnet")

        status = manager.get_total_status()
        assert status["total_tokens_consumed"] == 5000
        assert status["total_cost_usd"] > 0
        assert status["allocations_count"] == 1

    def test_get_total_status_multiple_allocations(self, manager):
        """Test total status with multiple allocations."""
        manager.allocate_budget("task_1", "agent_1", 10000, "haiku")
        manager.allocate_budget("task_2", "agent_2", 10000, "sonnet")
        manager.record_consumption("task_1", "agent_1", 5000, "haiku")
        manager.record_consumption("task_2", "agent_2", 5000, "sonnet")

        status = manager.get_total_status()
        assert status["total_tokens_consumed"] == 10000
        assert status["allocations_count"] == 2

    def test_calculate_cost_haiku(self):
        """Test cost calculation for Haiku."""
        cost = TokenBudgetManager._calculate_cost(1000000, "haiku")
        assert abs(cost - 0.80) < 0.01

    def test_calculate_cost_sonnet(self):
        """Test cost calculation for Sonnet."""
        cost = TokenBudgetManager._calculate_cost(1000000, "sonnet")
        assert abs(cost - 3.00) < 0.01

    def test_calculate_cost_opus(self):
        """Test cost calculation for Opus."""
        cost = TokenBudgetManager._calculate_cost(1000000, "opus")
        assert abs(cost - 15.00) < 0.01

    def test_calculate_cost_partial_tokens(self):
        """Test cost calculation for partial tokens."""
        # 500k tokens at $3/1M = $1.50
        cost = TokenBudgetManager._calculate_cost(500000, "sonnet")
        assert abs(cost - 1.50) < 0.01

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation defaults to Sonnet for unknown model."""
        cost = TokenBudgetManager._calculate_cost(1000000, "unknown")
        assert abs(cost - 3.00) < 0.01

    def test_reset_clears_allocations(self, manager):
        """Test reset clears all allocations."""
        manager.allocate_budget("task_1", "agent_1", 10000, "sonnet")
        manager.allocate_budget("task_2", "agent_2", 10000, "sonnet")

        manager.reset()

        assert len(manager.allocations) == 0
        assert manager.total_tokens_consumed == 0
        assert manager.total_cost_usd == 0.0
