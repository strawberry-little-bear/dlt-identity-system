# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import user_routes, verification_routes
from .database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(title="DLT身份验证系统")

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端应用访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 包含API路由
app.include_router(user_routes.router, prefix="/api/users", tags=["users"])
app.include_router(verification_routes.router, prefix="/api/verifications", tags=["verifications"])


@app.get("/")
async def root():
    """健康检查端点"""
    return {"message": "DLT身份验证系统API正在运行"}