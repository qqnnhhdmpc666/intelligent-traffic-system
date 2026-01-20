"""
导入示例路网数据脚本
用于向数据库中添加示例道路网络数据
"""

import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, SessionLocal
from models import RoadNetwork

def import_sample_road_data():
    """导入示例道路数据"""
    # 初始化数据库
    init_database()
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 检查是否已有数据
        existing_roads = db.query(RoadNetwork).count()
        if existing_roads > 0:
            print(f"数据库中已有 {existing_roads} 条道路数据，跳过导入")
            return
        
        # 示例道路数据
        sample_roads = [
            {
                "road_id": "road_1",
                "start_point": "A",
                "end_point": "B",
                "length": 1.2,
                "current_congestion": 30.0,
                "max_speed": 60.0
            },
            {
                "road_id": "road_2",
                "start_point": "B",
                "end_point": "C",
                "length": 0.8,
                "current_congestion": 20.0,
                "max_speed": 50.0
            },
            {
                "road_id": "road_3",
                "start_point": "A",
                "end_point": "C",
                "length": 2.0,
                "current_congestion": 40.0,
                "max_speed": 70.0
            },
            {
                "road_id": "road_4",
                "start_point": "C",
                "end_point": "D",
                "length": 1.5,
                "current_congestion": 25.0,
                "max_speed": 60.0
            },
            {
                "road_id": "road_5",
                "start_point": "B",
                "end_point": "D",
                "length": 1.8,
                "current_congestion": 35.0,
                "max_speed": 55.0
            }
        ]
        
        # 添加数据到数据库
        for road_data in sample_roads:
            road = RoadNetwork(**road_data)
            db.add(road)
        
        # 提交更改
        db.commit()
        
        print(f"成功导入 {len(sample_roads)} 条示例道路数据")
        print("路网数据已准备就绪，可以测试路径规划API了")
        
    except Exception as e:
        print(f"导入数据时出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("开始导入示例路网数据...")
    import_sample_road_data()
    print("导入完成！")
