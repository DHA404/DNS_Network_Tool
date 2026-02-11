#!/usr/bin/env python3
# DNS解析工具模块 - 优化版本

import os
import socket
import concurrent.futures
import threading
import time
import requests
import psutil
from typing import Optional, Dict, List, Any
from terminal_utils import TerminalUtils, Color


class DNSResolver:
    """DNS解析类 - 性能优化版本
    
    支持多线程并行解析、自适应超时、熔断机制和智能重试策略。
    
    Attributes:
        dns_servers: DNS服务器列表
        base_timeout: 基础超时时间
        dns_threads: DNS解析线程数
        timeout_tiers: 超时等级配置
        server_performance: 服务器性能历史记录
        stats: 解析统计信息
    """
    
    def __init__(self, dns_servers=None, timeout=2, dns_threads=30):
        """初始化DNS解析器
        
        Args:
            dns_servers: DNS服务器IP地址列表，默认为常用公共DNS服务器
            timeout: 基础超时时间（秒），默认2秒
            dns_threads: 最大并发线程数，默认30
        """
        self.dns_servers = dns_servers or [
            "8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222", "4.2.2.1",
        ]
        self.base_timeout = timeout

        cpu_count = os.cpu_count() or 4
        try:
            process = psutil.Process()
            system_load = psutil.cpu_percent(interval=0.1) / 100.0
        except Exception:
            system_load = 0.5

        load_factor = 1.0 - system_load * 0.5
        adjusted_threads = min(dns_threads, cpu_count * 2, len(self.dns_servers))
        self.dns_threads = max(1, int(adjusted_threads * load_factor))

        self.timeout_tiers = {
            'very_fast': 0.8,
            'fast': 1.2,
            'normal': 2.0,
            'slow': 3.5,
            'very_slow': 5.0,
        }

        self.server_performance = {}
        self.performance_history_size = 20

        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_response_time_ms': 0,
            'fast_fail_count': 0,
        }
        self.stats_lock = threading.Lock()

        self._first_query_completed = False
        self._first_query_avg_time = None

        self._retry_lock = threading.Lock()
        self._failed_servers = {}  # 记录失败次数用于熔断

    def _get_timeout_for_server(self, dns_server: str) -> float:
        """根据服务器历史性能获取分级超时时间
        
        Args:
            dns_server: DNS服务器IP地址
            
        Returns:
            float: 超时时间（秒）
            
        Notes:
            - very_fast: < 300ms, 超时 0.8s
            - fast: < 600ms, 超时 1.2s
            - normal: < 1200ms, 超时 2.0s
            - slow: < 2500ms, 超时 3.5s
            - very_slow: >= 2500ms, 超时 5.0s
        """
        if dns_server in self.server_performance:
            history = self.server_performance[dns_server]
            if len(history) >= 3:
                weights = [1.0, 1.5, 2.0, 2.5, 3.0][:len(history)]
                total_weight = sum(weights)
                weighted_avg = sum(h * w for h, w in zip(history, weights)) / total_weight
                
                if weighted_avg < 300:
                    return self.timeout_tiers['very_fast']
                elif weighted_avg < 600:
                    return self.timeout_tiers['fast']
                elif weighted_avg < 1200:
                    return self.timeout_tiers['normal']
                elif weighted_avg < 2500:
                    return self.timeout_tiers['slow']
                else:
                    return self.timeout_tiers['very_slow']
        
        if self._first_query_completed and self._first_query_avg_time is not None:
            if self._first_query_avg_time < 300:
                return self.timeout_tiers['fast']
            elif self._first_query_avg_time < 800:
                return self.timeout_tiers['normal']
            else:
                return self.timeout_tiers['slow']
        
        return self.timeout_tiers['normal']
    
    def _update_server_performance(self, dns_server: str, response_time_ms: float):
        """更新DNS服务器性能统计
        
        Args:
            dns_server: DNS服务器IP地址
            response_time_ms: 响应时间（毫秒）
            
        Notes:
            - 保持历史记录在指定大小内（默认20条）
            - 自动更新首次查询统计信息
        """
        if dns_server not in self.server_performance:
            self.server_performance[dns_server] = []
        
        self.server_performance[dns_server].append(response_time_ms)
        
        if len(self.server_performance[dns_server]) > self.performance_history_size:
            self.server_performance[dns_server].pop(0)
        
        if not self._first_query_completed:
            self._first_query_avg_time = response_time_ms
            self._first_query_completed = True
    
    def _get_server_speed_tier(self, dns_server: str) -> str:
        """获取DNS服务器速度等级
        
        Args:
            dns_server: DNS服务器IP地址
            
        Returns:
            str: 速度等级，可能的值为 'very_fast', 'fast', 'normal', 'slow', 'very_slow', 'unknown'
        """
        if dns_server not in self.server_performance:
            return 'unknown'
        
        history = self.server_performance[dns_server]
        if len(history) >= 3:
            weights = [1.0, 1.5, 2.0, 2.5, 3.0][:len(history)]
            total_weight = sum(weights)
            weighted_avg = sum(h * w for h, w in zip(history, weights)) / total_weight
            
            if weighted_avg < 300:
                return 'very_fast'
            elif weighted_avg < 600:
                return 'fast'
            elif weighted_avg < 1200:
                return 'normal'
            elif weighted_avg < 2500:
                return 'slow'
            else:
                return 'very_slow'
        
        avg_time = sum(history) / len(history)
        if avg_time < 500:
            return 'fast'
        elif avg_time < 1500:
            return 'normal'
        else:
            return 'slow'
    
    def _is_server_blocked(self, dns_server: str) -> bool:
        """检查服务器是否因连续失败被暂时阻断（熔断机制）
        
        Args:
            dns_server: DNS服务器IP地址
            
        Returns:
            bool: 如果服务器被阻断返回True，否则返回False
            
        Notes:
            - 连续失败3次后触发熔断
            - 熔断持续时间为30秒
        """
        with self._retry_lock:
            if dns_server in self._failed_servers:
                fail_info = self._failed_servers[dns_server]
                if fail_info['count'] >= 3:
                    time_since_first = time.time() - fail_info['first_failure']
                    if time_since_first < 30:
                        return True
                    else:
                        del self._failed_servers[dns_server]
            return False

    def _record_failure(self, dns_server: str):
        """记录DNS服务器解析失败
        
        Args:
            dns_server: DNS服务器IP地址
        """
        with self._retry_lock:
            if dns_server not in self._failed_servers:
                self._failed_servers[dns_server] = {'count': 0, 'first_failure': time.time()}
            self._failed_servers[dns_server]['count'] += 1
            self._failed_servers[dns_server]['first_failure'] = time.time()

    def _record_success(self, dns_server: str):
        """记录DNS服务器解析成功
        
        Args:
            dns_server: DNS服务器IP地址
        """
        with self._retry_lock:
            if dns_server in self._failed_servers:
                self._failed_servers[dns_server]['count'] = max(0, self._failed_servers[dns_server]['count'] - 1)

    def _resolve_with_retry(self, domain: str, dns_server: str, timeout: float) -> Dict[str, Any]:
        """带重试的DNS解析（指数退避）
        
        使用指数退避策略进行重试，最多重试2次。
        
        Args:
            domain: 要解析的域名
            dns_server: DNS服务器IP地址
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 解析结果字典，包含以下键：
                - dns_server: 使用的DNS服务器
                - ips: 解析到的IP地址列表
                - success: 是否成功
                - elapsed: 响应时间（毫秒）
                - error: 错误信息（如果失败）
                - speed_tier: 服务器速度等级
                
        Raises:
            Exception: 所有重试失败后抛出最后一个异常
        """
        max_retries = 2
        last_error = None

        for attempt in range(max_retries):
            try:
                return self._do_resolve(domain, dns_server, timeout)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = 0.2 * (2 ** attempt)
                    time.sleep(delay)
        raise last_error

    def _do_resolve(self, domain: str, dns_server: str, timeout: float) -> Dict[str, Any]:
        """执行实际的DNS解析
        
        使用dnspython库进行DNS解析，如果不可用则回退到socket方法。
        
        Args:
            domain: 要解析的域名
            dns_server: DNS服务器IP地址
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 解析结果字典，包含以下键：
                - dns_server: 使用的DNS服务器
                - ips: 解析到的IP地址列表
                - success: 是否成功
                - elapsed: 响应时间（毫秒）
                - error: 错误信息（如果失败）
                - speed_tier: 服务器速度等级
                
        Raises:
            Exception: 解析失败时抛出异常
        """
        start_time = time.time()
        try:
            import dns.resolver

            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.timeout = timeout
            resolver.lifetime = timeout
            ips = []
            
            def resolve_record(record_type):
                """解析指定类型的DNS记录"""
                try:
                    answers = resolver.resolve(domain, record_type)
                    return [rdata.address for rdata in answers]
                except Exception:
                    return []
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_a = executor.submit(resolve_record, "A")
                future_aaaa = executor.submit(resolve_record, "AAAA")
                
                ips.extend(future_a.result())
                ips.extend(future_aaaa.result())
            
            if not ips:
                raise Exception(f"DNS解析失败: 未从服务器 {dns_server} 解析到任何IP地址")

            end_time = time.time()
            elapsed = round((end_time - start_time) * 1000, 2)

            self._update_server_performance(dns_server, elapsed)
            self._record_success(dns_server)

            with self.stats_lock:
                self.stats['total_queries'] += 1
                self.stats['successful_queries'] += 1
                self.stats['total_response_time_ms'] += elapsed

            return {
                "dns_server": dns_server,
                "ips": list(set(ips)),
                "success": True,
                "elapsed": elapsed,
                "error": None,
                "speed_tier": self._get_server_speed_tier(dns_server)
            }
        except ImportError:
            ips = []
            try:
                info = socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM)
                ips = [ip[4][0] for ip in info]
            except socket.gaierror as e:
                pass

            try:
                info = socket.getaddrinfo(domain, None, socket.AF_INET6, socket.SOCK_STREAM)
                ips.extend([ip[4][0] for ip in info])
            except socket.gaierror as e:
                pass

            end_time = time.time()
            elapsed = round((end_time - start_time) * 1000, 2)

            if ips:
                self._update_server_performance(dns_server, elapsed)
                self._record_success(dns_server)

                with self.stats_lock:
                    self.stats['total_queries'] += 1
                    self.stats['successful_queries'] += 1
                    self.stats['total_response_time_ms'] += elapsed

                return {
                    "dns_server": dns_server,
                    "ips": list(set(ips)),
                    "success": True,
                    "elapsed": elapsed,
                    "error": None,
                    "speed_tier": self._get_server_speed_tier(dns_server)
                }
            else:
                raise Exception(f"DNS解析失败: 使用socket方法也未能解析到任何IP地址")
        except Exception as e:
            raise Exception(f"DNS解析异常: {str(e)}")

    def resolve_domain(self, domain, dns_server):
        """使用指定DNS服务器解析域名（带熔断和重试）
        
        Args:
            domain: 要解析的域名
            dns_server: DNS服务器IP地址
            
        Returns:
            Dict[str, Any]: 解析结果字典，包含以下键：
                - dns_server: 使用的DNS服务器
                - ips: 解析到的IP地址列表
                - success: 是否成功
                - elapsed: 响应时间（毫秒）
                - error: 错误信息（如果失败）
                - speed_tier: 服务器速度等级
        """
        if self._is_server_blocked(dns_server):
            return {
                "dns_server": dns_server,
                "ips": [],
                "success": False,
                "elapsed": 0,
                "error": "服务器暂时不可用（熔断）",
                "speed_tier": "blocked"
            }

        timeout = self._get_timeout_for_server(dns_server)

        try:
            result = self._resolve_with_retry(domain, dns_server, timeout)
            return result
        except Exception as e:
            end_time = time.time()
            elapsed = round((end_time - time.time()) * 1000, 2)

            self._record_failure(dns_server)

            with self.stats_lock:
                self.stats['total_queries'] += 1
                self.stats['failed_queries'] += 1

            return {
                "dns_server": dns_server,
                "ips": [],
                "success": False,
                "elapsed": elapsed,
                "error": str(e),
                "speed_tier": "failed"
            }

    def resolve_domain_parallel(self, domain, fast_fail=True):
        """并行使用多个DNS服务器解析域名
        
        使用线程池并发向所有配置的DNS服务器发送解析请求，
        提高解析成功率和速度。
        
        Args:
            domain: 要解析的域名
            fast_fail: 是否快速失败模式（收到第一个成功结果后立即返回）
            
        Returns:
            List[Dict[str, Any]]: 解析结果列表，每个元素包含：
                - dns_server: 使用的DNS服务器
                - ips: 解析到的IP地址列表
                - success: 是否成功
                - elapsed: 响应时间（毫秒）
                - error: 错误信息（如果失败）
                - speed_tier: 服务器速度等级
        """
        results = []
        success_count = 0
        
        max_threads = min(self.dns_threads, len(self.dns_servers))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_dns = {
                executor.submit(self.resolve_domain, domain, dns_server): dns_server for dns_server in self.dns_servers
            }

            if fast_fail:
                for future in concurrent.futures.as_completed(future_to_dns):
                    dns_server = future_to_dns[future]
                    try:
                        result = future.result()
                        results.append(result)
                        if result["success"]:
                            success_count += 1
                    except Exception as e:
                        results.append({"dns_server": dns_server, "ips": [], "success": False, "elapsed": 0, "error": str(e)})
                    
                    if success_count >= 5:
                        break
            else:
                for future in concurrent.futures.as_completed(future_to_dns):
                    dns_server = future_to_dns[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({"dns_server": dns_server, "ips": [], "success": False, "elapsed": 0, "error": str(e)})
        return results

    def get_unique_ips(self, results):
        """从解析结果中提取唯一IP地址及其来源信息
        
        Args:
            results: DNS解析结果列表
            
        Returns:
            Dict[str, Dict]: 唯一IP地址字典，键为IP地址，值为包含以下键的字典：
                - sources: 来源DNS服务器列表
                - avg_elapsed: 平均响应时间（毫秒）
        """
        unique_ips = {}

        for result in results:
            if result["success"]:
                dns_server = result["dns_server"]
                elapsed = result["elapsed"]
                for ip in result["ips"]:
                    if ip not in unique_ips:
                        unique_ips[ip] = {"sources": [dns_server], "avg_elapsed": elapsed}
                    else:
                        unique_ips[ip]["sources"].append(dns_server)
                        current_avg = unique_ips[ip]["avg_elapsed"]
                        current_count = len(unique_ips[ip]["sources"])
                        new_avg = round((current_avg * (current_count - 1) + elapsed) / current_count, 2)
                        unique_ips[ip]["avg_elapsed"] = new_avg

        return unique_ips

    def resolve_with_system_dns(self, domain):
        """使用系统DNS解析域名（备用方法）
        
        当所有配置的DNS服务器都无法解析时，使用系统默认DNS作为备用。
        
        Args:
            domain: 要解析的域名
            
        Returns:
            Dict[str, Any]: 解析结果，包含以下键：
                - ips: 解析到的IP地址列表
                - success: 是否成功
                - elapsed: 响应时间（毫秒）
                - error: 错误信息（如果失败）
        """
        start_time = time.time()
        try:
            ips = socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM)
            ip_list = [ip[4][0] for ip in ips]
            end_time = time.time()
            elapsed = round((end_time - start_time) * 1000, 2)

            return {"ips": list(set(ip_list)), "success": True, "elapsed": elapsed, "error": None}
        except Exception as e:
            end_time = time.time()
            elapsed = round((end_time - start_time) * 1000, 2)

            return {"ips": [], "success": False, "elapsed": elapsed, "error": str(e)}





