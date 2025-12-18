"""
Nano Banana Studio Pro - Suno AI Music Integration Service
============================================================
Enterprise-grade Suno API integration with multiple backend support:
- gcui-art/suno-api (TypeScript/Vercel)
- Local Python client (direct cookie auth)
- Keep-alive session management
- Rate limiting & credit protection

SECURITY NOTE: Your Suno cookie is sensitive! Never commit to Git.
Store in environment variables or .env file only.

Dependencies:
    pip install httpx aiohttp tenacity pydantic
"""

import os
import json
import asyncio
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field

logger = logging.getLogger("suno-service")

# =============================================================================
# CONFIGURATION
# =============================================================================

class SunoConfig:
    """Suno API configuration"""
    
    # API Endpoints (choose your deployment)
    VERCEL_API_URL = os.getenv("SUNO_VERCEL_URL", "https://your-suno-api.vercel.app")
    LOCAL_API_URL = os.getenv("SUNO_LOCAL_URL", "http://localhost:3000")
    
    # Direct Suno endpoints (for advanced use)
    SUNO_BASE_URL = "https://studio-api.suno.ai"
    SUNO_CLERK_URL = "https://clerk.suno.com"
    
    # Authentication
    SUNO_COOKIE = os.getenv("SUNO_COOKIE", "")
    
    # Rate limiting (protect your credits!)
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("SUNO_RATE_LIMIT", "10"))
    MAX_CONCURRENT_GENERATIONS = int(os.getenv("SUNO_MAX_CONCURRENT", "2"))
    
    # Timeouts
    GENERATION_TIMEOUT = int(os.getenv("SUNO_TIMEOUT", "300"))  # 5 minutes
    POLL_INTERVAL = int(os.getenv("SUNO_POLL_INTERVAL", "5"))  # seconds
    
    # Keep-alive
    KEEP_ALIVE_INTERVAL = int(os.getenv("SUNO_KEEP_ALIVE", "180"))  # 3 minutes
    
    # 2Captcha (optional, for CAPTCHA solving)
    CAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "")


# =============================================================================
# DATA MODELS
# =============================================================================

class SunoStyle(str, Enum):
    """Popular Suno music styles"""
    POP = "pop"
    ROCK = "rock"
    ELECTRONIC = "electronic"
    HIP_HOP = "hip hop"
    RNB = "r&b"
    JAZZ = "jazz"
    CLASSICAL = "classical"
    COUNTRY = "country"
    FOLK = "folk"
    METAL = "metal"
    INDIE = "indie"
    AMBIENT = "ambient"
    LOFI = "lo-fi"
    CINEMATIC = "cinematic"
    EPIC = "epic orchestral"
    SYNTHWAVE = "synthwave"
    CHILLWAVE = "chillwave"
    ACOUSTIC = "acoustic"
    BLUES = "blues"
    REGGAE = "reggae"
    LATIN = "latin"
    KPOP = "k-pop"
    JPOP = "j-pop"
    ANIME = "anime"
    CHRISTMAS = "christmas"
    

class SunoMood(str, Enum):
    """Music mood descriptors"""
    HAPPY = "happy, upbeat"
    SAD = "sad, melancholic"
    ENERGETIC = "energetic, powerful"
    CALM = "calm, peaceful"
    ROMANTIC = "romantic, emotional"
    DARK = "dark, mysterious"
    EPIC = "epic, triumphant"
    NOSTALGIC = "nostalgic, bittersweet"
    ANGRY = "angry, intense"
    DREAMY = "dreamy, ethereal"


class GenerationMode(str, Enum):
    """Suno generation modes"""
    SIMPLE = "simple"  # Just a prompt
    CUSTOM = "custom"  # With lyrics, style, title


class SongStatus(str, Enum):
    """Song generation status"""
    PENDING = "pending"
    GENERATING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


