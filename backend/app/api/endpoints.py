"""
API endpoint handlers for the Insight Stream application.
"""
from fastapi import APIRouter, HTTPException
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked,
    AgeRestricted,
    VideoUnplayable
)
import logging
from typing import List

from app.models.schemas import (
    VideoRequest, 
    VideoResponse, 
    CustomSummarizeRequest, 
    CategoryInfo, 
    PromptTemplate, 
    ChatRequest, 
    ChatResponse,
    TranslateSegmentRequest,
    TranslateSegmentResponse,
    TranslateBatchRequest,
    TranslateBatchResponse
)
from app.services.youtube_service import YouTubeService
from app.services.ai_factory import get_ai_service
from app.core.config import settings
from app.core.prompts import get_all_categories, get_modular_prompt
from app.core.cache import transcript_cache

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()

# Initialize services
youtube_service = YouTubeService()


@router.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Insight Stream API is running",
        "version": settings.APP_VERSION
    }


@router.post("/summarize", response_model=VideoResponse)
async def summarize_video(request: VideoRequest):
    """
    Extract transcript and generate AI summary for a YouTube video.

    Args:
        request: Contains YouTube URL

    Returns:
        Complete video data with transcript and summaries

    Raises:
        HTTPException: 400 for invalid URL, 404 for no transcript, 500 for server errors
    """
    logger.info(f"📥 Received request for URL: {request.url}")

    # Step 1: Extract video ID
    video_id = youtube_service.extract_video_id(request.url)
    if not video_id:
        logger.warning(f"Invalid URL: {request.url}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_url",
                "message": "유효하지 않은 YouTube URL입니다",
                "suggestion": "올바른 YouTube URL을 입력해주세요"
            }
        )

    logger.info(f"🆔 Extracted video ID: {video_id}")

    # Step 2: Fetch video title
    try:
        title = youtube_service.get_video_title(video_id)
        logger.info(f"📺 Video title: {title}")
    except Exception as e:
        logger.warning(f"Failed to fetch title, using default: {str(e)}")
        title = f"YouTube Video ({video_id})"

    # Step 3: Fetch transcript
    try:
        transcript_list = youtube_service.get_transcript(video_id)
        full_transcript = youtube_service.format_transcript(transcript_list)
        logger.info(f"✅ Transcript fetched ({len(transcript_list)} entries)")
    except RequestBlocked:
        logger.error(f"Request blocked by YouTube for video: {video_id}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "request_blocked",
                "message": "YouTube가 요청을 차단했습니다",
                "suggestion": "잠시 후 다시 시도하거나 네트워크를 변경해주세요"
            }
        )
    except AgeRestricted:
        logger.error(f"Age-restricted video: {video_id}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "age_restricted",
                "message": "연령 제한이 있는 영상입니다",
                "suggestion": "다른 영상을 시도해주세요"
            }
        )
    except VideoUnplayable:
        logger.error(f"Video unplayable: {video_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "video_unplayable",
                "message": "재생할 수 없는 영상입니다",
                "suggestion": "영상이 삭제되었거나 접근할 수 없습니다"
            }
        )
    except TranscriptsDisabled:
        logger.error(f"Transcripts disabled for video: {video_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "transcripts_disabled",
                "message": "이 영상은 자막이 비활성화되어 있습니다",
                "suggestion": "자막이 제공되는 다른 영상을 시도해주세요"
            }
        )
    except NoTranscriptFound:
        logger.error(f"No transcript found for video: {video_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "no_transcript",
                "message": "이 영상에는 자막이 제공되지 않습니다",
                "suggestion": "자막이 있는 다른 영상을 시도해주세요"
            }
        )
    except VideoUnavailable:
        logger.error(f"Video unavailable: {video_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "video_unavailable",
                "message": "영상을 찾을 수 없거나 비공개 상태입니다",
                "suggestion": "올바른 공개 영상 URL을 입력해주세요"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching transcript: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "transcript_error",
                "message": "자막을 가져오는 중 오류가 발생했습니다",
                "suggestion": "잠시 후 다시 시도해주세요"
            }
        )

    # Step 3: Generate AI summaries
    try:
        # Get AI service based on user's selection
        ai_service = get_ai_service(provider=request.ai_provider, model=request.model)

        # Check if API key is configured
        if not ai_service.is_configured:
            provider_name = request.ai_provider.upper()
            logger.error(f"{provider_name} API key not configured")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "api_key_required",
                    "message": f"{provider_name} API 키가 설정되지 않았습니다",
                    "suggestion": f"backend/.env 파일에 {provider_name}_API_KEY를 입력해주세요"
                }
            )

        logger.info(f"🤖 Generating AI summaries with {request.ai_provider.upper()}...")

        # Get raw transcript text for AI processing
        raw_text = youtube_service.get_raw_transcript_text(transcript_list)

        # Get category and format_type (with defaults)
        category = request.category or "general"
        format_type = request.format_type or "dialogue"  # Default to dialogue

        logger.info(f"📝 Using modular prompt - Topic: {category}, Format: {format_type}")

        # Use PromptGenerator for all requests (unified modular approach)
        # Limit transcript for overview and detail
        overview_transcript = raw_text[:settings.TRANSCRIPT_LIMIT_OVERVIEW]
        detail_transcript = raw_text[:settings.TRANSCRIPT_LIMIT_DETAIL]

        # Create complete prompts with transcript already embedded
        prompt_overview = get_modular_prompt(category, format_type, overview_transcript, "overview")
        prompt_detail = get_modular_prompt(category, format_type, detail_transcript, "detail")

        # Generate summaries with modular prompts
        # Pass empty string as transcript since it's already in the prompt
        summary_overview = ai_service.generate_summary_overview(
            "",  # Empty: transcript already included in prompt_overview
            custom_prompt=prompt_overview,
            system_prompt=None
        )
        summary_detail = ai_service.generate_summary_detail(
            "",  # Empty: transcript already included in prompt_detail
            custom_prompt=prompt_detail,
            system_prompt=None
        )

        # Remove [TARGET SCRIPT] section from prompts for display
        def remove_script_section(prompt: str) -> str:
            """Remove the [TARGET SCRIPT] section and everything after it from prompt."""
            if "[TARGET SCRIPT]" in prompt:
                return prompt.split("[TARGET SCRIPT]")[0].strip()
            return prompt
        
        prompts_used = {
            "overview": remove_script_section(prompt_overview),
            "detail": remove_script_section(prompt_detail)
        }

        logger.info("✅ AI summaries generated successfully")
    except HTTPException:
        # Re-raise HTTP exceptions (like API key error)
        raise
    except Exception as e:
        logger.error(f"Error generating summaries: {str(e)}")
        summary_overview = "AI 요약 생성 중 오류가 발생했습니다."
        summary_detail = "## ⚠️ 오류\\n\\n요약을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."

    # Step 4: Return response
    response = VideoResponse(
        video_id=video_id,
        title=title,
        full_transcript=full_transcript,
        summary_overview=summary_overview,
        summary_detail=summary_detail,
        category=category,
        format_type=format_type,
        prompts_used=prompts_used,
        ai_provider=request.ai_provider,
        model=request.model or "default"
    )

    # Cache the raw transcript for future prompt edits
    transcript_cache.set(video_id, raw_text, title=title, formatted_transcript=full_transcript)
    
    logger.info(f"✅ Successfully processed video {video_id}")
    return response


