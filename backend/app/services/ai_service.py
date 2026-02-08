"""
AI service for generating video summaries using Google Gemini.
"""
import google.generativeai as genai
import logging
from app.core.config import settings
from app.services.base_ai_service import BaseAIService

logger = logging.getLogger(__name__)


class GeminiService(BaseAIService):
    """Service for generating AI summaries using Google Gemini."""

    def __init__(self, model_name: str = None):
        """Initialize Gemini API with configuration.

        Args:
            model_name: Optional model name to use. If None, uses settings.GEMINI_MODEL
        """
        self.model_name = model_name or settings.GEMINI_MODEL

        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._is_configured = True
            logger.info(f"Gemini API configured successfully with model: {self.model_name}")
        else:
            self._is_configured = False
            logger.warning("Gemini API key not set! Please configure GEMINI_API_KEY in .env file")

    @property
    def is_configured(self) -> bool:
        """Check if Gemini API is properly configured."""
        return self._is_configured

    def generate_summary_overview(self, transcript: str, custom_prompt: str = None, system_prompt: str = None) -> str:
        """
        Generate a concise 2-3 sentence summary using Gemini.

        Args:
            transcript: Raw transcript text
            custom_prompt: Custom prompt template (optional). Use {transcript} as placeholder.
            system_prompt: System prompt for model behavior (optional, not used in Gemini)

        Returns:
            Concise overview summary (2-3 sentences)
        """
        if not self.is_configured:
            return "Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 설정해주세요."

        # Limit transcript length for API efficiency
        limited_transcript = transcript[:settings.TRANSCRIPT_LIMIT_OVERVIEW]

        # Use custom prompt if provided, otherwise use default
        if custom_prompt:
            # Check if prompt contains {transcript} placeholder
            if "{transcript}" in custom_prompt:
                # Traditional prompt: replace placeholder with transcript
                prompt = custom_prompt.replace("{transcript}", limited_transcript)
            else:
                # Modular prompt: append transcript to the end
                prompt = f"{custom_prompt}\n{limited_transcript}"
        else:
            prompt = f"""다음은 유튜브 영상의 전체 스크립트입니다.

이 영상의 핵심 내용을 2-3문장으로 간결하게 한국어로 요약해주세요.
- 핵심 메시지와 주요 주제만 포함
- 구체적이고 명확한 표현 사용
- 2-3문장으로 제한

스크립트:
{limited_transcript}

요약:"""

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "top_p": settings.GEMINI_TOP_P,
                    "max_output_tokens": settings.GEMINI_MAX_TOKENS_OVERVIEW,
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating overview: {str(e)}")
            return "AI 요약 생성 중 오류가 발생했습니다."

    def generate_summary_detail(self, transcript: str, custom_prompt: str = None, system_prompt: str = None) -> str:
        """
        Generate a detailed markdown summary using Gemini.

        The summary uses markdown format compatible with SummaryPanel parser:
        - ## for H2 headers
        - ### for H3 headers
        - - for bullet points
        - Emojis are allowed

        Args:
            transcript: Raw transcript text
            custom_prompt: Custom prompt template (optional). Use {transcript} as placeholder.
            system_prompt: System prompt for model behavior (optional, not used in Gemini)

        Returns:
            Detailed markdown summary
        """
        if not self.is_configured:
            return "## ⚙️ 설정 필요\\n\\nGemini API 키를 설정하면 AI 요약 기능을 사용할 수 있습니다."

        # Limit transcript length
        limited_transcript = transcript[:settings.TRANSCRIPT_LIMIT_DETAIL]

        # Use custom prompt if provided, otherwise use default
        if custom_prompt:
            # Check if prompt contains {transcript} placeholder
            if "{transcript}" in custom_prompt:
                # Traditional prompt: replace placeholder with transcript
                prompt = custom_prompt.replace("{transcript}", limited_transcript)
            else:
                # Modular prompt: append transcript to the end
                prompt = f"{custom_prompt}\n{limited_transcript}"
        else:
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
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "top_p": settings.GEMINI_TOP_P,
                    "max_output_tokens": settings.GEMINI_MAX_TOKENS_DETAIL,
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating detail: {str(e)}")
            return "## ⚠️ 오류\\n\\nAI 상세 요약 생성 중 오류가 발생했습니다."

    def chat(self, context: str, user_message: str, history: list) -> str:
        """
        Chat with video based on transcript context.

        Args:
            context: Context prompt with transcript
            user_message: User's current question
            history: List of previous messages [{"role": "user|assistant", "content": "..."}]

        Returns:
            AI reply text
        """
        if not self.is_configured:
            return "Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 설정해주세요."

        try:
            model = genai.GenerativeModel(self.model_name)
            
            # Build contents list for Gemini format
            contents = []
            
            # Add context as first user message
            contents.append({
                "role": "user",
                "parts": [{"text": context}]
            })
            
            # Add conversation history
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
            
            # Add current user message
            contents.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            
            response = model.generate_content(
                contents,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "top_p": settings.GEMINI_TOP_P,
                    "max_output_tokens": 1000,
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return "채팅 중 오류가 발생했습니다. 다시 시도해주세요."

    def translate_segment(self, text: str) -> str:
        """
        Translate a single text segment to Korean using cost-optimized model.

        Args:
            text: Text segment to translate

        Returns:
            Translated text in Korean
        """
        if not self.is_configured:
            return "Gemini API 키가 설정되지 않았습니다."

        prompt = f"""다음 텍스트를 한국어로 번역해주세요.

[번역 원칙]
- 원문의 의미와 맥락을 정확히 전달
- 자연스러운 한국어 표현 사용
- 전문 용어는 필요시 원어 병기 (예: "Machine Learning (기계학습)")
- 대화체는 한국어 대화체로 자연스럽게 변환

[원문]
{text}

[번역]"""

        try:
            # Use cost-optimized translation model (Flash)
            model = genai.GenerativeModel(settings.GEMINI_TRANSLATION_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in segment translation: {str(e)}")
            return "번역 중 오류가 발생했습니다."

    def translate_batch(self, segments: list) -> list:
        """
        Translate multiple segments in batch using cost-optimized model.

        Args:
            segments: List of text segments to translate

        Returns:
            List of translated texts in Korean
        """
        if not self.is_configured:
            return ["Gemini API 키가 설정되지 않았습니다."] * len(segments)

        # Join segments with separator
        segments_text = "\n---\n".join(segments)

        prompt = f"""아래 영어 텍스트 세그먼트들을 한국어로 번역해주세요.

[중요 규칙]
1. 원문을 포함하지 말고, 번역문만 출력하세요
2. 각 세그먼트를 순서대로 번역
3. 번역 결과만 "---" 구분자로 분리하여 출력
4. 원문의 의미와 맥락을 정확히 전달
5. 자연스러운 한국어 표현 사용
6. 전문 용어는 필요시 원어 병기 (예: "Machine Learning (기계학습)")
7. 대화체는 한국어 대화체로 자연스럽게 변환

[출력 형식 예시]
입력: "Hello---How are you?---Thank you"
출력: "안녕하세요---어떻게 지내세요?---감사합니다"

[입력 텍스트]
{segments_text}

[번역 출력 (번역문만, 원문 포함하지 말 것)]"""

        try:
            # Use cost-optimized translation model (Flash)
            model = genai.GenerativeModel(settings.GEMINI_TRANSLATION_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 8000,
                }
            )

            # Split result by separator
            translated_text = response.text.strip()
            translations = [t.strip() for t in translated_text.split("---")]

            # Validate count
            if len(translations) != len(segments):
                logger.warning(
                    f"Translation count mismatch: expected {len(segments)}, got {len(translations)}"
                )
                # Pad with originals if too few
                while len(translations) < len(segments):
                    translations.append(segments[len(translations)])
                # Truncate if too many
                translations = translations[:len(segments)]

            return translations
        except Exception as e:
            logger.error(f"Error in batch translation: {str(e)}")
            return ["번역 중 오류가 발생했습니다."] * len(segments)