class SunoGenerateRequest(BaseModel):
    """Request model for music generation"""
    prompt: str = Field(..., description="Music description or generation prompt")
    style: Optional[str] = Field(None, description="Music style (e.g., 'pop', 'rock')")
    title: Optional[str] = Field(None, description="Song title")
    lyrics: Optional[str] = Field(None, description="Custom lyrics (Custom Mode)")
    instrumental: bool = Field(False, description="Generate instrumental only")
    duration: Optional[int] = Field(None, description="Target duration in seconds")
    continue_clip_id: Optional[str] = Field(None, description="ID to extend existing song")
    continue_at: Optional[float] = Field(None, description="Timestamp to continue from")
    make_instrumental: bool = Field(False, description="Remove vocals from output")
    model: str = Field("chirp-v3-5", description="Suno model version")
    

class SunoSong(BaseModel):
    """Suno song response model"""
    id: str
    title: str
    status: SongStatus
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    duration: Optional[float] = None
    lyrics: Optional[str] = None
    style: Optional[str] = None
    model_name: Optional[str] = None
    created_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class SunoCredits(BaseModel):
    """Suno credit information"""
    credits_left: int
    monthly_limit: int
    monthly_usage: int
    period: Optional[str] = None


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """Token bucket rate limiter for credit protection"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[datetime] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire a rate limit token"""
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.time_window)
            
            # Remove old requests
            self.requests = [r for r in self.requests if r > cutoff]
            
            if len(self.requests) >= self.max_requests:
                wait_time = (self.requests[0] - cutoff).total_seconds()
                logger.warning(f"Rate limit reached. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                return await self.acquire()
            
            self.requests.append(now)
            return True
    
    @property
    def remaining(self) -> int:
        """Get remaining requests in current window"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.time_window)
        active = [r for r in self.requests if r > cutoff]
        return max(0, self.max_requests - len(active))


# =============================================================================
# SUNO API CLIENT
# =============================================================================

class SunoClient:
    """
    Suno AI music generation client.
    
    Supports multiple backends:
    - Vercel-deployed gcui-art/suno-api
    - Local suno-api instance
    - Direct Suno API (advanced)
    
    Example:
        client = SunoClient()
        song = await client.generate("upbeat pop song about summer")
        print(song.audio_url)
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        cookie: Optional[str] = None,
        use_rate_limiter: bool = True
    ):
        """
        Initialize Suno client.
        
        Args:
            api_url: API endpoint (Vercel or local)
            cookie: Suno session cookie (required for direct API)
            use_rate_limiter: Enable credit protection
        """
        self.api_url = api_url or SunoConfig.VERCEL_API_URL
        self.cookie = cookie or SunoConfig.SUNO_COOKIE
        
        # HTTP client with keep-alive
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(SunoConfig.GENERATION_TIMEOUT),
            follow_redirects=True
        )
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            SunoConfig.MAX_REQUESTS_PER_MINUTE
        ) if use_rate_limiter else None
        
        # Session management
        self._session_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._keep_alive_task: Optional[asyncio.Task] = None
        
        # Semaphore for concurrent generations
        self._generation_semaphore = asyncio.Semaphore(
            SunoConfig.MAX_CONCURRENT_GENERATIONS
        )
        
        logger.info(f"SunoClient initialized with API: {self.api_url}")
    
    async def _ensure_session(self):
        """Ensure valid session token"""
        if self._session_token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return
        
        # Refresh token
        await self._refresh_token()
    
    async def _refresh_token(self):
        """Refresh session token from cookie"""
        if not self.cookie:
            raise ValueError("Suno cookie not configured. Set SUNO_COOKIE env var.")
        
        # The token is extracted from the cookie
        # gcui-art/suno-api handles this automatically
        self._session_token = self.cookie
        self._token_expires = datetime.utcnow() + timedelta(hours=1)
        
        logger.debug("Session token refreshed")
    
    async def start_keep_alive(self):
        """Start background keep-alive task"""
        if self._keep_alive_task:
            return
        
        async def _keep_alive_loop():
            while True:
                try:
                    await asyncio.sleep(SunoConfig.KEEP_ALIVE_INTERVAL)
                    await self.get_credits()
                    logger.debug("Keep-alive ping successful")
                except Exception as e:
                    logger.warning(f"Keep-alive failed: {e}")
        
        self._keep_alive_task = asyncio.create_task(_keep_alive_loop())
        logger.info("Keep-alive task started")
    
    async def stop_keep_alive(self):
        """Stop keep-alive task"""
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            self._keep_alive_task = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.cookie:
            headers["Cookie"] = self.cookie
        
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make API request with retry logic"""
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        url = f"{self.api_url}{endpoint}"
        
        response = await self.client.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=self._get_headers()
        )
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited. Waiting {retry_after}s")
            await asyncio.sleep(retry_after)
            raise httpx.HTTPStatusError(
                "Rate limited",
                request=response.request,
                response=response
            )
        
        response.raise_for_status()
        return response.json()
    
    # -------------------------------------------------------------------------
    # PUBLIC API METHODS
    # -------------------------------------------------------------------------
    
    async def get_credits(self) -> SunoCredits:
        """
        Get remaining credits.
        
        Returns:
            SunoCredits object with balance info
        """
        data = await self._request("GET", "/api/get_limit")
        
        return SunoCredits(
            credits_left=data.get("credits_left", 0),
            monthly_limit=data.get("monthly_limit", 0),
            monthly_usage=data.get("monthly_usage", 0),
            period=data.get("period")
        )
    
    async def generate(
        self,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = None,
        instrumental: bool = False,
        wait_for_completion: bool = True
    ) -> List[SunoSong]:
        """
        Generate music from a text prompt (Simple Mode).
        
        Args:
            prompt: Description of the music to generate
            style: Music style (optional, enhances prompt)
            title: Song title (optional)
            instrumental: Generate without vocals
            wait_for_completion: Wait for generation to finish
            
        Returns:
            List of generated SunoSong objects (usually 2)
            
        Example:
            songs = await client.generate(
                "upbeat summer pop song with catchy chorus",
                style="pop",
                instrumental=False
            )
        """
        async with self._generation_semaphore:
            # Build enhanced prompt
            full_prompt = prompt
            if style:
                full_prompt = f"{style} style: {prompt}"
            
            payload = {
                "prompt": full_prompt,
                "make_instrumental": instrumental,
                "wait_audio": wait_for_completion
            }
            
            if title:
                payload["title"] = title
            
            logger.info(f"Generating music: {full_prompt[:50]}...")
            
            data = await self._request("POST", "/api/generate", payload)
            
            songs = self._parse_songs(data)
            
            if wait_for_completion and songs:
                songs = await self._wait_for_songs(songs)
            
            logger.info(f"Generated {len(songs)} songs")
            return songs
    
    async def generate_custom(
        self,
        lyrics: str,
        style: str,
        title: str,
        instrumental: bool = False,
        wait_for_completion: bool = True
    ) -> List[SunoSong]:
        """
        Generate music with custom lyrics (Custom Mode).
        
        Args:
            lyrics: Song lyrics with structure markers
            style: Music style/genre
            title: Song title
            instrumental: Generate instrumental version
            wait_for_completion: Wait for generation to finish
            
        Returns:
            List of generated SunoSong objects
            
        Example:
            songs = await client.generate_custom(
                lyrics=\"\"\"
                [Verse 1]
                Walking down the sunny street
                Summer vibes beneath my feet
                
                [Chorus]
                It's a beautiful day
                Let's dance the night away
                \"\"\",
                style="upbeat pop, summer vibes, catchy",
                title="Beautiful Day"
            )
        """
        async with self._generation_semaphore:
            payload = {
                "prompt": lyrics,
                "tags": style,
                "title": title,
                "make_instrumental": instrumental,
                "wait_audio": wait_for_completion
            }
            
            logger.info(f"Generating custom song: {title}")
            
            data = await self._request("POST", "/api/custom_generate", payload)
            
            songs = self._parse_songs(data)
            
            if wait_for_completion and songs:
                songs = await self._wait_for_songs(songs)
            
            return songs
    
    async def generate_lyrics(
        self,
        prompt: str
    ) -> str:
        """
        Generate lyrics from a prompt.
        
        Args:
            prompt: Description of the song concept
            
        Returns:
            Generated lyrics with structure markers
            
        Example:
            lyrics = await client.generate_lyrics(
                "a love song about meeting someone special at a coffee shop"
            )
        """
        payload = {"prompt": prompt}
        
        data = await self._request("POST", "/api/generate_lyrics", payload)
        
        return data.get("text", "")
    
    async def extend_song(
        self,
        song_id: str,
        continue_at: float,
        prompt: Optional[str] = None,
        style: Optional[str] = None,
        wait_for_completion: bool = True
    ) -> List[SunoSong]:
        """
        Extend an existing song.
        
        Args:
            song_id: ID of the song to extend
            continue_at: Timestamp (seconds) to continue from
            prompt: Additional context for extension
            style: Style tags for extension
            wait_for_completion: Wait for generation
            
        Returns:
            List of extended SunoSong objects
        """
        async with self._generation_semaphore:
            payload = {
                "continue_clip_id": song_id,
                "continue_at": continue_at,
                "wait_audio": wait_for_completion
            }
            
            if prompt:
                payload["prompt"] = prompt
            if style:
                payload["tags"] = style
            
            logger.info(f"Extending song {song_id} from {continue_at}s")
            
            data = await self._request("POST", "/api/extend_audio", payload)
            
            songs = self._parse_songs(data)
            
            if wait_for_completion and songs:
                songs = await self._wait_for_songs(songs)
            
            return songs
    
    async def get_song(self, song_id: str) -> Optional[SunoSong]:
        """
        Get a song by ID.
        
        Args:
            song_id: Song ID
            
        Returns:
            SunoSong object or None
        """
        data = await self._request("GET", "/api/get", params={"ids": song_id})
        
        songs = self._parse_songs(data)
        return songs[0] if songs else None
    
    async def get_songs(self, song_ids: List[str]) -> List[SunoSong]:
        """
        Get multiple songs by ID.
        
        Args:
            song_ids: List of song IDs
            
        Returns:
            List of SunoSong objects
        """
        ids_str = ",".join(song_ids)
        data = await self._request("GET", "/api/get", params={"ids": ids_str})
        
        return self._parse_songs(data)
    
    async def concat_songs(
        self,
        clip_id: str,
        wait_for_completion: bool = True
    ) -> Optional[SunoSong]:
        """
        Concatenate extended clips into a full song.
        
        Args:
            clip_id: ID of the song to concatenate
            wait_for_completion: Wait for processing
            
        Returns:
            Concatenated SunoSong object
        """
        payload = {"clip_id": clip_id}
        
        data = await self._request("POST", "/api/concat", payload)
        
        songs = self._parse_songs(data)
        
        if wait_for_completion and songs:
            songs = await self._wait_for_songs(songs)
        
        return songs[0] if songs else None
    
    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------
    
    def _parse_songs(self, data: Union[Dict, List]) -> List[SunoSong]:
        """Parse API response into SunoSong objects"""
        if isinstance(data, dict):
            data = data.get("data", [data]) if "data" in data else [data]
        
        songs = []
        for item in data:
            try:
                song = SunoSong(
                    id=item.get("id", ""),
                    title=item.get("title", "Untitled"),
                    status=self._parse_status(item.get("status", "pending")),
                    audio_url=item.get("audio_url"),
                    video_url=item.get("video_url"),
                    image_url=item.get("image_url") or item.get("image_large_url"),
                    duration=item.get("duration"),
                    lyrics=item.get("lyric") or item.get("prompt"),
                    style=item.get("tags") or item.get("style"),
                    model_name=item.get("model_name"),
                    created_at=self._parse_datetime(item.get("created_at")),
                    error_message=item.get("error_message"),
                    metadata=item.get("metadata", {})
                )
                songs.append(song)
            except Exception as e:
                logger.warning(f"Failed to parse song: {e}")
        
        return songs
    
    def _parse_status(self, status: str) -> SongStatus:
        """Parse status string to enum"""
        status_map = {
            "pending": SongStatus.PENDING,
            "streaming": SongStatus.GENERATING,
            "complete": SongStatus.COMPLETE,
            "error": SongStatus.ERROR,
        }
        return status_map.get(status.lower(), SongStatus.PENDING)
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None
    
    async def _wait_for_songs(
        self,
        songs: List[SunoSong],
        timeout: int = None
    ) -> List[SunoSong]:
        """Wait for songs to complete generation"""
        timeout = timeout or SunoConfig.GENERATION_TIMEOUT
        start_time = datetime.utcnow()
        song_ids = [s.id for s in songs]
        
        while True:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                logger.warning("Generation timeout reached")
                break
            
            # Check status
            updated_songs = await self.get_songs(song_ids)
            
            all_complete = all(
                s.status in (SongStatus.COMPLETE, SongStatus.ERROR)
                for s in updated_songs
            )
            
            if all_complete:
                logger.info("All songs completed")
                return updated_songs
            
            # Log progress
            pending = sum(1 for s in updated_songs if s.status == SongStatus.PENDING)
            generating = sum(1 for s in updated_songs if s.status == SongStatus.GENERATING)
            logger.debug(f"Progress: {pending} pending, {generating} generating")
            
            await asyncio.sleep(SunoConfig.POLL_INTERVAL)
        
        return songs
    
    async def download_song(
        self,
        song: SunoSong,
        output_dir: Path,
        include_video: bool = False
    ) -> Dict[str, Path]:
        """
        Download song files.
        
        Args:
            song: SunoSong object
            output_dir: Directory to save files
            include_video: Also download video if available
            
        Returns:
            Dict with paths to downloaded files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Download audio
        if song.audio_url:
            audio_path = output_dir / f"{song.id}.mp3"
            await self._download_file(song.audio_url, audio_path)
            results["audio"] = audio_path
            logger.info(f"Downloaded audio: {audio_path}")
        
        # Download video
        if include_video and song.video_url:
            video_path = output_dir / f"{song.id}.mp4"
            await self._download_file(song.video_url, video_path)
            results["video"] = video_path
            logger.info(f"Downloaded video: {video_path}")
        
        # Download cover image
        if song.image_url:
            image_path = output_dir / f"{song.id}.jpg"
            await self._download_file(song.image_url, image_path)
            results["image"] = image_path
        
        return results
    
    async def _download_file(self, url: str, path: Path):
        """Download file from URL"""
        async with self.client.stream("GET", url) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
    
    async def close(self):
        """Close client and cleanup"""
        await self.stop_keep_alive()
        await self.client.aclose()
        logger.info("SunoClient closed")


