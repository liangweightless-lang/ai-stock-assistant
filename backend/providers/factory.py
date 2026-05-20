from providers.base import BaseLLMProvider
from providers.qwen import QwenProvider

class LLMFactory:
    """大模型驱动器简单工厂 - 证券投研终端专属"""
    
    @staticmethod
    def get_provider() -> BaseLLMProvider:
        """
        统一获取大模型实例。此处默认绑定通义千问驱动。
        后续可根据 settings.LLM_PROVIDER 动态扩展至 openai_compat 等驱动。
        """
        return QwenProvider()
