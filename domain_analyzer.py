#!/usr/bin/env python3
# 域名分析模块

import os
import socket
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import re

from terminal_utils import TerminalUtils, Color


@dataclass
class DomainInfo:
    """域名信息数据类"""
    domain: str
    ip_address: str
    access_count: int = 1
    first_access: str = ""
    last_access: str = ""
    protocols: Set[str] = field(default_factory=set)
    ports: Set[int] = field(default_factory=set)
    connection_statuses: Set[str] = field(default_factory=set)
    resolved: bool = True
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "ip_address": self.ip_address,
            "access_count": self.access_count,
            "first_access": self.first_access,
            "last_access": self.last_access,
            "protocols": list(self.protocols),
            "ports": list(self.ports),
            "connection_statuses": list(self.connection_statuses),
            "resolved": self.resolved,
            "error_message": self.error_message
        }


class DomainAnalyzer:
    """域名分析器类"""
    
    def __init__(self, max_concurrent_resolves: int = 20, resolve_timeout: float = 2.0):
        self.max_concurrent_resolves = max_concurrent_resolves
        self.resolve_timeout = resolve_timeout
        self._resolve_lock = threading.Lock()
        
    def _is_valid_ip(self, address: str) -> bool:
        """检查是否为有效IP地址（IPv4）"""
        try:
            socket.inet_pton(socket.AF_INET, address)
            return True
        except (socket.error, OSError):
            return False
    
    def _is_valid_ipv6(self, address: str) -> bool:
        """检查是否为有效IPv6地址"""
        try:
            socket.inet_pton(socket.AF_INET6, address)
            return True
        except (socket.error, OSError):
            return False
    
    def _is_private_ip(self, address: str) -> bool:
        """检查是否为私有IP地址"""
        if not address:
            return False
        
        if self._is_valid_ipv6(address):
            return address.startswith('fe80::') or address.startswith('::1')
        
        if not self._is_valid_ip(address):
            return False
        
        private_ranges = [
            ('10.0.0.0', '10.255.255.255'),
            ('172.16.0.0', '172.31.255.255'),
            ('192.168.0.0', '192.168.255.255'),
            ('127.0.0.0', '127.0.0.255'),
        ]
        
        try:
            ip_num = sum(int(x) << (24 - 8 * i) for i, x in enumerate(address.split('.')))
            for start, end in private_ranges:
                start_parts = list(map(int, start.split('.')))
                end_parts = list(map(int, end.split('.')))
                start_num = sum(x << (24 - 8 * i) for i, x in enumerate(start_parts))
                end_num = sum(x << (24 - 8 * i) for i, x in enumerate(end_parts))
                
                if start_num <= ip_num <= end_num:
                    return True
        except (ValueError, IndexError):
            pass
        
        return False
    
    def _reverse_dns(self, ip_address: str) -> Optional[str]:
        """反向DNS解析"""
        try:
            return socket.gethostbyaddr(ip_address)[0]
        except (socket.herror, socket.gaierror, OSError):
            return None
    
    def _safe_resolve(self, ip_address: str) -> str:
        """线程安全的DNS解析"""
        with self._resolve_lock:
            try:
                hostname = socket.gethostbyaddr(ip_address)[0]
                return hostname
            except (socket.herror, socket.gaierror, OSError):
                return ip_address
    
    def _extract_domain_from_connection(self, remote_address: str, port: int) -> str:
        """从连接中提取域名"""
        if not remote_address or remote_address == '0.0.0.0':
            return ""
        
        if self._is_private_ip(remote_address):
            return f"local:{remote_address}:{port}"
        
        return remote_address
    
    def _filter_valid_connections(self, connections: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """过滤有效连接并按IP分组
        
        Args:
            connections: 连接数据列表
            
        Returns:
            Dict[str, List[Dict]]: 按IP分组的连接字典
        """
        unique_ips: Dict[str, List[Dict]] = defaultdict(list)
        
        for conn in connections:
            remote_addr = conn.get('remote_address', '')
            
            if not remote_addr or remote_addr == '0.0.0.0' or remote_addr.startswith('::'):
                continue
            
            if self._is_private_ip(remote_addr):
                domain_key = f"local:{remote_addr}"
            else:
                domain_key = remote_addr
            
            unique_ips[domain_key].append(conn)
        
        return unique_ips

    def _resolve_ip_batch(self, ips: List[str]) -> Dict[str, str]:
        """批量解析IP到域名
        
        Args:
            ips: IP地址列表
            
        Returns:
            Dict[str, str]: IP到域名的映射
        """
        def resolve_single_ip(ip: str) -> Tuple[str, str]:
            if ip.startswith("local:"):
                return (ip, ip)
            try:
                hostname = socket.gethostbyaddr(ip)[0]
                return (ip, hostname)
            except (socket.herror, socket.gaierror, OSError):
                return (ip, ip)
        
        result = {}
        total_ips = len(ips)
        
        if total_ips == 0:
            return result
        
        print(TerminalUtils.colored(f"\n🔄 正在反向解析 {total_ips} 个域名...", Color.CYAN))
        
        import concurrent.futures
        max_workers = min(50, total_ips)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(resolve_single_ip, ip): ip for ip in ips}
            completed = 0
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    ip, hostname = future.result()
                    result[ip] = hostname
                except Exception:
                    pass
                
                completed += 1
                if completed % 5 == 0 or completed == total_ips:
                    progress = int(completed / total_ips * 100)
                    print(f"\r  进度: {progress}% ({completed}/{total_ips})", end="", flush=True)
        
        print(f" ✓ 完成")
        return result

    def _build_domain_info(self, domain_name: str, ip: str, conn_list: List[Dict]) -> DomainInfo:
        """构建域名信息对象
        
        Args:
            domain_name: 域名
            ip: IP地址
            conn_list: 连接列表
            
        Returns:
            DomainInfo: 域名信息对象
        """
        domain_info = DomainInfo(
            domain=domain_name,
            ip_address=ip if not ip.startswith("local:") else ip.split(":")[1] if ":" in ip else ip,
            first_access=conn_list[0].get('timestamp', ''),
            last_access=conn_list[0].get('timestamp', '')
        )
        
        domain_info.access_count = len(conn_list)
        
        for conn in conn_list:
            timestamp = conn.get('timestamp', '')
            if timestamp > domain_info.last_access:
                domain_info.last_access = timestamp
            domain_info.protocols.add(conn.get('protocol', ''))
            domain_info.ports.add(conn.get('remote_port', 0))
            domain_info.connection_statuses.add(conn.get('status', ''))
        
        return domain_info

    def _categorize_domains(self, domain_map: Dict[str, DomainInfo]) -> Tuple[List[DomainInfo], int, int]:
        """分类域名为已解析和未解析
        
        Args:
            domain_map: 域名映射字典
            
        Returns:
            Tuple[List[DomainInfo], int, int]: (域名列表, 已解析数量, 未解析数量)
        """
        final_domains: List[DomainInfo] = []
        resolved_count = 0
        unresolved_count = 0
        
        for domain_key, domain_info in domain_map.items():
            if domain_info.domain.startswith("local:"):
                domain_info.resolved = True
                resolved_count += 1
            elif domain_info.domain != domain_info.ip_address:
                domain_info.resolved = True
                resolved_count += 1
            else:
                domain_info.resolved = False
                unresolved_count += 1
            
            final_domains.append(domain_info)
        
        return final_domains, resolved_count, unresolved_count

    def analyze_connections(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析连接数据并提取域名信息 - 重构版本
        
        Args:
            connections: 连接数据列表
            
        Returns:
            域名分析结果
        """
        if not connections:
            return {
                "success": True,
                "message": "没有连接数据可供分析",
                "domains": [],
                "statistics": {
                    "total_connections": 0,
                    "unique_domains": 0,
                    "resolved_domains": 0,
                    "unresolved_domains": 0
                }
            }
        
        unique_ips = self._filter_valid_connections(connections)
        ip_to_domain = self._resolve_ip_batch(list(unique_ips.keys()))
        
        domain_map: Dict[str, DomainInfo] = {}
        
        for ip, conn_list in unique_ips.items():
            domain_name = ip_to_domain.get(ip, ip)
            
            if domain_name not in domain_map:
                domain_map[domain_name] = self._build_domain_info(domain_name, ip, conn_list)
        
        final_domains, resolved_count, unresolved_count = self._categorize_domains(domain_map)
        
        sorted_domains = sorted(final_domains, key=lambda x: x.access_count, reverse=True)
        
        return {
            "success": True,
            "message": f"分析完成，发现 {len(sorted_domains)} 个唯一域名",
            "domains": [d.to_dict() for d in sorted_domains],
            "statistics": {
                "total_connections": len(connections),
                "unique_domains": len(sorted_domains),
                "resolved_domains": resolved_count,
                "unresolved_domains": unresolved_count
            },
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def generate_wireshark_filter(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """根据连接数据生成Wireshark过滤器
        
        Args:
            connections: 连接数据列表
            
        Returns:
            Wireshark过滤器信息
        """
        if not connections:
            return {
                "success": True,
                "filter": "",
                "filter_type": "none",
                "message": "没有连接数据",
                "ip_list": [],
                "port_list": [],
                "protocol_stats": {}
            }
        
        ip_set = set()
        port_set = set()
        protocol_stats = defaultdict(int)
        tcp_ports = set()
        udp_ports = set()
        
        for conn in connections:
            remote_addr = conn.get('remote_address', '')
            remote_port = conn.get('remote_port', 0)
            protocol = conn.get('protocol', '').upper()
            
            if remote_addr and remote_addr not in ('0.0.0.0', '::') and not remote_addr.startswith('fe80::'):
                ip_set.add(remote_addr)
            
            if remote_port:
                port_set.add(remote_port)
                if protocol == 'TCP':
                    tcp_ports.add(remote_port)
                elif protocol == 'UDP':
                    udp_ports.add(remote_port)
            
            if protocol:
                protocol_stats[protocol] += 1
        
        ip_list = sorted(ip_set)
        port_list = sorted(port_set)
        
        filters = {
            "ip_filter": "",
            "port_filter": "",
            "combined_filter": ""
        }
        
        if len(ip_list) <= 20:
            ip_expr = " or ".join([f"ip.addr == {ip}" for ip in ip_list])
            filters["ip_filter"] = ip_expr
        else:
            ip_ranges = self._group_ip_addresses(ip_list)
            ip_expr = " or ".join([f"ip.addr >= {r[0]} and ip.addr <= {r[1]}" for r in ip_ranges])
            filters["ip_filter"] = ip_expr
        
        if tcp_ports:
            tcp_expr = " or ".join([f"tcp.port == {p}" for p in sorted(tcp_ports)])
            filters["port_filter"] = tcp_expr
            filters["combined_filter"] = f"({filters['ip_filter']}) and ({tcp_expr})"
        elif udp_ports:
            udp_expr = " or ".join([f"udp.port == {p}" for p in sorted(udp_ports)])
            filters["port_filter"] = udp_expr
            filters["combined_filter"] = f"({filters['ip_filter']}) and ({udp_expr})"
        else:
            filters["combined_filter"] = filters["ip_filter"]
        
        if port_set and not tcp_ports and not udp_ports:
            port_expr = " or ".join([f"tcp.port == {p} or udp.port == {p}" for p in sorted(port_set)])
            filters["port_filter"] = port_expr
            filters["combined_filter"] = f"({filters['ip_filter']}) and ({port_expr})"
        
        return {
            "success": True,
            "filter": filters["combined_filter"],
            "ip_filter": filters["ip_filter"],
            "port_filter": filters["port_filter"],
            "message": f"生成Wireshark过滤器完成",
            "ip_list": ip_list,
            "port_list": port_list,
            "tcp_ports": sorted(tcp_ports),
            "udp_ports": sorted(udp_ports),
            "protocol_stats": dict(protocol_stats),
            "total_ips": len(ip_list),
            "total_ports": len(port_set)
        }
    
    def _group_ip_addresses(self, ip_list: List[str]) -> List[tuple]:
        """将IP地址分组为范围"""
        if not ip_list:
            return []
        
        def ip_to_int(ip):
            parts = ip.split(':')[0].split('.')
            return sum(int(p) << (8 * (3 - i)) for i, p in enumerate(parts))
        
        def int_to_ip(n):
            return '.'.join(str((n >> (8 * i)) & 255) for i in range(3, -1, -1))
        
        sorted_ips = sorted(ip_list, key=ip_to_int)
        ranges = []
        start_ip = sorted_ips[0]
        end_ip = start_ip
        start_int = ip_to_int(start_ip)
        
        for ip in sorted_ips[1:]:
            ip_int = ip_to_int(ip)
            if ip_int == start_int + 1:
                start_int = ip_int
                end_ip = ip
            else:
                ranges.append((start_ip, end_ip))
                start_ip = ip
                start_int = ip_to_int(ip)
                end_ip = ip
        
        ranges.append((start_ip, end_ip))
        
        consolidated = []
        for start, end in ranges:
            consolidated.append((start, end))
        
        return consolidated
    
    def resolve_domains_batch(self, domains: List[DomainInfo], max_workers: int = None) -> List[DomainInfo]:
        """批量解析域名（带缓存）
        
        Args:
            domains: 域名信息列表
            max_workers: 最大并发数
            
        Returns:
            解析后的域名信息列表
        """
        if max_workers is None:
            max_workers = self.max_concurrent_resolves
        
        resolved_count = 0
        error_count = 0
        
        for domain_info in domains:
            if domain_info.domain.startswith("local:"):
                continue
            
            if domain_info.resolved and domain_info.domain != domain_info.ip_address:
                resolved_count += 1
                continue
            
            try:
                hostname = socket.gethostbyaddr(domain_info.ip_address)
                domain_info.domain = hostname
                domain_info.resolved = True
                resolved_count += 1
            except (socket.herror, socket.gaierror, OSError):
                domain_info.resolved = False
                domain_info.error_message = "DNS解析失败"
                error_count += 1
            
            time.sleep(0.05)
        
        return domains
    
    def get_top_domains(self, analysis_result: Dict[str, Any], top_n: int = 20) -> List[Dict[str, Any]]:
        """获取访问次数最多的域名
        
        Args:
            analysis_result: 分析结果
            top_n: 返回前N个
            
        Returns:
            热门域名列表
        """
        domains = analysis_result.get("domains", [])
        return domains[:top_n]
    
    def categorize_domains(self, analysis_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """对域名进行分类
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            按类别分类的域名
        """
        domains = analysis_result.get("domains", [])
        
        categories = {
            "resolved": [],
            "unresolved": [],
            "local_network": [],
            "cloud_services": [],
            "common_patterns": []
        }
        
        cloud_patterns = [
            'amazon', 'aws', 'azure', 'google', 'cloudflare', 'alibaba',
            'tencent', 'huawei', 'baidu', 'apple', 'microsoft'
        ]
        
        common_domains = [
            'facebook', 'twitter', 'instagram', 'youtube', 'netflix',
            'amazon', 'github', 'stackoverflow', 'reddit', 'linkedin'
        ]
        
        for domain_info in domains:
            domain = domain_info.get("domain", "").lower()
            
            if domain.startswith("local:"):
                categories["local_network"].append(domain_info)
            elif not domain_info.get("resolved", True):
                categories["unresolved"].append(domain_info)
            else:
                categories["resolved"].append(domain_info)
                
                for pattern in cloud_patterns:
                    if pattern in domain:
                        categories["cloud_services"].append(domain_info)
                        break
                
                for pattern in common_domains:
                    if pattern in domain:
                        categories["common_patterns"].append(domain_info)
                        break
        
        return categories
    
    def generate_report(self, analysis_result: Dict[str, Any]) -> str:
        """生成格式化的分析报告
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            格式化的报告字符串
        """
        lines = []
        lines.append("=" * 70)
        lines.append("                      网络连接域名分析报告")
        lines.append("=" * 70)
        lines.append("")
        
        stats = analysis_result.get("statistics", {})
        lines.append(f"分析时间: {analysis_result.get('analysis_time', 'Unknown')}")
        lines.append(f"总连接数: {stats.get('total_connections', 0)}")
        lines.append(f"唯一域名: {stats.get('unique_domains', 0)}")
        lines.append(f"已解析: {stats.get('resolved_domains', 0)}")
        lines.append(f"未解析: {stats.get('unresolved_domains', 0)}")
        lines.append("")
        
        lines.append("-" * 70)
        lines.append("                          域名访问排行")
        lines.append("-" * 70)
        lines.append(f"{'排名':<6}{'域名':<35}{'访问次数':<12}{'IP 地址':<20}")
        lines.append("-" * 70)
        
        domains = analysis_result.get("domains", [])
        for i, domain_info in enumerate(domains[:30], 1):
            domain = domain_info.get("domain", "")[:33]
            count = domain_info.get("access_count", 0)
            ip = domain_info.get("ip_address", "")[:18]
            lines.append(f"{i:<6}{domain:<35}{count:<12}{ip:<20}")
        
        lines.append("-" * 70)
        lines.append("")
        
        categories = self.categorize_domains(analysis_result)
        
        if categories["cloud_services"]:
            lines.append("云服务域名:")
            for domain_info in categories["cloud_services"][:10]:
                lines.append(f"  • {domain_info.get('domain', '')}")
            lines.append("")
        
        if categories["common_patterns"]:
            lines.append("常见网站域名:")
            for domain_info in categories["common_patterns"][:10]:
                lines.append(f"  • {domain_info.get('domain', '')}")
            lines.append("")
        
        lines.append("=" * 70)
        lines.append("                        报告生成完毕")
        lines.append("=" * 70)
        
        return "\n".join(lines)


def create_domain_analyzer(
    max_concurrent_resolves: int = 20,
    resolve_timeout: float = 2.0
) -> DomainAnalyzer:
    """创建域名分析器的工厂函数"""
    return DomainAnalyzer(
        max_concurrent_resolves=max_concurrent_resolves,
        resolve_timeout=resolve_timeout
    )