# =============================================================================
# HIGH-LEVEL INTEGRATION FOR NANO BANANA
# =============================================================================

class SunoMusicService:
    """
    High-level music service for Nano Banana Studio Pro integration.
    
    Provides simplified interface for common music generation tasks.
    """
    
    def __init__(self):
        self.client = SunoClient()
        self._initialized = False
    
    async def initialize(self):
        """Initialize service and start keep-alive"""
        if self._initialized:
            return
        
        # Check credits
        credits = await self.client.get_credits()
        logger.info(f"Suno credits available: {credits.credits_left}")
        
        if credits.credits_left < 10:
            logger.warning("Low Suno credits! Consider recharging.")
        
        # Start keep-alive
        await self.client.start_keep_alive()
        
        self._initialized = True
    
    async def generate_background_music(
        self,
        description: str,
        duration: int = 60,
        style: str = "cinematic"
    ) -> Optional[SunoSong]:
        """
        Generate background music for video.
        
        Args:
            description: Scene/mood description
            duration: Target duration in seconds
            style: Music style
            
        Returns:
            Best matching SunoSong
        """
        await self.initialize()
        
        # Build prompt optimized for background music
        prompt = f"""
        {style} instrumental background music.
        {description}
        Duration: approximately {duration} seconds.
        No vocals, suitable for video background.
        Smooth, professional production quality.
        """
        
        songs = await self.client.generate(
            prompt=prompt.strip(),
            style=style,
            instrumental=True,
            wait_for_completion=True
        )
        
        if not songs:
            return None
        
        # Return the one closest to target duration
        return min(songs, key=lambda s: abs((s.duration or 0) - duration))
    
    async def generate_theme_song(
        self,
        title: str,
        theme: str,
        style: str,
        mood: str,
        with_lyrics: bool = True
    ) -> Optional[SunoSong]:
        """
        Generate a theme/intro song.
        
        Args:
            title: Song/video title
            theme: Theme description
            style: Music style
            mood: Mood descriptor
            with_lyrics: Include vocals
            
        Returns:
            Generated SunoSong
        """
        await self.initialize()
        
        if with_lyrics:
            # Generate lyrics first
            lyrics_prompt = f"""
            Write a short theme song about: {theme}
            Title: {title}
            Style: {style}
            Mood: {mood}
            Keep it catchy and memorable, about 1 minute long.
            """
            
            lyrics = await self.client.generate_lyrics(lyrics_prompt)
            
            songs = await self.client.generate_custom(
                lyrics=lyrics,
                style=f"{style}, {mood}",
                title=title,
                instrumental=False,
                wait_for_completion=True
            )
        else:
            prompt = f"{style} {mood} theme song for: {theme}"
            songs = await self.client.generate(
                prompt=prompt,
                style=style,
                title=title,
                instrumental=True,
                wait_for_completion=True
            )
        
        return songs[0] if songs else None
    
    async def generate_genre_music(
        self,
        genre: SunoStyle,
        mood: SunoMood,
        context: str = "",
        instrumental: bool = True
    ) -> Optional[SunoSong]:
        """
        Generate music by genre and mood.
        
        Args:
            genre: SunoStyle enum
            mood: SunoMood enum
            context: Additional context
            instrumental: No vocals
            
        Returns:
            Generated SunoSong
        """
        await self.initialize()
        
        prompt = f"{genre.value} music, {mood.value}"
        if context:
            prompt += f". {context}"
        
        songs = await self.client.generate(
            prompt=prompt,
            style=genre.value,
            instrumental=instrumental,
            wait_for_completion=True
        )
        
        return songs[0] if songs else None
    
    async def extend_to_duration(
        self,
        song: SunoSong,
        target_duration: int
    ) -> SunoSong:
        """
        Extend a song to reach target duration.
        
        Args:
            song: Original song
            target_duration: Target duration in seconds
            
        Returns:
            Extended SunoSong
        """
        await self.initialize()
        
        current = song
        
        while (current.duration or 0) < target_duration:
            # Extend from near the end
            continue_at = max(0, (current.duration or 30) - 5)
            
            extended = await self.client.extend_song(
                song_id=current.id,
                continue_at=continue_at,
                style=current.style,
                wait_for_completion=True
            )
            
            if not extended:
                break
            
            current = extended[0]
            logger.info(f"Extended to {current.duration}s")
        
        # Concatenate all extensions
        final = await self.client.concat_songs(current.id)
        
        return final or current
    
    async def close(self):
        """Close service"""
        await self.client.close()


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_suno_service: Optional[SunoMusicService] = None

def get_suno_service() -> SunoMusicService:
    """Get or create Suno service instance"""
    global _suno_service
    if _suno_service is None:
        _suno_service = SunoMusicService()
    return _suno_service


# =============================================================================
# CLI TESTING
# =============================================================================

async def _test_suno():
    """Test Suno integration"""
    service = get_suno_service()
    
    try:
        # Check credits
        credits = await service.client.get_credits()
        print(f"Credits: {credits.credits_left}/{credits.monthly_limit}")
        
        # Generate test music
        song = await service.generate_background_music(
            description="peaceful nature scene with flowing water",
            duration=30,
            style="ambient"
        )
        
        if song:
            print(f"Generated: {song.title}")
            print(f"Duration: {song.duration}s")
            print(f"URL: {song.audio_url}")
        
    finally:
        await service.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test_suno())
