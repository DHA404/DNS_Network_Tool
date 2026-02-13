#!/usr/bin/env python3
# DNS Network Tool - Main Entry Point

import os
import logging
import sys
from datetime import datetime
from typing import Dict, List, Callable, Optional
from terminal_utils import TerminalUtils, Color
from config_utils import ConfigManager, ConfigEditor
from log_utils import LogManager
from performance_monitor import performance_monitor

# 导入重构后的模块
from domain_handler import DomainHandler
from dns_service import DNSService
from network_service import NetworkService
from result_processor import ResultProcessor
from report_generator import ReportGenerator
from init_config import check_and_prompt_init, InitConfigManager

# 初始化配置管理
config_manager = ConfigManager()
config = config_manager.get_config()

# 检查并提示初始化（首次运行）
if not check_and_prompt_init(config_manager):
    sys.exit(0)

# 重新加载配置（可能已更新）
config = config_manager.get_config()

# 初始化日志管理
log_manager = LogManager(log_level=getattr(logging, config["log_level"]))
logger = log_manager.get_logger()


class DNSNetworkTool:
    def __init__(self):
        """初始化DNS网络工具"""
        # 从配置文件加载配置
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.dns_servers = self.config["dns_servers"]
        self.test_params = self.config["test_params"]
        self.config_editor = ConfigEditor(self.config_manager)
        
        # 初始化服务模块
        self.domain_handler = DomainHandler()
        self.dns_service = DNSService(self.dns_servers, self.test_params)
        self.network_service = NetworkService(self.test_params)
        self.result_processor = ResultProcessor()
        self.report_generator = ReportGenerator()

    def display_menu(self):
        """显示主菜单"""
        TerminalUtils.clear_screen()
        print(TerminalUtils.colored("=" * 60, Color.BLUE, Color.BOLD))
        print(TerminalUtils.colored("         DNS 解析与网络测试工具", Color.GREEN, Color.BOLD))
        print(TerminalUtils.colored("=" * 60, Color.BLUE, Color.BOLD))
        print("1. 域名输入并测试")
        print("2. 配置 DNS 服务器")
        print("3. 配置测试参数")
        print("4. 启动/关闭开发者模式")
        print("5. 初始化配置向导")
        print("6. 退出程序")
        print(TerminalUtils.colored("=" * 60, Color.BLUE, Color.BOLD))

    def _handle_domain_test(self, is_dev_mode: bool) -> bool:
        """处理域名测试选项
        
        Args:
            is_dev_mode: 是否为开发者模式
            
        Returns:
            bool: 当前的开发者模式状态（未改变）
        """
        logger.info("选择了域名输入并测试")
        if is_dev_mode:
            logger.debug("开始执行域名输入并测试功能")
        performance_monitor.start_section("域名输入并测试")
        self.domain_input_and_test()
        performance_monitor.end_section("域名输入并测试")
        if is_dev_mode:
            logger.debug("域名输入并测试功能执行完毕")
        return is_dev_mode

    def _handle_dns_config(self, is_dev_mode: bool) -> bool:
        """处理DNS配置选项
        
        Args:
            is_dev_mode: 是否为开发者模式
            
        Returns:
            bool: 当前的开发者模式状态（未改变）
        """
        logger.info("选择了配置 DNS 服务器")
        if is_dev_mode:
            logger.debug("开始执行配置 DNS 服务器功能")
        performance_monitor.start_section("配置 DNS 服务器")
        self.configure_dns_servers()
        performance_monitor.end_section("配置 DNS 服务器")
        if is_dev_mode:
            logger.debug("配置 DNS 服务器功能执行完毕")
        return is_dev_mode

    def _handle_test_params(self, is_dev_mode: bool) -> bool:
        """处理测试参数配置选项
        
        Args:
            is_dev_mode: 是否为开发者模式
            
        Returns:
            bool: 当前的开发者模式状态（未改变）
        """
        logger.info("选择了配置测试参数")
        if is_dev_mode:
            logger.debug("开始执行配置测试参数功能")
        performance_monitor.start_section("配置测试参数")
        self.configure_test_params()
        performance_monitor.end_section("配置测试参数")
        if is_dev_mode:
            logger.debug("配置测试参数功能执行完毕")
        return is_dev_mode

    def _handle_dev_mode_toggle(self, is_dev_mode: bool) -> bool:
        """处理开发者模式切换
        
        Args:
            is_dev_mode: 当前开发者模式状态
            
        Returns:
            bool: 切换后的开发者模式状态
        """
        is_dev_mode = not is_dev_mode
        status = "开启" if is_dev_mode else "关闭"
        print(TerminalUtils.colored(f"开发者模式已{status}！", Color.GREEN if is_dev_mode else Color.RED))
        logger.info(f"开发者模式已{status}")
        
        if is_dev_mode:
            log_manager.set_level(logging.DEBUG)
            logger.debug("日志级别已设置为DEBUG")
        else:
            log_manager.set_level(logging.INFO)
            logger.info("日志级别已设置为INFO")
        
        TerminalUtils.pause()
        return is_dev_mode

    def _handle_init_config(self, is_dev_mode: bool) -> bool:
        """处理初始化配置向导
        
        Args:
            is_dev_mode: 是否为开发者模式
            
        Returns:
            bool: 当前的开发者模式状态（未改变）
        """
        logger.info("选择了初始化配置向导")
        if is_dev_mode:
            logger.debug("开始执行初始化配置向导")
        performance_monitor.start_section("初始化配置向导")
        init_manager = InitConfigManager(self.config_manager)
        init_manager.show_init_menu()
        self.config = self.config_manager.get_config()
        self.dns_servers = self.config["dns_servers"]
        self.test_params = self.config["test_params"]
        performance_monitor.end_section("初始化配置向导")
        if is_dev_mode:
            logger.debug("初始化配置向导执行完毕")
        return is_dev_mode

    def _handle_exit(self, is_dev_mode: bool) -> bool:
        """处理退出程序
        
        Args:
            is_dev_mode: 是否为开发者模式
            
        Returns:
            bool: 返回None表示程序应退出
        """
        logger.info("选择了退出程序")
        if is_dev_mode:
            logger.debug("开始执行退出程序功能")
        print(TerminalUtils.colored("感谢使用 DNS 解析与网络测试工具，再见！", Color.GREEN))
        if is_dev_mode:
            logger.debug("停止性能监控并生成报告")
        performance_monitor.stop()
        performance_monitor.print_report()
        if is_dev_mode:
            logger.debug("程序执行完毕，正在退出")
        return None

    def _handle_reset_init(self, is_dev_mode: bool) -> bool:
        """处理重置初始化记录
        
        Args:
            is_dev_mode: 是否为开发者模式
            
        Returns:
            bool: 当前的开发者模式状态（未改变）
        """
        logger.info("选择了重置初始化记录")
        if is_dev_mode:
            logger.debug("开始执行重置初始化记录")
        performance_monitor.start_section("重置初始化记录")
        init_manager = InitConfigManager(self.config_manager)
        init_manager.reset_init_record()
        performance_monitor.end_section("重置初始化记录")
        if is_dev_mode:
            logger.debug("重置初始化记录执行完毕")
        TerminalUtils.pause()
        return is_dev_mode

    def _get_menu_handlers(self) -> Dict[str, Callable[[bool], Optional[bool]]]:
        """获取菜单处理器字典
        
        Returns:
            Dict[str, Callable]: 选项到处理函数的映射
        """
        return {
            "1": self._handle_domain_test,
            "2": self._handle_dns_config,
            "3": self._handle_test_params,
            "4": self._handle_dev_mode_toggle,
            "5": self._handle_init_config,
            "6": self._handle_exit,
            "802": self._handle_reset_init,
        }

    def run(self) -> None:
        """主程序运行逻辑 - 使用字典调度模式"""
        is_dev_mode = False
        
        logger.info("开始执行主程序")
        performance_monitor.start()
        logger.info("性能监控已启动")

        menu_handlers = self._get_menu_handlers()

        while True:
            logger.info("显示主菜单")
            self.display_menu()
            choice = input("请输入选项 (1-6): ")
            logger.info(f"用户输入选项: {choice}")

            handler = menu_handlers.get(choice)
            if handler:
                result = handler(is_dev_mode)
                if result is None:
                    break
                is_dev_mode = result
            else:
                logger.warning(f"无效选项: {choice}")
                print(TerminalUtils.colored("无效选项，请重新输入！", Color.RED))
                TerminalUtils.pause()
                logger.info("等待用户按Enter键继续")

    def domain_input_and_test(self):
        """域名输入并测试功能 - 重构后的简洁版本"""
        # 1. 获取域名输入
        domains, invalid_domains, warning_domains = self.domain_handler.get_domains_from_user()
        
        if not domains:
            return
        
        # 2. 确认是否执行测试
        if not self.domain_handler.confirm_test_execution(domains):
            return
        
        # 3. 获取解析模式
        resolution_mode = self.domain_handler.get_resolution_mode(domains)
        
        if resolution_mode == "comprehensive":
            self._handle_comprehensive_resolution(domains)
        else:
            self._handle_sequential_resolution(domains)
        
        TerminalUtils.pause()
    
    def _handle_comprehensive_resolution(self, domains: List[str]):
        """处理综合解析模式
        
        Args:
            domains: 域名列表
        """
        # 1. DNS解析
        domain_ip_map, all_ips = self.dns_service.comprehensive_resolve(domains)
        
        if not all_ips:
            print(TerminalUtils.colored("\n未解析到任何IP地址，无法执行网络测试！", Color.RED))
            return
        
        # 2. 获取测试类型
        test_types = self.domain_handler.get_test_types()
        
        # 3. 网络测试
        network_results = self.network_service.test_ips(list(all_ips), test_types)
        self.network_service.display_test_results(network_results, domain_ip_map)
        
        # 4. 处理最佳IP和hosts生成
        if self.domain_handler.confirm_best_ip_view():
            self._process_best_ips_and_hosts(domains, network_results, domain_ip_map)
        
        # 5. 导出测试报告
        self.report_generator.export_test_reports(network_results, self.network_service.network_manager)
    
    def _handle_sequential_resolution(self, domains: List[str]):
        """处理依次解析模式
        
        Args:
            domains: 域名列表
        """
        # 1. DNS解析
        domain_ip_map = self.dns_service.sequential_resolve(domains)
        
        # 2. 初始化收集变量
        all_best_ips = []
        all_hosts_content = "# DNS Network Tool 生成的hosts条目\n"
        all_hosts_content += f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        all_hosts_content += f"# 共 {len(domains)} 个域名\n\n"
        
        # 3. 逐个处理域名
        for domain in domains:
            if not self.dns_service.has_valid_ips(domain_ip_map, domain):
                continue
            
            # 获取测试类型
            test_types = self.domain_handler.get_test_types()
            
            # 网络测试
            ips = self.dns_service.get_domain_ips(domain_ip_map, domain)
            network_results = self.network_service.test_ips(ips, test_types)
            self.network_service.display_test_results(network_results, {domain: domain_ip_map[domain]})
            
            # 处理最佳IP
            if self.domain_handler.confirm_best_ip_view():
                sort_by = self.domain_handler.get_sort_preference()
                best_ips = self.network_service.get_best_ips(network_results, sort_by, 10)
                self.network_service.display_test_results(best_ips, {domain: domain_ip_map[domain]})
                
                # 收集最佳IP
                if best_ips:
                    all_best_ips.append(best_ips[0])
                    all_hosts_content += f"{best_ips[0]['ip']} {domain}\n"
        
        # 4. 处理hosts生成
        self._handle_sequential_hosts(domains, domain_ip_map, all_best_ips, all_hosts_content)
    
    def _process_best_ips_and_hosts(self, domains: List[str], network_results: List[Dict], 
                                  domain_ip_map: Dict):
        """处理最佳IP选择和hosts生成
        
        Args:
            domains: 域名列表
            network_results: 网络测试结果
            domain_ip_map: 域名到IP映射字典
        """
        # 获取排序偏好
        sort_by = self.domain_handler.get_sort_preference()
        
        # 获取最佳IP
        best_ips = self.network_service.get_best_ips(network_results, sort_by, 10)
        self.network_service.display_test_results(best_ips, domain_ip_map)
        
        # 生成hosts内容
        print(TerminalUtils.colored("\n=== 生成所有域名的hosts内容 ===", Color.CYAN, Color.BOLD))
        unique_ip_mode = self.domain_handler.confirm_unique_ip_mode()
        
        hosts_content = self.result_processor.generate_hosts_content(
            domains, best_ips, domain_ip_map, unique_ip_mode
        )
        
        # 复制到剪贴板并显示
        self.result_processor.copy_to_clipboard_and_display(hosts_content, "所有域名的hosts内容")
    
    def _handle_sequential_hosts(self, domains: List[str], domain_ip_map: Dict, 
                               all_best_ips: List[Dict], all_hosts_content: str):
        """处理依次解析模式的hosts生成
        
        Args:
            domains: 域名列表
            domain_ip_map: 域名到IP映射字典
            all_best_ips: 所有最佳IP列表
            all_hosts_content: 基础hosts内容
        """
        print(TerminalUtils.colored("\n=== 所有域名处理完成 ===", Color.CYAN, Color.BOLD))
        unique_ip_mode = self.domain_handler.confirm_unique_ip_mode()
        
        if unique_ip_mode:
            # 生成唯一IP模式的hosts内容
            hosts_content = self.result_processor.generate_sequential_hosts_content(
                domains, domain_ip_map, all_best_ips, True
            )
        else:
            # 使用默认模式的内容
            hosts_content = all_hosts_content
        
        # 复制到剪贴板并显示
        title = "唯一IP模式的hosts内容" if unique_ip_mode else "默认模式的hosts内容"
        self.result_processor.copy_to_clipboard_and_display(hosts_content, title)

    def configure_dns_servers(self):
        """配置 DNS 服务器"""
        # 运行DNS服务器配置菜单
        self.config_editor.edit_dns_servers()
        # 重新加载配置
        self.config = self.config_manager.get_config()
        self.dns_servers = self.config["dns_servers"]

    def configure_test_params(self):
        """配置测试参数"""
        self.config_editor.edit_test_params()
        self.config = self.config_manager.get_config()
        self.test_params = self.config["test_params"]


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    tool = DNSNetworkTool()
    tool.run()
