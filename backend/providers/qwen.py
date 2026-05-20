import asyncio
from typing import AsyncGenerator
import dashscope
from providers.base import BaseLLMProvider
from config.settings import settings, logger

class QwenProvider(BaseLLMProvider):
    """通义千问大模型驱动实现"""
    
    def __init__(self):
        self.model_name = 'qwen-plus'
        logger.debug("通义千问投研分析驱动实例化成功")

    async def generate_stream(
        self, 
        messages: list, 
        stop_event: asyncio.Event
    ) -> AsyncGenerator[str, None]:
        """流式请求阿里云通义千问模型"""
        logger.info(f"正在向 [通义千问] 发出投研流式生成请求...")
        
        # 实时异步提取数据流
        responses = dashscope.Generation.call(
            model=self.model_name,
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True,
            api_key=settings.DASHSCOPE_API_KEY,  # 显式传递密钥以防 SDK 隐式读取失败
        )

        for response in responses:
            if stop_event.is_set():
                logger.info("捕获打断信号，中止 Qwen 研报输出")
                break
            
            if response.status_code == 200:
                content = response.output.choices[0]['message']['content']
                if content:
                    yield content
            else:
                logger.error(f"[通义千问] 错误: {response.message} (状态码: {response.status_code})")
                break
            
            # 维持异步流执行流畅
            await asyncio.sleep(0.005)
