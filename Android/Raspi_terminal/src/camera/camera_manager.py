#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头管理模块
支持树莓派摄像头、USB摄像头和RTSP网络摄像头
"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Tuple, Callable
from loguru import logger
import queue
from abc import ABC, abstractmethod

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    logger.warning("picamera2 不可用，无法使用树莓派摄像头")


class CameraBase(ABC):
    """摄像头基类"""
    
    @abstractmethod
    def start(self) -> bool:
        """启动摄像头"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止摄像头"""
        pass
    
    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取帧"""
        pass
    
    @abstractmethod
    def is_opened(self) -> bool:
        """检查摄像头是否打开"""
        pass
    
    @abstractmethod
    def get_properties(self) -> dict:
        """获取摄像头属性"""
        pass


class PiCamera(CameraBase):
    """树莓派摄像头"""
    
    def __init__(self, config: dict):
        """
        初始化树莓派摄像头
        
        Args:
            config: 摄像头配置
        """
        if not PICAMERA_AVAILABLE:
            raise RuntimeError("picamera2 不可用")
        
        self.config = config
        self.width = config.get('width', 1280)
        self.height = config.get('height', 720)
        self.fps = config.get('fps', 30)
        
        self.camera = None
        self.is_running = False
        
        logger.info(f"树莓派摄像头初始化 - 分辨率: {self.width}x{self.height}, FPS: {self.fps}")
    
    def start(self) -> bool:
        """启动摄像头"""
        try:
            self.camera = Picamera2()
            
            # 配置摄像头
            camera_config = self.camera.create_preview_configuration(
                main={"format": "RGB888", "size": (self.width, self.height)}
            )
            self.camera.configure(camera_config)
            
            # 设置帧率
            self.camera.set_controls({"FrameRate": self.fps})
            
            # 启动摄像头
            self.camera.start()
            self.is_running = True
            
            logger.info("树莓派摄像头启动成功")
            return True
            
        except Exception as e:
            logger.error(f"树莓派摄像头启动失败: {e}")
            return False
    
    def stop(self):
        """停止摄像头"""
        if self.camera and self.is_running:
            try:
                self.camera.stop()
                self.camera.close()
                self.is_running = False
                logger.info("树莓派摄像头已停止")
            except Exception as e:
                logger.error(f"停止树莓派摄像头失败: {e}")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取帧"""
        if not self.is_running or not self.camera:
            return False, None
        
        try:
            frame = self.camera.capture_array()
            return True, frame
        except Exception as e:
            logger.error(f"读取树莓派摄像头帧失败: {e}")
            return False, None
    
    def is_opened(self) -> bool:
        """检查摄像头是否打开"""
        return self.is_running and self.camera is not None
    
    def get_properties(self) -> dict:
        """获取摄像头属性"""
        return {
            'type': 'picamera',
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'is_running': self.is_running
        }


class USBCamera(CameraBase):
    """USB摄像头"""
    
    def __init__(self, config: dict):
        """
        初始化USB摄像头
        
        Args:
            config: 摄像头配置
        """
        self.config = config
        self.device_id = config.get('usb_device_id', 0)
        self.width = config.get('width', 1280)
        self.height = config.get('height', 720)
        self.fps = config.get('fps', 30)
        
        self.cap = None
        
        logger.info(f"USB摄像头初始化 - 设备ID: {self.device_id}, 分辨率: {self.width}x{self.height}")
    
    def start(self) -> bool:
        """启动摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                logger.error(f"无法打开USB摄像头设备 {self.device_id}")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # 设置缓冲区大小
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            logger.info("USB摄像头启动成功")
            return True
            
        except Exception as e:
            logger.error(f"USB摄像头启动失败: {e}")
            return False
    
    def stop(self):
        """停止摄像头"""
        if self.cap:
            try:
                self.cap.release()
                self.cap = None
                logger.info("USB摄像头已停止")
            except Exception as e:
                logger.error(f"停止USB摄像头失败: {e}")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取帧"""
        if not self.cap or not self.cap.isOpened():
            return False, None
        
        try:
            ret, frame = self.cap.read()
            return ret, frame
        except Exception as e:
            logger.error(f"读取USB摄像头帧失败: {e}")
            return False, None
    
    def is_opened(self) -> bool:
        """检查摄像头是否打开"""
        return self.cap is not None and self.cap.isOpened()
    
    def get_properties(self) -> dict:
        """获取摄像头属性"""
        properties = {
            'type': 'usb',
            'device_id': self.device_id,
            'width': self.width,
            'height': self.height,
            'fps': self.fps
        }
        
        if self.cap and self.cap.isOpened():
            properties.update({
                'actual_width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'actual_height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'actual_fps': self.cap.get(cv2.CAP_PROP_FPS)
            })
        
        return properties


