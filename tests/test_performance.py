"""Unit tests for performance optimization module (Phase 5)."""

import pytest
import time
from datetime import datetime, timedelta
from parallelizer_skill.performance import (
    PerformanceConfig, OperationMetrics, CacheEntry, DecisionCache, AnalysisCache,
    memoize_decision, memoize_analysis, memoize_planning,
    ParallelExecutor, BatchOptimizer, MetricsCollector, PerformanceManager
)


@pytest.mark.unit
class TestCacheEntry:
    """Test cache entry functionality."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(key="test", value={"data": "value"}, ttl_seconds=100)
        assert entry.key == "test"
        assert entry.value == {"data": "value"}
        assert entry.ttl_seconds == 100
        assert entry.access_count == 0

    def test_cache_entry_not_expired(self):
        """Test cache entry is not expired when fresh."""
        entry = CacheEntry(key="test", value="data", ttl_seconds=3600)
        assert not entry.is_expired()

    def test_cache_entry_expired(self):
        """Test cache entry expiration detection."""
        entry = CacheEntry(key="test", value="data", ttl_seconds=1)
        entry.created_at = datetime.utcnow() - timedelta(seconds=2)
        assert entry.is_expired()

    def test_cache_entry_access_recording(self):
        """Test recording cache access."""
        entry = CacheEntry(key="test", value="data")
        assert entry.access_count == 0
        entry.record_access()
        assert entry.access_count == 1
        entry.record_access()
        assert entry.access_count == 2


@pytest.mark.unit
class TestDecisionCache:
    """Test decision cache functionality."""

    def test_decision_cache_creation(self):
        """Test creating decision cache."""
        cache = DecisionCache(max_size=100, ttl_seconds=1800)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 1800
        assert cache.hits == 0
        assert cache.misses == 0

    def test_decision_cache_hit(self):
        """Test cache hit."""
        cache = DecisionCache()
        cache.set("key1", {"value": 1})
        result = cache.get("key1")
        assert result == {"value": 1}
        assert cache.hits == 1
        assert cache.misses == 0

    def test_decision_cache_miss(self):
        """Test cache miss."""
        cache = DecisionCache()
        result = cache.get("nonexistent")
        assert result is None
        assert cache.hits == 0
        assert cache.misses == 1

    def test_decision_cache_ttl_expiry(self):
        """Test cache TTL expiration."""
        cache = DecisionCache(ttl_seconds=1)
        cache.set("key1", {"value": 1})
        # Manually expire the entry
        cache.cache["key1"].created_at = datetime.utcnow() - timedelta(seconds=2)
        result = cache.get("key1")
        assert result is None
        assert cache.misses == 1

    def test_decision_cache_size_limit(self):
        """Test cache eviction when size exceeded."""
        cache = DecisionCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert len(cache.cache) == 3
        cache.set("key4", "value4")
        assert len(cache.cache) == 3
        # LRU should evict key1 (least recently used)
        assert cache.get("key1") is None

    def test_decision_cache_lru_ordering(self):
        """Test LRU ordering when accessing entries."""
        cache = DecisionCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        # Access key1 to make it recently used
        cache.get("key1")
        cache.set("key4", "value4")
        # key2 should be evicted (least recently used)
        assert cache.get("key2") is None
        assert cache.get("key1") is not None

    def test_decision_cache_clear(self):
        """Test clearing cache."""
        cache = DecisionCache()
        cache.set("key1", "value1")
        cache.hits = 5
        cache.misses = 3
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_decision_cache_stats(self):
        """Test cache statistics."""
        cache = DecisionCache()
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_requests"] == 2
        assert stats["size"] == 1
        assert 49 < stats["hit_rate_percent"] < 51  # Approximately 50%


@pytest.mark.unit
class TestAnalysisCache:
    """Test analysis cache functionality."""

    def test_analysis_cache_creation(self):
        """Test creating analysis cache."""
        cache = AnalysisCache(max_size=200, ttl_seconds=3600)
        assert cache.max_size == 200
        assert cache.ttl_seconds == 3600

    def test_analysis_cache_get_set(self):
        """Test analysis cache get/set."""
        cache = AnalysisCache()
        cache.set("analysis1", {"complexity": 5})
        result = cache.get("analysis1")
        assert result == {"complexity": 5}

    def test_analysis_cache_invalidation(self):
        """Test cache invalidation."""
        cache = AnalysisCache()
        cache.set("analysis1", {"complexity": 5})
        cache.invalidate("analysis1")
        result = cache.get("analysis1")
        assert result is None

    def test_analysis_cache_clear(self):
        """Test clearing cache."""
        cache = AnalysisCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert len(cache.cache) == 0


@pytest.mark.unit
class TestMemoizeDecorators:
    """Test memoization decorators."""

    def test_memoize_decision(self):
        """Test decision memoization."""
        call_count = {"count": 0}

        @memoize_decision
        def test_decision(x: int) -> int:
            call_count["count"] += 1
            return x * 2

        result1 = test_decision(5)
        result2 = test_decision(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count["count"] == 1  # Should be called only once

    def test_memoize_decision_different_args(self):
        """Test memoization with different arguments."""
        call_count = {"count": 0}

        @memoize_decision
        def test_decision(x: int) -> int:
            call_count["count"] += 1
            return x * 2

        test_decision(5)
        test_decision(10)
        assert call_count["count"] == 2  # Different args, should call twice

    def test_memoize_analysis(self):
        """Test analysis memoization."""
        call_count = {"count": 0}

        @memoize_analysis
        def test_analysis(task_count: int) -> Dict:
            call_count["count"] += 1
            return {"tasks": task_count}

        result1 = test_analysis(10)
        result2 = test_analysis(10)
        assert result1 == {"tasks": 10}
        assert result2 == {"tasks": 10}
        assert call_count["count"] == 1

    def test_memoize_planning(self):
        """Test planning memoization."""
        call_count = {"count": 0}

        @memoize_planning
        def test_planning(task_id: str) -> str:
            call_count["count"] += 1
            return f"plan_{task_id}"

        result1 = test_planning("task1")
        result2 = test_planning("task1")
        assert result1 == "plan_task1"
        assert result2 == "plan_task1"
        assert call_count["count"] == 1

    def test_memoize_decorator_cache_access(self):
        """Test accessing cache from memoized function."""
        @memoize_decision
        def test_func(x: int) -> int:
            return x * 2

        test_func(5)
        assert hasattr(test_func, "cache")
        assert test_func.cache.hits == 0  # First call is a miss
        test_func(5)
        assert test_func.cache.hits == 1  # Second call is a hit


@pytest.mark.unit
class TestParallelExecutor:
    """Test parallel execution optimization."""

    def test_parallel_executor_creation(self):
        """Test creating parallel executor."""
        executor = ParallelExecutor(max_parallel=4)
        assert executor.max_parallel == 4

    def test_can_execute_parallel(self):
        """Test checking parallel execution feasibility."""
        executor = ParallelExecutor(max_parallel=4)
        assert executor.can_execute_parallel(3) is True
        assert executor.can_execute_parallel(4) is True
        assert executor.can_execute_parallel(5) is False

    def test_get_optimal_parallel_count(self):
        """Test getting optimal parallel count."""
        executor = ParallelExecutor(max_parallel=6)
        assert executor.get_optimal_parallel_count(3) == 3
        assert executor.get_optimal_parallel_count(6) == 6
        assert executor.get_optimal_parallel_count(10) == 6

    def test_estimate_speedup_no_parallelization(self):
        """Test speedup estimation with no parallelization."""
        executor = ParallelExecutor()
        estimated_time, speedup = executor.estimate_speedup(100, 1)
        assert estimated_time == 100
        assert speedup == 1.0

    def test_estimate_speedup_with_parallelization(self):
        """Test speedup estimation with parallelization."""
        executor = ParallelExecutor(max_parallel=4)
        serial_time = 100
        estimated_time, speedup = executor.estimate_speedup(serial_time, 4)
        assert estimated_time < serial_time
        assert speedup > 1.0

    def test_estimate_speedup_multiple_parallel(self):
        """Test speedup improves with more parallelization."""
        executor = ParallelExecutor(max_parallel=8)
        serial_time = 100
        _, speedup2 = executor.estimate_speedup(serial_time, 2)
        _, speedup4 = executor.estimate_speedup(serial_time, 4)
        assert speedup4 > speedup2


@pytest.mark.unit
class TestBatchOptimizer:
    """Test batch optimization."""

    def test_batch_optimizer_creation(self):
        """Test creating batch optimizer."""
        optimizer = BatchOptimizer()
        assert len(optimizer.batch_size_history) == 0

    def test_analyze_batch_impact(self):
        """Test analyzing batch impact."""
        optimizer = BatchOptimizer()
        result = optimizer.analyze_batch_impact(batch_size=10, execution_time=5.0)
        assert result["batch_size"] == 10
        assert result["execution_time"] == 5.0
        assert result["samples"] == 1
        assert result["average_time"] == 5.0

    def test_analyze_batch_impact_multiple_samples(self):
        """Test batch impact with multiple samples."""
        optimizer = BatchOptimizer()
        optimizer.analyze_batch_impact(10, 5.0)
        optimizer.analyze_batch_impact(10, 6.0)
        optimizer.analyze_batch_impact(10, 4.5)
        result = optimizer.analyze_batch_impact(10, 5.5)
        assert result["samples"] == 4
        assert abs(result["average_time"] - 5.25) < 0.01

    def test_recommend_batch_size(self):
        """Test batch size recommendation."""
        optimizer = BatchOptimizer()
        # For 100 tasks with 6 resources
        recommended = optimizer.recommend_batch_size(task_count=100, available_resources=6)
        assert recommended > 0
        assert recommended <= 100

    def test_recommend_batch_size_small_task_count(self):
        """Test batch recommendation for small task count."""
        optimizer = BatchOptimizer()
        recommended = optimizer.recommend_batch_size(task_count=5, available_resources=6)
        assert 0 < recommended <= 5

    def test_get_performance_trends(self):
        """Test getting performance trends."""
        optimizer = BatchOptimizer()
        optimizer.analyze_batch_impact(10, 5.0)
        optimizer.analyze_batch_impact(10, 6.0)
        optimizer.analyze_batch_impact(20, 4.0)
        trends = optimizer.get_performance_trends()
        assert 10 in trends
        assert 20 in trends
        assert trends[10]["samples"] == 2
        assert trends[20]["samples"] == 1


@pytest.mark.unit
class TestMetricsCollector:
    """Test metrics collection."""

    def test_metrics_collector_creation(self):
        """Test creating metrics collector."""
        collector = MetricsCollector(enabled=True)
        assert collector.enabled is True
        assert len(collector.metrics) == 0

    def test_record_operation(self):
        """Test recording an operation."""
        collector = MetricsCollector()
        collector.record_operation("decision", duration_seconds=0.5)
        assert len(collector.metrics) == 1
        assert collector.metrics[0].operation_name == "decision"
        assert collector.metrics[0].duration_seconds == 0.5

    def test_record_operation_disabled(self):
        """Test recording when disabled."""
        collector = MetricsCollector(enabled=False)
        collector.record_operation("decision", duration_seconds=0.5)
        assert len(collector.metrics) == 0

    def test_record_operation_with_cache_hit(self):
        """Test recording operation with cache hit."""
        collector = MetricsCollector()
        collector.record_operation("analysis", duration_seconds=0.1, cache_hit=True)
        assert collector.metrics[0].cache_hit is True

    def test_get_operation_stats(self):
        """Test getting operation statistics."""
        collector = MetricsCollector()
        collector.record_operation("decision", 0.5)
        collector.record_operation("decision", 0.6)
        collector.record_operation("analysis", 0.2)
        stats = collector.get_operation_stats("decision")
        assert stats["count"] == 2
        assert stats["total_time"] == 1.1
        assert abs(stats["avg_time"] - 0.55) < 0.01

    def test_get_operation_stats_all(self):
        """Test getting stats for all operations."""
        collector = MetricsCollector()
        collector.record_operation("decision", 0.5)
        collector.record_operation("analysis", 0.2)
        stats = collector.get_operation_stats()
        assert stats["count"] == 2

    def test_get_cumulative_stats(self):
        """Test getting cumulative statistics."""
        collector = MetricsCollector()
        collector.record_operation("decision", 0.5)
        collector.record_operation("analysis", 0.2)
        collector.record_operation("planning", 0.3)
        stats = collector.get_cumulative_stats()
        assert stats["total_operations"] == 3
        assert abs(stats["total_time"] - 1.0) < 0.01
        assert "operations_by_type" in stats

    def test_get_cumulative_stats_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        collector = MetricsCollector()
        collector.record_operation("decision", 0.5, cache_hit=True)
        collector.record_operation("decision", 0.1, cache_hit=True)
        collector.record_operation("analysis", 0.2, cache_hit=False)
        stats = collector.get_cumulative_stats()
        assert abs(stats["cache_hit_rate"] - 66.67) < 1  # Approximately 66.67%

    def test_get_cumulative_stats_success_rate(self):
        """Test success rate calculation."""
        collector = MetricsCollector()
        collector.record_operation("decision", 0.5, success=True)
        collector.record_operation("analysis", 0.2, success=False)
        stats = collector.get_cumulative_stats()
        assert abs(stats["success_rate"] - 50.0) < 1

    def test_metrics_collector_clear(self):
        """Test clearing metrics."""
        collector = MetricsCollector()
        collector.record_operation("decision", 0.5)
        assert len(collector.metrics) == 1
        collector.clear()
        assert len(collector.metrics) == 0


@pytest.mark.unit
class TestPerformanceManager:
    """Test overall performance manager."""

    def test_performance_manager_creation(self):
        """Test creating performance manager."""
        config = PerformanceConfig(cache_enabled=True)
        manager = PerformanceManager(config)
        assert manager.config.cache_enabled is True
        assert manager.decision_cache is not None
        assert manager.metrics_collector is not None

    def test_performance_manager_caching_disabled(self):
        """Test manager with caching disabled."""
        config = PerformanceConfig(cache_enabled=False)
        manager = PerformanceManager(config)
        assert manager.decision_cache is None
        assert manager.analysis_cache is None

    def test_performance_manager_parallelization_disabled(self):
        """Test manager with parallelization disabled."""
        config = PerformanceConfig(enable_parallel_execution=False)
        manager = PerformanceManager(config)
        assert manager.parallel_executor is None

    def test_performance_manager_get_stats(self):
        """Test getting stats from manager."""
        config = PerformanceConfig(
            cache_enabled=True,
            metrics_enabled=True,
            enable_batch_optimization=True
        )
        manager = PerformanceManager(config)
        manager.metrics_collector.record_operation("decision", 0.5)
        stats = manager.get_stats()
        assert "config" in stats
        assert "statistics" in stats

    def test_performance_manager_clear_caches(self):
        """Test clearing all caches."""
        config = PerformanceConfig(cache_enabled=True)
        manager = PerformanceManager(config)
        manager.decision_cache.set("key1", "value1")
        manager.metrics_collector.record_operation("decision", 0.5)
        manager.clear_caches()
        assert manager.decision_cache.get("key1") is None
        assert len(manager.metrics_collector.metrics) == 0


@pytest.mark.integration
class TestPerformanceIntegration:
    """Integration tests for performance optimization."""

    def test_decision_cache_improves_performance(self):
        """Test that decision caching improves performance."""
        cache = DecisionCache()

        # Simulate decision operation
        def make_decision(goal: str, complexity: int) -> Dict:
            return {"goal": goal, "complexity": complexity, "timestamp": time.time()}

        cache_key = "test_decision"

        # First call - cache miss
        start = time.time()
        result1 = make_decision("performance", 5)
        first_call_time = time.time() - start
        cache.set(cache_key, result1)

        # Second call - cache hit
        start = time.time()
        result2 = cache.get(cache_key)
        second_call_time = time.time() - start

        assert result2 is not None
        # Cache hit should be faster (or at least not slower)
        assert second_call_time <= first_call_time + 0.01  # Small margin for timing variance

    def test_parallel_executor_speedup_calculation(self):
        """Test parallel executor speedup calculation."""
        executor = ParallelExecutor(max_parallel=8)
        serial_time = 1000  # 1000 units

        _, speedup1 = executor.estimate_speedup(serial_time, 1)
        _, speedup2 = executor.estimate_speedup(serial_time, 2)
        _, speedup4 = executor.estimate_speedup(serial_time, 4)
        _, speedup8 = executor.estimate_speedup(serial_time, 8)

        # Speedup should improve with more parallelization
        assert speedup1 < speedup2 < speedup4 < speedup8

    def test_metrics_collection_complete_workflow(self):
        """Test metrics collection for complete workflow."""
        collector = MetricsCollector()

        # Simulate workflow
        collector.record_operation("analysis", 0.5)
        collector.record_operation("analysis", 0.4, cache_hit=True)
        collector.record_operation("decision", 0.3)
        collector.record_operation("planning", 0.2)
        collector.record_operation("planning", 0.15, cache_hit=True)

        stats = collector.get_cumulative_stats()
        assert stats["total_operations"] == 5
        assert abs(stats["total_time"] - 1.55) < 0.01
        assert stats["cache_hits"] == 2
        assert abs(stats["cache_hit_rate"] - 40.0) < 1


@pytest.mark.performance
class TestPerformanceImprovement:
    """Performance improvement tests."""

    def test_memoization_speedup(self):
        """Test that memoization provides measurable speedup."""

        @memoize_decision
        def expensive_decision(task_count: int) -> int:
            # Simulate expensive operation
            result = 0
            for i in range(task_count * 100):
                result += i
            return result

        # First call
        start = time.time()
        result1 = expensive_decision(100)
        first_call_time = time.time() - start

        # Second call (memoized)
        start = time.time()
        result2 = expensive_decision(100)
        second_call_time = time.time() - start

        assert result1 == result2
        # Memoized call should be faster than first call
        assert second_call_time < first_call_time  # Memoized should be faster

    def test_cache_reduces_redundant_work(self):
        """Test that caching reduces redundant work."""
        cache = DecisionCache(max_size=100)

        call_count = 0

        def cached_operation(key: str) -> Dict:
            nonlocal call_count
            call_count += 1
            return {"key": key, "call": call_count}

        # Fill cache
        for i in range(50):
            result = cached_operation(f"key_{i}")
            cache.set(f"key_{i}", result)

        # Access cached entries
        initial_calls = call_count
        for i in range(50):
            cache.get(f"key_{i}")

        final_calls = call_count
        # No new calls should be made for cached entries
        assert final_calls == initial_calls

    def test_batch_optimization_recommendation(self):
        """Test batch optimization provides reasonable recommendations."""
        optimizer = BatchOptimizer()

        # Test various task counts
        for task_count in [10, 50, 100, 1000]:
            recommended = optimizer.recommend_batch_size(task_count, 6)
            assert 0 < recommended <= task_count
            assert recommended >= 1


# Import Dict for type hints
from typing import Dict
