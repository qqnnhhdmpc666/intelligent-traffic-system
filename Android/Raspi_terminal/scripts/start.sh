#!/bin/bash
# 路口车流识别系统启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "路口车流识别系统启动脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help          显示此帮助信息"
    echo "  -c, --config FILE   指定配置文件路径"
    echo "  -d, --daemon        以守护进程模式运行"
    echo "  -t, --test          运行测试模式"
    echo "  -v, --verbose       详细输出模式"
    echo "  --check             检查系统环境"
    echo "  --status            显示系统状态"
    echo "  --stop              停止运行中的系统"
    echo
    echo "示例:"
    echo "  $0                  # 使用默认配置启动"
    echo "  $0 -c custom.yaml   # 使用自定义配置启动"
    echo "  $0 -d               # 以守护进程模式启动"
    echo "  $0 --check          # 检查系统环境"
}

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."
    
    # 检查Python虚拟环境
    VENV_DIR="$HOME/traffic_vision_env"
    if [[ ! -d "$VENV_DIR" ]]; then
        log_error "Python虚拟环境不存在: $VENV_DIR"
        log_info "请先运行安装脚本: ./scripts/install.sh"
        return 1
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 检查Python版本
    PYTHON_VERSION=$(python --version 2>&1)
    log_info "Python版本: $PYTHON_VERSION"
    
    # 检查关键依赖
    log_info "检查Python依赖..."
    python -c "
import sys
sys.path.append('src')

required_modules = [
    'cv2', 'numpy', 'ultralytics', 'requests', 
    'yaml', 'loguru', 'psutil', 'PIL'
]

missing_modules = []
for module in required_modules:
    try:
        __import__(module)
        print(f'✓ {module}')
    except ImportError:
        missing_modules.append(module)
        print(f'✗ {module}')

if missing_modules:
    print(f'缺少依赖: {missing_modules}')
    sys.exit(1)
else:
    print('所有依赖检查通过')
"
    
    if [[ $? -ne 0 ]]; then
        log_error "依赖检查失败"
        return 1
    fi
    
    # 检查摄像头
    log_info "检查摄像头设备..."
    if [[ -e /dev/video0 ]]; then
        log_info "发现USB摄像头: /dev/video0"
    elif [[ -e /dev/video1 ]]; then
        log_info "发现USB摄像头: /dev/video1"
    else
        log_warn "未发现USB摄像头设备"
    fi
    
    # 检查树莓派摄像头
    if command -v vcgencmd &> /dev/null; then
        CAMERA_STATUS=$(vcgencmd get_camera 2>/dev/null || echo "unknown")
        log_info "树莓派摄像头状态: $CAMERA_STATUS"
    fi
    
    # 检查配置文件
    if [[ -f "config/config.yaml" ]]; then
        log_info "配置文件存在: config/config.yaml"
    else
        log_warn "配置文件不存在，将使用默认配置"
    fi
    
    # 检查模型文件
    if [[ -f "models/yolov8n.pt" ]]; then
        log_info "YOLOv8模型文件存在: models/yolov8n.pt"
    else
        log_warn "YOLOv8模型文件不存在，首次运行时会自动下载"
    fi
    
    # 检查目录权限
    for dir in "logs" "data" "models"; do
        if [[ -d "$dir" ]]; then
            if [[ -w "$dir" ]]; then
                log_info "目录权限正常: $dir"
            else
                log_warn "目录权限不足: $dir"
            fi
        else
            log_warn "目录不存在: $dir"
            mkdir -p "$dir"
            log_info "已创建目录: $dir"
        fi
    done
    
    log_info "环境检查完成"
    return 0
}

# 获取系统状态
get_system_status() {
    log_info "获取系统状态..."
    
    # 检查进程
    PID_FILE="/tmp/traffic_vision.pid"
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "系统正在运行 (PID: $PID)"
            
            # 显示进程信息
            ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem
            
            # 显示端口占用
            if command -v netstat &> /dev/null; then
                log_info "网络连接:"
                netstat -tlnp 2>/dev/null | grep "$PID" || true
            fi
            
            return 0
        else
            log_warn "PID文件存在但进程不存在，清理PID文件"
            rm -f "$PID_FILE"
        fi
    fi
    
    log_info "系统未运行"
    return 1
}

