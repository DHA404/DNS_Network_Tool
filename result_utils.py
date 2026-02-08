#!/usr/bin/env python3
# 结果输出工具模块

import csv
import os
import subprocess
import sys
from datetime import datetime
from terminal_utils import TerminalUtils, Color


class ResultExporter:
    """结果导出类"""

    @staticmethod
    def copy_to_clipboard(text):
        """将文本安全地复制到剪贴板
        
        Args:
            text: 要复制到剪贴板的文本内容
            
        Returns:
            tuple: (成功状态, 消息)
        """
        if not text:
            return False, "没有可复制的内容"
        
        if not isinstance(text, str):
            return False, "输入内容必须是字符串类型"
        
        if len(text) > 1024 * 1024:
            return False, "内容过大，无法复制到剪贴板"
        
        try:
            if sys.platform == "win32":
                utf16_text = text.encode("utf-16-le")
                result = subprocess.run(
                    ["clip"],
                    input=utf16_text,
                    check=True,
                    timeout=5,
                    capture_output=True
                )
            elif sys.platform == "darwin":
                result = subprocess.run(
                    ["pbcopy"],
                    input=text.encode("utf-8"),
                    check=True,
                    timeout=5,
                    capture_output=True
                )
            else:
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=True,
                    timeout=5,
                    capture_output=True
                )
            return True, "内容已成功复制到剪贴板"
        except subprocess.TimeoutExpired:
            return False, "复制到剪贴板超时，请稍后重试"
        except FileNotFoundError:
            return False, "剪贴板工具未安装，请安装相应的剪贴板工具"
        except subprocess.CalledProcessError as e:
            return False, f"复制到剪贴板失败: 命令执行错误"
        except Exception as e:
            return False, f"复制到剪贴板失败: {str(e)}"

    @staticmethod
    def generate_hosts_file(domain, ips, output_path=None):
        """生成标准hosts文件格式条目"""
        if not ips:
            return None, "没有可用的IP地址"

        # 生成hosts内容
        hosts_content = "# DNS Network Tool 生成的hosts条目\n"
        hosts_content += f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        hosts_content += f"# 域名: {domain}\n"
        hosts_content += f"# 共 {len(ips)} 个IP地址\n\n"

        for ip in ips:
            hosts_content += f"{ip} {domain}\n"

        # 默认将内容复制到剪贴板
        copy_success, copy_message = ResultExporter.copy_to_clipboard(hosts_content)

        # 如果指定了输出路径，写入文件
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(hosts_content)
                return hosts_content, f"hosts文件已成功生成到: {output_path}，{copy_message}"
            except Exception as e:
                return hosts_content, f"生成hosts文件失败: {str(e)}，但{copy_message}"

        return hosts_content, copy_message

    @staticmethod
    def export_to_txt(results, output_path):
        """将测试结果导出为纯文本表格格式"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                # 写入标题和时间
                f.write("=" * 100 + "\n")
                f.write("DNS 解析与网络测试报告\n")
                f.write("=" * 100 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"测试IP数量: {len(results)}\n")
                f.write("=" * 100 + "\n\n")

                # 写入表头
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

                # 计算列宽
                col_widths = [len(header) for header in headers]

                # 收集所有行数据，计算最大列宽
                rows = []
                for result in results:
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
                    rows.append(row)

                    # 更新列宽
                    for i, value in enumerate(row):
                        if len(value) > col_widths[i]:
                            col_widths[i] = len(value)

                # 写入表头
                header_line = "|"
                for i, header in enumerate(headers):
                    header_line += f" {header.ljust(col_widths[i])} |"
                f.write(header_line + "\n")

                # 写入分隔线
                separator_line = "|"
                for width in col_widths:
                    separator_line += f"-{'-' * width}-|"
                f.write(separator_line + "\n")

                # 写入数据行
                for row in rows:
                    row_line = "|"
                    for i, value in enumerate(row):
                        row_line += f" {value.ljust(col_widths[i])} |"
                    f.write(row_line + "\n")

                # 写入分隔线
                f.write(separator_line + "\n")

            return True, f"测试报告已成功导出到: {output_path}"
        except Exception as e:
            return False, f"导出测试报告失败: {str(e)}"

    @staticmethod
    def export_to_csv(results, output_path):
        """将测试结果导出为CSV格式"""
        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # 写入表头
                headers = [
                    "IP地址",
                    "最小延迟(ms)",
                    "最大延迟(ms)",
                    "平均延迟(ms)",
                    "抖动(ms)",
                    "丢包率(%)",
                    "下载速度(Mbps)",
                    "上传速度(Mbps)",
                    "测试时间",
                ]
                writer.writerow(headers)

                # 写入数据行
                for result in results:
                    ip = result["ip"]
                    ping = result["ping"]
                    speed = result["speed"]
                    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 格式化ping数据
                    if ping and ping["success"]:
                        min_delay = ping["min_delay"] if ping["min_delay"] != float("inf") else ""
                        max_delay = ping["max_delay"] if ping["max_delay"] > 0 else ""
                        avg_delay = round(ping["avg_delay"], 2) if ping["avg_delay"] > 0 else ""
                        jitter = round(ping["jitter"], 2) if ping["jitter"] > 0 else ""
                        packet_loss = round(ping["packet_loss"], 1)
                    else:
                        min_delay = max_delay = avg_delay = jitter = packet_loss = ""

                    # 格式化速率数据
                    download_speed = ""
                    upload_speed = ""
                    if speed:
                        if speed["download"] and speed["download"]["success"]:
                            download_speed = speed["download"]["speed_mbps"]
                        if speed["upload"] and speed["upload"]["success"]:
                            upload_speed = speed["upload"]["speed_mbps"]

                    # 写入行数据
                    writer.writerow(
                        [ip, min_delay, max_delay, avg_delay, jitter, packet_loss, download_speed, upload_speed, test_time]
                    )

            return True, f"测试报告已成功导出到: {output_path}"
        except Exception as e:
            return False, f"导出测试报告失败: {str(e)}"

    @staticmethod
    def export_results(results, domain, output_format="txt", output_dir=None):
        """导出测试结果"""
        # 如果没有指定输出目录，默认导出到桌面
        if output_dir is None:
            # 获取用户主目录
            user_home = os.path.expanduser("~")
            # 根据操作系统获取桌面路径
            if sys.platform == "win32":
                # Windows系统
                output_dir = os.path.join(user_home, "Desktop")
            elif sys.platform == "darwin":
                # macOS系统
                output_dir = os.path.join(user_home, "Desktop")
            else:
                # Linux系统
                output_dir = os.path.join(user_home, "Desktop")

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_test_report_{timestamp}.{output_format}"
        output_path = os.path.join(output_dir, filename)

        # 根据格式导出
        if output_format == "txt":
            return ResultExporter.export_to_txt(results, output_path)
        elif output_format == "csv":
            return ResultExporter.export_to_csv(results, output_path)
        else:
            return False, f"不支持的输出格式: {output_format}"


class ResultProcessor:
    """结果处理类"""

    @staticmethod
    def filter_results(results, filters):
        """根据过滤条件筛选结果"""
        filtered = []

        for result in results:
            match = True

            # 按延迟过滤
            if "min_latency" in filters:
                if result["ping"] and result["ping"]["success"]:
                    if result["ping"]["avg_delay"] < filters["min_latency"]:
                        match = False
                else:
                    match = False

            if "max_latency" in filters:
                if result["ping"] and result["ping"]["success"]:
                    if result["ping"]["avg_delay"] > filters["max_latency"]:
                        match = False
                else:
                    match = False

            # 按丢包率过滤
            if "max_packet_loss" in filters:
                if result["ping"] and result["ping"]["success"]:
                    if result["ping"]["packet_loss"] > filters["max_packet_loss"]:
                        match = False
                else:
                    match = False

            # 按下载速度过滤
            if "min_download_speed" in filters:
                if result["speed"] and result["speed"]["download"] and result["speed"]["download"]["success"]:
                    if result["speed"]["download"]["speed_mbps"] < filters["min_download_speed"]:
                        match = False
                else:
                    match = False

            if match:
                filtered.append(result)

        return filtered

    @staticmethod
    def sort_results(results, sort_by="latency", ascending=True):
        """根据指定字段排序结果"""
        if not results:
            return results

        # 定义排序键函数
        def get_sort_key(result):
            if sort_by == "latency":
                if result["ping"] and result["ping"]["success"]:
                    return result["ping"]["avg_delay"]
                return float("inf")
            elif sort_by == "packet_loss":
                if result["ping"] and result["ping"]["success"]:
                    return result["ping"]["packet_loss"]
                return 100
            elif sort_by == "download_speed":
                if result["speed"] and result["speed"]["download"] and result["speed"]["download"]["success"]:
                    return result["speed"]["download"]["speed_mbps"]
                return 0
            elif sort_by == "upload_speed":
                if result["speed"] and result["speed"]["upload"] and result["speed"]["upload"]["success"]:
                    return result["speed"]["upload"]["speed_mbps"]
                return 0
            elif sort_by == "jitter":
                if result["ping"] and result["ping"]["success"]:
                    return result["ping"]["jitter"]
                return float("inf")
            else:
                return 0

        # 排序
        return sorted(results, key=get_sort_key, reverse=not ascending)

    @staticmethod
    def get_top_ips(results, sort_by="latency", top_n=10):
        """获取排名靠前的IP"""
        sorted_results = ResultProcessor.sort_results(results, sort_by)
        return sorted_results[:top_n]


class ResultDisplay:
    """结果显示类"""

    @staticmethod
    def display_summary(results):
        """显示测试结果摘要"""
        if not results:
            print(TerminalUtils.colored("没有测试结果", Color.RED))
            return

        # 计算统计信息
        total_ips = len(results)
        successful_ping = sum(1 for r in results if r["ping"] and r["ping"]["success"])
        successful_speed = sum(1 for r in results if r["speed"] and r["speed"]["download"] and r["speed"]["download"]["success"])

        # 计算平均延迟
        avg_latency = 0
        if successful_ping > 0:
            total_latency = sum(r["ping"]["avg_delay"] for r in results if r["ping"] and r["ping"]["success"])
            avg_latency = round(total_latency / successful_ping, 2)

        # 计算平均下载速度
        avg_download_speed = 0
        if successful_speed > 0:
            total_speed = sum(
                r["speed"]["download"]["speed_mbps"]
                for r in results
                if r["speed"] and r["speed"]["download"] and r["speed"]["download"]["success"]
            )
            avg_download_speed = round(total_speed / successful_speed, 2)

        # 显示摘要
        print(TerminalUtils.colored("\n=== 测试结果摘要 ===", Color.CYAN, Color.BOLD))
        print(f"测试IP总数: {total_ips}")
        print(f"Ping测试成功: {TerminalUtils.colored(successful_ping, Color.GREEN)}")
        print(f"速率测试成功: {TerminalUtils.colored(successful_speed, Color.GREEN)}")
        print(f"平均延迟: {avg_latency} ms")
        print(f"平均下载速度: {avg_download_speed} Mbps")

    @staticmethod
    def display_detailed_results(results):
        """显示详细测试结果"""
        from network_utils import NetworkTestManager

        network_manager = NetworkTestManager()
        network_manager.display_test_results(results)

    @staticmethod
    def display_hosts_preview(domain, ips, max_count=10):
        """显示hosts文件预览"""
        print(TerminalUtils.colored("\n=== Hosts文件预览 ===", Color.CYAN, Color.BOLD))
        print(f"# 域名: {domain}")
        print(f"# 共 {len(ips)} 个IP地址")
        print("# 前 {min(max_count, len(ips))} 个IP:")

        for ip in ips[:max_count]:
            print(f"{ip}    {domain}")

        if len(ips) > max_count:
            print(f"# ... 还有 {len(ips) - max_count} 个IP未显示")


class ResultManager:
    """结果管理类，整合所有结果处理功能"""

    def __init__(self):
        self.exporter = ResultExporter()
        self.processor = ResultProcessor()
        self.display = ResultDisplay()

    def process_and_export(self, results, domain, options):
        """处理并导出结果"""
        # 筛选结果
        if "filters" in options:
            results = self.processor.filter_results(results, options["filters"])

        # 排序结果
        if "sort_by" in options:
            results = self.processor.sort_results(results, options["sort_by"], options.get("ascending", True))

        # 显示结果
        self.display.display_summary(results)
        self.display.display_detailed_results(results)

        # 生成hosts文件
        if options.get("generate_hosts", False):
            # 只保留最佳IP（第一个）
            top_results = self.processor.get_top_ips(results, options.get("sort_by", "latency"))
            top_ips = [top_results[0]["ip"]] if top_results else []
            hosts_content, message = self.exporter.generate_hosts_file(domain, top_ips, options.get("hosts_output_path"))
            print(f"\n{message}")

            if hosts_content and not options.get("hosts_output_path"):
                # 显示hosts内容预览
                print(TerminalUtils.colored("\n=== Hosts内容预览 ===", Color.CYAN, Color.BOLD))
                print(hosts_content)

        # 导出报告
        if options.get("export_report", False):
            success, message = self.exporter.export_results(
                results, domain, options.get("output_format", "txt"), options.get("output_dir", "./reports")
            )
            print(f"\n{message}")

        return results
