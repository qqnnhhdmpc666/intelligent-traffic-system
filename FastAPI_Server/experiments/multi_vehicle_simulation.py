"""
多车辆并发交通仿真
验证D-KSPP避免导航踩踏的效果
"""

import numpy as np
import random
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
from dataclasses import dataclass
import json

# 导入现有路径规划代码
import sys
sys.path.append('..')
from core.pathfinding import Graph, PathFinder


@dataclass
class Vehicle:
    """车辆实体"""
    vehicle_id: int
    start_node: str
    end_node: str
    start_time: float  # 进入系统的时间
    path: List[str