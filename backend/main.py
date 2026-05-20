#!/usr/bin/env python3
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import dashscope

# 保证当前执行环境能够正常跨文件夹导入 config / routers / providers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings, logger
from routers.stock import router as stock_router

# 1. 使用 lifespan 管理生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    check_environment()
    yield

# 2. 实例化主 FastAPI 服务
app = FastAPI(
    title="Aegis AI Stock Assistant", 
    description="企业级证券投研 AI 助理微服务", 
    version="1.0.0",
    lifespan=lifespan
)

# 2. 注入全局 CORS 策略，彻底解除跨域阻碍 (企业级规范)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许 Vite 5173 等开发环境跨源访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 挂载子路由模块
app.include_router(stock_router)

# 4. 环境及密钥完整性自测
def check_environment():
    key = settings.DASHSCOPE_API_KEY
    if not key or key == "your_dashscope_api_key_here":
        logger.warning("=================================================================")
        logger.warning("⚠️  [警告] 未检测到有效的 DASHSCOPE_API_KEY 配置！")
        logger.warning("👉 AI 深度研报生成服务将停用。您仍然可以查行情和最新新闻头条。")
        logger.warning("=================================================================")
        dashscope.api_key = ""
        return
    
    dashscope.api_key = key
    logger.info("✔ 阿里云 DashScope SDK 全局密钥校验通过，已成功注入大模型内核")

# 5. 生产级前端静态托管
frontend_dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    logger.info(f"🧬 检测到已编译的前端包，自适应挂载托管目录: {frontend_dist_dir}")
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
else:
    logger.info("ℹ️ 前端开发模式：暂未检测到生产环境 dist 前端包，请独立启动 Vite 开发服务。")



if __name__ == "__main__":
    host = settings.SERVER_HOST
    port = settings.SERVER_PORT
    logger.info(f"🔥 Aegis 证券助理后端正在启动，绑定端口: {host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=True)
