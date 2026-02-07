"""
AI service for generating video summaries using OpenAI GPT models.
"""
from openai import OpenAI
import logging
from app.core.config import settings
from app.services.base_ai_service import BaseAIService

logger = logging.getLogger(__name__)


class OpenAIService(BaseAIService):
    """Service for generating AI summaries using OpenAI."""

    def __init__(self, model_name: str = None):
        """Initialize OpenAI API with configuration.

        Args:
            model_name: Optional model name to use. If None, uses settings.OPENAI_MODEL
        """
        self.model_name = model_name or settings.OPENAI_MODEL

        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self._is_configured = True
            logger.info(f"OpenAI API configured successfully with model: {self.model_name}")
        else:
            self.client = None
            self._is_configured = False
            logger.warning("OpenAI API key not set! Please configure OPENAI_API_KEY in .env file")

    @property
    def is_configured(self) -> bool:
        """Check if OpenAI API is properly configured."""
        return self._is_configured

    def generate_summary_overview(self, transcript: str, custom_prompt: str = None, system_prompt: str = None) -> str:
        """
        Generate a concise 2-3 sentence summary using OpenAI.

        Args:
            transcript: Raw transcript text
            custom_prompt: Custom prompt template (optional). Use {transcript} as placeholder.
            system_prompt: System prompt for model behavior (optional)

        Returns:
            Concise overview summary (2-3 sentences)
        """
        if not self.is_configured:
            return "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."

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

        # Use custom system prompt if provided
        sys_prompt = system_prompt or "당신은 YouTube 영상의 내용을 간결하고 명확하게 요약하는 AI 어시스턴트입니다."

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": sys_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS_OVERVIEW
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating overview with OpenAI: {str(e)}")
            return "AI 요약 생성 중 오류가 발생했습니다."

    def generate_summary_detail(self, transcript: str, custom_prompt: str = None, system_prompt: str = None) -> str:
        """
        Generate a detailed markdown summary using OpenAI.

        The summary uses markdown format compatible with SummaryPanel parser:
        - ## for H2 headers
        - ### for H3 headers
        - - for bullet points
        - Emojis are allowed

        Args:
            transcript: Raw transcript text
            custom_prompt: Custom prompt template (optional). Use {transcript} as placeholder.
            system_prompt: System prompt for model behavior (optional)

        Returns:
            Detailed markdown summary
        """
        if not self.is_configured:
            return "## ⚙️ 설정 필요\\n\\nOpenAI API 키를 설정하면 AI 요약 기능을 사용할 수 있습니다."

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

        # Use custom system prompt if provided
        sys_prompt = system_prompt or "당신은 YouTube 영상의 내용을 구조화된 마크다운 형식으로 상세하게 요약하는 AI 어시스턴트입니다. 이모지를 활용하여 가독성 높은 요약을 작성해주세요."

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": sys_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS_DETAIL
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating detail with OpenAI: {str(e)}")
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
            return "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."

        try:
            # Build messages list
            messages = [{"role": "system", "content": context}]
            
            # Add conversation history
            messages.extend(history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error in chat with OpenAI: {str(e)}")
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
            return "OpenAI API 키가 설정되지 않았습니다."

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
            # Use cost-optimized translation model (gpt-4o-mini)
            response = self.client.chat.completions.create(
                model=settings.OPENAI_TRANSLATION_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 전문 번역가입니다. 영어를 자연스러운 한국어로 번역해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error in segment translation with OpenAI: {str(e)}")
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
            return ["OpenAI API 키가 설정되지 않았습니다."] * len(segments)

        # Join segments with separator
        segments_text = "\n---\n".join(segments)

        prompt = f"""아래 YouTube 영상 스크립트의 세그먼트들을 한국어로 번역해주세요.

[번역 원칙]
- 각 세그먼트를 순서대로 번역
- 원문의 의미와 맥락을 정확히 전달
- 자연스러운 한국어 표현 사용
- 전문 용어는 필요시 원어 병기 (예: "Machine Learning (기계학습)")
- 대화체는 한국어 대화체로 자연스럽게 변환
- 세그먼트 구분을 위해 각 번역 결과를 "---" 구분자로 분리

[원문 세그먼트]
{segments_text}

[번역 세그먼트]"""

        try:
            # Use cost-optimized translation model (gpt-4o-mini)
            response = self.client.chat.completions.create(
                model=settings.OPENAI_TRANSLATION_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 전문 번역가입니다. 영어를 자연스러운 한국어로 번역해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=8000
            )

            # Split result by separator
            translated_text = response.choices[0].message.content.strip()
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
            logger.error(f"Error in batch translation with OpenAI: {str(e)}")
            return ["번역 중 오류가 발생했습니다."] * len(segments)
