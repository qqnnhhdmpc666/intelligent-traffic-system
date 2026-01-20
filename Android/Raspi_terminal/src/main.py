#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路口车流识别系统主程序
整合所有模块，实现完整的交通监控功能
"""

import sys
import os
import time
import signal
import threading
from pathlib import Path
import yaml
from loguru import logger

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

# 导入各个模块
from detection.vehicle_detector import VehicleDetector
from tracking.vehicle_tracker import VehicleTracker
from communication.data_reporter import DataReporter
from camera.camera_manager import CameraManager
from monitoring.system_monitor import SystemMonitor


class TrafficVisionSystem:
    """
    路口车流识别系统主类
    整合所有功能模块
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化系统
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 系统状态
        self.is_running = False
        self.start_time = None
        
        # 初始化日志
        self._setup_logging()
        
        # 初始化各个模块
        self.camera_manager = None
        self.vehicle_detector = None
        self.vehicle_tracker = None
        self.data_reporter = None
        self.system_monitor = None
        
        # 处理线程
        self.processing_thread = None
        self.lock = threading.Lock()
        
        # 统计信息
        self.frame_count = 0
        self.detection_count = 0
        self.last_report_time = time.time()
        
        logger.info("路口车流识别系统初始化完成")
    
    def _load_config(self, config_path: str = None) -> dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if config_path is None:
            # 默认配置文件路径
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            'system': {
                'name': 'TrafficVisionSystem',
                'version': '1.0.0',
                'intersection_id': 'DEFAULT_001',
                'location': 'Default Location'
            },
            'server': {
                'base_url': 'http://120.53.28.58:3389',
                'timeout': 30,
                'report_interval': 10
            },
            'camera': {
                'type': 'usb',
                'width': 1280,
                'height': 720,
                'fps': 30,
                'usb_device_id': 0
            },
            'detection': {
                'model_path': './models/yolov8n.pt',
                'device': 'cpu',
                'confidence_threshold': 0.5,
                'target_classes': [2, 3, 5, 7]
            },
            'monitoring': {
                'enable_system_monitor': True,
                'monitor_interval': 30
            },
            'logging': {
                'level': 'INFO',
                'console_output': True,
                'file_output': True
            }
        }
    
    def _setup_logging(self):
        """设置日志系统"""
        logging_config = self.config.get('logging', {})
        
        # 移除默认处理器
        logger.remove()
        
        # 日志级别
        log_level = logging_config.get('level', 'INFO')
        
        # 控制台输出
        if logging_config.get('console_output', True):
            logger.add(
                sys.stdout,
                level=log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
            )
        
        # 文件输出
        if logging_config.get('file_output', True):
            log_dir = logging_config.get('log_dir', './logs')
            os.makedirs(log_dir, exist_ok=True)
            
            logger.add(
                os.path.join(log_dir, "traffic_vision_{time:YYYY-MM-DD}.log"),
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                rotation="1 day",
                retention="7 days",
                compression="zip"
            )
    
    def initialize_modules(self):
        """初始化所有模块"""
        try:
            # 初始化摄像头管理器
            logger.info("初始化摄像头管理器...")
            self.camera_manager = CameraManager(self.config)
            
            # 初始化车辆检测器
            logger.info("初始化车辆检测器...")
            self.vehicle_detector = VehicleDetector(self.config)
            
            # 初始化车辆跟踪器
            logger.info("初始化车辆跟踪器...")
            self.vehicle_tracker = VehicleTracker(self.config)
            
            # 初始化数据上报器
            logger.info("初始化数据上报器...")
            self.data_reporter = DataReporter(self.config)
            
            # 初始化系统监控器
            logger.info("初始化系统监控器...")
            self.system_monitor = SystemMonitor(self.config)
            
            logger.info("所有模块初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"模块初始化失败: {e}")
            return False
    
    def start(self):
        """启动系统"""
        if self.is_running:
            logger.warning("系统已在运行")
            return False
        
        logger.info("启动路口车流识别系统...")
        
        # 初始化模块
        if not self.initialize_modules():
            logger.error("模块初始化失败，系统启动中止")
            return False
        
        try:
            # 启动系统监控器
            self.system_monitor.start()
            
            # 启动数据上报器
            self.data_reporter.start()
            
            # 启动摄像头
            if not self.camera_manager.start(self._frame_callback):
                logger.error("摄像头启动失败")
                return False
            
            # 启动处理线程
            self.is_running = True
            self.start_time = time.time()
            self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.processing_thread.start()
            
            logger.info("路口车流识别系统启动成功")
            return True
            
        except Exception as e:
            logger.error(f"系统启动失败: {e}")
            self.stop()
            return False
    
    def stop(self):
        """停止系统"""
        logger.info("停止路口车流识别系统...")
        
        self.is_running = False
        
        # 等待处理线程结束
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        # 停止各个模块
        if self.camera_manager:
            self.camera_manager.stop()
        
        if self.data_reporter:
            self.data_reporter.stop()
        
        if self.system_monitor:
            self.system_monitor.stop()
        
        logger.info("路口车流识别系统已停止")
    
    def _frame_callback(self, frame):
        """
        帧处理回调函数
        
        Args:
            frame: 图像帧
        """
        # 这个回调函数由摄像头管理器调用
        # 实际处理在_processing_worker中进行
        pass
    
    def _processing_worker(self):
        """处理工作线程"""
        logger.info("图像处理工作线程已启动")
        
        while self.is_running:
            try:
                # 获取图像帧
                frame = self.camera_manager.get_frame(timeout=1.0)
                if frame is None:
                    continue
                
                # 车辆检测
                detections = self.vehicle_detector.detect_vehicles(frame)
                
                # 车辆跟踪
                tracking_results = self.vehicle_tracker.update(detections)
                
                # 更新统计信息
                self._update_statistics(detections, tracking_results)
                
                # 定期上报数据
                self._report_data_if_needed(tracking_results)
                
                # 更新系统监控
                self._update_monitoring()
                
            except Exception as e:
                logger.error(f"图像处理异常: {e}")
                time.sleep(1)
        
        logger.info("图像处理工作线程已停止")
    
    def _update_statistics(self, detections, tracking_results):
        """更新统计信息"""
        with self.lock:
            self.frame_count += 1
            self.detection_count += len(detections)
    
    def _report_data_if_needed(self, tracking_results):
        """根据需要上报数据"""
        current_time = time.time()
        report_interval = self.config.get('server', {}).get('report_interval', 10)
        
        if current_time - self.last_report_time >= report_interval:
            # 获取交通统计数据
            traffic_stats = self.vehicle_tracker.get_traffic_statistics()
            
            # 上报数据
            self.data_reporter.report_traffic_data(traffic_stats)
            
            self.last_report_time = current_time
            logger.debug(f"上报交通数据: {traffic_stats['total_vehicles']} 辆车")
    
    def _update_monitoring(self):
        """更新系统监控"""
        if self.system_monitor:
            # 更新FPS
            camera_fps = self.camera_manager.get_fps()
            detection_fps = self.vehicle_detector.get_fps()
            
            # 使用较低的FPS作为系统FPS
            system_fps = min(camera_fps, detection_fps) if detection_fps > 0 else camera_fps
            self.system_monitor.update_fps(system_fps)
    
    def get_system_status(self) -> dict:
        """获取系统状态"""
        with self.lock:
            uptime = time.time() - self.start_time if self.start_time else 0
            
            status = {
                'is_running': self.is_running,
                'uptime': uptime,
                'frame_count': self.frame_count,
                'detection_count': self.detection_count,
                'modules': {}
            }
            
            # 摄像头状态
            if self.camera_manager:
                status['modules']['camera'] = {
                    'is_opened': self.camera_manager.is_opened(),
                    'fps': self.camera_manager.get_fps(),
                    'statistics': self.camera_manager.get_statistics()
                }
            
            # 检测器状态
            if self.vehicle_detector:
                status['modules']['detector'] = {
                    'fps': self.vehicle_detector.get_fps(),
                    'model_info': self.vehicle_detector.get_model_info()
                }
            
            # 跟踪器状态
            if self.vehicle_tracker:
                status['modules']['tracker'] = self.vehicle_tracker.get_traffic_statistics()
            
            # 数据上报器状态
            if self.data_reporter:
                status['modules']['reporter'] = self.data_reporter.get_status()
            
            # 系统监控状态
            if self.system_monitor:
                status['modules']['monitor'] = self.system_monitor.get_system_summary()
            
            return status
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("清理系统资源...")
        
        self.stop()
        
        # 清理各个模块
        if self.vehicle_detector:
            self.vehicle_detector.cleanup()
        
        if self.vehicle_tracker:
            self.vehicle_tracker.cleanup()
        
        if self.data_reporter:
            self.data_reporter.cleanup()
        
        if self.camera_manager:
            self.camera_manager.cleanup()
        
        if self.system_monitor:
            self.system_monitor.cleanup()
        
        logger.info("系统资源清理完成")


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在停止系统...")
    if 'system' in globals():
        system.cleanup()
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 解析命令行参数
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # 创建系统实例
    global system
    system = TrafficVisionSystem(config_path)
    
    try:
        # 启动系统
        if system.start():
            logger.info("系统运行中，按 Ctrl+C 停止...")
            
            # 主循环
            while system.is_running:
                time.sleep(1)
                
                # 定期打印状态信息
                if int(time.time()) % 60 == 0:  # 每分钟打印一次
                    status = system.get_system_status()
                    logger.info(f"系统状态 - 运行时间: {status['uptime']:.0f}s, "
                              f"处理帧数: {status['frame_count']}, "
                              f"检测车辆: {status['detection_count']}")
        else:
            logger.error("系统启动失败")
            return 1
    
    except KeyboardInterrupt:
        logger.info("用户中断，正在停止系统...")
    
    except Exception as e:
        logger.error(f"系统运行异常: {e}")
        return 1
    
    finally:
        # 清理资源
        system.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

