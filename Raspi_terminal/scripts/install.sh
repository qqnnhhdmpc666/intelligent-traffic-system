#!/bin/bash
# 路口车流识别系统安装脚本
# 适用于Raspberry Pi 5

set -e

echo "=========================================="
echo "路口车流识别系统安装脚本"
echo "适用于Raspberry Pi 5 + YOLOv8n"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "建议不要使用root用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统信息
check_system() {
    log_info "检查系统信息..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法检测操作系统"
        exit 1
    fi
    
    source /etc/os-release
    log_info "操作系统: $PRETTY_NAME"
    
    # 检查架构
    ARCH=$(uname -m)
    log_info "系统架构: $ARCH"
    
    # 检查是否为树莓派
    if [[ -f /proc/device-tree/model ]]; then
        MODEL=$(cat /proc/device-tree/model)
        log_info "设备型号: $MODEL"
    fi
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_info "Python版本: $PYTHON_VERSION"
    else
        log_error "Python3 未安装"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    sudo apt update
    sudo apt upgrade -y
}

# 安装系统依赖
install_system_dependencies() {
    log_info "安装系统依赖包..."
    
    # 基础开发工具
    sudo apt install -y \
        build-essential \
        cmake \
        pkg-config \
        git \
        wget \
        curl \
        unzip \
        software-properties-common
    
    # Python开发环境
    sudo apt install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-setuptools \
        python3-wheel
    
    # OpenCV依赖
    sudo apt install -y \
        libopencv-dev \
        python3-opencv \
        libgtk-3-dev \
        libcanberra-gtk-module \
        libcanberra-gtk3-module
    
    # 图像和视频处理库
    sudo apt install -y \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev
    
    # 数学库
    sudo apt install -y \
        libatlas-base-dev \
        gfortran \
        libblas-dev \
        liblapack-dev
    
    # 树莓派特定包
    if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        log_info "安装树莓派特定包..."
        sudo apt install -y \
            libraspberrypi-bin \
            libraspberrypi-dev \
            python3-picamera2
    fi
    
    # 系统监控工具
    sudo apt install -y \
        htop \
        iotop \
        nethogs \
        lsof
}

# 创建Python虚拟环境
create_virtual_environment() {
    log_info "创建Python虚拟环境..."
    
    VENV_DIR="$HOME/traffic_vision_env"
    
    if [[ -d "$VENV_DIR" ]]; then
        log_warn "虚拟环境已存在: $VENV_DIR"
        read -p "是否重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            return 0
        fi
    fi
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # 升级pip
    pip install --upgrade pip setuptools wheel
    
    log_info "虚拟环境创建完成: $VENV_DIR"
}

# 安装Python依赖
install_python_dependencies() {
    log_info "安装Python依赖包..."
    
    VENV_DIR="$HOME/traffic_vision_env"
    source "$VENV_DIR/bin/activate"
    
    # 安装PyTorch (CPU版本，适合树莓派)
    log_info "安装PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    
    # 安装项目依赖
    if [[ -f "requirements.txt" ]]; then
        log_info "从requirements.txt安装依赖..."
        pip install -r requirements.txt
    else
        log_warn "requirements.txt不存在，手动安装核心依赖..."
        
        # 核心依赖
        pip install \
            ultralytics \
            opencv-python \
            numpy \
            Pillow \
            requests \
            pandas \
            psutil \
            loguru \
            pyyaml \
            python-dotenv
        
        # 树莓派摄像头支持
        if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
            pip install picamera2
        fi
    fi
    
    log_info "Python依赖安装完成"
}

# 下载YOLOv8模型
download_models() {
    log_info "下载YOLOv8模型..."
    
    MODELS_DIR="./models"
    mkdir -p "$MODELS_DIR"
    
    # 下载YOLOv8n模型
    MODEL_URL="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
    MODEL_FILE="$MODELS_DIR/yolov8n.pt"
    
    if [[ ! -f "$MODEL_FILE" ]]; then
        log_info "下载YOLOv8n模型..."
        wget -O "$MODEL_FILE" "$MODEL_URL"
        
        if [[ $? -eq 0 ]]; then
            log_info "模型下载完成: $MODEL_FILE"
        else
            log_warn "模型下载失败，程序运行时会自动下载"
        fi
    else
        log_info "模型文件已存在: $MODEL_FILE"
    fi
}

