#!/usr/bin/env python3
"""
智慧交通调度系统性能测试脚本
对应论文4.2评价指标和4.3实验结果分析

测试内容：
- 平均行程时间 (Average Trip Time)
- 平均延误时间 (Average Delay Time)
- 路网总吞吐量 (Network Throughput)
- 路网平均速度 (Average Network Speed)
- 拥堵指数 (Congestion Index)
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class PerformanceResult:
    """性能测试结果"""
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
    response_times: List[float]

class TrafficSystemPerformanceTester:
    """智慧交通调度系统性能测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_path_planning_performance(self,
                                          duration: int = 60,
                                          concurrent_users: int = 10,
                                          requests_per_second: int = 10) -> PerformanceResult:
        """
        测试路径规划性能
        对应论文的平均行程时间和路网总吞吐量指标
        """
        print(f"🧭 开始路径规划性能测试...")
        print(f"   测试时长: {duration}秒")
        print(f"   并发用户: {concurrent_users}")
        print(f"   每秒请求: {requests_per_second}")

        start_time = time.time()
        end_time = start_time + duration

        response_times = []
        successful_requests = 0
        failed_requests = 0

        # 测试用的路径规划请求
        test_scenarios = [
            {"start_node": "A", "end_node": "B", "vehicle_type": "normal"},
            {"start_node": "A", "end_node": "C", "vehicle_type": "normal"},
            {"start_node": "B", "end_node": "D", "vehicle_type": "normal"},
            {"start_node": "C", "end_node": "E", "vehicle_type": "normal"},
            {"start_node": "A", "end_node": "E", "vehicle_type": "emergency"}
        ]

        semaphore = asyncio.Semaphore(concurrent_users)  # 控制并发数

        async def single_request(scenario_idx: int):
            nonlocal successful_requests, failed_requests

            async with semaphore:
                scenario = test_scenarios[scenario_idx % len(test_scenarios)]

                try:
                    request_data = {
                        "start_node": scenario["start_node"],
                        "end_node": scenario["end_node"],
                        "vehicle_type": scenario["vehicle_type"]
                    }

                    req_start = time.time()
                    async with self.session.post(
                        f"{self.base_url}/api/request_path",
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        result = await response.json()
                        req_end = time.time()

                        response_time = req_end - req_start
                        response_times.append(response_time)

                        if response.status == 200 and result.get("path"):
                            successful_requests += 1
                        else:
                            failed_requests += 1

                except Exception as e:
                    failed_requests += 1
                    # 记录错误但不打印以免刷屏

        # 创建任务
        tasks = []
        request_count = 0

        while time.time() < end_time:
            batch_start = time.time()

            # 每秒发送指定数量的请求
            for _ in range(requests_per_second):
                if time.time() >= end_time:
                    break

                task = asyncio.create_task(single_request(request_count))
                tasks.append(task)
                request_count += 1

            # 等待1秒
            await asyncio.sleep(max(0, 1.0 - (time.time() - batch_start)))

        # 等待所有任务完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # 计算结果
        total_requests = successful_requests + failed_requests
        actual_duration = time.time() - start_time

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
            p99_response_time = statistics.quantiles(response_times, n=100)[98]
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        requests_per_second = total_requests / actual_duration if actual_duration > 0 else 0

        result = PerformanceResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            response_times=response_times
        )

        print("✅ 路径规划性能测试完成"        print(f"   总请求数: {total_requests}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均响应时间: {avg_response_time*1000:.1f}ms")
        print(f"   QPS: {requests_per_second:.1f}")

        return result

    async def test_traffic_update_performance(self,
                                            duration: int = 60,
                                            concurrent_users: int = 10,
                                            requests_per_second: int = 20) -> PerformanceResult:
        """
        测试交通数据更新性能
        对应论文的数据处理能力评估
        """
        print(f"🚗 开始交通数据更新性能测试...")
        print(f"   测试时长: {duration}秒")
        print(f"   并发用户: {concurrent_users}")
        print(f"   每秒请求: {requests_per_second}")

        start_time = time.time()
        end_time = start_time + duration

        response_times = []
        successful_requests = 0
        failed_requests = 0

        semaphore = asyncio.Semaphore(concurrent_users)

        async def single_request(intersection_idx: int):
            nonlocal successful_requests, failed_requests

            async with semaphore:
                # 生成测试数据
                test_data = {
                    "intersection_id": "02d",
                    "location": f"Test Intersection {intersection_idx}",
                    "timestamp": "2024-01-01T12:00:00",
                    "roads": [
                        {
                            "road_id": f"road_{(intersection_idx % 4) + 1}",
                            "vehicle_count": (intersection_idx % 20) + 1,
                            "average_speed": 20 + (intersection_idx % 30),
                            "congestion_level": ["low", "medium", "high"][intersection_idx % 3]
                        }
                    ],
                    "summary": {
                        "total_vehicles": (intersection_idx % 20) + 1,
                        "vehicle_types": {"car": (intersection_idx % 15) + 1, "truck": intersection_idx % 5},
                        "average_speed": 20 + (intersection_idx % 30),
                        "data_quality": "good"
                    }
                }

                try:
                    req_start = time.time()
                    async with self.session.post(
                        f"{self.base_url}/api/traffic_update",
                        json=test_data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        result = await response.json()
                        req_end = time.time()

                        response_time = req_end - req_start
                        response_times.append(response_time)

                        if response.status == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1

                except Exception as e:
                    failed_requests += 1

        # 创建任务
        tasks = []
        request_count = 0

        while time.time() < end_time:
            batch_start = time.time()

            for _ in range(requests_per_second):
                if time.time() >= end_time:
                    break

                task = asyncio.create_task(single_request(request_count))
                tasks.append(task)
                request_count += 1

            await asyncio.sleep(max(0, 1.0 - (time.time() - batch_start)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # 计算结果
        total_requests = successful_requests + failed_requests
        actual_duration = time.time() - start_time

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
            p99_response_time = statistics.quantiles(response_times, n=100)[98]
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        requests_per_second = total_requests / actual_duration if actual_duration > 0 else 0

        result = PerformanceResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            response_times=response_times
        )

        print("✅ 交通数据更新性能测试完成"        print(f"   总请求数: {total_requests}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均响应时间: {avg_response_time*1000:.1f}ms")
        print(f"   QPS: {requests_per_second:.1f}")

        return result

    async def get_paper_metrics(self) -> Dict[str, Any]:
        """获取论文评价指标"""
        try:
            async with self.session.get(f"{self.base_url}/api/paper_metrics") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"获取论文指标失败: {response.status}")
                    return {}
        except Exception as e:
            print(f"获取论文指标异常: {e}")
            return {}

    def calculate_paper_metrics_from_results(self, path_result: PerformanceResult,
                                           traffic_result: PerformanceResult) -> Dict[str, Any]:
        """
        根据测试结果计算论文评价指标

        对应论文4.2评价指标：
        - 平均行程时间 (Average Trip Time)
        - 平均延误时间 (Average Delay Time)
        - 路网总吞吐量 (Network Throughput)
        - 路网平均速度 (Average Network Speed)
        - 拥堵指数 (Congestion Index)
        """

        # 合并所有响应时间
        all_response_times = path_result.response_times + traffic_result.response_times

        if not all_response_times:
            return {
                "note": "无测试数据",
                "average_trip_time": 0,
                "average_delay_time": 0,
                "network_throughput": 0,
                "average_network_speed": 0,
                "congestion_index": 0
            }

        # 1. 平均行程时间 - 路径规划的平均响应时间
        average_trip_time = path_result.average_response_time * 1000  # 转换为毫秒

        # 2. 平均延误时间 - 响应时间的变异性（标准差）
        if len(all_response_times) > 1:
            delay_variation = statistics.stdev(all_response_times)
            average_delay_time = delay_variation * 1000  # 转换为毫秒
        else:
            average_delay_time = 0

        # 3. 路网总吞吐量 - 每秒处理的请求数
        total_requests = path_result.total_requests + traffic_result.total_requests
        # 假设测试时长60秒
        network_throughput = total_requests / 60  # 请求/秒

        # 4. 路网平均速度 - 归一化速度指标（响应越快速度越快）
        if average_trip_time > 0:
            # 简单的归一化：基准100ms = 速度100
            average_network_speed = 10000 / average_trip_time  # 归一化到0-100范围
        else:
            average_network_speed = 100

        # 5. 拥堵指数 - 基于95%分位数响应时间
        if all_response_times:
            p95_time = statistics.quantiles(all_response_times, n=20)[18]
            mean_time = statistics.mean(all_response_times)
            if mean_time > 0:
                congestion_index = (p95_time / mean_time - 1) * 100  # 百分比
            else:
                congestion_index = 0
        else:
            congestion_index = 0

        return {
            "average_trip_time": round(average_trip_time, 2),  # 毫秒
            "average_delay_time": round(average_delay_time, 2),  # 毫秒
            "network_throughput": round(network_throughput, 2),  # 请求/秒
            "average_network_speed": round(min(average_network_speed, 100), 2),  # 0-100
            "congestion_index": round(max(0, congestion_index), 2),  # 百分比
            "test_summary": {
                "path_planning_requests": path_result.total_requests,
                "traffic_update_requests": traffic_result.total_requests,
                "total_requests": total_requests,
                "path_success_rate": path_result.success_rate,
                "traffic_success_rate": traffic_result.success_rate
            }
        }

async def run_comprehensive_test():
    """运行综合性能测试"""
    print("🚀 开始智慧交通调度系统综合性能测试")
    print("=" * 60)

    async with TrafficSystemPerformanceTester() as tester:

        # 1. 路径规划性能测试
        print("\n📍 第一阶段: 路径规划性能测试")
        path_result = await tester.test_path_planning_performance(
            duration=30,  # 30秒测试
            concurrent_users=5,
            requests_per_second=5
        )

        # 2. 交通数据更新性能测试
        print("\n🚗 第二阶段: 交通数据更新性能测试")
        traffic_result = await tester.test_traffic_update_performance(
            duration=30,  # 30秒测试
            concurrent_users=5,
            requests_per_second=10
        )

        # 3. 计算论文评价指标
        print("\n📊 第三阶段: 计算论文评价指标")
        paper_metrics = tester.calculate_paper_metrics_from_results(path_result, traffic_result)

        # 4. 获取服务器内部指标
        server_metrics = await tester.get_paper_metrics()

        # 5. 输出结果
        print("\n" + "=" * 60)
        print("📈 性能测试结果汇总")
        print("=" * 60)

        print("
🧭 路径规划性能:"        print(f"   总请求数: {path_result.total_requests}")
        print(f"   成功率: {path_result.success_rate:.1f}%")
        print(f"   平均响应时间: {path_result.average_response_time*1000:.1f}ms")
        print(f"   95%响应时间: {path_result.p95_response_time*1000:.1f}ms")
        print(f"   QPS: {path_result.requests_per_second:.1f}")

        print("
🚗 交通数据更新性能:"        print(f"   总请求数: {traffic_result.total_requests}")
        print(f"   成功率: {traffic_result.success_rate:.1f}%")
        print(f"   平均响应时间: {traffic_result.average_response_time*1000:.1f}ms")
        print(f"   95%响应时间: {traffic_result.p95_response_time*1000:.1f}ms")
        print(f"   QPS: {traffic_result.requests_per_second:.1f}")

        print("
📊 论文评价指标 (对应4.2节):"        print(f"   平均行程时间: {paper_metrics['average_trip_time']:.1f}ms")
        print(f"   平均延误时间: {paper_metrics['average_delay_time']:.1f}ms")
        print(f"   路网总吞吐量: {paper_metrics['network_throughput']:.1f} 请求/秒")
        print(f"   路网平均速度: {paper_metrics['average_network_speed']:.1f}/100")
        print(f"   拥堵指数: {paper_metrics['congestion_index']:.1f}%")

        print("
🔍 测试总结:"        test_summary = paper_metrics.get('test_summary', {})
        print(f"   路径规划请求: {test_summary.get('path_planning_requests', 0)}")
        print(f"   交通更新请求: {test_summary.get('traffic_update_requests', 0)}")
        print(f"   总请求数: {test_summary.get('total_requests', 0)}")

        # 保存结果到文件
        result_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "path_planning": {
                "total_requests": path_result.total_requests,
                "success_rate": path_result.success_rate,
                "average_response_time": path_result.average_response_time,
                "qps": path_result.requests_per_second
            },
            "traffic_update": {
                "total_requests": traffic_result.total_requests,
                "success_rate": traffic_result.success_rate,
                "average_response_time": traffic_result.average_response_time,
                "qps": traffic_result.requests_per_second
            },
            "paper_metrics": paper_metrics
        }

        with open("performance_test_results.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 详细结果已保存到: performance_test_results.json")

        return result_data

async def run_load_test(concurrent_users: int = 20, duration: int = 60):
    """运行负载测试"""
    print(f"🔥 开始负载测试: {concurrent_users}并发用户, {duration}秒")

    async with TrafficSystemPerformanceTester() as tester:
        # 调用服务器的负载测试API
        async with tester.session.post(
            f"{tester.base_url}/api/load_test",
            json={
                "test_type": "load",
                "duration": duration,
                "concurrent_users": concurrent_users,
                "requests_per_second": 50
            }
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ 负载测试已启动: {result}")
            else:
                print(f"❌ 负载测试启动失败: {response.status}")

        # 等待测试完成
        await asyncio.sleep(duration + 5)

        # 获取测试结果
        async with tester.session.get(f"{tester.base_url}/api/performance_results?test_type=system_load") as response:
            if response.status == 200:
                results = await response.json()
                print(f"📊 负载测试结果: {len(results.get('results', []))} 条记录")
                if results.get('results'):
                    latest = results['results'][-1]
                    print(f"   并发用户: {latest.get('concurrent_users')}")
                    print(f"   总请求数: {latest.get('total_requests')}")
                    print(f"   QPS: {latest.get('requests_per_second', 0):.1f}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='智慧交通调度系统性能测试')
    parser.add_argument('--test', choices=['comprehensive', 'path_planning', 'traffic_update', 'load'],
                       default='comprehensive', help='测试类型')
    parser.add_argument('--duration', type=int, default=60, help='测试时长(秒)')
    parser.add_argument('--concurrent', type=int, default=10, help='并发用户数')
    parser.add_argument('--qps', type=int, default=10, help='每秒请求数')
    parser.add_argument('--url', default='http://localhost:8000', help='服务器URL')

    args = parser.parse_args()

    if args.test == 'comprehensive':
        asyncio.run(run_comprehensive_test())
    elif args.test == 'path_planning':
        async def test_path():
            async with TrafficSystemPerformanceTester(args.url) as tester:
                result = await tester.test_path_planning_performance(
                    duration=args.duration,
                    concurrent_users=args.concurrent,
                    requests_per_second=args.qps
                )
                print(f"路径规划QPS: {result.requests_per_second:.1f}")
        asyncio.run(test_path())
    elif args.test == 'traffic_update':
        async def test_traffic():
            async with TrafficSystemPerformanceTester(args.url) as tester:
                result = await tester.test_traffic_update_performance(
                    duration=args.duration,
                    concurrent_users=args.concurrent,
                    requests_per_second=args.qps
                )
                print(f"交通更新QPS: {result.requests_per_second:.1f}")
        asyncio.run(test_traffic())
    elif args.test == 'load':
        asyncio.run(run_load_test(args.concurrent, args.duration))

if __name__ == "__main__":
    main()