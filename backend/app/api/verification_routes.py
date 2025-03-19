from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models.models import Verification, User, Verifier
from ..schemas.schemas import VerificationCreate, VerificationResponse, VerificationUpdate
from ..database import get_db
from ..core.blockchain import BlockchainManager
from .user_routes import get_current_user, is_valid_ethereum_address

# 创建路由器
router = APIRouter()

# 实例化区块链管理器
blockchain = BlockchainManager()

# 验证者API密钥认证依赖
async def get_verifier_by_api_key(api_key: str = Header(...), db: Session = Depends(get_db)):
    """通过API密钥获取验证者"""
    verifier = db.query(Verifier).filter(Verifier.api_key == api_key).first()
    if not verifier or not verifier.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥或验证者未激活"
        )
    return verifier

# 新增 - 身份状态端点
@router.get("/identity-status/{user_id}")
async def get_identity_status(
    user_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户在区块链上的身份状态"""
    # 验证权限
    if user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许查看其他用户的身份状态"
        )
    
    try:
        # 从数据库获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 获取验证记录
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id
        ).order_by(Verification.verification_date.desc()).all()
        
        # 确定身份状态
        status_value = "pending"
        latest_verification = None
        if verifications:
            latest_verification = verifications[0]
            if latest_verification.status == "approved":
                status_value = "verified"
            elif latest_verification.status == "rejected":
                status_value = "rejected"
        
        # 确保区块链地址有效
        blockchain_address = user.blockchain_address if user.blockchain_address and is_valid_ethereum_address(user.blockchain_address) else "0x0000000000000000000000000000000000000000"
        
        # 创建响应数据
        try:
            identity_hash = blockchain.get_identity_hash(user_id) if hasattr(blockchain, "get_identity_hash") else None
        except:
            identity_hash = None
        
        return {
            "user_id": user_id,
            "status": status_value,
            "blockchain_address": blockchain_address,
            "identity_hash": identity_hash,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else datetime.now().isoformat(),
            "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') else datetime.now().isoformat(),
            "blockchain_info": {
                "contract_address": blockchain.contract_address if hasattr(blockchain, "contract_address") else None,
                "transaction_hash": latest_verification.transaction_hash if latest_verification else None,
                "block_number": None,  # 可以根据需要添加实际区块号
                "timestamp": latest_verification.verification_date.isoformat() if latest_verification and latest_verification.verification_date else None
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取身份状态错误: {str(e)}"
        )

# 新增 - 验证请求列表端点
@router.get("/list")
async def get_verification_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的验证请求列表"""
    try:
        verifications = db.query(Verification).filter(
            Verification.user_id == current_user.id
        ).all()
        
        return verifications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取验证请求列表失败: {str(e)}"
        )

# 路由定义
@router.post("/request", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def request_verification(
    verification: VerificationCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户请求身份验证"""
    # 检查用户权限
    if verification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许为其他用户请求验证"
        )
    
    # 检查是否已存在待处理的相同类型验证
    existing_verification = db.query(Verification).filter(
        Verification.user_id == verification.user_id,
        Verification.verification_type == verification.verification_type,
        Verification.status == "pending"
    ).first()
    
    if existing_verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已存在待处理的{verification.verification_type}验证请求"
        )
    
    # 分配给默认验证者（这里可以改进为基于验证类型分配）
    default_verifier = db.query(Verifier).filter(Verifier.is_active == True).first()
    if not default_verifier:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="没有可用的验证者"
        )
    
    # 创建验证请求
    new_verification = Verification(
        user_id=verification.user_id,
        verifier_id=default_verifier.id,
        verification_type=verification.verification_type,
        status="pending",
        notes=verification.notes
    )
    
    db.add(new_verification)
    db.commit()
    db.refresh(new_verification)
    
    return new_verification

@router.get("/pending", response_model=List[VerificationResponse])
async def get_pending_verifications(
    verifier: Verifier = Depends(get_verifier_by_api_key),
    db: Session = Depends(get_db)
):
    """获取验证者的待处理验证请求"""
    verifications = db.query(Verification).filter(
        Verification.verifier_id == verifier.id,
        Verification.status == "pending"
    ).all()
    
    return verifications

@router.put("/{verification_id}", response_model=VerificationResponse)
async def update_verification_status(
    verification_id: str,
    verification_update: VerificationUpdate,
    verifier: Verifier = Depends(get_verifier_by_api_key),
    db: Session = Depends(get_db)
):
    """更新验证状态"""
    # 获取验证请求
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="验证请求不存在"
        )
    
    # 检查验证者权限
    if verification.verifier_id != verifier.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许更新其他验证者的验证请求"
        )
    
    # 检查状态是否有效
    valid_statuses = ["pending", "approved", "rejected"]
    if verification_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态，必须是: {', '.join(valid_statuses)}"
        )
    
    # 如果状态变为已批准，则在区块链上记录
    transaction_hash = None
    if verification_update.status == "approved" and verification.status != "approved":
        try:
            # 获取用户
            user = db.query(User).filter(User.id == verification.user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            # 在区块链上验证身份
            transaction_hash = blockchain.verify_identity(
                user.id, 
                verifier.blockchain_address,
                verification.verification_type
            )
            
            # 更新用户验证状态
            user.is_verified = True
            db.add(user)
            
        except Exception as e:
            print(f"区块链验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"区块链验证失败: {str(e)}"
            )
    
    # 更新验证记录
    verification.status = verification_update.status
    verification.notes = verification_update.notes or verification.notes
    
    # 如果提供了交易哈希或从区块链操作获取了哈希
    if verification_update.transaction_hash:
        verification.transaction_hash = verification_update.transaction_hash
    elif transaction_hash:
        verification.transaction_hash = transaction_hash
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    
    return verification

@router.get("/user/{user_id}", response_model=List[VerificationResponse])
async def get_user_verifications(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有验证记录"""
    # 检查权限（只能查看自己的验证记录）
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许查看其他用户的验证记录"
        )
    
    verifications = db.query(Verification).filter(Verification.user_id == user_id).all()
    return verifications

@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_by_id(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过ID获取验证记录详情"""
    # 获取验证记录
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="验证记录不存在"
        )
    
    # 检查权限（用户只能查看自己的验证记录）
    if verification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许查看其他用户的验证记录"
        )
    
    return verification

@router.get("/blockchain/status/{user_id}/{verification_type}")
async def check_blockchain_verification_status(
    user_id: str,
    verification_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从区块链检查用户的验证状态"""
    # 检查权限
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不允许查看其他用户的验证状态"
        )
    
    try:
        is_verified = blockchain.check_verification_status(user_id, verification_type)
        return {"user_id": user_id, "verification_type": verification_type, "is_verified": is_verified}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查区块链验证状态时出错: {str(e)}"
        )