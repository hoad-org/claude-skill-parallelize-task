"""Configuration system with 4-level hierarchy (code → master → repo → env)."""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class OrchestrationConfig:
    """Orchestration settings."""

    max_concurrent_agents: int = 6
    max_task_depth: int = 3
    max_execution_time_minutes: int = 60
    per_task_timeout_minutes: int = 15
    heartbeat_interval_seconds: int = 5
    heartbeat_timeout_seconds: int = 30
    state_dir: str = "orchestration_state"


@dataclass
class TokenBudgetConfig:
    """Token and cost budget settings."""

    global_ceiling_per_run: int = 100_000
    per_agent_ceiling: int = 50_000
    reserved_capacity_percent: int = 10
    cost_limit_daily_usd: float = 1.00
    cost_limit_monthly_usd: float = 30.00
    token_safety_margin_percent: int = 20


@dataclass
class ModelSelectionConfig:
    """Model selection strategy."""

    haiku_complexity_limit: int = 4
    sonnet_complexity_limit: int = 8
    haiku_confidence_threshold: float = 0.90
    sonnet_confidence_threshold: float = 0.85
    escalation_fallback: bool = True
    max_escalations_per_task: int = 2


@dataclass
class ThinkingLevelConfig:
    """Extended thinking strategy."""

    deterministic_thinking: bool = False
    novel_problem_thinking: bool = True
    prod_risk_thinking: bool = True
    thinking_cost_multiplier: float = 3.0
    budget_threshold_for_thinking: float = 0.5


@dataclass
class OutputPatternConfig:
    """Output coordination patterns."""

    code_pattern: str = "pr_model"
    analysis_pattern: str = "scratchpad_model"
    data_pattern: str = "api_model"
    chained_pattern: str = "hierarchical_model"


@dataclass
class GuardrailsConfig:
    """Safety guardrails."""

    circuit_breaker_failure_threshold: int = 3
    health_check_interval_seconds: int = 300
    cost_override_gate: bool = True
    agent_limit_override_gate: bool = True
    stage_gate_timeout_minutes: int = 2


@dataclass
class SkillConfig:
    """Complete skill configuration."""

    orchestration: OrchestrationConfig = field(default_factory=OrchestrationConfig)
    token_budget: TokenBudgetConfig = field(default_factory=TokenBudgetConfig)
    model_selection: ModelSelectionConfig = field(default_factory=ModelSelectionConfig)
    thinking_levels: ThinkingLevelConfig = field(default_factory=ThinkingLevelConfig)
    output_patterns: OutputPatternConfig = field(default_factory=OutputPatternConfig)
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "SkillConfig":
        """Create config from dictionary (for JSON loading)."""
        return cls(
            orchestration=OrchestrationConfig(**data.get("orchestration", {})),
            token_budget=TokenBudgetConfig(**data.get("token_budget", {})),
            model_selection=ModelSelectionConfig(**data.get("model_selection", {})),
            thinking_levels=ThinkingLevelConfig(**data.get("thinking_levels", {})),
            output_patterns=OutputPatternConfig(**data.get("output_patterns", {})),
            guardrails=GuardrailsConfig(**data.get("guardrails", {})),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "orchestration": asdict(self.orchestration),
            "token_budget": asdict(self.token_budget),
            "model_selection": asdict(self.model_selection),
            "thinking_levels": asdict(self.thinking_levels),
            "output_patterns": asdict(self.output_patterns),
            "guardrails": asdict(self.guardrails),
        }


class ConfigLoader:
    """Load configuration from 4-level hierarchy: code → master → repo → env."""

    # Level 1: Code defaults
    DEFAULT_CONFIG = SkillConfig()

    # Level 2: Master config (~/.claude/parallelize-task/config.json)
    MASTER_CONFIG_DIR = Path.home() / ".claude" / "parallelize-task"
    MASTER_CONFIG_FILE = MASTER_CONFIG_DIR / "config.json"

    # Level 3: Repo config (.claude/parallelize-task.json)
    REPO_CONFIG_FILE = Path(".claude") / "parallelize-task.json"

    # Level 4: Environment variables (PARALLELIZE_TASK_*)
    ENV_PREFIX = "PARALLELIZE_TASK_"

    @classmethod
    def load(cls) -> SkillConfig:
        """Load config from 4-level hierarchy (highest priority wins)."""
        config = cls.DEFAULT_CONFIG

        # Level 2: Master config
        if cls.MASTER_CONFIG_FILE.exists():
            config = cls._merge_configs(config, cls._load_json(cls.MASTER_CONFIG_FILE))

        # Level 3: Repo config
        if cls.REPO_CONFIG_FILE.exists():
            config = cls._merge_configs(config, cls._load_json(cls.REPO_CONFIG_FILE))

        # Level 4: Environment variables
        config = cls._apply_env_overrides(config)

        return config

    @staticmethod
    def _load_json(path: Path) -> SkillConfig:
        """Load JSON config file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return SkillConfig.from_dict(data)
        except Exception as e:
            raise ValueError(f"Failed to load config from {path}: {e}")

    @staticmethod
    def _merge_configs(base: SkillConfig, override: SkillConfig) -> SkillConfig:
        """Deep merge two configs (override takes precedence)."""
        base_dict = base.to_dict()
        override_dict = override.to_dict()

        def deep_merge(d1: dict, d2: dict) -> dict:
            for key, value in d2.items():
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    d1[key] = deep_merge(d1[key], value)
                else:
                    d1[key] = value
            return d1

        merged = deep_merge(base_dict, override_dict)
        return SkillConfig.from_dict(merged)

    @staticmethod
    def _apply_env_overrides(config: SkillConfig) -> SkillConfig:
        """Apply environment variable overrides (highest priority)."""
        env_dict = {}

        for key, value in os.environ.items():
            if key.startswith(ConfigLoader.ENV_PREFIX):
                # Extract nested key: PARALLELIZE_TASK_ORCHESTRATION_MAX_AGENTS → orchestration.max_agents
                relative_key = key[len(ConfigLoader.ENV_PREFIX) :].lower()
                parts = relative_key.split("_", 1)  # Split on first underscore

                if len(parts) == 2:
                    section, param = parts
                    if section not in env_dict:
                        env_dict[section] = {}
                    # Convert env param name to snake_case
                    env_dict[section][param] = ConfigLoader._parse_value(value)

        if env_dict:
            config = ConfigLoader._merge_configs(config, SkillConfig.from_dict(env_dict))

        return config

    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        if value.lower() in ("true", "yes"):
            return True
        if value.lower() in ("false", "no"):
            return False
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value


def get_config() -> SkillConfig:
    """Get loaded configuration (cached on first call)."""
    if not hasattr(get_config, "_config"):
        get_config._config = ConfigLoader.load()
    return get_config._config


def reset_config() -> None:
    """Reset cached configuration (for testing)."""
    if hasattr(get_config, "_config"):
        delattr(get_config, "_config")
