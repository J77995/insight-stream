"""
Transcript caching system for optimized prompt re-summarization.
Stores video transcripts in memory to avoid re-sending large texts.
Single-session mode: only stores the most recent video.
"""
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TranscriptCache:
    """Simple in-memory cache for video transcripts with TTL (single session mode)."""
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize the transcript cache.
        
        Args:
            ttl_hours: Time-to-live in hours for cached entries (default: 24)
        """
        self._current_video: Optional[dict] = None
        self._ttl = timedelta(hours=ttl_hours)
        logger.info(f"💾 TranscriptCache initialized with TTL: {ttl_hours} hours (single session mode)")
    
    def set(self, video_id: str, transcript: str, title: str = None, formatted_transcript: str = None) -> None:
        """
        Store transcript with metadata (overwrites previous cache).
        
        Args:
            video_id: YouTube video ID
            transcript: Raw transcript text
            title: Video title (optional)
            formatted_transcript: Formatted transcript with timestamps (optional)
        """
        self._current_video = {
            'video_id': video_id,
            'transcript': transcript,
            'title': title,
            'formatted_transcript': formatted_transcript,
            'timestamp': datetime.now()
        }
        logger.info(f"💾 Cached transcript for video: {video_id} ({len(transcript)} chars)")
    
    def get(self, video_id: str) -> Optional[str]:
        """
        Get transcript if exists, matches video_id, and not expired.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript text if found and valid, None otherwise
        """
        if not self._current_video:
            logger.warning(f"⚠️ No transcript in cache")
            return None
        
        if self._current_video['video_id'] != video_id:
            logger.warning(f"⚠️ Video ID mismatch: requested {video_id}, cached {self._current_video['video_id']}")
            return None
        
        age = datetime.now() - self._current_video['timestamp']
        
        if age > self._ttl:
            logger.info(f"⏰ Transcript expired for video: {video_id} (age: {age})")
            self._current_video = None
            return None
        
        logger.info(f"✅ Retrieved cached transcript for video: {video_id} (age: {age})")
        return self._current_video['transcript']
    
    def get_title(self, video_id: str) -> Optional[str]:
        """
        Get cached video title.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video title if found, None otherwise
        """
        if not self._current_video or self._current_video['video_id'] != video_id:
            return None
        return self._current_video.get('title')
    
    def get_formatted_transcript(self, video_id: str) -> Optional[str]:
        """
        Get cached formatted transcript.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Formatted transcript if found, None otherwise
        """
        if not self._current_video or self._current_video['video_id'] != video_id:
            return None
        return self._current_video.get('formatted_transcript')
    
    def get_current_video_id(self) -> Optional[str]:
        """
        Get the current cached video ID.
        
        Returns:
            Video ID if cache exists, None otherwise
        """
        if self._current_video:
            return self._current_video['video_id']
        return None
    
    def clear_expired(self) -> int:
        """
        Remove expired entry from cache.
        
        Returns:
            Number of entries removed (0 or 1)
        """
        if not self._current_video:
            return 0
        
        now = datetime.now()
        age = now - self._current_video['timestamp']
        
        if age > self._ttl:
            video_id = self._current_video['video_id']
            self._current_video = None
            logger.info(f"🧹 Cleared expired transcript for video: {video_id}")
            return 1
        
        return 0
    
    def stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if self._current_video:
            size = len(self._current_video['transcript'])
            return {
                'has_cache': True,
                'video_id': self._current_video['video_id'],
                'size_bytes': size,
                'size_mb': round(size / 1024 / 1024, 2),
                'cached_at': self._current_video['timestamp'].isoformat()
            }
        return {
            'has_cache': False,
            'video_id': None,
            'size_bytes': 0,
            'size_mb': 0,
            'cached_at': None
        }


# Global cache instance
transcript_cache = TranscriptCache()
