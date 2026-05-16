"""Pytest configuration."""

import pytest


@pytest.fixture(autouse=True)
def reset_modules():
    """Reset modules between tests."""
    yield
