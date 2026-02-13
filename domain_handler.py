#!/usr/bin/env python3
"""
域名处理模块 - 负责域名输入、验证和处理逻辑
"""

from typing import List, Tuple, Optional
from terminal_utils import TerminalUtils, Color
from domain_utils import DomainInputHandler


class DomainHandler:
    """域名处理器 - 统一管理域名相关的所有操作"""
    
    def __init__(self) -> None:
        """初始化域名处理器"""
        pass
    
    def get_domains_from_user(self) -> Tuple[List[str], List[str], List[str]]:
        """从用户输入获取域名列表
        
        Returns:
            tuple: (有效域名列表, 无效域名列表, 警告域名列表)
        """
        print(TerminalUtils.colored("\n=== 域名输入并测试 ===", Color.CYAN, Color.BOLD))
        print("1. 单个域名输入")
        print("2. 批量输入（逗号分隔或隔行）")
        
        input_choice = input("请选择输入方式 (1-2): ")
        
        domains = []
        invalid_domains = []
        warning_domains = []
        
        if input_choice == "1":
            """处理单个域名输入"""
            domain = DomainInputHandler.get_single_domain()
            domains = [domain] if domain else []
        elif input_choice == "2":
            """处理批量域名输入"""
            domains, invalid_domains, warning_domains = DomainInputHandler.get_batch_domains_from_input()
            DomainInputHandler.display_validation_results(domains, invalid_domains, warning_domains)
        else:
            print(TerminalUtils.colored("无效选项，请重新输入！", Color.RED))
            TerminalUtils.pause()
            return [], [], []
        
        # 去重处理
        domains = self._deduplicate_domains(domains)
        
        return domains, invalid_domains, warning_domains
    
    def _deduplicate_domains(self, domains: List[str]) -> List[str]:
        """对域名列表进行去重处理
        
        Args:
            domains: 原始域名列表
            
        Returns:
            List[str]: 去重后的域名列表
        """
        original_count = len(domains)
        deduplicated_domains = list(set(domains))
        deduplicated_count = len(deduplicated_domains)
        
        if original_count > deduplicated_count:
            print(
                TerminalUtils.colored(
                    f"\n去重处理：从 {original_count} 个域名去重到 {deduplicated_count} 个唯一域名", 
                    Color.YELLOW
                )
            )
        
        return deduplicated_domains
    
    def confirm_test_execution(self, domains: List[str]) -> bool:
        """询问用户是否执行测试
        
        Args:
            domains: 域名列表
            
        Returns:
            bool: 用户是否确认执行测试
        """
        if not domains:
            return False
            
        test_choice = input(f"\n发现 {len(domains)} 个有效域名，是否执行DNS解析和网络测试？ (y/n): ")
        return test_choice.lower() == "y"
    
    def get_resolution_mode(self, domains: List[str]) -> str:
        """获取用户选择的解析模式
        
        Args:
            domains: 域名列表
            
        Returns:
            str: 解析模式 ("comprehensive" 或 "sequential")
        """
        # 如果只有一个域名，默认使用综合解析
        if len(domains) == 1:
            return "comprehensive"
        
        print("\n选择解析方式:")
        print("1. 综合解析（将所有域名同时解析出IP，并测试所有解析出的IP的延迟和速度）")
        print("2. 依次解析（一个个解析，当前的设置）")
        
        resolve_choice = input("请输入选项 (1-2): ")
        
        return "comprehensive" if resolve_choice == "1" else "sequential"
    
    def get_test_types(self) -> List[str]:
        """获取用户选择的测试类型
        
        Returns:
            List[str]: 测试类型列表
        """
        print("\n选择测试类型:")
        print("1. 仅ping测试")
        print("2. ping + 速率测试")
        
        test_type_choice = input("请输入选项 (1-2): ")
        
        test_types = ["ping"]
        if test_type_choice == "2":
            test_types.append("speed")
            
        return test_types
    
    def get_sort_preference(self) -> str:
        """获取用户选择的排序方式
        
        Returns:
            str: 排序方式 ("latency", "speed", "balance")
        """
        print("\n选择排序方式:")
        print("1. 延迟优先")
        print("2. 速率优先")
        print("3. 平衡模式")
        
        sort_choice = input("请输入选项 (1-3): ")
        
        sort_map = {
            "1": "latency",
            "2": "speed", 
            "3": "balance"
        }
        
        return sort_map.get(sort_choice, "latency")
    
    def confirm_best_ip_view(self) -> bool:
        """询问用户是否查看最优IP
        
        Returns:
            bool: 用户是否确认查看最优IP
        """
        best_choice = input("\n是否查看最优IP列表？ (y/n): ")
        return best_choice.lower() == "y"
    
    def confirm_unique_ip_mode(self) -> bool:
        """询问用户是否使用唯一IP模式
        
        Returns:
            bool: 用户是否选择唯一IP模式
        """
        unique_ip_choice = input("\n是否使用唯一IP模式？(y/n): ")
        return unique_ip_choice.lower() == "y"