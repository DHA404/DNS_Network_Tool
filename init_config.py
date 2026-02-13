#!/usr/bin/env python3
# 初始化配置模块 - 自动检测系统性能并优化配置

import socket
import threading
import concurrent.futures
import time
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 导入项目模块
from terminal_utils import TerminalUtils, Color
from config_utils import ConfigManager
from network_utils import PingTest


class SystemPerformanceTester:
    """系统性能测试类
    
    测试系统支持的最高并发连接数、最大线程数、DNS解析线程数
    支持用户中断
    """
    
    def __init__(self):
        self.test_targets = [10, 50, 100, 200, 300, 500, 750, 1000]
        self.dns_test_targets = [10, 50, 100, 200, 300, 500]
        self.test_timeout = 5  # 测试超时时间
        self._cancelled = False  # 中断标志
        
    def cancel(self):
        """设置中断标志"""
        self._cancelled = True
    
    def reset_cancel(self):
        """重置中断标志"""
        self._cancelled = False
    
    def _check_cancelled(self) -> bool:
        """检查是否被中断"""
        return self._cancelled
    
    def test_concurrent_connections(self, target: int) -> Tuple[bool, float]:
        """测试并发连接数
        
        Args:
            target: 目标并发连接数
            
        Returns:
            (是否成功, 成功率)
        """
        if self._cancelled:
            return False, 0.0
            
        success_count = 0
        test_host = "1.1.1.1"  # Cloudflare DNS
        test_port = 53
        
        def try_connect():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((test_host, test_port))
                sock.close()
                return result == 0
            except Exception:
                return False
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=target) as executor:
                futures = [executor.submit(try_connect) for _ in range(target)]
                results = [f.result(timeout=5) for f in futures]
                success_count = sum(results)
                success_rate = success_count / target
                return success_rate >= 0.8, success_rate
        except Exception as e:
            return False, 0.0
    
    def test_max_threads(self, target: int) -> Tuple[bool, float]:
        """测试最大线程数
        
        Args:
            target: 目标线程数
            
        Returns:
            (是否成功, 执行效率)
        """
        if self._cancelled:
            return False, 0.0
            
        def simple_task():
            # 简单的CPU计算任务
            result = 0
            for i in range(10000):
                result += i
            return result
        
        try:
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=target) as executor:
                futures = [executor.submit(simple_task) for _ in range(target)]
                results = [f.result(timeout=10) for f in futures]
            end_time = time.time()
            
            execution_time = end_time - start_time
            # 如果所有任务都在合理时间内完成，则认为成功
            efficiency = len(results) / target
            return efficiency >= 0.9, efficiency
        except Exception as e:
            return False, 0.0
    
    def test_dns_threads(self, target: int) -> Tuple[bool, float]:
        """测试DNS解析线程数
        
        Args:
            target: 目标线程数
            
        Returns:
            (是否成功, 解析成功率)
        """
        if self._cancelled:
            return False, 0.0
            
        test_domains = ["google.com", "github.com", "cloudflare.com", "baidu.com"]
        
        def resolve_domain(domain):
            try:
                socket.gethostbyname(domain)
                return True
            except Exception:
                return False
        
        try:
            # 创建更多任务来测试并发能力
            domains_to_test = (test_domains * ((target // len(test_domains)) + 1))[:target]
            
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=target) as executor:
                futures = [executor.submit(resolve_domain, domain) for domain in domains_to_test]
                results = [f.result(timeout=5) for f in futures]
            end_time = time.time()
            
            success_rate = sum(results) / len(results)
            # 成功率大于70%且执行时间在合理范围内
            return success_rate >= 0.7, success_rate
        except Exception as e:
            return False, 0.0
    
    def find_max_concurrent_connections(self, test_range: List[int]) -> int:
        """使用二分查找找到最大并发连接数
        
        Args:
            test_range: 测试范围列表（已排序）
            
        Returns:
            最大成功连接数
        """
        if not test_range:
            return 10
            
        left, right = 0, len(test_range) - 1
        result = 10
        
        while left <= right:
            mid = (left + right) // 2
            target = test_range[mid]
            
            print(f"  测试并发连接数: {target}...", end=" ")
            success, rate = self.test_concurrent_connections(target)
            
            if success:
                result = target
                left = mid + 1
                print(TerminalUtils.colored(f"通过 (成功率: {rate:.1%})", Color.GREEN))
            else:
                right = mid - 1
                print(TerminalUtils.colored(f"失败 (成功率: {rate:.1%})", Color.RED))
            
            if self._cancelled:
                break
        
        return result
    
    def find_max_threads(self, test_range: List[int]) -> int:
        """使用二分查找找到最大线程数
        
        Args:
            test_range: 测试范围列表（已排序）
            
        Returns:
            最大成功线程数
        """
        if not test_range:
            return 10
            
        left, right = 0, len(test_range) - 1
        result = 10
        
        while left <= right:
            mid = (left + right) // 2
            target = test_range[mid]
            
            print(f"  测试线程数: {target}...", end=" ")
            success, rate = self.test_max_threads(target)
            
            if success:
                result = target
                left = mid + 1
                print(TerminalUtils.colored(f"通过 (效率: {rate:.1%})", Color.GREEN))
            else:
                right = mid - 1
                print(TerminalUtils.colored(f"失败 (效率: {rate:.1%})", Color.RED))
            
            if self._cancelled:
                break
        
        return result
    
    def find_max_dns_threads(self, test_range: List[int]) -> int:
        """使用二分查找找到最大DNS线程数
        
        Args:
            test_range: 测试范围列表（已排序）
            
        Returns:
            最大成功DNS线程数
        """
        if not test_range:
            return 10
            
        left, right = 0, len(test_range) - 1
        result = 10
        
        while left <= right:
            mid = (left + right) // 2
            target = test_range[mid]
            
            print(f"  测试DNS线程数: {target}...", end=" ")
            success, rate = self.test_dns_threads(target)
            
            if success:
                result = target
                left = mid + 1
                print(TerminalUtils.colored(f"通过 (成功率: {rate:.1%})", Color.GREEN))
            else:
                right = mid - 1
                print(TerminalUtils.colored(f"失败 (成功率: {rate:.1%})", Color.RED))
            
            if self._cancelled:
                break
        
        return result
    
    def run_performance_tests_binary(self) -> Dict[str, int]:
        """使用二分查找运行性能测试（更快）
        
        Returns:
            包含三个指标的字典
        """
        print(TerminalUtils.colored("\n=== 开始系统性能测试 (二分查找模式) ===", Color.CYAN, Color.BOLD))
        print("提示: 按 Ctrl+C 可随时中断测试\n")
        
        self.reset_cancel()
        
        # 测试并发连接数
        print("\n[1/3] 测试并发连接数...")
        try:
            max_connections = self.find_max_concurrent_connections(self.test_targets)
        except KeyboardInterrupt:
            print(TerminalUtils.colored("\n测试被用户中断", Color.YELLOW))
            self._cancelled = True
            max_connections = 10
        
        if self._cancelled:
            return {"concurrent_connections": 10, "max_threads": 10, "dns_threads": 10}
        
        # 测试最大线程数
        print("\n[2/3] 测试最大线程数...")
        try:
            max_threads = self.find_max_threads(self.test_targets)
        except KeyboardInterrupt:
            print(TerminalUtils.colored("\n测试被用户中断", Color.YELLOW))
            self._cancelled = True
            max_threads = 10
        
        if self._cancelled:
            return {"concurrent_connections": max_connections, "max_threads": 10, "dns_threads": 10}
        
        # 测试DNS解析线程数
        print("\n[3/3] 测试DNS解析线程数...")
        try:
            max_dns_threads = self.find_max_dns_threads(self.dns_test_targets)
        except KeyboardInterrupt:
            print(TerminalUtils.colored("\n测试被用户中断", Color.YELLOW))
            self._cancelled = True
            max_dns_threads = 10
        
        # 计算最终值（乘以2/3，向下取整）
        final_connections = int(max_connections * 2 / 3)
        final_threads = int(max_threads * 2 / 3)
        final_dns_threads = int(max_dns_threads * 2 / 3)
        
        # 确保最小值
        final_connections = max(10, final_connections)
        final_threads = max(10, final_threads)
        final_dns_threads = max(10, final_dns_threads)
        
        print(TerminalUtils.colored("\n=== 性能测试结果 ===", Color.GREEN, Color.BOLD))
        print(f"最大并发连接数: {max_connections} → 优化后: {final_connections}")
        print(f"最大线程数: {max_threads} → 优化后: {final_threads}")
        print(f"DNS解析线程数: {max_dns_threads} → 优化后: {final_dns_threads}")
        
        return {
            "concurrent_connections": final_connections,
            "max_threads": final_threads,
            "dns_threads": final_dns_threads
        }
    
    def run_performance_tests(self) -> Dict[str, int]:
        """运行所有性能测试
        
        Returns:
            包含三个指标的字典
        """
        # 使用二分查找模式（更快）
        return self.run_performance_tests_binary()


class DNSServerTester:
    """DNS服务器测试类
    
    依次测试每个DNS服务器，删除不合格的
    支持并行测试和用户中断
    """
    
    def __init__(self):
        self.connection_timeout = 2  # 连接超时时间
        self.ping_count = 3  # ping测试次数
        self.ping_timeout = 2  # ping超时时间
        self._cancelled = False  # 中断标志
        
    def cancel(self):
        """设置中断标志"""
        self._cancelled = True
    
    def reset_cancel(self):
        """重置中断标志"""
        self._cancelled = False
        
    def test_connection(self, server: str, port: int = 53) -> bool:
        """测试DNS服务器连接
        
        Args:
            server: DNS服务器IP地址
            port: 端口号，默认53
            
        Returns:
            是否连接成功
        """
        if self._cancelled:
            return False
            
        try:
            # 判断是IPv4还是IPv6
            if ":" in server:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            sock.settimeout(self.connection_timeout)
            result = sock.connect_ex((server, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def test_ping(self, server: str) -> Tuple[bool, int]:
        """测试DNS服务器ping
        
        Args:
            server: DNS服务器IP地址
            
        Returns:
            (是否至少1次成功, 成功次数)
        """
        if self._cancelled:
            return False, 0
            
        ping_tester = PingTest(count=self.ping_count, timeout=self.ping_timeout)
        result = ping_tester.ping(server)
        
        success_count = 0
        if result.get("success"):
            # 检查是否有成功的ping
            delays = result.get("delays", [])
            success_count = len([d for d in delays if d > 0])
        
        return success_count > 0, success_count
    
    def test_dns_server(self, server: str) -> bool:
        """测试单个DNS服务器
        
        Args:
            server: DNS服务器IP地址
            
        Returns:
            是否通过测试
        """
        if self._cancelled:
            return False
        
        # 第一步：连接测试
        if not self.test_connection(server):
            return False
        
        # 第二步：ping测试
        ping_success, _ = self.test_ping(server)
        return ping_success
    
    def filter_dns_servers(self, servers: List[str]) -> List[str]:
        """筛选DNS服务器
        
        Args:
            servers: DNS服务器列表
            
        Returns:
            通过测试的服务器列表
        """
        print(TerminalUtils.colored("\n=== 开始DNS服务器测试 ===", Color.CYAN, Color.BOLD))
        print(f"待测试服务器数量: {len(servers)}")
        print("测试标准: 2秒内连接成功，且ping测试3次至少1次成功")
        print("提示: 按 Ctrl+C 可随时中断测试\n")
        
        self.reset_cancel()
        valid_servers = []
        removed_count = 0
        
        try:
            for i, server in enumerate(servers, 1):
                if self._cancelled:
                    print(TerminalUtils.colored("\n测试已中断", Color.YELLOW))
                    break
                    
                print(f"[{i}/{len(servers)}] 测试 {server}...", end=" ")
                
                if self.test_dns_server(server):
                    valid_servers.append(server)
                    print(TerminalUtils.colored("通过", Color.GREEN))
                else:
                    removed_count += 1
                    print(TerminalUtils.colored("移除", Color.RED))
        except KeyboardInterrupt:
            print(TerminalUtils.colored("\n\n测试被用户中断", Color.YELLOW))
            self._cancelled = True
        
        print(TerminalUtils.colored(f"\n=== DNS服务器测试结果 ===", Color.GREEN, Color.BOLD))
        print(f"原始服务器数量: {len(servers)}")
        print(f"通过测试数量: {len(valid_servers)}")
        print(f"移除服务器数量: {removed_count}")
        
        return valid_servers
    
    def filter_dns_servers_parallel(self, servers: List[str], max_workers: int = 10) -> List[str]:
        """并行筛选DNS服务器
        
        Args:
            servers: DNS服务器列表
            max_workers: 最大并行测试数
            
        Returns:
            通过测试的服务器列表
        """
        print(TerminalUtils.colored("\n=== 开始DNS服务器测试 (并行模式) ===", Color.CYAN, Color.BOLD))
        print(f"待测试服务器数量: {len(servers)}")
        print(f"并行测试数: {max_workers}")
        print("测试标准: 2秒内连接成功，且ping测试3次至少1次成功")
        print("提示: 按 Ctrl+C 可随时中断测试\n")
        
        self.reset_cancel()
        results = {}
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_server = {
                    executor.submit(self.test_dns_server, server): server 
                    for server in servers
                }
                
                completed = 0
                total = len(servers)
                for future in concurrent.futures.as_completed(future_to_server):
                    if self._cancelled:
                        for f in future_to_server:
                            f.cancel()
                        break
                    
                    server = future_to_server[future]
                    completed += 1
                    
                    try:
                        success = future.result()
                        results[server] = success
                        status = "通过" if success else "移除"
                        color = Color.GREEN if success else Color.RED
                        print(f"[{completed}/{total}] {server}: {TerminalUtils.colored(status, color)}")
                    except Exception as e:
                        results[server] = False
                        print(f"[{completed}/{total}] {server}: {TerminalUtils.colored('错误', Color.RED)}")
        except KeyboardInterrupt:
            print(TerminalUtils.colored("\n\n测试被用户中断", Color.YELLOW))
            self._cancelled = True
        
        valid_servers = [server for server, success in results.items() if success]
        removed_count = len(results) - len(valid_servers)
        
        print(TerminalUtils.colored(f"\n=== DNS服务器测试结果 ===", Color.GREEN, Color.BOLD))
        print(f"原始服务器数量: {len(servers)}")
        print(f"通过测试数量: {len(valid_servers)}")
        print(f"移除服务器数量: {removed_count}")
        
        return valid_servers


class InitConfigManager:
    """初始化配置管理类"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.performance_tester = SystemPerformanceTester()
        self.dns_tester = DNSServerTester()
        
    def run_init_config(self, force: bool = False) -> bool:
        """运行初始化配置
        
        Args:
            force: 是否强制重新初始化
            
        Returns:
            是否成功
        """
        print(TerminalUtils.colored("\n" + "=" * 60, Color.BLUE, Color.BOLD))
        print(TerminalUtils.colored("         初始化配置向导", Color.GREEN, Color.BOLD))
        print(TerminalUtils.colored("=" * 60, Color.BLUE, Color.BOLD))
        
        if not force:
            print("\n本向导将帮助您：")
            print("1. 自动检测系统性能，优化并发连接数、线程数等参数")
            print("2. 测试所有DNS服务器，移除不可用或响应慢的服务器")
            print("\n注意：此过程可能需要几分钟时间，请耐心等待。")
            
            choice = input("\n是否开始初始化配置? (y/n): ").lower()
            if choice != 'y':
                print("已取消初始化配置")
                return False
        
        try:
            # 第一步：系统性能测试
            print(TerminalUtils.colored("\n>>> 第一步：系统性能测试", Color.YELLOW, Color.BOLD))
            performance_results = self.performance_tester.run_performance_tests()
            
            # 更新配置
            print("\n正在更新性能参数...")
            for param, value in performance_results.items():
                success, message = self.config_manager.update_test_param(param, value)
                if not success:
                    print(TerminalUtils.colored(f"更新 {param} 失败: {message}", Color.RED))
            
            # 第二步：DNS服务器测试
            print(TerminalUtils.colored("\n>>> 第二步：DNS服务器测试", Color.YELLOW, Color.BOLD))
            current_servers = self.config_manager.get_dns_servers()
            
            # 根据服务器数量选择测试方式
            if len(current_servers) > 20:
                # 服务器数量多时使用并行测试
                print(f"检测到 {len(current_servers)} 个DNS服务器，将使用并行测试模式...")
                valid_servers = self.dns_tester.filter_dns_servers_parallel(
                    current_servers, max_workers=20
                )
            else:
                valid_servers = self.dns_tester.filter_dns_servers(current_servers)
            
            # 更新DNS服务器列表
            if len(valid_servers) != len(current_servers):
                print("\n正在更新DNS服务器列表...")
                success, message = self.config_manager.set_dns_servers(valid_servers)
                if success:
                    print(TerminalUtils.colored("DNS服务器列表已更新", Color.GREEN))
                else:
                    print(TerminalUtils.colored(f"更新DNS服务器列表失败: {message}", Color.RED))
            
            # 标记已完成初始化
            self._mark_initialized()
            
            print(TerminalUtils.colored("\n" + "=" * 60, Color.GREEN, Color.BOLD))
            print(TerminalUtils.colored("         初始化配置完成！", Color.GREEN, Color.BOLD))
            print(TerminalUtils.colored("=" * 60, Color.GREEN, Color.BOLD))
            print("\n优化后的配置已保存到 config.json")
            print('您可以在"配置测试参数"中查看和调整这些参数。')
            
            return True
            
        except Exception as e:
            print(TerminalUtils.colored(f"\n初始化配置失败: {str(e)}", Color.RED))
            return False
    
    def _mark_initialized(self):
        """标记已完成初始化"""
        try:
            config = self.config_manager.get_config()
            config["initialized"] = True
            config["init_time"] = datetime.now().isoformat()
            self.config_manager.update_config(config)
        except Exception:
            pass
    
    def is_initialized(self) -> bool:
        """检查是否已完成初始化或已跳过初始化"""
        try:
            config = self.config_manager.get_config()
            # 已完成初始化或已跳过初始化都不再提示
            return config.get("initialized", False) or config.get("init_skipped", False)
        except Exception:
            return False
    
    def mark_init_skipped(self):
        """标记用户已跳过初始化"""
        try:
            config = self.config_manager.get_config()
            config["init_skipped"] = True
            config["init_skip_time"] = datetime.now().isoformat()
            self.config_manager.update_config(config)
        except Exception:
            pass
    
    def show_init_menu(self):
        """显示初始化菜单"""
        while True:
            print(TerminalUtils.colored("\n=== 初始化配置 ===", Color.CYAN, Color.BOLD))
            print("1. 运行初始化配置向导")
            print("2. 重新运行初始化配置（强制）")
            print("3. 返回主菜单")
            
            choice = input("\n请输入选项 (1-3): ")
            
            if choice == "1":
                if self.is_initialized():
                    print(TerminalUtils.colored("\n系统已完成初始化。如需重新配置，请选择选项2。", Color.YELLOW))
                    continue
                self.run_init_config(force=False)
                input("\n按回车键继续...")
                
            elif choice == "2":
                confirm = input("\n确定要重新运行初始化配置吗？这将覆盖现有配置。(y/n): ").lower()
                if confirm == 'y':
                    self.run_init_config(force=True)
                input("\n按回车键继续...")
                
            elif choice == "3":
                break
            else:
                print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))
    
    def reset_init_record(self) -> bool:
        """重置初始化记录
        
        清除 initialized、init_skipped 等字段，使程序下次启动时重新提示初始化
        
        Returns:
            是否成功重置
        """
        try:
            # 直接访问config_manager的config属性
            config = self.config_manager.config
            
            # 检查是否存在初始化记录（包括已完成或已跳过）
            has_record = config.get("initialized", False) or config.get("init_skipped", False)
            if not has_record:
                print(TerminalUtils.colored("\n当前没有初始化记录，无需重置。", Color.YELLOW))
                return False
            
            # 确认操作
            confirm = input("\n确定要重置初始化记录吗？下次启动时将重新提示初始化。(y/n): ").lower()
            if confirm != 'y':
                print("已取消重置操作")
                return False
            
            # 删除所有初始化相关标记
            removed = False
            for key in ["initialized", "init_time", "init_skipped", "init_skip_time"]:
                if key in config:
                    del config[key]
                    removed = True
            
            # 直接保存配置
            if removed:
                self.config_manager.save_config()
            
            print(TerminalUtils.colored("\n初始化记录已重置！", Color.GREEN))
            print("下次启动程序时将重新提示初始化配置向导。")
            return True
            
        except Exception as e:
            print(TerminalUtils.colored(f"\n重置初始化记录失败: {str(e)}", Color.RED))
            return False


def check_and_prompt_init(config_manager: ConfigManager) -> bool:
    """检查并提示初始化
    
    在程序启动时调用，检查是否需要初始化
    
    Args:
        config_manager: 配置管理器实例
        
    Returns:
        是否继续运行程序
    """
    init_manager = InitConfigManager(config_manager)
    
    if init_manager.is_initialized():
        return True
    
    print(TerminalUtils.colored("\n" + "=" * 60, Color.YELLOW, Color.BOLD))
    print(TerminalUtils.colored("         欢迎使用 DNS Network Tool", Color.GREEN, Color.BOLD))
    print(TerminalUtils.colored("=" * 60, Color.YELLOW, Color.BOLD))
    
    print("\n检测到这是首次运行，建议运行初始化配置向导：")
    print("• 自动检测系统性能并优化参数")
    print("• 测试并筛选可用的DNS服务器")
    print("• 获得最佳的使用体验")
    
    print("\n选项：")
    print("1. 运行初始化配置向导（推荐）")
    print("2. 跳过初始化，使用默认配置")
    print("3. 退出程序")
    
    choice = input("\n请输入选项 (1-3): ")
    
    if choice == "1":
        success = init_manager.run_init_config(force=False)
        input("\n按回车键继续...")
        return success
    elif choice == "2":
        print("\n已跳过初始化，使用默认配置。")
        print('您可以随时在"配置管理"菜单中运行初始化向导。')
        # 标记已跳过初始化，下次不再提示
        init_manager.mark_init_skipped()
        input("\n按回车键继续...")
        return True
    elif choice == "3":
        print("\n程序已退出")
        return False
    else:
        print(TerminalUtils.colored("无效选项，使用默认配置", Color.YELLOW))
        input("\n按回车键继续...")
        return True


if __name__ == "__main__":
    # 测试代码
    config_manager = ConfigManager()
    init_manager = InitConfigManager(config_manager)
    init_manager.show_init_menu()
