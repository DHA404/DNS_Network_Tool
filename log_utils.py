#!/usr/bin/env python3
# 日志管理工具模块

import logging
import os
import functools
from logging.handlers import RotatingFileHandler
from datetime import datetime


class LogManager:
    """日志管理类"""

    def __init__(self, log_dir=None, log_level=logging.INFO, max_bytes=10 * 1024 * 1024, backup_count=7):
        """
        初始化日志管理器

        Args:
            log_dir: 日志文件目录
            log_level: 日志级别
            max_bytes: 单个日志文件最大大小（字节）
            backup_count: 保留的日志文件数量
        """
        # 如果没有指定日志目录，使用当前文件所在目录下的logs目录
        if log_dir is None:
            # 获取当前文件所在目录的绝对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 将日志目录设置为当前文件所在目录下的logs
            self.log_dir = os.path.join(current_dir, "logs")
        else:
            self.log_dir = log_dir
        
        self.log_level = log_level
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)

        # 清理旧日志文件
        self.cleanup_old_logs()

        # 创建日志记录器
        self.logger = logging.getLogger("DNSNetworkTool")
        self.logger.setLevel(logging.DEBUG)  # 记录所有级别的日志
        self.logger.propagate = False  # 防止日志重复记录

        # 清除现有的处理器
        self.logger.handlers.clear()

        # 创建控制台处理器
        self._create_console_handler()

        # 创建文件处理器
        self._create_file_handler()

    def cleanup_old_logs(self):
        """清理旧日志文件，删除7天前的日志"""
        try:
            # 获取当前时间
            current_time = datetime.now().timestamp()
            # 7天的秒数
            seven_days_seconds = 7 * 24 * 60 * 60
            
            # 获取所有日志文件
            for file in os.listdir(self.log_dir):
                # 检查是否为日志文件
                if file.endswith(".log") or file.endswith(".log."):
                    file_path = os.path.join(self.log_dir, file)
                    if os.path.isfile(file_path):
                        # 获取文件修改时间
                        mtime = os.path.getmtime(file_path)
                        # 计算文件年龄（秒）
                        file_age = current_time - mtime
                        
                        # 如果文件超过7天，删除
                        if file_age > seven_days_seconds:
                            os.remove(file_path)
                            # 避免在logger初始化前调用logger
                            print(f"已删除7天前的日志文件: {file_path}")
        except Exception as e:
            print(f"清理旧日志文件时出错: {str(e)}")

    def _create_console_handler(self):
        """创建控制台日志处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)

        # 控制台日志格式
        console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(console_handler)

    def _create_file_handler(self):
        """创建文件日志处理器"""
        # 生成日志文件名（按日期）
        log_filename = f"{self.log_dir}/{datetime.now().strftime('%Y-%m-%d')}.log"

        # 创建按大小旋转的文件处理器
        file_handler = RotatingFileHandler(log_filename, maxBytes=self.max_bytes, backupCount=self.backup_count, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 文件日志记录所有级别

        # 文件日志格式（更详细）
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(file_handler)

    def get_logger(self):
        """获取日志记录器"""
        return self.logger

    def set_level(self, level):
        """设置日志级别"""
        self.log_level = level
        self.logger.setLevel(logging.DEBUG)  # 日志记录器始终记录DEBUG及以上级别

        # 更新所有处理器的日志级别
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                # 控制台处理器使用指定的日志级别
                handler.setLevel(level)
            elif isinstance(handler, logging.FileHandler):
                # 文件处理器始终记录DEBUG及以上级别，确保所有日志都被写入文件
                handler.setLevel(logging.DEBUG)

    def debug(self, message, *args, **kwargs):
        """记录DEBUG级别的日志"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """记录INFO级别的日志"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """记录WARNING级别的日志"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """记录ERROR级别的日志"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """记录CRITICAL级别的日志"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        """记录异常信息"""
        self.logger.exception(message, *args, **kwargs)

    def log_operation(self, operation, details=None):
        """记录操作日志"""
        if details:
            self.info(f"操作: {operation} | 详情: {details}")
        else:
            self.info(f"操作: {operation}")

    def log_error(self, error_type, error_message, details=None):
        """记录错误日志"""
        if details:
            self.error(f"错误类型: {error_type} | 错误信息: {error_message} | 详情: {details}")
        else:
            self.error(f"错误类型: {error_type} | 错误信息: {error_message}")

    def log_debug(self, module, message):
        """记录调试日志"""
        self.debug(f"模块: {module} | 信息: {message}")


# 创建全局日志管理器实例
global_logger = None


def get_logger():
    """获取全局日志管理器"""
    global global_logger
    if global_logger is None:
        global_logger = LogManager()
    return global_logger


# 日志装饰器
def log_function_call(func):
    """记录函数调用的装饰器"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"调用函数: {func.__name__} | 参数: args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功 | 返回值: {result}")
            return result
        except Exception:
            logger.exception(f"函数 {func.__name__} 执行失败")
            raise

    return wrapper


# 示例用法
if __name__ == "__main__":
    # 初始化日志管理器
    log_manager = LogManager(log_level=logging.DEBUG)

    # 记录不同级别的日志
    log_manager.debug("这是一条DEBUG日志")
    log_manager.info("这是一条INFO日志")
    log_manager.warning("这是一条WARNING日志")
    log_manager.error("这是一条ERROR日志")

    # 记录操作日志
    log_manager.log_operation("DNS解析", "解析域名: www.example.com")

    # 记录错误日志
    log_manager.log_error("网络错误", "连接超时", "连接到8.8.8.8超时")

    # 动态调整日志级别
    log_manager.set_level(logging.WARNING)
    log_manager.debug("这条日志不会被记录，因为日志级别已调整为WARNING")
    log_manager.warning("这条日志会被记录")
