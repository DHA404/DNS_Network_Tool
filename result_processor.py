#!/usr/bin/env python3
"""
结果处理模块 - 负责hosts生成和结果处理逻辑
"""

from datetime import datetime
from typing import List, Dict, Set
from terminal_utils import TerminalUtils, Color
from result_utils import ResultExporter


class ResultProcessor:
    """结果处理器 - 统一管理结果处理相关的所有操作"""
    
    def __init__(self) -> None:
        """初始化结果处理器"""
        pass
    
    def generate_hosts_content(self, domains: List[str], best_ips: List[Dict], 
                             domain_ip_map: Dict[str, Dict], unique_ip_mode: bool = False) -> str:
        """生成hosts内容
        
        Args:
            domains: 域名列表
            best_ips: 最佳IP列表
            domain_ip_map: 域名到IP映射字典
            unique_ip_mode: 是否使用唯一IP模式
            
        Returns:
            str: hosts内容
        """
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建hosts内容
        hosts_content = "# DNS Network Tool 生成的hosts条目\n"
        hosts_content += f"# 生成时间: {timestamp}\n"
        hosts_content += f"# 共 {len(domains)} 个域名\n"
        
        if unique_ip_mode:
            hosts_content += self._generate_unique_ip_hosts(domains, best_ips)
        else:
            hosts_content += self._generate_individual_ip_hosts(domains, best_ips, domain_ip_map)
        
        return hosts_content
    
    def _generate_unique_ip_hosts(self, domains: List[str], best_ips: List[Dict]) -> str:
        """生成唯一IP模式的hosts内容
        
        Args:
            domains: 域名列表
            best_ips: 最佳IP列表
            
        Returns:
            str: 唯一IP模式的hosts内容
        """
        hosts_content = "# 模式: 唯一IP模式\n\n"
        
        if not best_ips:
            print(TerminalUtils.colored("未找到最佳IP，无法使用唯一IP模式", Color.RED))
            return ""
        
        # 选择最优IP（最佳IP列表中的第一个）
        best_ip = best_ips[0]["ip"]
        print(TerminalUtils.colored(f"\n=== 选择的唯一最优IP: {best_ip} ===", Color.GREEN, Color.BOLD))
        
        # 为所有域名使用同一个最优IP
        for domain in domains:
            hosts_content += f"{best_ip} {domain}\n"
        
        return hosts_content
    
    def _generate_individual_ip_hosts(self, domains: List[str], best_ips: List[Dict], 
                                    domain_ip_map: Dict[str, Dict]) -> str:
        """生成每个域名独立IP模式的hosts内容
        
        Args:
            domains: 域名列表
            best_ips: 最佳IP列表
            domain_ip_map: 域名到IP映射字典
            
        Returns:
            str: 独立IP模式的hosts内容
        """
        hosts_content = "# 模式: 每个域名独立IP\n\n"
        
        for domain in domains:
            domain_best_ip = self._find_best_ip_for_domain(domain, best_ips, domain_ip_map)
            
            if domain_best_ip:
                hosts_content += f"{domain_best_ip} {domain}\n"
            else:
                print(
                    TerminalUtils.colored(
                        f"警告：无法为域名 {domain} 生成hosts条目，可能是解析失败或没有找到有效IP",
                        Color.YELLOW,
                    )
                )
        
        return hosts_content
    
    def _find_best_ip_for_domain(self, domain: str, best_ips: List[Dict], 
                               domain_ip_map: Dict[str, Dict]) -> str:
        """为指定域名查找最佳IP
        
        Args:
            domain: 域名
            best_ips: 最佳IP列表
            domain_ip_map: 域名到IP映射字典
            
        Returns:
            str: 最佳IP地址，如果未找到返回空字符串
        """
        # 检查域名是否在domain_ip_map中
        if domain not in domain_ip_map:
            return ""
        
        # 获取该域名的所有IP
        domain_ips = domain_ip_map[domain]["unique_ips"].keys()
        
        # 在最佳IP列表中查找该域名的IP
        for ip_info in best_ips:
            if ip_info["ip"] in domain_ips:
                return ip_info["ip"]
        
        # 如果在最佳IP列表中没有找到，使用该域名解析到的第一个IP
        if domain_ips:
            return list(domain_ips)[0]
        
        return ""
    
    def copy_to_clipboard_and_display(self, content: str, title: str = "hosts内容"):
        """复制内容到剪贴板并显示
        
        Args:
            content: 要复制的内容
            title: 显示标题
        """
        if not content:
            print(TerminalUtils.colored("没有内容可复制", Color.RED))
            return
        
        # 复制到剪贴板
        success, message = ResultExporter.copy_to_clipboard(content)
        print(f"\n{message}")
        print(TerminalUtils.colored(f"=== {title}已复制到剪贴板 ===", Color.GREEN, Color.BOLD))
        print(content)
    
    def generate_sequential_hosts_content(self, domains: List[str], domain_ip_map: Dict[str, Dict],
                                        all_best_ips: List[Dict], unique_ip_mode: bool = False) -> str:
        """生成依次解析模式的hosts内容
        
        Args:
            domains: 域名列表
            domain_ip_map: 域名到IP映射字典
            all_best_ips: 所有最佳IP列表
            unique_ip_mode: 是否使用唯一IP模式
            
        Returns:
            str: hosts内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建hosts内容
        hosts_content = "# DNS Network Tool 生成的hosts条目\n"
        hosts_content += f"# 生成时间: {timestamp}\n"
        hosts_content += f"# 共 {len(domains)} 个域名\n"
        
        if unique_ip_mode and all_best_ips:
            # 唯一IP模式
            hosts_content += "# 模式: 唯一IP模式\n\n"
            
            # 选择所有IP中的最优IP（按延迟排序）
            all_best_ips.sort(key=lambda x: x["ping"]["avg_delay"])
            best_ip = all_best_ips[0]["ip"]
            print(TerminalUtils.colored(f"\n=== 选择的唯一最优IP: {best_ip} ===", Color.GREEN, Color.BOLD))
            
            # 为所有域名使用同一个最优IP
            for domain in domains:
                hosts_content += f"{best_ip}    {domain}\n"
        else:
            # 默认模式：每个域名使用自己的最佳IP
            hosts_content += "# 模式: 每个域名独立IP\n\n"
            
            for domain in domains:
                domain_best_ip = self._find_best_ip_for_domain(domain, all_best_ips, domain_ip_map)
                if domain_best_ip:
                    hosts_content += f"{domain_best_ip} {domain}\n"
        
        return hosts_content
    
    def validate_hosts_content(self, content: str) -> bool:
        """验证hosts内容是否有效
        
        Args:
            content: hosts内容
            
        Returns:
            bool: 是否有效
        """
        if not content or not content.strip():
            return False
        
        lines = content.strip().split('\n')
        valid_lines = 0
        
        for line in lines:
            line = line.strip()
            # 跳过注释行和空行
            if line.startswith('#') or not line:
                continue
            
            # 检查是否是有效的hosts条目格式
            parts = line.split()
            if len(parts) >= 2:
                valid_lines += 1
        
        return valid_lines > 0