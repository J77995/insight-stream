from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from urllib.parse import urlparse, parse_qs
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Insight Stream API", version="1.0.0")

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configure Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
    logger.warning("Gemini API key not set! Please configure GEMINI_API_KEY in .env file")
else:
    genai.configure(api_key=gemini_api_key)

# Pydantic models
class VideoRequest(BaseModel):
    url: str

class VideoResponse(BaseModel):
    video_id: str
    title: str
    full_transcript: str
    summary_overview: str
    summary_detail: str


# --- Helper Functions ---

def extract_video_id(url: str) -> str | None:
    """
    Extract video ID from various YouTube URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    """
    try:
        parsed_url = urlparse(url)

        # youtu.be format
        if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed_url.path[1:]

        # youtube.com formats
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            # /watch?v=VIDEO_ID
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]

            # /embed/VIDEO_ID
            if parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]

            # /v/VIDEO_ID
            if parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]

        return None
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        return None


def get_transcript(video_id: str) -> list:
    """
    Fetch transcript for a YouTube video.

    Tries languages in this order: Korean → English → auto-generated Korean → auto-generated English
    """
    import xml.etree.ElementTree as ET

    try:
        # Try Korean first
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        logger.info(f"Successfully fetched Korean transcript for {video_id}")
        return transcript
    except ET.ParseError as e:
        logger.error(f"XML parse error for Korean transcript: {str(e)}")
    except Exception as e:
        logger.debug(f"Korean transcript not available: {str(e)}")

    try:
        # Try English
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        logger.info(f"Successfully fetched English transcript for {video_id}")
        return transcript
    except ET.ParseError as e:
        logger.error(f"XML parse error for English transcript: {str(e)}")
    except Exception as e:
        logger.debug(f"English transcript not available: {str(e)}")

    try:
        # Try any available transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try to find Korean or English transcript
        for transcript_info in transcript_list:
            try:
                transcript = transcript_info.fetch()
                logger.info(f"Successfully fetched {transcript_info.language} transcript for {video_id}")
                return transcript
            except ET.ParseError as e:
                logger.error(f"XML parse error for {transcript_info.language}: {str(e)}")
                continue
            except Exception as e:
                logger.debug(f"Failed to fetch {transcript_info.language}: {str(e)}")
                continue

        # If all attempts failed
        raise Exception("All available transcripts failed to parse")

    except Exception as e:
        logger.error(f"Failed to fetch any transcript for {video_id}: {str(e)}")
        raise


def format_transcript(transcript_list: list) -> str:
    """
    Format transcript into the format expected by TranscriptPanel.

    Format: "line_number text\n\nline_number text\n\n..."
    Example: "1 First sentence\n\n2 Second sentence"
    """
    formatted_lines = []
    for i, entry in enumerate(transcript_list, start=1):
        text = entry['text'].strip()
        formatted_lines.append(f"{i} {text}")

    return "\n\n".join(formatted_lines)


def generate_summary_overview(transcript: str) -> str:
    """
    Generate a concise 2-3 sentence summary using Gemini.
    """
    # Limit transcript length for API efficiency (first 8000 chars ~ 2000 tokens)
    limited_transcript = transcript[:8000]

    prompt = f"""다음은 유튜브 영상의 전체 스크립트입니다.

이 영상의 핵심 내용을 2-3문장으로 간결하게 한국어로 요약해주세요.
- 핵심 메시지와 주요 주제만 포함
- 구체적이고 명확한 표현 사용
- 2-3문장으로 제한

스크립트:
{limited_transcript}

요약:"""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 500,
            }
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating overview: {str(e)}")
        return "AI 요약 생성 중 오류가 발생했습니다."


def generate_summary_detail(transcript: str) -> str:
    """
    Generate a detailed markdown summary using Gemini.

    The summary must use markdown format compatible with SummaryPanel parser:
    - ## for H2 headers
    - ### for H3 headers
    - - for bullet points
    - Emojis are allowed
    """
    # Limit transcript length (first 12000 chars ~ 3000 tokens)
    limited_transcript = transcript[:12000]

    prompt = f"""다음은 유튜브 영상의 전체 스크립트입니다.

이 영상의 내용을 상세하게 분석하여 구조화된 마크다운 형식으로 정리해주세요.

요구사항:
1. 한국어로 작성
2. 마크다운 형식 사용 (##, ###, -, 등)
3. 주요 섹션을 논리적으로 구분
4. 각 섹션별로 핵심 포인트를 불릿 포인트(-)로 정리
5. 이모지 사용 가능 (## 💡, ### 📊 등)
6. 3-5개의 주요 섹션으로 구성

구조 예시:
## 💡 [주요 주제 1]
- 핵심 포인트 1
- 핵심 포인트 2

### [세부 주제]
- 상세 설명

스크립트:
{limited_transcript}

상세 요약:"""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 2000,
            }
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating detail: {str(e)}")
        return "## ⚠️ 오류\n\nAI 상세 요약 생성 중 오류가 발생했습니다."


# --- API Endpoints ---

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Insight Stream API is running",
        "version": "1.0.0"
    }


@app.post("/summarize", response_model=VideoResponse)
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
    video_id = extract_video_id(request.url)
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

    # Step 2: Fetch transcript
    try:
        transcript_list = get_transcript(video_id)
        full_transcript = format_transcript(transcript_list)
        logger.info(f"✅ Transcript fetched ({len(transcript_list)} entries)")
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
    if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
        # Fallback when Gemini API is not configured
        logger.warning("Gemini API not configured, using fallback summaries")
        summary_overview = "Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 설정해주세요."
        summary_detail = "## ⚙️ 설정 필요\n\nGemini API 키를 설정하면 AI 요약 기능을 사용할 수 있습니다."
    else:
        try:
            logger.info("🤖 Generating AI summaries with Gemini...")

            # Get raw transcript text for AI processing
            raw_text = " ".join([entry['text'] for entry in transcript_list])

            summary_overview = generate_summary_overview(raw_text)
            summary_detail = generate_summary_detail(raw_text)

            logger.info("✅ AI summaries generated successfully")
        except Exception as e:
            logger.error(f"Error generating summaries: {str(e)}")
            summary_overview = "AI 요약 생성 중 오류가 발생했습니다."
            summary_detail = "## ⚠️ 오류\n\n요약을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."

    # Step 4: Return response
    response = VideoResponse(
        video_id=video_id,
        title=f"YouTube Video ({video_id})",  # Could be enhanced with actual title fetching
        full_transcript=full_transcript,
        summary_overview=summary_overview,
        summary_detail=summary_detail
    )

    logger.info(f"✅ Successfully processed video {video_id}")
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
