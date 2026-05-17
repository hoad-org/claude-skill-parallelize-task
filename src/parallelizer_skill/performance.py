"""Performance optimization module with caching, memoization, and metrics (Phase 5)."""

import hashlib
import time
from dataclasses import dataclass, field, asdict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
import threading


@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    enable_memoization: bool = True
    enable_parallel_execution: bool = True
    metrics_enabled: bool = True
    enable_batch_optimization: bool = True


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""
    operation_name: str
    duration_seconds: float
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    cache_hit: bool = False
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_name": self.operation_name,
            "duration_seconds": self.duration_seconds,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "cache_hit": self.cache_hit,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class CacheEntry:
    """Single cache entry with TTL and metadata."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 3600
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        age = datetime.utcnow() - self.created_at
        return age.total_seconds() > self.ttl_seconds

    def record_access(self) -> None:
        """Record access for LRU tracking."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class DecisionCache:
    """LRU cache for decision engine results with TTL support."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize cache."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None

            entry.record_access()
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]

            self.cache[key] = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=self.ttl_seconds
            )

            # Evict least recently used if over limit
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": total,
                "hit_rate_percent": hit_rate,
            }


class AnalysisCache:
    """Cache for complexity analysis results."""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 7200):
        """Initialize analysis cache."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached analysis."""
        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None

            entry.record_access()
            self.hits += 1
            self.cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any) -> None:
        """Cache analysis result."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]

            self.cache[key] = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=self.ttl_seconds
            )

            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """Invalidate specific cache entry."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": total,
                "hit_rate_percent": hit_rate,
            }


