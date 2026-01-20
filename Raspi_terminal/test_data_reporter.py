#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试DataReporter模块
向FastAPI服务器上报模拟的交通数据
"""

import sys
import os
import time

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 导入DataReporter
from communication.data_reporter import DataReporter


def test_data_reporter():
    """测试DataReporter模块"""
    print("开始测试DataReporter模块...")
    
    # 配置
    config = {
        'server': {
            'base_url': 'http://localhost:8000',  # 本地FastAPI服务器地址
            'timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 5,
            'report_interval': 5,
            'batch_size': 100,
            'api_endpoints': {
                'traffic_update': '/api/traffic_update',
                'health_check': '/health'
            }
        },
        'system': {
            'intersection_id': 'TEST_001',
            'location': 'Test Location'
        }
    }
    
    # 创建DataReporter实例
    reporter = DataReporter(config)
    
    # 启动DataReporter
    reporter.start()
    print("DataReporter启动成功")
    
    # 等待一段时间，让健康检查线程运行
    time.sleep(2)
    
    # 检查服务器连接状态
    status = reporter.get_status()
    print(f"服务器连接状态: {'正常' if status['connection_status'] else '异常'}")
    
    # 模拟交通数据
    test_traffic_data = {
        'total_vehicles': 15,
        'zone_counts': {
            'north_lane': 4,
            'south_lane': 3,
            'east_lane': 5,
            'west_lane': 3
        },
        'average_speed': 28.5,
        'vehicle_types': {
            'car': 12,
            'truck': 3
        }
    }
    
    # 上报数据
    print("上报模拟交通数据...")
    success = reporter.report_traffic_data(test_traffic_data)
    print(f"数据上报结果: {'成功' if success else '失败'}")
    
    # 等待一段时间，让上报线程运行
    time.sleep(10)
    
    # 再次检查状态
    status = reporter.get_status()
    print("\nDataReporter状态:")
    print(f"  总上报次数: {status['total_reports']}")
    print(f"  失败次数: {status['failed_reports']}")
    print(f"  成功率: {status['success_rate']:.1f}%")
    print(f"  队列大小: {status['queue_size']}")
    print(f"  失败队列大小: {status['failed_queue_size']}")
    
    # 清理资源
    reporter.cleanup()
    print("\n测试完成，资源已清理")


if __name__ == "__main__":
    test_data_reporter()
