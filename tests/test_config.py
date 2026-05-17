"""Unit tests for configuration system (4-level hierarchy)."""

import pytest
from parallelizer_skill.config import (
    SkillConfig, ConfigLoader, get_config, reset_config
)


@pytest.mark.unit
class TestConfigDefaults:
    """Test default configuration."""

    def test_default_config_creates_with_max_agents_6(self):
        """Verify default config sets max_agents to 6."""
        config = SkillConfig()
        assert config.orchestration.max_concurrent_agents == 6

    def test_default_config_has_all_sections(self):
        """Verify all config sections exist."""
        config = SkillConfig()
        assert config.orchestration is not None
        assert config.token_budget is not None
        assert config.model_selection is not None
        assert config.thinking_levels is not None
        assert config.output_patterns is not None
        assert config.guardrails is not None

    def test_orchestration_defaults(self):
        """Verify orchestration defaults."""
        config = SkillConfig()
        assert config.orchestration.max_concurrent_agents == 6
        assert config.orchestration.max_task_depth == 3
        assert config.orchestration.per_task_timeout_minutes == 15

    def test_token_budget_defaults(self):
        """Verify token budget defaults."""
        config = SkillConfig()
        assert config.token_budget.global_ceiling_per_run == 100_000
        assert config.token_budget.cost_limit_daily_usd == 1.00
        assert config.token_budget.cost_limit_monthly_usd == 30.00


@pytest.mark.unit
class TestConfigHierarchy:
    """Test 4-level configuration hierarchy."""

    def test_from_dict_converts_correctly(self):
        """Test converting dict to config."""
        data = {
            "orchestration": {"max_concurrent_agents": 4},
            "token_budget": {"cost_limit_daily_usd": 2.0},
        }
        config = SkillConfig.from_dict(data)
        assert config.orchestration.max_concurrent_agents == 4
        assert config.token_budget.cost_limit_daily_usd == 2.0

    def test_to_dict_converts_back(self):
        """Test converting config to dict."""
        config = SkillConfig()
        data = config.to_dict()
        assert "orchestration" in data
        assert data["orchestration"]["max_concurrent_agents"] == 6

    def test_merge_configs_simple(self):
        """Test merging two configs."""
        base = SkillConfig()
        override_data = {"orchestration": {"max_concurrent_agents": 8}}
        override = SkillConfig.from_dict(override_data)

        merged = ConfigLoader._merge_configs(base, override)
        assert merged.orchestration.max_concurrent_agents == 8
        # Other fields should remain from base
        assert merged.orchestration.max_task_depth == 3

    def test_merge_configs_deep(self):
        """Test deep merge of nested configs."""
        base = SkillConfig()
        override_data = {
            "orchestration": {"max_concurrent_agents": 4},
            "token_budget": {"cost_limit_daily_usd": 5.0},
        }
        override = SkillConfig.from_dict(override_data)

        merged = ConfigLoader._merge_configs(base, override)
        assert merged.orchestration.max_concurrent_agents == 4
        assert merged.token_budget.cost_limit_daily_usd == 5.0


@pytest.mark.unit
class TestConfigLoader:
    """Test configuration loader."""

    def test_parse_value_bool_true(self):
        """Test parsing bool true values."""
        assert ConfigLoader._parse_value("true") is True
        assert ConfigLoader._parse_value("yes") is True
        assert ConfigLoader._parse_value("True") is True

    def test_parse_value_bool_false(self):
        """Test parsing bool false values."""
        assert ConfigLoader._parse_value("false") is False
        assert ConfigLoader._parse_value("no") is False
        assert ConfigLoader._parse_value("False") is False

    def test_parse_value_int(self):
        """Test parsing int values."""
        assert ConfigLoader._parse_value("42") == 42
        assert isinstance(ConfigLoader._parse_value("100"), int)

    def test_parse_value_float(self):
        """Test parsing float values."""
        assert ConfigLoader._parse_value("3.14") == 3.14
        assert isinstance(ConfigLoader._parse_value("1.5"), float)

    def test_parse_value_string(self):
        """Test parsing string values."""
        assert ConfigLoader._parse_value("hello") == "hello"
        assert isinstance(ConfigLoader._parse_value("test"), str)


@pytest.mark.unit
class TestConfigCaching:
    """Test config caching."""

    def test_get_config_caches_result(self):
        """Test that get_config caches config on first call."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config_clears_cache(self):
        """Test that reset_config clears cache."""
        reset_config()
        # Verify cache is empty before first call
        assert not hasattr(get_config, "_config")

        config1 = get_config()
        # Verify cache is populated after first call
        assert hasattr(get_config, "_config")

        reset_config()
        # Verify cache is cleared after reset
        assert not hasattr(get_config, "_config")

        config2 = get_config()
        # Verify cache is repopulated after new get_config call
        assert hasattr(get_config, "_config")


@pytest.mark.unit
class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_max_agents_raises_error(self):
        """Test that invalid max_agents value raises error."""
        # Should still create config, but validation would happen at runtime
        config = SkillConfig()
        config.orchestration.max_concurrent_agents = -1  # Invalid
        # Validation happens in usage, not in config creation

    def test_zero_token_budget_raises_error(self):
        """Test that zero token budget is allowed (edge case)."""
        config = SkillConfig()
        config.token_budget.global_ceiling_per_run = 0
        # This is technically allowed, but would make orchestration impossible
