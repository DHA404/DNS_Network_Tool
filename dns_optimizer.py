#!/usr/bin/env python3
# DNS智能优化模块 - 包含服务器选择、熔断器、指数退避重试

import time
import random
import threading
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import requests


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 断开
    HALF_OPEN = "half_open"  # 半开


@dataclass
class ServerMetrics:
    """DNS服务器指标"""
    server: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    last_success_time: float = 0
    last_failure_time: float = 0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    score: float = 100.0
    circuit_state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """熔断器实现"""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        timeout_seconds: float = 30.0
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.consecutive_successes = 0
        self.last_failure_time = 0
        self._lock = threading.Lock()

    def record_success(self):
        """记录成功"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.consecutive_successes += 1
                if self.consecutive_successes >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            else:
                self.consecutive_successes = 1

    def record_failure(self):
        """记录失败"""
        with self._lock:
            self.failure_count += 1
            self.consecutive_successes = 0
            self.last_failure_time = time.time()

            if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN

    def allow_request(self) -> bool:
        """是否允许请求"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.consecutive_successes = 0
                    return True
                return False
            else:  # HALF_OPEN
                return True

    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state


class ExponentialBackoff:
    """指数退避策略"""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5,
        jitter: bool = True
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """获取延迟时间"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)
        return delay

    def should_retry(self, attempt: int, error: Optional[Exception] = None) -> bool:
        """是否应该重试"""
        if attempt >= self.max_retries:
            return False
        return True

    def execute_with_retry(
        self,
        func,
        *args,
        retry_on: tuple = (requests.RequestException, ConnectionError, TimeoutError)
    ) -> Any:
        """带重试的执行"""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args)
            except retry_on as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    time.sleep(delay)
        raise last_error


class DNSServerGrouper:
    """DNS服务器分组管理器 - 根据响应时间将服务器分组，优先使用快速组"""
    
    FAST_THRESHOLD_MS = 100      # 快速服务器阈值 (毫秒)
    MEDIUM_THRESHOLD_MS = 300    # 中速服务器阈值 (毫秒)
    
    def __init__(self, dns_servers: List[str]):
        """初始化DNS服务器分组器
        
        Args:
            dns_servers: DNS服务器列表
        """
        self.all_servers = dns_servers
        self.fast_servers: List[str] = []
        self.medium_servers: List[str] = []
        self.slow_servers: List[str] = []
        self.unknown_servers: List[str] = []
        self.server_latency_history: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._initialize_groups()
    
    def _initialize_groups(self):
        """初始化分组，将所有服务器标记为未知"""
        self.unknown_servers = list(self.all_servers)
    
    def update_server_latency(self, server: str, latency_ms: float):
        """更新服务器延迟信息
        
        Args:
            server: 服务器地址
            latency_ms: 延迟时间（毫秒）
        """
        with self._lock:
            if server not in self.server_latency_history:
                self.server_latency_history[server] = []
            
            history = self.server_latency_history[server]
            history.append(latency_ms)
            if len(history) > 10:
                history.pop(0)
            
            self._reclassify_server(server)
    
    def _reclassify_server(self, server: str):
        """重新分类单个服务器"""
        if server not in self.server_latency_history or not self.server_latency_history[server]:
            return
        
        avg_latency = statistics.mean(self.server_latency_history[server])
        
        self._remove_from_all_groups(server)
        
        if avg_latency <= self.FAST_THRESHOLD_MS:
            self.fast_servers.append(server)
        elif avg_latency <= self.MEDIUM_THRESHOLD_MS:
            self.medium_servers.append(server)
        else:
            self.slow_servers.append(server)
        
        if server in self.unknown_servers:
            self.unknown_servers.remove(server)
    
    def _remove_from_all_groups(self, server: str):
        """从所有分组中移除服务器"""
        if server in self.fast_servers:
            self.fast_servers.remove(server)
        if server in self.medium_servers:
            self.medium_servers.remove(server)
        if server in self.slow_servers:
            self.slow_servers.remove(server)
    
    def get_servers_by_priority(self, count: int = None) -> List[str]:
        """按优先级获取服务器列表
        
        优先从快速组获取，快速组不足时从中级组获取，依此类推
        
        Args:
            count: 需要获取的服务器数量
            
        Returns:
            按优先级排序的服务器列表
        """
        if count is None:
            count = len(self.all_servers)
        
        result = []
        groups = [self.fast_servers, self.medium_servers, self.slow_servers, self.unknown_servers]
        
        for group in groups:
            remaining = count - len(result)
            if remaining <= 0:
                break
            result.extend(group[:remaining])
        
        return result[:count]
    
    def get_fast_servers(self, count: int = None) -> List[str]:
        """获取快速组服务器
        
        Args:
            count: 需要获取的服务器数量
            
        Returns:
            快速组服务器列表
        """
        if count is None:
            return list(self.fast_servers)
        return self.fast_servers[:count]
    
    def get_group_stats(self) -> Dict[str, Any]:
        """获取分组统计信息
        
        Returns:
            分组统计信息字典
        """
        return {
            "total_servers": len(self.all_servers),
            "fast_count": len(self.fast_servers),
            "medium_count": len(self.medium_servers),
            "slow_count": len(self.slow_servers),
            "unknown_count": len(self.unknown_servers),
            "fast_servers": list(self.fast_servers),
            "medium_servers": list(self.medium_servers),
            "slow_servers": list(self.slow_servers)
        }


class SmartDNSPool:
    """智能DNS服务器池管理器 - 整合分组策略和性能评分"""
    
    def __init__(
        self,
        dns_servers: List[str],
        min_servers: int = 8,
        max_servers: int = 20,
        failure_threshold: int = 5,
        timeout_seconds: float = 30.0
    ):
        self.all_servers = dns_servers
        self.min_servers = min_servers
        self.max_servers = max_servers
        
        self._servers: Dict[str, ServerMetrics] = {}
        self._lock = threading.Lock()
        
        self.server_grouper = DNSServerGrouper(dns_servers)
        
        for server in dns_servers:
            self._servers[server] = ServerMetrics(server=server)
            self._servers[server].circuit_breaker = CircuitBreaker(
                failure_threshold=failure_threshold,
                timeout_seconds=timeout_seconds
            )
        
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化服务器池，选择初始可用服务器"""
        available = [s for s in self.all_servers if self._servers[s].circuit_breaker.get_state() == CircuitState.CLOSED]
        if len(available) < self.min_servers:
            for server in self.all_servers:
                if len(available) >= self.min_servers:
                    break
                self._servers[server].circuit_breaker = CircuitBreaker()

    def select_servers(self, count: int = None) -> List[str]:
        """根据性能评分和分组策略选择最优服务器
        
        优先从快速组选择，快速组不足时从中级组选择
        
        Args:
            count: 需要选择的服务器数量
            
        Returns:
            选择的服务器列表
        """
        if count is None:
            count = min(self.max_servers, len(self.all_servers))
        
        available = []
        for server, metrics in self._servers.items():
            if metrics.circuit_breaker.get_state() == CircuitState.CLOSED:
                available.append((server, metrics.score))
        
        if len(available) < self.min_servers:
            for server in self.all_servers:
                if len(available) >= self.min_servers:
                    break
                if server not in [s[0] for s in available]:
                    available.append((server, 50.0))
        
        available.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in available[:count]]
    
    def select_servers_by_group(self, count: int = None) -> List[str]:
        """使用分组策略选择服务器（优先快速组）
        
        这种方法优先从已知的快速服务器组中选择，
        如果快速组数量不足，则从中级组和慢速组补充。
        
        Args:
            count: 需要选择的服务器数量
            
        Returns:
            选择的服务器列表
        """
        if count is None:
            count = min(self.max_servers, len(self.all_servers))
        
        return self.server_grouper.get_servers_by_priority(count)
    
    def update_server_metrics(
        self,
        server: str,
        success: bool,
        response_time_ms: float
    ):
        """更新服务器指标，同时更新分组信息
        
        Args:
            server: 服务器地址
            success: 是否成功
            response_time_ms: 响应时间（毫秒）
        """
        with self._lock:
            if server not in self._servers:
                return
            
            metrics = self._servers[server]
            metrics.total_requests += 1
            metrics.response_times.append(response_time_ms)
            
            if len(metrics.response_times) > 20:
                metrics.response_times.pop(0)
            
            if success:
                metrics.successful_requests += 1
                metrics.last_success_time = time.time()
                metrics.circuit_breaker.record_success()
            else:
                metrics.failed_requests += 1
                metrics.last_failure_time = time.time()
                metrics.circuit_breaker.record_failure()
            
            if metrics.total_requests > 0:
                metrics.error_rate = metrics.failed_requests / metrics.total_requests
            
            if metrics.response_times:
                metrics.avg_response_time = statistics.mean(metrics.response_times)
            
            metrics.score = self._calculate_score(metrics)
        
        self.server_grouper.update_server_latency(server, response_time_ms)

    def _calculate_score(self, metrics: ServerMetrics) -> float:
        """计算服务器综合评分 (0-100)"""
        if metrics.total_requests == 0:
            return 80.0

        score = 100.0

        if metrics.error_rate > 0:
            score -= metrics.error_rate * 50

        if metrics.avg_response_time > 0:
            if metrics.avg_response_time < 100:
                score -= 0
            elif metrics.avg_response_time < 300:
                score -= 5
            elif metrics.avg_response_time < 600:
                score -= 15
            elif metrics.avg_response_time < 1000:
                score -= 25
            else:
                score -= 40

        if metrics.circuit_breaker.get_state() == CircuitState.OPEN:
            score = 0

        return max(0, min(100, score))

    def get_pool_stats(self) -> Dict[str, Any]:
        """获取池统计信息"""
        total = len(self._servers)
        closed = sum(1 for m in self._servers.values() if m.circuit_breaker.get_state() == CircuitState.CLOSED)
        open_ = sum(1 for m in self._servers.values() if m.circuit_breaker.get_state() == CircuitState.OPEN)
        half_open = sum(1 for m in self._servers.values() if m.circuit_breaker.get_state() == CircuitState.HALF_OPEN)

        avg_score = statistics.mean([m.score for m in self._servers.values()]) if self._servers else 0
        avg_response = statistics.mean([m.avg_response_time for m in self._servers.values() if m.avg_response_time > 0]) if self._servers else 0

        return {
            "total_servers": total,
            "closed_circuits": closed,
            "open_circuits": open_,
            "half_open_circuits": half_open,
            "avg_score": round(avg_score, 2),
            "avg_response_time_ms": round(avg_response, 2),
            "top_servers": sorted(
                [(s, m.score) for s, m in self._servers.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


class DNSPrefetcher:
    """DNS预取器 - 提前解析可能需要的域名"""

    def __init__(self, dns_resolver):
        self.dns_resolver = dns_resolver

    def prefetch(self, domains: List[str]):
        """预取域名"""
        # 由于取消缓存功能，预取功能也取消
        pass

    def get(self, domain: str) -> Optional[Dict]:
        """获取预取结果"""
        # 由于取消缓存功能，直接返回None
        return None


class AdaptiveTimeout:
    """自适应超时管理器"""

    def __init__(
        self,
        base_timeout: float = 2.0,
        min_timeout: float = 0.5,
        max_timeout: float = 10.0,
        adaptation_factor: float = 0.8
    ):
        self.base_timeout = base_timeout
        self.min_timeout = min_timeout
        self.max_timeout = max_timeout
        self.adaptation_factor = adaptation_factor
        self._history: Dict[str, List[float]] = defaultdict(list)

    def get_timeout(self, server: str) -> float:
        """根据服务器历史获取超时时间"""
        if server not in self._history or not self._history[server]:
            return self.base_timeout

        recent_times = self._history[server][-10:]
        avg_time = statistics.mean(recent_times)

        timeout = avg_time * self.adaptation_factor * 2
        timeout = max(self.min_timeout, min(self.max_timeout, timeout))

        return timeout

    def update(self, server: str, response_time: float, success: bool):
        """更新超时历史"""
        self._history[server].append(response_time)
        if len(self._history[server]) > 20:
            self._history[server].pop(0)


def create_optimized_dns_pool(dns_servers: List[str]) -> SmartDNSPool:
    """创建优化的DNS服务器池"""
    return SmartDNSPool(
        dns_servers=dns_servers,
        min_servers=10,
        max_servers=20,
        failure_threshold=4,
        timeout_seconds=30.0
    )


def run_dns_pool_demo():
    """演示DNS服务器池优化效果"""
    print("=" * 60)
    print("DNS智能服务器池演示")
    print("=" * 60)

    test_servers = [
        "8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222",
        "114.114.114.114", "119.29.29.29", "223.5.5.5", "180.76.76.76"
    ]

    pool = create_optimized_dns_pool(test_servers)

    print(f"\n初始服务器池: {len(test_servers)} 个服务器")

    for i in range(20):
        servers = pool.select_servers(8)
        if i < 5 or i == 9 or i == 14 or i == 19:
            print(f"\n第 {i+1} 次选择，选择的服务器:")
            for s in servers[:5]:
                print(f"  {s}: 评分 {pool._servers[s].score:.1f}")

    print("\n" + "-" * 60)
    stats = pool.get_pool_stats()
    print(f"池状态:")
    print(f"  总服务器: {stats['total_servers']}")
    print(f"  正常: {stats['closed_circuits']}")
    print(f"  断开: {stats['open_circuits']}")
    print(f"  半开: {stats['half_open_circuits']}")
    print(f"  平均评分: {stats['avg_score']}")
    print(f"  平均响应时间: {stats['avg_response_time_ms']}ms")

    print("\n" + "-" * 60)
    print("熔断器演示:")

    breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=2)

    for i in range(10):
        allowed = breaker.allow_request()
        print(f"  请求 {i+1}: {'允许' if allowed else '拒绝'}")
        if allowed and i % 3 == 2:
            breaker.record_failure()

    print("\n" + "=" * 60)
    print("演示完成!")


if __name__ == "__main__":
    run_dns_pool_demo()