# 创建系统服务
create_systemd_service() {
    log_info "创建系统服务..."
    
    read -p "是否创建systemd服务以便开机自启动? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 0
    fi
    
    SERVICE_NAME="traffic-vision"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    WORK_DIR=$(pwd)
    VENV_DIR="$HOME/traffic_vision_env"
    USER=$(whoami)
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Traffic Vision System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd配置
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable "$SERVICE_NAME"
    
    log_info "系统服务创建完成: $SERVICE_NAME"
    log_info "使用以下命令管理服务:"
    log_info "  启动: sudo systemctl start $SERVICE_NAME"
    log_info "  停止: sudo systemctl stop $SERVICE_NAME"
    log_info "  状态: sudo systemctl status $SERVICE_NAME"
    log_info "  日志: sudo journalctl -u $SERVICE_NAME -f"
}

# 设置权限
setup_permissions() {
    log_info "设置文件权限..."
    
    # 设置脚本执行权限
    chmod +x scripts/*.sh
    chmod +x src/main.py
    
    # 创建日志目录
    mkdir -p logs
    chmod 755 logs
    
    # 创建数据目录
    mkdir -p data/{recordings,debug}
    chmod 755 data data/recordings data/debug
}

# 运行测试
run_tests() {
    log_info "运行系统测试..."
    
    VENV_DIR="$HOME/traffic_vision_env"
    source "$VENV_DIR/bin/activate"
    
    # 测试Python导入
    log_info "测试Python模块导入..."
    python3 -c "
import sys
sys.path.append('src')

try:
    from detection.vehicle_detector import VehicleDetector
    from tracking.vehicle_tracker import VehicleTracker
    from communication.data_reporter import DataReporter
    from camera.camera_manager import CameraManager
    from monitoring.system_monitor import SystemMonitor
    print('所有模块导入成功')
except ImportError as e:
    print(f'模块导入失败: {e}')
    sys.exit(1)
"
    
    if [[ $? -eq 0 ]]; then
        log_info "模块测试通过"
    else
        log_error "模块测试失败"
        return 1
    fi
    
    # 测试配置文件
    if [[ -f "config/config.yaml" ]]; then
        log_info "配置文件存在"
    else
        log_warn "配置文件不存在，将使用默认配置"
    fi
}

# 显示安装完成信息
show_completion_info() {
    log_info "安装完成！"
    echo
    echo "=========================================="
    echo "路口车流识别系统安装完成"
    echo "=========================================="
    echo
    echo "项目目录: $(pwd)"
    echo "虚拟环境: $HOME/traffic_vision_env"
    echo
    echo "使用方法:"
    echo "1. 激活虚拟环境:"
    echo "   source $HOME/traffic_vision_env/bin/activate"
    echo
    echo "2. 运行系统:"
    echo "   python src/main.py"
    echo
    echo "3. 或者指定配置文件:"
    echo "   python src/main.py config/config.yaml"
    echo
    echo "配置文件: config/config.yaml"
    echo "日志目录: logs/"
    echo "模型目录: models/"
    echo
    echo "注意事项:"
    echo "- 首次运行时会自动下载YOLOv8模型"
    echo "- 确保摄像头已正确连接"
    echo "- 检查服务器地址配置是否正确"
    echo "- 建议在良好的网络环境下运行"
    echo
    echo "如有问题，请查看日志文件或联系技术支持"
    echo "=========================================="
}

# 主安装流程
main() {
    log_info "开始安装路口车流识别系统..."
    
    # 检查环境
    check_root
    check_system
    
    # 安装依赖
    update_system
    install_system_dependencies
    
    # 设置Python环境
    create_virtual_environment
    install_python_dependencies
    
    # 下载模型
    download_models
    
    # 设置权限
    setup_permissions
    
    # 创建系统服务
    create_systemd_service
    
    # 运行测试
    if ! run_tests; then
        log_error "测试失败，请检查安装"
        exit 1
    fi
    
    # 显示完成信息
    show_completion_info
    
    log_info "安装脚本执行完成"
}

# 执行主函数
main "$@"

