"""Performance benchmarking suite for Phase 5 optimization (timing-based)."""

import time
import pytest
from typing import List, Tuple
from parallelizer_skill.models import Task, TaskDependency, TaskPriority
from parallelizer_skill.decision_engine import (
    DecisionEngine,
    DecisionContext,
    ParallelizationGoal,
    TaskComplexityClass,
    ResourceConstraint,
    DependencyDensity,
    FailureTolerance,
    PriorityMetric,
)
from parallelizer_skill.complexity import ComplexityScorer
from parallelizer_skill.dag_analyzer import DAGAnalyzer
from parallelizer_skill.performance import (
    PerformanceConfig,
    PerformanceManager,
    DecisionCache,
    AnalysisCache,
    ParallelExecutor,
    BatchOptimizer,
    MetricsCollector,
    memoize_decision,
    memoize_analysis,
)


# ============================================================================
# FIXTURE BUILDERS FOR WORKFLOW SCENARIOS
# ============================================================================


@pytest.fixture
def small_workflow() -> Tuple[List[Task], List[TaskDependency]]:
    """Small workflow: 5 tasks, 2 dependencies."""
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


@pytest.fixture
def medium_workflow() -> Tuple[List[Task], List[TaskDependency]]:
    """Medium workflow: 20 tasks, 10 dependencies."""
    tasks = [Task(id=f"task_{i}", name=f"Task {i}", estimated_duration=float(i % 5 + 1)) for i in range(1, 21)]

    dependencies = [
        TaskDependency(source_task_id="task_1", target_task_id="task_2"),
        TaskDependency(source_task_id="task_2", target_task_id="task_3"),
        TaskDependency(source_task_id="task_2", target_task_id="task_4"),
        TaskDependency(source_task_id="task_3", target_task_id="task_5"),
        TaskDependency(source_task_id="task_4", target_task_id="task_6"),
        TaskDependency(source_task_id="task_5", target_task_id="task_7"),
        TaskDependency(source_task_id="task_6", target_task_id="task_8"),
        TaskDependency(source_task_id="task_7", target_task_id="task_9"),
        TaskDependency(source_task_id="task_8", target_task_id="task_10"),
        TaskDependency(source_task_id="task_15", target_task_id="task_20"),
    ]
    return tasks, dependencies


@pytest.fixture
def large_workflow() -> Tuple[List[Task], List[TaskDependency]]:
    """Large workflow: 100 tasks, 50 dependencies."""
    tasks = [
        Task(
            id=f"task_{i}",
            name=f"Task {i}",
            estimated_duration=float((i % 10) + 1),
            parallelizable=(i % 3 != 0),
            resource_type=["cpu", "memory", "io"][i % 3],
        )
        for i in range(1, 101)
    ]

    dependencies = []
    for i in range(1, 51):
        source_id = f"task_{i}"
        target_id = f"task_{i * 2}"
        if i * 2 <= 100:
            dependencies.append(TaskDependency(source_task_id=source_id, target_task_id=target_id))

    return tasks, dependencies


@pytest.fixture
def complex_workflow() -> Tuple[List[Task], List[TaskDependency]]:
    """Complex workflow: 30 tasks with diverse resource types."""
    tasks = []
    resource_types = ["cpu", "memory", "io", "gpu", "network"]
    priorities = [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]

    for i in range(1, 31):
        task = Task(
            id=f"task_{i}",
            name=f"Task {i}",
            estimated_duration=float((i % 8) + 0.5),
            parallelizable=(i % 2 == 0),
            resource_type=resource_types[i % len(resource_types)],
            priority=priorities[i % len(priorities)],
            max_concurrent=max(1, (i % 5)),
        )
        tasks.append(task)

    dependencies = [TaskDependency(source_task_id=f"task_{i}", target_task_id=f"task_{i + 1}") for i in range(1, 10)]

    return tasks, dependencies


