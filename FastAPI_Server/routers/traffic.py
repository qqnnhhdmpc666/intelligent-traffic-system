"""
交通数据API路由
处理TrafficVisionSystem的数据上报
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from database import get_db
from models import (
    TrafficRecord, TrafficUpdateRequest, TrafficUpdateResponse,
    TrafficRecord as TrafficRecordDB
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/traffic_update", response_model=TrafficUpdateResponse)
async def traffic_update(
    data: TrafficUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    TrafficVisionSystem交通数据更新接口

    接收路口检测到的交通数据并保存到数据库
    """
    try:
        logger.info(f"接收到路口 {data.intersection_id} 的交通数据更新")

        saved_records = 0

        # 处理每条道路的数据
        for road in data.roads:
            record = TrafficRecordDB(
                terminal_id=data.intersection_id,
                direction=road.road_id,
                timestamp=datetime.fromisoformat(data.timestamp.replace('Z', '+00:00')),
                location=data.location,
                vehicle_count=road.vehicle_count,
                average_speed=road.average_speed,
                congestion_level=road.congestion_level
            )
            db.add(record)
            saved_records += 1

            # 更新RoadNetwork中的拥堵信息（如果存在对应道路）
            try:
                from models import RoadNetwork
                road_network = db.query(RoadNetwork).filter(
                    RoadNetwork.start_point.contains({"node_id": road.road_id.split('_')[0]})
                ).first()

                if road_network:
                    # 根据vehicle_count估算拥堵度 (0-100)
                    congestion_value = min(road.vehicle_count * 2, 100)
                    road_network.current_congestion = congestion_value
                    road_network.updated_at = datetime.utcnow()
                    logger.debug(f"更新道路 {road.road_id} 拥堵度: {congestion_value}")

            except Exception as e:
                logger.warning(f"更新道路拥堵信息失败: {e}")
                # 不影响主要数据保存流程

        # 提交事务
        db.commit()

        logger.info(f"成功保存 {saved_records} 条交通记录")

        return TrafficUpdateResponse(
            message=f"成功保存 {saved_records} 条交通数据",
            records_saved=saved_records,
            intersection_id=data.intersection_id,
            timestamp=data.timestamp
        )

    except Exception as e:
        db.rollback()
        logger.error(f"交通数据更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据保存失败: {str(e)}")

@router.get("/api/traffic/")
async def get_traffic_data(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取交通数据历史记录

    Args:
        limit: 返回记录数量限制，默认100条

    Returns:
        交通数据列表
    """
    try:
        records = db.query(TrafficRecordDB).order_by(
            TrafficRecordDB.timestamp.desc()
        ).limit(limit).all()

        data = [{
            'id': record.id,
            'terminal_id': record.terminal_id,
            'vehicle_type': record.vehicle_type,
            'direction': record.direction,
            'timestamp': record.timestamp.isoformat(),
            'location': record.location,
            'vehicle_count': record.vehicle_count,
            'average_speed': record.average_speed,
            'congestion_level': record.congestion_level
        } for record in records]

        return {"data": data, "count": len(data)}

    except Exception as e:
        logger.error(f"获取交通数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")