"""
图数据结构模块
用于表示和管理交通路网
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
# 从models.py导入RoadNetwork类
try:
    from ..models import RoadNetwork
except ImportError:
    # 如果导入失败，使用模拟数据
    RoadNetwork = None


class Graph:
    """
    带权有向图类
    用于表示交通路网
    """
    
    def __init__(self):
        """
        初始化图
        - adj: 邻接表，存储 {节点: [(邻居节点, 边权重, 边信息)]}
        - nodes: 节点集合
        - edges: 边信息字典，key为 (from_node, to_node)
        """
        self.adj: Dict[str, List[Tuple[str, float, Dict]]] = defaultdict(list)
        self.nodes: set = set()
        self.edges: Dict[Tuple[str, str], Dict] = {}
    
    def add_edge(self, from_node: str, to_node: str, weight: float, edge_data: Optional[Dict] = None):
        """
        添加有向边
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            weight: 边的权重
            edge_data: 边的附加信息（如道路ID、长度、速度等）
        """
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        
        edge_info = edge_data.copy() if edge_data else {}
        edge_info['weight'] = weight
        
        self.adj[from_node].append((to_node, weight, edge_info))
        self.edges[(from_node, to_node)] = edge_info
    
    def get_neighbors(self, node: str) -> List[Tuple[str, float, Dict]]:
        """
        获取节点的所有邻居
        
        Args:
            node: 节点ID
            
        Returns:
            邻居列表，每个元素为 (邻居节点, 权重, 边信息)
        """
        return self.adj.get(node, [])
    
    def get_edge_weight(self, from_node: str, to_node: str) -> Optional[float]:
        """
        获取边的权重
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            
        Returns:
            边的权重，如果边不存在则返回None
        """
        edge = self.edges.get((from_node, to_node))
        return edge['weight'] if edge else None
    
    def has_edge(self, from_node: str, to_node: str) -> bool:
        """
        判断边是否存在
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            
        Returns:
            边是否存在
        """
        return (from_node, to_node) in self.edges
    
    def get_all_nodes(self) -> List[str]:
        """
        获取所有节点
        
        Returns:
            节点列表
        """
        return list(self.nodes)
    
    def update_edge_weight(self, from_node: str, to_node: str, new_weight: float):
        """
        更新边的权重
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            new_weight: 新的权重
        """
        if (from_node, to_node) in self.edges:
            # 更新edges字典中的权重
            self.edges[(from_node, to_node)]['weight'] = new_weight
            # 更新邻接表中的权重
            for i, (neighbor, _, edge_info) in enumerate(self.adj[from_node]):
                if neighbor == to_node:
                    self.adj[from_node][i] = (neighbor, new_weight, edge_info)
                    break
    
    @classmethod
    def from_database(cls) -> 'Graph':
        """
        从数据库加载路网数据构建图
        
        Returns:
            Graph实例
        """
        graph = cls()
        
        # 检查RoadNetwork是否可用
        if RoadNetwork and hasattr(RoadNetwork, 'objects'):
            # 从数据库加载所有道路
            roads = RoadNetwork.objects.all()
            
            for road in roads:
                # 从JSONField中获取节点ID
                # 假设start_point和end_point是JSON格式，可能是 {"node_id": "A"} 或者直接是字符串
                start_node = road.start_point
                end_node = road.end_point
                
                # 处理不同的数据格式
                if isinstance(start_node, dict):
                    start_node = start_node.get('node_id', str(road.road_id) + '_start')
                if isinstance(end_node, dict):
                    end_node = end_node.get('node_id', str(road.road_id) + '_end')
                
                # 转换为字符串
                start_node = str(start_node)
                end_node = str(end_node)
                
                # 计算动态权重（论文公式）
                # w(e) = α * L(e) / S_max(e) + β * T_current(e)
                # 这里使用默认参数，可以在settings中配置
                alpha = 0.6  # 基础通行时间权重系数
                beta = 0.4   # 实时拥堵延时权重系数
                
                # 获取道路长度（如果为0则使用默认值）
                length = road.length if road.length > 0 else 1.0  # 默认1公里，避免除零
                max_speed = road.max_speed if road.max_speed > 0 else 60.0  # 默认60km/h
                current_congestion = road.current_congestion if road.current_congestion >= 0 else 0.0
                
                # 计算基础通行时间（小时）
                base_time = length / max_speed if max_speed > 0 else length / 60.0
                
                # 计算动态权重（转换为秒）
                # α * L(e) / S_max(e) 转换为秒：乘以3600
                # β * T_current(e) 已经是秒
                dynamic_weight = alpha * base_time * 3600 + beta * current_congestion
                
                # 存储边的附加信息
                edge_data = {
                    'road_id': road.road_id,
                    'length': length,
                    'max_speed': max_speed,
                    'current_congestion': current_congestion,
                }
                
                graph.add_edge(start_node, end_node, dynamic_weight, edge_data)
        else:
            # 如果RoadNetwork不可用，使用模拟数据构建图
            # 模拟一个科学合理的交通网络，使用26个字母作为节点
            print("⚠️  RoadNetwork不可用，使用模拟数据构建图")
            
            # 添加模拟节点和边 - 构建一个网格状的交通网络
            # 设计原则：
            # 1. 节点按26个字母排序，形成一个5x6的网格（A-Z）
            # 2. 相邻节点之间有道路连接
            # 3. 道路长度根据实际距离计算
            # 4. 最大速度根据道路等级设置
            # 5. 拥堵度根据道路位置和重要性设置
            
            mock_edges = []
            road_id_counter = 1
            
            # 定义26个字母节点
            nodes = [chr(ord('A') + i) for i in range(26)]
            
            # 构建网格连接
            # 水平连接（同一行内的相邻节点）
            for i in range(25):
                if (i + 1) % 5 != 0:  # 每5个节点一行
                    from_node = nodes[i]
                    to_node = nodes[i + 1]
                    length = 1.0  # 水平距离1公里
                    max_speed = 60.0  # 城市道路
                    current_congestion = 0.0 + (i % 10) * 0.5  # 轻微拥堵
                    
                    mock_edges.append((
                        from_node,
                        to_node,
                        length / max_speed * 3600,  # 权重：通行时间（秒）
                        {'road_id': f'R{road_id_counter}', 'length': length, 'max_speed': max_speed, 'current_congestion': current_congestion}
                    ))
                    road_id_counter += 1
            
            # 垂直连接（相邻行之间的节点）
            for i in range(20):
                from_node = nodes[i]
                to_node = nodes[i + 5]  # 下行对应的节点
                length = 1.2  # 垂直距离1.2公里
                max_speed = 80.0  # 主干道
                current_congestion = 0.0 + (i % 8) * 0.8  # 中等拥堵
                
                mock_edges.append((
                    from_node,
                    to_node,
                    length / max_speed * 3600,  # 权重：通行时间（秒）
                    {'road_id': f'R{road_id_counter}', 'length': length, 'max_speed': max_speed, 'current_congestion': current_congestion}
                ))
                road_id_counter += 1
            
            # 添加更多的对角线连接（高速公路）
            diagonal_connections = [
                (0, 6),  # A -> G
                (1, 7),  # B -> H
                (2, 8),  # C -> I
                (3, 9),  # D -> J
                (4, 10), # E -> K
                (5, 11), # F -> L
                (6, 12), # G -> M
                (7, 13), # H -> N
                (8, 14), # I -> O
                (9, 15), # J -> P
                (10, 16),# K -> Q
                (11, 17),# L -> R
                (12, 18),# M -> S
                (13, 19),# N -> T
                (14, 20),# O -> U
                (15, 21),# P -> V
                (16, 22),# Q -> W
                (17, 23),# R -> X
                (18, 24),# S -> Y
                (19, 25),# T -> Z
                # 添加更多对角线连接
                (0, 7),  # A -> H
                (1, 8),  # B -> I
                (2, 9),  # C -> J
                (3, 10), # D -> K
                (4, 11), # E -> L
                (5, 12), # F -> M
                (6, 13), # G -> N
                (7, 14), # H -> O
                (8, 15), # I -> P
                (9, 16), # J -> Q
                (10, 17),# K -> R
                (11, 18),# L -> S
                (12, 19),# M -> T
                (13, 20),# N -> U
                (14, 21),# O -> V
                (15, 22),# P -> W
                (16, 23),# Q -> X
                (17, 24),# R -> Y
                (18, 25),# S -> Z
            ]
            
            for from_idx, to_idx in diagonal_connections:
                from_node = nodes[from_idx]
                to_node = nodes[to_idx]
                length = 1.7  # 对角线距离
                max_speed = 100.0  # 高速公路
                current_congestion = 0.0 + (from_idx % 6) * 1.0  # 轻微拥堵
                
                mock_edges.append((
                    from_node,
                    to_node,
                    length / max_speed * 3600,  # 权重：通行时间（秒）
                    {'road_id': f'R{road_id_counter}', 'length': length, 'max_speed': max_speed, 'current_congestion': current_congestion}
                ))
                road_id_counter += 1
            
            # 添加环形连接（环城高速）
            ring_connections = [
                (0, 4),   # A -> E
                (4, 9),   # E -> J
                (9, 14),  # J -> O
                (14, 19), # O -> T
                (19, 24), # T -> Y
                (24, 20), # Y -> U
                (20, 15), # U -> P
                (15, 10), # P -> K
                (10, 5),  # K -> F
                (5, 0),   # F -> A
                # 添加更多环形连接
                (1, 5),   # B -> F
                (5, 10),  # F -> K
                (10, 15), # K -> P
                (15, 20), # P -> U
                (20, 25), # U -> Z
                (25, 21), # Z -> V
                (21, 16), # V -> Q
                (16, 11), # Q -> L
                (11, 6),  # L -> G
                (6, 1),   # G -> B
            ]
            
            for from_idx, to_idx in ring_connections:
                from_node = nodes[from_idx]
                to_node = nodes[to_idx]
                length = 2.0  # 环形道路长度2.0公里
                max_speed = 120.0  # 环城高速
                current_congestion = 0.0 + (from_idx % 5) * 0.5  # 轻微拥堵
                
                mock_edges.append((
                    from_node,
                    to_node,
                    length / max_speed * 3600,  # 权重：通行时间（秒）
                    {'road_id': f'R{road_id_counter}', 'length': length, 'max_speed': max_speed, 'current_congestion': current_congestion}
                ))
                road_id_counter += 1
            
            # 添加一些跨区域的长距离连接
            long_connections = [
                ('A', 'Z', 30.0, {'road_id': f'R{road_id_counter}', 'length': 30.0, 'max_speed': 120.0, 'current_congestion': 5.0}),
                ('B', 'Y', 28.0, {'road_id': f'R{road_id_counter + 1}', 'length': 28.0, 'max_speed': 120.0, 'current_congestion': 4.5}),
                ('C', 'X', 26.0, {'road_id': f'R{road_id_counter + 2}', 'length': 26.0, 'max_speed': 120.0, 'current_congestion': 4.0}),
                ('D', 'W', 24.0, {'road_id': f'R{road_id_counter + 3}', 'length': 24.0, 'max_speed': 120.0, 'current_congestion': 3.5}),
                ('E', 'V', 22.0, {'road_id': f'R{road_id_counter + 4}', 'length': 22.0, 'max_speed': 120.0, 'current_congestion': 3.0}),
            ]
            
            for edge in long_connections:
                mock_edges.append(edge)
            
            for start_node, end_node, weight, edge_data in mock_edges:
                graph.add_edge(start_node, end_node, weight, edge_data)
        
        return graph
    
    def __str__(self):
        """图的字符串表示"""
        return f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)})"
    
    def __repr__(self):
        return self.__str__()


def calculate_distance(point1: Dict, point2: Dict) -> float:
    """
    计算两点之间的距离（如果点是坐标格式）
    
    Args:
        point1: 点1的坐标，格式为 {"lat": float, "lon": float} 或 {"x": float, "y": float}
        point2: 点2的坐标
        
    Returns:
        距离（单位取决于坐标系统）
    """
    # 如果包含经纬度，使用Haversine公式
    if 'lat' in point1 and 'lon' in point1:
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = radians(point1['lat']), radians(point1['lon'])
        lat2, lon2 = radians(point2['lat']), radians(point2['lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # 地球半径（公里）
        return r * c
    
    # 如果包含x, y坐标，使用欧氏距离
    elif 'x' in point1 and 'y' in point1:
        from math import sqrt
        dx = point2['x'] - point1['x']
        dy = point2['y'] - point1['y']
        return sqrt(dx*dx + dy*dy)
    
    # 如果无法计算，返回0
    return 0.0
