.PHONY: test coverage lint format type-check check clean help

help:
	@echo "Available targets:"
	@echo "  test       - Run tests"
	@echo "  coverage   - Run tests and show coverage report"
	@echo "  lint       - Check code style with ruff"
	@echo "  format     - Format code with black"
	@echo "  type-check - Check types with mypy"
	@echo "  check      - Run all checks (lint, format, type-check, coverage)"
	@echo "  clean      - Remove build artifacts and cache"

test:
	python -m pytest tests/ -v

coverage:
	python -m pytest tests/ -v --cov=src/parallelizer_skill --cov-report=html --cov-report=term-missing

lint:
	python -m ruff check src/ tests/

format:
	python -m black src/ tests/ --check

type-check:
	python -m mypy src/

check: lint format type-check coverage
	@echo "✅ All checks passed!"

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
