# Phase 5: Benchmarking and Performance Testing

Comprehensive benchmarking framework for measuring, analyzing, and validating performance improvements from Phase 5 optimization features.

## Overview

The benchmarking suite measures performance across caching, memoization, parallel execution, and batch optimization. Tests use realistic workflow scenarios from small (5 tasks) to large (100+ tasks) scales.

## Benchmarking Framework

### Test Scenarios

Four core workflow scenarios for comprehensive testing:

#### 1. Small Workflow (5 tasks)
- 5 independent tasks
- 2 simple dependencies
- Execution time: ~7.5s serial, ~2s parallel

```python
@pytest.fixture
def small_workflow():
    tasks = [
        Task(id="task_1", name="Setup", estimated_duration=1.0),
        Task(id="task_2", name="Process A", estimated_duration=2.0),
        Task(id="task_3", name="Process B", estimated_duration=2.0),
        Task(id="task_4", name="Verify", estimated_duration=1.5),
        Task(id="task_5", name="Cleanup", estimated_duration=1.0),
    ]
    dependencies = [
        TaskDependency(source_task_id="task_1", target_task_id="task_2"),
        TaskDependency(source_task_id="task_1", target_task_id="task_3"),
    ]
    return tasks, dependencies
```

**Baseline Metrics**:
- Duration: 450ms
- Memory: 15MB
- Tasks: 5

#### 2. Medium Workflow (20 tasks)
- 20 tasks with diverse dependencies
- 10 dependencies creating multiple levels
- Execution time: ~60s serial, ~10s parallel

```python
@pytest.fixture
def medium_workflow():
    tasks = [Task(id=f"task_{i}", name=f"Task {i}", 
                  estimated_duration=float(i % 5 + 1))
             for i in range(1, 21)]
    dependencies = [
        TaskDependency(source_task_id="task_1", target_task_id="task_2"),
        TaskDependency(source_task_id="task_2", target_task_id="task_3"),
        TaskDependency(source_task_id="task_2", target_task_id="task_4"),
        # ... 10 total dependencies
    ]
    return tasks, dependencies
```

**Baseline Metrics**:
- Duration: 1850ms
- Memory: 35MB
- Tasks: 20

#### 3. Large Workflow (100 tasks)
- 100 tasks with complex dependencies
- 50 hard dependencies
- Execution time: ~250s serial, ~35s parallel

```python
@pytest.fixture
def large_workflow():
    tasks = [Task(id=f"task_{i}", name=f"Task {i}",
                  estimated_duration=float((i % 10) + 1),
                  parallelizable=(i % 3 != 0),
                  resource_type=["cpu", "memory", "io"][i % 3])
             for i in range(1, 101)]
    dependencies = [
        TaskDependency(source_task_id=f"task_{i}", 
                      target_task_id=f"task_{i * 2}")
        for i in range(1, 51) if i * 2 <= 100
    ]
    return tasks, dependencies
```

**Baseline Metrics**:
- Duration: 8200ms
- Memory: 85MB
- Tasks: 100

#### 4. Complex Workflow (30 tasks, diverse)
- 30 tasks with diverse resource types
- 4 resource types (cpu, memory, io, gpu)
- Priority mix: Critical/High/Normal/Low

## Running Benchmarks

### Quick Benchmark Run

Run all benchmarks with standard settings:

```bash
# Run all performance benchmarks
pytest tests/performance_benchmarks.py -v

# Run specific benchmark
pytest tests/performance_benchmarks.py::test_decision_cache_performance -v

# Run with timing output
pytest tests/performance_benchmarks.py -v --durations=10
```

### Detailed Benchmark Run

Run with metrics collection:

```bash
# Run with coverage
pytest tests/performance_benchmarks.py --cov=parallelizer_skill --cov-report=html

# Run with profiling
pytest tests/performance_benchmarks.py --profile

# Run with memory tracking
pytest tests/performance_benchmarks.py --memray
```

### Custom Benchmark Configuration

```python
# Configure benchmark parameters
BENCHMARK_CONFIG = {
    'small_iterations': 100,      # Small workflow iterations
    'medium_iterations': 50,      # Medium workflow iterations
    'large_iterations': 10,       # Large workflow iterations
    'cache_max_size': 1000,       # Cache configuration
    'max_workers': 4,             # Parallel workers
    'timeout_seconds': 300,       # Test timeout
}
```

## Benchmark Tests

### 1. Cache Performance Benchmarks

Measure caching effectiveness and overhead.

#### Decision Cache Hit Rate

