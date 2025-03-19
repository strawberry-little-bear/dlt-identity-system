# app/core/blockchain.py
import json
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import hashlib

# 加载环境变量
load_dotenv()

class BlockchainManager:
    """管理与以太坊区块链的交互"""
    
    def __init__(self):
        """初始化区块链连接和合约"""
        # 连接到区块链节点 - 使用WEB3_PROVIDER_URI而不是BLOCKCHAIN_NODE_URL
        self.web3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI", "http://127.0.0.1:8545")))
        
        # 为POA网络添加中间件（如Rinkeby, Ganache等）
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # 检查连接
        if not self.web3.isConnected():
            raise Exception("无法连接到以太坊节点")
            
        # 加载合约ABI和地址
        try:
            # 使用环境变量存储合约地址
            self.contract_address = os.getenv("CONTRACT_ADDRESS")
            if not self.contract_address:
                raise Exception("CONTRACT_ADDRESS 环境变量未设置")
            
            # 加载ABI文件
            abi_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "..","contracts", "build", "DigitalIdentity.abi")
            
            with open(abi_path, 'r', encoding='utf-8') as file:
                contract_abi = json.load(file)
                
            # 创建合约实例
            self.contract = self.web3.eth.contract(address=self.contract_address, abi=contract_abi)
            
            # 使用ADMIN_PRIVATE_KEY生成账户并设置为默认账户
            admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
            if admin_private_key:
                # 确保私钥格式正确
                if not admin_private_key.startswith("0x"):
                    admin_private_key = "0x" + admin_private_key
                
                # 从私钥生成账户
                account = self.web3.eth.account.from_key(admin_private_key)
                self.web3.eth.default_account = account.address
                print(f"使用私钥生成的账户地址: {account.address}")
            else:
                # 尝试使用第一个可用账户
                accounts = self.web3.eth.accounts
                if accounts:
                    self.web3.eth.default_account = accounts[0]
                    print(f"使用区块链第一个账户: {accounts[0]}")
                else:
                    raise Exception("没有可用的以太坊账户，请设置ADMIN_PRIVATE_KEY环境变量")
            
        except Exception as e:
            print(f"初始化区块链合约时出错: {e}")
            raise
    
    def get_identity_hash(self, user_id):
        """
        计算用户身份的哈希值
        
        Args:
            user_id: 用户唯一标识符
            
        Returns:
            str: 用户身份的哈希值
        """
        try:
            # 使用 SHA-256 生成确定性哈希
            identity_hash = hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()
            return f'0x{identity_hash}'
        except Exception as e:
            print(f"生成身份哈希时出错: {e}")
            return None
    
    def register_identity(self, user_id, user_address):
        """在区块链上注册用户身份
        
        Args:
            user_id: 用户唯一标识符
            user_address: 用户的以太坊地址
            
        Returns:
            transaction_hash: 交易哈希
        """
        try:
            # 生成身份哈希
            identity_hash = self.get_identity_hash(user_id)
            
            # 移除前缀 "0x"，因为我们将作为字符串传递
            if identity_hash.startswith("0x"):
                identity_hash = identity_hash[2:]
            
            print(f"准备调用registerIdentity，参数: {identity_hash}")
            
            # 确保我们有有效的发送地址
            from_address = self.web3.eth.default_account
            if not from_address:
                # 如果默认账户未设置，使用用户提供的地址
                from_address = user_address
                if not from_address:
                    raise Exception("没有可用的发送地址，请设置ADMIN_PRIVATE_KEY环境变量或提供有效的user_address")
            
            print(f"交易发送地址: {from_address}")
            
            # 准备交易
            tx = self.contract.functions.registerIdentity(
                identity_hash
            ).buildTransaction({
                'from': from_address,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(from_address)
            })
            
            # 签名交易 - 使用ADMIN_PRIVATE_KEY而不是PRIVATE_KEY
            admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
            if not admin_private_key:
                raise Exception("ADMIN_PRIVATE_KEY 环境变量未设置")
                
            # 确保私钥格式正确
            if not admin_private_key.startswith("0x"):
                admin_private_key = "0x" + admin_private_key
                
            signed_tx = self.web3.eth.account.sign_transaction(tx, admin_private_key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # 等待交易确认
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            print(f"身份注册成功，交易哈希: {tx_receipt.transactionHash.hex()}")
            return tx_receipt.transactionHash.hex()
        
        except Exception as e:
            print(f"注册身份时出错: {e}")
            import traceback
            print(traceback.format_exc())
            raise
    
    # 其他方法保持不变...
    
    def check_verification_status(self, user_id, verification_type):
        """检查用户在特定验证类型上的验证状态
        
        Args:
            user_id: 用户唯一标识符
            verification_type: 验证类型
            
        Returns:
            bool: 验证状态
        """
        try:
            return self.contract.functions.checkVerificationStatus(
                user_id,
                verification_type
            ).call()
        except Exception as e:
            print(f"检查验证状态时出错: {e}")
            return False
    
    def get_identity_details(self, user_id):
        """获取用户身份详情
        
        Args:
            user_id: 用户唯一标识符
            
        Returns:
            dict: 用户身份详情
        """
        try:
            result = self.contract.functions.getIdentityDetails(user_id).call()
            
            # 解析结果
            details = {
                "owner": result[0],
                "exists": result[1],
                "verifications": []
            }
            
            # 获取验证记录
            verification_count = self.contract.functions.getVerificationCount(user_id).call()
            
            for i in range(verification_count):
                verification = self.contract.functions.getVerification(user_id, i).call()
                details["verifications"].append({
                    "verificationType": verification[0],
                    "verifier": verification[1],
                    "timestamp": verification[2]
                })
                
            return details
            
        except Exception as e:
            print(f"获取身份详情时出错: {e}")
            raise