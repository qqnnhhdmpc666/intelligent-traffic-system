# 路口车流识别系统 (TrafficVisionSystem)

基于Raspberry Pi 5和YOLOv8n的智能交通监控系统，实现实时车辆检测、跟踪和交通数据上报。

**🚨 更新说明**: 此系统已完全替换原有的Raspi_terminal项目，提供更完善的功能和更好的性能。

## 🚀 系统特色

### 🎯 核心功能
- **实时车辆检测**: 基于YOLOv8n模型，支持多种车辆类型识别
- **智能车辆跟踪**: 多目标跟踪算法，准确统计车流量
- **数据实时上报**: 自动向服务器上报交通统计数据
- **多摄像头支持**: 支持树莓派摄像头、USB摄像头和RTSP网络摄像头
- **系统监控**: 实时监控系统资源使用情况和性能指标

### 🔧 技术亮点
- **轻量化设计**: 专为Raspberry Pi 5优化，低功耗高效率
- **模块化架构**: 清晰的分层设计，便于维护和扩展
- **智能告警**: 自动检测系统异常并发出告警
- **灵活配置**: 支持YAML配置文件，易于定制
- **完善日志**: 详细的日志记录和轮转管理

## 📁 项目结构

```
TrafficVisionSystem/
├── src/                          # 源代码目录
│   ├── detection/                # 车辆检测模块
│   │   └── vehicle_detector.py   # YOLOv8车辆检测器
│   ├── tracking/                 # 车辆跟踪模块
│   │   └── vehicle_tracker.py    # 多目标跟踪器
│   ├── communication/            # 通信模块
│   │   └── data_reporter.py      # 数据上报器
│   ├── camera/                   # 摄像头管理模块
│   │   └── camera_manager.py     # 摄像头管理器
│   ├── monitoring/               # 系统监控模块
│   │   └── system_monitor.py     # 系统监控器
│   └── main.py                   # 主程序入口
├── config/                       # 配置文件目录
│   └── config.yaml               # 系统配置文件
├── scripts/                      # 脚本目录
│   ├── install.sh                # 安装脚本
│   └── start.sh                  # 启动脚本
├── models/                       # 模型文件目录
├── logs/                         # 日志文件目录
├── data/                         # 数据目录
│   ├── recordings/               # 录像文件
│   └── debug/                    # 调试数据
├── requirements.txt              # Python依赖
└── README.md                     # 项目说明
```

## 🛠️ 安装部署

### 系统要求

- **硬件**: Raspberry Pi 5 (推荐8GB内存版本)
- **操作系统**: Raspberry Pi OS (64-bit) 或 Ubuntu 22.04+
- **Python**: 3.8+
- **摄像头**: 树莓派摄像头、USB摄像头或RTSP网络摄像头
- **网络**: 稳定的网络连接用于数据上报

### 快速安装

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd TrafficVisionSystem
   ```

2. **运行安装脚本**
   ```bash
   chmod +x scripts/install.sh
   ./scripts/install.sh
   ```

3. **配置系统**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # 编辑配置文件，设置服务器地址、摄像头类型等
   nano config/config.yaml
   ```

4. **启动系统**
   ```bash
   ./scripts/start.sh
   ```

### 手动安装

如果自动安装脚本失败，可以手动安装：

1. **更新系统**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **安装系统依赖**
   ```bash
   sudo apt install -y python3-dev python3-pip python3-venv
   sudo apt install -y libopencv-dev python3-opencv
   sudo apt install -y build-essential cmake pkg-config
   ```

3. **创建虚拟环境**
   ```bash
   python3 -m venv ~/traffic_vision_env
   source ~/traffic_vision_env/bin/activate
   ```

4. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **下载模型**
   ```bash
   mkdir -p models
   wget -O models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
   ```

## ⚙️ 配置说明

### 主要配置项

```yaml
# 系统基本信息
system:
  name: "TrafficVisionSystem"
  version: "1.0.0"
  intersection_id: "INTERSECTION_001"  # 路口ID
  location: "Main Street & First Ave"   # 路口位置

# 服务器配置
server:
  base_url: "http://120.53.28.58:3389"  # 服务器地址
  timeout: 30                           # 请求超时时间
  report_interval: 10                   # 数据上报间隔(秒)

# 摄像头配置
camera:
  type: "usb"                          # 摄像头类型: usb/picamera/rtsp
  width: 1280                          # 图像宽度
  height: 720                          # 图像高度
  fps: 30                              # 帧率
  usb_device_id: 0                     # USB摄像头设备ID

# 检测配置
detection:
  model_path: "./models/yolov8n.pt"    # 模型文件路径
  device: "cpu"                        # 推理设备: cpu/cuda
  confidence_threshold: 0.5            # 置信度阈值
  target_classes: [2, 3, 5, 7]        # 目标类别(车辆类型)

# 监控配置
monitoring:
  enable_system_monitor: true          # 启用系统监控
  monitor_interval: 30                 # 监控间隔(秒)
  alerts:
    high_cpu_threshold: 80             # CPU使用率告警阈值
    high_memory_threshold: 85          # 内存使用率告警阈值
    high_temperature_threshold: 70     # 温度告警阈值
```

