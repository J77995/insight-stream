"""
Pydantic models for request and response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List


class VideoRequest(BaseModel):
    """Request model for video summarization."""
    url: str = Field(..., description="YouTube video URL")
    ai_provider: Optional[str] = Field(default="gemini", description="AI provider (gemini or openai)")
    model: Optional[str] = Field(default=None, description="Model name (optional, uses default if not specified)")
    category: Optional[str] = Field(default="general", description="Content category for prompt selection")
    format_type: Optional[str] = Field(default="dialogue", description="Format type (dialogue or presentation) for modular prompts")

    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        """Validate that the URL is a YouTube URL."""
        if not any(d in v.lower() for d in ['youtube.com', 'youtu.be']):
            raise ValueError('URL must be a valid YouTube URL')
        return v

    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Validate that the AI provider is supported."""
        v = v.lower()
        if v not in ['gemini', 'openai']:
            raise ValueError('AI provider must be either "gemini" or "openai"')
        return v


class VideoResponse(BaseModel):
    """Response model containing video data and summaries."""
    video_id: str
    title: str
    full_transcript: str
    summary_overview: str
    summary_detail: str
    category: Optional[str] = None
    format_type: Optional[str] = None
    prompts_used: Optional[Dict[str, str]] = None
    ai_provider: Optional[str] = None
    model: Optional[str] = None


class CustomSummarizeRequest(BaseModel):
    """Request model for custom prompt summarization."""
    video_id: str
    transcript: Optional[str] = None  # Optional - will use cache if not provided
    custom_overview_prompt: Optional[str] = None
    custom_detail_prompt: Optional[str] = None
    custom_system_prompt: Optional[str] = None
    ai_provider: str = "gemini"
    model: Optional[str] = None


class CategoryInfo(BaseModel):
    """Category information for prompt templates."""
    category: str
    display_name: str
    description: str


class PromptTemplate(BaseModel):
    """Complete prompt template for a category."""
    category: str
    display_name: str
    description: str
    system_prompt: str
    overview_prompt: str
    detail_prompt: str


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error: str
    message: str
    suggestion: str


class ChatRequest(BaseModel):
    """Request model for chat with video."""
    video_id: str = Field(..., description="YouTube video ID")
    message: str = Field(..., description="User's question or message")
    conversation_history: List[dict] = Field(default=[], description="Previous conversation messages")
    ai_provider: str = Field(default="gemini", description="AI provider (gemini or openai)")
    model: Optional[str] = Field(default=None, description="Model name (optional)")

    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Validate that the AI provider is supported."""
        v = v.lower()
        if v not in ['gemini', 'openai']:
            raise ValueError('AI provider must be either "gemini" or "openai"')
        return v


class ChatResponse(BaseModel):
    """Response model for chat with video."""
    video_id: str
    reply: str


class TranslateSegmentRequest(BaseModel):
    """Request model for single segment translation."""
    video_id: str = Field(..., description="YouTube video ID")
    text: str = Field(..., description="Text segment to translate")
    ai_provider: str = Field(default="gemini", description="AI provider (gemini or openai)")
    model: Optional[str] = Field(default=None, description="Model name (optional, uses translation-optimized model)")

    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Validate that the AI provider is supported."""
        v = v.lower()
        if v not in ['gemini', 'openai']:
            raise ValueError('AI provider must be either "gemini" or "openai"')
        return v


class TranslateSegmentResponse(BaseModel):
    """Response model for single segment translation."""
    translation: str


class TranslateBatchRequest(BaseModel):
    """Request model for batch translation."""
    video_id: str = Field(..., description="YouTube video ID")
    segments: List[str] = Field(..., description="Text segments to translate (without timestamps)")
    ai_provider: str = Field(default="gemini", description="AI provider (gemini or openai)")
    model: Optional[str] = Field(default=None, description="Model name (optional, uses translation-optimized model)")

    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Validate that the AI provider is supported."""
        v = v.lower()
        if v not in ['gemini', 'openai']:
            raise ValueError('AI provider must be either "gemini" or "openai"')
        return v


class TranslateBatchResponse(BaseModel):
    """Response model for batch translation."""
    translations: List[str]
