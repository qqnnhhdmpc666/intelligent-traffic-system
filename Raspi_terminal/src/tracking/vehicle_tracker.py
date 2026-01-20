#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车辆跟踪模块
实现车辆跟踪和流量统计
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import time
import threading
from collections import defaultdict, deque
from loguru import logger
import uuid


class Vehicle:
    """车辆对象"""
    
    def __init__(self, detection: Dict, track_id: str = None):
        """
        初始化车辆对象
        
        Args:
            detection: 检测结果
            track_id: 跟踪ID
        """
        self.track_id = track_id or str(uuid.uuid4())[:8]
        self.class_id = detection['class_id']
        self.class_name = detection['class_name']
        
        # 位置信息
        self.bbox = detection['bbox']
        self.center = self._calculate_center(self.bbox)
        self.area = self._calculate_area(self.bbox)
        
        # 跟踪信息
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.confidence = detection['confidence']
        
        # 轨迹信息
        self.trajectory = deque(maxlen=30)  # 保留最近30个位置
        self.trajectory.append((self.center, time.time()))
        
        # 状态信息
        self.is_counted = False
        self.zone_history = []  # 经过的区域历史
        self.speed = 0.0  # 估算速度（像素/秒）
        
        # 跟踪质量
        self.tracking_confidence = 1.0
        self.missed_frames = 0
        self.total_frames = 1
    
    def update(self, detection: Dict):
        """
        更新车辆信息
        
        Args:
            detection: 新的检测结果
        """
        # 更新位置信息
        old_center = self.center
        self.bbox = detection['bbox']
        self.center = self._calculate_center(self.bbox)
        self.area = self._calculate_area(self.bbox)
        
        # 更新时间信息
        current_time = time.time()
        self.last_seen = current_time
        self.confidence = detection['confidence']
        
        # 更新轨迹
        self.trajectory.append((self.center, current_time))
        
        # 计算速度
        if len(self.trajectory) >= 2:
            self._calculate_speed()
        
        # 更新跟踪质量
        self.total_frames += 1
        self.tracking_confidence = min(1.0, self.tracking_confidence + 0.1)
    
    def miss_frame(self):
        """标记丢失帧"""
        self.missed_frames += 1
        self.total_frames += 1
        self.tracking_confidence = max(0.0, self.tracking_confidence - 0.2)
    
    def _calculate_center(self, bbox: List[float]) -> Tuple[float, float]:
        """计算边界框中心点"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _calculate_area(self, bbox: List[float]) -> float:
        """计算边界框面积"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    def _calculate_speed(self):
        """计算车辆速度"""
        if len(self.trajectory) < 2:
            return
        
        # 使用最近的两个点计算速度
        (x2, y2), t2 = self.trajectory[-1]
        (x1, y1), t1 = self.trajectory[-2]
        
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        time_diff = t2 - t1
        
        if time_diff > 0:
            self.speed = distance / time_diff
    
    def get_age(self) -> float:
        """获取车辆存在时间"""
        return time.time() - self.first_seen
    
    def get_tracking_quality(self) -> float:
        """获取跟踪质量分数"""
        if self.total_frames == 0:
            return 0.0
        
        detection_rate = (self.total_frames - self.missed_frames) / self.total_frames
        return detection_rate * self.tracking_confidence
    
    def is_valid(self, max_missed_frames: int = 10) -> bool:
        """检查车辆是否仍然有效"""
        return self.missed_frames < max_missed_frames


