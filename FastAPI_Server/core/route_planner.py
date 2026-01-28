"""
路径规划器模块
实现论文中描述的完整路径规划算法
"""
import time
from typing import Dict, List, Optional, Tuple
# 同一目录下的导入
try:
    from .graph import Graph
    from .pathfinding import Dijkstra, YensKShortestPaths, SoftmaxSelector
except ImportError:
    # 如果相对导入失败，使用绝对导入
    from graph import Graph
    from pathfinding import Dijkstra, YensKShortestPaths, SoftmaxSelector
# 配置参数（硬编码，避免Django依赖）
K_SHORTEST_PATHS = 25     # K短路算法的K值（大幅增加以提高路径多样性）
SOFTMAX_TEMPERATURE = 0.08  # Softmax温度系数（进一步降低以提高选择质量）
WEIGHT_ALPHA = 0.1         # 权重系数α（保持以增加拥堵的影响）
WEIGHT_BETA = 0.9          # 权重系数β（保持以增加拥堵的影响）


class GraphCache:
    """图缓存管理器 - 性能优化"""

    def __init__(self, cache_ttl: int = 300):
        self._graph = None
        self._last_update = 0
        self._cache_ttl = cache_ttl  # 缓存有效期（秒）
        self._cache_hits = 0
        self._cache_misses = 0

    def get_graph(self):
        """获取缓存的图，如果过期则重新加载"""
        current_time = time.time()

        if (self._graph is None or
            current_time - self._last_update > self._cache_ttl):
            # 缓存过期，重新加载
            self._graph = Graph.from_database()
            self._last_update = current_time
            self._cache_misses += 1
            print(f"🔄 图缓存已更新 (缓存未命中: {self._cache_misses})")
        else:
            self._cache_hits += 1

        return self._graph

    def invalidate_cache(self):
        """强制失效缓存"""
        self._graph = None
        self._last_update = 0

    def get_cache_stats(self):
        """获取缓存统计信息"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "last_update": self._last_update,
            "cache_ttl": self._cache_ttl
        }

class PathCache:
    """路径结果缓存 - 性能优化"""

    def __init__(self, max_size: int = 1000, ttl: int = 600):
        self._cache = {}
        self._max_size = max_size
        self._ttl = ttl  # 缓存有效期（秒）
        self._hits = 0
        self._misses = 0

    def _make_key(self, start: str, end: str, vehicle_type: str) -> str:
        """生成缓存键"""
        return f"{start}_{end}_{vehicle_type}"

    def get_path(self, start: str, end: str, vehicle_type: str):
        """获取缓存的路径"""
        key = self._make_key(start, end, vehicle_type)
        current_time = time.time()

        if key in self._cache:
            cached_item = self._cache[key]
            # 检查是否过期
            if current_time - cached_item['cached_at'] < self._ttl:
                self._hits += 1
                return cached_item['data']
            else:
                # 过期删除
                del self._cache[key]

        self._misses += 1
        return None

    def set_path(self, start: str, end: str, vehicle_type: str, path_data: dict):
        """缓存路径结果"""
        key = self._make_key(start, end, vehicle_type)

        # 检查缓存大小，如果满了删除最旧的
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(),
                           key=lambda k: self._cache[k]['cached_at'])
            del self._cache[oldest_key]

        # 存储缓存
        self._cache[key] = {
            'data': path_data,
            'cached_at': time.time()
        }

    def clear_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items()
            if current_time - item['cached_at'] > self._ttl
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            print(f"🧹 清理了 {len(expired_keys)} 个过期路径缓存")

    def get_cache_stats(self):
        """获取缓存统计信息"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "max_size": self._max_size,
            "ttl": self._ttl
        }

