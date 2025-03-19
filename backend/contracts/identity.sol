// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DigitalIdentity {
    // 身份结构体
    struct Identity {
        bytes32 did;          // 去中心化身份标识符
        address owner;        // 身份所有者地址
        uint256 createdAt;    // 创建时间
        bool active;          // 身份是否激活
        mapping(bytes32 => Credential) credentials;  // 凭证映射
    }
    
    // 凭证结构体
    struct Credential {
        bytes32 hash;         // 凭证哈希
        address issuer;       // 发行者地址
        uint256 issuedAt;     // 发行时间
        uint256 expiresAt;    // 过期时间
        bool valid;           // 是否有效
    }
    
    // 状态变量
    mapping(address => Identity) public identities;
    mapping(address => bool) public verifiers;
    address public admin;
    
    // 事件定义
    event IdentityCreated(address indexed owner, bytes32 did);
    event CredentialIssued(address indexed owner, bytes32 indexed credentialId);
    event VerifierAdded(address indexed verifier);
    event VerifierRemoved(address indexed verifier);
    
    // 构造函数
    constructor() {
        admin = msg.sender;
    }
    
    // 修饰符
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }
    
    modifier onlyVerifier() {
        require(verifiers[msg.sender], "Only verifier can perform this action");
        _;
    }
    
    // 创建身份 - 先声明此函数，以便后面的函数可以调用它
    function createIdentity(bytes32 _did) public returns (bool) {
        require(identities[msg.sender].did == bytes32(0), "Identity already exists");
        
        Identity storage newIdentity = identities[msg.sender];
        newIdentity.did = _did;
        newIdentity.owner = msg.sender;
        newIdentity.createdAt = block.timestamp;
        newIdentity.active = true;
        
        emit IdentityCreated(msg.sender, _did);
        return true;
    }
    
    // 注册身份 - 在createIdentity之后声明，这样可以调用它
    function registerIdentity(string memory _dataHash) external returns (bool) {
        // 将字符串转换为bytes32类型的DID
        bytes32 did = keccak256(abi.encodePacked(_dataHash, msg.sender, block.timestamp));
        
        // 调用已有的创建身份函数
        return createIdentity(did);
    }
    
    // 添加验证者
    function addVerifier(address _verifier) external onlyAdmin {
        require(!verifiers[_verifier], "Verifier already exists");
        verifiers[_verifier] = true;
        emit VerifierAdded(_verifier);
    }
    
    // 移除验证者
    function removeVerifier(address _verifier) external onlyAdmin {
        require(verifiers[_verifier], "Verifier does not exist");
        verifiers[_verifier] = false;
        emit VerifierRemoved(_verifier);
    }
    
    // 颁发凭证
    function issueCredential(
        address _owner,
        bytes32 _credentialId,
        bytes32 _credentialHash,
        uint256 _expiresAt
    ) external onlyVerifier returns (bool) {
        require(identities[_owner].active, "Identity not active");
        require(_expiresAt > block.timestamp, "Invalid expiration time");
        
        Credential storage credential = identities[_owner].credentials[_credentialId];
        credential.hash = _credentialHash;
        credential.issuer = msg.sender;
        credential.issuedAt = block.timestamp;
        credential.expiresAt = _expiresAt;
        credential.valid = true;
        
        emit CredentialIssued(_owner, _credentialId);
        return true;
    }
    
    // 验证凭证
    function verifyCredential(
        address _owner,
        bytes32 _credentialId
    ) external view returns (bool, address, uint256, uint256) {
        Credential storage credential = identities[_owner].credentials[_credentialId];
        return (
            credential.valid && 
            credential.expiresAt > block.timestamp,
            credential.issuer,
            credential.issuedAt,
            credential.expiresAt
        );
    }
    
    // 撤销凭证
    function revokeCredential(
        address _owner,
        bytes32 _credentialId
    ) external returns (bool) {
        require(
            msg.sender == identities[_owner].credentials[_credentialId].issuer ||
            msg.sender == admin,
            "Not authorized to revoke"
        );
        
        identities[_owner].credentials[_credentialId].valid = false;
        return true;
    }
}