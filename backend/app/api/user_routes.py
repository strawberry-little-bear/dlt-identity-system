from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from fastapi.security import OAuth2PasswordBearer

from ..models.models import User, Document
from ..schemas.schemas import UserCreate, UserResponse, UserLogin, DocumentCreate, DocumentResponse, Token,UserUpdate
from ..database import get_db
from ..core.blockchain import BlockchainManager

# 创建路由器
router = APIRouter()

# 实例化区块链管理器
blockchain = BlockchainManager()

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")
# 工具函数
def is_valid_ethereum_address(address: str) -> bool:
    """验证以太坊地址是否有效"""
    return (
        isinstance(address, str) and 
        address.startswith('0x') and 
        len(address) == 42 and 
        all(c in '0123456789abcdefABCDEF' for c in address[2:])
    )
    
def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配哈希值"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """从JWT令牌获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# 路由定义
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """注册新用户并在区块链上创建身份"""
    # 检查用户名或邮箱是否已存在
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )
    
    # 验证区块链地址（如果提供）
    if user.blockchain_address:
        if not is_valid_ethereum_address(user.blockchain_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的以太坊地址"
            )
    
    # 创建新用户
    hashed_password = hash_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        blockchain_address=user.blockchain_address,
        id_number=user.id_number
    )
    
    # 保存到数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 在区块链上注册身份
    try:
        if new_user.blockchain_address:
            tx_hash = blockchain.register_identity(new_user.id, new_user.blockchain_address)
            print(f"用户 {new_user.id} 在区块链上注册，交易哈希: {tx_hash}")
    except Exception as e:
        print(f"区块链注册失败: {e}")
    
    return new_user

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录并返回访问令牌"""
    # 查找用户
    user = db.query(User).filter(User.username == user_credentials.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # 返回令牌和用户信息
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user  # 包含用户信息
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    """通过ID获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user

@router.post("/documents", response_model=DocumentResponse)
async def upload_document(
    document: DocumentCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传身份文档"""
    # 验证用户ID
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许为其他用户上传文档"
        )
    
    # 创建文档记录
    new_document = Document(
        user_id=document.user_id,
        document_type=document.document_type,
        document_hash=document.document_hash,
        ipfs_hash=document.ipfs_hash,
        status="pending"
    )
    
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    
    return new_document

@router.get("/documents/{user_id}", response_model=List[DocumentResponse])
async def get_user_documents(
    user_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有文档"""
    # 验证权限（只能查看自己的文档）
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许查看其他用户的文档"
        )
    
    documents = db.query(Document).filter(Document.user_id == user_id).all()
    return documents

@router.get("/blockchain/identity/{user_id}")
async def get_blockchain_identity(
    user_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从区块链获取用户身份信息"""
    # 验证用户存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证权限
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许查看其他用户的区块链身份"
        )
    
    try:
        identity_details = blockchain.get_identity_details(user_id)
        return identity_details
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取区块链身份时出错: {str(e)}"
        )
@router.put("/update-blockchain-address")
async def update_blockchain_address(
    blockchain_address: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户区块链地址"""
    # 验证地址
    if not is_valid_ethereum_address(blockchain_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的以太坊地址"
        )
    
    try:
        # 检查地址是否已被其他用户使用
        existing_user = db.query(User).filter(User.blockchain_address == blockchain_address).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该区块链地址已被其他用户使用"
            )
        
        # 更新用户区块链地址
        current_user.blockchain_address = blockchain_address
        db.commit()
        
        # 在区块链上重新注册身份
        tx_hash = blockchain.register_identity(current_user.id, blockchain_address)
        
        return {
            "message": "区块链地址更新成功",
            "transaction_hash": tx_hash,
            "blockchain_address": blockchain_address
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新区块链地址失败: {str(e)}"
        )
 
@router.put("/update")
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 更新用户信息
        if user_update.full_name:
            current_user.full_name = user_update.full_name
        
        if user_update.id_number:
            # 检查身份证号是否已被其他用户使用
            existing_user = db.query(User).filter(
                User.id_number == user_update.id_number, 
                User.id != current_user.id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该身份证号已被其他用户使用"
                )
            
            current_user.id_number = user_update.id_number
        
        db.commit()
        db.refresh(current_user)
        
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"更新失败: {str(e)}"
        )