class RoutePlanner:
    """
    路径规划器
    实现论文中描述的动态路径规划算法（D-KSPP）
    已集成性能优化缓存机制
    """

    # 配置参数（使用上方定义的常量）
    K_SHORTEST_PATHS = K_SHORTEST_PATHS
    SOFTMAX_TEMPERATURE = SOFTMAX_TEMPERATURE
    WEIGHT_ALPHA = WEIGHT_ALPHA
    WEIGHT_BETA = WEIGHT_BETA

    def __init__(self):
        """初始化路径规划器"""
        # 性能优化缓存
        self.graph_cache = GraphCache(cache_ttl=300)  # 5分钟缓存
        self.path_cache = PathCache(max_size=1000, ttl=600)  # 1000个路径，10分钟过期
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        return {
            "graph_cache": self.graph_cache.get_cache_stats(),
            "path_cache": self.path_cache.get_cache_stats()
        }
    
    def plan_route(self, start: str, end: str, vehicle_type: str = "normal") -> Dict:
        """
        规划路径（主要方法）- 已集成缓存优化

        Args:
            start: 起始节点ID
            end: 目标节点ID
            vehicle_type: 车辆类型（"normal" 或 "emergency"）

        Returns:
            路径信息字典，包含：
            - path: 路径节点列表
            - weight: 路径总权重（成本）
            - distance: 路径总距离（公里）
            - duration: 预计通行时间（秒）
            - message: 消息
            - cached: 是否来自缓存
        """
        start_time = time.time()

        # 1. 检查路径缓存
        cached_result = self.path_cache.get_path(start, end, vehicle_type)
        if cached_result:
            cached_result['cached'] = True
            cached_result['processing_time'] = time.time() - start_time
            # 确保缓存结果中包含all_paths字段
            if 'all_paths' not in cached_result:
                cached_result['all_paths'] = None
            return cached_result
        
        # 获取图（使用缓存优化）
        graph = self.graph_cache.get_graph()

        # 检查图是否为空
        if not graph or len(graph.nodes) == 0:
            return {
                'path': [],
                'weight': 0,
                'distance': 0,
                'duration': 0,
                'congestion': 0,
                'message': '路网数据为空，请先导入路网数据',
                'cached': False
            }

        # 转换为字符串
        start = str(start)
        end = str(end)

        # 检查节点是否存在
        if start not in graph.nodes:
            return {
                'path': [],
                'weight': 0,
                'distance': 0,
                'duration': 0,
                'congestion': 0,
                'message': f'起始节点 {start} 不存在',
                'cached': False
            }

        if end not in graph.nodes:
            return {
                'path': [],
                'weight': 0,
                'distance': 0,
                'duration': 0,
                'congestion': 0,
                'message': f'目标节点 {end} 不存在',
                'cached': False
            }

        if start == end:
            result = {
                'path': [start],
                'weight': 0,
                'distance': 0,
                'duration': 0,
                'congestion': 0,
                'message': '起始节点和目标节点相同',
                'cached': False
            }
            # 缓存结果
            self.path_cache.set_path(start, end, vehicle_type, result)
            return result

        # 特殊车辆优先处理（论文3.2.4节）
        if vehicle_type == "emergency":
            path, weight = Dijkstra.shortest_path(graph, start, end)
            if path is None:
                result = {
                    'path': [],
                    'weight': 0,
                    'distance': 0,
                    'duration': 0,
                    'congestion': 0,
                    'message': '无法找到路径',
                    'cached': False
                }
                self.path_cache.set_path(start, end, vehicle_type, result)
                return result
            
            # 计算路径的详细信息
            distance, duration, congestion = self._calculate_path_details(path, graph)
            processing_time = time.time() - start_time
            
            return {
                'path': path,
                'weight': weight,
                'distance': distance,
                'duration': duration,
                'congestion': congestion,
                'message': '特殊车辆最短路径',
                'processing_time': processing_time
            }
        
        # 普通车辆：使用K短路+Softmax概率分配（论文3.2.2和3.2.3节）
        # 1. 计算K条最短路径
        k_paths = YensKShortestPaths.k_shortest_paths(
            graph, start, end, k=self.K_SHORTEST_PATHS
        )

        if not k_paths:
            result = {
                'path': [],
                'weight': 0,
                'distance': 0,
                'duration': 0,
                'congestion': 0,
                'message': '无法找到路径',
                'cached': False
            }
            self.path_cache.set_path(start, end, vehicle_type, result)
            return result
        
        # 2. 计算每条路径的概率
        probabilities = SoftmaxSelector.calculate_probabilities(
            k_paths, temperature=self.SOFTMAX_TEMPERATURE
        )
        
        # 计算每条路径的详细信息
        paths_with_details = []
        for i, (path, weight) in enumerate(k_paths):
            distance, duration, congestion = self._calculate_path_details(path, graph)
            paths_with_details.append({
                'path': path,
                'weight': weight,
                'distance': distance,
                'duration': duration,
                'congestion': congestion,
                'probability': probabilities[i],
                'rank': i + 1
            })
        
        # 为路径添加标签
        if paths_with_details:
            # 找到最短距离的路径
            shortest_distance = min(paths_with_details, key=lambda x: x['distance'])
            shortest_distance['label'] = '最短距离'
            
            # 找到最快时间的路径
            fastest_time = min(paths_with_details, key=lambda x: x['duration'])
            fastest_time['label'] = '最快时间'
            
            # 找到最畅通的路径
            least_congested = min(paths_with_details, key=lambda x: x['congestion'])
            least_congested['label'] = '最畅通'
            
            # 找到最高概率的路径
            highest_probability = max(paths_with_details, key=lambda x: x['probability'])
            highest_probability['label'] = '推荐路径'
        
        # 选择默认路径（在拥堵场景中优先规避拥堵路段）
        if paths_with_details:
            # 计算每条路径的拥堵程度和时间
            max_congestion = max(p['congestion'] for p in paths_with_details) if paths_with_details else 0
            avg_duration = sum(p['duration'] for p in paths_with_details) / len(paths_with_details) if paths_with_details else 0
            avg_congestion = sum(p['congestion'] for p in paths_with_details) / len(paths_with_details) if paths_with_details else 0
            min_duration = min(p['duration'] for p in paths_with_details) if paths_with_details else 0
            max_duration = max(p['duration'] for p in paths_with_details) if paths_with_details else 0
            
            # 计算每条路径的评分
            for p in paths_with_details:
                # 基础时间评分（权重最高）
                time_score = p['duration'] * 1.0
                
                # 拥堵惩罚（激进增强极端拥堵下的惩罚力度）
                if max_congestion > 0:
                    # 动态调整拥堵惩罚权重，拥堵越严重，惩罚权重越大
                    congestion_weight = 0.6  # 进一步增加基础权重
                    if p['congestion'] > avg_congestion * 2.0:  # 更严格的阈值
                        congestion_weight = 3.0  # 大幅增加严重拥堵的惩罚
                    elif p['congestion'] > avg_congestion * 1.5:
                        congestion_weight = 2.0  # 进一步增加中度拥堵的惩罚
                    elif p['congestion'] > avg_congestion:
                        congestion_weight = 1.2  # 进一步增加轻微拥堵的惩罚
                    
                    # 改进拥堵惩罚计算，使用更强烈的非线性惩罚函数
                    congestion_ratio = p['congestion'] / max_congestion
                    congestion_penalty = (congestion_ratio ** 3) * avg_duration * congestion_weight  # 立方函数大幅增强惩罚
                else:
                    congestion_penalty = 0
                
                # 路径长度惩罚（避免路径过长，惩罚较轻）
                path_length_penalty = (len(p['path']) - 2) * 0.3  # 减少路径长度惩罚，鼓励绕开拥堵路段
                
                # 时间接近度奖励（如果路径时间接近最短时间，给予奖励）
                time_proximity_bonus = 0
                if min_duration > 0 and p['duration'] <= min_duration * 1.15:  # 放宽时间接近度阈值
                    time_proximity_bonus = - (min_duration * 0.15)  # 增加时间奖励
                
                # 拥堵分布奖励（如果路径拥堵低于平均水平，给予额外奖励）
                congestion_bonus = 0
                if avg_congestion > 0 and p['congestion'] < avg_congestion * 0.8:
                    congestion_bonus = - (avg_congestion * 0.2)  # 拥堵低于平均水平的奖励
                
                # 综合评分 = 时间评分 + 拥堵惩罚 + 路径长度惩罚 + 时间接近度奖励 + 拥堵分布奖励
                p['comprehensive_score'] = time_score + congestion_penalty + path_length_penalty + time_proximity_bonus + congestion_bonus
            
            # 选择综合评分最低的路径
            selected_path_info = min(paths_with_details, key=lambda x: x['comprehensive_score'])
        else:
            selected_path_info = None
        
        processing_time = time.time() - start_time
        
        result = {
            'path': selected_path_info['path'] if selected_path_info else [],
            'weight': selected_path_info['weight'] if selected_path_info else 0,
            'distance': selected_path_info['distance'] if selected_path_info else 0,
            'duration': selected_path_info['duration'] if selected_path_info else 0,
            'congestion': selected_path_info['congestion'] if selected_path_info else 0,
            'message': '路径规划成功',
            'processing_time': processing_time,
            'alternative_paths': len(k_paths),  # 备选路径数量
            'probabilities': probabilities,  # 各路径的选择概率（用于调试）
            'cached': False,
            'all_paths': paths_with_details  # 返回所有路径及其详细信息
        }

        # 缓存计算结果
        self.path_cache.set_path(start, end, vehicle_type, result)

        return result
    
    def _calculate_path_details(self, path: List[str], graph) -> Tuple[float, float, float]:
        """
        计算路径的详细信息

        Args:
            path: 路径节点列表
            graph: 图对象

        Returns:
            (总距离, 预计时间, 总拥堵延时)
        """
        if len(path) < 2:
            return 0.0, 0.0, 0.0

        total_distance = 0.0
        total_duration = 0.0
        total_congestion = 0.0

        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]

            # 获取边的信息
            edge = graph.edges.get((from_node, to_node))
            if edge:
                total_distance += edge.get('length', 0.0)
                total_congestion += edge.get('current_congestion', 0.0)

        # 预计时间 = 权重（已经包含了距离和拥堵）
        total_duration = sum(
            graph.get_edge_weight(path[i], path[i+1])
            for i in range(len(path) - 1)
            if graph.get_edge_weight(path[i], path[i+1]) is not None
        )

        return total_distance, total_duration, total_congestion
    
    @staticmethod
    def get_optimal_route(start: str, end: str, vehicle_type: str = "normal") -> Dict:
        """
        静态方法接口（保持向后兼容）
        
        Args:
            start: 起始节点ID
            end: 目标节点ID
            vehicle_type: 车辆类型
            
        Returns:
            路径信息字典
        """
        planner = RoutePlanner()
        return planner.plan_route(start, end, vehicle_type)
