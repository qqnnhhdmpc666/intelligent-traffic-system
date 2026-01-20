#!/usr/bin/env python3
"""简单路径测试"""

import sys
import os

# 从FastAPI_Server/routers/ 模拟
current_file = os.path.abspath(__file__)
routers_dir = os.path.dirname(current_file)
fastapi_dir = os.path.dirname(routers_dir)

print(f"Current file: {current_file}")
print(f"Routers dir: {routers_dir}")
print(f"FastAPI dir: {fastapi_dir}")

# 计算路径
path_to_add = os.path.join(routers_dir, '..', '..', '..', 'Server')
absolute_path = os.path.abspath(path_to_add)

print(f"Path to add: {path_to_add}")
print(f"Absolute path: {absolute_path}")
print(f"Server exists: {os.path.exists(absolute_path)}")

if os.path.exists(absolute_path):
    core_path = os.path.join(absolute_path, 'core')
    print(f"Core exists: {os.path.exists(core_path)}")

    if os.path.exists(core_path):
        sys.path.insert(0, absolute_path)
        print(f"Added to path: {absolute_path}")

        try:
            from core.graph import Graph
            print("✅ Graph imported successfully!")
        except ImportError as e:
            print(f"❌ Graph import failed: {e}")