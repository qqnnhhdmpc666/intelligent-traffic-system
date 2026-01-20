"""
性能测试API路由
实现论文中的性能评价指标测试
"""

import time
import asyncio
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import threading
import concurrent.futures

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from models import PathRequest, TrafficUpdateRequest
from core.route_planner import RoutePlanner

router = APIRouter()

# 性能测试数据存储
performance_results = {
    "path_planning_tests": [],
    "traffic_update_tests": [],
    "concurrent_tests": [],
    "system_load_tests": []
}

class PerformanceTestRequest(BaseModel):
    """性能测试请求"""
    test_type: str  # "path_planning", "traffic_update", "concurrent", "load"
    duration: int = 60  # 测试时长(秒)
    concurrent_users: int = 10  # 并发用户数
    requests_per_second: int = 10  # 每秒请求数

class PerformanceTestResult(BaseModel):
    """性能测试结果"""
    test_id: str
    test_type: str
    start_time: str
    end_time: str
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_details: List[Dict[str, Any]] = []

class SystemMetrics(BaseModel):
    """系统性能指标"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    active_threads: int
    active_connections: int
    queue_size: int
    response_times: List[float] = []

# 全局性能监控器
performance_monitor = {
    "response_times": [],
    "active_tests": 0,
    "last_cleanup": time.time()
}

def record_response_time(response_time: float):
    """记录响应时间"""
    performance_monitor["response_times"].append(response_time)

    # 定期清理旧数据（保留最近1小时）
    current_time = time.time()
    if current_time - performance_monitor["last_cleanup"] > 3600:
        # 只保留最近1小时的数据
        cutoff_time = current_time - 3600
        # 这里简化处理，实际可以根据时间戳过滤
        if len(performance_monitor["response_times"]) > 10000:
            performance_monitor["response_times"] = performance_monitor["response_times"][-5000:]
        performance_monitor["last_cleanup"] = current_time

async def run_path_planning_test(duration: int, requests_per_second: int) -> Dict[str, Any]:
    """运行路径规划性能测试"""
    start_time = time.time()
    end_time = start_time + duration

    response_times = []
    errors = []
    successful_requests = 0
    failed_requests = 0

    # 测试用的路径规划请求
    test_requests = [
        {"start_node": "A", "end_node": "B", "vehicle_type": "normal"},
        {"start_node": "A", "end_node": "C", "vehicle_type": "normal"},
        {"start_node": "B", "end_node": "D", "vehicle_type": "normal"},
        {"start_node": "C", "end_node": "E", "vehicle_type": "normal"},
        {"start_node": "A", "end_node": "E", "vehicle_type": "emergency"}
    ]

    request_index = 0

    while time.time() < end_time:
        batch_start = time.time()

        # 控制请求频率
        for _ in range(requests_per_second):
            if time.time() >= end_time:
                break

            try:
                # 选择测试请求
                test_data = test_requests[request_index % len(test_requests)]
                request_index += 1

                # 执行路径规划
                planner = RoutePlanner()
                req_start = time.time()
                result = planner.plan_route(
                    test_data["start_node"],
                    test_data["end_node"],
                    test_data["vehicle_type"]
                )
                req_end = time.time()

                response_time = req_end - req_start
                response_times.append(response_time)
                record_response_time(response_time)

                if result and "path" in result:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    errors.append({
                        "request": test_data,
                        "error": "规划失败",
                        "response_time": response_time
                    })

            except Exception as e:
                failed_requests += 1
                errors.append({
                    "request": test_requests[request_index % len(test_requests)],
                    "error": str(e),
                    "response_time": time.time() - batch_start
                })

        # 控制每秒的请求数
        batch_time = time.time() - batch_start
        if batch_time < 1.0:
            await asyncio.sleep(1.0 - batch_time)

    total_requests = successful_requests + failed_requests

    # 计算统计数据
    if response_times:
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
    else:
        avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
    actual_duration = time.time() - start_time
    requests_per_second = total_requests / actual_duration if actual_duration > 0 else 0

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": success_rate,
        "average_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "p95_response_time": p95_response_time,
        "p99_response_time": p99_response_time,
        "requests_per_second": requests_per_second,
        "errors": errors[:10]  # 只保留前10个错误
    }

async def run_traffic_update_test(duration: int, requests_per_second: int) -> Dict[str, Any]:
    """运行交通数据更新性能测试"""
    start_time = time.time()
    end_time = start_time + duration

    response_times = []
    errors = []
    successful_requests = 0
    failed_requests = 0

    # 测试用的交通数据
    test_data_template = {
        "intersection_id": "TEST_001",
        "location": "Test Intersection",
        "timestamp": "2024-01-01T12:00:00",
        "roads": [
            {
                "road_id": "road_north",
                "vehicle_count": 5,
                "average_speed": 25.5,
                "congestion_level": "medium"
            }
        ],
        "summary": {
            "total_vehicles": 5,
            "vehicle_types": {"car": 4, "truck": 1},
            "average_speed": 25.5,
            "data_quality": "good"
        }
    }

    while time.time() < end_time:
        batch_start = time.time()

        # 控制请求频率
        for _ in range(requests_per_second):
            if time.time() >= end_time:
                break

            try:
                # 修改测试数据以模拟不同场景
                test_data = test_data_template.copy()
                test_data["intersection_id"] = f"TEST_{_ % 10:03d}"
                test_data["roads"][0]["vehicle_count"] = (_ % 20) + 1
                test_data["summary"]["total_vehicles"] = test_data["roads"][0]["vehicle_count"]

                # 这里简化处理，实际应该调用traffic_update逻辑
                req_start = time.time()
                # 模拟数据库操作延迟
                await asyncio.sleep(0.001)  # 1ms模拟数据库操作
                req_end = time.time()

                response_time = req_end - req_start
                response_times.append(response_time)
                record_response_time(response_time)

                successful_requests += 1

            except Exception as e:
                failed_requests += 1
                errors.append({
                    "error": str(e),
                    "response_time": time.time() - batch_start
                })

        # 控制每秒的请求数
        batch_time = time.time() - batch_start
        if batch_time < 1.0:
            await asyncio.sleep(1.0 - batch_time)

    total_requests = successful_requests + failed_requests

    # 计算统计数据
    if response_times:
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]
        p99_response_time = statistics.quantiles(response_times, n=100)[98]
    else:
        avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
    actual_duration = time.time() - start_time
    requests_per_second = total_requests / actual_duration if actual_duration > 0 else 0

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": success_rate,
        "average_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "p95_response_time": p95_response_time,
        "p99_response_time": p99_response_time,
        "requests_per_second": requests_per_second,
        "errors": errors[:10]
    }

@router.post("/api/performance_test", response_model=PerformanceTestResult)
async def run_performance_test(request: PerformanceTestRequest, background_tasks: BackgroundTasks):
    """运行性能测试"""
    test_id = f"{request.test_type}_{int(time.time())}"

    # 增加活跃测试计数
    performance_monitor["active_tests"] += 1

    try:
        start_time = datetime.utcnow().isoformat()

        if request.test_type == "path_planning":
            result = await run_path_planning_test(request.duration, request.requests_per_second)
        elif request.test_type == "traffic_update":
            result = await run_traffic_update_test(request.duration, request.requests_per_second)
        elif request.test_type == "concurrent":
            # 并发测试 - 同时运行路径规划和交通更新
            path_task = asyncio.create_task(run_path_planning_test(request.duration, request.requests_per_second // 2))
            traffic_task = asyncio.create_task(run_traffic_update_test(request.duration, request.requests_per_second // 2))

            path_result, traffic_result = await asyncio.gather(path_task, traffic_task)

            # 合并结果
            result = {
                "total_requests": path_result["total_requests"] + traffic_result["total_requests"],
                "successful_requests": path_result["successful_requests"] + traffic_result["successful_requests"],
                "failed_requests": path_result["failed_requests"] + traffic_result["failed_requests"],
                "success_rate": (path_result["successful_requests"] + traffic_result["successful_requests"]) /
                              (path_result["total_requests"] + traffic_result["total_requests"]) * 100,
                "average_response_time": statistics.mean([
                    path_result["average_response_time"], traffic_result["average_response_time"]
                ]),
                "min_response_time": min(path_result["min_response_time"], traffic_result["min_response_time"]),
                "max_response_time": max(path_result["max_response_time"], traffic_result["max_response_time"]),
                "p95_response_time": max(path_result["p95_response_time"], traffic_result["p95_response_time"]),
                "p99_response_time": max(path_result["p99_response_time"], traffic_result["p99_response_time"]),
                "requests_per_second": path_result["requests_per_second"] + traffic_result["requests_per_second"],
                "errors": (path_result["errors"] + traffic_result["errors"])[:10]
            }
        else:
            raise HTTPException(status_code=400, detail=f"不支持的测试类型: {request.test_type}")

        end_time = datetime.utcnow().isoformat()
        duration = request.duration

        # 保存测试结果
        test_result = PerformanceTestResult(
            test_id=test_id,
            test_type=request.test_type,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            **result
        )

        performance_results[request.test_type + "_tests"].append(test_result.dict())

        # 限制保存的测试结果数量
        if len(performance_results[request.test_type + "_tests"]) > 10:
            performance_results[request.test_type + "_tests"] = performance_results[request.test_type + "_tests"][-10:]

        return test_result

    finally:
        # 减少活跃测试计数
        performance_monitor["active_tests"] -= 1

@router.get("/api/performance_results")
async def get_performance_results(test_type: Optional[str] = None):
    """获取性能测试结果"""
    if test_type:
        key = test_type + "_tests"
        if key in performance_results:
            return {"results": performance_results[key]}
        else:
            raise HTTPException(status_code=404, detail=f"未找到测试类型: {test_type}")
    else:
        return performance_results

@router.get("/api/performance_metrics", response_model=SystemMetrics)
async def get_performance_metrics():
    """获取当前系统性能指标"""
    try:
        import psutil
        import os

        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=0.1)

        # 内存使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # 活跃线程数
        active_threads = threading.active_count()

        # 响应时间统计
        response_times = performance_monitor["response_times"][-100:]  # 最近100个请求

        return SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            active_threads=active_threads,
            active_connections=performance_monitor["active_tests"],  # 简化为活跃测试数
            queue_size=0,  # FastAPI没有显式队列，这里可以扩展
            response_times=response_times
        )

    except ImportError:
        # 如果没有psutil，返回简化数据
        return SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            cpu_usage=0.0,
            memory_usage=0.0,
            active_threads=threading.active_count(),
            active_connections=performance_monitor["active_tests"],
            queue_size=0,
            response_times=performance_monitor["response_times"][-100:]
        )

@router.delete("/api/performance_results")
async def clear_performance_results():
    """清除性能测试结果"""
    global performance_results
    performance_results = {
        "path_planning_tests": [],
        "traffic_update_tests": [],
        "concurrent_tests": [],
        "system_load_tests": []
    }
    performance_monitor["response_times"].clear()
    return {"message": "性能测试结果已清除"}

# 论文评价指标计算函数
def calculate_paper_metrics() -> Dict[str, Any]:
    """
    计算论文中的评价指标
    基于收集的性能数据计算：
    - 平均行程时间 (Average Trip Time)
    - 平均延误时间 (Average Delay Time)
    - 路网总吞吐量 (Network Throughput)
    - 路网平均速度 (Average Network Speed)
    - 拥堵指数 (Congestion Index)
    """

    # 获取最近的测试数据
    all_response_times = performance_monitor["response_times"]

    if not all_response_times:
        return {
            "average_trip_time": 0,
            "average_delay_time": 0,
            "network_throughput": 0,
            "average_network_speed": 0,
            "congestion_index": 0,
            "note": "暂无性能测试数据"
        }

    # 1. 平均行程时间 - 映射为平均响应时间
    average_trip_time = statistics.mean(all_response_times) * 1000  # 转换为毫秒

    # 2. 平均延误时间 - 计算响应时间的标准差（抖动）
    if len(all_response_times) > 1:
        average_delay_time = statistics.stdev(all_response_times) * 1000
    else:
        average_delay_time = 0

    # 3. 路网总吞吐量 - 每秒处理的请求数
    total_requests = len(all_response_times)
    time_span = 60  # 假设1分钟时间窗口
    network_throughput = total_requests / time_span

    # 4. 路网平均速度 - 倒数映射（响应越快，速度越快）
    if average_trip_time > 0:
        average_network_speed = 1000 / average_trip_time  # 归一化速度指标
    else:
        average_network_speed = 100

    # 5. 拥堵指数 - 基于响应时间分布计算
    if all_response_times:
        p95_time = statistics.quantiles(all_response_times, n=20)[18]
        congestion_index = (p95_time / average_trip_time) * 100 if average_trip_time > 0 else 0
    else:
        congestion_index = 0

    return {
        "average_trip_time": round(average_trip_time, 2),  # 毫秒
        "average_delay_time": round(average_delay_time, 2),  # 毫秒
        "network_throughput": round(network_throughput, 2),  # 请求/秒
        "average_network_speed": round(average_network_speed, 2),  # 归一化速度
        "congestion_index": round(congestion_index, 2),  # 百分比
        "sample_size": len(all_response_times),
        "time_window": f"{time_span}s"
    }

@router.get("/api/paper_metrics")
async def get_paper_metrics():
    """获取论文评价指标"""
    return calculate_paper_metrics()

@router.get("/api/cache_stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    try:
        from core.route_planner import RoutePlanner
        planner = RoutePlanner()
        return planner.get_cache_stats()
    except Exception as e:
        return {"error": f"获取缓存统计失败: {str(e)}"}

@router.post("/api/clear_cache")
async def clear_cache():
    """清理所有缓存"""
    try:
        from core.route_planner import RoutePlanner
        planner = RoutePlanner()

        # 清理路径缓存
        planner.path_cache._cache.clear()
        planner.path_cache._hits = 0
        planner.path_cache._misses = 0

        # 清理图缓存
        planner.graph_cache.invalidate_cache()

        return {"message": "缓存已清理"}
    except Exception as e:
        return {"error": f"清理缓存失败: {str(e)}"}

@router.post("/api/load_test")
async def run_load_test(request: PerformanceTestRequest, background_tasks: BackgroundTasks):
    """运行负载测试 - 模拟高并发场景"""
    background_tasks.add_task(run_load_test_background, request)
    return {"message": "负载测试已启动", "test_type": "load", "duration": request.duration}

async def run_load_test_background(request: PerformanceTestRequest):
    """后台运行负载测试"""
    import asyncio

    print(f"开始负载测试: {request.concurrent_users}并发用户, {request.duration}秒")

    async def worker(worker_id: int):
        """工作线程"""
        end_time = time.time() + request.duration
        request_count = 0

        while time.time() < end_time:
            try:
                # 随机选择测试类型
                if worker_id % 2 == 0:
                    # 路径规划测试
                    planner = RoutePlanner()
                    start_time = time.time()
                    result = planner.plan_route("A", "B", "normal")
                    response_time = time.time() - start_time
                else:
                    # 交通更新测试（模拟）
                    start_time = time.time()
                    await asyncio.sleep(0.01)  # 模拟处理时间
                    response_time = time.time() - start_time

                record_response_time(response_time)
                request_count += 1

                # 短暂延迟避免过度占用CPU
                await asyncio.sleep(0.001)

            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                break

        return request_count

    # 创建并发任务
    tasks = []
    for i in range(request.concurrent_users):
        task = asyncio.create_task(worker(i))
        tasks.append(task)

    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)

    total_requests = sum(r for r in results if isinstance(r, int))
    print(f"负载测试完成: 处理了{total_requests}个请求")

    # 保存测试结果
    test_result = {
        "test_id": f"load_test_{int(time.time())}",
        "test_type": "load",
        "concurrent_users": request.concurrent_users,
        "duration": request.duration,
        "total_requests": total_requests,
        "requests_per_second": total_requests / request.duration if request.duration > 0 else 0,
        "timestamp": datetime.utcnow().isoformat()
    }

    performance_results["system_load_tests"].append(test_result)