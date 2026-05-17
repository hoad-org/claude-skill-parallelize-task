# Phase 4 Integration Tests Documentation

Complete guide to Phase 4 integration test suite and coverage.

## Test Suite Overview

Phase 4 has comprehensive integration and unit tests achieving **89.17% coverage** with **414 tests passing**.

### Test Categories

```
tests/
├── test_cli_integration.py      # CLI command testing (Phase 4)
├── test_orchestrator.py         # WorkflowOrchestrator testing
├── test_stage_orchestrator.py   # Stage gate enforcement testing
├── test_agent_monitor.py        # Agent execution tracking
├── test_callbacks.py            # Progress callbacks
├── test_output_coordinator.py   # Output formatting
├── test_persistence.py          # State persistence
├── test_strategy_document.py    # Documentation generation
├── test_escalation.py           # Failure recovery
├── test_complexity.py           # Task complexity scoring
├── test_decision_engine.py      # Strategy decisions
├── test_execution_planner.py    # Plan generation
└── conftest.py                  # Shared fixtures
```

## Running Tests

### Run All Tests
```bash
pytest
# Output: ===================== 414 passed in 1.46s =======================
```

### Run Specific Test File
```bash
pytest tests/test_orchestrator.py
```

### Run Specific Test Class
```bash
pytest tests/test_orchestrator.py::TestWorkflowOrchestrator
```

### Run Specific Test Method
```bash
pytest tests/test_orchestrator.py::TestWorkflowOrchestrator::test_analyze_workflow
```

### Run with Coverage
```bash
pytest --cov=src/parallelizer_skill --cov-report=html
# Coverage report written to htmlcov/index.html
```

### Run by Test Type
```bash
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m dag           # DAG analysis tests
pytest -m optimization  # Optimization tests
```

### Verbose Output
```bash
pytest -v              # Show each test
pytest -vv             # Extra verbose with output
pytest -s              # Show print statements
```

## Test Coverage

### Coverage by Module

| Module | Coverage | Status |
|--------|----------|--------|
| models.py | 100% | ✓ Complete |
| strategy_document.py | 100% | ✓ Complete |
| token_budget.py | 100% | ✓ Complete |
| orchestrator.py | 92% | ✓ Strong |
| stage_orchestrator.py | 95% | ✓ Strong |
| decision_engine.py | 94% | ✓ Strong |
| complexity.py | 94% | ✓ Strong |
| escalation.py | 91% | ✓ Strong |
| persistence.py | 88% | ✓ Strong |
| output_coordinator.py | 90% | ✓ Strong |
| dag_analyzer.py | 92% | ✓ Strong |
| config.py | 85% | ✓ Good |
| optimizer.py | 96% | ✓ Strong |
| execution_planner.py | 78% | → Good |
| callbacks.py | 93% | ✓ Strong |
| agent_monitor.py | 81% | → Good |
| cli.py | 75% | → Fair |

**Overall: 89.17% coverage (target: 75%)**

## CLI Integration Tests

### Test Categories

#### Input/Output Tests
- JSON file loading and validation
- Output formatting (JSON/text)
- File writing with path creation
- Error handling for missing files

#### Command Tests
- `analyze` command with various options
- `decide` command with different goals
- `plan` command with dependencies
- `execute` command with dry-run
- `document` command with formats
- `reset` command with workflow IDs

#### Workflow Tests
- Full pipeline (analyze → decide → plan → execute → document)
- Partial workflows (analyze only, analyze → decide)
- Error recovery workflows
- State persistence across commands

#### Integration Tests
- Orchestrator integration
- Stage orchestrator integration
- Configuration loading
- Persistence manager integration

### Example Test

```python
def test_analyze_command():
    """Test analyze command with valid tasks."""
    tasks = [
        Task(id="t1", name="Task 1", estimated_duration=1.0),
        Task(id="t2", name="Task 2", estimated_duration=2.0),
    ]
    deps = [TaskDependency(source_task_id="t1", target_task_id="t2")]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tasks_file = write_json_file(f"{tmpdir}/tasks.json", tasks)
        deps_file = write_json_file(f"{tmpdir}/deps.json", deps)
        output_file = f"{tmpdir}/analysis.json"
        
        result = analyze(tasks_file, deps_file, output_file)
        
        assert result == 0
        assert Path(output_file).exists()
        
        analysis = load_json_file(output_file)
        assert analysis["total_tasks"] == 2
        assert analysis["critical_path"] == ["t1", "t2"]
```

## Orchestrator Tests

### Core Functionality Tests

```
TestWorkflowOrchestrator:
├── test_initialize()               # Create orchestrator
├── test_analyze_workflow()         # Run analysis
├── test_make_decision()            # Get decision
├── test_plan_execution()           # Create plan
├── test_execute_workflow()         # Run workflow
├── test_generate_strategy_document() # Document results
└── test_handle_failure()           # Error recovery
```

### Workflow State Tests

```
TestWorkflowState:
├── test_state_persistence()        # Save/load state
├── test_state_updates()            # Update state
├── test_workflow_metadata()        # Track metadata
└── test_recovery_from_state()      # Resume from saved state
```

## Stage Orchestrator Tests

### Stage Management Tests

```
TestStageOrchestrator:
├── test_add_stage()                # Define stages
├── test_stage_order()              # Verify ordering
├── test_start_stage()              # Begin execution
├── test_task_status_update()       # Track progress
├── test_check_stage_ready()        # Verify completion
└── test_check_stage_passed()       # Verify success
```

### Gate Policy Tests

