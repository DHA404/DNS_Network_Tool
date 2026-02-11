#!/usr/bin/env python3
# 配置管理工具模块

import json
import os
import socket
import threading
import time
from typing import Dict, Any, List, Tuple, Optional
from terminal_utils import TerminalUtils, Color


class ConfigManager:
    """配置管理类"""

    def __init__(self, config_file: Optional[str] = None) -> None:
        # 使用绝对路径加载配置文件，确保无论程序在哪个目录下运行都能找到
        if config_file is None:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_file: str = os.path.join(current_dir, "config.json")
        else:
            self.config_file: str = config_file

        # 配置模板
        self.config_template: Dict[str, Any] = {
            "dns_servers": [
                "8.8.8.8",  # Google DNS
                "1.1.1.1",  # Cloudflare DNS
                "9.9.9.9",  # Quad9 DNS
                "208.67.222.222",  # OpenDNS
                "4.2.2.1",  # Level3 DNS
            ],
            "test_params": {
                "ping_count": 10,
                "ping_timeout": 2,
                "ping_interval": 0.2,  # ping测试间隔时间（秒）
                "test_duration": 10,
                "packet_size": 1024,
                "concurrent_connections": 4,
                "max_threads": 30,  # 最大线程数
                "dns_threads": 15,  # DNS解析线程数
                "dns_timeout": 5,  # DNS解析超时时间
                
                "top_n_ips": 10,  # 显示的最优IP数量
                "speed_test_type": "tcp",  # 速率测试类型（tcp/udp）
                "enable_ipv6": False,  # 是否启用IPv6测试
                "output_format": "txt",  # 默认输出格式
                "auto_save_results": False,  # 是否自动保存结果
                "enable_download_test": True,  # 是否启用下载速度测试
                "enable_upload_test": False,  # 是否启用上传速度测试
                "speed_test_method": "both",  # 速度测试方法：direct/both/server
                "min_data_threshold": 1048576,  # 直接连接返回数据量阈值
                "min_valid_data": 102400,  # 最小有效数据量
                "min_speed": 1.0,  # 最小显示速度
                "ipv6_support": {
                    "enabled": False,  # 是否启用IPv6支持
                    "dns_resolution": False,  # 是否启用IPv6 DNS解析
                    "ping_test": False,  # 是否启用IPv6 Ping测试
                    "speed_test": False,  # 是否启用IPv6速度测试
                    "mixed_test": False,  # 是否支持IPv4和IPv6混合测试
                    "ipv6_dns_servers": [  # IPv6 DNS服务器列表
                        "2001:4860:4860::8888",  # Google DNS IPv6
                        "2001:4860:4860::8844",  # Google DNS IPv6
                        "2606:4700:4700::1111",  # Cloudflare DNS IPv6
                        "2606:4700:4700::1001",  # Cloudflare DNS IPv6
                    ]
                }
            },
            "log_level": "INFO",
            # HTML界面相关配置
            "web_interface": {
                "enabled": False,  # 是否启用Web界面
                "host": "0.0.0.0",  # Web界面监听地址
                "port": 58090,  # Web界面端口
                "theme": "default",  # Web界面主题
            },
        }

        # 默认配置（与模板相同）
        self.default_config: Dict[str, Any] = self.config_template.copy()

        self.config: Dict[str, Any] = self.load_config()
        # 配置文件最后修改时间，用于热重载
        self._last_modified = os.path.getmtime(self.config_file) if os.path.exists(self.config_file) else 0
        # 热重载标志
        self._enable_hot_reload = False
        # 热重载线程
        self._hot_reload_thread = None
        # 热重载检查间隔（秒）
        self._hot_reload_interval = 5

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # 创建一个默认配置的副本
                merged_config = self.default_config.copy()

                # 处理顶层配置，但跳过嵌套配置，因为我们需要特殊处理
                for key, value in config.items():
                    if key not in ["test_params", "web_interface", "dns_servers"]:
                        merged_config[key] = value

                # 特殊处理嵌套配置，确保保留默认配置中用户配置没有的参数

                # 1. DNS服务器配置
                if "dns_servers" in config:
                    merged_config["dns_servers"] = config["dns_servers"]

                # 2. 测试参数配置
                if "test_params" in config:
                    # 创建一个默认test_params的副本
                    test_params = merged_config["test_params"].copy()
                    # 用用户配置的test_params更新，保留默认配置中用户没有的参数
                    test_params.update(config["test_params"])
                    merged_config["test_params"] = test_params

                # 3. Web界面配置
                if "web_interface" in config:
                    # 创建一个默认web_interface的副本
                    web_interface = merged_config["web_interface"].copy()
                    # 用用户配置的web_interface更新，保留默认配置中用户没有的参数
                    web_interface.update(config["web_interface"])
                    merged_config["web_interface"] = web_interface

                # 验证配置
                is_valid, message = self.validate_config(merged_config)
                if not is_valid:
                    print(TerminalUtils.colored(f"配置文件验证失败: {message}，将使用默认配置", Color.YELLOW))
                    return self.default_config.copy()

                return merged_config
            else:
                # 如果配置文件不存在，返回默认配置
                return self.default_config.copy()
        except Exception as e:
            print(TerminalUtils.colored(f"加载配置文件失败: {str(e)}，将使用默认配置", Color.RED))
            return self.default_config.copy()

    def save_config(self) -> Tuple[bool, str]:
        """保存配置到文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True, f"配置已成功保存到: {self.config_file}"
        except Exception as e:
            return False, f"保存配置失败: {str(e)}"

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> Tuple[bool, str]:
        """更新配置"""
        self.config.update(new_config)
        return self.save_config()

    # DNS服务器配置方法
    def get_dns_servers(self) -> List[str]:
        """获取DNS服务器列表"""
        return self.config["dns_servers"].copy()

    def add_dns_server(self, server: str) -> Tuple[bool, str]:
        """添加DNS服务器"""
        # 验证DNS服务器地址的有效性
        if not self.validate_ip(server):
            return False, f"无效的DNS服务器地址: {server}"
        
        if server not in self.config["dns_servers"]:
            self.config["dns_servers"].append(server)
            return self.save_config()
        return False, f"DNS服务器 {server} 已存在"

    def remove_dns_server(self, index: int) -> Tuple[bool, str]:
        """删除DNS服务器"""
        if 0 <= index < len(self.config["dns_servers"]):
            removed_server = self.config["dns_servers"].pop(index)
            success, message = self.save_config()
            if success:
                return True, f"已成功删除DNS服务器: {removed_server}"
            return success, message
        return False, "无效的DNS服务器索引"

    def reorder_dns_servers(self, new_order: List[int]) -> Tuple[bool, str]:
        """重新排序DNS服务器"""
        if len(new_order) == len(self.config["dns_servers"]) and set(new_order) == set(range(len(self.config["dns_servers"]))):
            # 创建新的DNS服务器列表
            new_servers = [self.config["dns_servers"][i] for i in new_order]
            self.config["dns_servers"] = new_servers
            return self.save_config()
        return False, "无效的排序顺序"

    def set_dns_servers(self, servers: List[str]) -> Tuple[bool, str]:
        """设置DNS服务器列表"""
        self.config["dns_servers"] = servers
        return self.save_config()

    # 测试参数配置方法
    def get_test_params(self) -> Dict[str, Any]:
        """获取测试参数"""
        return self.config["test_params"].copy()

    def update_test_param(self, param_name: str, value: Any) -> Tuple[bool, str]:
        """更新单个测试参数"""
        if param_name in self.config["test_params"]:
            self.config["test_params"][param_name] = value
            return self.save_config()
        return False, f"无效的测试参数: {param_name}"

    def update_test_params(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """更新多个测试参数"""
        for param_name, value in params.items():
            if param_name in self.config["test_params"] or param_name == "ipv6_support":
                if param_name == "ipv6_support" and isinstance(value, dict):
                    # 验证ipv6_support内部参数
                    for ipv6_key, ipv6_value in value.items():
                        if ipv6_key in ["enabled", "dns_resolution", "ping_test", "speed_test", "mixed_test"]:
                            if not isinstance(ipv6_value, bool):
                                return False, f"参数 {ipv6_key} 必须是布尔值"
                        elif ipv6_key == "ipv6_dns_servers":
                            if not isinstance(ipv6_value, list):
                                return False, f"参数 {ipv6_key} 必须是列表类型"
                            # 验证IPv6 DNS服务器格式
                            for dns_server in ipv6_value:
                                if not self._is_valid_ip(dns_server):
                                    return False, f"无效的DNS服务器地址: {dns_server}"
                self.config["test_params"][param_name] = value
        return self.save_config()

    # 日志级别配置方法
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.config["log_level"]

    def set_log_level(self, level: str) -> Tuple[bool, str]:
        """设置日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level.upper() in valid_levels:
            self.config["log_level"] = level.upper()
            return self.save_config()
        return False, f"无效的日志级别: {level}，有效值: {', '.join(valid_levels)}"

    # Web界面配置方法
    def get_web_interface_config(self) -> Dict[str, Any]:
        """获取Web界面配置"""
        return self.config["web_interface"].copy()

    def update_web_interface_config(self, web_config: Dict[str, Any]) -> Tuple[bool, str]:
        """更新Web界面配置"""
        self.config["web_interface"].update(web_config)
        return self.save_config()

    def update_web_interface_param(self, param_name: str, value: Any) -> Tuple[bool, str]:
        """更新单个Web界面参数"""
        if param_name in self.config["web_interface"]:
            self.config["web_interface"][param_name] = value
            return self.save_config()
        return False, f"无效的Web界面参数: {param_name}"

    def display_config(self) -> None:
        """显示当前配置"""
        print(TerminalUtils.colored("\n=== 当前配置 ===", Color.CYAN, Color.BOLD))

        # 显示DNS服务器
        print(TerminalUtils.colored("\nDNS服务器列表:", Color.BLUE, Color.BOLD))
        for i, server in enumerate(self.config["dns_servers"], 1):
            print(f"{i}. {server}")

        # 显示测试参数
        print(TerminalUtils.colored("\n测试参数:", Color.BLUE, Color.BOLD))
        for param, value in self.config["test_params"].items():
            # 格式化参数名称
            param_name = param.replace("_", " ").title()
            print(f"{param_name}: {value}")

        # 显示日志级别
        print(TerminalUtils.colored(f"\n日志级别: {self.config['log_level']}", Color.BLUE, Color.BOLD))

        # 显示Web界面配置
        print(TerminalUtils.colored("\nWeb界面配置:", Color.BLUE, Color.BOLD))
        for param, value in self.config["web_interface"].items():
            # 格式化参数名称
            param_name = param.replace("_", " ").title()
            print(f"{param_name}: {value}")

    def validate_ip(self, ip: str) -> bool:
        """验证IP地址格式（支持IPv4和IPv6，使用跨平台兼容的方法）"""
        try:
            # 首先检查是否是纯数字格式，避免DNS解析
            # 对于IPv4，应该是xxx.xxx.xxx.xxx格式
            # 对于IPv6，应该包含冒号
            
            # 检查是否是有效的IPv4地址格式
            if '.' in ip and ':' not in ip:
                # 尝试分割IP地址
                parts = ip.split('.')
                if len(parts) != 4:
                    return False
                # 检查每个部分是否是0-255之间的整数
                for part in parts:
                    if not part.isdigit() or not (0 <= int(part) <= 255):
                        return False
                return True
            # 检查是否是有效的IPv6地址格式
            elif ':' in ip:
                # 使用socket.getaddrinfo验证IPv6地址
                socket.getaddrinfo(ip, None, socket.AF_INET6, socket.SOCK_STREAM)
                return True
            else:
                # 既不是IPv4也不是IPv6格式
                return False
        except socket.gaierror:
            # 不是有效的IPv6地址
            return False
        except Exception:
            # 其他异常，返回False
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证配置文件的有效性"""
        # 验证DNS服务器格式
        if "dns_servers" in config:
            if not isinstance(config["dns_servers"], list):
                return False, "dns_servers 必须是列表类型"
            for server in config["dns_servers"]:
                if not self.validate_ip(server):
                    return False, f"无效的DNS服务器地址: {server}"
        
        # 验证测试参数
        if "test_params" in config:
            test_params = config["test_params"]
            
            # 验证IPv6支持配置
            if "ipv6_support" in test_params and isinstance(test_params["ipv6_support"], dict):
                ipv6_config = test_params["ipv6_support"]
                # 验证IPv6支持的布尔参数
                for key in ["enabled", "dns_resolution", "ping_test", "speed_test", "mixed_test"]:
                    if key in ipv6_config and not isinstance(ipv6_config[key], bool):
                        return False, f"ipv6_support.{key} 必须是布尔值"
                # 验证IPv6 DNS服务器列表
                if "ipv6_dns_servers" in ipv6_config:
                    if not isinstance(ipv6_config["ipv6_dns_servers"], list):
                        return False, "ipv6_support.ipv6_dns_servers 必须是列表类型"
                    for server in ipv6_config["ipv6_dns_servers"]:
                        if not self.validate_ip(server):
                            return False, f"无效的IPv6 DNS服务器地址: {server}"
        
        # 验证日志级别
        if "log_level" in config:
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config["log_level"].upper() not in valid_log_levels:
                return False, f"无效的日志级别: {config['log_level']}，有效值: {', '.join(valid_log_levels)}"
        
        # 验证Web界面配置
        if "web_interface" in config:
            web_config = config["web_interface"]
            if "enabled" in web_config and not isinstance(web_config["enabled"], bool):
                return False, "web_interface.enabled 必须是布尔值"
            if "port" in web_config:
                if not isinstance(web_config["port"], int) or not (1024 <= web_config["port"] <= 65535):
                    return False, "web_interface.port 必须是1024-65535之间的整数"
        
        return True, "配置有效"
    
    def enable_hot_reload(self, interval: int = 5) -> None:
        """启用配置文件热重载"""
        self._enable_hot_reload = True
        self._hot_reload_interval = interval
        
        def hot_reload_loop():
            """热重载循环"""
            while self._enable_hot_reload:
                try:
                    if os.path.exists(self.config_file):
                        current_mtime = os.path.getmtime(self.config_file)
                        if current_mtime != self._last_modified:
                            # 配置文件已修改，重新加载
                            new_config = self.load_config()
                            # 验证新配置
                            is_valid, message = self.validate_config(new_config)
                            if is_valid:
                                self.config = new_config
                                self._last_modified = current_mtime
                                print(TerminalUtils.colored("配置文件已自动重新加载", Color.GREEN))
                            else:
                                print(TerminalUtils.colored(f"配置文件无效，热重载失败: {message}", Color.RED))
                    time.sleep(self._hot_reload_interval)
                except Exception as e:
                    print(TerminalUtils.colored(f"配置热重载出错: {str(e)}", Color.RED))
                    time.sleep(self._hot_reload_interval)
        
        # 启动热重载线程
        self._hot_reload_thread = threading.Thread(target=hot_reload_loop, daemon=True)
        self._hot_reload_thread.start()
    
    def disable_hot_reload(self) -> None:
        """禁用配置文件热重载"""
        self._enable_hot_reload = False
        if self._hot_reload_thread:
            self._hot_reload_thread.join(timeout=5)
            self._hot_reload_thread = None
    
    def get_config_template(self) -> Dict[str, Any]:
        """获取配置模板"""
        return self.config_template.copy()


class ConfigEditor:
    """配置编辑器类，提供交互式配置编辑功能"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager: ConfigManager = config_manager

    def edit_dns_servers(self) -> None:
        """编辑DNS服务器列表"""
        while True:
            print(TerminalUtils.colored("\n=== DNS服务器配置 ===", Color.CYAN, Color.BOLD))
            servers = self.config_manager.get_dns_servers()

            for i, server in enumerate(servers, 1):
                print(f"{i}. {server}")

            print("\n操作选项:")
            print("1. 添加DNS服务器 - 添加新的DNS服务器IP地址到测试列表")
            print("2. 删除DNS服务器 - 从测试列表中删除指定的DNS服务器")
            print("3. 保存并返回 - 保存当前配置并返回上一级菜单")

            choice = input("请输入选项 (1-3): ")

            if choice == "1":
                # 添加DNS服务器
                new_server = input("请输入新的DNS服务器IP: ")
                if self.config_manager.validate_ip(new_server):
                    success, message = self.config_manager.add_dns_server(new_server)
                    print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                else:
                    print(TerminalUtils.colored("无效的IP地址格式", Color.RED))

            elif choice == "2":
                # 删除DNS服务器
                if len(servers) == 0:
                    print(TerminalUtils.colored("没有可删除的DNS服务器", Color.YELLOW))
                    continue

                try:
                    index = int(input(f"请输入要删除的DNS服务器编号 (1-{len(servers)}): ")) - 1
                    success, message = self.config_manager.remove_dns_server(index)
                    print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "3":
                # 保存并返回
                break

            else:
                print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))

    def edit_test_params(self) -> None:
        """编辑测试参数"""
        while True:
            print(TerminalUtils.colored("\n=== 测试参数配置 ===", Color.CYAN, Color.BOLD))
            params = self.config_manager.get_test_params()

            for param, value in params.items():
                param_name = param.replace("_", " ").title()
                print(f"{param_name}: {value}")

            print("\n操作选项:")
            print("1. 修改ping测试次数 - 每个IP执行的ping测试包数量，影响延迟计算准确性")
            print("2. 修改ping超时时间 - 每个ping包的超时等待时间，单位：秒")
            print("3. 修改ping测试间隔 - 连续ping包之间的等待时间，单位：秒")
            print("4. 修改速率测试时长 - 每个IP执行速率测试的持续时间，单位：秒")
            print("5. 修改数据包大小 - 网络测试使用的数据包大小，单位：字节")
            print("6. 修改并发连接数 - 速率测试时使用的并发连接数量")
            print("7. 修改最大线程数 - 并行处理IP测试的最大线程数量")
            print("8. 修改DNS解析超时时间 - 域名解析的最大等待时间，单位：秒")
            print("9. 修改显示的最优IP数量 - 测试结果中显示的最优IP数量")
            print("10. 修改速率测试类型 - 选择TCP或UDP协议进行速率测试")
            print("11. 启用/禁用IPv6测试 - 是否对IPv6地址进行测试")
            print("12. 修改默认输出格式 - 设置测试结果的默认保存格式（txt/csv）")
            print("13. 修改DNS解析线程数 - 同时解析多个域名的最大线程数量")
            print("14. 启用/禁用自动保存结果 - 是否自动保存测试结果到文件")
            print("15. 启用/禁用下载速度测试 - 是否对IP执行下载速度测试")
            print("16. 启用/禁用上传速度测试 - 是否对IP执行上传速度测试")
            print("19. 保存并返回 - 保存当前配置并返回主菜单")

            choice = input("请输入选项 (1-17): ")

            if choice == "1":
                # 修改ping测试次数
                try:
                    current_value = params.get("ping_count", 10)
                    value = int(input(f"当前ping测试次数: {current_value}\n请输入新的ping测试次数 (1-500): "))
                    if 1 <= value <= 500:
                        success, message = self.config_manager.update_test_param("ping_count", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("ping测试次数必须在1-100之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "2":
                # 修改ping超时时间
                try:
                    current_value = params.get("ping_timeout", 2)
                    value = float(input(f"当前ping超时时间: {current_value}秒\n请输入新的ping超时时间 (0.1-30): "))
                    if 0.1 <= value <= 30:
                        success, message = self.config_manager.update_test_param("ping_timeout", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("ping超时时间必须在0.1-10秒之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "3":
                # 修改ping测试间隔
                try:
                    current_value = params.get("ping_interval", 0.5)
                    value = float(input(f"当前ping测试间隔: {current_value}秒\n请输入新的ping测试间隔时间 (0.01-10): "))
                    if 0.01 <= value <= 10:
                        success, message = self.config_manager.update_test_param("ping_interval", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("ping测试间隔必须在0.1-5秒之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "4":
                # 修改速率测试时长
                try:
                    current_value = params.get("test_duration", 10)
                    value = int(input(f"当前速率测试时长: {current_value}秒\n请输入新的速率测试时长 (1-600): "))
                    if 1 <= value <= 600:
                        success, message = self.config_manager.update_test_param("test_duration", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("速率测试时长必须在1-300秒之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "5":
                # 修改数据包大小
                try:
                    current_value = params.get("packet_size", 1024)
                    value = int(input(f"当前数据包大小: {current_value}字节\n请输入新的数据包大小 (64-65535): "))
                    if 64 <= value <= 65535:
                        success, message = self.config_manager.update_test_param("packet_size", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("数据包大小必须在64-65536字节之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "6":
                # 修改并发连接数
                try:
                    current_value = params.get("concurrent_connections", 4)
                    value = int(input(f"当前并发连接数: {current_value}\n请输入新的并发连接数 (1-500): "))
                    if 1 <= value <= 500:
                        success, message = self.config_manager.update_test_param("concurrent_connections", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("并发连接数必须在1-100之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "7":
                # 修改最大线程数
                try:
                    current_value = params.get("max_threads", 30)
                    value = int(input(f"当前最大线程数: {current_value}\n请输入新的最大线程数 (5-500): "))
                    if 5 <= value <= 500:
                        success, message = self.config_manager.update_test_param("max_threads", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("最大线程数必须在5-200之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "8":
                # 修改DNS解析超时时间
                try:
                    current_value = params.get("dns_timeout", 5)
                    value = float(input(f"当前DNS解析超时时间: {current_value}秒\n请输入新的DNS解析超时时间 (1-60): "))
                    if 1 <= value <= 60:
                        success, message = self.config_manager.update_test_param("dns_timeout", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("DNS解析超时时间必须在1-30秒之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "9":
                # 修改显示的最优IP数量
                try:
                    current_value = params.get("top_n_ips", 10)
                    value = int(input(f"当前显示的最优IP数量: {current_value}\n请输入新的显示数量 (1-100): "))
                    if 1 <= value <= 100:
                        success, message = self.config_manager.update_test_param("top_n_ips", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("显示数量必须在1-50之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "10":
                # 修改速率测试类型
                current_value = params.get("speed_test_type", "tcp")
                print(f"\n当前速率测试类型: {current_value.upper()}")
                print("选择速率测试类型:")
                print("1. TCP")
                print("2. UDP")
                type_choice = input("请输入选项 (1-2): ")
                if type_choice == "1":
                    speed_type = "tcp"
                elif type_choice == "2":
                    speed_type = "udp"
                else:
                    print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))
                    continue
                success, message = self.config_manager.update_test_param("speed_test_type", speed_type)
                print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))

            elif choice == "11":
                # 启用/禁用IPv6测试
                current_value = params.get("enable_ipv6", False)
                new_value = not current_value
                success, message = self.config_manager.update_test_param("enable_ipv6", new_value)
                print(
                    TerminalUtils.colored(f"IPv6测试已{'启用' if new_value else '禁用'}", Color.GREEN if success else Color.RED)
                )

            elif choice == "12":
                # 修改默认输出格式
                current_value = params.get("output_format", "txt")
                print(f"\n当前默认输出格式: {current_value}")
                print("选择默认输出格式:")
                print("1. 纯文本 (txt)")
                print("2. CSV格式 (csv)")
                format_choice = input("请输入选项 (1-2): ")
                if format_choice == "1":
                    output_format = "txt"
                elif format_choice == "2":
                    output_format = "csv"
                else:
                    print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))
                    continue
                success, message = self.config_manager.update_test_param("output_format", output_format)
                print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))

            elif choice == "13":
                # 修改DNS解析线程数
                try:
                    current_value = params.get("dns_threads", 10)
                    value = int(input(f"当前DNS解析线程数: {current_value}\n请输入新的DNS解析线程数 (1-200): "))
                    if 1 <= value <= 200:
                        success, message = self.config_manager.update_test_param("dns_threads", value)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("DNS解析线程数必须在1-100之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))
            elif choice == "14":
                # 启用/禁用自动保存结果
                current_value = params.get("auto_save_results", False)
                new_value = not current_value
                success, message = self.config_manager.update_test_param("auto_save_results", new_value)
                print(
                    TerminalUtils.colored(
                        f"自动保存结果已{'启用' if new_value else '禁用'}", Color.GREEN if success else Color.RED
                    )
                )
            elif choice == "15":
                # 启用/禁用下载速度测试
                current_value = params.get("enable_download_test", True)
                new_value = not current_value
                success, message = self.config_manager.update_test_param("enable_download_test", new_value)
                print(
                    TerminalUtils.colored(
                        f"下载速度测试已{'启用' if new_value else '禁用'}", Color.GREEN if success else Color.RED
                    )
                )
            elif choice == "16":
                # 启用/禁用上传速度测试
                current_value = params.get("enable_upload_test", False)
                new_value = not current_value
                success, message = self.config_manager.update_test_param("enable_upload_test", new_value)
                print(
                    TerminalUtils.colored(
                        f"上传速度测试已{'启用' if new_value else '禁用'}", Color.GREEN if success else Color.RED
                    )
                )
            elif choice == "17":
                # 保存并返回
                break

            else:
                print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))

    def edit_web_interface(self) -> None:
        """编辑Web界面配置"""
        while True:
            print(TerminalUtils.colored("\n=== Web界面配置 ===", Color.CYAN, Color.BOLD))
            web_config = self.config_manager.get_web_interface_config()

            for param, value in web_config.items():
                param_name = param.replace("_", " ").title()
                print(f"{param_name}: {value}")

            print("\n操作选项:")
            print("1. 启用/禁用Web界面 - 开启或关闭基于浏览器的图形化操作界面")
            print("2. 修改Web界面监听地址 - 设置Web界面监听的IP地址")
            print("3. 修改Web界面端口 - 设置Web界面访问的端口号")
            print("4. 修改Web界面主题 - 切换Web界面的显示主题（默认/深色/浅色）")
            print("5. 保存并返回 - 保存当前配置并返回上一级菜单")

            choice = input("请输入选项 (1-5): ")

            if choice == "1":
                # 启用/禁用Web界面
                current_value = web_config.get("enabled", False)
                new_value = not current_value
                success, message = self.config_manager.update_web_interface_param("enabled", new_value)
                print(TerminalUtils.colored(f"Web界面已{'启用' if new_value else '禁用'}", Color.GREEN if success else Color.RED))

            elif choice == "2":
                # 修改Web界面监听地址
                host = input("请输入Web界面监听地址 (默认: 0.0.0.0): ") or "0.0.0.0"
                success, message = self.config_manager.update_web_interface_param("host", host)
                print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))

            elif choice == "3":
                # 修改Web界面端口
                try:
                    port = int(input("请输入Web界面端口 (1024-65535): "))
                    if 1024 <= port <= 65535:
                        success, message = self.config_manager.update_web_interface_param("port", port)
                        print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))
                    else:
                        print(TerminalUtils.colored("Web界面端口必须在1024-65535之间", Color.RED))
                except ValueError:
                    print(TerminalUtils.colored("无效的输入，请输入数字", Color.RED))

            elif choice == "4":
                # 修改Web界面主题
                print("\n选择Web界面主题:")
                print("1. 默认主题 (default)")
                print("2. 深色主题 (dark)")
                print("3. 浅色主题 (light)")
                theme_choice = input("请输入选项 (1-3): ")
                if theme_choice == "1":
                    theme = "default"
                elif theme_choice == "2":
                    theme = "dark"
                elif theme_choice == "3":
                    theme = "light"
                else:
                    print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))
                    continue
                success, message = self.config_manager.update_web_interface_param("theme", theme)
                print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))

            elif choice == "5":
                # 保存并返回
                break

            else:
                print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))

    def run_config_menu(self) -> None:
        """运行配置菜单"""
        while True:
            print(TerminalUtils.colored("\n=== 配置管理 ===", Color.CYAN, Color.BOLD))
            print("1. 查看当前配置 - 显示所有配置项的当前值")
            print("2. 配置DNS服务器 - 添加、删除或修改用于测试的DNS服务器列表")
            print("3. 配置测试参数 - 调整ping、速率测试等网络测试相关参数")
            print("4. 配置Web界面 - 设置基于浏览器的图形化操作界面参数")
            print("5. 恢复默认配置 - 将所有配置项恢复为初始默认值")
            print("6. 返回主菜单 - 保存当前配置并返回程序主菜单")

            choice = input("请输入选项 (1-6): ")

            if choice == "1":
                # 查看当前配置
                self.config_manager.display_config()
                TerminalUtils.pause()

            elif choice == "2":
                # 配置DNS服务器
                self.edit_dns_servers()

            elif choice == "3":
                # 配置测试参数
                self.edit_test_params()

            elif choice == "4":
                # 配置Web界面
                self.edit_web_interface()

            elif choice == "5":
                # 恢复默认配置
                confirm = input("确定要恢复默认配置吗？ (y/n): ")
                if confirm.lower() == "y":
                    self.config_manager.config = self.config_manager.default_config.copy()
                    success, message = self.config_manager.save_config()
                    print(TerminalUtils.colored(message, Color.GREEN if success else Color.RED))

            elif choice == "6":
                # 返回主菜单
                break

            else:
                print(TerminalUtils.colored("无效选项，请重新输入", Color.RED))
