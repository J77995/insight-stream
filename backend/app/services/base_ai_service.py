"""
Base AI service interface for video summarization.
All AI providers must implement this interface.
"""
from abc import ABC, abstractmethod


class BaseAIService(ABC):
    """Abstract base class for AI summarization services."""

    @abstractmethod
    def __init__(self):
        """Initialize the AI service with API credentials."""
        pass

    @abstractmethod
    def generate_summary_overview(self, transcript: str) -> str:
        """
        Generate a concise 2-3 sentence summary.

        Args:
            transcript: Raw transcript text

        Returns:
            Concise overview summary (2-3 sentences)
        """
        pass

    @abstractmethod
    def generate_summary_detail(self, transcript: str) -> str:
        """
        Generate a detailed markdown summary.

        The summary should use markdown format:
        - ## for H2 headers
        - ### for H3 headers
        - - for bullet points
        - Emojis are allowed

        Args:
            transcript: Raw transcript text

        Returns:
            Detailed markdown summary
        """
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the service is properly configured with API credentials.

        Returns:
            True if configured, False otherwise
        """
        pass
