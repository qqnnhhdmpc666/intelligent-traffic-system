import requests
import json
import time

def test_raspberry_pi_to_fastapi():
    """测试Raspberry Pi → FastAPI数据上报"""
    print("=== 测试 Raspberry Pi → FastAPI 数据上报 ===")
    url = "http://localhost:8000/api/traffic_update"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    data = {
        "intersection_id": "raspi_001",
        "timestamp": timestamp,
        "location": "A",
        "roads": [
            {
                "road_id": "A_B",
                "vehicle_count": 5,
                "average_speed": 25.5,
                "congestion_level": "medium",
                "timestamp": timestamp
            }
        ],
        "summary": {
            "total_vehicles": 5,
            "vehicle_types": {
                "car": 5
            },
            "average_speed": 25.5,
            "data_quality": "good"
        }
    }
    response = requests.post(url, json=data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), indent=2)}")
    print()

def test_fastapi_to_android():
    """测试FastAPI → Android路径规划响应"""
    print("=== 测试 FastAPI → Android 路径规划响应 ===")
    url = "http://localhost:8000/api/request_path"
    test_cases = [
        {"start_node": "A", "end_node": "Y", "vehicle_type": "normal"},
        {"start_node": "B", "end_node": "X", "vehicle_type": "normal"},
        {"start_node": "C", "end_node": "W", "vehicle_type": "emergency"}
    ]
    
    for i, case in enumerate(test_cases):
        print(f"测试用例 {i+1}: {case['start_node']} → {case['end_node']} ({case['vehicle_type']})")
        response = requests.post(url, json=case)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2)}")
        print()

def test_node_list():
    """测试获取节点列表"""
    print("=== 测试获取节点列表 ===")
    url = "http://localhost:8000/api/nodes"
    response = requests.get(url)
    print(f"响应状态码: {response.status_code}")
    nodes_data = response.json()
    # 检查返回格式
    if isinstance(nodes_data, dict):
        if 'nodes' in nodes_data:
            nodes = nodes_data['nodes']
            count = nodes_data.get('count', len(nodes))
            print(f"节点数量: {count}")
            print(f"节点列表: {nodes}")
        else:
            print(f"响应内容: {nodes_data}")
    else:
        print(f"响应内容: {nodes_data}")
    print()

def test_road_list():
    """测试获取道路列表"""
    print("=== 测试获取道路列表 ===")
    url = "http://localhost:8000/api/roads"
    response = requests.get(url)
    print(f"响应状态码: {response.status_code}")
    roads_data = response.json()
    # 检查返回格式
    if isinstance(roads_data, dict):
        if 'roads' in roads_data:
            roads = roads_data['roads']
            print(f"道路数量: {len(roads)}")
            print(f"前5条道路: {roads[:5]}")
        else:
            print(f"响应内容: {roads_data}")
    else:
        print(f"响应内容: {roads_data}")
    print()

if __name__ == "__main__":
    print("🚀 智慧交通调度系统端到端测试")
    print("=" * 60)
    
    try:
        test_node_list()
        test_road_list()
        test_raspberry_pi_to_fastapi()
        test_fastapi_to_android()
        print("✅ 端到端测试完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        print("=" * 60)
