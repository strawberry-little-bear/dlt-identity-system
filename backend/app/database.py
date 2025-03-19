# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库URL，如果不存在则使用默认SQLite URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./identity_system.db")

# 创建SQLAlchemy引擎
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # 只对SQLite需要
)

# 创建会话类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 获取数据库会话的依赖函数
def get_db():
    """提供数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()