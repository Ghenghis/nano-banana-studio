"""
Nano Banana Studio Pro - SunoAI Package Integration
====================================================
Alternative Suno client using the pip-installable SunoAI package.
Simpler setup: just `pip install SunoAI`

This wraps the Malith-Rukshan/Suno-API library for easy integration.

Install:
    pip install SunoAI

Usage:
    from backend.services.suno_pip_client import SunoPipClient
    
    client = SunoPipClient()
    songs = await client.generate("upbeat pop song about coding")
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("suno-pip-client")

# Check if SunoAI is installed
try:
    from suno import Suno, ModelVersions
    SUNO_AVAILABLE = True
except ImportError:
    SUNO_AVAILABLE = False
    logger.warning("SunoAI package not installed. Run: pip install SunoAI")


@dataclass
class SunoPipSong:
    """Song data from SunoAI package"""
    id: str
    title: str
    status: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    duration: Optional[float] = None
    lyrics: Optional[str] = None
    style: Optional[str] = None
    created_at: Optional[datetime] = None
    raw_data: Dict = None


class SunoPipClient:
    """
    Suno client using the pip-installable SunoAI package.
    
    This is the simplest integration method - just pip install and go!
    
    Setup:
        1. pip install SunoAI
        2. Set SUNO_COOKIE environment variable
        3. Use the client
    
    Example:
        client = SunoPipClient()
        
        # Simple generation
        songs = await client.generate("happy pop song")
        
        # Custom generation with lyrics
        songs = await client.generate_custom(
            lyrics="[Verse]\\nHello world...",
            style="pop, upbeat",
            title="Hello World"
        )
    """
    
    def __init__(self, cookie: Optional[str] = None):
        """
        Initialize SunoAI client.
        
        Args:
            cookie: Suno session cookie (or uses SUNO_COOKIE env var)
        """
        if not SUNO_AVAILABLE:
            raise ImportError(
                "SunoAI package not installed. Install with: pip install SunoAI"
            )
        
        self.cookie = cookie or os.getenv("SUNO_COOKIE")
        if not self.cookie:
            raise ValueError(
                "Suno cookie required. Set SUNO_COOKIE environment variable."
            )
        
        # Initialize the Suno client
        self._client = Suno(cookie=self.cookie)
        
        logger.info("SunoPipClient initialized")
    
    def _parse_song(self, clip: Any) -> SunoPipSong:
        """Convert SunoAI clip to our format"""
        return SunoPipSong(
            id=getattr(clip, 'id', ''),
            title=getattr(clip, 'title', 'Untitled'),
            status=getattr(clip, 'status', 'unknown'),
            audio_url=getattr(clip, 'audio_url', None),
            video_url=getattr(clip, 'video_url', None),
            image_url=getattr(clip, 'image_large_url', None) or getattr(clip, 'image_url', None),
            duration=getattr(clip, 'duration', None),
            lyrics=getattr(clip, 'lyric', None),
            style=getattr(clip, 'tags', None),
            created_at=None,
            raw_data=clip.__dict__ if hasattr(clip, '__dict__') else {}
        )
    
    async def get_credits(self) -> Dict[str, int]:
        """
        Get remaining credits.
        
        Returns:
            Dict with credits_left, monthly_limit, monthly_usage
        """
        # Run in thread pool since SunoAI is sync
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, self._client.get_credits)
        
        return {
            "credits_left": info.get("credits_left", 0),
            "monthly_limit": info.get("monthly_limit", 0),
            "monthly_usage": info.get("monthly_usage", 0)
        }
    
    async def generate(
        self,
        prompt: str,
        instrumental: bool = False,
        model: str = "chirp-v3-5",
        wait: bool = True
    ) -> List[SunoPipSong]:
        """
        Generate music from a text prompt.
        
        Args:
            prompt: Description of the music
            instrumental: No vocals if True
            model: Model version (chirp-v3-5, chirp-v3-0, chirp-v4)
            wait: Wait for completion
            
        Returns:
            List of generated songs (usually 2)
        """
        loop = asyncio.get_event_loop()
        
        # Map model string to enum
        model_version = ModelVersions.CHIRP_V3_5
        if "v4" in model.lower():
            model_version = ModelVersions.CHIRP_V4
        elif "v3-0" in model.lower() or "v3.0" in model.lower():
            model_version = ModelVersions.CHIRP_V3_0
        
        logger.info(f"Generating music: {prompt[:50]}...")
        
        clips = await loop.run_in_executor(
            None,
            lambda: self._client.generate(
                prompt=prompt,
                is_custom=False,
                wait_audio=wait,
                make_instrumental=instrumental,
                model_version=model_version
            )
        )
        
        songs = [self._parse_song(clip) for clip in clips]
        logger.info(f"Generated {len(songs)} songs")
        
        return songs
    
    async def generate_custom(
        self,
        lyrics: str,
        style: str,
        title: str,
        instrumental: bool = False,
        model: str = "chirp-v3-5",
        wait: bool = True
    ) -> List[SunoPipSong]:
        """
        Generate music with custom lyrics.
        
        Args:
            lyrics: Song lyrics with structure markers [Verse], [Chorus], etc.
            style: Music style tags (comma-separated)
            title: Song title
            instrumental: Instrumental only
            model: Model version
            wait: Wait for completion
            
        Returns:
            List of generated songs
        """
        loop = asyncio.get_event_loop()
        
        model_version = ModelVersions.CHIRP_V3_5
        if "v4" in model.lower():
            model_version = ModelVersions.CHIRP_V4
        
        logger.info(f"Generating custom song: {title}")
        
        clips = await loop.run_in_executor(
            None,
            lambda: self._client.generate(
                prompt=lyrics,
                tags=style,
                title=title,
                is_custom=True,
                wait_audio=wait,
                make_instrumental=instrumental,
                model_version=model_version
            )
        )
        
        songs = [self._parse_song(clip) for clip in clips]
        return songs
    
    async def generate_lyrics(self, prompt: str) -> str:
        """
        Generate lyrics from a prompt.
        
        Args:
            prompt: Description of the song concept
            
        Returns:
            Generated lyrics with structure markers
        """
        loop = asyncio.get_event_loop()
        
        result = await loop.run_in_executor(
            None,
            lambda: self._client.generate_lyrics(prompt=prompt)
        )
        
        return result.get("text", "") if isinstance(result, dict) else str(result)
    
    async def get_song(self, song_id: str) -> Optional[SunoPipSong]:
        """
        Get a song by ID.
        
        Args:
            song_id: The song ID
            
        Returns:
            SunoPipSong or None
        """
        loop = asyncio.get_event_loop()
        
        clip = await loop.run_in_executor(
            None,
            lambda: self._client.get_song(song_id)
        )
        
        return self._parse_song(clip) if clip else None
    
    async def get_songs(self) -> List[SunoPipSong]:
        """
        Get all songs in the account.
        
        Returns:
            List of all songs
        """
        loop = asyncio.get_event_loop()
        
        clips = await loop.run_in_executor(
            None,
            self._client.get_songs
        )
        
        return [self._parse_song(clip) for clip in clips]
    
    async def download(
        self,
        song: SunoPipSong,
        output_dir: Path,
        include_video: bool = False
    ) -> Dict[str, Path]:
        """
        Download song files.
        
        Args:
            song: Song to download
            output_dir: Directory for output files
            include_video: Also download video
            
        Returns:
            Dict with paths to downloaded files
        """
        import httpx
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        async with httpx.AsyncClient() as client:
            # Download audio
            if song.audio_url:
                audio_path = output_dir / f"{song.id}.mp3"
                response = await client.get(song.audio_url)
                audio_path.write_bytes(response.content)
                results["audio"] = audio_path
            
            # Download video
            if include_video and song.video_url:
                video_path = output_dir / f"{song.id}.mp4"
                response = await client.get(song.video_url)
                video_path.write_bytes(response.content)
                results["video"] = video_path
            
            # Download cover
            if song.image_url:
                image_path = output_dir / f"{song.id}.jpg"
                response = await client.get(song.image_url)
                image_path.write_bytes(response.content)
                results["image"] = image_path
        
        return results


# =============================================================================
# UNIFIED SUNO INTERFACE
# =============================================================================

class UnifiedSunoClient:
    """
    Unified Suno client that auto-selects the best available backend.
    
    Priority:
    1. SunoAI pip package (simplest)
    2. Local suno-api Docker service
    3. Vercel deployment
    
    Example:
        client = UnifiedSunoClient()
        songs = await client.generate("upbeat pop song")
    """
    
    def __init__(self):
        self._client = None
        self._backend = None
    
    async def _ensure_client(self):
        """Initialize the best available client"""
        if self._client:
            return
        
        # Try SunoAI pip package first
        if SUNO_AVAILABLE and os.getenv("SUNO_COOKIE"):
            try:
                self._client = SunoPipClient()
                self._backend = "pip"
                logger.info("Using SunoAI pip package backend")
                return
            except Exception as e:
                logger.warning(f"SunoAI pip package failed: {e}")
        
        # Try REST API (local or Vercel)
        from backend.services.suno_service import SunoClient
        
        local_url = os.getenv("SUNO_LOCAL_URL")
        vercel_url = os.getenv("SUNO_VERCEL_URL")
        
        if local_url:
            try:
                self._client = SunoClient(api_url=local_url)
                # Test connection
                await self._client.get_credits()
                self._backend = "local"
                logger.info(f"Using local suno-api: {local_url}")
                return
            except Exception as e:
                logger.warning(f"Local suno-api failed: {e}")
        
        if vercel_url:
            try:
                self._client = SunoClient(api_url=vercel_url)
                await self._client.get_credits()
                self._backend = "vercel"
                logger.info(f"Using Vercel suno-api: {vercel_url}")
                return
            except Exception as e:
                logger.warning(f"Vercel suno-api failed: {e}")
        
        raise RuntimeError(
            "No Suno backend available. Options:\n"
            "1. pip install SunoAI and set SUNO_COOKIE\n"
            "2. Run local suno-api and set SUNO_LOCAL_URL\n"
            "3. Deploy to Vercel and set SUNO_VERCEL_URL"
        )
    
    @property
    def backend(self) -> Optional[str]:
        """Get the active backend name"""
        return self._backend
    
    async def get_credits(self) -> Dict[str, int]:
        """Get credit balance"""
        await self._ensure_client()
        
        if self._backend == "pip":
            return await self._client.get_credits()
        else:
            credits = await self._client.get_credits()
            return {
                "credits_left": credits.credits_left,
                "monthly_limit": credits.monthly_limit,
                "monthly_usage": credits.monthly_usage
            }
    
    async def generate(
        self,
        prompt: str,
        instrumental: bool = False,
        wait: bool = True
    ) -> List[Dict]:
        """Generate music from prompt"""
        await self._ensure_client()
        
        if self._backend == "pip":
            songs = await self._client.generate(prompt, instrumental, wait=wait)
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status,
                    "audio_url": s.audio_url,
                    "video_url": s.video_url,
                    "duration": s.duration,
                    "lyrics": s.lyrics,
                    "style": s.style
                }
                for s in songs
            ]
        else:
            songs = await self._client.generate(
                prompt=prompt,
                instrumental=instrumental,
                wait_for_completion=wait
            )
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status.value,
                    "audio_url": s.audio_url,
                    "video_url": s.video_url,
                    "duration": s.duration,
                    "lyrics": s.lyrics,
                    "style": s.style
                }
                for s in songs
            ]
    
    async def generate_custom(
        self,
        lyrics: str,
        style: str,
        title: str,
        instrumental: bool = False,
        wait: bool = True
    ) -> List[Dict]:
        """Generate with custom lyrics"""
        await self._ensure_client()
        
        if self._backend == "pip":
            songs = await self._client.generate_custom(
                lyrics=lyrics,
                style=style,
                title=title,
                instrumental=instrumental,
                wait=wait
            )
        else:
            songs = await self._client.generate_custom(
                lyrics=lyrics,
                style=style,
                title=title,
                instrumental=instrumental,
                wait_for_completion=wait
            )
        
        return [
            {
                "id": s.id if hasattr(s, 'id') else s["id"],
                "title": s.title if hasattr(s, 'title') else s["title"],
                "audio_url": s.audio_url if hasattr(s, 'audio_url') else s.get("audio_url"),
                "duration": s.duration if hasattr(s, 'duration') else s.get("duration"),
            }
            for s in songs
        ]
    
    async def generate_lyrics(self, prompt: str) -> str:
        """Generate lyrics"""
        await self._ensure_client()
        
        if self._backend == "pip":
            return await self._client.generate_lyrics(prompt)
        else:
            return await self._client.generate_lyrics(prompt)
    
    async def close(self):
        """Cleanup"""
        if self._client and hasattr(self._client, 'close'):
            await self._client.close()


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

_unified_client: Optional[UnifiedSunoClient] = None

def get_unified_suno() -> UnifiedSunoClient:
    """Get or create unified Suno client"""
    global _unified_client
    if _unified_client is None:
        _unified_client = UnifiedSunoClient()
    return _unified_client


# =============================================================================
# CLI TEST
# =============================================================================

async def _test():
    """Test the unified client"""
    client = get_unified_suno()
    
    try:
        credits = await client.get_credits()
        print(f"Backend: {client.backend}")
        print(f"Credits: {credits['credits_left']}")
        
        # Test generation
        songs = await client.generate(
            "calm ambient music for studying",
            instrumental=True
        )
        
        for song in songs:
            print(f"Generated: {song['title']}")
            print(f"  URL: {song['audio_url']}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
