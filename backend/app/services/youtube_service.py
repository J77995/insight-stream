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
import os

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for handling YouTube video transcript extraction."""

    def __init__(self):
        """Initialize YouTube API client with cookies and ScraperAPI support."""
        self._api = YouTubeTranscriptApi()
        
        # Get cookies from environment variable (optional)
        self._cookies = os.getenv('YOUTUBE_COOKIES', None)
        
        # Get ScraperAPI key (optional, for anti-blocking)
        self._scraperapi_key = os.getenv('SCRAPERAPI_KEY', None)
        
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
        try:
            # Try to fetch from oembed API (no API key needed)
            import requests
            response = requests.get(
                f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('title', f'YouTube Video ({video_id})')
        except Exception as e:
            logger.warning(f"Failed to fetch video title for {video_id}: {str(e)}")
        
        return f'YouTube Video ({video_id})'

    def get_transcript(self, video_id: str) -> list:
        """
        Fetch transcript for a YouTube video with enhanced anti-blocking measures.

        Tries languages in this order: Korean → English → any available
        If ScraperAPI is configured, uses it as a proxy for anti-blocking.

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
        # Prepare fetch kwargs
        fetch_kwargs = {}
        
        # Use ScraperAPI if available (preferred method)
        if self._scraperapi_key:
            logger.info(f"🔒 Using ScraperAPI for {video_id}")
            # Set proxy through environment variables (youtube-transcript-api uses requests internally)
            import os
            proxy = f"http://scraperapi:{self._scraperapi_key}@proxy-server.scraperapi.com:8001"
            os.environ['HTTP_PROXY'] = proxy
            os.environ['HTTPS_PROXY'] = proxy
        elif self._cookies:
            fetch_kwargs['cookies'] = self._cookies
        
        try:
            # Try Korean first
            try:
                fetched = self._api.fetch(video_id, languages=['ko'], **fetch_kwargs)
                transcript = fetched.to_raw_data()
                logger.info(f"✅ Successfully fetched Korean transcript for {video_id}")
                return transcript
            except (NoTranscriptFound, TranscriptsDisabled) as e:
                logger.debug(f"Korean transcript not available: {str(e)}")
            except RequestBlocked as e:
                logger.warning(f"⚠️ YouTube blocked Korean request for {video_id}: {str(e)}")

            # Try English
            try:
                fetched = self._api.fetch(video_id, languages=['en'], **fetch_kwargs)
                transcript = fetched.to_raw_data()
                logger.info(f"✅ Successfully fetched English transcript for {video_id}")
                return transcript
            except (NoTranscriptFound, TranscriptsDisabled) as e:
                logger.debug(f"English transcript not available: {str(e)}")
            except RequestBlocked as e:
                logger.warning(f"⚠️ YouTube blocked English request for {video_id}: {str(e)}")

            # Try any available transcript
            try:
                transcript_list = self._api.list(video_id, **fetch_kwargs)

                # Try to find any transcript
                for transcript_info in transcript_list:
                    try:
                        fetched = transcript_info.fetch()
                        transcript = fetched.to_raw_data()
                        logger.info(f"✅ Successfully fetched {transcript_info.language} transcript for {video_id}")
                        return transcript
                    except Exception as e:
                        logger.debug(f"Failed to fetch {transcript_info.language}: {str(e)}")
                        continue

                # If all attempts failed
                raise NoTranscriptFound(video_id, [], None)

            except RequestBlocked as e:
                logger.error(f"❌ YouTube blocked all requests for {video_id}")
                raise RequestBlocked(
                    video_id,
                    "YouTube가 요청을 차단했습니다. 잠시 후 다시 시도하거나 다른 영상을 시도해주세요."
                )
            except Exception as e:
                logger.error(f"❌ Failed to fetch any transcript for {video_id}: {str(e)}")
                raise
        finally:
            # Clean up proxy environment variables if ScraperAPI was used
            if self._scraperapi_key:
                if 'HTTP_PROXY' in os.environ:
                    del os.environ['HTTP_PROXY']
                if 'HTTPS_PROXY' in os.environ:
                    del os.environ['HTTPS_PROXY']

    def format_transcript(self, transcript_list: list) -> str:
        """
        Format transcript into timeline-based paragraphs.

        Groups transcript entries by 30-second intervals and formats with timestamps.
        Sentences are kept intact within each group.
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
        
        for entry in transcript_list:
            start_time = entry['start']
            text = entry['text'].strip()
            
            # Skip empty texts
            if not text:
                continue
            
            # Check if we need a new group
            if not current_group['texts'] or start_time - current_group['timestamp'] >= GROUP_INTERVAL:
                if current_group['texts']:
                    grouped.append(current_group)
                current_group = {
                    'timestamp': start_time,
                    'texts': [text]
                }
            else:
                current_group['texts'].append(text)
        
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
