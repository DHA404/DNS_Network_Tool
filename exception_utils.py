#!/usr/bin/env python3
# 异常处理工具模块

import logging
import traceback
import time
from typing import Optional, Dict, Any


class DNSNetworkToolException(Exception):
    """DNS Network Tool 自定义异常基类
    
    所有自定义异常的父类，提供统一的错误信息格式。
    
    Attributes:
        message: 错误描述信息
        error_code: 错误代码
        details: 额外的错误详情字典
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """将异常信息转换为字典格式
        
        Returns:
            Dict[str, Any]: 包含错误信息的字典
        """
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class DNSResolveException(DNSNetworkToolException):
    """DNS解析异常
    
    在进行DNS域名解析时发生的错误。
    
    Args:
        message: 错误描述信息
        domain: 正在解析的域名
        dns_server: 使用的DNS服务器地址
        record_type: DNS记录类型（如A、AAAA、MX等）
    """
    
    def __init__(self, message: str, domain: Optional[str] = None, dns_server: Optional[str] = None, record_type: Optional[str] = None):
        details = {}
        if domain:
            details["domain"] = domain
        if dns_server:
            details["dns_server"] = dns_server
        if record_type:
            details["record_type"] = record_type
        super().__init__(message, "DNS_RESOLVE_ERROR", details)


class TimeoutException(DNSNetworkToolException):
    """超时异常
    
    操作超过设定的超时时间而失败。
    
    Args:
        message: 错误描述信息
        operation: 超时的操作名称
        timeout_seconds: 设定的超时时间（秒）
        elapsed_seconds: 实际耗时（秒）
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, timeout_seconds: Optional[float] = None, elapsed_seconds: Optional[float] = None):
        details = {}
        if operation:
            details["operation"] = operation
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if elapsed_seconds:
            details["elapsed_seconds"] = elapsed_seconds
        super().__init__(message, "TIMEOUT_ERROR", details)


class ConnectionException(DNSNetworkToolException):
    """连接异常
    
    网络连接建立失败或被中断。
    
    Args:
        message: 错误描述信息
        host: 连接的目标主机
        port: 连接的目标端口
        connection_type: 连接类型（如TCP、UDP、ICMP）
    """
    
    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None, connection_type: Optional[str] = None):
        details = {}
        if host:
            details["host"] = host
        if port:
            details["port"] = port
        if connection_type:
            details["connection_type"] = connection_type
        super().__init__(message, "CONNECTION_ERROR", details)


class ValidationException(DNSNetworkToolException):
    """验证异常
    
    输入参数验证失败。
    
    Args:
        message: 错误描述信息
        field: 验证失败的字段名称
        value: 验证失败的值
        validation_rule: 验证规则描述
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, validation_rule: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if validation_rule:
            details["validation_rule"] = validation_rule
        super().__init__(message, "VALIDATION_ERROR", details)


class SecurityException(DNSNetworkToolException):
    """安全异常
    
    检测到安全相关的问题或威胁。
    
    Args:
        message: 错误描述信息
        security_level: 安全级别（如low、medium、high、critical）
        threat_type: 威胁类型（如injection、spoofing、pollution）
    """
    
    def __init__(self, message: str, security_level: Optional[str] = None, threat_type: Optional[str] = None):
        details = {}
        if security_level:
            details["security_level"] = security_level
        if threat_type:
            details["threat_type"] = threat_type
        super().__init__(message, "SECURITY_ERROR", details)


class FileOperationException(DNSNetworkToolException):
    """文件操作异常
    
    文件读写操作失败。
    
    Args:
        message: 错误描述信息
        file_path: 操作的文件路径
        operation: 文件操作类型（如read、write、delete）
    """
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        super().__init__(message, "FILE_OPERATION_ERROR", details)


class RateLimitException(DNSNetworkToolException):
    """速率限制异常
    
    请求频率超过限制。
    
    Args:
        message: 错误描述信息
        rate_limit: 速率限制值
        current_rate: 当前请求频率
        retry_after: 建议重试等待时间（秒）
    """
    
    def __init__(self, message: str, rate_limit: Optional[float] = None, current_rate: Optional[float] = None, retry_after: Optional[float] = None):
        details = {}
        if rate_limit:
            details["rate_limit"] = rate_limit
        if current_rate:
            details["current_rate"] = current_rate
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class PerformanceException(DNSNetworkToolException):
    """性能异常
    
    系统性能不满足要求。
    
    Args:
        message: 错误描述信息
        metric: 性能指标名称（如response_time、throughput、latency）
        expected_value: 期望的性能值
        actual_value: 实际测量的性能值
    """
    
    def __init__(self, message: str, metric: Optional[str] = None, expected_value: Optional[float] = None, actual_value: Optional[float] = None):
        details = {}
        if metric:
            details["metric"] = metric
        if expected_value:
            details["expected_value"] = expected_value
        if actual_value:
            details["actual_value"] = actual_value
        super().__init__(message, "PERFORMANCE_ERROR", details)


class PlatformException(DNSNetworkToolException):
    """平台异常
    
    平台特定的功能不支持或失败。
    
    Args:
        message: 错误描述信息
        platform: 平台标识（如windows、linux、darwin）
        operation: 尝试的操作
    """
    
    def __init__(self, message: str, platform: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if platform:
            details["platform"] = platform
        if operation:
            details["operation"] = operation
        super().__init__(message, "PLATFORM_ERROR", details)


class NetworkTestException(DNSNetworkToolException):
    """网络测试异常
    
    网络测试操作失败。
    
    Args:
        message: 错误描述信息
        ip: 测试的目标IP地址
        test_type: 测试类型（如ping、tcp、udp、speed）
    """
    
    def __init__(self, message: str, ip: Optional[str] = None, test_type: Optional[str] = None):
        details = {}
        if ip:
            details["ip"] = ip
        if test_type:
            details["test_type"] = test_type
        super().__init__(message, "NETWORK_TEST_ERROR", details)


class ConfigException(DNSNetworkToolException):
    """配置异常
    
    配置加载或验证失败。
    
    Args:
        message: 错误描述信息
        config_key: 配置项键名
        config_source: 配置来源（如file、environment、default）
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_source: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_source:
            details["config_source"] = config_source
        super().__init__(message, "CONFIG_ERROR", details)





