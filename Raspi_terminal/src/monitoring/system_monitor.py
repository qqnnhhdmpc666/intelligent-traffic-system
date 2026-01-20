#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控模块
监控系统资源使用情况和性能指标
"""

import psutil
import time
import threading
from typing import Dict, List, Optional
from loguru import logger
from collections import deque
import json
from datetime import datetime

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    # 树莓派温度监控
    import subprocess
    RPI_TEMP_AVAILABLE = True
except ImportError:
    RPI_TEMP_AVAILABLE = False


class SystemMonitor:
    """
    系统监控器
    监控CPU、内存、磁盘、网络、温度等系统指标
    """
    
    def __init__(self, config: Dict):
        """
        初始化系统监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.monitoring_config = config.get('monitoring', {})
        
        # 监控配置
        self.enable_monitor = self.monitoring_config.get('enable_system_monitor', True)
        self.monitor_interval = self.monitoring_config.get('monitor_interval', 30)
        
        # 监控项目
        self.track_fps = self.monitoring_config.get('track_fps', True)
        self.track_memory = self.monitoring_config.get('track_memory', True)
        self.track_cpu = self.monitoring_config.get('track_cpu', True)
        self.track_temperature = self.monitoring_config.get('track_temperature', True)
        
        # 告警阈值
        self.alerts = self.monitoring_config.get('alerts', {})
        self.high_cpu_threshold = self.alerts.get('high_cpu_threshold', 80)
        self.high_memory_threshold = self.alerts.get('high_memory_threshold', 85)
        self.high_temperature_threshold = self.alerts.get('high_temperature_threshold', 70)
        self.low_fps_threshold = self.alerts.get('low_fps_threshold', 15)
        
        # 数据存储
        self.history_length = 100  # 保留最近100个数据点
        self.cpu_history = deque(maxlen=self.history_length)
        self.memory_history = deque(maxlen=self.history_length)
        self.temperature_history = deque(maxlen=self.history_length)
        self.fps_history = deque(maxlen=self.history_length)
        self.disk_history = deque(maxlen=self.history_length)
        self.network_history = deque(maxlen=self.history_length)
        
        # 告警记录
        self.alerts_history = deque(maxlen=50)
        
        # 线程管理
        self.monitor_thread = None
        self.is_running = False
        self.lock = threading.Lock()
        
        # 网络统计基准
        self.last_network_stats = None
        self.last_network_time = None
        
        # 系统启动时间
        self.start_time = time.time()
        
        logger.info("系统监控器初始化完成")
    
    def start(self):
        """启动系统监控"""
        if not self.enable_monitor:
            logger.info("系统监控已禁用")
            return
        
        if self.is_running:
            logger.warning("系统监控已在运行")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
        
        logger.info("系统监控已启动")
    
    def stop(self):
        """停止系统监控"""
        self.is_running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("系统监控已停止")
    
    def _monitor_worker(self):
        """监控工作线程"""
        logger.info("系统监控工作线程已启动")
        
        while self.is_running:
            try:
                # 收集系统指标
                metrics = self._collect_metrics()
                
                # 存储历史数据
                self._store_metrics(metrics)
                
                # 检查告警
                self._check_alerts(metrics)
                
                # 等待下次监控
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"系统监控异常: {e}")
                time.sleep(5)
        
        logger.info("系统监控工作线程已停止")
    
    def _collect_metrics(self) -> Dict:
        """收集系统指标"""
        metrics = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat()
        }
        
        # CPU使用率
        if self.track_cpu:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                
                metrics['cpu'] = {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': cpu_freq.current if cpu_freq else 0
                }
            except Exception as e:
                logger.warning(f"获取CPU信息失败: {e}")
                metrics['cpu'] = {'usage_percent': 0, 'count': 0, 'frequency': 0}
        
        # 内存使用情况
        if self.track_memory:
            try:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                metrics['memory'] = {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'usage_percent': memory.percent,
                    'swap_total': swap.total,
                    'swap_used': swap.used,
                    'swap_percent': swap.percent
                }
            except Exception as e:
                logger.warning(f"获取内存信息失败: {e}")
                metrics['memory'] = {'usage_percent': 0}
        
        # 磁盘使用情况
        try:
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            metrics['disk'] = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'usage_percent': (disk.used / disk.total) * 100,
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0
            }
        except Exception as e:
            logger.warning(f"获取磁盘信息失败: {e}")
            metrics['disk'] = {'usage_percent': 0}
        
        # 网络使用情况
        try:
            network = psutil.net_io_counters()
            current_time = time.time()
            
            if self.last_network_stats and self.last_network_time:
                time_diff = current_time - self.last_network_time
                bytes_sent_diff = network.bytes_sent - self.last_network_stats.bytes_sent
                bytes_recv_diff = network.bytes_recv - self.last_network_stats.bytes_recv
                
                metrics['network'] = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'send_rate': bytes_sent_diff / time_diff if time_diff > 0 else 0,
                    'recv_rate': bytes_recv_diff / time_diff if time_diff > 0 else 0
                }
            else:
                metrics['network'] = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'send_rate': 0,
                    'recv_rate': 0
                }
            
            self.last_network_stats = network
            self.last_network_time = current_time
            
        except Exception as e:
            logger.warning(f"获取网络信息失败: {e}")
            metrics['network'] = {'send_rate': 0, 'recv_rate': 0}
        
        # 温度监控
        if self.track_temperature:
            metrics['temperature'] = self._get_temperature()
        
        # GPU使用情况（如果可用）
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # 使用第一个GPU
                    metrics['gpu'] = {
                        'usage_percent': gpu.load * 100,
                        'memory_used': gpu.memoryUsed,
                        'memory_total': gpu.memoryTotal,
                        'memory_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100,
                        'temperature': gpu.temperature
                    }
            except Exception as e:
                logger.warning(f"获取GPU信息失败: {e}")
        
        return metrics
    
    def _get_temperature(self) -> Dict:
        """获取系统温度"""
        temperature_data = {}
        
        # 树莓派CPU温度
        if RPI_TEMP_AVAILABLE:
            try:
                result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    temp_str = result.stdout.strip()
                    if 'temp=' in temp_str:
                        temp_value = float(temp_str.split('=')[1].replace("'C", ""))
                        temperature_data['cpu'] = temp_value
            except Exception as e:
                logger.debug(f"获取树莓派CPU温度失败: {e}")
        
        # 系统温度传感器
        try:
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                for entry in entries:
                    if entry.current:
                        temperature_data[f"{name}_{entry.label or 'sensor'}"] = entry.current
        except Exception as e:
            logger.debug(f"获取系统温度传感器失败: {e}")
        
        return temperature_data
    
    def _store_metrics(self, metrics: Dict):
        """存储指标数据"""
        with self.lock:
            timestamp = metrics['timestamp']
            
            # 存储CPU数据
            if 'cpu' in metrics:
                self.cpu_history.append({
                    'timestamp': timestamp,
                    'usage_percent': metrics['cpu']['usage_percent']
                })
            
            # 存储内存数据
            if 'memory' in metrics:
                self.memory_history.append({
                    'timestamp': timestamp,
                    'usage_percent': metrics['memory']['usage_percent']
                })
            
            # 存储温度数据
            if 'temperature' in metrics:
                self.temperature_history.append({
                    'timestamp': timestamp,
                    'temperatures': metrics['temperature']
                })
            
            # 存储磁盘数据
            if 'disk' in metrics:
                self.disk_history.append({
                    'timestamp': timestamp,
                    'usage_percent': metrics['disk']['usage_percent']
                })
            
            # 存储网络数据
            if 'network' in metrics:
                self.network_history.append({
                    'timestamp': timestamp,
                    'send_rate': metrics['network']['send_rate'],
                    'recv_rate': metrics['network']['recv_rate']
                })
    
    def _check_alerts(self, metrics: Dict):
        """检查告警条件"""
        alerts = []
        current_time = time.time()
        
        # CPU使用率告警
        if 'cpu' in metrics:
            cpu_usage = metrics['cpu']['usage_percent']
            if cpu_usage > self.high_cpu_threshold:
                alert = {
                    'type': 'high_cpu',
                    'message': f"CPU使用率过高: {cpu_usage:.1f}%",
                    'value': cpu_usage,
                    'threshold': self.high_cpu_threshold,
                    'timestamp': current_time
                }
                alerts.append(alert)
        
        # 内存使用率告警
        if 'memory' in metrics:
            memory_usage = metrics['memory']['usage_percent']
            if memory_usage > self.high_memory_threshold:
                alert = {
                    'type': 'high_memory',
                    'message': f"内存使用率过高: {memory_usage:.1f}%",
                    'value': memory_usage,
                    'threshold': self.high_memory_threshold,
                    'timestamp': current_time
                }
                alerts.append(alert)
        
        # 温度告警
        if 'temperature' in metrics:
            for sensor, temp in metrics['temperature'].items():
                if temp > self.high_temperature_threshold:
                    alert = {
                        'type': 'high_temperature',
                        'message': f"{sensor}温度过高: {temp:.1f}°C",
                        'value': temp,
                        'threshold': self.high_temperature_threshold,
                        'sensor': sensor,
                        'timestamp': current_time
                    }
                    alerts.append(alert)
        
        # 记录告警
        if alerts:
            with self.lock:
                for alert in alerts:
                    self.alerts_history.append(alert)
                    logger.warning(f"系统告警: {alert['message']}")
    
    def update_fps(self, fps: float):
        """
        更新FPS数据
        
        Args:
            fps: 当前FPS值
        """
        if not self.track_fps:
            return
        
        with self.lock:
            self.fps_history.append({
                'timestamp': time.time(),
                'fps': fps
            })
            
            # 检查FPS告警
            if fps < self.low_fps_threshold:
                alert = {
                    'type': 'low_fps',
                    'message': f"FPS过低: {fps:.1f}",
                    'value': fps,
                    'threshold': self.low_fps_threshold,
                    'timestamp': time.time()
                }
                self.alerts_history.append(alert)
                logger.warning(f"性能告警: {alert['message']}")
    
    def get_current_metrics(self) -> Dict:
        """获取当前系统指标"""
        return self._collect_metrics()
    
    def get_system_summary(self) -> Dict:
        """获取系统摘要信息"""
        current_metrics = self._collect_metrics()
        
        with self.lock:
            # 计算平均值
            avg_cpu = 0
            avg_memory = 0
            avg_fps = 0
            
            if self.cpu_history:
                avg_cpu = sum(item['usage_percent'] for item in self.cpu_history) / len(self.cpu_history)
            
            if self.memory_history:
                avg_memory = sum(item['usage_percent'] for item in self.memory_history) / len(self.memory_history)
            
            if self.fps_history:
                avg_fps = sum(item['fps'] for item in self.fps_history) / len(self.fps_history)
            
            return {
                'uptime': time.time() - self.start_time,
                'current': {
                    'cpu_usage': current_metrics.get('cpu', {}).get('usage_percent', 0),
                    'memory_usage': current_metrics.get('memory', {}).get('usage_percent', 0),
                    'disk_usage': current_metrics.get('disk', {}).get('usage_percent', 0),
                    'temperature': current_metrics.get('temperature', {}),
                    'network_send_rate': current_metrics.get('network', {}).get('send_rate', 0),
                    'network_recv_rate': current_metrics.get('network', {}).get('recv_rate', 0)
                },
                'average': {
                    'cpu_usage': avg_cpu,
                    'memory_usage': avg_memory,
                    'fps': avg_fps
                },
                'alerts_count': len(self.alerts_history),
                'last_alert': self.alerts_history[-1] if self.alerts_history else None
            }
    
    def get_history_data(self, metric_type: str, limit: int = 50) -> List[Dict]:
        """
        获取历史数据
        
        Args:
            metric_type: 指标类型 ('cpu', 'memory', 'temperature', 'fps', 'disk', 'network')
            limit: 返回数据点数量限制
            
        Returns:
            历史数据列表
        """
        with self.lock:
            if metric_type == 'cpu':
                return list(self.cpu_history)[-limit:]
            elif metric_type == 'memory':
                return list(self.memory_history)[-limit:]
            elif metric_type == 'temperature':
                return list(self.temperature_history)[-limit:]
            elif metric_type == 'fps':
                return list(self.fps_history)[-limit:]
            elif metric_type == 'disk':
                return list(self.disk_history)[-limit:]
            elif metric_type == 'network':
                return list(self.network_history)[-limit:]
            else:
                return []
    
    def get_alerts(self, limit: int = 20) -> List[Dict]:
        """
        获取告警历史
        
        Args:
            limit: 返回告警数量限制
            
        Returns:
            告警列表
        """
        with self.lock:
            return list(self.alerts_history)[-limit:]
    
    def export_metrics(self, filepath: str):
        """
        导出指标数据到文件
        
        Args:
            filepath: 导出文件路径
        """
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'system_summary': self.get_system_summary(),
                'current_metrics': self.get_current_metrics(),
                'history': {
                    'cpu': list(self.cpu_history),
                    'memory': list(self.memory_history),
                    'temperature': list(self.temperature_history),
                    'fps': list(self.fps_history),
                    'disk': list(self.disk_history),
                    'network': list(self.network_history)
                },
                'alerts': list(self.alerts_history)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"系统指标已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"导出系统指标失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        
        with self.lock:
            self.cpu_history.clear()
            self.memory_history.clear()
            self.temperature_history.clear()
            self.fps_history.clear()
            self.disk_history.clear()
            self.network_history.clear()
            self.alerts_history.clear()
        
        logger.info("系统监控器资源已清理")


