from fastapi import status
import pytest

def test_create_verification_request(client):
    """
    测试创建身份验证请求
    1. 先注册用户
    2. 创建验证请求
    3. 验证请求创建成功
    """
    # 注册用户
    register_data = {
        "username": "verifyuser",
        "email": "verify@example.com",
        "password": "verify_password_123",
        "full_name": "Verify User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    register_response = client.post("/api/users/register", json=register_data)
    user_id = register_response.json()['id']
    
    # 登录获取token
    login_data = {
        "username": "verifyuser",
        "password": "verify_password_123"
    }
    login_response = client.post("/api/users/login", json=login_data)
    access_token = login_response.json()['access_token']
    
    # 创建验证请求
    verification_data = {
        "user_id": user_id,
        "verification_type": "KYC",
        "notes": "测试身份验证"
    }
    
    response = client.post(
        "/api/verifications/request", 
        json=verification_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 验证请求创建结果
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data['user_id'] == user_id
    assert response_data['verification_type'] == "KYC"
    assert response_data['status'] == "pending"

def test_duplicate_verification_request(client):
    """
    测试重复创建验证请求
    1. 成功创建第一个请求
    2. 尝试创建相同类型的第二个请求应被拒绝
    """
    # 注册用户
    register_data = {
        "username": "duplicateverify",
        "email": "duplicateverify@example.com",
        "password": "verify_password_123",
        "full_name": "Duplicate Verify User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    register_response = client.post("/api/users/register", json=register_data)
    user_id = register_response.json()['id']
    
    # 登录获取token
    login_data = {
        "username": "duplicateverify",
        "password": "verify_password_123"
    }
    login_response = client.post("/api/users/login", json=login_data)
    access_token = login_response.json()['access_token']
    
    # 创建第一个验证请求
    verification_data = {
        "user_id": user_id,
        "verification_type": "KYC",
        "notes": "测试身份验证"
    }
    
    response1 = client.post(
        "/api/verifications/request", 
        json=verification_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response1.status_code == status.HTTP_201_CREATED
    
    # 尝试创建重复的验证请求
    response2 = client.post(
        "/api/verifications/request", 
        json=verification_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST

def test_get_user_verifications(client):
    """
    测试获取用户的验证记录
    1. 注册用户
    2. 创建多个验证请求
    3. 获取用户的验证记录
    """
    # 注册用户
    register_data = {
        "username": "verificationhistory",
        "email": "history@example.com",
        "password": "verify_password_123",
        "full_name": "Verification History User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    register_response = client.post("/api/users/register", json=register_data)
    user_id = register_response.json()['id']
    
    # 登录获取token
    login_data = {
        "username": "verificationhistory",
        "password": "verify_password_123"
    }
    login_response = client.post("/api/users/login", json=login_data)
    access_token = login_response.json()['access_token']
    
    # 创建多个验证请求
    verification_types = ["KYC", "AML", "CDD"]
    for ver_type in verification_types:
        verification_data = {
            "user_id": user_id,
            "verification_type": ver_type,
            "notes": f"测试{ver_type}验证"
        }
        
        response = client.post(
            "/api/verifications/request", 
            json=verification_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    # 获取用户验证记录
    response = client.get(
        f"/api/verifications/user/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 验证返回结果
    assert response.status_code == status.HTTP_200_OK
    verifications = response.json()
    assert len(verifications) == len(verification_types)
    
    # 检查验证类型
    returned_types = [v['verification_type'] for v in verifications]
    for ver_type in verification_types:
        assert ver_type in returned_types

def test_unauthorized_verification_access(client):
    """
    测试未授权访问验证记录
    1. 创建两个用户
    2. 一个用户尝试获取另一个用户的验证记录
    3. 验证被拒绝
    """
    # 注册第一个用户
    register_data1 = {
        "username": "user1",
        "email": "user1@example.com",
        "password": "password_123",
        "full_name": "User One",
        "blockchain_address": "0x1111111111111111111111111111111111111111"
    }
    register_response1 = client.post("/api/users/register", json=register_data1)
    user_id1 = register_response1.json()['id']
    
    # 注册第二个用户
    register_data2 = {
        "username": "user2",
        "email": "user2@example.com",
        "password": "password_456",
        "full_name": "User Two",
        "blockchain_address": "0x2222222222222222222222222222222222222222"
    }
    register_response2 = client.post("/api/users/register", json=register_data2)
    user_id2 = register_response2.json()['id']
    
    # 第一个用户登录
    login_data1 = {
        "username": "user1",
        "password": "password_123"
    }
    login_response1 = client.post("/api/users/login", json=login_data1)
    access_token1 = login_response1.json()['access_token']
    
    # 尝试获取第二个用户的验证记录
    response = client.get(
        f"/api/verifications/user/{user_id2}",
        headers={"Authorization": f"Bearer {access_token1}"}
    )
    
    # 验证访问被拒绝
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_get_verification_by_id(client):
    """
    测试获取单个验证记录
    1. 注册用户
    2. 创建验证请求
    3. 获取特定验证记录
    """
    # 注册用户
    register_data = {
        "username": "getverification",
        "email": "getverification@example.com",
        "password": "verify_password_123",
        "full_name": "Get Verification User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    register_response = client.post("/api/users/register", json=register_data)
    user_id = register_response.json()['id']
    
    # 登录获取token
    login_data = {
        "username": "getverification",
        "password": "verify_password_123"
    }
    login_response = client.post("/api/users/login", json=login_data)
    access_token = login_response.json()['access_token']
    
    # 创建验证请求
    verification_data = {
        "user_id": user_id,
        "verification_type": "KYC",
        "notes": "测试获取单个验证记录"
    }
    
    create_response = client.post(
        "/api/verifications/request", 
        json=verification_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    verification_id = create_response.json()['id']
    
    # 获取特定验证记录
    get_response = client.get(
        f"/api/verifications/{verification_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 验证返回结果
    assert get_response.status_code == status.HTTP_200_OK
    verification = get_response.json()
    assert verification['id'] == verification_id
    assert verification['user_id'] == user_id
    assert verification['verification_type'] == "KYC"

def test_verification_status_update(client):
    """
    测试验证状态更新
    1. 注册验证机构
    2. 创建验证请求
    3. 更新验证状态
    """
    # 注册用户
    register_data = {
        "username": "verificationupdate",
        "email": "verificationupdate@example.com",
        "password": "verify_password_123",
        "full_name": "Verification Update User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    register_response = client.post("/api/users/register", json=register_data)
    user_id = register_response.json()['id']
    
    # 注册验证机构
    verifier_data = {
        "name": "Test Bank",
        "blockchain_address": "0x9876543210987654321098765432109876543210",
        "api_key": "test_bank_api_key"
    }
    # 这里需要根据您实际的验证机构注册API调整
    verifier_response = client.post("/api/verifiers/register", json=verifier_data)
    assert verifier_response.status_code == status.HTTP_201_CREATED
    verifier_id = verifier_response.json()['id']
    
    # 登录用户获取token
    login_data = {
        "username": "verificationupdate",
        "password": "verify_password_123"
    }
    login_response = client.post("/api/users/login", json=login_data)
    access_token = login_response.json()['access_token']
    
    # 创建验证请求
    verification_data = {
        "user_id": user_id,
        "verification_type": "KYC",
        "notes": "测试验证状态更新"
    }
    
    create_response = client.post(
        "/api/verifications/request", 
        json=verification_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    verification_id = create_response.json()['id']
    
    # 更新验证状态（使用验证机构API KEY）
    update_data = {
        "status": "approved",
        "notes": "验证通过",
        "transaction_hash": "0x" + "1" * 64
    }
    
    update_response = client.put(
        f"/api/verifications/{verification_id}",
        json=update_data,
        headers={"X-API-Key": "test_bank_api_key"}
    )
    
    # 验证状态更新结果
    assert update_response.status_code == status.HTTP_200_OK
    updated_verification = update_response.json()
    assert updated_verification['status'] == "approved"
    assert updated_verification['notes'] == "验证通过"