@router.get("/api/prompts/categories", response_model=List[CategoryInfo])
async def get_categories():
    """
    Get all available prompt categories.

    Returns:
        List of category information
    """
    logger.info("📋 Fetching prompt categories")
    categories = get_all_categories()
    return categories


@router.post("/api/prompts/custom", response_model=VideoResponse)
async def custom_summarize(request: CustomSummarizeRequest):
    """
    Generate summary with custom prompts (for testing/immediate use).

    Args:
        request: Contains video info, optional transcript, and custom prompts

    Returns:
        Video response with new summaries
    """
    logger.info(f"🔄 Custom summarize request for video: {request.video_id}")

    try:
        # Get transcript from cache or request
        if request.transcript:
            transcript = request.transcript
            logger.info("📄 Using transcript from request")
        else:
            transcript = transcript_cache.get(request.video_id)
            if not transcript:
                logger.error(f"Transcript not found in cache for video: {request.video_id}")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "transcript_not_found",
                        "message": "저장된 스크립트를 찾을 수 없습니다",
                        "suggestion": "영상을 다시 요약해주세요"
                    }
                )
            logger.info("💾 Using cached transcript")
        
        # Get title and formatted transcript from cache
        title = transcript_cache.get_title(request.video_id) or f"YouTube Video ({request.video_id})"
        formatted_transcript = transcript_cache.get_formatted_transcript(request.video_id) or transcript
        
        # Get AI service
        ai_service = get_ai_service(provider=request.ai_provider, model=request.model)

        # Check if API key is configured
        if not ai_service.is_configured:
            provider_name = request.ai_provider.upper()
            logger.error(f"{provider_name} API key not configured")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "api_key_required",
                    "message": f"{provider_name} API 키가 설정되지 않았습니다",
                    "suggestion": f"backend/.env 파일에 {provider_name}_API_KEY를 입력해주세요"
                }
            )

        logger.info(f"🤖 Generating summaries with custom prompts...")

        # Generate summaries with custom prompts
        summary_overview = ai_service.generate_summary_overview(
            transcript,
            custom_prompt=request.custom_overview_prompt,
            system_prompt=request.custom_system_prompt
        )

        summary_detail = ai_service.generate_summary_detail(
            transcript,
            custom_prompt=request.custom_detail_prompt,
            system_prompt=request.custom_system_prompt
        )

        logger.info("✅ Custom summaries generated successfully")

        return VideoResponse(
            video_id=request.video_id,
            title=title,
            full_transcript=formatted_transcript,
            summary_overview=summary_overview,
            summary_detail=summary_detail,
            category="custom",
            prompts_used={
                "overview": request.custom_overview_prompt or "default",
                "detail": request.custom_detail_prompt or "default"
            },
            ai_provider=request.ai_provider,
            model=request.model or "default"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in custom summarize: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "summarize_error",
                "message": "커스텀 요약 생성 중 오류가 발생했습니다",
                "suggestion": "잠시 후 다시 시도해주세요"
            }
        )