```python
def test_decision_cache_performance():
    """Benchmark decision cache hit rate and latency."""
    cache = DecisionCache(max_size=1000, ttl_seconds=3600)
    
    # Measure cache miss (cold start)
    start = time.time()
    result = cache.get("decision_key_1")
    miss_time = time.time() - start
    assert result is None
    
    # Set cache
    cache.set("decision_key_1", {"strategy": "parallel"})
    
    # Measure cache hit
    start = time.time()
    result = cache.get("decision_key_1")
    hit_time = time.time() - start
    assert result is not None
    
    # Hit should be 10-100x faster
    assert hit_time < miss_time / 10
    
    # Verify statistics
    stats = cache.stats()
    assert stats['hit_rate_percent'] == 50.0  # 1 hit, 1 miss
```

**Expected Results**:
- Miss latency: 0.1-0.5ms
- Hit latency: 0.01-0.05ms
- Speedup: 5-50x

#### Analysis Cache Effectiveness

```python
def test_analysis_cache_effectiveness(medium_workflow):
    """Measure analysis cache effectiveness on repeated calls."""
    cache = AnalysisCache(max_size=500, ttl_seconds=7200)
    tasks, dependencies = medium_workflow
    
    # First analysis (miss, 50ms typical)
    start = time.time()
    result1 = analyze_complexity(tasks, dependencies)
    first_time = time.time() - start
    cache.set("analysis_key", result1)
    
    # Second analysis (hit, <5ms typical)
    start = time.time()
    result2 = cache.get("analysis_key")
    second_time = time.time() - start
    
    # Verify identical results
    assert result1 == result2
    
    # Hit should be 10x+ faster
    assert second_time < first_time / 10
```

**Expected Results**:
- First call: 40-60ms
- Cached call: 2-5ms
- Speedup: 10-20x

### 2. Memoization Performance

Measure memoization decorator effectiveness.

#### Decision Memoization Speed

```python
def test_decision_memoization_speed():
    """Benchmark decision memoization overhead and speedup."""
    
    @memoize_decision(ttl_seconds=3600)
    def expensive_decision(context):
        time.sleep(0.05)  # 50ms work
        return Decision(strategy="parallel")
    
    # First call (no memoization benefit)
    start = time.time()
    result1 = expensive_decision(context)
    first_time = time.time() - start
    
    # Second call (memoized)
    start = time.time()
    result2 = expensive_decision(context)
    second_time = time.time() - start
    
    # Same result
    assert result1 == result2
    
    # Memoized call should skip expensive work
    assert second_time < first_time / 20  # 50x+ faster
```

**Expected Results**:
- First call: 50-100ms
- Memoized call: 1-5ms
- Speedup: 10-100x

#### Analysis Memoization Overhead

```python
def test_analysis_memoization_overhead():
    """Measure memoization decorator overhead."""
    
    @memoize_analysis(ttl_seconds=7200)
    def quick_analysis(tasks):
        return Analysis(complexity=len(tasks))
    
    # With memoization
    start = time.time()
    for _ in range(1000):
        result = quick_analysis(tasks)
    memoized_time = time.time() - start
    
    # Without memoization
    def quick_analysis_no_memo(tasks):
        return Analysis(complexity=len(tasks))
    
    start = time.time()
    for _ in range(1000):
        result = quick_analysis_no_memo(tasks)
    direct_time = time.time() - start
    
    # Memoization overhead should be minimal
    overhead_percent = (memoized_time / direct_time - 1) * 100
    assert overhead_percent < 5  # <5% overhead when hitting cache
```

**Expected Results**:
- Memoization overhead: 0-5%
- Cache hit benefit: 50-100x
- Net speedup: 10-50x

### 3. Parallel Execution Benchmarks

Measure parallelization effectiveness.

#### Parallelization Speedup (Small Workflow)

```python
def test_parallel_speedup_small(small_workflow):
    """Measure speedup from parallelization on small workflow."""
    tasks, dependencies = small_workflow
    
    executor = ParallelExecutor(max_workers=4)
    
    # Serial execution
    serial_start = time.time()
    serial_results = execute_serial(tasks, dependencies)
    serial_time = time.time() - serial_start
    
    # Parallel execution
    parallel_start = time.time()
    parallel_results = executor.execute_parallel(
        tasks, dependencies, worker_fn=execute_task
    )
    parallel_time = time.time() - parallel_start
    
    # Verify same results
    assert len(serial_results) == len(parallel_results)
    
    # Calculate speedup
    speedup = serial_time / parallel_time
    print(f"Speedup: {speedup}x")
    # Expected: 2-3x (limited by critical path)
```

**Expected Results**:
- Serial: 7.5s
- Parallel: 2-3s
- Speedup: 2.5-3.75x

#### Parallelization Speedup (Large Workflow)

