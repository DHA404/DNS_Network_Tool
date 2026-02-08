#!/usr/bin/env python3
# 进程管理模块

import psutil
import os
import signal
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ProcessInfo:
    """进程信息数据类"""
    pid: int
    name: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    connections: int = 0
    status: str = "unknown"
    create_time: str = ""
    executable: str = ""
    command_line: str = ""
    user: str = ""
    nice: int = 0
    num_threads: int = 0
    io_counters: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "connections": self.connections,
            "status": self.status,
            "create_time": self.create_time,
            "executable": self.executable,
            "command_line": self.command_line,
            "user": self.user,
            "nice": self.nice,
            "num_threads": self.num_threads,
            "io_counters": self.io_counters
        }


class ProcessManager:
    """进程管理器类 - 性能优化版本"""
    
    def __init__(self, refresh_interval: float = 1.0):
        self.refresh_interval = refresh_interval
        self._last_cpu_times = {}
    
    def get_basic_processes(self, limit: int = 100) -> List[ProcessInfo]:
        """快速获取进程基本信息
        
        Args:
            limit: 返回的最大进程数
            
        Returns:
            进程信息列表（仅包含pid、name、connections）
        """
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    info = proc.info
                    if not info or not info.get('pid'):
                        continue
                    
                    pid = info['pid']
                    name = info.get('name', 'unknown') or 'unknown'
                    
                    connections = 0
                    try:
                        connections = len(proc.net_connections(kind='inet'))
                    except Exception:
                        pass
                    
                    proc_info = ProcessInfo(
                        pid=pid,
                        name=name,
                        connections=connections,
                    )
                    processes.append(proc_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception:
                    continue
        except Exception:
            pass
        
        processes.sort(key=lambda x: x.connections, reverse=True)
        
        return processes[:limit]
    
    def get_process_details_batch(self, pids: List[int]) -> Dict[int, ProcessInfo]:
        """批量获取进程详细信息（按需加载）
        
        Args:
            pids: 要获取详情的PID列表
            
        Returns:
            PID到进程信息的映射
        """
        results = {}
        
        for pid in pids:
            info = self.get_process_by_pid(pid)
            if info:
                results[pid] = info
        
        return results
    
    def get_all_processes(self, sort_by: str = "connections", limit: int = 50) -> List[ProcessInfo]:
        """获取所有进程信息（分层加载优化）
        
        Args:
            sort_by: 排序方式 (connections, cpu, memory, name, pid)
            limit: 返回的最大进程数
            
        Returns:
            进程信息列表
        """
        processes = self.get_basic_processes(limit=limit * 2)
        
        sort_key_map = {
            'connections': lambda x: x.connections,
            'cpu': lambda x: x.cpu_percent,
            'memory': lambda x: x.memory_percent,
            'name': lambda x: x.name.lower(),
            'pid': lambda x: x.pid
        }
        
        sort_key = sort_key_map.get(sort_by, sort_key_map['connections'])
        
        sorted_processes = sorted(processes, key=sort_key, reverse=True)[:limit]
        
        if sort_by in ('cpu', 'memory'):
            pids = [p.pid for p in sorted_processes]
            details = self.get_process_details_batch(pids)
            for proc in sorted_processes:
                if proc.pid in details:
                    proc.cpu_percent = details[proc.pid].cpu_percent
                    proc.memory_percent = details[proc.pid].memory_percent
        
        return sorted_processes
    
    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """获取指定PID的进程信息"""
        try:
            proc = psutil.Process(pid)
            info = proc.info
            
            connections = len(proc.net_connections(kind='inet'))
            
            create_time = ""
            if info.get('create_time'):
                try:
                    create_time = datetime.fromtimestamp(info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, OSError):
                    pass
            
            command_line = ""
            if info.get('cmdline'):
                try:
                    command_line = ' '.join(info['cmdline'])
                except Exception:
                    pass
            
            return ProcessInfo(
                pid=info['pid'],
                name=info.get('name', 'unknown') or 'unknown',
                cpu_percent=info.get('cpu_percent', 0) or 0,
                memory_percent=info.get('memory_percent', 0) or 0,
                connections=connections,
                status=info.get('status', 'unknown') or 'unknown',
                create_time=create_time,
                executable=info.get('exe', '') or '',
                command_line=command_line[:200] if command_line else '',
                user=info.get('username', '') or '',
                nice=info.get('nice', 0) or 0,
                num_threads=info.get('num_threads', 0) or 0,
                io_counters=dict(info.get('io_counters', {})) or {}
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception:
            return None
    
    def find_processes_by_name(self, name: str) -> List[ProcessInfo]:
        """根据进程名查找所有匹配的进程"""
        name = name.lower()
        all_processes = self.get_all_processes(limit=200)
        return [p for p in all_processes if name in p.name.lower()]
    
    def kill_processes(self, pids: List[int], force: bool = False, timeout: float = 3.0) -> Dict[str, Any]:
        """批量结束进程
        
        Args:
            pids: 要结束的进程PID列表
            force: 是否强制结束
            timeout: 等待进程结束的超时时间
            
        Returns:
            操作结果字典
        """
        results = {
            "success": [],
            "failed": [],
            "access_denied": [],
            "not_found": []
        }
        
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                
                if not force:
                    try:
                        proc.terminate()
                        proc.wait(timeout=timeout)
                        results["success"].append({
                            "pid": pid,
                            "name": proc.name(),
                            "method": "terminate"
                        })
                    except psutil.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=1.0)
                        results["success"].append({
                            "pid": pid,
                            "name": proc.name(),
                            "method": "kill (after timeout)"
                        })
                else:
                    proc.kill()
                    proc.wait(timeout=1.0)
                    results["success"].append({
                        "pid": pid,
                        "name": proc.name(),
                        "method": "force kill"
                    })
                    
            except psutil.NoSuchProcess:
                results["not_found"].append({"pid": pid})
            except psutil.AccessDenied:
                results["access_denied"].append({"pid": pid})
            except Exception:
                results["failed"].append({"pid": pid})
        
        return results
    
    def get_process_connections(self, pid: int) -> List[Dict[str, Any]]:
        """获取进程的连接信息"""
        connections = []
        
        try:
            proc = psutil.Process(pid)
            net_connections = proc.net_connections(kind='inet')
            
            for conn in net_connections:
                conn_info = {
                    "local_address": conn.laddr.ip if conn.laddr else "0.0.0.0",
                    "local_port": conn.laddr.port if conn.laddr else 0,
                    "remote_address": conn.raddr.ip if conn.raddr else "0.0.0.0",
                    "remote_port": conn.raddr.port if conn.raddr else 0,
                    "status": conn.status,
                    "protocol": "TCP" if conn.type == 1 else "UDP",
                    "pid": pid
                }
                connections.append(conn_info)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception:
            pass
        
        return connections
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统资源使用摘要"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "process_count": len(list(psutil.process_iter())),
            "connection_count": len(psutil.net_connections(kind='inet')),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def parse_process_spec(self, spec: str, process_list: List[ProcessInfo] = None) -> List[int]:
        """解析进程规格字符串
        
        Args:
            spec: 规格字符串，支持: 单个PID、PID列表(逗号/空格)、范围(1-5)、索引(1,2,3)
            process_list: 进程列表（用于索引解析）
            
        Returns:
            PID列表
        """
        pids = []
        spec = spec.strip()
        
        if not spec:
            return pids
        
        if spec.isdigit():
            pids = [int(spec)]
            return pids
        
        if ',' in spec:
            parts = [p.strip() for p in spec.split(',')]
        else:
            parts = spec.split()
        
        for part in parts:
            if part.isdigit():
                pids.append(int(part))
            elif '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if process_list:
                        for i in range(start - 1, min(end, len(process_list))):
                            if process_list[i].pid not in pids:
                                pids.append(process_list[i].pid)
                except ValueError:
                    pass
        
        return list(set(pids))
    
    def filter_by_name(self, process_list: List[ProcessInfo], names: List[str]) -> List[ProcessInfo]:
        """根据进程名列表过滤进程"""
        names_lower = [n.lower() for n in names]
        return [p for p in process_list if any(n in p.name.lower() for n in names_lower)]
    
    def get_unique_process_names(self, process_list: List[ProcessInfo]) -> Dict[str, List[int]]:
        """获取唯一进程名及其所有PID的映射"""
        name_map = defaultdict(list)
        for proc in process_list:
            name_map[proc.name].append(proc.pid)
        return dict(name_map)


def create_process_manager(refresh_interval: float = 1.0) -> ProcessManager:
    """创建进程管理器的工厂函数"""
    return ProcessManager(refresh_interval=refresh_interval)