### 摄像头配置

#### USB摄像头
```yaml
camera:
  type: "usb"
  usb_device_id: 0  # 通常是0，如果有多个摄像头可能是1、2等
```

#### 树莓派摄像头
```yaml
camera:
  type: "picamera"
  # 树莓派摄像头会自动检测，无需额外配置
```

#### RTSP网络摄像头
```yaml
camera:
  type: "rtsp"
  rtsp_url: "rtsp://username:password@192.168.1.100:554/stream"
```

## 🚀 使用方法

### 基本使用

1. **启动系统**
   ```bash
   ./scripts/start.sh
   ```

2. **后台运行**
   ```bash
   ./scripts/start.sh --daemon
   ```

3. **使用自定义配置**
   ```bash
   ./scripts/start.sh --config my_config.yaml
   ```

4. **测试模式**
   ```bash
   ./scripts/start.sh --test
   ```

### 系统管理

1. **检查系统状态**
   ```bash
   ./scripts/start.sh --status
   ```

2. **停止系统**
   ```bash
   ./scripts/start.sh --stop
   ```

3. **检查环境**
   ```bash
   ./scripts/start.sh --check
   ```

### 直接运行

```bash
# 激活虚拟环境
source ~/traffic_vision_env/bin/activate

# 运行主程序
python src/main.py

# 或指定配置文件
python src/main.py config/config.yaml
```

## 📊 系统监控

### 日志查看

- **系统日志**: `logs/traffic_vision_YYYY-MM-DD.log`
- **实时日志**: `tail -f logs/traffic_vision_$(date +%Y-%m-%d).log`

### 性能监控

系统会自动监控以下指标：
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络流量
- 系统温度
- 处理帧率

### 告警机制

当系统指标超过阈值时会自动发出告警：
- CPU使用率 > 80%
- 内存使用率 > 85%
- 系统温度 > 70°C
- 处理帧率 < 15 FPS

## 🔧 故障排除

### 常见问题

1. **摄像头无法打开**
   - 检查摄像头连接
   - 确认设备权限：`sudo usermod -a -G video $USER`
   - 重启系统后重试

2. **模型下载失败**
   - 检查网络连接
   - 手动下载模型文件到 `models/` 目录

3. **内存不足**
   - 降低图像分辨率
   - 减少处理帧率
   - 使用更小的模型

4. **服务器连接失败**
   - 检查服务器地址配置
   - 确认网络连通性
   - 检查防火墙设置

### 调试模式

启用详细日志输出：
```bash
./scripts/start.sh --verbose
```

或设置环境变量：
```bash
export LOGURU_LEVEL=DEBUG
python src/main.py
```

### 性能优化

1. **硬件优化**
   - 使用高速SD卡（Class 10或更高）
   - 确保充足的电源供应
   - 添加散热器或风扇

2. **软件优化**
   - 调整图像分辨率和帧率
   - 优化检测区域设置
   - 使用GPU加速（如果可用）

## 🔌 API接口

系统会向配置的服务器地址发送交通数据：

### 数据上报接口

**POST** `/api/traffic_update`

```json
{
  "intersection_id": "INTERSECTION_001",
  "location": "Main Street & First Ave",
  "timestamp": "2024-01-01T12:00:00",
  "roads": [
    {
      "road_id": "road_north",
      "vehicle_count": 5,
      "average_speed": 25.5,
      "congestion_level": "medium",
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "summary": {
    "total_vehicles": 5,
    "vehicle_types": {"car": 4, "truck": 1},
    "average_speed": 25.5,
    "data_quality": "good"
  }
}
```

## 🤝 开发指南

### 代码结构

- **检测模块**: 负责车辆检测，基于YOLOv8
- **跟踪模块**: 负责多目标跟踪，统计车流量
- **通信模块**: 负责数据上报和网络通信
- **摄像头模块**: 负责摄像头管理和图像采集
- **监控模块**: 负责系统监控和性能统计

### 扩展开发

1. **添加新的检测算法**
   - 继承 `VehicleDetector` 基类
   - 实现 `detect_vehicles` 方法

2. **添加新的摄像头类型**
   - 继承 `CameraBase` 基类
   - 实现相应的接口方法

3. **添加新的数据上报方式**
   - 修改 `DataReporter` 类
   - 添加新的通信协议支持

### 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行集成测试
./scripts/start.sh --test
```

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🙋‍♂️ 支持

如有问题或建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 提交 [Issue](issues)
3. 联系技术支持

## 🔄 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持YOLOv8n车辆检测
- 支持多种摄像头类型
- 实现实时数据上报
- 添加系统监控功能

---

**路口车流识别系统** - 让交通监控更智能！