@router.post("/api/chat", response_model=ChatResponse)
async def chat_with_video(request: ChatRequest):
    """
    Chat with video based on transcript context.

    Args:
        request: Contains video_id, message, conversation history, and AI settings

    Returns:
        ChatResponse with AI reply

    Raises:
        HTTPException: 404 for missing transcript, 400 for API key issues, 500 for server errors
    """
    logger.info(f"💬 Chat request for video: {request.video_id}")

    try:
        # 1. Get transcript from cache
        transcript = transcript_cache.get(request.video_id)
        
        if not transcript:
            logger.error(f"Transcript not found in cache for video: {request.video_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "transcript_not_found",
                    "message": "스크립트를 찾을 수 없습니다",
                    "suggestion": "영상을 다시 요약해주세요"
                }
            )

        # 2. Get AI service
        ai_service = get_ai_service(provider=request.ai_provider, model=request.model)

        # 3. Check if API key is configured
        if not ai_service.is_configured:
            provider_name = request.ai_provider.upper()
            logger.error(f"{provider_name} API key not configured")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "api_key_required",
                    "message": f"{provider_name} API 키가 설정되지 않았습니다",
                    "suggestion": f"backend/.env 파일에 {provider_name}_API_KEY를 입력해주세요"
                }
            )

        # 4. Construct context prompt with strict instructions
        context_prompt = f"""다음은 YouTube 영상의 전체 스크립트입니다:

{transcript}

[지시사항]
- 위 스크립트의 내용만을 바탕으로 사용자의 질문에 정확하게 답변하세요
- 스크립트에 명시적으로 언급된 내용만 답변하세요
- 스크립트에 없는 내용은 추측하거나 외부 지식을 사용하지 마세요
- 확실하지 않은 경우 "스크립트에서 해당 내용을 찾을 수 없습니다"라고 답변하세요
- 답변은 간결하고 명확하게 작성하세요"""

        # 5. Call chat method with history
        reply = ai_service.chat(context_prompt, request.message, request.conversation_history)

        logger.info(f"✅ Chat response generated for video: {request.video_id}")
        return ChatResponse(video_id=request.video_id, reply=reply)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "chat_error",
                "message": "채팅 중 오류가 발생했습니다",
                "suggestion": "잠시 후 다시 시도해주세요"
            }
        )


@router.post("/api/translate/segment", response_model=TranslateSegmentResponse)
async def translate_segment(request: TranslateSegmentRequest):
    """
    Translate a single text segment to Korean.

    Args:
        request: Contains video_id, text, AI provider and model settings

    Returns:
        TranslateSegmentResponse with translated text

    Raises:
        HTTPException: 400 for API key issues, 500 for server errors
    """
    logger.info(f"🌐 Segment translation request for video: {request.video_id}")

    try:
        # Get AI service with translation-optimized model
        ai_service = get_ai_service(provider=request.ai_provider, model=None)

        # Check if API key is configured
        if not ai_service.is_configured:
            provider_name = request.ai_provider.upper()
            logger.error(f"{provider_name} API key not configured")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "api_key_required",
                    "message": f"{provider_name} API 키가 설정되지 않았습니다",
                    "suggestion": f"backend/.env 파일에 {provider_name}_API_KEY를 입력해주세요"
                }
            )

        # Translate segment
        translation = ai_service.translate_segment(request.text)

        logger.info(f"✅ Segment translated for video: {request.video_id}")
        return TranslateSegmentResponse(translation=translation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in segment translation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "translation_error",
                "message": "번역 중 오류가 발생했습니다",
                "suggestion": "잠시 후 다시 시도해주세요"
            }
        )


@router.post("/api/translate/batch", response_model=TranslateBatchResponse)
async def translate_batch(request: TranslateBatchRequest):
    """
    Translate multiple text segments to Korean in batch.

    Args:
        request: Contains video_id, segments array, AI provider and model settings

    Returns:
        TranslateBatchResponse with translated texts

    Raises:
        HTTPException: 400 for API key issues, 500 for server errors
    """
    logger.info(f"🌐 Batch translation request for video: {request.video_id} ({len(request.segments)} segments)")

    try:
        # Get AI service with translation-optimized model
        ai_service = get_ai_service(provider=request.ai_provider, model=None)

        # Check if API key is configured
        if not ai_service.is_configured:
            provider_name = request.ai_provider.upper()
            logger.error(f"{provider_name} API key not configured")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "api_key_required",
                    "message": f"{provider_name} API 키가 설정되지 않았습니다",
                    "suggestion": f"backend/.env 파일에 {provider_name}_API_KEY를 입력해주세요"
                }
            )

        # Translate batch
        translations = ai_service.translate_batch(request.segments)

        logger.info(f"✅ Batch translated for video: {request.video_id}")
        return TranslateBatchResponse(translations=translations)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch translation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "translation_error",
                "message": "전체 번역 중 오류가 발생했습니다",
                "suggestion": "잠시 후 다시 시도해주세요"
            }
        )
