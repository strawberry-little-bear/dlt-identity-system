# app/schemas/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import uuid

# 用户模式
class UserBase(BaseModel):
    """用户基本信息"""
    username: str
    email: EmailStr
    full_name: str
    id_number: Optional[str] = None
    
class UserCreate(UserBase):
    """创建用户所需信息"""
    password: str
    blockchain_address: Optional[str] = None
    id_number: Optional[str] = None
class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    blockchain_address: str
    is_verified: bool
    created_at: datetime
    id_number: Optional[str] = None
    class Config:
        orm_mode = True

# 验证者模式
class VerifierBase(BaseModel):
    """验证者基本信息"""
    name: str
    blockchain_address: str

class VerifierCreate(VerifierBase):
    """创建验证者所需信息"""
    pass

class VerifierResponse(VerifierBase):
    """验证者响应模型"""
    id: str
    api_key: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# 验证模式
class VerificationBase(BaseModel):
    """验证基本信息"""
    verification_type: str
    notes: Optional[str] = None

class VerificationCreate(VerificationBase):
    """创建验证所需信息"""
    user_id: str

class VerificationResponse(VerificationBase):
    """验证响应模型"""
    id: str
    user_id: str
    verifier_id: str
    status: str
    transaction_hash: Optional[str]
    verification_date: datetime

    class Config:
        orm_mode = True

# 文档模式
class DocumentBase(BaseModel):
    """文档基本信息"""
    document_type: str
    document_hash: str
    ipfs_hash: Optional[str] = None

class DocumentCreate(DocumentBase):
    """创建文档所需信息"""
    user_id: str

class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: str
    user_id: str
    status: str
    uploaded_at: datetime

    class Config:
        orm_mode = True

# 登录模式
class UserLogin(BaseModel):
    """用户登录所需信息"""
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserResponse] = None

# 验证状态更新
class VerificationUpdate(BaseModel):
    """更新验证状态所需信息"""
    status: str
    transaction_hash: Optional[str] = None
    notes: Optional[str] = None
    
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    id_number: Optional[str] = None
    # 可以添加其他可更新的字段