class DNSAnalysis:
    """DNS解析结果分析类"""

    @staticmethod
    def analyze_results(results):
        """分析DNS解析结果"""
        total_servers = len(results)
        successful_servers = sum(1 for r in results if r["success"])
        failed_servers = total_servers - successful_servers

        total_ips = set()
        for r in results:
            if r["success"]:
                total_ips.update(r["ips"])

        avg_response_time = 0
        if successful_servers > 0:
            avg_response_time = round(sum(r["elapsed"] for r in results if r["success"]) / successful_servers, 2)

        return {
            "total_servers": total_servers,
            "successful_servers": successful_servers,
            "failed_servers": failed_servers,
            "total_unique_ips": len(total_ips),
            "avg_response_time": avg_response_time,
            "results": results,
        }

    @staticmethod
    def detect_dns_poisoning(results):
        """检测可能的DNS污染"""
        # 简单检测：如果不同DNS服务器返回的IP地址差异很大，可能存在污染
        all_ips = []
        for r in results:
            if r["success"]:
                all_ips.append(set(r["ips"]))

        if len(all_ips) < 2:
            return False, "无法检测：DNS服务器数量不足"

        # 计算IP集合的相似度
        base_ips = all_ips[0]
        for i, ips in enumerate(all_ips[1:], 1):
            if len(ips.intersection(base_ips)) == 0:
                return True, f"可能存在DNS污染：服务器 {results[i]['dns_server']} 返回的IP与其他服务器完全不同"

        return False, "未检测到明显的DNS污染"


