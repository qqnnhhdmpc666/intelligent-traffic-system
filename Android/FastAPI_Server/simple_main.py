"""
简化的FastAPI服务器 - 用于测试
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="智慧交通调度系统", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "智慧交通调度系统运行正常"}

@app.get("/docs")
def get_docs():
    return {"message": "API文档"}

@app.post("/api/request_path")
def request_path(start_node: str = "I_0_0", end_node: str = "I_0_1", vehicle_type: str = "normal"):
    """模拟路径规划请求"""
    return {
        "success": True,
        "start_node": start_node,
        "end_node": end_node,
        "vehicle_type": vehicle_type,
        "path": [start_node, end_node],
        "estimated_time": 10.5,
        "algorithm": "SP" if vehicle_type == "emergency" else "D_KSPP"
    }

@app.post("/api/traffic_update")
def traffic_update():
    """模拟交通数据更新"""
    return {"message": "交通数据更新成功"}

if __name__ == "__main__":
    print("🚀 启动简化的FastAPI服务器...")
    print("📍 访问地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)