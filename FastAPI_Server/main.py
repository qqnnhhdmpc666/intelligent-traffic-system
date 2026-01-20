"""
智慧交通调度系统 - FastAPI版本
基于FastAPI的轻量级交通调度服务器
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

# 导入路由
from routers import traffic, planning, system, performance
from database import init_database

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在初始化智慧交通调度系统 (FastAPI版)...")

    # 初始化数据库
    init_database()

    logger.info("智慧交通调度系统初始化完成")
    logger.info("访问 http://localhost:8000/docs 查看API文档")

    yield

    # 关闭时清理
    logger.info("智慧交通调度系统正在关闭...")

# 创建FastAPI应用
app = FastAPI(
    title="智慧交通调度系统",
    description="基于FastAPI的交通调度系统，兼容TrafficVisionSystem",
    version="2.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(traffic.router)
app.include_router(planning.router)
app.include_router(system.router)
app.include_router(performance.router)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "智慧交通调度系统 FastAPI版",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "TrafficVisionSystem兼容",
            "完整路径规划算法",
            "自动API文档生成"
        ],
        "endpoints": {
            "traffic_update": "POST /api/traffic_update",
            "request_path": "POST /api/request_path",
            "system_stats": "GET /api/system_stats",
            "health": "GET /health",
            "docs": "GET /docs",
            "api_docs": "GET /openapi.json"
        }
    }

if __name__ == "__main__":
    # 开发模式启动
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )