#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据上报模块
负责将交通数据上报到服务器
"""

import requests
import json
import time
import threading
from typing import Dict, List, Optional
from collections import deque
from loguru import logger
import queue
from datetime import datetime


class DataReporter:
    """
    数据上报器
    负责将交通统计数据上报到服务器
    """
    
    def __init__(self, config: Dict):
        """
        初始化数据上报器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.server_config = config.get('server', {})
        self.system_config = config.get('system', {})
        
        # 服务器配置
        self.base_url = self.server_config.get('base_url', 'http://localhost:8000')
        self.timeout = self.server_config.get('timeout', 30)
        self.retry_attempts = self.server_config.get('retry_attempts', 3)
        self.retry_delay = self.server_config.get('retry_delay', 5)
        
        # 上报配置
        self.report_interval = self.server_config.get('report_interval', 10)
        self.batch_size = self.server_config.get('batch_size', 100)
        
        # 系统信息
        self.intersection_id = self.system_config.get('intersection_id', 'UNKNOWN')
        self.location = self.system_config.get('location', 'Unknown Location')
        
        # API端点
        self.endpoints = self.server_config.get('api_endpoints', {})
        self.traffic_update_url = f"{self.base_url}{self.endpoints.get('traffic_update', '/api/traffic_update')}"
        self.health_check_url = f"{self.base_url}{self.endpoints.get('health_check', '/health')}"
        
        # 数据队列
        self.data_queue = queue.Queue(maxsize=1000)
        self.failed_data = deque(maxlen=500)  # 失败数据缓存
        
        # 状态信息
        self.is_running = False
        self.last_successful_report = None
        self.total_reports = 0
        self.failed_reports = 0
        self.connection_status = False
        
        # 线程管理
        self.report_thread = None
        self.health_check_thread = None
        self.lock = threading.Lock()
        
        # 创建会话
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TrafficVisionSystem/1.0'
        })
        
        logger.info(f"数据上报器初始化完成 - 服务器: {self.base_url}")
    
    def start(self):
        """启动数据上报服务"""
        if self.is_running:
            logger.warning("数据上报服务已在运行")
            return
        
        self.is_running = True
        
        # 启动上报线程
        self.report_thread = threading.Thread(target=self._report_worker, daemon=True)
        self.report_thread.start()
        
        # 启动健康检查线程
        self.health_check_thread = threading.Thread(target=self._health_check_worker, daemon=True)
        self.health_check_thread.start()
        
        logger.info("数据上报服务已启动")
    
    def stop(self):
        """停止数据上报服务"""
        self.is_running = False
        
        if self.report_thread and self.report_thread.is_alive():
            self.report_thread.join(timeout=5)
        
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
        
        logger.info("数据上报服务已停止")
    
    def report_traffic_data(self, traffic_data: Dict) -> bool:
        """
        上报交通数据
        
        Args:
            traffic_data: 交通统计数据
            
        Returns:
            是否成功添加到队列
        """
        try:
            # 构造上报数据
            report_data = self._build_report_data(traffic_data)
            
            # 添加到队列
            self.data_queue.put(report_data, block=False)
            return True
            
        except queue.Full:
            logger.warning("数据队列已满，丢弃数据")
            return False
        except Exception as e:
            logger.error(f"添加数据到队列失败: {e}")
            return False
    
    def _build_report_data(self, traffic_data: Dict) -> Dict:
        """
        构造上报数据格式
        
        Args:
            traffic_data: 原始交通数据
            
        Returns:
            格式化的上报数据
        """
        current_time = datetime.now().isoformat()
        
        # 构造道路数据
        roads_data = []
        zone_counts = traffic_data.get('zone_counts', {})
        
        for zone_name, count in zone_counts.items():
            # 将区域名称映射到道路ID
            road_id = self._zone_to_road_id(zone_name)
            
            road_data = {
                'road_id': road_id,
                'vehicle_count': count,
                'average_speed': traffic_data.get('average_speed', 0.0),
                'congestion_level': self._calculate_congestion_level(count),
                'timestamp': current_time
            }
            roads_data.append(road_data)
        
        # 如果没有区域数据，创建一个默认道路数据
        if not roads_data:
            roads_data.append({
                'road_id': 'default_road',
                'vehicle_count': traffic_data.get('total_vehicles', 0),
                'average_speed': traffic_data.get('average_speed', 0.0),
                'congestion_level': 'low',
                'timestamp': current_time
            })
        
        return {
            'intersection_id': self.intersection_id,
            'location': self.location,
            'timestamp': current_time,
            'roads': roads_data,
            'summary': {
                'total_vehicles': traffic_data.get('total_vehicles', 0),
                'vehicle_types': traffic_data.get('vehicle_types', {}),
                'average_speed': traffic_data.get('average_speed', 0.0),
                'data_quality': 'good'  # 可以根据实际情况调整
            }
        }
    
    def _zone_to_road_id(self, zone_name: str) -> str:
        """
        将区域名称映射到道路ID
        
        Args:
            zone_name: 区域名称
            
        Returns:
            道路ID
        """
        # 简单的映射规则，可以根据实际需要调整
        zone_mapping = {
            'north_lane': 'road_north',
            'south_lane': 'road_south',
            'east_lane': 'road_east',
            'west_lane': 'road_west'
        }
        
        return zone_mapping.get(zone_name, f"road_{zone_name}")
    
    def _calculate_congestion_level(self, vehicle_count: int) -> str:
        """
        计算拥堵等级
        
        Args:
            vehicle_count: 车辆数量
            
        Returns:
            拥堵等级
        """
        if vehicle_count <= 2:
            return 'low'
        elif vehicle_count <= 5:
            return 'medium'
        else:
            return 'high'
    
    def _report_worker(self):
        """上报工作线程"""
        logger.info("数据上报工作线程已启动")
        
        while self.is_running:
            try:
                # 收集批量数据
                batch_data = []
                
                # 等待数据或超时
                try:
                    data = self.data_queue.get(timeout=self.report_interval)
                    batch_data.append(data)
                    
                    # 收集更多数据（如果有）
                    while len(batch_data) < self.batch_size:
                        try:
                            data = self.data_queue.get_nowait()
                            batch_data.append(data)
                        except queue.Empty:
                            break
                    
                except queue.Empty:
                    # 超时，检查是否有失败的数据需要重试
                    if self.failed_data:
                        batch_data = [self.failed_data.popleft()]
                
                # 发送数据
                if batch_data:
                    success = self._send_batch_data(batch_data)
                    
                    if success:
                        with self.lock:
                            self.total_reports += len(batch_data)
                            self.last_successful_report = time.time()
                    else:
                        # 将失败的数据加入重试队列
                        for data in batch_data:
                            if len(self.failed_data) < self.failed_data.maxlen:
                                self.failed_data.append(data)
                        
                        with self.lock:
                            self.failed_reports += len(batch_data)
                
            except Exception as e:
                logger.error(f"数据上报工作线程异常: {e}")
                time.sleep(1)
        
        logger.info("数据上报工作线程已停止")
    
    def _send_batch_data(self, batch_data: List[Dict]) -> bool:
        """
        发送批量数据
        
        Args:
            batch_data: 批量数据列表
            
        Returns:
            是否发送成功
        """
        for attempt in range(self.retry_attempts):
            try:
                # 如果是单条数据，直接发送
                if len(batch_data) == 1:
                    response = self.session.post(
                        self.traffic_update_url,
                        json=batch_data[0],
                        timeout=self.timeout
                    )
                else:
                    # 批量数据，需要逐条发送（根据API设计）
                    for data in batch_data:
                        response = self.session.post(
                            self.traffic_update_url,
                            json=data,
                            timeout=self.timeout
                        )
                        response.raise_for_status()
                
                response.raise_for_status()
                
                logger.debug(f"成功上报 {len(batch_data)} 条数据")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"数据上报失败 (尝试 {attempt + 1}/{self.retry_attempts}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"数据上报异常: {e}")
                break
        
        logger.error(f"数据上报最终失败，丢弃 {len(batch_data)} 条数据")
        return False
    
    def _health_check_worker(self):
        """健康检查工作线程"""
        logger.info("健康检查工作线程已启动")
        
        while self.is_running:
            try:
                # 执行健康检查
                self.connection_status = self._check_server_health()
                
                # 等待下次检查
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
                self.connection_status = False
                time.sleep(10)
        
        logger.info("健康检查工作线程已停止")
    
    def _check_server_health(self) -> bool:
        """
        检查服务器健康状态
        
        Returns:
            服务器是否健康
        """
        try:
            response = self.session.get(self.health_check_url, timeout=10)
            response.raise_for_status()
            
            # 检查响应内容
            if response.status_code == 200:
                logger.debug("服务器健康检查通过")
                return True
            else:
                logger.warning(f"服务器健康检查失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"服务器健康检查失败: {e}")
            return False
        except Exception as e:
            logger.error(f"健康检查异常: {e}")
            return False
    
    def get_status(self) -> Dict:
        """
        获取上报器状态
        
        Returns:
            状态信息
        """
        with self.lock:
            return {
                'is_running': self.is_running,
                'connection_status': self.connection_status,
                'total_reports': self.total_reports,
                'failed_reports': self.failed_reports,
                'success_rate': (self.total_reports / (self.total_reports + self.failed_reports) * 100) if (self.total_reports + self.failed_reports) > 0 else 0,
                'last_successful_report': self.last_successful_report,
                'queue_size': self.data_queue.qsize(),
                'failed_queue_size': len(self.failed_data),
                'server_url': self.base_url
            }
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        status = self.get_status()
        
        return {
            'uptime': time.time() - (self.last_successful_report or time.time()),
            'total_reports_sent': status['total_reports'],
            'failed_reports': status['failed_reports'],
            'success_rate': status['success_rate'],
            'current_queue_size': status['queue_size'],
            'connection_healthy': status['connection_status'],
            'last_report_time': status['last_successful_report']
        }
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        
        # 清理队列
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break
        
        self.failed_data.clear()
        
        # 关闭会话
        if self.session:
            self.session.close()
        
        logger.info("数据上报器资源已清理")


if __name__ == "__main__":
    # 测试代码
    import yaml
    
    # 使用默认配置
    config = {
        'server': {
            'base_url': 'http://120.53.28.58:3389',
            'timeout': 30,
            'retry_attempts': 3,
            'report_interval': 10,
            'api_endpoints': {
                'traffic_update': '/api/traffic_update',
                'health_check': '/health'
            }
        },
        'system': {
            'intersection_id': 'TEST_001',
            'location': 'Test Location'
        }
    }
    
    # 创建上报器
    reporter = DataReporter(config)
    
    # 启动服务
    reporter.start()
    
    # 测试上报数据
    test_data = {
        'total_vehicles': 5,
        'zone_counts': {'north_lane': 2, 'south_lane': 3},
        'average_speed': 25.5,
        'vehicle_types': {'car': 4, 'truck': 1}
    }
    
    success = reporter.report_traffic_data(test_data)
    print(f"数据上报结果: {success}")
    
    # 等待一段时间
    time.sleep(5)
    
    # 获取状态
    status = reporter.get_status()
    print(f"上报器状态: {status}")
    
    # 清理资源
    reporter.cleanup()