class RTSPCamera(CameraBase):
    """RTSP网络摄像头"""
    
    def __init__(self, config: dict):
        """
        初始化RTSP摄像头
        
        Args:
            config: 摄像头配置
        """
        self.config = config
        self.rtsp_url = config.get('rtsp_url', '')
        self.width = config.get('width', 1280)
        self.height = config.get('height', 720)
        
        self.cap = None
        
        logger.info(f"RTSP摄像头初始化 - URL: {self.rtsp_url}")
    
    def start(self) -> bool:
        """启动摄像头"""
        try:
            if not self.rtsp_url:
                logger.error("RTSP URL未配置")
                return False
            
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            if not self.cap.isOpened():
                logger.error(f"无法连接RTSP流: {self.rtsp_url}")
                return False
            
            # 设置缓冲区大小
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            logger.info("RTSP摄像头启动成功")
            return True
            
        except Exception as e:
            logger.error(f"RTSP摄像头启动失败: {e}")
            return False
    
    def stop(self):
        """停止摄像头"""
        if self.cap:
            try:
                self.cap.release()
                self.cap = None
                logger.info("RTSP摄像头已停止")
            except Exception as e:
                logger.error(f"停止RTSP摄像头失败: {e}")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取帧"""
        if not self.cap or not self.cap.isOpened():
            return False, None
        
        try:
            ret, frame = self.cap.read()
            return ret, frame
        except Exception as e:
            logger.error(f"读取RTSP摄像头帧失败: {e}")
            return False, None
    
    def is_opened(self) -> bool:
        """检查摄像头是否打开"""
        return self.cap is not None and self.cap.isOpened()
    
    def get_properties(self) -> dict:
        """获取摄像头属性"""
        properties = {
            'type': 'rtsp',
            'rtsp_url': self.rtsp_url,
            'width': self.width,
            'height': self.height
        }
        
        if self.cap and self.cap.isOpened():
            properties.update({
                'actual_width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'actual_height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'actual_fps': self.cap.get(cv2.CAP_PROP_FPS)
            })
        
        return properties


class CameraManager:
    """
    摄像头管理器
    统一管理不同类型的摄像头
    """
    
    def __init__(self, config: dict):
        """
        初始化摄像头管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.camera_config = config.get('camera', {})
        
        # 摄像头类型
        self.camera_type = self.camera_config.get('type', 'usb')
        
        # 创建摄像头实例
        self.camera = self._create_camera()
        
        # 帧处理
        self.frame_queue = queue.Queue(maxlen=10)
        self.frame_callback = None
        
        # 线程管理
        self.capture_thread = None
        self.is_running = False
        self.lock = threading.Lock()
        
        # 统计信息
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.dropped_frames = 0
        
        logger.info(f"摄像头管理器初始化完成 - 类型: {self.camera_type}")
    
    def _create_camera(self) -> CameraBase:
        """创建摄像头实例"""
        if self.camera_type == 'picamera':
            if not PICAMERA_AVAILABLE:
                logger.warning("picamera2不可用，切换到USB摄像头")
                self.camera_type = 'usb'
                return USBCamera(self.camera_config)
            return PiCamera(self.camera_config)
        
        elif self.camera_type == 'usb':
            return USBCamera(self.camera_config)
        
        elif self.camera_type == 'rtsp':
            return RTSPCamera(self.camera_config)
        
        else:
            logger.warning(f"未知摄像头类型: {self.camera_type}，使用USB摄像头")
            return USBCamera(self.camera_config)
    
    def start(self, frame_callback: Optional[Callable] = None) -> bool:
        """
        启动摄像头
        
        Args:
            frame_callback: 帧处理回调函数
            
        Returns:
            是否启动成功
        """
        if self.is_running:
            logger.warning("摄像头已在运行")
            return True
        
        # 启动摄像头
        if not self.camera.start():
            logger.error("摄像头启动失败")
            return False
        
        # 设置回调函数
        self.frame_callback = frame_callback
        
        # 启动捕获线程
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.capture_thread.start()
        
        logger.info("摄像头管理器启动成功")
        return True
    
    def stop(self):
        """停止摄像头"""
        self.is_running = False
        
        # 等待捕获线程结束
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        
        # 停止摄像头
        self.camera.stop()
        
        # 清空队列
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("摄像头管理器已停止")
    
    def _capture_worker(self):
        """捕获工作线程"""
        logger.info("摄像头捕获线程已启动")
        
        while self.is_running:
            try:
                # 读取帧
                ret, frame = self.camera.read_frame()
                
                if not ret or frame is None:
                    logger.warning("读取帧失败")
                    time.sleep(0.1)
                    continue
                
                # 更新统计信息
                self._update_statistics()
                
                # 处理帧
                self._process_frame(frame)
                
            except Exception as e:
                logger.error(f"捕获线程异常: {e}")
                time.sleep(1)
        
        logger.info("摄像头捕获线程已停止")
    
    def _process_frame(self, frame: np.ndarray):
        """
        处理帧
        
        Args:
            frame: 图像帧
        """
        # 添加到队列
        try:
            self.frame_queue.put(frame, block=False)
        except queue.Full:
            # 队列满，丢弃最旧的帧
            try:
                self.frame_queue.get_nowait()
                self.frame_queue.put(frame, block=False)
                self.dropped_frames += 1
            except queue.Empty:
                pass
        
        # 调用回调函数
        if self.frame_callback:
            try:
                self.frame_callback(frame)
            except Exception as e:
                logger.error(f"帧回调函数异常: {e}")
    
    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        获取最新帧
        
        Args:
            timeout: 超时时间
            
        Returns:
            图像帧或None
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _update_statistics(self):
        """更新统计信息"""
        with self.lock:
            self.frame_count += 1
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
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'frame_count': self.frame_count,
                'current_fps': self.current_fps,
                'dropped_frames': self.dropped_frames,
                'queue_size': self.frame_queue.qsize(),
                'is_running': self.is_running,
                'camera_properties': self.camera.get_properties()
            }
    
    def is_opened(self) -> bool:
        """检查摄像头是否打开"""
        return self.camera.is_opened()
    
    def get_camera_info(self) -> dict:
        """获取摄像头信息"""
        return {
            'type': self.camera_type,
            'properties': self.camera.get_properties(),
            'is_opened': self.is_opened(),
            'is_running': self.is_running
        }
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        logger.info("摄像头管理器资源已清理")


if __name__ == "__main__":
    # 测试代码
    import yaml
    
    # 使用默认配置
    config = {
        'camera': {
            'type': 'usb',  # 或 'picamera', 'rtsp'
            'width': 1280,
            'height': 720,
            'fps': 30,
            'usb_device_id': 0
        }
    }
    
    def frame_callback(frame):
        """帧处理回调"""
        print(f"收到帧: {frame.shape}")
    
    # 创建摄像头管理器
    camera_manager = CameraManager(config)
    
    # 启动摄像头
    if camera_manager.start(frame_callback):
        print("摄像头启动成功")
        
        # 运行一段时间
        time.sleep(5)
        
        # 获取统计信息
        stats = camera_manager.get_statistics()
        print(f"统计信息: {stats}")
        
        # 获取摄像头信息
        info = camera_manager.get_camera_info()
        print(f"摄像头信息: {info}")
    
    # 清理资源
    camera_manager.cleanup()

