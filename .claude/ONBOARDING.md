# Session Onboarding Checklist

**Time Estimate**: 10-15 minutes for full setup  
**Purpose**: Get your Claude session ready to work on the parallelize-task skill

---

## Step 1: Environment Setup (3 min)

```bash
# Navigate to repo
cd /Users/craighoad/Repos/claude-skill-parallelize-task

# Verify Python version (must be 3.12+)
python --version

# Install dependencies (first time only)
pip install -e ".[dev]"

# Verify installation
python -c "import parallelizer_skill; print(parallelizer_skill.__version__)"
```

**Expected Output**: `1.1.0`

---

## Step 2: Verify All Quality Gates Pass (5 min)

```bash
# Run full quality check (all gates must pass)
make check

# Expected output:
# ✅ All checks passed!
# - Linting: 0 errors
# - Formatting: All formatted
# - Type checking: 0 errors
# - Tests: 559 passed
# - Coverage: 89.78% (>85% required)
```

If any fail, run individually:
```bash
make lint        # Ruff linting
make format      # Black formatting
make type-check  # MyPy type checking
make test        # Pytest suite
make coverage    # Coverage report
```

---

## Step 3: Understand Current State (2 min)

```bash
# See recent commits
git log --oneline -5

# Check git status (should be clean)
git status

# See test coverage summary
pytest tests/ -q --tb=no 2>&1 | tail -3
```

**Expected State**:
- ✅ Clean git status (no uncommitted changes)
- ✅ All tests passing
- ✅ Coverage ≥89%
- ✅ All commits authored by Claude

---

## Step 4: Memory & Resource Check (1 min)

⚠️ **IMPORTANT FOR MACOS**: Check available memory BEFORE spawning agents

```bash
# Check available memory
vm_stat | head -3

# If available memory < 2GB: Don't spawn agents
# If available memory 2-4GB: Use 1 agent max
# If available memory > 4GB: Use max 2 agents
# NEVER use 4 agents in parallel on constrained systems
```

**Memory Usage Per Agent**:
- Test suite: ~500MB
- Full context: ~200MB
- Temp files: ~100MB
- **Total per agent: ~1GB reserve**

---

## Step 5: Understand Your Task (4 min)

### If Adding New Features
1. Read `DEVELOPMENT.md` → section "Adding Features"
2. Check `ARCHITECTURE.md` → understand affected modules
3. Look at similar tests: `grep -r "test_your_feature" tests/`

### If Working on Integration
1. Read `INTEGRATIONS.md` → find your integration
2. Check the Rail doc in Confluence
3. Review existing integration tests

### If Fixing Bugs
1. Look at recent commits: `git log --all -S "bug_keywords"`
2. Find relevant test file
3. Create test that reproduces bug first
4. Then fix implementation

### If Writing Tests
1. Check `TESTING.md` for test patterns
2. Run existing test suite to see patterns
3. Coverage must stay ≥85%

---

## Step 6: Read Relevant Documentation (3 min)

Choose based on your task:

### Core System Understanding
- ARCHITECTURE.md → System design overview
- src/parallelizer_skill/models.py → Data models
- src/parallelizer_skill/decision_engine.py → Main algorithm

### Deployment & Operations
- INTEGRATIONS.md → Cloud providers, DevArmor
- docs/PHASE6_KUBERNETES.md → K8s deployment
- docs/DEPLOYMENT.md → Full deployment guide

### API & Dashboard
- docs/PHASE6_WEB_DASHBOARD.md → Frontend overview
- API reference: Run `make api-docs` then visit `/docs`
- Frontend: `cd frontend && npm run dev`

### Testing
- TESTING.md → Test strategy
- tests/conftest.py → Test fixtures
- tests/integration/ → Example integration tests

---

## Agent Usage Pattern (CRITICAL ⚠️)

### ❌ DON'T DO THIS
```
"Max 4 agents" - Launches 4 Claude processes in parallel
→ Each loads 300KB context + runs 559 tests
→ 4GB+ memory usage
→ macOS swap/crash
```

### ✅ DO THIS INSTEAD

**Single Agent, Sequential Operations**:
```
Agent 1 does Task A
Agent 1 does Task B
Agent 1 does Task C
= Much faster, uses 800MB, no memory thrashing
```

