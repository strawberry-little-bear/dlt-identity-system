# app/models/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid

def generate_uuid():
    """生成唯一标识符"""
    return str(uuid.uuid4())

class User(Base):
    """用户模型，存储用户基本信息"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    id_number = Column(String, nullable=True, unique=True)
    blockchain_address = Column(String, unique=True)  # 用户区块链地址
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # 用户是否通过身份验证
    
    # 关系
    verifications = relationship("Verification", back_populates="user")
    documents = relationship("Document", back_populates="user")

class Verification(Base):
    """验证记录模型，存储验证历史"""
    __tablename__ = "verifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    verifier_id = Column(String, ForeignKey("verifiers.id"))  # 验证者ID
    verification_type = Column(String)  # KYC, AML等
    status = Column(String)  # pending, approved, rejected
    transaction_hash = Column(String)  # 区块链交易哈希
    verification_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="verifications")
    verifier = relationship("Verifier", back_populates="verifications")

class Verifier(Base):
    """验证者模型，代表金融机构"""
    __tablename__ = "verifiers"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True)
    blockchain_address = Column(String, unique=True)  # 验证者区块链地址
    api_key = Column(String, unique=True)  # 用于API认证
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    verifications = relationship("Verification", back_populates="verifier")

class Document(Base):
    """用户文档模型，存储用户上传的身份文档信息"""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    document_type = Column(String)  # passport, id_card, drivers_license等
    document_hash = Column(String)  # 文档哈希值，而不是实际文档
    ipfs_hash = Column(String, nullable=True)  # 可选的IPFS哈希，用于分布式存储
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending")  # pending, verified, rejected
    
    # 关系
    user = relationship("User", back_populates="documents")