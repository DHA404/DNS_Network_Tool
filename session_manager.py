#!/usr/bin/env python3
# HTTP会话管理模块 - 优化版本

import requests
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SessionManager:
    """HTTP会话管理器，提供连接池和重试机制 - 优化版本"""

    _instance: Optional['SessionManager'] = None

    def __init__(self) -> None:
        self._session: Optional[requests.Session] = None
        self._init_session()

    def _init_session(self) -> None:
        """初始化请求会话，配置连接池和重试策略 - 优化配置"""
        self._session = requests.Session()

        retry_strategy = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=50,
            pool_maxsize=200
        )

        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Keep-Alive": "timeout=30, max=100"
        })

    def get_session(self) -> requests.Session:
        """获取当前会话实例"""
        if self._session is None:
            self._init_session()
        return self._session

    def close(self) -> None:
        """关闭会话"""
        if self._session:
            self._session.close()
            self._session = None

    def __del__(self) -> None:
        self.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_session_manager() -> SessionManager:
    """获取会话管理器单例"""
    if SessionManager._instance is None:
        SessionManager._instance = SessionManager()
    return SessionManager._instance
