from web3 import Web3
from eth_account import Account
import json
import os
from dotenv import load_dotenv
import solcx
import sys
import importlib

# 设置默认编码为 UTF-8
if sys.getdefaultencoding() != 'utf-8':
    importlib.reload(sys)
    sys.setdefaultencoding('utf-8')

# 安装特定版本的solc
solcx.install_solc('0.8.0')

load_dotenv()

def compile_contract():
    """编译智能合约"""
    try:
        # 使用 UTF-8 编码读取合约源代码
        with open("backend/contracts/Identity.sol", "r", encoding='utf-8') as file:
            source = file.read()

        # 编译合约
        compiled_sol = solcx.compile_source(
            source,
            output_values=['abi', 'bin'],
            solc_version='0.8.0'
        )

        # 获取合约接口
        contract_id, contract_interface = compiled_sol.popitem()
        
        # 保存编译结果
        os.makedirs('backend/contracts/build', exist_ok=True)
        
        # 使用 UTF-8 编码写入文件
        with open('backend/contracts/build/DigitalIdentity.abi', 'w', encoding='utf-8') as f:
            json.dump(contract_interface['abi'], f, ensure_ascii=False)
        
        with open('backend/contracts/build/DigitalIdentity.bin', 'w', encoding='utf-8') as f:
            f.write(contract_interface['bin'])
            
        return contract_interface
    except Exception as e:
        print(f"编译合约失败: {str(e)}")
        raise

def deploy_contract():
    """部署智能合约"""
    try:
        # 连接到区块链
        w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI", "http://127.0.0.1:8545")))
        
        # 确保连接成功
        if not w3.isConnected():  # Web3.py 5.x 版本正确的方法
            raise Exception("无法连接到以太坊网络")
        
        # 编译合约
        contract_interface = compile_contract()
        
        # 准备部署账户
        admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
        if not admin_private_key:
            # 如果没有设置私钥，使用ganache的第一个账户
            accounts = w3.eth.accounts
            if accounts:
                admin_address = accounts[0]
                # 获取 Ganache 提供的私钥
                admin_private_key = "0x" + "1" * 64  # 这里应该替换为实际的 Ganache 私钥
            else:
                raise Exception("没有可用的账户")
            
        admin_account = Account.from_key(admin_private_key)
        
        # 确保账户有足够的ETH
        balance = w3.eth.get_balance(admin_account.address)
        if balance == 0:
            raise Exception("部署账户没有ETH")
            
        print(f"部署账户: {admin_account.address}")
        # 使用 Web3.fromWei 进行单位转换
        print(f"账户余额: {Web3.fromWei(balance, 'ether')} ETH")
        
        # 创建合约实例
        contract = w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # 构建交易（修复 build_transaction 为 buildTransaction）
        construct_txn = contract.constructor().buildTransaction({
            'from': admin_account.address,
            'nonce': w3.eth.get_transaction_count(admin_account.address),
            'gas': 3000000,
            'gasPrice': w3.eth.gas_price
        })
        
        # 签名交易
        signed_txn = w3.eth.account.sign_transaction(construct_txn, admin_private_key)
        
        # 使用 rawTransaction 替代 raw_transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"交易已发送，等待确认... (tx_hash: {tx_hash.hex()})")
        
        # 等待交易确认
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt['status'] == 1:
            print(f"合约已成功部署到地址: {tx_receipt.contractAddress}")
            
            # 更新.env文件
            env_path = "backend/.env"
            if os.path.exists(env_path):
                with open(env_path, "r", encoding='utf-8') as f:
                    env_content = f.read()
                
                if "CONTRACT_ADDRESS=" in env_content:
                    env_content = env_content.replace(
                        f"CONTRACT_ADDRESS={os.getenv('CONTRACT_ADDRESS', '')}",
                        f"CONTRACT_ADDRESS={tx_receipt.contractAddress}"
                    )
                else:
                    env_content += f"\nCONTRACT_ADDRESS={tx_receipt.contractAddress}"
                
                with open(env_path, "w", encoding='utf-8') as f:
                    f.write(env_content)
            
            return tx_receipt.contractAddress
        else:
            raise Exception("合约部署失败")
            
    except Exception as e:
        print(f"部署合约失败: {str(e)}")
        raise

if __name__ == "__main__":
    print("开始部署智能合约...")
    try:
        # 安装solc编译器（如果需要）
        if not solcx.get_installed_solc_versions():
            print("正在安装 solc 编译器...")
            solcx.install_solc('0.8.0')
        
        contract_address = deploy_contract()
        print(f"合约部署成功！地址: {contract_address}")
    except Exception as e:
        print(f"部署过程中出现错误: {str(e)}")