class ExceptionHandler:
    """统一异常处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_count = 0
        self.retry_counts = {}
    
    def handle_exception(self, 
                        exception: Exception, 
                        context: Optional[str] = None,
                        retry_count: int = 0,
                        max_retries: int = 3) -> Dict[str, Any]:
        """统一处理异常"""
        self.error_count += 1
        
        # 获取异常信息
        if isinstance(exception, DNSNetworkToolException):
            error_info = exception.to_dict()
        else:
            error_info = {
                "error": True,
                "error_code": exception.__class__.__name__.upper(),
                "message": str(exception),
                "details": {}
            }
        
        # 添加上下文信息
        if context:
            error_info["context"] = context
        
        # 记录详细错误信息
        self.logger.error(f"异常发生: {exception}", exc_info=True)
        self.logger.error(f"上下文: {context}")
        self.logger.error(f"错误信息: {error_info}")
        
        # 检查是否需要重试
        if self._should_retry(exception, retry_count, max_retries):
            error_info["retryable"] = True
            error_info["retry_count"] = retry_count
            error_info["max_retries"] = max_retries
        else:
            error_info["retryable"] = False
        
        return error_info
    
    def _should_retry(self, exception: Exception, retry_count: int, max_retries: int) -> bool:
        """判断是否应该重试"""
        # 网络相关错误可以重试
        if isinstance(exception, (ConnectionError, TimeoutError, OSError, ConnectionResetError, ConnectionRefusedError)):
            return retry_count < max_retries
        
        # DNS解析错误可以重试
        if isinstance(exception, DNSResolveException) and any(keyword in str(exception).lower() for keyword in ["timeout", "connection", "network"]):
            return retry_count < max_retries
        
        # 网络测试错误可以重试
        if isinstance(exception, NetworkTestException) and any(keyword in str(exception).lower() for keyword in ["timeout", "connection", "network"]):
            return retry_count < max_retries
        
        # 其他类型错误不重试
        return False
    
    def retry_with_backoff(self, func, *args, max_retries: int = 3, backoff_factor: float = 1.0, **kwargs):
        """带退避的重试机制"""
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    raise e
                
                # 计算等待时间（指数退避）
                wait_time = backoff_factor * (2 ** attempt)
                self.logger.warning(f"尝试 {attempt + 1} 失败，{wait_time}秒后重试: {e}")
                
                import time
                time.sleep(wait_time)
        
        # 如果所有重试都失败，抛出最后一个异常
        raise e
    
    def create_error_response(self, exception: Exception, status_code: int = 500) -> tuple:
        """创建HTTP错误响应"""
        error_info = self.handle_exception(exception)
        return error_info, status_code
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "total_errors": self.error_count,
            "retry_counts": self.retry_counts
        }


# 全局异常处理器实例
global_exception_handler = ExceptionHandler()


def safe_execute(func, *args, context: Optional[str] = None, logger: Optional[logging.Logger] = None, **kwargs):
    """安全执行函数，捕获所有异常并统一处理"""
    handler = ExceptionHandler(logger)
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = handler.handle_exception(e, context)
        # 可以根据需要返回错误信息或重新抛出异常
        raise DNSNetworkToolException(f"{context}: {str(e)}") from e


def format_exception_message(exception: Exception, context: Optional[str] = None) -> str:
    """格式化异常消息"""
    if context:
        return f"[{context}] {type(exception).__name__}: {str(exception)}"
    else:
        return f"{type(exception).__name__}: {str(exception)}"


def log_exception_details(exception: Exception, logger: logging.Logger, context: Optional[str] = None):
    """记录异常详细信息"""
    logger.error("=" * 60)
    logger.error("异常详情")
    logger.error("=" * 60)
    logger.error(f"异常类型: {type(exception).__name__}")
    logger.error(f"异常消息: {str(exception)}")
    if context:
        logger.error(f"发生上下文: {context}")
    logger.error("完整堆栈:")
    logger.error(traceback.format_exc())
    logger.error("=" * 60)
