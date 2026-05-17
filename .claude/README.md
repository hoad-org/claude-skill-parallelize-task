# Claude Parallelize-Task Skill: Development Guide

**Welcome to the intelligent task parallelization skill!** This document is your starting point for any Claude session working on this repository.

## 🚀 Quick Start (5 minutes)

1. **Read this file** (you're here!)
2. **Open ONBOARDING.md** for session setup
3. **Check ARCHITECTURE.md** for system overview
4. **Review INTEGRATIONS.md** for DevArmor/infrastructure links

Then proceed with your task.

---

## Project Overview

**Claude Parallelize-Task** is a production-grade intelligent task parallelization system that analyzes workflows, makes optimization decisions, and orchestrates parallel execution across cloud providers.

| Aspect | Details |
|--------|---------|
| **Status** | ✅ Production Ready (Phase 6 Complete) |
| **Version** | 1.1.0 |
| **Release Date** | 2026-05-17 |
| **Test Coverage** | 89.78% (559 tests) |
| **Python** | 3.12+ |
| **License** | MIT |

---

## What This System Does

### Core Capabilities
- **Q1-Q6 Decision Engine**: Questionnaire-driven parallelization strategy selection
- **Complexity Scoring**: Task complexity analysis with feasibility ratings
- **Orchestration**: DAG-based workflow execution planning
- **Performance Optimization**: LRU caching, memoization, batch optimization
- **Enterprise Monitoring**: Metrics collection, event logging, health checks, alerting
- **REST API**: 27 production endpoints with WebSocket real-time updates
- **Web Dashboard**: 7-page Vue.js 3 SPA with dark mode
- **Container Deployment**: Docker, Kubernetes, Helm with CI/CD automation

### Integration Points
- **DevArmor**: Cost governance, resource enforcement (see INTEGRATIONS.md)
- **Kubernetes**: Native K8s deployment with RBAC, network policies, HPA
- **Cloud Providers**: AWS, GCP, Azure (tested via CloudCTL)
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **CI/CD**: GitHub Actions with semantic versioning, multi-arch builds

---

## Directory Structure

```
.claude/
├── README.md                    ← You are here
├── ONBOARDING.md               ← Session setup checklist
├── ARCHITECTURE.md             ← System design & components
├── DEVELOPMENT.md              ← How to continue developing
├── INTEGRATIONS.md             ← DevArmor, CloudCTL, Confluence
└── TESTING.md                  ← Test strategy & commands

src/parallelizer_skill/
├── __init__.py
├── models.py                   ← Data models (Pydantic)
├── config.py                   ← 4-level config hierarchy
├── decision_engine.py          ← Q1-Q6 questionnaire logic
├── complexity.py               ← Task complexity scoring
├── dag_analyzer.py             ← DAG analysis & topological sort
├── orchestrator.py             ← Main workflow coordination
├── performance.py              ← Caching, optimization, memoization
├── monitoring.py               ← Metrics, events, alerts, health checks
├── api.py                      ← FastAPI 27 endpoints
├── cli.py                      ← Command-line interface
└── [8 more modules]

tests/
├── unit/                       ← 40+ unit test files
├── integration/                ← End-to-end workflows
├── performance_benchmarks.py   ← 32 benchmark cases
├── smoke_tests.py              ← 40+ production checks
├── load_tests.py               ← 30+ concurrency scenarios
└── security_tests.py           ← 35+ security validations

frontend/
├── src/pages/                  ← 7 Vue.js pages
├── src/stores/                 ← Pinia state management
├── src/services/               ← API & WebSocket clients
└── dist/                       ← Built static assets

k8s/                            ← 6 K8s manifests
helm/                           ← Helm chart + values
scripts/                        ← 10 deployment scripts
docs/                           ← 18 markdown guides
```

---

## Essential Commands

### Development
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (559 tests)
make test

# Check coverage (must be >85%)
make coverage

# Quality checks (lint, format, type-check)
make check

# Run specific test class
pytest tests/test_decision_engine.py::TestDecisionEngine -v

# Generate API docs
python -c "from src.parallelizer_skill.api import create_app; app = create_app()"
# Then visit http://localhost:8000/docs
```

### Deployment
```bash
# Build Docker image
make docker-build

# Deploy to Kubernetes
make k8s-deploy

# Deploy with Helm
make helm-deploy

# Run health checks
scripts/health-check.sh

# Dry-run pre-deployment checks
scripts/pre-deploy-checks.sh --dry-run
```

---

## Key Design Decisions

### Architecture
- **3-Pillar Design**: CLI layer, config layer (4-level hierarchy), guardrails layer
- **Separation of Concerns**: Decision engine, complexity scorer, orchestrator, monitoring are independent
- **Async-First**: FastAPI with async/await, WebSocket support for real-time updates
- **Stateless Services**: Horizontally scalable via Kubernetes

### Configuration
- **4-Level Hierarchy**: Defaults → Master config → Repo config → Environment variables
- **Environment-Specific**: dev.env, staging.env, production.env
- **Secret Management**: Kubernetes secrets, .env.example pattern (no secrets in git)

### Testing
- **>85% Coverage**: 559 tests across unit, integration, performance, smoke, load, security
- **Pytest + AsyncIO**: Full async/await test support
- **Fixture-Based**: Reusable test fixtures for common workflows

### Monitoring
- **6 Alert Types**: Performance degradation, high failure rate, excessive escalations, cache thrashing, resource exhaustion, health check failure
- **Event Logging**: 39 event types with 4 severity levels
- **Health Monitoring**: 3-state health model (HEALTHY/DEGRADED/UNHEALTHY)

---

## Before You Start

### ✅ Pre-Session Checklist

- [ ] Read ONBOARDING.md (5 min)
- [ ] Run `make check` to verify all quality gates pass
- [ ] Check `pytest tests/ -q` shows 559 tests passing
- [ ] Verify coverage ≥85% with `make coverage`
- [ ] Review git log to understand recent changes: `git log --oneline -10`
- [ ] Check available macOS memory before spawning agents: `vm_stat`
- [ ] If continuing previous work, read the relevant Phase documentation

### ⚠️ Known Constraints

1. **Memory Management**: Use sequential agent pattern, not parallel (see ONBOARDING.md)
2. **Python 3.12+**: Required for type hints and async features
3. **No Hardcoded Secrets**: All credentials must be environment variables
4. **Test Coverage**: Never commit code with coverage < 85%

### 🔗 Critical External Resources

| Resource | Link | Purpose |
|----------|------|---------|
| Official Rail | [Confluence Rail](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/25165826/) | How Claude should use cloudctl/infrastructure |
| DevArmor Status | [Memory](/Users/craighoad/.claude/projects/-Users-craighoad-Repos/memory/MEMORY.md#devarmor) | Cost governance, enforcement rules |
| CloudCTL Docs | [Solution Doc](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/25165826/) | Cloud provider integration |
| Jira Skill | `/Repos/jira-skill` | Reference implementation (100% coverage) |
| Git Workflow | Memory/feedback_git_no_verify.md | Always use --no-verify, [skip ci] |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-05-17 | Phase 6: Containerization, API, Dashboard, Deployment |
| 1.0.0 | 2026-05-15 | Phase 5: Performance optimization, monitoring |
| 0.9.0 | 2026-05-14 | Phase 4: Orchestration, CLI integration |
| 0.8.0 | 2026-05-13 | Phase 3: Decision engine, strategy generation |
| 0.7.0 | 2026-05-12 | Phase 2: Resilience, complexity, callbacks |
| 0.5.0 | 2026-05-10 | Phase 1: Core models, basic scoring |

---

## Next Steps

1. **First Time?** → Read ONBOARDING.md next
2. **Continuing Work?** → Check DEVELOPMENT.md for your task
3. **Understanding System?** → Start with ARCHITECTURE.md
4. **Working on Integration?** → See INTEGRATIONS.md
5. **Writing Tests?** → Review TESTING.md

---

## Support & Reference

- **Tests**: `pytest tests/ -v` to see all 559 test cases
- **Coverage**: `make coverage` for detailed coverage report
- **API Docs**: Run `python -m uvicorn src.parallelizer_skill.api:create_app --reload` then visit `/docs`
- **Git History**: `git log --all --graph --oneline` for full context
- **Issues**: Check `git log` for recent commits and error patterns

---

**Last Updated**: 2026-05-17  
**Maintained by**: Claude Code  
**Repository**: `/Users/craighoad/Repos/claude-skill-parallelize-task`
