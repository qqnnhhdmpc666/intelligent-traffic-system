# 智慧交通调度系统

基于边缘计算与云协同的智能交通调度系统，采用D-KSPP算法实现动态路径规划，在拥堵场景下效率提升超过5%。

## 项目简介

本项目是一个完整的智慧交通调度系统，采用边缘计算与云协同架构，实现实时交通监控、拥堵检测和智能路径规划。系统包含三个核心组件：

- **FastAPI后端服务**：基于FastAPI的轻量级API服务器，实现D-KSPP路径规划算法
- **树莓派边缘节点**：基于YOLOv8的车辆检测与数据采集系统
- **Java桌面客户端**：可视化监控与路径规划客户端

### 核心技术

- **D-KSPP算法**：结合Dijkstra最短路径、Yen's K短路算法和Softmax选择机制
- **动态拥堵感知**：实时分析道路拥堵状况，动态调整路径规划策略
- **边缘计算架构**：树莓派边缘节点进行本地车辆检测，降低云端计算压力
- **YOLOv8目标检测**：轻量级深度学习模型，在树莓派上实现实时车辆识别

### 性能指标

- **拥堵场景效率提升**：重度拥堵场景下效率提升5.15%
- **算法响应时间**：平均响应时间<100ms
- **车辆检测准确率**：YOLOv8模型准确率>90%
- **系统并发能力**：支持多节点并发数据上报

## 系统架构

```
智慧交通调度系统
├── FastAPI_Server/          # 云端API服务器
│   ├── core/               # 核心算法模块
│   │   ├── route_planner.py    # D-KSPP路径规划算法
│   │   ├── pathfinding.py      # 路径查找算法（Dijkstra、Yen's K短路）
│   │   └── graph.py            # 图数据结构
│   ├── routers/            # API路由
│   │   ├── planning.py        # 路径规划API
│   │   ├── traffic.py         # 交通数据API
│   │   └── system.py          # 系统管理API
│   ├── experiments/         # 实验模块
│   │   └── congestion_experiment.py  # 拥堵场景实验
│   └── main.py              # FastAPI应用入口
├── Raspi_terminal/          # 树莓派边缘节点
│   ├── src/                # 源代码
│   │   ├── detection/          # 车辆检测模块
│   │   ├── tracking/           # 车辆追踪模块
│   │   ├── communication/      # 数据上报模块
│   │   └── camera/             # 摄像头管理模块
│   ├── models/             # YOLOv8模型
│   └── config/             # 配置文件
└── JavaDesktopClient/       # Java桌面客户端
    └── TrafficClient.java  # 客户端主程序
```

## 安装说明

### 环境要求

- **Python**: 3.9+
- **Java**: 11+（用于桌面客户端）
- **树莓派**: Raspberry Pi 4B/5（用于边缘节点）
- **操作系统**: Windows/Linux/macOS

### 1. 安装FastAPI后端服务

```bash
cd FastAPI_Server
pip install -r requirements.txt
```

### 2. 安装树莓派边缘节点

在树莓派上执行：

```bash
cd Raspi_terminal
pip install -r requirements.txt
```

### 3. 编译Java桌面客户端

```bash
cd JavaDesktopClient
javac TrafficClient.java
java TrafficClient
```

## 使用指南

### 启动FastAPI后端服务

```bash
cd FastAPI_Server
python main.py
```

服务启动后访问：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 启动树莓派边缘节点

在树莓派上执行：

```bash
cd Raspi_terminal
python src/main.py
```

### 运行拥堵场景实验

```bash
cd FastAPI_Server
python experiments/congestion_experiment.py
```

### 使用Java桌面客户端

```bash
cd JavaDesktopClient
java TrafficClient
```

## API接口

### 路径规划接口

```bash
POST /api/request_path
Content-Type: application/json

{
  "start_node": "A",
  "end_node": "B",
  "vehicle_type": "normal"
}
```

### 交通数据上报接口

```bash
POST /api/traffic_update
Content-Type: application/json

{
  "intersection_id": "raspi-2024",
  "roads": [{
    "road_id": "road_north",
    "vehicle_count": 5,
    "average_speed": 25.5,
    "congestion_level": "medium"
  }]
}
```

### 系统状态查询接口

```bash
GET /api/system_stats
```

## D-KSPP算法说明

### 算法原理

D-KSPP算法结合了三种核心算法：

1. **Dijkstra最短路径算法**：计算基础最短路径
2. **Yen's K短路算法**：生成K条备选路径
3. **Softmax选择机制**：基于拥堵状况智能选择最优路径

### 核心参数

- `K_SHORTEST_PATHS = 25`：K短路算法的K值
- `SOFTMAX_TEMPERATURE = 0.08`：Softmax温度系数
- `WEIGHT_ALPHA = 0.1`：路径长度权重系数
- `WEIGHT_BETA = 0.9`：拥堵状况权重系数

### 路径选择策略

算法综合考虑以下因素：
- 拥堵惩罚：拥堵度越高，惩罚越大
- 路径长度惩罚：路径越长，惩罚越大
- 时间邻近性奖励：优先选择时间上更接近的路径
- 拥堵奖励：在拥堵场景下给予额外奖励

## 实验结果

### 拥堵场景性能对比

| 拥堵场景 | SP算法时间(s) | D-KSPP算法时间(s) | 时间改进(%) | SP算法效率 | D-KSPP算法效率 | 效率改进(%) |
|---------|--------------|------------------|------------|-----------|---------------|------------|
| 轻度拥堵 | 0.12 | 0.11 | 8.33 | 0.083333 | 0.090909 | 9.09 |
| 中度拥堵 | 0.15 | 0.14 | 6.67 | 0.066667 | 0.071429 | 7.14 |
| 重度拥堵 | 0.18 | 0.17 | 5.56 | 0.055556 | 0.058824 | 5.88 |
| 极端拥堵 | 0.22 | 0.21 | 4.55 | 0.045455 | 0.047619 | 4.76 |





---

*最后更新：2026-01-28*
