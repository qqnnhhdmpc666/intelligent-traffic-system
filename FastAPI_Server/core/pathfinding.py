"""
路径规划算法模块
实现论文中描述的路径规划算法：
- Dijkstra最短路径算法
- Yen's K短路算法
- Softmax概率分配
"""
import heapq
import math
from typing import List, Tuple, Dict, Optional, Set
# 由于可能存在循环导入，先注释掉Graph导入
# from graph import Graph
# 实际使用时再处理


class Dijkstra:
    """
    Dijkstra最短路径算法
    """
    
    @staticmethod
    def shortest_path(graph: Graph, start: str, end: str) -> Tuple[Optional[List[str]], float]:
        """
        计算从起点到终点的最短路径
        
        Args:
            graph: 图对象
            start: 起始节点
            end: 目标节点
            
        Returns:
            (路径节点列表, 路径总权重) 如果不存在路径则返回 (None, float('inf'))
        """
        if start not in graph.nodes or end not in graph.nodes:
            return None, float('inf')
        
        if start == end:
            return [start], 0.0
        
        # 距离字典，存储从起点到每个节点的最短距离
        dist = {node: float('inf') for node in graph.nodes}
        dist[start] = 0.0
        
        # 前驱节点字典，用于重建路径
        prev = {}
        
        # 优先队列：(距离, 节点)
        pq = [(0.0, start)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            # 如果已经访问过，跳过
            if current in visited:
                continue
            
            visited.add(current)
            
            # 如果到达目标节点，提前退出
            if current == end:
                break
            
            # 遍历邻居节点
            neighbors = graph.get_neighbors(current)
            for neighbor, weight, _ in neighbors:
                if neighbor in visited:
                    continue
                
                # 计算新距离
                new_dist = current_dist + weight
                
                # 如果找到更短的路径，更新
                if new_dist < dist[neighbor]:
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # 如果无法到达目标节点
        if end not in prev and start != end:
            if dist[end] == float('inf'):
                return None, float('inf')
        
        # 重建路径
        if end not in prev and start != end:
            return None, float('inf')
        
        path = []
        current = end
        while current is not None:
            path.insert(0, current)
            current = prev.get(current)
            if current == start:
                path.insert(0, start)
                break
        
        if not path or path[0] != start:
            return None, float('inf')
        
        return path, dist[end]
    
    @staticmethod
    def shortest_path_with_blocked_edges(graph: Graph, start: str, end: str, 
                                        blocked_edges: Set[Tuple[str, str]]) -> Tuple[Optional[List[str]], float]:
        """
        计算最短路径，但排除某些边（用于Yen's算法）
        
        Args:
            graph: 图对象
            start: 起始节点
            end: 目标节点
            blocked_edges: 被阻塞的边集合，元素为 (from_node, to_node)
            
        Returns:
            (路径节点列表, 路径总权重)
        """
        if start not in graph.nodes or end not in graph.nodes:
            return None, float('inf')
        
        if start == end:
            return [start], 0.0
        
        dist = {node: float('inf') for node in graph.nodes}
        dist[start] = 0.0
        prev = {}
        pq = [(0.0, start)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == end:
                break
            
            neighbors = graph.get_neighbors(current)
            for neighbor, weight, _ in neighbors:
                # 检查边是否被阻塞
                if (current, neighbor) in blocked_edges:
                    continue
                
                if neighbor in visited:
                    continue
                
                new_dist = current_dist + weight
                if new_dist < dist[neighbor]:
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        if end not in prev and start != end:
            if dist[end] == float('inf'):
                return None, float('inf')
        
        if end not in prev and start != end:
            return None, float('inf')
        
        path = []
        current = end
        while current is not None:
            path.insert(0, current)
            current = prev.get(current)
            if current == start:
                path.insert(0, start)
                break
        
        if not path or path[0] != start:
            return None, float('inf')
        
        return path, dist[end]


class YensKShortestPaths:
    """
    Yen's K短路算法
    实现论文中描述的K短路算法
    """
    
    @staticmethod
    def k_shortest_paths(graph: Graph, start: str, end: str, k: int = 5) -> List[Tuple[List[str], float]]:
        """
        找出从起点到终点的K条最短路径
        
        Args:
            graph: 图对象
            start: 起始节点
            end: 目标节点
            k: 需要找出的路径数量
            
        Returns:
            路径列表，每个元素为 (路径节点列表, 路径总权重)，按权重递增排序
        """
        # 找到第一条最短路径
        first_path, first_weight = Dijkstra.shortest_path(graph, start, end)
        if first_path is None:
            return []
        
        # 存储所有找到的路径 (路径, 权重)
        A = [(first_path, first_weight)]
        # 候选路径集合 (权重, 路径)
        B = []
        
        for _ in range(1, k):
            # 如果已找到k条路径，退出
            if len(A) >= k:
                break
            
            # 获取最后一条找到的路径
            prev_path, prev_weight = A[-1]
            
            # 遍历路径上的每个节点（除了最后一个）
            for i in range(len(prev_path) - 1):
                # 分支节点（spur node）
                spur_node = prev_path[i]
                # 从起点到分支节点的路径（root path）
                root_path = prev_path[:i+1]
                root_path_cost = YensKShortestPaths._calculate_path_cost(graph, root_path)
                
                # 需要阻塞的边：所有已找到路径中，从分支节点出发的边
                blocked_edges = set()
                for path, _ in A:
                    if len(path) > i + 1:
                        if path[:i+1] == root_path:
                            # 阻塞这条路径中从spur_node出发的边
                            edge = (spur_node, path[i+1])
                            blocked_edges.add(edge)
                
                # 计算从spur_node到终点的最短路径（排除阻塞的边）
                spur_path, spur_cost = Dijkstra.shortest_path_with_blocked_edges(
                    graph, spur_node, end, blocked_edges
                )
                
                if spur_path is not None:
                    # 合并root_path和spur_path（去除重复的spur_node）
                    total_path = root_path[:-1] + spur_path
                    total_cost = root_path_cost - graph.get_edge_weight(root_path[-2], root_path[-1]) if len(root_path) > 1 else 0
                    total_cost += spur_cost
                    
                    # 检查路径是否已经在候选集合中
                    if (total_path, total_cost) not in B and (total_path, total_cost) not in A:
                        heapq.heappush(B, (total_cost, total_path))
            
            # 如果候选集合为空，无法找到更多路径
            if not B:
                break
            
            # 从候选集合中取出最短的路径
            cost, path = heapq.heappop(B)
            A.append((path, cost))
        
        return A
    
    @staticmethod
    def _calculate_path_cost(graph: Graph, path: List[str]) -> float:
        """
        计算路径的总成本
        
        Args:
            graph: 图对象
            path: 路径节点列表
            
        Returns:
            路径总成本
        """
        if len(path) < 2:
            return 0.0
        
        total_cost = 0.0
        for i in range(len(path) - 1):
            weight = graph.get_edge_weight(path[i], path[i+1])
            if weight is None:
                return float('inf')
            total_cost += weight
        
        return total_cost


class SoftmaxSelector:
    """
    Softmax概率分配模型
    实现论文中描述的Softmax概率分配
    """
    
    @staticmethod
    def calculate_probabilities(paths: List[Tuple[List[str], float]], 
                               temperature: float = 1.0) -> List[float]:
        """
        使用Softmax函数计算每条路径的选择概率
        
        Args:
            paths: 路径列表，每个元素为 (路径节点列表, 路径成本)
            temperature: 温度系数τ，控制随机性。越小越确定性，越大越随机
            
        Returns:
            每条路径的选择概率列表
        """
        if not paths:
            return []
        
        if temperature <= 0:
            temperature = 1e-10  # 避免除零
        
        # 计算每条路径的效用（效用 = -成本）
        utilities = [-cost for _, cost in paths]
        
        # 使用Softmax函数计算概率
        # Prob(P_i) = exp(U(P_i) / τ) / Σ exp(U(P_j) / τ)
        exp_utilities = [math.exp(u / temperature) for u in utilities]
        sum_exp = sum(exp_utilities)
        
        probabilities = [exp_u / sum_exp for exp_u in exp_utilities]
        
        return probabilities
    
    @staticmethod
    def select_path(paths: List[Tuple[List[str], float]], 
                   probabilities: List[float]) -> Tuple[List[str], float]:
        """
        根据概率分布随机选择一条路径
        
        Args:
            paths: 路径列表
            probabilities: 每条路径的概率
            
        Returns:
            选中的路径 (路径节点列表, 路径成本)
        """
        import random
        
        if not paths or not probabilities:
            raise ValueError("Paths and probabilities cannot be empty")
        
        # 使用累积概率分布进行随机采样
        cumsum = 0.0
        r = random.random()
        
        for i, prob in enumerate(probabilities):
            cumsum += prob
            if r <= cumsum:
                return paths[i]
        
        # 如果由于浮点误差没有选中，返回最后一条路径
        return paths[-1]
