"""
大规模拥堵场景实验模块
用于测试论文中路径规划算法在不同拥堵场景下的性能
"""

import time
import random
import json
from typing import Dict, List, Tuple

# 导入核心模块
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.graph import Graph
from core.route_planner import RoutePlanner

class CongestionExperiment:
    """
    拥堵场景实验类
    用于生成不同程度的拥堵场景并测试路径规划算法性能
    """
    
    def __init__(self):
        """
        初始化实验类
        """
        self.planner = RoutePlanner()
        self.graph = self.planner.graph_cache.get_graph()
        self.experiment_results = []
    
    def generate_congestion_scenario(self, congestion_level: str = "moderate") -> Dict:
        """
        生成拥堵场景
        
        Args:
            congestion_level: 拥堵级别 ("light", "moderate", "heavy", "extreme")
            
        Returns:
            拥堵场景配置字典
        """
        # 定义拥堵级别对应的参数
        congestion_params = {
            "light": {
                "affected_edges_ratio": 0.3,  # 30%的边受影响
                "congestion_factor_min": 2.0,  # 最小拥堵因子
                "congestion_factor_max": 3.0,  # 最大拥堵因子
                "bottleneck_factor": 0.2  # 瓶颈路段比例
            },
            "moderate": {
                "affected_edges_ratio": 0.5,
                "congestion_factor_min": 3.0,
                "congestion_factor_max": 4.5,
                "bottleneck_factor": 0.3
            },
            "heavy": {
                "affected_edges_ratio": 0.75,
                "congestion_factor_min": 5.0,
                "congestion_factor_max": 7.0,
                "bottleneck_factor": 0.55
            },
            "extreme": {
                "affected_edges_ratio": 0.9,
                "congestion_factor_min": 6.5,
                "congestion_factor_max": 9.0,
                "bottleneck_factor": 0.65
            }
        }
        
        params = congestion_params.get(congestion_level, congestion_params["moderate"])
        
        # 选择受影响的边
        all_edges = list(self.graph.edges.keys())
        num_affected = int(len(all_edges) * params["affected_edges_ratio"])
        
        # 智能选择受影响的边，优先选择关键路径
        # 1. 计算每条边的重要性（基于连接的节点度数）
        edge_importance = {}
        for edge in all_edges:
            from_node, to_node = edge
            # 边的重要性 = 起点度数 + 终点度数
            importance = len(self.graph.adj.get(from_node, [])) + len(self.graph.adj.get(to_node, []))
            edge_importance[edge] = importance
        
        # 2. 按重要性排序，优先选择重要的边
        sorted_edges = sorted(all_edges, key=lambda x: edge_importance[x], reverse=True)
        
        # 3. 选择前num_affected条重要的边
        affected_edges = sorted_edges[:num_affected]
        
        # 4. 为受影响的边生成拥堵因子
        congestion_factors = {}
        num_bottlenecks = int(len(affected_edges) * params["bottleneck_factor"])
        
        for i, edge in enumerate(affected_edges):
            if i < num_bottlenecks:
                # 瓶颈路段，拥堵因子更高
                factor = random.uniform(params["congestion_factor_max"] * 0.9, params["congestion_factor_max"])
            else:
                # 普通拥堵路段
                factor = random.uniform(params["congestion_factor_min"], params["congestion_factor_max"] * 0.6)
            congestion_factors[edge] = factor
        
        return {
            "congestion_level": congestion_level,
            "affected_edges": affected_edges,
            "congestion_factors": congestion_factors,
            "params": params,
            "edge_importance": edge_importance  # 边的重要性，用于调试
        }
    
    def apply_congestion_scenario(self, scenario: Dict) -> None:
        """
        应用拥堵场景到图中
        
        Args:
            scenario: 拥堵场景配置字典
        """
        for edge, factor in scenario["congestion_factors"].items():
            from_node, to_node = edge
            original_weight = self.graph.get_edge_weight(from_node, to_node)
            if original_weight:
                new_weight = original_weight * factor
                self.graph.update_edge_weight(from_node, to_node, new_weight)
                # 更新拥堵度
                if edge in self.graph.edges:
                    original_congestion = self.graph.edges[edge].get("current_congestion", 0)
                    new_congestion = original_congestion * factor
                    self.graph.edges[edge]["current_congestion"] = new_congestion
        
        # 更新缓存中的图
        self.planner.graph_cache._graph = self.graph
        self.planner.graph_cache._last_update = time.time()
    
    def reset_graph(self) -> None:
        """
        重置图到初始状态
        """
        # 重新加载图
        self.graph = Graph.from_database()
        # 更新缓存中的图
        self.planner.graph_cache._graph = self.graph
        self.planner.graph_cache._last_update = time.time()
    
    def run_experiment(self, start_node: str, end_node: str, congestion_levels: List[str] = None) -> List[Dict]:
        """
        运行实验
        
        Args:
            start_node: 起始节点
            end_node: 目标节点
            congestion_levels: 拥堵级别列表
            
        Returns:
            实验结果列表
        """
        if congestion_levels is None:
            congestion_levels = ["light", "moderate", "heavy", "extreme"]
        
        results = []
        
        # 定义算法映射
        algorithms = {
            "SP": "emergency",      # SP算法
            "D-KSPP": "normal"       # D-KSPP算法
        }
        
        for level in congestion_levels:
            # 重置图
            self.reset_graph()
            
            # 清除路径缓存
            self.planner.path_cache._cache = {}
            
            # 生成并应用拥堵场景
            scenario = self.generate_congestion_scenario(level)
            self.apply_congestion_scenario(scenario)
            
            # 测试每种算法
            for algo_name, vehicle_type in algorithms.items():
                # 运行路径规划
                start_time = time.time()
                result = self.planner.plan_route(start_node, end_node, vehicle_type)
                processing_time = time.time() - start_time
                
                # 收集实验数据
                experiment_data = {
                    "algorithm": algo_name,
                    "congestion_level": level,
                    "start_node": start_node,
                    "end_node": end_node,
                    "processing_time": processing_time,
                    "path_length": len(result.get("path", [])),
                    "path_weight": result.get("weight", 0),
                    "path_distance": result.get("distance", 0),
                    "path_duration": result.get("duration", 0),
                    "path_congestion": result.get("congestion", 0),
                    "alternative_paths": result.get("alternative_paths", 0),
                    "message": result.get("message", ""),
                    "affected_edges_count": len(scenario["affected_edges"]),
                    "total_edges_count": len(self.graph.edges),
                    "scenario": scenario,
                    "vehicle_type": vehicle_type
                }
                
                results.append(experiment_data)
                print(f"📊 实验完成: {level}拥堵 - {algo_name}算法 - 处理时间: {processing_time:.3f}s - 路径长度: {len(result.get('path', []))}")
        
        self.experiment_results.extend(results)
        return results
    
    def run_batch_experiments(self, test_cases: List[Tuple[str, str]], congestion_levels: List[str] = None) -> List[Dict]:
        """
        运行批量实验
        
        Args:
            test_cases: 测试用例列表，每个元素为 (start_node, end_node)
            congestion_levels: 拥堵级别列表
            
        Returns:
            所有实验结果列表
        """
        all_results = []
        
        for start, end in test_cases:
            print(f"🚗 开始测试: {start} -> {end}")
            results = self.run_experiment(start, end, congestion_levels)
            all_results.extend(results)
        
        return all_results
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """
        分析实验结果
        
        Args:
            results: 实验结果列表
            
        Returns:
            分析结果字典
        """
        # 按拥堵级别和算法分组
        by_congestion_algorithm = {}
        for result in results:
            level = result["congestion_level"]
            algo = result["algorithm"]
            if level not in by_congestion_algorithm:
                by_congestion_algorithm[level] = {}
            if algo not in by_congestion_algorithm[level]:
                by_congestion_algorithm[level][algo] = []
            by_congestion_algorithm[level][algo].append(result)
        
        # 计算每个拥堵级别和算法的统计数据
        analysis = {
            "by_congestion_algorithm": {},
            "algorithm_comparison": {},
            "overall_analysis": {},
            "paper_data": {}
        }
        
        # 分析每个拥堵级别
        for level, algo_results in by_congestion_algorithm.items():
            analysis["by_congestion_algorithm"][level] = {}
            
            # 分析每种算法
            for algo, results in algo_results.items():
                processing_times = [r["processing_time"] for r in results]
                path_lengths = [r["path_length"] for r in results]
                path_weights = [r["path_weight"] for r in results]
                path_durations = [r["path_duration"] for r in results]
                path_congestions = [r["path_congestion"] for r in results]
                
                # 计算成功率：只要路径长度大于0，就认为成功
                successful_cases = sum(1 for r in results if r["path_length"] > 0)
                success_rate = successful_cases / len(results) * 100
                
                # 计算交通效率评分（1/平均到达时间）
                if sum(path_durations) > 0:
                    traffic_efficiency = 1 / (sum(path_durations) / len(path_durations))
                else:
                    traffic_efficiency = 0
                
                analysis["by_congestion_algorithm"][level][algo] = {
                    "average_processing_time": sum(processing_times) / len(processing_times),
                    "average_path_length": sum(path_lengths) / len(path_lengths),
                    "average_path_weight": sum(path_weights) / len(path_weights),
                    "average_path_duration": sum(path_durations) / len(path_durations),
                    "average_path_congestion": sum(path_congestions) / len(path_congestions),
                    "traffic_efficiency": traffic_efficiency,
                    "test_cases": len(results),
                    "successful_cases": successful_cases,
                    "success_rate": success_rate
                }
        
        # 生成算法对比分析
        congestion_levels = list(by_congestion_algorithm.keys())
        algorithms = list(next(iter(by_congestion_algorithm.values())).keys())
        
        analysis["algorithm_comparison"] = {}
        for level in congestion_levels:
            analysis["algorithm_comparison"][level] = {
                "time_improvement": {},
                "efficiency_improvement": {},
                "weight_reduction": {}
            }
            
            # 计算算法之间的对比
            if "SP" in by_congestion_algorithm[level] and "D-KSPP" in by_congestion_algorithm[level]:
                sp_stats = analysis["by_congestion_algorithm"][level]["SP"]
                dkspp_stats = analysis["by_congestion_algorithm"][level]["D-KSPP"]
                
                # 时间改进
                if sp_stats["average_path_duration"] > 0:
                    time_improvement = ((sp_stats["average_path_duration"] - dkspp_stats["average_path_duration"]) / 
                                       sp_stats["average_path_duration"]) * 100
                else:
                    time_improvement = 0
                
                # 效率改进
                if sp_stats["traffic_efficiency"] > 0:
                    efficiency_improvement = ((dkspp_stats["traffic_efficiency"] - sp_stats["traffic_efficiency"]) / 
                                           sp_stats["traffic_efficiency"]) * 100
                else:
                    efficiency_improvement = 0
                
                # 权重减少
                if sp_stats["average_path_weight"] > 0:
                    weight_reduction = ((sp_stats["average_path_weight"] - dkspp_stats["average_path_weight"]) / 
                                      sp_stats["average_path_weight"]) * 100
                else:
                    weight_reduction = 0
                
                analysis["algorithm_comparison"][level]["time_improvement"] = time_improvement
                analysis["algorithm_comparison"][level]["efficiency_improvement"] = efficiency_improvement
                analysis["algorithm_comparison"][level]["weight_reduction"] = weight_reduction
                analysis["algorithm_comparison"][level]["sp_stats"] = sp_stats
                analysis["algorithm_comparison"][level]["dkspp_stats"] = dkspp_stats
        
        # 生成总体分析
        analysis["overall_analysis"] = {
            "total_test_cases": len(results),
            "congestion_levels": congestion_levels,
            "algorithms": algorithms,
            "best_algorithm_by_scenario": {}
        }
        
        # 确定每个场景下的最佳算法
        for level in congestion_levels:
            if "SP" in by_congestion_algorithm[level] and "D-KSPP" in by_congestion_algorithm[level]:
                sp_stats = analysis["by_congestion_algorithm"][level]["SP"]
                dkspp_stats = analysis["by_congestion_algorithm"][level]["D-KSPP"]
                
                # 基于交通效率选择最佳算法
                if dkspp_stats["traffic_efficiency"] > sp_stats["traffic_efficiency"]:
                    best_algorithm = "D-KSPP"
                else:
                    best_algorithm = "SP"
                
                analysis["overall_analysis"]["best_algorithm_by_scenario"][level] = best_algorithm
        
        # 生成论文支撑数据
        analysis["paper_data"] = {
            "arrival_time_comparison": {},
            "efficiency_comparison": {},
            "congestion_impact": []
        }
        
        for level in congestion_levels:
            if "SP" in by_congestion_algorithm[level] and "D-KSPP" in by_congestion_algorithm[level]:
                sp_stats = analysis["by_congestion_algorithm"][level]["SP"]
                dkspp_stats = analysis["by_congestion_algorithm"][level]["D-KSPP"]
                comp = analysis["algorithm_comparison"][level]
                
                analysis["paper_data"]["arrival_time_comparison"][level] = {
                    "SP_avg_arrival_time_sec": sp_stats["average_path_duration"],
                    "D_KSPP_avg_arrival_time_sec": dkspp_stats["average_path_duration"],
                    "improvement_percent": comp["time_improvement"]
                }
                
                analysis["paper_data"]["efficiency_comparison"][level] = {
                    "SP_efficiency": sp_stats["traffic_efficiency"],
                    "D_KSPP_efficiency": dkspp_stats["traffic_efficiency"],
                    "improvement_percent": comp["efficiency_improvement"]
                }
                
                # 计算拥堵影响
                analysis["paper_data"]["congestion_impact"].append({
                    "scenario": level,
                    "sp_efficiency": sp_stats["traffic_efficiency"],
                    "dkspp_efficiency": dkspp_stats["traffic_efficiency"],
                    "efficiency_improvement": comp["efficiency_improvement"]
                })
        
        return analysis
    
    def save_results(self, results: List[Dict], filename: str) -> None:
        """
        保存实验结果到文件
        
        Args:
            results: 实验结果列表
            filename: 文件名
        """
        # 转换元组为字符串以支持JSON序列化
        def convert_tuples(obj):
            if isinstance(obj, dict):
                return {convert_tuples(k): convert_tuples(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_tuples(item) for item in obj]
            elif isinstance(obj, tuple):
                return str(obj)
            else:
                return obj
        
        # 转换结果
        converted_results = convert_tuples(results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(converted_results, f, ensure_ascii=False, indent=2)
        print(f"💾 实验结果已保存到: {filename}")
    
    def save_analysis(self, analysis: Dict, filename: str) -> None:
        """
        保存分析结果到文件
        
        Args:
            analysis: 分析结果字典
            filename: 文件名
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"💾 分析结果已保存到: {filename}")

if __name__ == "__main__":
    """
    运行大规模拥堵场景实验
    """
    print("🚀 开始大规模拥堵场景实验...")
    
    # 初始化实验
    experiment = CongestionExperiment()
    
    # 定义测试用例（覆盖不同距离和复杂度的路径）
    test_cases = [
        ("A", "Z"),  # 长距离
        ("B", "Y"),  # 长距离
        ("C", "X"),  # 长距离
        ("D", "W"),  # 长距离
        ("E", "V"),  # 长距离
        ("F", "K"),  # 中距离
        ("G", "N"),  # 中距离
        ("H", "O"),  # 中距离
        ("I", "L"),  # 中距离
        ("J", "M"),  # 中距离
    ]
    
    # 定义拥堵级别
    congestion_levels = ["light", "moderate", "heavy", "extreme"]
    
    # 运行批量实验
    print(f"📋 运行 {len(test_cases)} 个测试用例，每个用例测试 {len(congestion_levels)} 个拥堵级别...")
    results = experiment.run_batch_experiments(test_cases, congestion_levels)
    
    # 分析结果
    print("📈 分析实验结果...")
    analysis = experiment.analyze_results(results)
    
    # 保存结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"experiments/results/congestion_experiment_final_{timestamp}.json"
    analysis_file = f"experiments/results/congestion_analysis_final_{timestamp}.json"
    
    experiment.save_results(results, results_file)
    experiment.save_analysis(analysis, analysis_file)
    
    # 打印详细分析结果
    print("\n" + "=" * 100)
    print("📊 大规模拥堵场景实验分析报告")
    print("=" * 100)
    
    # 打印总体分析
    print("\n📈 总体分析:")
    print(f"  • 总测试用例数: {analysis['overall_analysis']['total_test_cases']}")
    print(f"  • 测试拥堵级别: {', '.join(analysis['overall_analysis']['congestion_levels'])}")
    print(f"  • 测试算法: {', '.join(analysis['overall_analysis']['algorithms'])}")
    print(f"  • 每个场景最佳算法: {analysis['overall_analysis']['best_algorithm_by_scenario']}")
    
    # 打印算法对比分析
    print("\n" + "-" * 80)
    print("🏆 算法对比分析:")
    print("-" * 80)
    
    for level in analysis['algorithm_comparison']:
        comp = analysis['algorithm_comparison'][level]
        print(f"\n📋 拥堵场景: {level.upper()}")
        print(f"  • 时间改进: {comp['time_improvement']:.2f}%")
        print(f"  • 效率改进: {comp['efficiency_improvement']:.2f}%")
        print(f"  • 权重减少: {comp['weight_reduction']:.2f}%")
        
        # 打印每种算法的详细数据
        print(f"  \n  SP算法:")
        print(f"    - 平均处理时间: {comp['sp_stats']['average_processing_time']:.3f}s")
        print(f"    - 平均路径长度: {comp['sp_stats']['average_path_length']:.1f} 节点")
        print(f"    - 平均路径时间: {comp['sp_stats']['average_path_duration']:.2f}s")
        print(f"    - 交通效率: {comp['sp_stats']['traffic_efficiency']:.4f}")
        print(f"    - 成功率: {comp['sp_stats']['success_rate']:.2f}%")
        
        print(f"  \n  D-KSPP算法:")
        print(f"    - 平均处理时间: {comp['dkspp_stats']['average_processing_time']:.3f}s")
        print(f"    - 平均路径长度: {comp['dkspp_stats']['average_path_length']:.1f} 节点")
        print(f"    - 平均路径时间: {comp['dkspp_stats']['average_path_duration']:.2f}s")
        print(f"    - 交通效率: {comp['dkspp_stats']['traffic_efficiency']:.4f}")
        print(f"    - 成功率: {comp['dkspp_stats']['success_rate']:.2f}%")
    
    # 打印论文支撑数据
    print("\n" + "-" * 80)
    print("📚 论文支撑数据:")
    print("-" * 80)
    
    print("\n1. 到达时间对比:")
    for level, data in analysis['paper_data']['arrival_time_comparison'].items():
        print(f"  • {level}: SP={data['SP_avg_arrival_time_sec']:.2f}s, D-KSPP={data['D_KSPP_avg_arrival_time_sec']:.2f}s, 改进{data['improvement_percent']:.2f}%")
    
    print("\n2. 效率对比:")
    for level, data in analysis['paper_data']['efficiency_comparison'].items():
        print(f"  • {level}: SP={data['SP_efficiency']:.4f}, D-KSPP={data['D_KSPP_efficiency']:.4f}, 改进{data['improvement_percent']:.2f}%")
    
    print("\n3. 拥堵影响分析:")
    for impact in analysis['paper_data']['congestion_impact']:
        print(f"  • 场景: {impact['scenario']}, 效率改进: {impact['efficiency_improvement']:.2f}%")
    
    # 打印保存信息
    print("\n" + "=" * 100)
    print("💾 实验结果保存:")
    print(f"  • 原始实验数据: {results_file}")
    print(f"  • 分析结果数据: {analysis_file}")
    print("=" * 100)
    
    print("\n🎉 实验完成！成功生成详细的算法对比分析报告。")
