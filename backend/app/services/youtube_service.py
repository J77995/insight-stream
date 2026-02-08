"""
YouTube service for extracting and processing video transcripts.
"""
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked,
    AgeRestricted,
    VideoUnplayable
)
from urllib.parse import urlparse, parse_qs
import logging
import re
from app.core.config import settings

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for handling YouTube video transcript extraction."""

    def __init__(self):
        """Initialize YouTube API client with cookies and ScraperAPI support."""
        self._api = YouTubeTranscriptApi()
        
        # Get cookies from settings (optional)
        self._cookies = settings.YOUTUBE_COOKIES if settings.YOUTUBE_COOKIES else None
        
        # Get ScraperAPI key from settings (optional, for anti-blocking)
        self._scraperapi_key = settings.SCRAPERAPI_KEY if settings.SCRAPERAPI_KEY else None
        
        # Set User-Agent to mimic real browser
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        if self._scraperapi_key:
            logger.info("✅ ScraperAPI configured - anti-blocking enabled")
        elif self._cookies:
            logger.info("YouTube cookies configured for transcript fetching")
        else:
            logger.info("No YouTube cookies or ScraperAPI configured, using default settings")

    def extract_video_id(self, url: str) -> str | None:
        """
        Extract video ID from various YouTube URL formats.

        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        - https://m.youtube.com/watch?v=VIDEO_ID

        Args:
            url: YouTube video URL

        Returns:
            Video ID string or None if extraction fails
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

    def get_video_title(self, video_id: str) -> str:
        """
        Get video title from YouTube.

        Args:
            video_id: YouTube video ID

        Returns:
            Video title, or default title if fetch fails
        """
        metadata = self.get_video_metadata(video_id)
        return metadata.get('title', f'YouTube Video ({video_id})')

    def get_video_metadata(self, video_id: str) -> dict:
        """
        Get video metadata from YouTube (title, channel name).

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with title, channel, and channel_url
        """
        try:
            # Try to fetch from oembed API (no API key needed)
            import requests
            response = requests.get(
                f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'title': data.get('title', f'YouTube Video ({video_id})'),
                    'channel': data.get('author_name', 'Unknown Channel'),
                    'channel_url': data.get('author_url', ''),
                }
        except Exception as e:
            logger.warning(f"Failed to fetch video metadata for {video_id}: {str(e)}")

        # Return default values if fetch fails
        return {
            'title': f'YouTube Video ({video_id})',
            'channel': 'Unknown Channel',
            'channel_url': '',
        }

    def get_transcript(self, video_id: str) -> list:
        """
        Fetch transcript for a YouTube video with enhanced anti-blocking measures.

        Tries languages in this order: Korean → English → any available
        If ScraperAPI is configured, uses it as a proxy for youtube-transcript-api.

        Args:
            video_id: YouTube video ID

        Returns:
            List of transcript entries (raw data format)

        Raises:
            TranscriptsDisabled: When transcripts are disabled for the video
            NoTranscriptFound: When no transcript is available
            VideoUnavailable: When the video is not accessible
            RequestBlocked: When YouTube blocks the request
            AgeRestricted: When video is age-restricted
            VideoUnplayable: When video cannot be played
            Exception: For other transcript-related errors
        """
        # Configure proxies if ScraperAPI is available
        proxies = None
        if self._scraperapi_key:
            logger.info(f"🔒 Using ScraperAPI as proxy for {video_id}")
            # ScraperAPI proxy format
            proxies = {
                'http': f'http://scraperapi:{self._scraperapi_key}@proxy-server.scraperapi.com:8001',
                'https': f'http://scraperapi:{self._scraperapi_key}@proxy-server.scraperapi.com:8001'
            }
        
        # Use youtube-transcript-api with proxies
        try:
            # Try Korean first
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
                transcript = transcript_list.find_transcript(['ko'])
                result = transcript.fetch()
                logger.info(f"✅ Successfully fetched Korean transcript for {video_id}")
                return result
            except (NoTranscriptFound, TranscriptsDisabled) as e:
                logger.debug(f"Korean transcript not available: {str(e)}")
            except RequestBlocked as e:
                logger.warning(f"⚠️ YouTube blocked Korean request for {video_id}: {str(e)}")

            # Try English
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
                transcript = transcript_list.find_transcript(['en'])
                result = transcript.fetch()
                logger.info(f"✅ Successfully fetched English transcript for {video_id}")
                return result
            except (NoTranscriptFound, TranscriptsDisabled) as e:
                logger.debug(f"English transcript not available: {str(e)}")
            except RequestBlocked as e:
                logger.warning(f"⚠️ YouTube blocked English request for {video_id}: {str(e)}")

            # Try any available transcript
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
                
                # Try to find any transcript
                for transcript_info in transcript_list:
                    try:
                        result = transcript_info.fetch()
                        logger.info(f"✅ Successfully fetched {transcript_info.language} transcript for {video_id}")
                        return result
                    except Exception as e:
                        logger.debug(f"Failed to fetch {transcript_info.language}: {str(e)}")
                        continue

                # If all attempts failed
                raise NoTranscriptFound(video_id, [], None)

            except RequestBlocked as e:
                logger.error(f"❌ YouTube blocked all requests for {video_id}")
                raise Exception("YouTube가 요청을 차단했습니다. 잠시 후 다시 시도하거나 다른 영상을 시도해주세요.")
            except Exception as e:
                logger.error(f"❌ Failed to fetch any transcript for {video_id}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"❌ All transcript fetching methods failed for {video_id}")
            raise

    def format_transcript(self, transcript_list: list) -> str:
        """
        Format transcript into timeline-based paragraphs.

        Groups transcript entries by 30-second intervals and formats with timestamps.
        Sentences are kept intact within each group - won't split mid-sentence.
        Format: "mm:ss text1 text2 text3\n\nmm:ss text4 text5"
        Example: "0:05 First sentence. Second sentence.\n\n0:35 Third sentence."

        Args:
            transcript_list: List of transcript entries from YouTube API

        Returns:
            Formatted transcript string with timestamps and complete sentences
        """
        if not transcript_list:
            return ""

        grouped = []
        current_group = {
            'timestamp': 0,
            'texts': []
        }

        # Group interval in seconds (30 seconds per paragraph)
        GROUP_INTERVAL = 30
        # Maximum group duration to prevent excessive accumulation
        MAX_GROUP_DURATION = 45

        # Sentence-ending punctuation
        SENTENCE_ENDERS = ('.', '!', '?', '...', '。', '！', '？')

        for i, entry in enumerate(transcript_list):
            start_time = entry['start']
            text = entry['text'].strip()

            # Skip empty texts
            if not text:
                continue

            # Add text to current group
            current_group['texts'].append(text)

            # Check if we should start a new group
            time_exceeded = start_time - current_group['timestamp'] >= GROUP_INTERVAL
            max_exceeded = start_time - current_group['timestamp'] >= MAX_GROUP_DURATION
            is_last_entry = i == len(transcript_list) - 1

            # Check if current text ends with sentence-ending punctuation
            ends_with_sentence = text.endswith(SENTENCE_ENDERS)

            should_split = False

            if max_exceeded or is_last_entry:
                # Maximum time exceeded or last entry → force split
                should_split = True
            elif time_exceeded and ends_with_sentence:
                # 30 seconds exceeded + sentence complete → split
                should_split = True

            if should_split and current_group['texts']:
                grouped.append(current_group)
                current_group = {
                    'timestamp': transcript_list[i + 1]['start'] if not is_last_entry else start_time,
                    'texts': []
                }
                # If not splitting, keep accumulating until we find a sentence end or timeout

        # Add the last group
        if current_group['texts']:
            grouped.append(current_group)
        
        # Format the output
        formatted_lines = []
        for group in grouped:
            # Skip groups with no text
            if not group['texts']:
                continue
                
            # Convert timestamp to mm:ss format
            minutes = int(group['timestamp'] // 60)
            seconds = int(group['timestamp'] % 60)
            timestamp = f"{minutes}:{seconds:02d}"
            
            # Combine texts into a paragraph (filter out empty strings)
            # Join with space to keep sentences flowing naturally
            combined_text = " ".join([t for t in group['texts'] if t.strip()])

            # Only add if there's actual content
            if combined_text.strip():
                formatted_lines.append(f"{timestamp} {combined_text}")
        
        return "\n\n".join(formatted_lines)

    def get_raw_transcript_text(self, transcript_list: list) -> str:
        """
        Extract raw text from transcript for AI processing.

        Args:
            transcript_list: List of transcript entries

        Returns:
            Concatenated transcript text
        """
        return " ".join([entry['text'] for entry in transcript_list])
