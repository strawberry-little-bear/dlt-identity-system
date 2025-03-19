from fastapi import status
import pytest

def test_user_registration(client):
    """
    测试用户注册流程
    1. 成功注册
    2. 验证响应状态码
    3. 检查返回的用户信息
    """
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secure_password_123",
        "full_name": "Test User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    
    # 发起注册请求
    response = client.post("/api/users/register", json=user_data)
    
    # 验证注册结果
    assert response.status_code == status.HTTP_201_CREATED
    
    # 检查返回的用户信息
    response_data = response.json()
    assert "id" in response_data
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]
    assert response_data["full_name"] == user_data["full_name"]

def test_duplicate_registration(client):
    """
    测试重复注册
    1. 首次注册成功
    2. 使用相同用户名再次注册应失败
    """
    user_data = {
        "username": "duplicateuser",
        "email": "duplicate@example.com",
        "password": "secure_password_123",
        "full_name": "Duplicate User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    
    # 第一次注册
    response1 = client.post("/api/users/register", json=user_data)
    assert response1.status_code == status.HTTP_201_CREATED
    
    # 重复注册
    response2 = client.post("/api/users/register", json=user_data)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST

def test_user_login(client):
    """
    测试用户登录流程
    1. 先注册用户
    2. 使用正确凭证登录
    3. 验证返回的访问令牌
    """
    # 注册用户
    register_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "login_password_123",
        "full_name": "Login User",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    client.post("/api/users/register", json=register_data)
    
    # 登录测试
    login_data = {
        "username": "loginuser",
        "password": "login_password_123"
    }
    
    response = client.post("/api/users/login", json=login_data)
    
    # 验证登录结果
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "access_token" in response_data
    assert "token_type" in response_data
    assert response_data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """
    测试使用无效凭证登录
    1. 未注册用户登录
    2. 密码错误登录
    """
    # 未注册用户登录
    invalid_login1 = {
        "username": "nonexistent_user",
        "password": "some_password"
    }
    response1 = client.post("/api/users/login", json=invalid_login1)
    assert response1.status_code == status.HTTP_401_UNAUTHORIZED
    
    # 注册用户但密码错误
    register_data = {
        "username": "credtest",
        "email": "cred@example.com",
        "password": "correct_password",
        "full_name": "Credentials Test",
        "blockchain_address": "0x1234567890123456789012345678901234567890"
    }
    client.post("/api/users/register", json=register_data)
    
    # 使用错误密码登录
    invalid_login2 = {
        "username": "credtest",
        "password": "wrong_password"
    }
    response2 = client.post("/api/users/login", json=invalid_login2)
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED