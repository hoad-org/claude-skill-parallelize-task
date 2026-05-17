"""Token budget management and cost enforcement (GAP 2)."""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from datetime import datetime
from parallelizer_skill.config import get_config


@dataclass
class TokenAllocation:
    """Token allocation for a task."""
    task_id: str
    agent_id: str
    estimated_tokens: int
    allocated_tokens: int
    consumed_tokens: int = 0
    cost_usd: float = 0.0

    def remaining(self) -> int:
        """Get remaining tokens for this agent's task."""
        return self.allocated_tokens - self.consumed_tokens

    def is_exceeded(self) -> bool:
        """Check if agent exceeded token allocation."""
        return self.consumed_tokens > self.allocated_tokens

    def utilization_percent(self) -> float:
        """Get token utilization percentage."""
        if self.allocated_tokens == 0:
            return 0.0
        return (self.consumed_tokens / self.allocated_tokens) * 100


class TokenBudgetManager:
    """Manage token budgets and cost enforcement (GAP 2)."""

    # Model costs per 1M tokens (USD)
    MODEL_COSTS = {
        "haiku": 0.80,
        "sonnet": 3.00,
        "opus": 15.00,
    }

    def __init__(self):
        """Initialize token budget manager."""
        self.config = get_config()
        self.allocations: Dict[str, TokenAllocation] = {}
        self.total_tokens_consumed: int = 0
        self.total_cost_usd: float = 0.0
        self.created_at = datetime.utcnow()
        self.daily_cost_start = datetime.utcnow()

    def allocate_budget(self, task_id: str, agent_id: str, estimated_tokens: int, model: str) -> int:
        """Allocate token budget for a task."""
        key = f"{task_id}:{agent_id}"

        # Check global ceiling
        if estimated_tokens > self.config.token_budget.global_ceiling_per_run:
            raise ValueError(
                f"Task {task_id} tokens ({estimated_tokens}) exceed global ceiling "
                f"({self.config.token_budget.global_ceiling_per_run})"
            )

        # Check per-agent ceiling
        if estimated_tokens > self.config.token_budget.per_agent_ceiling:
            raise ValueError(
                f"Task {task_id} tokens ({estimated_tokens}) exceed per-agent ceiling "
                f"({self.config.token_budget.per_agent_ceiling})"
            )

        # Apply safety margin
        safety_margin = 1.0 + (self.config.token_budget.token_safety_margin_percent / 100)
        allocated = int(estimated_tokens * safety_margin)

        # Estimate cost upfront
        cost_usd = self._calculate_cost(allocated, model)

        # Check daily budget
        if self.total_cost_usd + cost_usd > self.config.token_budget.cost_limit_daily_usd:
            raise ValueError(
                f"Task cost (${cost_usd:.4f}) would exceed daily limit "
                f"(${self.config.token_budget.cost_limit_daily_usd:.2f})"
            )

        # Create allocation
        allocation = TokenAllocation(
            task_id=task_id,
            agent_id=agent_id,
            estimated_tokens=estimated_tokens,
            allocated_tokens=allocated,
            cost_usd=cost_usd,
        )

        self.allocations[key] = allocation
        return allocated

    def record_consumption(self, task_id: str, agent_id: str, tokens: int, model: str) -> None:
        """Record token consumption from agent."""
        key = f"{task_id}:{agent_id}"

        if key not in self.allocations:
            raise ValueError(f"No allocation for {key}")

        allocation = self.allocations[key]
        allocation.consumed_tokens = tokens

        # Update actual cost
        actual_cost = self._calculate_cost(tokens, model)
        allocation.cost_usd = actual_cost

        # Update global tracking
        self.total_tokens_consumed += tokens
        self.total_cost_usd += actual_cost

    def check_budget_exceeded(self, task_id: str, agent_id: str) -> Tuple[bool, Optional[str]]:
        """Check if agent exceeded token budget."""
        key = f"{task_id}:{agent_id}"

        if key not in self.allocations:
            return False, None

        allocation = self.allocations[key]

        if allocation.is_exceeded():
            msg = (
                f"Agent {agent_id} consumed {allocation.consumed_tokens} tokens, "
                f"allocated {allocation.allocated_tokens}"
            )
            return True, msg

        return False, None

    def check_cost_limit(self) -> Tuple[bool, Optional[str]]:
        """Check if daily cost limit exceeded."""
        if self.total_cost_usd > self.config.token_budget.cost_limit_daily_usd:
            msg = (
                f"Total cost ${self.total_cost_usd:.4f} exceeds daily limit "
                f"${self.config.token_budget.cost_limit_daily_usd:.2f}"
            )
            return True, msg

        return False, None

    def get_remaining_budget(self) -> float:
        """Get remaining budget (USD) for today."""
        return self.config.token_budget.cost_limit_daily_usd - self.total_cost_usd

    def get_allocation_status(self, task_id: str, agent_id: str) -> Optional[TokenAllocation]:
        """Get allocation status for a task."""
        key = f"{task_id}:{agent_id}"
        return self.allocations.get(key)

    def get_total_status(self) -> Dict:
        """Get overall budget status."""
        return {
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "remaining_budget_usd": round(self.get_remaining_budget(), 4),
            "daily_limit_usd": self.config.token_budget.cost_limit_daily_usd,
            "allocations_count": len(self.allocations),
        }

    @staticmethod
    def _calculate_cost(tokens: int, model: str) -> float:
        """Calculate cost in USD for tokens."""
        rate = TokenBudgetManager.MODEL_COSTS.get(model.lower(), 3.00)  # Default to Sonnet
        return (tokens / 1_000_000) * rate

    def reset(self) -> None:
        """Reset all tracking (for testing)."""
        self.allocations.clear()
        self.total_tokens_consumed = 0
        self.total_cost_usd = 0.0