**Limited Parallel** (only if memory available):
```
Check: vm_stat shows >6GB available
Then: Use max 2 agents
Never: Use 4 agents on typical Mac
```

---

## Pre-Work Checklist

Before starting ANY task:

- [ ] `cd /Users/craighoad/Repos/claude-skill-parallelize-task`
- [ ] `python --version` shows 3.12+
- [ ] `make check` passes (all quality gates)
- [ ] `pytest tests/ -q` shows 559 passed
- [ ] `git status` shows clean (no changes)
- [ ] `vm_stat` shows available memory
- [ ] Appropriate documentation read

---

## Quick Command Reference

```bash
# Testing
make test                    # Run all 559 tests
make coverage                # Show coverage report
pytest tests/test_decision_engine.py -v  # Run specific test file

# Quality
make check                   # All quality gates
make lint                    # Ruff linting only
make format                  # Black formatting only
make type-check              # MyPy type checking only

# Development
python -m pytest tests/integration/ -v  # Integration tests only
pytest tests/ -k "performance" -v       # Run matching tests
pytest tests/test_api.py::TestAPI::test_health_check -v  # Single test

# API & Frontend
python -m uvicorn src.parallelizer_skill.api:create_app --reload  # API
cd frontend && npm run dev  # Frontend (if Node installed)

# Git
git log --oneline -10       # Recent commits
git diff                    # Uncommitted changes
git status                  # Clean status check

# Deployment
make docker-build           # Build container
make k8s-deploy             # Deploy to K8s
scripts/health-check.sh     # Verify deployment
```

---

## Common Issues & Solutions

### Issue: Tests fail after editing code

**Solution**:
```bash
# 1. Revert changes if unsure
git checkout .

# 2. Re-run make check
make check

# 3. Run specific failing test with verbose output
pytest tests/test_file.py::TestClass::test_method -vv
```

### Issue: Coverage drops below 85%

**Solution**:
```bash
# Show uncovered lines
make coverage

# Add tests to cover the missing lines
# Usually: pytest tests/test_module.py -v --cov --cov-report=term-missing

# Verify coverage >= 85%
pytest tests/ --cov=src/parallelizer_skill --cov-fail-under=85
```

### Issue: Memory error when running tests

**Solution**:
```bash
# Run tests in smaller batches
pytest tests/test_decision_engine.py -v    # One file at a time
pytest tests/ -n 2                          # Use 2 workers max

# Or run without coverage (less memory)
pytest tests/ -q
```

### Issue: Type checking fails

**Solution**:
```bash
# Run mypy with detailed output
mypy src/ --show-error-codes --show-column-numbers

# Fix type hints in the affected file
# Usually missing: Optional[], List[], Dict[] imports

# Verify mypy passes
make type-check
```

---

## Know Before You Code

1. **No Hardcoded Secrets**: Use environment variables only
2. **Import from models.py**: Pydantic models for all data
3. **Use config.get_config()**: For configuration access
4. **Async-First**: Use `async def` and `await` for I/O
5. **Test Coverage**: Always maintain ≥85%
6. **Git Workflow**: Use `--no-verify` and `[skip ci]` per user memory
7. **Sequential Work**: Use 1 agent max on constrained systems
8. **Check git before starting**: `git log --oneline -1` to see last change

---

## Success Criteria

After onboarding, you should be able to:

- ✅ Run `make check` and see all gates pass
- ✅ Run `pytest tests/ -q` and see 559 tests pass
- ✅ Understand git history: `git log --oneline -10`
- ✅ Know what to do if a test fails
- ✅ Know which documentation to read for your task
- ✅ Have memory available to work safely

---

## Next Steps

1. **New to this codebase?** → Read ARCHITECTURE.md
2. **Adding a feature?** → Read DEVELOPMENT.md
3. **Working on deployment?** → Read INTEGRATIONS.md
4. **Writing tests?** → Read TESTING.md
5. **Ready to code?** → Pick your task and start!

---

**If stuck**: Check the git log, run `make check`, and review the relevant .claude/XXX.md file.

**Remember**: The quality gates exist to keep the code production-ready. Work with them, not against them.

---

**Last Updated**: 2026-05-17  
**Session Time**: ~15 minutes to complete  
**Success Rate**: 99% (only fails if Python < 3.12)
