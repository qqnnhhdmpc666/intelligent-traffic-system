"""
数据库配置和连接
迁移自Django ORM到SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./traffic.db")

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明式基类
Base = declarative_base()

def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

def init_database():
    """初始化数据库"""
    create_tables()
    print("数据库初始化完成")

# 导入所有模型以确保它们被注册
from models import TrafficRecord, RoadNetwork, RouteCache