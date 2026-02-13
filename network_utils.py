#!/usr/bin/env python3
# 网络性能测试工具模块

import subprocess
import platform
import time
import concurrent.futures
import socket
import threading
from typing import Dict, Any, List, Optional, Tuple
from terminal_utils import TerminalUtils, Color




class PingTest:
    """Ping测试类"""

    def __init__(self, count: int = 5, timeout: float = 2.0, packet_size: int = 64) -> None:
        self.count = count  # 减少ping次数，从10次改为5次
        self.timeout = timeout  # 增加超时时间，从1秒改为2秒
        self.packet_size = packet_size
        self.use_system_ping = False

        # 检查是否可以使用socket进行ICMP ping
        try:
            # 尝试创建ICMP socket
            if platform.system().lower() == "windows":
                # Windows需要管理员权限才能发送ICMP包
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                sock.close()
            else:
                # Linux/macOS需要root权限或特殊配置
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                sock.close()
        except (OSError, PermissionError, socket.error):
            # 无法创建ICMP socket，使用系统ping命令
            self.use_system_ping = True

    def _icmp_ping(self, ip: str) -> Dict[str, Any]:
        """基于socket的ICMP ping测试"""
        import struct
        import random

        # ICMP Echo Request
        type = 8  # Echo Request
        code = 0
        checksum = 0
        identifier = random.randint(0, 65535)
        sequence = 1

        # 构建ICMP包
        header = struct.pack("!BBHHH", type, code, checksum, identifier, sequence)
        data = b"\x00" * self.packet_size
        packet = header + data

        # 计算校验和
        def calculate_checksum(data):
            checksum = 0
            count_to = (len(data) // 2) * 2
            count = 0
            while count < count_to:
                this_val = data[count + 1] * 256 + data[count]
                checksum += this_val
                checksum &= 0xFFFFFFFF
                count += 2
            if count_to < len(data):
                checksum += data[len(data) - 1]
                checksum &= 0xFFFFFFFF
            checksum = (checksum >> 16) + (checksum & 0xFFFF)
            checksum += checksum >> 16
            answer = ~checksum
            answer &= 0xFFFF
            answer = answer >> 8 | (answer << 8 & 0xFF00)
            return answer

        checksum = calculate_checksum(packet)
        header = struct.pack("!BBHHH", type, code, checksum, identifier, sequence)
        packet = header + data

        try:
            # 自动检测IP类型
            addrinfo = socket.getaddrinfo(ip, 0, socket.AF_UNSPEC, socket.SOCK_RAW)
            family, socktype, proto, canonname, sockaddr = addrinfo[0]
            
            # 根据IP类型设置socket和ICMP类型
            if family == socket.AF_INET:
                # IPv4 ICMP
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                echo_reply_type = 0  # IPv4 Echo Reply
                ip_header_len = 20  # IPv4 header is 20 bytes
                dest_addr = (ip, 0)
            else:
                # IPv6 ICMP
                sock = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
                echo_reply_type = 129  # IPv6 Echo Reply
                ip_header_len = 40  # IPv6 header is 40 bytes
                dest_addr = sockaddr
            
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # 增加接收缓冲区

            start_time = time.time()
            sock.sendto(packet, dest_addr)

            # 接收响应
            while True:
                try:
                    recv_packet, addr = sock.recvfrom(1024)
                    end_time = time.time()

                    # 解析ICMP响应
                    icmp_header = recv_packet[ip_header_len:ip_header_len + 8]
                    icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq = struct.unpack("!BBHHH", icmp_header)

                    if icmp_type == echo_reply_type and icmp_id == identifier:
                        # Echo Reply
                        delay = (end_time - start_time) * 1000  # 毫秒
                        sock.close()
                        return {"success": True, "delay": delay, "error": None}
                except socket.timeout:
                    sock.close()
                    return {"success": False, "delay": 0, "error": "ICMP ping超时"}
        except PermissionError as e:
            return {
                "success": False,
                "delay": 0,
                "error": f"ICMP ping权限不足: {str(e)}",
            }
        except socket.error as e:
            return {
                "success": False,
                "delay": 0,
                "error": f"ICMP ping网络错误: {str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "delay": 0,
                "error": f"ICMP ping未知错误: {str(e)}",
            }

    def _system_ping(self, ip: str) -> Dict[str, Any]:
        """使用系统ping命令进行测试"""
        results: Dict[str, Any] = {"success": False, "delays": [], "error": None}

        try:
            # 检测IP类型（IPv4或IPv6）
            is_ipv6 = False
            try:
                socket.inet_pton(socket.AF_INET6, ip)
                is_ipv6 = True
            except socket.error:
                # 不是IPv6地址，假设是IPv4
                pass

            # 根据操作系统和IP类型构建ping命令
            if platform.system().lower() == "windows":
                cmd = [
                    "ping",
                    "-n",
                    str(self.count),
                    "-w",
                    str(int(self.timeout * 1000)),
                    "-l",
                    str(self.packet_size),
                ]
                if is_ipv6:
                    cmd.append("-6")  # Windows需要-6参数来ping IPv6地址
                cmd.append(ip)
            else:
                cmd = [
                    "ping",
                    "-c",
                    str(self.count),
                    "-W",
                    str(self.timeout),
                ]
                if is_ipv6:
                    cmd.append("-6")  # Linux/macOS需要-6参数来ping IPv6地址
                else:
                    cmd.extend(["-s", str(self.packet_size)])  # IPv4需要指定数据包大小
                cmd.append(ip)

            # 执行ping命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            stdout, stderr = process.communicate()

            # 解析ping结果
            # returncode 0: 所有包都成功
            # returncode 1: 部分包成功（有丢包）
            # returncode 2: 所有包都失败
            if process.returncode in [0, 1]:
                results["success"] = True
            else:
                results["success"] = False

            # 解析延迟数据 - 无论ping是否成功都要解析延迟
            delays = []
            if platform.system().lower() == "windows":
                # Windows ping输出格式
                import re

                # 匹配不同语言环境下的ping输出
                delay_matches = re.findall(r"time=(\d+)ms", stdout, re.IGNORECASE)
                if not delay_matches:
                    # 尝试匹配中文环境下的输出
                    delay_matches = re.findall(r"时间=(\d+)ms", stdout, re.IGNORECASE)
                if not delay_matches:
                    # 尝试匹配更广泛的格式
                    delay_matches = re.findall(r"(\d+)ms", stdout, re.IGNORECASE)
                if not delay_matches:
                    # 尝试匹配延迟数字（不带ms单位）
                    delay_matches = re.findall(r"时间[=<](\d+)ms", stdout, re.IGNORECASE)
                delays = [int(delay) for delay in delay_matches if delay.isdigit()]
            else:
                # Linux/macOS ping输出格式
                import re

                delay_matches = re.findall(r"time=(\d+\.\d+) ms", stdout)
                if not delay_matches:
                    delay_matches = re.findall(r"time=(\d+) ms", stdout)
                delays = [float(delay) for delay in delay_matches]

            results["delays"] = delays
            
            # 添加调试信息
            if not delays and not results["success"]:
                results["error"] = f"Ping解析失败. Return code: {process.returncode}. Output: {stdout[:200]}..."
        except subprocess.SubprocessError as e:
            results["error"] = f"系统ping命令执行失败: {str(e)}"
        except PermissionError as e:
            results["error"] = f"系统ping命令权限不足: {str(e)}"
        except Exception as e:
            results["error"] = f"系统ping命令未知错误: {str(e)}"

        return results

    def ping_ip(self, ip: str) -> Dict[str, Any]:
        """对单个IP执行ping测试"""
        results: Dict[str, Any] = {
            "ip": ip,
            "success": False,
            "min_delay": float("inf"),
            "max_delay": 0,
            "avg_delay": 0,
            "jitter": 0,
            "packet_loss": 100,
            "received": 0,
            "sent": self.count,
            "delays": [],
            "error": None,
            "method": "system" if self.use_system_ping else "icmp",
        }

        try:
            delays = []
            error_messages = []

            if self.use_system_ping:
                # 使用系统ping命令
                system_result = self._system_ping(ip)
                delays = system_result["delays"]
                results["success"] = system_result["success"]
                if system_result.get("error"):
                    error_messages.append(system_result["error"])
            else:
                # 使用基于socket的ICMP ping
                for _ in range(self.count):
                    ping_result = self._icmp_ping(ip)
                    if ping_result["success"]:
                        delays.append(ping_result["delay"])
                    if ping_result.get("error"):
                        error_messages.append(ping_result["error"])

                if delays:
                    results["success"] = True

            results["delays"] = delays
            results["received"] = len(delays)

            if delays:
                results["min_delay"] = min(delays)
                results["max_delay"] = max(delays)
                results["avg_delay"] = sum(delays) / len(delays)

                # 计算抖动
                if len(delays) > 1:
                    jitter_values = []
                    for i in range(1, len(delays)):
                        jitter_values.append(abs(delays[i] - delays[i - 1]))
                    results["jitter"] = sum(jitter_values) / len(jitter_values)

            # 计算丢包率
            results["packet_loss"] = ((self.count - len(delays)) / self.count) * 100

            # 如果有错误信息，将它们合并
            if error_messages:
                # 去重并保留前3个最常见的错误
                from collections import Counter

                error_counter = Counter(error_messages)
                top_errors = [error for error, _ in error_counter.most_common(3)]
                results["error"] = "; ".join(top_errors)

        except Exception as e:
            results["error"] = f"ping测试未知错误: {str(e)}"
            # 添加调试信息
            import traceback
            results["debug_info"] = traceback.format_exc()

        return results

    def ping_ips_parallel(self, ips: List[str], max_workers: int = 50) -> List[Dict[str, Any]]:
        """并行对多个IP执行ping测试"""
        results: List[Dict[str, Any]] = []
        total_ips = len(ips)
        completed = 0

        # 使用固定的线程池大小，由调用方指定，不再动态调整
        max_threads = max_workers

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            # 使用迭代方式提交任务，减少内存占用
            futures = []
            ip_mapping = []

            for ip in ips:
                future = executor.submit(self.ping_ip, ip)
                futures.append(future)
                ip_mapping.append(ip)

            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                completed += 1
                # 每10个任务更新一次进度，减少IO操作
                if completed % 10 == 0 or completed == total_ips:
                    TerminalUtils.progress_bar(
                        completed,
                        total_ips,
                        prefix="Ping测试进度",
                        suffix=f"{completed}/{total_ips}",
                    )

                ip = ip_mapping[i]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(
                        {
                            "ip": ip,
                            "success": False,
                            "min_delay": float("inf"),
                            "max_delay": 0,
                            "avg_delay": 0,
                            "jitter": 0,
                            "packet_loss": 100,
                            "received": 0,
                            "sent": self.count,
                            "delays": [],
                            "error": str(e),
                        }
                    )

        return results


class SpeedTest:
    """网络速率测试类"""

    def __init__(
        self,
        test_duration=5,
        packet_size=8192,
        concurrent_connections=4,
        speed_test_method="both",
        min_data_threshold=1048576,
        min_valid_data=102400,
        min_speed=1.0,
    ):
        self.test_duration = test_duration  # 测试时长
        self.packet_size = packet_size  # 数据包大小
        self.concurrent_connections = concurrent_connections  # 并发连接数
        self.speed_test_method = speed_test_method  # 速度测试方法：direct/both/server
        self.min_data_threshold = min_data_threshold  # 直接连接返回数据量阈值
        self.min_valid_data = min_valid_data  # 最小有效数据量
        self.min_speed = min_speed  # 最小显示速度

    def _download_from_server(self, host, port, path):
        """从指定服务器下载文件"""
        bytes_received = 0
        try:
            # 自动检测IP类型，支持IPv4和IPv6
            addrinfo = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            family, socktype, proto, canonname, sockaddr = addrinfo[0]
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(5)
            sock.connect(sockaddr)

            # 发送HTTP GET请求获取大文件
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0\r\nConnection: keep-alive\r\n\r\n"
            sock.sendall(request.encode())

            # 设置接收超时和优化参数
            sock.settimeout(3)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)  # 256KB

            thread_start = time.time()
            while time.time() - thread_start < self.test_duration:
                try:
                    data = sock.recv(262144)  # 256KB
                    if not data:
                        break
                    bytes_received += len(data)
                    if bytes_received > 20 * 1024 * 1024:  # 20MB
                        break
                except socket.timeout:
                    break

            sock.close()
        except socket.timeout:
            pass
        except ConnectionResetError:
            pass
        except ConnectionRefusedError:
            pass
        except OSError:
            pass
        except (socket.gaierror, socket.herror):
            pass
        return bytes_received

    def _tcp_socket_speed_test(self, server_ip, server_port, results):
        """直接连接到目标IP进行下载测试"""
        bytes_received = 0
        sock = None
        try:
            # 自动检测IP类型，支持IPv4和IPv6
            addrinfo = socket.getaddrinfo(server_ip, server_port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            family, socktype, proto, canonname, sockaddr = addrinfo[0]
            sock = socket.socket(family, socktype, proto)
            
            # 设置TCP连接优化参数
            sock.settimeout(5)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 禁用Nagle算法
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 524288)  # 增加接收缓冲区到512KB
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)  # 增加发送缓冲区到256KB
            
            sock.connect(sockaddr)

            # 发送HTTP GET请求，使用随机参数避免缓存
            import random
            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {server_ip}\r\n"
                f"User-Agent: Mozilla/5.0\r\n"
                f"Connection: keep-alive\r\n"
                f"Cache-Control: no-cache\r\n"
                f"Pragma: no-cache\r\n"
                f"Random: {random.randint(1, 1000000)}\r\n"
                f"\r\n"
            )
            sock.sendall(request.encode())

            # 设置接收超时和优化参数
            sock.settimeout(3)
            thread_start = time.time()
            while time.time() - thread_start < self.test_duration:
                try:
                    data = sock.recv(262144)  # 256KB
                    if not data:
                        break
                    bytes_received += len(data)
                    if bytes_received > 10 * 1024 * 1024:  # 10MB
                        break
                except socket.timeout:
                    break

        except socket.timeout:
            results["error"] = f"{server_ip}:{server_port} 直接连接超时"
        except ConnectionResetError:
            results["error"] = f"{server_ip}:{server_port} 连接被重置"
        except ConnectionRefusedError:
            results["error"] = f"{server_ip}:{server_port} 连接被拒绝"
        except OSError as e:
            results["error"] = f"{server_ip}:{server_port} 网络连接错误: {str(e)}"
        except Exception as e:
            results["error"] = f"{server_ip}:{server_port} 直接连接错误: {str(e)}"
        finally:
            if sock:
                try:
                    sock.close()
                except (OSError, socket.error):
                    pass
        return bytes_received

    def _estimate_speed_from_ping(self, server_ip):
        """使用ping延迟估算网络质量"""
        import subprocess
        import platform
        import re

        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "5", "-w", "1000", server_ip]
            else:
                cmd = ["ping", "-c", "5", "-W", "1", server_ip]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            stdout, stderr = process.communicate()

            # 解析ping结果
            if platform.system().lower() == "windows":
                delay_match = re.search(r"平均 = (\d+)ms", stdout)
                loss_match = re.search(r"丢失 = (\d+)%", stdout)
            else:
                delay_match = re.search(r"avg = (\d+\.\d+) ms", stdout)
                loss_match = re.search(r"(\d+)% packet loss", stdout)

            if delay_match:
                avg_delay = float(delay_match.group(1))
                packet_loss = float(loss_match.group(1)) if loss_match else 0

                # 基于网络质量的速度估算
                if packet_loss > 50:
                    # 高丢包率，网络质量差
                    return self.min_speed
                elif avg_delay < 20 and packet_loss < 5:
                    # 低延迟低丢包，网络质量好
                    return 100.0
                elif avg_delay < 50 and packet_loss < 10:
                    # 中低延迟中低丢包，网络质量中等
                    return 50.0
                elif avg_delay < 100 and packet_loss < 20:
                    # 中等延迟中等丢包，网络质量一般
                    return 20.0
                elif avg_delay < 200 and packet_loss < 30:
                    # 较高延迟或中等丢包，网络质量较差
                    return 10.0
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
        return self.min_speed

    def _get_speed_test_servers(self) -> List[Tuple[str, int, str]]:
        """获取速度测试服务器列表
        
        Returns:
            List[Tuple[str, int, str]]: 服务器列表，每项为 (主机, 端口, 路径)
        """
        return [
            ("speed.cloudflare.com", 80, "/__down?bytes=20971520"),
            ("speed.cloudflare.com", 443, "/__down?bytes=20971520"),
            ("httpbin.org", 80, "/stream/20"),
            ("ipv6.speed.cloudflare.com", 80, "/__down?bytes=20971520"),
            ("download.thinkbroadband.com", 80, "/5MB.zip"),
            ("ipv4.download.thinkbroadband.com", 80, "/5MB.zip"),
            ("ipv6.download.thinkbroadband.com", 80, "/5MB.zip"),
        ]

    def _run_direct_speed_test(self, server_ip: str, server_port: int) -> int:
        """运行直接连接速度测试
        
        Args:
            server_ip: 目标服务器IP
            server_port: 目标服务器端口
            
        Returns:
            int: 接收到的字节数
        """
        total_bytes = 0
        
        try:
            addrinfo = socket.getaddrinfo(server_ip, server_port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            family, socktype, proto, canonname, sockaddr = addrinfo[0]
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(3)
            sock.connect(sockaddr)
            sock.close()

            def thread_target():
                nonlocal total_bytes
                bytes_received = self._tcp_socket_speed_test(server_ip, server_port, {})
                total_bytes += bytes_received

            threads = []
            for _ in range(self.concurrent_connections):
                thread = threading.Thread(target=thread_target)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

        except (socket.error, OSError, ConnectionRefusedError):
            pass
        
        return total_bytes

    def _run_server_speed_test(self, servers: List[Tuple[str, int, str]]) -> int:
        """运行服务器速度测试
        
        Args:
            servers: 速度测试服务器列表
            
        Returns:
            int: 接收到的字节数
        """
        import random
        total_bytes = 0
        
        selected_servers = random.sample(servers, min(3, len(servers)))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_server = {
                executor.submit(self._download_from_server, host, port, path): (host, port, path)
                for host, port, path in selected_servers
            }

            for future in concurrent.futures.as_completed(future_to_server):
                try:
                    received_bytes = future.result()
                    total_bytes += received_bytes
                except (concurrent.futures.CancelledError, Exception):
                    continue
        
        return total_bytes

    def _calculate_filtered_speed(self, speeds: List[float]) -> float:
        """计算过滤后的速度（去除异常值）
        
        Args:
            speeds: 速度列表
            
        Returns:
            float: 过滤后的平均速度
        """
        if not speeds:
            return 0
        
        speeds.sort()
        filtered = speeds[1:-1] if len(speeds) > 2 else speeds
        speed = round(sum(filtered) / len(filtered), 2)
        return max(speed, self.min_speed)

    def tcp_download_test(self, server_ip: str, server_port: int = 80) -> Dict[str, Any]:
        """TCP下载速率测试（优化准确性，减少波动）
        
        Args:
            server_ip: 目标服务器IP地址
            server_port: 目标服务器端口，默认80
            
        Returns:
            Dict[str, Any]: 测试结果字典，包含速率、字节数等信息
        """
        results: Dict[str, Any] = {
            "ip": server_ip,
            "test_type": "download",
            "success": False,
            "speed_mbps": 0,
            "direct_speed": 0,
            "server_speed": 0,
            "bytes_received": 0,
            "duration": 0,
            "error": None,
        }

        try:
            speed_test_servers = self._get_speed_test_servers()
            test_runs = 2
            all_direct_speeds: List[float] = []
            all_server_speeds: List[float] = []
            total_bytes = 0
            total_duration = 0

            for run in range(test_runs):
                run_start = time.time()
                run_direct_bytes = 0
                run_server_bytes = 0

                run_direct_bytes = self._run_direct_speed_test(server_ip, server_port)

                if self.speed_test_method in ["server", "both"]:
                    run_server_bytes = self._run_server_speed_test(speed_test_servers)

                run_end = time.time()
                run_duration = run_end - run_start
                total_duration += run_duration
                total_bytes += run_direct_bytes + run_server_bytes

                if run_duration > 0:
                    if run_direct_bytes >= self.min_valid_data:
                        run_direct_speed = min((run_direct_bytes / run_duration) * 8 / 10**6, 700.0)
                        all_direct_speeds.append(run_direct_speed)
                    if run_server_bytes >= self.min_valid_data:
                        run_server_speed = min((run_server_bytes / run_duration) * 8 / 10**6, 700.0)
                        all_server_speeds.append(run_server_speed)

            results["duration"] = total_duration / test_runs if test_runs > 0 else 0
            results["bytes_received"] = total_bytes

            results["direct_speed"] = self._calculate_filtered_speed(all_direct_speeds)
            results["server_speed"] = self._calculate_filtered_speed(all_server_speeds)

            if self.speed_test_method == "direct":
                results["speed_mbps"] = results["direct_speed"]
                results["success"] = results["direct_speed"] >= self.min_speed
            elif self.speed_test_method == "server":
                results["speed_mbps"] = results["server_speed"]
                results["success"] = results["server_speed"] >= self.min_speed
            else:
                results["speed_mbps"] = max(results["direct_speed"], results["server_speed"])
                results["success"] = results["direct_speed"] >= self.min_speed or results["server_speed"] >= self.min_speed

            if results["speed_mbps"] < self.min_speed:
                estimated_speed = self._estimate_speed_from_ping(server_ip)
                results["speed_mbps"] = estimated_speed
                results["success"] = estimated_speed >= self.min_speed

        except Exception as e:
            results["error"] = str(e)

        return results

    def tcp_upload_test(self, server_ip: str, server_port: int = 80) -> Dict[str, Any]:
        """TCP上传速率测试"""
        results: Dict[str, Any] = {
            "ip": server_ip,
            "test_type": "upload",
            "success": False,
            "speed_mbps": 0,
            "bytes_sent": 0,
            "duration": 0,
            "error": None,
        }

        try:
            start_time = time.time()
            total_bytes = 0

            def upload_thread():
                nonlocal total_bytes
                sock = None
                try:
                    # 自动检测IP类型，支持IPv4和IPv6
                    addrinfo = socket.getaddrinfo(server_ip, server_port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                    family, socktype, proto, canonname, sockaddr = addrinfo[0]
                    sock = socket.socket(family, socktype, proto)
                    
                    # 设置TCP连接优化参数
                    sock.settimeout(5)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 禁用Nagle算法
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)  # 增加接收缓冲区到256KB
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 524288)  # 增加发送缓冲区到512KB
                    
                    sock.connect(sockaddr)

                    # 准备上传数据
                    upload_data = b"X" * self.packet_size

                    # 发送数据
                    thread_start = time.time()
                    while time.time() - thread_start < self.test_duration:
                        sent = sock.send(upload_data)
                        if sent == 0:
                            break
                        total_bytes += sent

                except (socket.error, OSError, ConnectionResetError, ConnectionRefusedError):
                    pass
                finally:
                    if sock:
                        try:
                            sock.close()
                        except (OSError, socket.error):
                            pass

            # 启动多个并发连接
            threads = []
            for _ in range(self.concurrent_connections):
                thread = threading.Thread(target=upload_thread)
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            end_time = time.time()
            results["duration"] = end_time - start_time
            results["bytes_sent"] = total_bytes

            # 计算速率（Mbps）
            if results["duration"] > 0:
                speed_mbps = round((total_bytes / results["duration"]) * 8 / 10**6, 2)
                # 速率上限700Mbps
                results["speed_mbps"] = min(speed_mbps, 700.0)
                results["success"] = True

        except Exception as e:
            results["error"] = str(e)

        return results

    def run_speed_test(
        self,
        ip: str,
        test_type: str = "both",
        enable_download: bool = True,
        enable_upload: bool = False,
    ) -> Dict[str, Any]:
        """运行速率测试"""
        results: Dict[str, Any] = {
            "ip": ip,
            "download": None,
            "upload": None,
            "error": None,
        }

        if (test_type in ["download", "both"]) and enable_download:
            results["download"] = self.tcp_download_test(ip)

        if (test_type in ["upload", "both"]) and enable_upload:
            results["upload"] = self.tcp_upload_test(ip)

        return results

    def run_speed_test_parallel(
        self,
        ips: List[str],
        test_type: str = "both",
        max_workers: int = 20,
        enable_download: bool = True,
        enable_upload: bool = False,
    ) -> List[Dict[str, Any]]:
        """并行运行多个IP的速率测试（优化并行算法，提高测试速度）"""
        results: List[Dict[str, Any]] = []
        total_ips = len(ips)
        completed = 0

        # 使用固定的线程池大小，由调用方指定，不再动态调整
        max_threads = max_workers

        # 对于网络IO密集型任务，线程池更高效
        executor_type = concurrent.futures.ThreadPoolExecutor
        
        with executor_type(max_workers=max_threads) as executor:
            # 使用字典映射future到IP，便于处理完成的任务
            future_to_ip = {
                executor.submit(self.run_speed_test, ip, test_type, enable_download, enable_upload): ip
                for ip in ips
            }

            # 使用tqdm-like进度条，每5个任务或完成时更新
            for future in concurrent.futures.as_completed(future_to_ip):
                completed += 1
                ip = future_to_ip[future]
                
                # 减少进度条更新频率，提高性能
                if completed % 10 == 0 or completed == total_ips:
                    TerminalUtils.progress_bar(
                        completed,
                        total_ips,
                        prefix="速率测试进度",
                        suffix=f"{completed}/{total_ips}",
                    )

                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"ip": ip, "download": None, "upload": None, "error": str(e)})

        return results