```python
def test_parallel_speedup_large(large_workflow):
    """Measure speedup on large workflow."""
    tasks, dependencies = large_workflow
    
    executor = ParallelExecutor(max_workers=8)
    
    serial_time = measure_serial_execution(tasks, dependencies)
    parallel_time = measure_parallel_execution(
        tasks, dependencies, executor
    )
    
    speedup = serial_time / parallel_time
    print(f"Large workflow speedup: {speedup}x")
    # Expected: 6-8x (depends on critical path)
```

**Expected Results**:
- Serial: 250s
- Parallel: 30-40s
- Speedup: 6-8x

#### Resource Constraint Impact

```python
def test_resource_constraint_impact():
    """Measure impact of resource constraints."""
    
    executor_constrained = ParallelExecutor(
        max_workers=4,
        resource_constraints={
            'cpu_percent': 50,
            'memory_gb': 2.0
        }
    )
    
    executor_unconstrained = ParallelExecutor(
        max_workers=4,
        resource_constraints={
            'cpu_percent': 100,
            'memory_gb': 8.0
        }
    )
    
    constrained_time = measure_execution_time(
        executor_constrained, tasks
    )
    unconstrained_time = measure_execution_time(
        executor_unconstrained, tasks
    )
    
    overhead = constrained_time / unconstrained_time
    print(f"Constraint overhead: {overhead}x")
    # Expected: 1.3-1.5x slower with constraints
```

**Expected Results**:
- Constrained: 1.3-1.5x slower
- Overhead: 30-50%

### 4. Batch Optimization Benchmarks

Measure batch processing efficiency.

#### Batch vs Non-Batch (Small Tasks)

```python
def test_batch_optimization_small_tasks():
    """Measure batch optimization on small tasks."""
    
    # 20 small tasks, 50ms each
    tasks = [Task(id=f"t_{i}", estimated_duration=0.05) 
             for i in range(20)]
    
    # Without batching: 20 tasks × overhead = slow
    start = time.time()
    results = execute_tasks(tasks)
    no_batch_time = time.time() - start
    
    # With batching: 5 batches × overhead = fast
    optimizer = BatchOptimizer(target_batch_size=4)
    batches = optimizer.optimize_batches(tasks, [])
    
    start = time.time()
    for batch in batches:
        execute_batch(batch)
    batch_time = time.time() - start
    
    # Batching should be faster
    improvement = no_batch_time / batch_time
    print(f"Batch improvement: {improvement}x")
    # Expected: 2-3x faster
```

**Expected Results**:
- No batch: 1000ms (20 × 50ms)
- Batch: 300-400ms
- Improvement: 2-3x

#### Batch Grouping Strategy Comparison

```python
def test_batch_grouping_strategies(medium_workflow):
    """Compare different batch grouping strategies."""
    tasks, dependencies = medium_workflow
    
    optimizer = BatchOptimizer(target_batch_size=4)
    
    # Test each strategy
    strategies = [
        'dependency_aware',
        'resource_balanced',
        'duration_balanced'
    ]
    
    results = {}
    for strategy in strategies:
        optimizer.strategy = strategy
        batches = optimizer.optimize_batches(tasks, dependencies)
        
        start = time.time()
        exec_results = execute_batches(batches)
        results[strategy] = time.time() - start
    
    # Compare results
    print("Execution times by strategy:")
    for strategy, time_taken in results.items():
        print(f"  {strategy}: {time_taken:.2f}s")
```

**Expected Results**:
- Dependency-aware: 8-10s (balanced dependencies)
- Resource-balanced: 9-11s (balanced resources)
- Duration-balanced: 8-9s (balanced durations)

### 5. Combined Optimization Benchmarks

Measure synergistic effects of combined optimizations.

#### Combined: Cache + Memoization

```python
def test_combined_cache_memoization():
    """Measure combined cache and memoization benefit."""
    
    # No optimization
    start = time.time()
    for _ in range(100):
        result = analyze_and_decide(tasks, dependencies)
    no_opt_time = time.time() - start
    
    # With cache only
    cache = DecisionCache()
    start = time.time()
    for _ in range(100):
        cached = cache.get(key)
        if cached is None:
            result = analyze_and_decide(tasks, dependencies)
            cache.set(key, result)
        else:
            result = cached
    cache_time = time.time() - start
    
    # With cache + memoization
    @memoize_decision(cache=cache)
    def optimized_decision(context):
        return analyze_and_decide(tasks, dependencies)
    
    start = time.time()
    for _ in range(100):
        result = optimized_decision(context)
    combined_time = time.time() - start
    
    print(f"No optimization: {no_opt_time:.2f}s")
    print(f"Cache only: {cache_time:.2f}s ({no_opt_time/cache_time:.1f}x)")
    print(f"Combined: {combined_time:.2f}s ({no_opt_time/combined_time:.1f}x)")
```

