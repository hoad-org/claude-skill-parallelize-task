.PHONY: test coverage lint format type-check check clean help docker-build docker-push docker-compose-up docker-compose-down k8s-deploy k8s-verify helm-deploy helm-status pre-deploy-checks health-check rollback scale backup restore smoke-tests load-tests security-tests release

help:
	@echo "Available targets:"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test           - Run tests"
	@echo "  coverage       - Run tests and show coverage report"
	@echo "  lint           - Check code style with ruff"
	@echo "  format         - Format code with black"
	@echo "  type-check     - Check types with mypy"
	@echo "  check          - Run all checks (lint, format, type-check, coverage)"
	@echo "  clean          - Remove build artifacts and cache"
	@echo ""
	@echo "Deployment Testing:"
	@echo "  smoke-tests    - Run smoke tests (basic deployment verification)"
	@echo "  load-tests     - Run load tests (performance under load)"
	@echo "  security-tests - Run security tests (vulnerability checks)"
	@echo ""
	@echo "Pre-Deployment:"
	@echo "  pre-deploy-checks - Run all pre-deployment validation"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build         - Build Docker image"
	@echo "  docker-push          - Push Docker image to registry"
	@echo "  docker-compose-up    - Start services with Docker Compose"
	@echo "  docker-compose-down  - Stop services"
	@echo ""
	@echo "Kubernetes:"
	@echo "  k8s-deploy - Deploy to Kubernetes cluster"
	@echo "  k8s-verify - Verify Kubernetes deployment"
	@echo ""
	@echo "Helm:"
	@echo "  helm-deploy - Deploy using Helm chart"
	@echo "  helm-status - Check Helm release status"
	@echo ""
	@echo "Operations:"
	@echo "  health-check - Check deployment health"
	@echo "  rollback     - Rollback to previous version"
	@echo "  scale        - Scale deployment replicas"
	@echo "  backup       - Backup deployment state"
	@echo "  restore      - Restore from backup"
	@echo ""
	@echo "Release:"
	@echo "  release - Create release version"

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

.PHONY: install-hooks
install-hooks:
	@echo "Installing git hooks..."
	@mkdir -p .git-hooks-local
	@if [ -f .claude/pre-commit-hook-template.sh ]; then \
		cp .claude/pre-commit-hook-template.sh .git-hooks-local/pre-commit; \
		chmod +x .git-hooks-local/pre-commit; \
		git config core.hooksPath .git-hooks-local; \
		echo "✅ Git hooks installed"; \
	else \
		echo "⚠️  Hook template not found at .claude/pre-commit-hook-template.sh"; \
	fi

.PHONY: setup
setup: install-hooks
	@echo "✅ Development environment ready"

# Docker targets
.PHONY: docker-build
docker-build:
	@./scripts/build.sh

.PHONY: docker-push
docker-push:
	@./scripts/push.sh

.PHONY: docker-compose-up
docker-compose-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d
	@echo "✅ Services started"
	@echo "Services:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Prometheus: http://localhost:9091"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Redis: localhost:6379"

.PHONY: docker-compose-down
docker-compose-down:
	@echo "Stopping services..."
	docker-compose down
	@echo "✅ Services stopped"

# Kubernetes targets
.PHONY: k8s-deploy
k8s-deploy:
	@./scripts/deploy.sh

.PHONY: k8s-verify
k8s-verify:
	@echo "Checking Kubernetes deployment..."
	kubectl get pods -l app=parallelizer
	kubectl get svc -l app=parallelizer
	kubectl get ingress

# Helm targets
.PHONY: helm-deploy
helm-deploy:
	@./scripts/helm-deploy.sh

.PHONY: helm-status
helm-status:
	@helm status parallelizer || echo "Release not installed"
	@helm list | grep parallelizer || echo "No parallelizer releases found"

# Pre-deployment validation
.PHONY: pre-deploy-checks
pre-deploy-checks:
	@echo "Running pre-deployment validation..."
	@bash ./scripts/pre-deploy-checks.sh

# Operations targets
.PHONY: health-check
health-check:
	@bash ./scripts/health-check.sh $(NAMESPACE) $(ENVIRONMENT)

.PHONY: rollback
rollback:
	@bash ./scripts/rollback.sh $(NAMESPACE) $(REVISION) $(DRY_RUN)

.PHONY: scale
scale:
	@bash ./scripts/scale.sh $(NAMESPACE) $(OPERATION) $(REPLICAS) $(ENVIRONMENT)

.PHONY: backup
backup:
	@bash ./scripts/backup.sh $(NAMESPACE) $(BACKUP_DIR) $(RETENTION)

.PHONY: restore
restore:
	@bash ./scripts/restore.sh $(NAMESPACE) $(BACKUP_ARCHIVE) $(DRY_RUN)

# Testing targets
.PHONY: smoke-tests
smoke-tests:
	python -m pytest tests/smoke_tests.py -v

.PHONY: load-tests
load-tests:
	python -m pytest tests/load_tests.py -v

.PHONY: security-tests
security-tests:
	python -m pytest tests/security_tests.py -v

# Release target
.PHONY: release
release:
	@echo "Creating release..."
	@bash -c 'VERSION=$$(grep "^version = " pyproject.toml | cut -d'"' -f2) && echo "Release version: $$VERSION"'