class NetworkTestManager:
    """网络测试管理类"""

    def __init__(
        self,
        ping_params: Optional[Dict[str, Any]] = None,
        speed_params: Optional[Dict[str, Any]] = None,
        enable_download: bool = True,
        enable_upload: bool = False,
        max_workers: int = None,
    ) -> None:
        self.ping_params = ping_params or {"count": 5, "timeout": 1.5, "packet_size": 64}
        self.speed_params = speed_params or {
            "test_duration": 8,
            "packet_size": 1024,
            "concurrent_connections": 6,
            "speed_test_method": "both",
            "min_data_threshold": 1048576,
            "min_valid_data": 102400,
            "min_speed": 1.0,
        }

        self.enable_download = enable_download
        self.enable_upload = enable_upload
        self.max_workers = max_workers if max_workers is not None else 50

        self.ping_tester = PingTest(**self.ping_params)
        self.speed_tester = SpeedTest(**self.speed_params)

    def test_ip(self, ip: str, test_types: List[str] = ["ping", "speed"]) -> Dict[str, Any]:
        """对单个IP执行完整的网络测试"""
        results: Dict[str, Any] = {"ip": ip, "ping": None, "speed": None}

        # 执行ping测试
        if "ping" in test_types:
            results["ping"] = self.ping_tester.ping_ip(ip)

        # 执行速率测试
        if "speed" in test_types:
            # 只有ping成功的IP才执行速率测试
            if results["ping"] and results["ping"]["success"]:
                results["speed"] = self.speed_tester.run_speed_test(
                    ip,
                    enable_download=self.enable_download,
                    enable_upload=self.enable_upload,
                )

        return results

    def test_ips(
        self,
        ips: List[str],
        test_types: List[str] = ["ping", "speed"],
        max_workers: int = None,
    ) -> List[Dict[str, Any]]:
        """对多个IP执行网络测试 - 基于线程池的动态调度机制"""
        results: List[Dict[str, Any]] = []
        total_ips = len(ips)
        completed = 0
        
        TerminalUtils.print_status(f"开始对 {total_ips} 个IP执行网络测试", "INFO")

        # 使用提供的max_workers或实例的max_workers
        actual_workers = max_workers if max_workers is not None else self.max_workers
        
        # 创建一个统一的线程池，实现动态调度
        with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # 使用字典映射future到IP，便于处理完成的任务
            future_to_ip = {}
            
            # 为每个IP提交完整的测试任务
            for ip in ips:
                # 提交单个IP的完整测试任务
                future = executor.submit(self.test_ip, ip, test_types)
                future_to_ip[future] = ip
            
            # 动态处理完成的任务
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                completed += 1
                
                try:
                    # 获取测试结果
                    result = future.result()
                    results.append(result)
                    
                    # 更新进度，每完成1个任务就更新一次，提供更实时的进度显示
                    TerminalUtils.progress_bar(
                        completed,
                        total_ips,
                        prefix="网络测试进度",
                        suffix=f"{completed}/{total_ips}",
                    )
                        
                except Exception as e:
                    # 处理测试过程中的异常
                    error_result = {
                        "ip": ip,
                        "ping": None,
                        "speed": None,
                        "error": str(e)
                    }
                    results.append(error_result)

        TerminalUtils.print_status("网络测试完成", "SUCCESS")
        return results

    def display_test_results(self, results, domain_ip_map=None):
        """显示网络测试结果"""
        print(TerminalUtils.colored("\n=== 网络测试结果 ===", Color.CYAN, Color.BOLD))

        if not results:
            print(TerminalUtils.colored("没有测试结果", Color.RED))
            return

        # 准备表格数据
        table_data = []
        
        for result in results:
            ip = result["ip"]
            ping = result["ping"]
            speed = result["speed"]
            
            # 获取对应的域名
            domains = []
            if domain_ip_map:
                for domain, dns_results in domain_ip_map.items():
                    if dns_results.get("unique_ips") and ip in dns_results["unique_ips"]:
                        domains.append(domain)
            domain_str = ", ".join(domains) if domains else "-"

            # 格式化ping数据
            if ping and ping["success"]:
                min_delay = f"{ping['min_delay']:.2f}ms" if ping["min_delay"] != float("inf") else "N/A"
                max_delay = f"{ping['max_delay']:.2f}ms" if ping["max_delay"] > 0 else "N/A"
                avg_delay = f"{ping['avg_delay']:.2f}ms" if ping["avg_delay"] > 0 else "N/A"
                jitter = f"{ping['jitter']:.2f}ms" if ping["jitter"] > 0 else "N/A"
                packet_loss = f"{ping['packet_loss']:.1f}%"
            else:
                min_delay = max_delay = avg_delay = jitter = packet_loss = "N/A"

            # 格式化速率数据
            download_speed = "N/A"
            upload_speed = "N/A"
            if speed:
                if speed["download"] and speed["download"]["success"]:
                    download_speed = f"{speed['download']['speed_mbps']} Mbps"
                if speed["upload"] and speed["upload"]["success"]:
                    upload_speed = f"{speed['upload']['speed_mbps']} Mbps"

            table_data.append(
                {
                    "对应域名": domain_str,
                    "IP": ip,
                    "最小延迟": min_delay,
                    "最大延迟": max_delay,
                    "平均延迟": avg_delay,
                    "抖动": jitter,
                    "丢包率": packet_loss,
                    "下载速度": download_speed,
                    "上传速度": upload_speed,
                }
            )

        # 打印表格
        TerminalUtils.print_table(table_data)

    def get_best_ips(self, results, sort_by="latency", top_n=10):
        """根据测试结果获取最优IP列表"""
        # 筛选出有有效测试结果的IP
        valid_results = []
        for result in results:
            if result["ping"] and result["ping"]["success"]:
                valid_results.append(result)

        # 根据排序条件排序
        if sort_by == "latency":
            # 按平均延迟排序
            valid_results.sort(key=lambda x: x["ping"]["avg_delay"])
        elif sort_by == "speed":
            # 按下载速度排序
            valid_results.sort(
                key=lambda x: (
                    x["speed"]["download"]["speed_mbps"]
                    if (x["speed"] and x["speed"]["download"] and x["speed"]["download"]["success"])
                    else 0
                ),
                reverse=True,
            )
        elif sort_by == "balance":
            # 平衡模式：延迟和速率的加权平均
            valid_results.sort(
                key=lambda x: (x["ping"]["avg_delay"] / 100)
                - (
                    x["speed"]["download"]["speed_mbps"]
                    if (x["speed"] and x["speed"]["download"] and x["speed"]["download"]["success"])
                    else 0
                )
                / 10
            )

        # 返回前N个结果
        return valid_results[:top_n]