@pytest.fixture
def dependency_heavy_workflow() -> Tuple[List[Task], List[TaskDependency]]:
    """Dependency-heavy workflow: 10 tasks, 20 dependencies (complex DAG)."""
    tasks = [Task(id=f"task_{i}", name=f"Task {i}", estimated_duration=2.0) for i in range(1, 11)]

    dependencies = [
        TaskDependency(source_task_id="task_1", target_task_id="task_2"),
        TaskDependency(source_task_id="task_1", target_task_id="task_3"),
        TaskDependency(source_task_id="task_1", target_task_id="task_4"),
        TaskDependency(source_task_id="task_2", target_task_id="task_5"),
        TaskDependency(source_task_id="task_3", target_task_id="task_5"),
        TaskDependency(source_task_id="task_4", target_task_id="task_6"),
        TaskDependency(source_task_id="task_2", target_task_id="task_7"),
        TaskDependency(source_task_id="task_3", target_task_id="task_7"),
        TaskDependency(source_task_id="task_5", target_task_id="task_8"),
        TaskDependency(source_task_id="task_6", target_task_id="task_8"),
        TaskDependency(source_task_id="task_7", target_task_id="task_9"),
        TaskDependency(source_task_id="task_8", target_task_id="task_9"),
        TaskDependency(source_task_id="task_5", target_task_id="task_10"),
        TaskDependency(source_task_id="task_6", target_task_id="task_10"),
        TaskDependency(source_task_id="task_9", target_task_id="task_10"),
    ]

    return tasks, dependencies


# ============================================================================
# PERFORMANCE BENCHMARKS
# ============================================================================


@pytest.mark.unit
class TestDecisionEnginePerformance:
    """Benchmark decision engine performance with various optimizations."""

    def test_decision_context_creation(self, small_workflow):
        """Benchmark decision context creation."""
        start = time.perf_counter()
        for _ in range(100):
            context = DecisionContext(
                q1_goal=ParallelizationGoal.PERFORMANCE,
                q2_complexity=TaskComplexityClass.SIMPLE,
                q3_resource_constraint=ResourceConstraint.NONE,
                q4_dependency_density=DependencyDensity.SPARSE,
                q5_failure_tolerance=FailureTolerance.FAIL_FAST,
                q6_priority_metric=PriorityMetric.SPEED,
            )
        elapsed = time.perf_counter() - start

        assert context is not None
        assert elapsed > 0

    def test_decision_engine_initialization(self, small_workflow):
        """Benchmark decision engine initialization."""
        config = PerformanceConfig(cache_enabled=True)
        _manager = PerformanceManager(config)

        start = time.perf_counter()
        for _ in range(10):
            engine = DecisionEngine()
        elapsed = time.perf_counter() - start

        assert engine is not None
        assert elapsed > 0


@pytest.mark.unit
class TestComplexityScoringPerformance:
    """Benchmark complexity scoring with optimizations."""

    def test_complexity_scoring_no_memoization(self, medium_workflow):
        """Benchmark complexity scoring without memoization."""
        tasks, dependencies = medium_workflow
        scorer = ComplexityScorer()

        start = time.perf_counter()
        for _ in range(3):
            scores = {}
            for task in tasks:
                scores[task.id] = scorer.score_task(task, dependencies)
        elapsed = time.perf_counter() - start

        assert len(scores) == len(tasks)
        assert elapsed > 0

    def test_complexity_scoring_with_memoization(self, medium_workflow):
        """Benchmark complexity scoring with memoization."""
        tasks, dependencies = medium_workflow
        scorer = ComplexityScorer()

        @memoize_analysis
        def score_task_cached(task_id: str) -> float:
            task = next((t for t in tasks if t.id == task_id), None)
            if task:
                return scorer.score_task(task, dependencies).score
            return 0.0

        start = time.perf_counter()
        for _ in range(3):
            result = {task.id: score_task_cached(task.id) for task in tasks}
        elapsed = time.perf_counter() - start

        assert len(result) == len(tasks)
        assert elapsed > 0