class VehicleTracker:
    """
    车辆跟踪器
    实现多目标跟踪和流量统计
    """
    
    def __init__(self, config: Dict):
        """
        初始化跟踪器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.tracking_config = config.get('traffic_analysis', {})
        
        # 跟踪参数
        self.max_tracking_distance = self.tracking_config.get('max_tracking_distance', 50)
        self.max_tracking_frames = self.tracking_config.get('max_tracking_frames', 30)
        self.min_tracking_confidence = self.tracking_config.get('min_tracking_confidence', 0.3)
        
        # 车辆过滤参数
        self.vehicle_min_area = self.tracking_config.get('vehicle_min_area', 1000)
        self.vehicle_max_area = self.tracking_config.get('vehicle_max_area', 50000)
        
        # 统计参数
        self.statistics_window = self.tracking_config.get('statistics_window', 60)
        self.history_length = self.tracking_config.get('history_length', 3600)
        
        # 跟踪状态
        self.vehicles = {}  # 当前跟踪的车辆
        self.next_id = 1
        
        # 统计数据
        self.traffic_counts = defaultdict(int)  # 各区域车流量
        self.vehicle_history = deque(maxlen=1000)  # 车辆历史记录
        self.zone_statistics = defaultdict(lambda: defaultdict(int))  # 区域统计
        
        # 计数线
        self.counting_lines = []
        self._setup_counting_lines()
        
        # 线程锁
        self.lock = threading.Lock()
        
        logger.info("车辆跟踪器初始化完成")
    
    def _setup_counting_lines(self):
        """设置计数线"""
        # 从配置中获取检测区域，生成计数线
        detection_zones = self.config.get('detection', {}).get('detection_zones', [])
        
        for zone in detection_zones:
            zone_name = zone.get('name', 'unknown')
            polygon = zone.get('polygon', [])
            
            if len(polygon) >= 2:
                # 简单地使用区域的中心线作为计数线
                points = np.array(polygon)
                center_x = int(np.mean(points[:, 0]))
                center_y = int(np.mean(points[:, 1]))
                
                # 创建水平或垂直计数线
                if 'north' in zone_name.lower() or 'south' in zone_name.lower():
                    # 垂直方向的车道，使用水平计数线
                    line = {
                        'name': f"{zone_name}_line",
                        'start': (center_x - 50, center_y),
                        'end': (center_x + 50, center_y),
                        'direction': 'horizontal'
                    }
                else:
                    # 水平方向的车道，使用垂直计数线
                    line = {
                        'name': f"{zone_name}_line",
                        'start': (center_x, center_y - 50),
                        'end': (center_x, center_y + 50),
                        'direction': 'vertical'
                    }
                
                self.counting_lines.append(line)
    
    def update(self, detections: List[Dict]) -> Dict:
        """
        更新跟踪器
        
        Args:
            detections: 检测结果列表
            
        Returns:
            跟踪结果和统计信息
        """
        with self.lock:
            # 过滤检测结果
            valid_detections = self._filter_detections(detections)
            
            # 数据关联
            matched_pairs, unmatched_detections, unmatched_vehicles = self._associate_detections(valid_detections)
            
            # 更新匹配的车辆
            for vehicle_id, detection in matched_pairs:
                self.vehicles[vehicle_id].update(detection)
            
            # 创建新车辆
            for detection in unmatched_detections:
                vehicle_id = f"V_{self.next_id:04d}"
                self.next_id += 1
                self.vehicles[vehicle_id] = Vehicle(detection, vehicle_id)
            
            # 处理丢失的车辆
            for vehicle_id in unmatched_vehicles:
                self.vehicles[vehicle_id].miss_frame()
            
            # 移除无效车辆
            self._remove_invalid_vehicles()
            
            # 更新统计信息
            self._update_statistics()
            
            # 返回跟踪结果
            return self._get_tracking_results()
    
    def _filter_detections(self, detections: List[Dict]) -> List[Dict]:
        """
        过滤检测结果
        
        Args:
            detections: 原始检测结果
            
        Returns:
            过滤后的检测结果
        """
        valid_detections = []
        
        for detection in detections:
            bbox = detection['bbox']
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            
            # 面积过滤
            if self.vehicle_min_area <= area <= self.vehicle_max_area:
                valid_detections.append(detection)
        
        return valid_detections
    
    def _associate_detections(self, detections: List[Dict]) -> Tuple[List[Tuple], List[Dict], List[str]]:
        """
        数据关联：将检测结果与现有车辆匹配
        
        Args:
            detections: 检测结果列表
            
        Returns:
            匹配对、未匹配检测、未匹配车辆
        """
        if not self.vehicles or not detections:
            return [], detections, list(self.vehicles.keys())
        
        # 计算距离矩阵
        vehicle_ids = list(self.vehicles.keys())
        distance_matrix = np.full((len(vehicle_ids), len(detections)), np.inf)
        
        for i, vehicle_id in enumerate(vehicle_ids):
            vehicle = self.vehicles[vehicle_id]
            vehicle_center = vehicle.center
            
            for j, detection in enumerate(detections):
                detection_center = self._calculate_center(detection['bbox'])
                distance = np.sqrt((vehicle_center[0] - detection_center[0])**2 + 
                                 (vehicle_center[1] - detection_center[1])**2)
                
                if distance <= self.max_tracking_distance:
                    distance_matrix[i, j] = distance
        
        # 使用匈牙利算法进行最优匹配（简化版）
        matched_pairs = []
        unmatched_detections = list(detections)
        unmatched_vehicles = list(vehicle_ids)
        
        # 贪心匹配
        while True:
            min_distance = np.inf
            best_match = None
            
            for i, vehicle_id in enumerate(unmatched_vehicles):
                for j, detection in enumerate(unmatched_detections):
                    if i < distance_matrix.shape[0] and j < distance_matrix.shape[1]:
                        distance = distance_matrix[vehicle_ids.index(vehicle_id), detections.index(detection)]
                        if distance < min_distance:
                            min_distance = distance
                            best_match = (vehicle_id, detection)
            
            if best_match is None or min_distance > self.max_tracking_distance:
                break
            
            vehicle_id, detection = best_match
            matched_pairs.append((vehicle_id, detection))
            unmatched_vehicles.remove(vehicle_id)
            unmatched_detections.remove(detection)
        
        return matched_pairs, unmatched_detections, unmatched_vehicles
    
    def _calculate_center(self, bbox: List[float]) -> Tuple[float, float]:
        """计算边界框中心点"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _remove_invalid_vehicles(self):
        """移除无效车辆"""
        invalid_vehicles = []
        
        for vehicle_id, vehicle in self.vehicles.items():
            if not vehicle.is_valid(self.max_tracking_frames):
                invalid_vehicles.append(vehicle_id)
                
                # 记录车辆历史
                self.vehicle_history.append({
                    'track_id': vehicle_id,
                    'class_name': vehicle.class_name,
                    'first_seen': vehicle.first_seen,
                    'last_seen': vehicle.last_seen,
                    'duration': vehicle.get_age(),
                    'trajectory_length': len(vehicle.trajectory),
                    'average_speed': vehicle.speed,
                    'tracking_quality': vehicle.get_tracking_quality()
                })
        
        for vehicle_id in invalid_vehicles:
            del self.vehicles[vehicle_id]
    
    def _update_statistics(self):
        """更新统计信息"""
        current_time = time.time()
        
        # 更新区域车辆计数
        zone_counts = defaultdict(int)
        
        for vehicle in self.vehicles.values():
            # 检查车辆在哪个区域
            for zone in self.config.get('detection', {}).get('detection_zones', []):
                zone_name = zone.get('name', 'unknown')
                zone_polygon = np.array(zone.get('polygon', []), dtype=np.int32)
                
                if self._point_in_polygon(vehicle.center, zone_polygon):
                    zone_counts[zone_name] += 1
                    break
        
        # 更新统计数据
        for zone_name, count in zone_counts.items():
            self.zone_statistics[zone_name]['current_count'] = count
            self.zone_statistics[zone_name]['last_update'] = current_time
    
    def _point_in_polygon(self, point: Tuple[float, float], polygon: np.ndarray) -> bool:
        """检查点是否在多边形内"""
        if len(polygon) < 3:
            return False
        
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _get_tracking_results(self) -> Dict:
        """获取跟踪结果"""
        vehicles_info = []
        
        for vehicle in self.vehicles.values():
            vehicle_info = {
                'track_id': vehicle.track_id,
                'bbox': vehicle.bbox,
                'center': vehicle.center,
                'class_name': vehicle.class_name,
                'confidence': vehicle.confidence,
                'speed': vehicle.speed,
                'age': vehicle.get_age(),
                'tracking_quality': vehicle.get_tracking_quality()
            }
            vehicles_info.append(vehicle_info)
        
        return {
            'vehicles': vehicles_info,
            'total_vehicles': len(self.vehicles),
            'zone_statistics': dict(self.zone_statistics),
            'timestamp': time.time()
        }
    
    def get_traffic_statistics(self) -> Dict:
        """获取交通统计信息"""
        with self.lock:
            # 计算各类型车辆数量
            vehicle_types = defaultdict(int)
            for vehicle in self.vehicles.values():
                vehicle_types[vehicle.class_name] += 1
            
            # 计算平均速度
            speeds = [v.speed for v in self.vehicles.values() if v.speed > 0]
            avg_speed = np.mean(speeds) if speeds else 0.0
            
            return {
                'total_vehicles': len(self.vehicles),
                'vehicle_types': dict(vehicle_types),
                'zone_counts': {k: v['current_count'] for k, v in self.zone_statistics.items()},
                'average_speed': avg_speed,
                'historical_count': len(self.vehicle_history),
                'timestamp': time.time()
            }
    
    def draw_tracking_results(self, frame: np.ndarray, tracking_results: Dict) -> np.ndarray:
        """
        在图像上绘制跟踪结果
        
        Args:
            frame: 输入图像帧
            tracking_results: 跟踪结果
            
        Returns:
            绘制了跟踪结果的图像
        """
        result_frame = frame.copy()
        
        # 绘制车辆跟踪框和轨迹
        for vehicle_info in tracking_results['vehicles']:
            bbox = vehicle_info['bbox']
            track_id = vehicle_info['track_id']
            class_name = vehicle_info['class_name']
            speed = vehicle_info['speed']
            
            # 绘制跟踪框
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # 绘制跟踪ID和信息
            label = f"ID:{track_id} {class_name} {speed:.1f}px/s"
            cv2.putText(result_frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # 绘制轨迹
            if track_id in self.vehicles:
                vehicle = self.vehicles[track_id]
                if len(vehicle.trajectory) > 1:
                    points = [tuple(map(int, pos)) for pos, _ in vehicle.trajectory]
                    for i in range(1, len(points)):
                        cv2.line(result_frame, points[i-1], points[i], (0, 255, 255), 2)
        
        # 绘制计数线
        for line in self.counting_lines:
            start = tuple(map(int, line['start']))
            end = tuple(map(int, line['end']))
            cv2.line(result_frame, start, end, (0, 0, 255), 3)
            
            # 绘制计数线名称
            mid_x = (start[0] + end[0]) // 2
            mid_y = (start[1] + end[1]) // 2
            cv2.putText(result_frame, line['name'], (mid_x, mid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return result_frame
    
    def cleanup(self):
        """清理资源"""
        with self.lock:
            self.vehicles.clear()
            self.vehicle_history.clear()
            self.zone_statistics.clear()
        
        logger.info("车辆跟踪器资源已清理")


if __name__ == "__main__":
    # 测试代码
    import yaml
    
    # 使用默认配置
    config = {
        'traffic_analysis': {
            'max_tracking_distance': 50,
            'max_tracking_frames': 30,
            'vehicle_min_area': 1000,
            'vehicle_max_area': 50000
        },
        'detection': {
            'detection_zones': [
                {
                    'name': 'north_lane',
                    'polygon': [[100, 100], [500, 100], [500, 300], [100, 300]]
                }
            ]
        }
    }
    
    # 创建跟踪器
    tracker = VehicleTracker(config)
    
    # 测试跟踪
    test_detections = [
        {
            'bbox': [200, 150, 300, 250],
            'confidence': 0.8,
            'class_id': 2,
            'class_name': 'car'
        }
    ]
    
    results = tracker.update(test_detections)
    print(f"跟踪结果: {results}")
    
    stats = tracker.get_traffic_statistics()
    print(f"交通统计: {stats}")
    
    # 清理资源
    tracker.cleanup()