# 停止系统
stop_system() {
    log_info "停止系统..."
    
    PID_FILE="/tmp/traffic_vision.pid"
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "发送停止信号到进程 $PID"
            kill -TERM "$PID"
            
            # 等待进程结束
            for i in {1..10}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    log_info "进程已停止"
                    rm -f "$PID_FILE"
                    return 0
                fi
                sleep 1
            done
            
            # 强制终止
            log_warn "进程未响应，强制终止"
            kill -KILL "$PID"
            rm -f "$PID_FILE"
            return 0
        else
            log_warn "PID文件存在但进程不存在"
            rm -f "$PID_FILE"
        fi
    fi
    
    # 查找并终止相关进程
    PIDS=$(pgrep -f "traffic.*vision\|main\.py" || true)
    if [[ -n "$PIDS" ]]; then
        log_info "发现相关进程: $PIDS"
        echo "$PIDS" | xargs kill -TERM
        sleep 2
        
        # 检查是否还有进程
        PIDS=$(pgrep -f "traffic.*vision\|main\.py" || true)
        if [[ -n "$PIDS" ]]; then
            log_warn "强制终止进程: $PIDS"
            echo "$PIDS" | xargs kill -KILL
        fi
    fi
    
    log_info "系统已停止"
}

# 启动系统
start_system() {
    local config_file="$1"
    local daemon_mode="$2"
    local test_mode="$3"
    local verbose_mode="$4"
    
    log_info "启动路口车流识别系统..."
    
    # 检查是否已在运行
    PID_FILE="/tmp/traffic_vision.pid"
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_error "系统已在运行 (PID: $PID)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    # 激活虚拟环境
    VENV_DIR="$HOME/traffic_vision_env"
    source "$VENV_DIR/bin/activate"
    
    # 构建启动命令
    CMD="python src/main.py"
    
    if [[ -n "$config_file" ]]; then
        CMD="$CMD $config_file"
    fi
    
    # 设置环境变量
    export PYTHONPATH="$PWD/src:$PYTHONPATH"
    
    if [[ "$verbose_mode" == "true" ]]; then
        export LOGURU_LEVEL="DEBUG"
    fi
    
    # 创建日志目录
    mkdir -p logs
    
    if [[ "$daemon_mode" == "true" ]]; then
        # 守护进程模式
        log_info "以守护进程模式启动..."
        
        nohup $CMD > logs/system.log 2>&1 &
        PID=$!
        echo "$PID" > "$PID_FILE"
        
        # 等待一下确保启动成功
        sleep 3
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "系统启动成功 (PID: $PID)"
            log_info "日志文件: logs/system.log"
            log_info "使用 '$0 --status' 查看状态"
            log_info "使用 '$0 --stop' 停止系统"
        else
            log_error "系统启动失败"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        # 前台模式
        log_info "以前台模式启动..."
        log_info "按 Ctrl+C 停止系统"
        
        # 设置信号处理
        trap 'log_info "收到中断信号，正在停止..."; exit 0' INT TERM
        
        if [[ "$test_mode" == "true" ]]; then
            log_info "测试模式：运行30秒后自动停止"
            timeout 30 $CMD || true
        else
            $CMD
        fi
    fi
}

# 主函数
main() {
    local config_file=""
    local daemon_mode="false"
    local test_mode="false"
    local verbose_mode="false"
    local check_only="false"
    local status_only="false"
    local stop_only="false"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--config)
                config_file="$2"
                shift 2
                ;;
            -d|--daemon)
                daemon_mode="true"
                shift
                ;;
            -t|--test)
                test_mode="true"
                shift
                ;;
            -v|--verbose)
                verbose_mode="true"
                shift
                ;;
            --check)
                check_only="true"
                shift
                ;;
            --status)
                status_only="true"
                shift
                ;;
            --stop)
                stop_only="true"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 切换到项目目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$PROJECT_DIR"
    
    # 执行相应操作
    if [[ "$check_only" == "true" ]]; then
        check_environment
        exit $?
    elif [[ "$status_only" == "true" ]]; then
        get_system_status
        exit $?
    elif [[ "$stop_only" == "true" ]]; then
        stop_system
        exit $?
    else
        # 启动系统前先检查环境
        if ! check_environment; then
            log_error "环境检查失败，无法启动系统"
            exit 1
        fi
        
        # 启动系统
        start_system "$config_file" "$daemon_mode" "$test_mode" "$verbose_mode"
    fi
}

# 执行主函数
main "$@"