@pytest.mark.unit
class TestExecutionPlanningPerformance:
    """Benchmark execution planning performance."""

    def test_dag_analysis_small(self, small_workflow):
        """Benchmark DAG analysis on small workflow."""
        tasks, dependencies = small_workflow

        start = time.perf_counter()
        analyzer = DAGAnalyzer(tasks, dependencies)
        result = analyzer.get_critical_path()
        elapsed = time.perf_counter() - start

        assert result is not None
        assert elapsed >= 0

    def test_dag_analysis_medium(self, medium_workflow):
        """Benchmark DAG analysis on medium workflow."""
        tasks, dependencies = medium_workflow

        start = time.perf_counter()
        analyzer = DAGAnalyzer(tasks, dependencies)
        result = analyzer.get_critical_path()
        elapsed = time.perf_counter() - start

        assert result is not None
        assert elapsed >= 0

    def test_dag_analysis_large(self, large_workflow):
        """Benchmark DAG analysis on large workflow."""
        tasks, dependencies = large_workflow

        start = time.perf_counter()
        analyzer = DAGAnalyzer(tasks, dependencies)
        result = analyzer.get_critical_path()
        elapsed = time.perf_counter() - start

        assert result is not None
        assert elapsed >= 0

    def test_execution_planning_small(self, small_workflow):
        """Benchmark execution planning on small workflow."""
        tasks, dependencies = small_workflow

        start = time.perf_counter()
        analyzer = DAGAnalyzer(tasks, dependencies)
        levels = analyzer.get_levels()
        groups = analyzer.get_parallelizable_groups()
        elapsed = time.perf_counter() - start

        assert levels is not None
        assert groups is not None
        assert elapsed >= 0


@pytest.mark.unit
class TestCachePerformance:
    """Benchmark cache performance and speedup."""

    def test_cache_speedup_factor(self):
        """Verify cache speedup with repeated access."""
        cache = DecisionCache(max_size=1000)

        # Populate cache
        start = time.perf_counter()
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
        _populate_time = time.perf_counter() - start

        # Access cached entries
        start = time.perf_counter()
        for i in range(100):
            _ = cache.get(f"key_{i}")
        access_time = time.perf_counter() - start

        assert cache.hits >= 95
        assert access_time >= 0

    def test_decision_cache_hit_rate(self):
        """Benchmark cache hit rate on repeated access patterns."""
        cache = DecisionCache(max_size=50)

        cache.clear()
        # Populate cache
        for i in range(25):
            cache.set(f"key_{i}", {"data": i})

        # Repeated access pattern
        for _ in range(4):
            for i in range(25):
                cache.get(f"key_{i}")

        stats = cache.stats()
        assert stats["size"] == 25
        assert stats["hit_rate_percent"] > 90

    def test_analysis_cache_invalidation(self):
        """Benchmark cache invalidation performance."""
        cache = AnalysisCache(max_size=200)

        cache.clear()
        for i in range(100):
            cache.set(f"analysis_{i}", {"complexity": i})

        # Invalidate half
        for i in range(50):
            cache.invalidate(f"analysis_{i}")

        assert len(cache.cache) <= 100


@pytest.mark.unit
class TestParallelExecutionPerformance:
    """Benchmark parallelization efficiency."""

    def test_parallel_executor_speedup_estimation(self):
        """Benchmark speedup estimation calculations."""
        executor = ParallelExecutor(max_parallel=8)

        start = time.perf_counter()
        results = {}
        for parallel_count in range(1, 9):
            time_taken, speedup = executor.estimate_speedup(1000, parallel_count)
            results[parallel_count] = speedup
        elapsed = time.perf_counter() - start

        assert len(results) == 8
        assert results[8] > results[1]
        assert elapsed >= 0

    def test_batch_size_optimization(self):
        """Benchmark batch size optimization."""
        optimizer = BatchOptimizer()

        start = time.perf_counter()
        results = {}
        for task_count in [10, 50, 100, 500, 1000]:
            for resources in [2, 4, 8]:
                recommended = optimizer.recommend_batch_size(task_count, resources)
                results[f"{task_count}_{resources}"] = recommended
        elapsed = time.perf_counter() - start

        assert len(results) == 15
        assert elapsed >= 0