def _hash_args(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """Create hash of function arguments."""
    try:
        # Convert args and kwargs to JSON-serializable format
        serializable = {
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        content = str(serializable).encode('utf-8')
        return hashlib.md5(content).hexdigest()
    except Exception:
        # Fallback: use object ids if not serializable
        return hashlib.md5(str(id(args)).encode('utf-8')).hexdigest()


def memoize_decision(func: Callable) -> Callable:
    """Memoize decision engine calls."""
    cache = DecisionCache(max_size=500, ttl_seconds=3600)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        cache_key = _hash_args(args, kwargs)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = func(*args, **kwargs)
        cache.set(cache_key, result)
        return result

    wrapper.cache = cache  # type: ignore
    return wrapper


def memoize_analysis(func: Callable) -> Callable:
    """Memoize complexity analysis calls."""
    cache = AnalysisCache(max_size=300, ttl_seconds=7200)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        cache_key = _hash_args(args, kwargs)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = func(*args, **kwargs)
        cache.set(cache_key, result)
        return result

    wrapper.cache = cache  # type: ignore
    return wrapper


def memoize_planning(func: Callable) -> Callable:
    """Memoize execution planning calls."""
    cache = AnalysisCache(max_size=200, ttl_seconds=5400)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        cache_key = _hash_args(args, kwargs)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = func(*args, **kwargs)
        cache.set(cache_key, result)
        return result

    wrapper.cache = cache  # type: ignore
    return wrapper


class ParallelExecutor:
    """Execute independent task groups in parallel."""

    def __init__(self, max_parallel: int = 6):
        """Initialize executor."""
        self.max_parallel = max_parallel
        self.active_tasks = 0
        self._lock = threading.RLock()

    def can_execute_parallel(self, task_count: int) -> bool:
        """Check if tasks can run in parallel given constraints."""
        with self._lock:
            return task_count <= self.max_parallel

    def get_optimal_parallel_count(self, task_count: int) -> int:
        """Get optimal number of parallel tasks."""
        return min(task_count, self.max_parallel)

    def estimate_speedup(self, serial_time: float, parallel_count: int) -> Tuple[float, float]:
        """Estimate speedup from parallelization."""
        if parallel_count <= 1:
            return serial_time, 1.0

        # Assume linear speedup with diminishing returns for overhead
        overhead_factor = 1.0 + (0.05 * (parallel_count - 1))  # 5% per extra parallel task
        estimated_parallel_time = (serial_time / parallel_count) * overhead_factor

        speedup = serial_time / estimated_parallel_time if estimated_parallel_time > 0 else 1.0
        return estimated_parallel_time, speedup


class BatchOptimizer:
    """Optimize batching strategy for task execution."""

    def __init__(self):
        """Initialize optimizer."""
        self.batch_size_history: Dict[int, List[float]] = {}

    def analyze_batch_impact(self, batch_size: int, execution_time: float) -> Dict[str, Any]:
        """Analyze impact of batch size on execution time."""
        if batch_size not in self.batch_size_history:
            self.batch_size_history[batch_size] = []

        self.batch_size_history[batch_size].append(execution_time)

        return {
            "batch_size": batch_size,
            "execution_time": execution_time,
            "samples": len(self.batch_size_history[batch_size]),
            "average_time": sum(self.batch_size_history[batch_size]) / len(self.batch_size_history[batch_size]),
        }

    def recommend_batch_size(self, task_count: int, available_resources: int = 6) -> int:
        """Recommend optimal batch size."""
        # Simple heuristic: batch size = sqrt(task_count) * resource_factor
        base_size = max(1, int((task_count ** 0.5)))
        recommended = min(base_size * available_resources, task_count)
        return max(1, recommended)

    def get_performance_trends(self) -> Dict[int, Dict[str, float]]:
        """Get performance trends by batch size."""
        trends = {}
        for batch_size, times in self.batch_size_history.items():
            trends[batch_size] = {
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "samples": len(times),
            }
        return trends


class MetricsCollector:
    """Collect and aggregate performance metrics."""

    def __init__(self, enabled: bool = True):
        """Initialize collector."""
        self.enabled = enabled
        self.metrics: List[OperationMetrics] = []
        self._lock = threading.RLock()

    def record_operation(
        self,
        operation_name: str,
        duration_seconds: float,
        cache_hit: bool = False,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a single operation."""
        if not self.enabled:
            return

        with self._lock:
            metric = OperationMetrics(
                operation_name=operation_name,
                duration_seconds=duration_seconds,
                cache_hit=cache_hit,
                success=success,
                error_message=error_message,
            )
            self.metrics.append(metric)

    def get_operation_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for operations."""
        with self._lock:
            if operation_name:
                ops = [m for m in self.metrics if m.operation_name == operation_name]
            else:
                ops = self.metrics

            if not ops:
                return {"count": 0, "operations": []}

            durations = [m.duration_seconds for m in ops]
            cache_hits = sum(1 for m in ops if m.cache_hit)

            return {
                "operation": operation_name or "all",
                "count": len(ops),
                "total_time": sum(durations),
                "min_time": min(durations),
                "max_time": max(durations),
                "avg_time": sum(durations) / len(durations),
                "cache_hits": cache_hits,
                "cache_hit_rate": (cache_hits / len(ops) * 100) if ops else 0,
                "success_rate": (sum(1 for m in ops if m.success) / len(ops) * 100) if ops else 0,
            }

    def get_cumulative_stats(self) -> Dict[str, Any]:
        """Get cumulative statistics across all operations."""
        with self._lock:
            if not self.metrics:
                return {"total_operations": 0}

            all_durations = [m.duration_seconds for m in self.metrics]
            all_cache_hits = sum(1 for m in self.metrics if m.cache_hit)
            all_success = sum(1 for m in self.metrics if m.success)

            ops_by_name = {}
            for metric in self.metrics:
                if metric.operation_name not in ops_by_name:
                    ops_by_name[metric.operation_name] = []
                ops_by_name[metric.operation_name].append(metric)

            return {
                "total_operations": len(self.metrics),
                "total_time": sum(all_durations),
                "min_time": min(all_durations),
                "max_time": max(all_durations),
                "avg_time": sum(all_durations) / len(all_durations),
                "cache_hits": all_cache_hits,
                "cache_hit_rate": (all_cache_hits / len(self.metrics) * 100),
                "success_rate": (all_success / len(self.metrics) * 100),
                "operations_by_type": {
                    op_name: len(metrics)
                    for op_name, metrics in ops_by_name.items()
                },
            }

    def clear(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()


class PerformanceManager:
    """Central manager for all performance optimizations."""

    def __init__(self, config: PerformanceConfig):
        """Initialize performance manager."""
        self.config = config
        self.decision_cache = DecisionCache(
            max_size=config.cache_max_size,
            ttl_seconds=config.cache_ttl_seconds
        ) if config.cache_enabled else None
        self.analysis_cache = AnalysisCache(
            max_size=config.cache_max_size // 2,
            ttl_seconds=config.cache_ttl_seconds
        ) if config.cache_enabled else None
        self.parallel_executor = ParallelExecutor() if config.enable_parallel_execution else None
        self.batch_optimizer = BatchOptimizer() if config.enable_batch_optimization else None
        self.metrics_collector = MetricsCollector(enabled=config.metrics_enabled)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = {}

        if self.config.cache_enabled and self.decision_cache:
            stats["decision_cache"] = self.decision_cache.stats()

        if self.config.cache_enabled and self.analysis_cache:
            stats["analysis_cache"] = self.analysis_cache.stats()

        if self.config.metrics_enabled:
            stats["metrics"] = self.metrics_collector.get_cumulative_stats()

        if self.config.enable_batch_optimization and self.batch_optimizer:
            stats["batch_optimization"] = self.batch_optimizer.get_performance_trends()

        return {
            "config": asdict(self.config),
            "statistics": stats,
        }

    def clear_caches(self) -> None:
        """Clear all caches."""
        if self.decision_cache:
            self.decision_cache.clear()
        if self.analysis_cache:
            self.analysis_cache.clear()
        self.metrics_collector.clear()
