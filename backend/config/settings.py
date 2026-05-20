import os
import logging
from dotenv import load_dotenv

# 加载 .env 配置文件
load_dotenv()

class Settings:
    """企业级集中式配置类 - Aegis AI 证券投研终端"""
    
    # 阿里云 DashScope ASR / TTS / LLM 统一秘钥
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    
    # 集中绑定参数
    SERVER_HOST: str = os.getenv("STOCK_SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("PORT", os.getenv("STOCK_SERVER_PORT", "9091")))
    
    # 全局日志级别
    LOG_LEVEL: str = os.getenv("STOCK_SERVER_LOG_LEVEL", "INFO").upper()

# 实例化全局配置
settings = Settings()

def init_logging() -> logging.Logger:
    """初始化微服务统一的日志管理器"""
    logger = logging.getLogger("stock_agent")
    
    if not logger.handlers:
        level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
        
        # 统一的终端标准输出流格式 (与 lite-voice-study 保持完美一致)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.info(f"🚀 企业级投研分析服务日志初始化成功，日志级别: {settings.LOG_LEVEL}")
        
    return logger

# 全局共享 Logger
logger = init_logging()