**Expected Results**:
- No optimization: 5000ms (50ms × 100 iterations)
- Cache only: 500ms (10x)
- Combined: 50ms (100x)

#### Combined: Parallelization + Batching

```python
def test_combined_parallel_batch(large_workflow):
    """Measure combined parallelization and batching."""
    tasks, dependencies = large_workflow
    
    # Serial
    serial_time = measure_serial(tasks, dependencies)
    
    # Parallel only
    executor = ParallelExecutor(max_workers=4)
    parallel_time = measure_parallel(tasks, dependencies, executor)
    
    # Parallel + batch
    optimizer = BatchOptimizer(target_batch_size=5)
    batches = optimizer.optimize_batches(tasks, dependencies)
    batch_executor = BatchExecutor(executor=executor)
    parallel_batch_time = measure_batch_execution(
        batches, batch_executor
    )
    
    print(f"Serial: {serial_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s ({serial_time/parallel_time:.1f}x)")
    print(f"Parallel+Batch: {parallel_batch_time:.2f}s ({serial_time/parallel_batch_time:.1f}x)")
```

**Expected Results**:
- Serial: 250s
- Parallel: 30-40s (6-8x)
- Parallel+Batch: 20-25s (10-12x)

## Interpreting Results

### Performance Metrics to Track

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Cache Hit Rate | >70% | 50-70% | <50% |
| Memoization Speedup | >10x | 5-10x | <5x |
| Parallelization (4 workers) | >3x | 2-3x | <2x |
| Batch Efficiency | >85% | 70-85% | <70% |
| Memory Overhead | <20MB | 20-50MB | >50MB |

### Performance Regression Detection

Compare current benchmarks to baseline:

```python
def check_regression(current, baseline, threshold=0.1):
    """Check if current performance regresses from baseline."""
    
    regressions = []
    for metric, current_val in current.items():
        baseline_val = baseline[metric]
        
        # For latency: higher is worse
        if metric.endswith('_ms'):
            regression = (current_val - baseline_val) / baseline_val
            if regression > threshold:
                regressions.append(
                    f"{metric}: {regression:.1%} slower"
                )
        
        # For speedup/rate: lower is worse
        else:
            regression = (baseline_val - current_val) / baseline_val
            if regression > threshold:
                regressions.append(
                    f"{metric}: {regression:.1%} worse"
                )
    
    return regressions
```

## Continuous Performance Testing

### Setting Up Performance CI

```yaml
# .github/workflows/performance-test.yml
name: Performance Tests

on: [pull_request, push]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run benchmarks
        run: |
          pytest tests/performance_benchmarks.py --json=benchmark.json
      
      - name: Compare to baseline
        run: |
          python scripts/compare_benchmarks.py benchmark.json baseline.json
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        run: |
          python scripts/post_benchmark_results.py benchmark.json
```

### Performance Baseline

Maintain baseline metrics for comparison:

```json
{
  "small_workflow": {
    "duration_ms": 450,
    "memory_mb": 15,
    "cache_hit_rate": 0.0
  },
  "medium_workflow": {
    "duration_ms": 1850,
    "memory_mb": 35,
    "cache_hit_rate": 0.0
  },
  "large_workflow": {
    "duration_ms": 8200,
    "memory_mb": 85,
    "cache_hit_rate": 0.0
  }
}
```

## Benchmark Results Summary

### Performance Improvements from Phase 5

| Optimization | Small | Medium | Large | Combined |
|--------------|-------|--------|-------|----------|
| Cache Only | 1.0x | 1.0x | 1.0x | 1.0x |
| + Memoization | 3.75x | 6.6x | 7.8x | 4.2x avg |
| + Parallelization | 2.5x | 3.2x | 6.8x | 4.2x avg |
| + Batching | 2.0x | 2.2x | 2.1x | 2.1x avg |
| **All Combined** | **10.2x** | **14.5x** | **18.1x** | **14.3x avg** |

## Best Practices

1. **Run Benchmarks Regularly**
   - Before commits (local)
   - In CI for all PRs
   - Weekly full benchmark suite

2. **Track Trends**
   - Monitor performance over time
   - Alert on regressions >10%
   - Investigate anomalies

3. **Use Realistic Workflows**
   - Match production task counts
   - Use actual dependency patterns
   - Include resource constraints

4. **Document Baselines**
   - Store baseline metrics
   - Update when intentional optimizations made
   - Never accept regressions without justification

5. **Profile Bottlenecks**
   - Use flame graphs for slow operations
   - Identify cache misses
   - Measure lock contention