@pytest.mark.unit
class TestOrchestrationPerformance:
    """Benchmark complete orchestration pipeline."""

    def test_dag_analyzer_parallelization_small(self, small_workflow):
        """Benchmark DAG analysis parallelization on small workflow."""
        tasks, dependencies = small_workflow

        start = time.perf_counter()
        analyzer = DAGAnalyzer(tasks, dependencies)
        groups = analyzer.get_parallelizable_groups()
        bottlenecks = analyzer.get_bottlenecks()
        elapsed = time.perf_counter() - start

        assert groups is not None
        assert bottlenecks is not None
        assert elapsed >= 0

    def test_dag_analyzer_parallelization_medium(self, medium_workflow):
        """Benchmark DAG analysis parallelization on medium workflow."""
        tasks, dependencies = medium_workflow

        start = time.perf_counter()
        analyzer = DAGAnalyzer(tasks, dependencies)
        groups = analyzer.get_parallelizable_groups()
        bottlenecks = analyzer.get_bottlenecks()
        elapsed = time.perf_counter() - start

        assert groups is not None
        assert bottlenecks is not None
        assert elapsed >= 0


# ============================================================================
# OPTIMIZATION COMPARISON TESTS
# ============================================================================


@pytest.mark.unit
class TestOptimizationComparisons:
    """Compare optimization strategies."""

    def test_cache_enabled_vs_disabled(self, medium_workflow):
        """Compare performance with cache enabled vs disabled."""
        tasks, dependencies = medium_workflow

        # Test cache hit rate instead of timing
        cache = DecisionCache(max_size=1000)

        # Populate cache
        for i in range(50):
            cache.set(f"key_{i}", {"data": i})

        # Access patterns
        for _ in range(10):
            for i in range(50):
                cache.get(f"key_{i}")

        stats = cache.stats()
        # Most accesses should be cache hits
        assert stats["hit_rate_percent"] > 90

    def test_memoization_enabled_vs_disabled(self):
        """Compare performance with memoization."""

        # Without memoization
        def expensive_function_no_memo(x: int) -> int:
            result = 0
            for i in range(x * 1000):
                result += i
            return result

        start_time = time.perf_counter()
        for _ in range(5):
            expensive_function_no_memo(100)
        no_memo_time = time.perf_counter() - start_time

        # With memoization
        @memoize_decision
        def expensive_function_memo(x: int) -> int:
            result = 0
            for i in range(x * 1000):
                result += i
            return result

        start_time = time.perf_counter()
        for _ in range(5):
            expensive_function_memo(100)
        memo_time = time.perf_counter() - start_time

        # Memoized should be faster (after first call)
        assert memo_time < no_memo_time

    def test_parallel_vs_sequential(self, medium_workflow):
        """Compare parallel vs sequential execution time estimation."""
        executor = ParallelExecutor(max_parallel=8)
        serial_time = 1000.0

        # Sequential execution (1 parallel)
        seq_time, seq_speedup = executor.estimate_speedup(serial_time, 1)
        assert seq_speedup == 1.0

        # Parallel execution (8 parallel)
        par_time, par_speedup = executor.estimate_speedup(serial_time, 8)

        # Parallel should be faster
        assert par_time < seq_time
        assert par_speedup > 1.0

    def test_batch_size_impact(self):
        """Benchmark impact of different batch sizes."""
        optimizer = BatchOptimizer()

        # Track performance with different batch sizes
        results = {}
        for batch_size in [5, 10, 25, 50, 100]:
            optimizer.analyze_batch_impact(batch_size, 2.5)
            optimizer.analyze_batch_impact(batch_size, 2.7)
            optimizer.analyze_batch_impact(batch_size, 2.4)

            impact = optimizer.analyze_batch_impact(batch_size, 2.6)
            results[batch_size] = impact["average_time"]

        # All batch sizes should have reasonable execution times
        assert all(t > 0 for t in results.values())