```
TestGatePolicies:
├── test_all_pass_gate()            # All must succeed
├── test_all_complete_gate()        # All must finish
├── test_majority_gate()            # 80% must pass
└── test_failed_tasks_tracking()    # Record failures
```

## Error Scenarios

Tests cover common failure scenarios:

1. **Invalid Input**
   - Missing required files
   - Malformed JSON
   - Invalid task IDs
   - Circular dependencies

2. **Execution Failures**
   - Task timeout
   - Resource exhaustion
   - Agent failure
   - Network error

3. **Recovery Scenarios**
   - Automatic retry
   - Manual recovery
   - Escalation handling
   - State restoration

4. **Edge Cases**
   - Empty task lists
   - Single task workflows
   - Deep dependency chains
   - Highly parallel workflows

## Performance Tests

### Scalability Tests
- 10, 100, 1000 task workflows
- Deep dependency chains (100+ levels)
- Complex resource constraints
- Large batch sizes

### Timing Tests
- Analysis time vs task count
- Planning time vs dependency complexity
- Execution overhead
- State persistence speed

### Example Performance Test

```python
@pytest.mark.performance
def test_large_workflow_analysis():
    """Test analysis of 1000-task workflow."""
    tasks = [Task(id=f"t{i}", name=f"Task {i}") for i in range(1000)]
    deps = [TaskDependency(f"t{i}", f"t{i+1}") for i in range(999)]
    
    orch = WorkflowOrchestrator()
    
    start = time.time()
    analysis = orch.analyze_workflow("wf", tasks, deps)
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # Must complete in < 1 second
    assert analysis.total_tasks == 1000
```

## Fixtures

### Shared Fixtures (conftest.py)

```python
@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    return [
        Task(id="t1", name="Load", estimated_duration=2.0),
        Task(id="t2", name="Process A", estimated_duration=3.0),
        Task(id="t3", name="Process B", estimated_duration=3.0),
        Task(id="t4", name="Aggregate", estimated_duration=1.0),
    ]

@pytest.fixture
def sample_dependencies():
    """Create sample dependencies."""
    return [
        TaskDependency("t1", "t2"),
        TaskDependency("t1", "t3"),
        TaskDependency("t2", "t4"),
        TaskDependency("t3", "t4"),
    ]

@pytest.fixture
def orchestrator():
    """Create test orchestrator."""
    return WorkflowOrchestrator()
```

## Adding New Tests

### Test Structure

```python
import pytest
from parallelizer_skill.orchestrator import WorkflowOrchestrator

@pytest.mark.integration
class TestNewFeature:
    """Test description."""
    
    def test_specific_behavior(self, sample_tasks, sample_dependencies):
        """Test description."""
        # Arrange
        orch = WorkflowOrchestrator()
        
        # Act
        result = orch.analyze_workflow("wf", sample_tasks, sample_dependencies)
        
        # Assert
        assert result is not None
        assert result.total_tasks == 4
```

### Coverage Guidelines

1. Test happy path (success case)
2. Test error cases (failure handling)
3. Test edge cases (boundary conditions)
4. Test integration (component interaction)
5. Target 85%+ coverage minimum

### Running Coverage Report

```bash
# Generate coverage report
pytest --cov=src/parallelizer_skill --cov-report=html

# View in browser
open htmlcov/index.html

# Show missing coverage
coverage report --skip-covered
```

## CI/CD Integration

Tests run automatically via GitHub Actions:

- **Trigger**: Push to main or PR
- **Environment**: Python 3.12+
- **Requirements**: pytest, pytest-cov
- **Pass Criteria**: All tests pass, coverage ≥ 75%

### GitHub Actions Workflow

```yaml
- name: Run tests
  run: pytest --cov=src/parallelizer_skill

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Data

### Sample Workflows

1. **Simple Pipeline** (4 tasks, 1 chain)
2. **Parallel Groups** (6 tasks, multiple parallel branches)
3. **Complex Dependencies** (12 tasks, deep chains)
4. **Resource Constrained** (8 tasks, resource limits)
5. **Highly Parallel** (100 tasks, minimal dependencies)

### Test Fixtures Location

Located in `tests/conftest.py`:

```python
@pytest.fixture
def simple_workflow():
    """4-task simple pipeline."""
    
@pytest.fixture
def parallel_workflow():
    """6-task with parallel branches."""
    
@pytest.fixture
def complex_workflow():
    """12-task complex dependency graph."""
```

## Known Issues & Limitations

### Current Limitations
- CLI tests mock orchestrator (don't test actual execution)
- Some corner cases in escalation not fully covered
- Agent monitor coverage at 81%
- Execution planner coverage at 78%

### Areas for Future Testing
- Real agent execution (Phase 5)
- Multi-agent coordination
- Long-running workflow state recovery
- Advanced resource constraints
- Performance under high concurrency

## Performance Benchmarks

### Current Performance

| Operation | Time | Tasks |
|-----------|------|-------|
| Analyze | ~50ms | 100 |
| Analyze | ~500ms | 1000 |
| Decide | ~10ms | Any |
| Plan | ~100ms | 100 |
| Plan | ~1000ms | 1000 |

## Test Reporting

### Generate Test Report
```bash
pytest --html=report.html --self-contained-html
```

### View Coverage Details
```bash
pytest --cov=src/parallelizer_skill --cov-report=term-missing
```

## Quick Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/parallelizer_skill --cov-report=html

# Run specific category
pytest -m integration

# Run with verbose output
pytest -v

# Run single test
pytest tests/test_orchestrator.py::test_analyze_workflow

# Run until first failure
pytest -x

# Run last failed tests
pytest --lf

# Run with logging
pytest -s --log-cli-level=DEBUG
```
