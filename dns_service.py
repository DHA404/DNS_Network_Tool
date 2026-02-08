#!/usr/bin/env python3
"""
DNS解析服务模块 - 负责DNS解析相关的所有操作
"""

from typing import List, Dict, Set, Tuple
from terminal_utils import TerminalUtils, Color
from dns_utils import DNSResolverWrapper


class DNSService:
    """DNS解析服务 - 统一管理DNS解析相关的所有操作"""
    
    def __init__(self, dns_servers: List[str], test_params: Dict):
        """初始化DNS解析服务
        
        Args:
            dns_servers: DNS服务器列表
            test_params: 测试参数配置
        """
        self.dns_servers = dns_servers
        self.test_params = test_params
        self.dns_resolver = DNSResolverWrapper(
            dns_servers,
            dns_threads=test_params.get("dns_threads", 10),
        )
    
    def comprehensive_resolve(self, domains: List[str]) -> Tuple[Dict[str, Dict], Set[str]]:
        """综合解析模式 - 并行解析所有域名
        
        Args:
            domains: 域名列表
            
        Returns:
            tuple: (域名到IP映射字典, 所有唯一IP集合)
        """
        print(TerminalUtils.colored("\n=== 综合解析模式 ===", Color.CYAN, Color.BOLD))
        
        # 并行解析所有域名
        domain_ip_map = self.dns_resolver.parallel_resolve(domains)
        
        # 收集所有唯一IP
        all_ips = set()
        print("\n=== 解析结果汇总 ===")
        
        for domain, dns_results in domain_ip_map.items():
            if dns_results["unique_ips"]:
                all_ips.update(dns_results["unique_ips"].keys())
                print(f"域名 {domain} 解析到 {len(dns_results['unique_ips'])} 个IP")
            else:
                print(f"域名 {domain} 未解析到任何IP")
        
        return domain_ip_map, all_ips
    
    def sequential_resolve(self, domains: List[str]) -> Dict[str, Dict]:
        """依次解析模式 - 逐个解析域名
        
        Args:
            domains: 域名列表
            
        Returns:
            Dict[str, Dict]: 域名到IP映射字典
        """
        print(TerminalUtils.colored("\n=== 依次解析模式 ===", Color.CYAN, Color.BOLD))
        
        domain_ip_map = {}
        
        for domain in domains:
            print(TerminalUtils.colored(f"\n=== 处理域名: {domain} ===", Color.CYAN, Color.BOLD))
            
            # 执行DNS解析
            dns_results = self.dns_resolver.resolve(domain)
            domain_ip_map[domain] = dns_results
            
            # 显示DNS解析结果
            self.dns_resolver.display_results(dns_results)
        
        return domain_ip_map
    
    def get_domain_ips(self, domain_ip_map: Dict[str, Dict], domain: str) -> List[str]:
        """获取指定域名的IP列表
        
        Args:
            domain_ip_map: 域名到IP映射字典
            domain: 域名
            
        Returns:
            List[str]: IP列表
        """
        if domain not in domain_ip_map:
            return []
        
        return list(domain_ip_map[domain]["unique_ips"].keys())
    
    def has_valid_ips(self, domain_ip_map: Dict[str, Dict], domain: str = None) -> bool:
        """检查是否有有效的IP地址
        
        Args:
            domain_ip_map: 域名到IP映射字典
            domain: 可选，指定域名
            
        Returns:
            bool: 是否有有效IP
        """
        if domain:
            return (domain in domain_ip_map and 
                   domain_ip_map[domain]["unique_ips"])
        else:
            return any(dns_results["unique_ips"] 
                      for dns_results in domain_ip_map.values())
    
    def get_all_unique_ips(self, domain_ip_map: Dict[str, Dict]) -> Set[str]:
        """获取所有唯一IP地址
        
        Args:
            domain_ip_map: 域名到IP映射字典
            
        Returns:
            Set[str]: 所有唯一IP集合
        """
        all_ips = set()
        for dns_results in domain_ip_map.values():
            if dns_results["unique_ips"]:
                all_ips.update(dns_results["unique_ips"].keys())
        return all_ips
    
    def display_resolution_summary(self, domain_ip_map: Dict[str, Dict]):
        """显示解析结果汇总
        
        Args:
            domain_ip_map: 域名到IP映射字典
        """
        total_domains = len(domain_ip_map)
        total_ips = len(self.get_all_unique_ips(domain_ip_map))
        
        print(f"\n=== 解析汇总 ===")
        print(f"总域名数: {total_domains}")
        print(f"总IP数: {total_ips}")
        
        for domain, dns_results in domain_ip_map.items():
            ip_count = len(dns_results["unique_ips"]) if dns_results["unique_ips"] else 0
            status = "成功" if ip_count > 0 else "失败"
            print(f"  {domain}: {ip_count} 个IP ({status})")