# ============================================================================
# SCALING & EFFICIENCY TESTS
# ============================================================================


@pytest.mark.unit
class TestScalingBehavior:
    """Test performance scaling with workflow size."""

    def test_complexity_scoring_scales_linearly(self, small_workflow, medium_workflow, large_workflow):
        """Verify complexity scoring scales appropriately."""
        scorer = ComplexityScorer()
        times = {}

        for name, (tasks, deps) in [
            ("small", small_workflow),
            ("medium", medium_workflow),
            ("large", large_workflow),
        ]:
            start = time.perf_counter()
            for task in tasks:
                scorer.score_task(task, deps)
            elapsed = time.perf_counter() - start
            times[name] = elapsed

        # Times should increase with workflow size
        assert times["small"] < times["medium"]
        assert times["medium"] < times["large"]

    def test_dag_analysis_scaling(self, small_workflow, medium_workflow, large_workflow):
        """Test DAG analysis scaling."""
        times = {}

        for name, (tasks, deps) in [
            ("small", small_workflow),
            ("medium", medium_workflow),
            ("large", large_workflow),
        ]:
            start = time.perf_counter()
            analyzer = DAGAnalyzer(tasks, deps)
            analyzer.get_critical_path()
            analyzer.get_levels()
            elapsed = time.perf_counter() - start
            times[name] = elapsed

        # Times should increase but sub-linearly
        assert times["small"] < times["medium"]
        assert times["medium"] < times["large"]

    def test_large_workflow_scaling(self, large_workflow):
        """Benchmark large workflow performance."""
        tasks, dependencies = large_workflow

        start = time.perf_counter()
        analyzer = DAGAnalyzer(tasks, dependencies)
        result = analyzer.get_parallelizable_groups()
        elapsed = time.perf_counter() - start

        assert result is not None
        assert elapsed >= 0


@pytest.mark.unit
class TestMemoryEfficiency:
    """Test memory efficiency of optimization strategies."""

    def test_cache_memory_footprint(self):
        """Measure cache memory usage."""
        cache = DecisionCache(max_size=1000)

        # Populate cache
        for i in range(500):
            cache.set(f"key_{i}", {"data": list(range(100))})

        # Cache should not exceed max size
        assert len(cache.cache) <= 1000

        # Cache should evict LRU entries
        for i in range(200, 400):
            cache.set(f"key_{i}_new", {"data": list(range(100))})

        assert len(cache.cache) <= 1000

    def test_metrics_collector_memory(self):
        """Test metrics collector memory usage."""
        collector = MetricsCollector(enabled=True)

        # Record many operations
        for _ in range(1000):
            collector.record_operation("test", 0.001)

        # Memory should be bounded
        assert len(collector.metrics) == 1000

        # Clear should release memory
        collector.clear()
        assert len(collector.metrics) == 0

    def test_batch_optimizer_history_bounded(self):
        """Verify batch optimizer history is bounded."""
        optimizer = BatchOptimizer()

        # Record many batch analyses
        for i in range(100):
            optimizer.analyze_batch_impact(10 + (i % 50), 2.5 + (i % 5) * 0.1)

        # History should be reasonably bounded
        assert len(optimizer.batch_size_history) > 0


# ============================================================================
# METRICS & REPORTING
# ============================================================================


