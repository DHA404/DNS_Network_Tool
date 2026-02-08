#!/usr/bin/env python3
# 性能监控模块

import time
from collections import defaultdict
from typing import Dict, Any, Optional
from log_utils import get_logger


class PerformanceMonitor:
    """性能监控类"""

    def __init__(self) -> None:
        self.logger = get_logger()
        self._is_running = False
        self._sections: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "start_time": None,
            "end_time": None,
            "executions": 0,
            "total_time": 0,
            "min_time": float("inf"),
            "max_time": 0,
        })
        self._current_section: Optional[str] = None
        self._current_section_start: float = 0

    def start(self) -> None:
        """启动性能监控"""
        self._is_running = True
        self.logger.info("性能监控已启动")

    def stop(self) -> None:
        """停止性能监控"""
        self._is_running = False
        self.logger.info("性能监控已停止")

    def start_section(self, section_name: str) -> None:
        """开始监控某个部分"""
        if not self._is_running:
            return

        self._current_section = section_name
        self._current_section_start = time.time()
        self._sections[section_name]["start_time"] = self._current_section_start

    def end_section(self, section_name: str) -> None:
        """结束监控某个部分"""
        if not self._is_running or self._current_section != section_name:
            return

        end_time = time.time()
        exec_time = end_time - self._current_section_start

        section = self._sections[section_name]
        section["end_time"] = end_time
        section["executions"] += 1
        section["total_time"] += exec_time
        section["min_time"] = min(section["min_time"], exec_time)
        section["max_time"] = max(section["max_time"], exec_time)

        self._current_section = None
        self._current_section_start = 0

    def print_report(self) -> None:
        """打印性能报告"""
        if not self._sections:
            return

        print("\n" + "=" * 60)
        print("性能监控报告")
        print("=" * 60)

        for section_name, data in self._sections.items():
            if data["executions"] > 0:
                avg_time = data["total_time"] / data["executions"]
                print(f"\n{section_name}:")
                print(f"  执行次数: {data['executions']}")
                print(f"  总耗时: {data['total_time']:.4f}秒")
                print(f"  平均耗时: {avg_time:.4f}秒")
                print(f"  最小耗时: {data['min_time']:.4f}秒")
                print(f"  最大耗时: {data['max_time']:.4f}秒")

        print("\n" + "=" * 60)

    def get_report(self) -> Dict[str, Dict[str, Any]]:
        """获取性能报告数据"""
        report = {}
        for section_name, data in self._sections.items():
            if data["executions"] > 0:
                report[section_name] = {
                    "executions": data["executions"],
                    "total_time": data["total_time"],
                    "avg_time": data["total_time"] / data["executions"],
                    "min_time": data["min_time"],
                    "max_time": data["max_time"],
                }
        return report

    def reset(self) -> None:
        """重置所有监控数据"""
        self._sections.clear()
        self._current_section = None
        self._current_section_start = 0


# 创建全局性能监控实例
performance_monitor = PerformanceMonitor()
