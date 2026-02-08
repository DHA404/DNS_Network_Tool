#!/usr/bin/env python3
"""
网络测试服务模块 - 负责网络测试相关的所有操作
"""

from typing import List, Dict
from terminal_utils import TerminalUtils, Color
from network_utils import NetworkTestManager


class NetworkService:
    """网络测试服务 - 统一管理网络测试相关的所有操作"""
    
    def __init__(self, test_params: Dict):
        """初始化网络测试服务
        
        Args:
            test_params: 测试参数配置
        """
        self.test_params = test_params
        self.network_manager = NetworkTestManager(
            ping_params={
                "count": test_params["ping_count"],
                "timeout": test_params["ping_timeout"],
                "packet_size": 64,
            },
            speed_params={
                "test_duration": test_params["test_duration"],
                "packet_size": test_params["packet_size"],
                "concurrent_connections": test_params["concurrent_connections"],
                "speed_test_method": test_params.get("speed_test_method", "both"),
                "min_data_threshold": test_params.get("min_data_threshold", 1048576),
                "min_valid_data": test_params.get("min_valid_data", 102400),
                "min_speed": test_params.get("min_speed", 1.0),
            },
            enable_download=test_params.get("enable_download_test", True),
            enable_upload=test_params.get("enable_upload_test", False),
            max_workers=test_params.get("max_threads", 50),
        )
    
    def test_ips(self, ips: List[str], test_types: List[str]) -> List[Dict]:
        """测试IP列表
        
        Args:
            ips: IP地址列表
            test_types: 测试类型列表
            
        Returns:
            List[Dict]: 测试结果列表
        """
        if not ips:
            return []
        
        print(TerminalUtils.colored(f"\n=== 网络测试 ===", Color.CYAN, Color.BOLD))
        print(f"共 {len(ips)} 个IP，开始测试...")
        
        # 执行网络测试
        network_results = self.network_manager.test_ips(ips, test_types=test_types)
        
        return network_results
    
    def display_test_results(self, network_results: List[Dict], domain_ip_map: Dict[str, Dict]):
        """显示测试结果
        
        Args:
            network_results: 网络测试结果
            domain_ip_map: 域名到IP映射字典
        """
        self.network_manager.display_test_results(network_results, domain_ip_map)
    
    def get_best_ips(self, network_results: List[Dict], sort_by: str = "latency", top_n: int = 10) -> List[Dict]:
        """获取最佳IP列表
        
        Args:
            network_results: 网络测试结果
            sort_by: 排序方式 ("latency", "speed", "balance")
            top_n: 返回的IP数量
            
        Returns:
            List[Dict]: 最佳IP列表
        """
        return self.network_manager.get_best_ips(network_results, sort_by=sort_by, top_n=top_n)
    
    def test_domain_ips(self, domain_ip_map: Dict[str, Dict], domain: str, test_types: List[str]) -> List[Dict]:
        """测试指定域名的IP
        
        Args:
            domain_ip_map: 域名到IP映射字典
            domain: 域名
            test_types: 测试类型列表
            
        Returns:
            List[Dict]: 测试结果列表
        """
        ips = self._get_domain_ips(domain_ip_map, domain)
        if not ips:
            return []
        
        return self.test_ips(ips, test_types)
    
    def _get_domain_ips(self, domain_ip_map: Dict[str, Dict], domain: str) -> List[str]:
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
    
    def has_test_results(self, network_results: List[Dict]) -> bool:
        """检查是否有有效的测试结果
        
        Args:
            network_results: 网络测试结果
            
        Returns:
            bool: 是否有有效结果
        """
        return len(network_results) > 0
    
    def get_test_summary(self, network_results: List[Dict]) -> Dict:
        """获取测试结果汇总信息
        
        Args:
            network_results: 网络测试结果
            
        Returns:
            Dict: 汇总信息
        """
        if not network_results:
            return {"total_ips": 0, "successful_tests": 0, "failed_tests": 0}
        
        successful_tests = 0
        failed_tests = 0
        
        for result in network_results:
            ping = result.get("ping", {})
            if ping and ping.get("success", False):
                successful_tests += 1
            else:
                failed_tests += 1
        
        return {
            "total_ips": len(network_results),
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": successful_tests / len(network_results) * 100 if network_results else 0
        }