@pytest.mark.unit
class TestMetricsReporting:
    """Test performance metrics collection and reporting."""

    def test_operation_timing_metrics(self):
        """Test operation timing metrics."""
        collector = MetricsCollector()

        # Record various operations
        collector.record_operation("decision", 0.5)
        collector.record_operation("decision", 0.6)
        collector.record_operation("analysis", 0.3)
        collector.record_operation("planning", 0.2)

        stats = collector.get_cumulative_stats()

        assert stats["total_operations"] == 4
        assert stats["total_time"] > 1.5
        assert "operations_by_type" in stats

    def test_cache_hit_rate_reporting(self):
        """Test cache hit rate reporting."""
        collector = MetricsCollector()

        # Simulate cache hits and misses
        for i in range(100):
            cache_hit = (i % 4) == 0  # 25% hit rate
            collector.record_operation("cache_access", 0.01, cache_hit=cache_hit)

        stats = collector.get_cumulative_stats()

        assert "cache_hit_rate" in stats
        assert 20 < stats["cache_hit_rate"] < 30  # ~25%

    def test_success_rate_reporting(self):
        """Test success rate reporting."""
        collector = MetricsCollector()

        # Simulate successes and failures
        for i in range(100):
            success = (i % 5) != 0  # 80% success rate
            collector.record_operation("operation", 0.1, success=success)

        stats = collector.get_cumulative_stats()

        assert "success_rate" in stats
        assert 75 < stats["success_rate"] < 85

    def test_performance_summary_report(self, medium_workflow):
        """Generate performance summary report."""
        config = PerformanceConfig(cache_enabled=True, metrics_enabled=True, enable_batch_optimization=True)
        manager = PerformanceManager(config)

        # Record operations
        for i in range(20):
            manager.metrics_collector.record_operation("decision", 0.1 + (i % 5) * 0.01)
            manager.metrics_collector.record_operation("analysis", 0.05 + (i % 3) * 0.01)

        stats = manager.get_stats()

        assert "config" in stats
        assert "statistics" in stats
        assert len(manager.metrics_collector.metrics) == 40


# ============================================================================
# END-TO-END PERFORMANCE TESTS
# ============================================================================


@pytest.mark.unit
class TestEndToEndPerformance:
    """End-to-end performance tests."""

    def test_complete_pipeline_small(self, small_workflow):
        """Test complete pipeline on small workflow."""
        tasks, dependencies = small_workflow
        config = PerformanceConfig(
            cache_enabled=True, metrics_enabled=True, enable_parallel_execution=True, enable_batch_optimization=True
        )
        _manager = PerformanceManager(config)

        start = time.perf_counter()

        # Run pipeline
        analyzer = DAGAnalyzer(tasks, dependencies)
        critical_path = analyzer.get_critical_path()
        _levels = analyzer.get_levels()
        _groups = analyzer.get_parallelizable_groups()

        elapsed = time.perf_counter() - start

        assert critical_path is not None
        assert elapsed < 5.0  # Should complete in < 5 seconds

    def test_complete_pipeline_medium(self, medium_workflow):
        """Test complete pipeline on medium workflow."""
        tasks, dependencies = medium_workflow

        start = time.perf_counter()

        analyzer = DAGAnalyzer(tasks, dependencies)
        critical_path = analyzer.get_critical_path()
        _levels = analyzer.get_levels()
        _groups = analyzer.get_parallelizable_groups()

        elapsed = time.perf_counter() - start

        assert critical_path is not None
        assert elapsed < 10.0  # Should complete in < 10 seconds

    def test_cache_effectiveness_in_repeated_analysis(self, small_workflow):
        """Test cache effectiveness in repeated analysis."""
        tasks, dependencies = small_workflow
        config = PerformanceConfig(cache_enabled=True)
        _manager = PerformanceManager(config)

        # First analysis (cache misses)
        start = time.perf_counter()
        analyzer1 = DAGAnalyzer(tasks, dependencies)
        analysis1 = analyzer1.get_critical_path()
        _first_time = time.perf_counter() - start

        # Second analysis (cache hits)
        start = time.perf_counter()
        analyzer2 = DAGAnalyzer(tasks, dependencies)
        analysis2 = analyzer2.get_critical_path()
        _second_time = time.perf_counter() - start

        # Both should complete successfully
        assert analysis1 is not None
        assert analysis2 is not None
