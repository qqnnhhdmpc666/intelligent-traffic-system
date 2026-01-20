"""
图数据结构模块
用于表示和管理交通路网
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
# 简化导入，避免路径问题
RoadNetwork = None  # 先设为None，实际使用时再处理


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
