#!/usr/bin/env python3
"""
FastAPI智慧交通调度系统启动脚本
提供多种启动方式和环境检查
"""

import subprocess
import sys
import time
import os
import signal
import argparse
from pathlib import Path

class FastAPIServer:
    """FastAPI服务器管理器"""

    def __init__(self):
        self.server_process = None
        self.is_running = False

    def check_environment(self):
        """检查运行环境"""
        print("🔍 检查FastAPI运行环境...")

        # 检查Python版本
        if sys.version_info < (3, 8):
            print("❌ 需要Python 3.8或更高版本")
            return False

        # 检查必要依赖
        required_packages = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package}")

        if missing_packages:
            print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
            print("请运行: pip install -r requirements.txt")
            return False

        # 检查算法文件是否存在
        algo_files = [
            "../../Server/core/graph.py",
            "../../Server/core/pathfinding.py",
            "../../Server/core/route_planner.py"
        ]

        for algo_file in algo_files:
            if not os.path.exists(algo_file):
                print(f"❌ 找不到算法文件: {algo_file}")
                return False
            else:
                print(f"✅ 算法文件: {algo_file}")

        print("✅ 环境检查通过")
        return True

    def start_server(self, host="0.0.0.0", port=8000, reload=False):
        """启动FastAPI服务器"""
        try:
            print("🚀 启动智慧交通调度系统 (FastAPI版)...")

            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

            # 构建启动命令
            cmd = [
                sys.executable, "-m", "uvicorn",
                "main:app",
                "--host", host,
                "--port", str(port)
            ]

            if reload:
                cmd.append("--reload")

            print(f"执行命令: {' '.join(cmd)}")

            # 启动服务器
            self.server_process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env
            )

            self.is_running = True

            # 等待服务器启动
            print("⏳ 等待服务器启动...")
            for i in range(10):
                time.sleep(1)
                if self.check_server_health(host, port):
                    print("✅ 服务器启动成功！"                    print(f"   📖 API文档: http://{host}:{port}/docs")
                    print(f"   🌐 Web界面: http://{host}:{port}")
                    print(f"   💚 健康检查: http://{host}:{port}/health")
                    return True
                print(f"   等待中... ({i+1}/10)")

            print("❌ 服务器启动超时")
            self.stop_server()
            return False

        except Exception as e:
            print(f"❌ 启动服务器失败: {e}")
            return False

    def check_server_health(self, host="localhost", port=8000):
        """检查服务器健康状态"""
        try:
            import requests
            response = requests.get(f"http://{host}:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def stop_server(self):
        """停止服务器"""
        if self.server_process and self.is_running:
            print("🛑 正在停止服务器...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

            self.is_running = False
            print("✅ 服务器已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FastAPI智慧交通调度系统启动器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    parser.add_argument('--reload', action='store_true', help='开发模式自动重载')
    parser.add_argument('--check', action='store_true', help='仅检查环境')
    parser.add_argument('--daemon', action='store_true', help='守护进程模式')

    args = parser.parse_args()

    server = FastAPIServer()

    # 环境检查
    if not server.check_environment():
        sys.exit(1)

    if args.check:
        print("✅ 环境检查完成")
        sys.exit(0)

    # 启动服务器
    if args.daemon:
        # 守护进程模式
        if server.start_server(args.host, args.port, args.reload):
            print("🔄 服务器在守护进程模式下运行")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                server.stop_server()
    else:
        # 交互模式
        if server.start_server(args.host, args.port, args.reload):
            try:
                print("
📋 服务器运行中..."                print("可用命令:")
                print("  - 按 Ctrl+C 停止服务器")
                print(f"  - 访问 http://{args.host}:{args.port}/docs 查看API文档")
                print()

                # 保持运行
                while server.is_running:
                    time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 收到停止信号...")
                server.stop_server()

if __name__ == "__main__":
    main()