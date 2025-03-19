import pytest
from backend.app.core.blockchain import BlockchainManager

def test_identity_hash_generation():
    """
    测试身份哈希生成
    1. 验证哈希生成
    2. 检查哈希格式
    3. 相同输入生成相同哈希
    """
    blockchain_manager = BlockchainManager()
    
    # 测试用户ID
    user_id = "test_user_123"
    
    # 生成身份哈希
    hash1 = blockchain_manager.get_identity_hash(user_id)
    hash2 = blockchain_manager.get_identity_hash(user_id)
    
    # 验证哈希
    assert hash1 is not None
    assert isinstance(hash1, str)
    assert hash1.startswith('0x')
    assert len(hash1) == 66  # 0x + 64位哈希
    
    # 相同输入生成相同哈希
    assert hash1 == hash2

def test_blockchain_identity_registration():
    """
    测试区块链身份注册
    1. 注册身份
    2. 验证交易哈希
    3. 检查注册过程
    """
    blockchain_manager = BlockchainManager()
    
    # 测试数据
    user_id = "blockchain_test_user"
    user_address = "0x1234567890123456789012345678901234567890"
    
    # 注册身份
    transaction_hash = blockchain_manager.register_identity(user_id, user_address)
    
    # 验证交易哈希
    assert transaction_hash is not None
    assert isinstance(transaction_hash, str)
    assert transaction_hash.startswith('0x')
    assert len(transaction_hash) == 66  # 标准以太坊交易哈希长度

def test_invalid_blockchain_address():
    """
    测试无效的区块链地址
    1. 验证地址验证方法
    2. 测试各种无效地址
    """
    blockchain_manager = BlockchainManager()
    
    # 测试无效地址
    invalid_addresses = [
        "0x123",  # 地址太短
        "12345678901234567890123456789012345678901",  # 不以0x开头
        "0xGGGGG",  # 包含非法字符
        "",  # 空地址
        None  # 空值
    ]
    
    for invalid_addr in invalid_addresses:
        with pytest.raises(ValueError):
            blockchain_manager.register_identity("test_user", invalid_addr)

def test_blockchain_verification_status():
    """
    测试区块链上的身份验证状态
    1. 注册身份
    2. 检查验证状态
    """
    blockchain_manager = BlockchainManager()
    
    # 测试数据
    user_id = "verification_status_test"
    verification_type = "KYC"
    
    # 检查初始状态
    initial_status = blockchain_manager.check_verification_status(user_id, verification_type)
    assert initial_status is False
    
    # 模拟验证过程（实际实现可能需要调整）
    blockchain_manager.verify_identity(
        user_id, 
        "0x1234567890123456789012345678901234567890",  # 验证者地址
        verification_type
    )
    
    # 再次检查状态
    updated_status = blockchain_manager.check_verification_status(user_id, verification_type)
    assert updated_status is True