class DNSResolverWrapper:
    """DNS解析包装类，提供更易用的接口"""

    def __init__(self, dns_servers=None, dns_threads=10):
        self.dns_resolver = DNSResolver(dns_servers, dns_threads=dns_threads)
        self.dns_threads = dns_threads

    def resolve(self, domain, fast_fail=True):
        """完整的DNS解析流程"""
        TerminalUtils.print_status(f"开始解析域名: {domain}", "INFO")
        # 1. 使用多个DNS服务器并行解析
        results = self.dns_resolver.resolve_domain_parallel(domain, fast_fail=fast_fail)

        # 2. 分析解析结果
        analysis = DNSAnalysis.analyze_results(results)

        # 3. 检测DNS污染
        is_poisoned, poison_message = DNSAnalysis.detect_dns_poisoning(results)

        # 4. 获取唯一IP地址
        unique_ips = self.dns_resolver.get_unique_ips(results)

        # 5. 如果并行解析失败，尝试使用系统DNS
        if analysis["successful_servers"] == 0:
            TerminalUtils.print_status("所有DNS服务器解析失败，尝试使用系统DNS", "WARNING")
            system_result = self.dns_resolver.resolve_with_system_dns(domain)
            if system_result["success"]:
                for ip in system_result["ips"]:
                    unique_ips[ip] = {"sources": ["system_dns"], "avg_elapsed": system_result["elapsed"]}

        

        # 7. 生成最终结果
        final_results = {
            "domain": domain,
            "analysis": analysis,
            "is_poisoned": is_poisoned,
            "poison_message": poison_message,
            "unique_ips": unique_ips,
            "raw_results": results,
        }

        TerminalUtils.print_status(f"域名 {domain} 解析完成", "SUCCESS")

        return final_results

    def parallel_resolve(self, domains, fast_fail=True):
        """并行解析多个域名（自动去除重复域名）"""
        # 去重：确保每个唯一域名只处理一次
        unique_domains = list(set(domains))
        if len(unique_domains) != len(domains):
            print(f"检测到重复域名，已自动去重：{len(domains)} 个 → {len(unique_domains)} 个")
        domain_results = {}

        # 使用配置的DNS线程数
        max_workers = min(self.dns_threads, len(unique_domains))
        # 使用ThreadPoolExecutor并行解析多个域名
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有解析任务
            future_to_domain = {executor.submit(self.resolve, domain, fast_fail=fast_fail): domain for domain in unique_domains}
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    domain_results[domain] = result
                except Exception as e:
                    TerminalUtils.print_status(f"域名 {domain} 解析失败: {str(e)}", "ERROR")
                    domain_results[domain] = {
                        "domain": domain,
                        "analysis": {
                            "total_servers": 0,
                            "successful_servers": 0,
                            "failed_servers": 0,
                            "total_unique_ips": 0,
                            "avg_response_time": 0,
                            "results": [],
                        },
                        "is_poisoned": False,
                        "poison_message": "解析失败",
                        "unique_ips": {},
                        "raw_results": [],
                    }

        # 统一格式：为每个域名显示解析完成状态
        for domain, result in domain_results.items():
            if result["unique_ips"]:  # 成功解析
                TerminalUtils.print_status(f"域名 {domain} 解析完成", "SUCCESS")
            else:  # 解析失败
                TerminalUtils.print_status(f"域名 {domain} 解析失败", "ERROR")

        return domain_results

    def display_results(self, results):
        """显示DNS解析结果"""
        print(TerminalUtils.colored(f"\n=== DNS解析结果: {results['domain']} ===", Color.CYAN, Color.BOLD))

        # 显示分析摘要
        analysis = results["analysis"]
        print(f"DNS服务器总数: {analysis['total_servers']}")
        print(f"成功解析: {TerminalUtils.colored(analysis['successful_servers'], Color.GREEN)}")
        print(f"解析失败: {TerminalUtils.colored(analysis['failed_servers'], Color.RED)}")
        print(f"平均响应时间: {analysis['avg_response_time']} ms")
        print(f"唯一IP地址数: {analysis['total_unique_ips']}")

        # 显示DNS污染检测结果
        if results["is_poisoned"]:
            print(TerminalUtils.colored(f"DNS污染检测: {results['poison_message']}", Color.RED))
        else:
            print(TerminalUtils.colored(f"DNS污染检测: {results['poison_message']}", Color.GREEN))

        # 显示详细IP信息
        print(TerminalUtils.colored("\n=== IP地址详细信息 ===", Color.CYAN, Color.BOLD))

        if not results["unique_ips"]:
            print(TerminalUtils.colored("未解析到任何IP地址", Color.RED))
            return

        # 准备表格数据
        table_data = []
        for ip, info in results["unique_ips"].items():
            table_data.append(
                {
                    "IP": ip,
                    "平均耗时": f"{info['avg_elapsed']} ms",
                }
            )

        # 打印表格
        TerminalUtils.print_table(table_data)