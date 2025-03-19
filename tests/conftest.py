import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 导入您的主应用和数据库相关模块
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.core.blockchain import BlockchainManager

# 创建测试数据库引擎（使用内存SQLite）
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 模拟区块链管理器，用于测试
class MockBlockchainManager:
    def __init__(self):
        self.contract = None
    
    def register_identity(self, user_id, user_address):
        """
        模拟区块链身份注册
        返回一个模拟的交易哈希
        """
        return "0x" + "1" * 64
    
    def get_identity_hash(self, user_id):
        """
        模拟生成身份哈希
        """
        return f"0x{hash(user_id)}"

@pytest.fixture(scope="function")
def client():
    """
    创建测试客户端
    每个测试函数运行前重新创建数据库表
    """
    # 创建所有数据库表
    Base.metadata.create_all(bind=engine)
    
    # 重写数据库依赖
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # 重写区块链管理器
    def override_blockchain_manager():
        return MockBlockchainManager()
    
    # 覆盖应用中的依赖
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[BlockchainManager] = override_blockchain_manager
    
    # 创建测试客户端
    test_client = TestClient(app)
    
    yield test_client
    
    # 清理
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db():
    """
    创建测试数据库会话
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()