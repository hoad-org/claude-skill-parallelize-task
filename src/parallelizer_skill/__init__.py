"""Claude skill for intelligent task parallelization and workflow optimization."""

__version__ = "1.1.0"

from parallelizer_skill.models import Task, TaskDependency, ExecutionPlan, TaskGroup
from parallelizer_skill.optimizer import TaskOrchestrator
from parallelizer_skill.dag_analyzer import DAGAnalyzer
from parallelizer_skill.execution_planner import ExecutionPlanner
from parallelizer_skill.config import SkillConfig, ConfigLoader, get_config
from parallelizer_skill.agent_monitor import AgentMonitor, AgentState, AgentStatus
from parallelizer_skill.token_budget import TokenBudgetManager, TokenAllocation
from parallelizer_skill.stage_orchestrator import StageOrchestrator, Stage, GatePolicy
from parallelizer_skill.output_coordinator import OutputCoordinator, OutputPattern

__all__ = [
    # Models
    "Task",
    "TaskDependency",
    "ExecutionPlan",
    "TaskGroup",
    # Core
    "TaskOrchestrator",
    "DAGAnalyzer",
    "ExecutionPlanner",
    # Configuration
    "SkillConfig",
    "ConfigLoader",
    "get_config",
    # Agent monitoring (GAP 1)
    "AgentMonitor",
    "AgentState",
    "AgentStatus",
    # Token budget (GAP 2)
    "TokenBudgetManager",
    "TokenAllocation",
    # Stage orchestration (GAP 3)
    "StageOrchestrator",
    "Stage",
    "GatePolicy",
    # Output coordination (GAP 4)
    "OutputCoordinator",
    "OutputPattern",
]
