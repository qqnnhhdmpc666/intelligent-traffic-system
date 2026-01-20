#!/usr/bin/env python3
"""
初始化5x5网格路网数据
为智慧交通调度系统添加完整的5x5网格节点和道路数据
"""

import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库相关模块
from database import engine, Base, SessionLocal
from models import RoadNetwork


def init_5x5_grid():
    """
    初始化5x5网格路网数据
    创建25个节点和相应的道路
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("📋 数据库表创建完成")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 生成5x5网格的节点ID（A-Y）
        nodes = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y"]
        
        # 计算节点在网格中的位置
        node_positions = {}
        for i in range(5):
            for j in range(5):
                index = i * 5 + j
                node_positions[nodes[index]] = (i, j)
        
        # 清除现有的道路数据
        existing_roads = db.query(RoadNetwork).all()
        for road in existing_roads:
            db.delete(road)
        db.commit()
        print("🧹 清除现有道路数据完成")
        
        # 创建道路数据
        roads = []
        road_id = 1
        
        # 创建水平道路（每行5个节点，4条道路）
        for row in range(5):
            for col in range(4):
                start_index = row * 5 + col
                end_index = row * 5 + (col + 1)
                start_node = nodes[start_index]
                end_node = nodes[end_index]
                
                # 创建正向道路
                road = RoadNetwork(
                    road_id=f"road_h_{row}_{col}",
                    start_point=start_node,
                    end_point=end_node,
                    length=1.0,  # 1公里
                    current_congestion=0.0,
                    max_speed=60.0  # 60 km/h
                )
                roads.append(road)
                road_id += 1
                
                # 创建反向道路
                road_reverse = RoadNetwork(
                    road_id=f"road_h_{row}_{col}_reverse",
                    start_point=end_node,
                    end_point=start_node,
                    length=1.0,  # 1公里
                    current_congestion=0.0,
                    max_speed=60.0  # 60 km/h
                )
                roads.append(road_reverse)
                road_id += 1
        
        # 创建垂直道路（每列5个节点，4条道路）
        for col in range(5):
            for row in range(4):
                start_index = row * 5 + col
                end_index = (row + 1) * 5 + col
                start_node = nodes[start_index]
                end_node = nodes[end_index]
                
                # 创建正向道路
                road = RoadNetwork(
                    road_id=f"road_v_{row}_{col}",
                    start_point=start_node,
                    end_point=end_node,
                    length=1.0,  # 1公里
                    current_congestion=0.0,
                    max_speed=60.0  # 60 km/h
                )
                roads.append(road)
                road_id += 1
                
                # 创建反向道路
                road_reverse = RoadNetwork(
                    road_id=f"road_v_{row}_{col}_reverse",
                    start_point=end_node,
                    end_point=start_node,
                    length=1.0,  # 1公里
                    current_congestion=0.0,
                    max_speed=60.0  # 60 km/h
                )
                roads.append(road_reverse)
                road_id += 1
        
        # 批量添加道路数据
        db.bulk_save_objects(roads)
        db.commit()
        
        print(f"✅ 5x5网格路网数据初始化完成")
        print(f"📊 生成的道路数据:")
        print(f"   • 总节点数: {len(nodes)}")
        print(f"   • 总道路数: {len(roads)}")
        print(f"   • 水平道路: {5 * 4 * 2} 条")  # 每行4条，5行，双向
        print(f"   • 垂直道路: {5 * 4 * 2} 条")  # 每列4条，5列，双向
        print(f"   • 道路总长度: {len(roads) * 1.0} 公里")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 开始初始化5x5网格路网数据")
    print("=" * 50)
    init_5x5_grid()
    print("=" * 50)
    print("🎉 5x5网格路网数据初始化完成")
    print("\n📝 后续操作:")
    print("   1. 启动FastAPI服务器: python start_fastapi.py")
    print("   2. 运行测试脚本: python 终极版终极_大规模拥堵场景测试.py")
    print("   3. 查看API文档: http://localhost:8000/docs")