if __name__ == "__main__":
    # 测试代码
    import yaml
    
    # 使用默认配置
    config = {
        'monitoring': {
            'enable_system_monitor': True,
            'monitor_interval': 5,
            'track_fps': True,
            'track_memory': True,
            'track_cpu': True,
            'track_temperature': True,
            'alerts': {
                'high_cpu_threshold': 80,
                'high_memory_threshold': 85,
                'high_temperature_threshold': 70,
                'low_fps_threshold': 15
            }
        }
    }
    
    # 创建系统监控器
    monitor = SystemMonitor(config)
    
    # 启动监控
    monitor.start()
    
    # 模拟运行
    for i in range(10):
        time.sleep(2)
        
        # 更新FPS数据
        monitor.update_fps(25.0 + i)
        
        if i == 5:
            # 获取系统摘要
            summary = monitor.get_system_summary()
            print(f"系统摘要: {summary}")
    
    # 获取历史数据
    cpu_history = monitor.get_history_data('cpu', 5)
    print(f"CPU历史数据: {cpu_history}")
    
    # 获取告警
    alerts = monitor.get_alerts()
    print(f"告警记录: {alerts}")
    
    # 导出数据
    monitor.export_metrics('./system_metrics.json')
    
    # 清理资源
    monitor.cleanup()

