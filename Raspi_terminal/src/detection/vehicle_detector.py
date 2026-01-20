#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车辆检测模块
基于YOLOv8n实现实时车辆检测
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import time
from loguru import logger
import threading
from pathlib import Path


class VehicleDetector:
    """
    车辆检测器
    使用YOLOv8n模型检测视频流中的车辆
    """
    
    def __init__(self, config: Dict):
        """
        初始化检测器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.detection_config = config.get('detection', {})
        
        # 模型配置
        self.model_path = self.detection_config.get('model_path', './models/yolov8n.pt')
        self.device = self.detection_config.get('device', 'cpu')
        self.confidence_threshold = self.detection_config.get('confidence_threshold', 0.5)
        self.iou_threshold = self.detection_config.get('iou_threshold', 0.45)
        self.max_detections = self.detection_config.get('max_detections', 100)
        
        # 目标类别（车辆相关）
        self.target_classes = self.detection_config.get('target_classes', [2, 3, 5, 7])
        self.class_names = {
            2: 'car',
            3: 'motorcycle', 
            5: 'bus',
            7: 'truck'
        }
        
        # 检测区域
        self.detection_zones = self.detection_config.get('detection_zones', [])
        
        # 性能统计
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 初始化模型
        self.model = None
        self._load_model()
        
        logger.info(f"车辆检测器初始化完成 - 模型: {self.model_path}, 设备: {self.device}")
    
    def _load_model(self):
        """加载YOLOv8模型"""
        try:
            # 检查模型文件是否存在
            model_path = Path(self.model_path)
            if not model_path.exists():
                logger.warning(f"模型文件不存在: {self.model_path}, 将下载默认模型")
                self.model_path = 'yolov8n.pt'  # 使用默认模型，会自动下载
            
            # 加载模型
            self.model = YOLO(self.model_path)
            
            # 设置设备
            if self.device == 'cuda' and not self._check_cuda():
                logger.warning("CUDA不可用，切换到CPU")
                self.device = 'cpu'
            
            logger.info(f"YOLOv8模型加载成功: {self.model_path}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def _check_cuda(self) -> bool:
        """检查CUDA是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """
        检测帧中的车辆
        
        Args:
            frame: 输入图像帧
            
        Returns:
            检测结果列表，每个元素包含：
            - bbox: 边界框 [x1, y1, x2, y2]
            - confidence: 置信度
            - class_id: 类别ID
            - class_name: 类别名称
        """
        if self.model is None:
            logger.error("模型未加载")
            return []
        
        try:
            # 执行检测
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                max_det=self.max_detections,
                classes=self.target_classes,
                device=self.device,
                verbose=False
            )
            
            # 解析检测结果
            detections = []
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()  # 边界框
                    confidences = result.boxes.conf.cpu().numpy()  # 置信度
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)  # 类别ID
                    
                    for i in range(len(boxes)):
                        class_id = class_ids[i]
                        if class_id in self.target_classes:
                            detection = {
                                'bbox': boxes[i].tolist(),
                                'confidence': float(confidences[i]),
                                'class_id': int(class_id),
                                'class_name': self.class_names.get(class_id, 'unknown'),
                                'timestamp': time.time()
                            }
                            detections.append(detection)
            
            # 更新FPS统计
            self._update_fps()
            
            return detections
            
        except Exception as e:
            logger.error(f"车辆检测失败: {e}")
            return []
    
    def detect_in_zones(self, frame: np.ndarray) -> Dict[str, List[Dict]]:
        """
        在指定区域内检测车辆
        
        Args:
            frame: 输入图像帧
            
        Returns:
            按区域分组的检测结果
        """
        # 获取全图检测结果
        all_detections = self.detect_vehicles(frame)
        
        # 按区域分组
        zone_detections = {}
        
        for zone in self.detection_zones:
            zone_name = zone.get('name', 'unknown')
            zone_polygon = np.array(zone.get('polygon', []), dtype=np.int32)
            
            zone_detections[zone_name] = []
            
            for detection in all_detections:
                bbox = detection['bbox']
                # 计算边界框中心点
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                
                # 检查中心点是否在区域内
                if self._point_in_polygon((center_x, center_y), zone_polygon):
                    zone_detections[zone_name].append(detection)
        
        return zone_detections
    
    def _point_in_polygon(self, point: Tuple[float, float], polygon: np.ndarray) -> bool:
        """
        检查点是否在多边形内
        
        Args:
            point: 点坐标 (x, y)
            polygon: 多边形顶点数组
            
        Returns:
            是否在多边形内
        """
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
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        在图像上绘制检测结果
        
        Args:
            frame: 输入图像帧
            detections: 检测结果列表
            
        Returns:
            绘制了检测框的图像
        """
        result_frame = frame.copy()
        
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # 绘制边界框
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(result_frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(result_frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return result_frame
    
    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """
        在图像上绘制检测区域
        
        Args:
            frame: 输入图像帧
            
        Returns:
            绘制了检测区域的图像
        """
        result_frame = frame.copy()
        
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        
        for i, zone in enumerate(self.detection_zones):
            zone_name = zone.get('name', f'Zone_{i}')
            zone_polygon = np.array(zone.get('polygon', []), dtype=np.int32)
            
            if len(zone_polygon) >= 3:
                color = colors[i % len(colors)]
                
                # 绘制多边形
                cv2.polylines(result_frame, [zone_polygon], True, color, 2)
                
                # 绘制区域名称
                center_x = int(np.mean(zone_polygon[:, 0]))
                center_y = int(np.mean(zone_polygon[:, 1]))
                cv2.putText(result_frame, zone_name, (center_x, center_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return result_frame
    
    def _update_fps(self):
        """更新FPS统计"""
        with self.lock:
            self.fps_counter += 1
            current_time = time.time()
            
            if current_time - self.fps_start_time >= 1.0:
                self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
                self.fps_counter = 0
                self.fps_start_time = current_time
    
    def get_fps(self) -> float:
        """获取当前FPS"""
        with self.lock:
            return self.current_fps
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'model_path': self.model_path,
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold,
            'target_classes': self.target_classes,
            'class_names': self.class_names
        }
    
    def cleanup(self):
        """清理资源"""
        if self.model is not None:
            del self.model
            self.model = None
        logger.info("车辆检测器资源已清理")


if __name__ == "__main__":
    # 测试代码
    import yaml
    
    # 加载配置
    config_path = "../../config/config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        # 使用默认配置
        config = {
            'detection': {
                'model_path': 'yolov8n.pt',
                'device': 'cpu',
                'confidence_threshold': 0.5,
                'target_classes': [2, 3, 5, 7]
            }
        }
    
    # 创建检测器
    detector = VehicleDetector(config)
    
    # 测试检测
    test_image = np.zeros((720, 1280, 3), dtype=np.uint8)
    detections = detector.detect_vehicles(test_image)
    
    print(f"检测结果: {len(detections)} 个车辆")
    print(f"模型信息: {detector.get_model_info()}")
    
    # 清理资源
    detector.cleanup()

