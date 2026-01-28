"""
路径规划API路由
复用现有的路径规划算法
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import time
import logging

from models import PathRequest, PathResponse

# 导入本地算法实现
from core.graph import Graph
from core.pathfinding import Dijkstra, YensKShortestPaths, SoftmaxSelector
from core.route_planner import RoutePlanner

router = APIRouter()
logger = logging.getLogger(__name__)

# 全局路由规划器实例
route_planner = None

def get_route_planner():
    """获取路由规划器实例"""
    global route_planner
    if route_planner is None:
        route_planner = RoutePlanner()
    return route_planner

@router.post("/api/request_path", response_model=PathResponse)
async def request_path(data: PathRequest):
    """
    同步路径规划接口

    使用论文实现的完整算法（D-KSPP）进行路径规划
    """
    try:
        start_time = time.time()

        logger.info(f"开始路径规划: {data.start_node} -> {data.end_node}, 类型: {data.vehicle_type}")

        planner = get_route_planner()
        result = planner.plan_route(data.start_node, data.end_node, data.vehicle_type)

        processing_time = time.time() - start_time

        if not result.get('path'):
            raise HTTPException(
                status_code=400,
                detail=result.get('message', '路径规划失败')
            )

        # 构造响应
        response = PathResponse(
            path=result['path'],
            weight=result['weight'],
            distance=result.get('distance', 0),
            duration=result.get('duration', 0),
            congestion=result.get('congestion', 0),
            message=result.get('message', '成功'),
            all_paths=result.get('all_paths', None)
        )

        logger.info(f"路径规划完成: {len(result['path'])}个节点, 耗时: {processing_time:.3f}s")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"路径规划异常: {e}")
        raise HTTPException(status_code=500, detail=f"路径规划失败: {str(e)}")

@router.get("/api/nodes")
async def get_nodes():
    """
    获取路网节点列表
    """
    try:
        planner = get_route_planner()

        # 获取图中的所有节点
        graph = planner.graph_cache.get_graph()
        nodes = list(graph.nodes) if graph else []

        logger.info(f"获取节点列表: {len(nodes)}个节点")

        return {
            "nodes": sorted(nodes),
            "count": len(nodes)
        }

    except Exception as e:
        logger.error(f"获取节点列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取节点失败: {str(e)}")

@router.get("/api/roads")
async def get_roads():
    """
    获取路网道路列表及其状态
    """
    try:
        planner = get_route_planner()
        
        # 获取图中的所有边
        graph = planner.graph_cache.get_graph()
        
        roads_data = []
        
        if graph:
            for (from_node, to_node), edge_data in graph.edges.items():
                road_data = {
                    'from': from_node,
                    'to': to_node,
                    'weight': edge_data.get('weight', 0),
                    'capacity': 100,  # 默认容量
                    'flow': int(edge_data.get('current_congestion', 0) * 10),  # 简化为拥堵度*10
                    'load_factor': edge_data.get('current_congestion', 0) / 100.0 if edge_data.get('current_congestion', 0) > 0 else 0,
                    'length': edge_data.get('length', 0),
                    'max_speed': edge_data.get('max_speed', 60),
                    'current_congestion': edge_data.get('current_congestion', 0)
                }
                roads_data.append(road_data)

        logger.info(f"获取道路列表: {len(roads_data)}条道路")

        return {"roads": roads_data}

    except Exception as e:
        logger.error(f"获取道路列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取道路失败: {str(e)}")