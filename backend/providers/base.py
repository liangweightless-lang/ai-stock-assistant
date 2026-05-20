import asyncio
from typing import AsyncGenerator

class BaseLLMProvider:
    """大语言模型统一驱动基类"""
    
    async def generate_stream(
        self, 
        messages: list, 
        stop_event: asyncio.Event
    ) -> AsyncGenerator[str, None]:
        """
        流式文本生成的抽象接口
        """
        raise NotImplementedError("大模型驱动必须实现 generate_stream 流式输出方法")
