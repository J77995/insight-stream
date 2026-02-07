"""
AI Service Factory for selecting the appropriate AI provider.
"""
import logging
from typing import Optional
from app.core.config import settings
from app.services.base_ai_service import BaseAIService
from app.services.ai_service import GeminiService
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class AIServiceFactory:
    """Factory for creating AI service instances based on configuration."""

    @staticmethod
    def create_ai_service(provider: Optional[str] = None, model: Optional[str] = None) -> BaseAIService:
        """
        Create and return an AI service instance based on the provider parameter.

        Args:
            provider: AI provider name ('gemini' or 'openai'). If None, uses settings.AI_PROVIDER
            model: Model name to use. If None, uses default from settings

        Returns:
            BaseAIService: An instance of GeminiService or OpenAIService

        Raises:
            ValueError: If the AI_PROVIDER is not supported
        """
        # Use provided provider or fall back to settings
        selected_provider = (provider or settings.AI_PROVIDER).lower()

        if selected_provider == "gemini":
            logger.info(f"Using Gemini AI provider with model: {model or settings.GEMINI_MODEL}")
            return GeminiService(model_name=model)
        elif selected_provider == "openai":
            logger.info(f"Using OpenAI provider with model: {model or settings.OPENAI_MODEL}")
            return OpenAIService(model_name=model)
        else:
            error_msg = f"Unsupported AI provider: {selected_provider}. Supported providers: 'gemini', 'openai'"
            logger.error(error_msg)
            raise ValueError(error_msg)


def get_ai_service(provider: Optional[str] = None, model: Optional[str] = None) -> BaseAIService:
    """
    Convenience function to get an AI service instance.

    Args:
        provider: AI provider name ('gemini' or 'openai'). If None, uses settings.AI_PROVIDER
        model: Model name to use. If None, uses default from settings

    Returns:
        BaseAIService: Configured AI service instance
    """
    return AIServiceFactory.create_ai_service(provider, model)
