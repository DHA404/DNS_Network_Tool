#!/usr/bin/env python3
"""
报告生成模块 - 负责测试报告的生成和导出
"""

import os
import shutil
from datetime import datetime
from typing import List, Dict
from terminal_utils import TerminalUtils, Color


class ReportGenerator:
    """报告生成器 - 统一管理测试报告的生成和导出"""
    
    def __init__(self, output_dir: str = None):
        """初始化报告生成器
        
        Args:
            output_dir: 输出目录，默认为程序目录下的测试结果文件夹
        """
        if output_dir is None:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.join(current_dir, "测试结果")
        else:
            self.output_dir = output_dir
    
    def export_test_reports(self, network_results: List[Dict], network_manager):
        """导出测试报告到指定目录
        
        Args:
            network_results: 网络测试结果
            network_manager: 网络管理器实例，用于获取最佳IP
        """
        if not network_results:
            print(TerminalUtils.colored("没有测试结果可导出", Color.YELLOW))
            return
        
        # 准备输出目录
        self._prepare_output_directory()
        
        # 定义排序方式
        sort_modes = {
            "latency": "延迟优先",
            "speed": "速率优先", 
            "balance": "平衡模式"
        }
        
        # 预格式化所有网络结果
        formatted_results = self._format_network_results(network_results)
        
        # 按三种排序方式导出
        exported_files = []
        for sort_key, sort_name in sort_modes.items():
            filename = self._generate_report_filename(sort_name)
            file_path = os.path.join(self.output_dir, filename)
            
            if self._export_single_report(network_results, network_manager, formatted_results, 
                                        file_path, sort_key, sort_name):
                exported_files.append(filename)
        
        # 显示导出结果
        self._display_export_summary(exported_files, sort_modes)
    
    def _prepare_output_directory(self):
        """准备输出目录"""
        # 自动删除上一次的测试记录
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _format_network_results(self, network_results: List[Dict]) -> Dict[str, List[str]]:
        """格式化网络测试结果
        
        Args:
            network_results: 网络测试结果
            
        Returns:
            Dict[str, List[str]]: 格式化后的结果字典
        """
        headers = [
            "IP地址",
            "最小延迟(ms)",
            "最大延迟(ms)", 
            "平均延迟(ms)",
            "抖动(ms)",
            "丢包率(%)",
            "下载速度(Mbps)",
            "上传速度(Mbps)",
        ]
        
        # 格式化所有结果，计算最大列宽
        formatted_results = {}
        max_col_widths = [len(header) for header in headers]
        
        for result in network_results:
            ip = result["ip"]
            ping = result["ping"]
            speed = result["speed"]
            
            # 格式化ping数据
            if ping and ping["success"]:
                min_delay = f"{ping['min_delay']}" if ping["min_delay"] != float("inf") else "N/A"
                max_delay = f"{ping['max_delay']}" if ping["max_delay"] > 0 else "N/A"
                avg_delay = f"{ping['avg_delay']:.2f}" if ping["avg_delay"] > 0 else "N/A"
                jitter = f"{ping['jitter']:.2f}" if ping["jitter"] > 0 else "N/A"
                packet_loss = f"{ping['packet_loss']:.1f}"
            else:
                min_delay = max_delay = avg_delay = jitter = packet_loss = "N/A"
            
            # 格式化速率数据
            download_speed = "N/A"
            upload_speed = "N/A"
            if speed:
                if speed["download"] and speed["download"]["success"]:
                    download_speed = f"{speed['download']['speed_mbps']}"
                if speed["upload"] and speed["upload"]["success"]:
                    upload_speed = f"{speed['upload']['speed_mbps']}"
            
            row = [ip, min_delay, max_delay, avg_delay, jitter, packet_loss, download_speed, upload_speed]
            formatted_results[ip] = row
            
            # 更新全局最大列宽
            for i, value in enumerate(row):
                if len(value) > max_col_widths[i]:
                    max_col_widths[i] = len(value)
        
        return formatted_results
    
    def _generate_report_filename(self, sort_name: str) -> str:
        """生成报告文件名
        
        Args:
            sort_name: 排序方式名称
            
        Returns:
            str: 文件名
        """
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        return f"{timestamp}-{sort_name}.txt"
    
    def _export_single_report(self, network_results: List[Dict], network_manager, 
                            formatted_results: Dict, file_path: str, 
                            sort_key: str, sort_name: str) -> bool:
        """导出单个报告文件
        
        Args:
            network_results: 网络测试结果
            network_manager: 网络管理器实例
            formatted_results: 格式化后的结果
            file_path: 文件路径
            sort_key: 排序键
            sort_name: 排序名称
            
        Returns:
            bool: 是否导出成功
        """
        try:
            # 获取对应排序方式的最佳IP
            sorted_ips = network_manager.get_best_ips(network_results, sort_by=sort_key, top_n=10)
            
            headers = [
                "IP地址",
                "最小延迟(ms)",
                "最大延迟(ms)",
                "平均延迟(ms)",
                "抖动(ms)",
                "丢包率(%)",
                "下载速度(Mbps)",
                "上传速度(Mbps)",
            ]
            
            # 计算最大列宽
            max_col_widths = [len(header) for header in headers]
            for result in network_results:
                ip = result["ip"]
                if ip in formatted_results:
                    row = formatted_results[ip]
                    for i, value in enumerate(row):
                        if len(value) > max_col_widths[i]:
                            max_col_widths[i] = len(value)
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                # 写入标题和时间
                f.write("=" * 100 + "\n")
                f.write(f"DNS 解析与网络测试报告 - {sort_name}\n")
                f.write("=" * 100 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"测试IP数量: {len(sorted_ips)}\n")
                f.write(f"排序方式: {sort_name}\n")
                f.write("=" * 100 + "\n\n")
                
                # 写入表头
                header_line = "|"
                for i, header in enumerate(headers):
                    header_line += f" {header.ljust(max_col_widths[i])} |"
                f.write(header_line + "\n")
                
                # 写入分隔线
                separator_line = "|"
                for width in max_col_widths:
                    separator_line += f"-{'-' * width}-|"
                f.write(separator_line + "\n")
                
                # 写入数据行
                for result in sorted_ips:
                    ip = result["ip"]
                    if ip in formatted_results:
                        row = formatted_results[ip]
                        row_line = "|"
                        for i, value in enumerate(row):
                            row_line += f" {value.ljust(max_col_widths[i])} |"
                        f.write(row_line + "\n")
                
                # 写入分隔线
                f.write(separator_line + "\n")
                
                # 检查是否有失败的测试，如果有则添加调试信息
                failed_tests = []
                for result in network_results:
                    if result.get("ping") and not result["ping"].get("success", False):
                        failed_tests.append(result)
                
                if failed_tests:
                    f.write("\n" + "=" * 100 + "\n")
                    f.write("调试信息 - 失败的测试\n")
                    f.write("=" * 100 + "\n")
                    for result in failed_tests[:5]:  # 只显示前5个失败的测试
                        ip = result["ip"]
                        ping_result = result.get("ping", {})
                        f.write(f"IP: {ip}\n")
                        if ping_result.get("error"):
                            f.write(f"错误: {ping_result['error']}\n")
                        if ping_result.get("debug_info"):
                            f.write(f"调试信息: {ping_result['debug_info'][:200]}...\n")
                        f.write("-" * 50 + "\n")
            
            return True
            
        except Exception as e:
            print(TerminalUtils.colored(f"导出报告失败: {e}", Color.RED))
            return False
    
    def _display_export_summary(self, exported_files: List[str], sort_modes: Dict[str, str]):
        """显示导出汇总信息
        
        Args:
            exported_files: 导出的文件列表
            sort_modes: 排序方式字典
        """
        print(TerminalUtils.colored(f"\n=== 测试报告已自动导出到 {self.output_dir} ===", Color.GREEN, Color.BOLD))
        print(TerminalUtils.colored(f"生成了 {len(exported_files)} 份报告，按三种排序方式分类", Color.GREEN))
        
        for filename in exported_files:
            print(f"  - {filename}")
    
    def generate_summary_report(self, domains: List[str], network_results: List[Dict], 
                              domain_ip_map: Dict) -> str:
        """生成汇总报告
        
        Args:
            domains: 域名列表
            network_results: 网络测试结果
            domain_ip_map: 域名到IP映射字典
            
        Returns:
            str: 汇总报告内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"# DNS Network Tool 测试汇总报告\n"
        report += f"生成时间: {timestamp}\n"
        report += f"测试域名数: {len(domains)}\n"
        report += f"测试IP数: {len(network_results)}\n\n"
        
        # 域名解析统计
        report += "## 域名解析统计\n"
        for domain in domains:
            if domain in domain_ip_map:
                ip_count = len(domain_ip_map[domain]["unique_ips"])
                report += f"- {domain}: {ip_count} 个IP\n"
        
        # 网络测试统计
        report += "\n## 网络测试统计\n"
        successful_tests = 0
        for result in network_results:
            ping = result.get("ping", {})
            if ping and ping.get("success", False):
                successful_tests += 1
        
        report += f"- 成功测试: {successful_tests}/{len(network_results)}\n"
        report += f"- 成功率: {successful_tests/len(network_results)*100:.1f}%\n" if network_results else "- 成功率: 0%\n"
        
        return report