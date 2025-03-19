# DLT Identity System

基于区块链的去中心化身份验证系统，用于金融机构的KYC流程。

## 功能特点

- 去中心化身份管理
- 智能合约自动化验证
- 安全的KYC流程
- 多机构互信机制

## 技术栈

### 后端
- FastAPI
- SQLAlchemy
- Web3.py
- PostgreSQL

### 前端
- React
- Web3.js
- Material-UI

### 区块链
- Ethereum
- Ganache (开发环境)
- Solidity

## 快速开始

1. 克隆项目
```bash
git clone https://github.com/yourusername/dlt-identity-system.git
cd dlt-identity-system
```

2. 安装依赖
```bash
# 后端依赖
cd backend
python -m venv venv
source venv/bin/activate  # Unix/MacOS
# 或
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

3. 配置环境变量
```bash
cp backend/.env.example backend/.env
# 编辑 .env 文件设置必要的环境变量
```

4. 启动开发服务器
```bash
# 启动后端
cd backend
uvicorn app.main:app --reload

# 启动前端
cd frontend
npm start
```

5. 部署智能合约
```bash
cd backend
python scripts/deploy.py
```

## 项目结构

```
dlt-identity-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── schemas/
│   ├── contracts/
│   └── tests/
└── frontend/
    ├── src/
    ├── public/
    └── package.json
```

## API文档

启动后端服务器后，访问 http://localhost:8000/docs 查看完整的API文档。

## 测试

```bash
# 运行后端测试
cd backend
pytest

# 运行前端测试
cd frontend
npm test
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情