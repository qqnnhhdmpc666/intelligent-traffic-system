"""
系统管理API路由
包括健康检查、系统统计等
"""

from fastapi import APIRouter, HTTPException
import time
import psutil
import os
from datetime import datetime
import logging

from models import HealthResponse, SystemInfo, SystemStats

router = APIRouter()
logger = logging.getLogger(__name__)

# 服务器启动时间
_server_start_time = time.time()

@router.get("/", response_model=SystemInfo)
async def root():
    """根路径 - 系统信息"""
    return SystemInfo()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        # 获取进程信息
        process = psutil.Process(os.getpid())
        uptime = time.time() - process.create_time()

        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            uptime=uptime
        )

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="健康检查失败")

@router.get("/api/system_stats", response_model=SystemStats)
async def get_system_stats():
    """
    获取系统统计信息

    包括路网状态、系统负载等
    """
    try:
        from database import SessionLocal
        from models import RoadNetwork

        db = SessionLocal()
        try:
            # 获取道路统计
            roads = db.query(RoadNetwork).all()

            total_roads = len(roads)
            total_capacity = total_roads * 100  # 简化计算
            total_flow = sum(int(road.current_congestion * 10) for road in roads)
            congested_roads = sum(1 for road in roads if road.current_congestion > 50)
            average_load_factor = sum(road.current_congestion / 100.0 for road in roads) / total_roads if total_roads > 0 else 0

            # 获取图的节点数量
            try:
                from core.graph import Graph
                graph = Graph.from_database()
                total_nodes = len(graph.nodes)
            except Exception as e:
                print(f"获取节点数量失败: {e}")
                total_nodes = 0

            # 系统资源信息
            try:
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent(interval=0.1)

                system_stats = SystemStats(
                    total_nodes=total_nodes,
                    total_roads=total_roads,
                    total_capacity=total_capacity,
                    total_flow=total_flow,
                    average_load_factor=round(average_load_factor, 3),
                    congested_roads=congested_roads,
                    thread_pool_stats={
                        "max_workers": 10,
                        "running_tasks": 0,
                        "pending_tasks": 0,
                        "total_submitted": 0,
                        "total_completed": 0,
                        "total_failed": 0,
                        "total_tasks": 0,
                        "queue_size": 0
                    },
                    log_stats={
                        "log_dir": "./logs",
                        "total_files": 0,
                        "total_size": 0,
                        "files": []
                    }
                )

            except ImportError:
                # 如果没有psutil，使用简化版本
                system_stats = SystemStats(
                    total_nodes=total_nodes,
                    total_roads=total_roads,
                    total_capacity=total_capacity,
                    total_flow=total_flow,
                    average_load_factor=round(average_load_factor, 3),
                    congested_roads=congested_roads
                )

            logger.info(f"获取系统统计: {total_nodes}节点, {total_roads}道路")

            return system_stats

        finally:
            db.close()

    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.get("/api/thread_stats")
async def get_thread_stats():
    """获取线程池统计信息"""
    # 简化实现，返回固定数据
    return {
        "max_workers": 10,
        "running_tasks": 0,
        "pending_tasks": 0,
        "total_submitted": 0,
        "total_completed": 0,
        "total_failed": 0,
        "total_tasks": 0,
        "queue_size": 0
    }

@router.get("/api/log_stats")
async def get_log_stats():
    """获取日志统计信息"""
    try:
        log_dir = "./logs"
        if not os.path.exists(log_dir):
            return {
                "log_dir": log_dir,
                "total_files": 0,
                "total_size": 0,
                "files": []
            }

        total_files = 0
        total_size = 0
        files = []

        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)
                size = os.path.getsize(filepath)
                total_files += 1
                total_size += size
                files.append({
                    "name": filename,
                    "size": size,
                    "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })

        return {
            "log_dir": log_dir,
            "total_files": total_files,
            "total_size": total_size,
            "files": files
        }

    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        return {
            "log_dir": "./logs",
            "error": str(e),
            "total_files": 0,
            "total_size": 0,
            "files": []
        }