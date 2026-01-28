"""
数据模型定义
包含Pydantic模型和SQLAlchemy模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

Base = declarative_base()

# SQLAlchemy 数据库模型

class TrafficRecord(Base):
    """交通记录表"""
    __tablename__ = "traffic_records"

    id = Column(Integer, primary_key=True, index=True)
    terminal_id = Column(String(50), index=True)  # 路口ID
    vehicle_type = Column(String(20), default="mixed")  # 车辆类型
    direction = Column(String(50), default="unknown")  # 方向/道路ID
    timestamp = Column(DateTime, default=datetime.utcnow)  # 时间戳
    location = Column(String(100), default="Unknown")  # 位置描述
    vehicle_count = Column(Integer, default=0)  # 车辆数量
    average_speed = Column(Float, default=0.0)  # 平均速度
    congestion_level = Column(String(20), default="low")  # 拥堵等级

class RoadNetwork(Base):
    """道路网络表"""
    __tablename__ = "road_network"

    id = Column(Integer, primary_key=True, index=True)
    road_id = Column(String(50), unique=True, index=True)
    start_point = Column(JSON)  # 起点节点
    end_point = Column(JSON)    # 终点节点
    length = Column(Float, default=0.0)  # 道路长度(km)
    current_congestion = Column(Float, default=0.0)  # 当前拥堵延时
    max_speed = Column(Float)  # 最高时速(km/h)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RouteCache(Base):
    """路径缓存表"""
    __tablename__ = "route_cache"

    id = Column(Integer, primary_key=True, index=True)
    start_point = Column(JSON)
    end_point = Column(JSON)
    optimal_path = Column(JSON)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

# Pydantic 请求/响应模型

class RoadData(BaseModel):
    """道路数据模型"""
    road_id: str
    vehicle_count: int = 0
    average_speed: float = 0.0
    congestion_level: str = "low"
    timestamp: str

class TrafficSummary(BaseModel):
    """交通汇总数据"""
    total_vehicles: int = 0
    vehicle_types: Dict[str, int] = {}
    average_speed: float = 0.0
    data_quality: str = "good"

class TrafficUpdateRequest(BaseModel):
    """TrafficVisionSystem交通数据更新请求"""
    intersection_id: str
    location: str = "Unknown"
    timestamp: str
    roads: List[RoadData]
    summary: TrafficSummary

class TrafficUpdateResponse(BaseModel):
    """交通数据更新响应"""
    message: str
    records_saved: int
    intersection_id: str
    timestamp: str

class PathRequest(BaseModel):
    """路径规划请求"""
    start_node: str
    end_node: str
    vehicle_type: str = "normal"

class PathDetail(BaseModel):
    """路径详细信息"""
    path: List[str]
    weight: float
    distance: float
    duration: float
    congestion: float
    probability: float
    rank: int
    label: Optional[str] = None

class PathResponse(BaseModel):
    """路径规划响应"""
    path: List[str]
    weight: float
    distance: float
    duration: float
    congestion: float
    message: str
    all_paths: Optional[List[PathDetail]] = None

class NodeInfo(BaseModel):
    """节点信息"""
    id: str
    x: int
    y: int
    node_type: str = "intersection"

class RoadInfo(BaseModel):
    """道路信息"""
    id: str
    start_node: str
    end_node: str
    length: float
    weight: float
    capacity: int = 100
    flow: int = 0
    load_factor: float = 0.0

class SystemStats(BaseModel):
    """系统统计信息"""
    total_nodes: int
    total_roads: int
    total_capacity: int
    total_flow: int
    average_load_factor: float
    congested_roads: int
    thread_pool_stats: Dict[str, Any] = {
        "max_workers": 10,
        "running_tasks": 0,
        "pending_tasks": 0,
        "total_submitted": 0,
        "total_completed": 0,
        "total_failed": 0,
        "total_tasks": 0,
        "queue_size": 0
    }
    log_stats: Dict[str, Any] = {
        "log_dir": "/var/log",
        "total_files": 0,
        "total_size": 0,
        "files": []
    }

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    timestamp: str
    uptime: float

class SystemInfo(BaseModel):
    """系统信息"""
    message: str = "智慧交通调度系统"
    version: str = "2.0.0"
    status: str = "running"