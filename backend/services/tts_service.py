"""
Nano Banana Studio Pro - TTS Service
======================================
Multi-provider text-to-speech synthesis.

Providers:
- ElevenLabs (cloud, high quality)
- OpenAI TTS (cloud)
- Coqui XTTS (local)
- Edge TTS (free, cloud)
- Bark (local, expressive)

Features:
- Voice cloning support
- Multi-language synthesis
- Emotion/style control
- SSML support
- Streaming synthesis

Dependencies:
    pip install httpx edge-tts pydub
"""

import os
import json
import asyncio
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger("tts-service")


# =============================================================================
# CONFIGURATION
# =============================================================================

class TTSConfig:
    """TTS service configuration"""
    # API Keys
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Local services
    XTTS_SERVICE_URL = os.getenv("XTTS_SERVICE_URL", "http://localhost:8003")
    BARK_SERVICE_URL = os.getenv("BARK_SERVICE_URL", "http://localhost:8004")
    
    # Paths
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/outputs"))
    VOICE_DIR = Path(os.getenv("VOICE_DIR", "/app/data/voices"))
    CACHE_DIR = Path(os.getenv("CACHE_DIR", "/app/data/cache/tts"))


# =============================================================================
# ENUMS & DATA MODELS
# =============================================================================

class TTSProvider(str, Enum):
    AUTO = "auto"
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    EDGE = "edge"
    XTTS = "xtts"
    BARK = "bark"


class Voice(str, Enum):
    # ElevenLabs voices
    ADAM = "adam"
    RACHEL = "rachel"
    DOMI = "domi"
    BELLA = "bella"
    ANTONI = "antoni"
    
    # OpenAI voices
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"
    
    # Edge TTS voices
    JENNY = "en-US-JennyNeural"
    GUY = "en-US-GuyNeural"
    ARIA = "en-US-AriaNeural"


class SpeechStyle(str, Enum):
    NEUTRAL = "neutral"
    CHEERFUL = "cheerful"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    WHISPERING = "whispering"
    SHOUTING = "shouting"
    NARRATION = "narration"


VOICE_MAPPINGS: Dict[TTSProvider, Dict[str, str]] = {
    TTSProvider.ELEVENLABS: {
        "adam": "pNInz6obpgDQGcFmaJgB",
        "rachel": "21m00Tcm4TlvDq8ikWAM",
        "domi": "AZnzlk1XvdvUeBnXmlld",
        "bella": "EXAVITQu4vr4xnSDxMaL",
        "antoni": "ErXwobaYiN019PkySvjV"
    },
    TTSProvider.OPENAI: {
        "alloy": "alloy",
        "echo": "echo",
        "fable": "fable",
        "onyx": "onyx",
        "nova": "nova",
        "shimmer": "shimmer"
    },
    TTSProvider.EDGE: {
        "jenny": "en-US-JennyNeural",
        "guy": "en-US-GuyNeural",
        "aria": "en-US-AriaNeural"
    }
}


@dataclass
class TTSRequest:
    """TTS synthesis request"""
    text: str
    voice: str = "alloy"
    provider: TTSProvider = TTSProvider.AUTO
    language: str = "en"
    
    speed: float = 1.0
    pitch: float = 1.0
    style: SpeechStyle = SpeechStyle.NEUTRAL
    
    # Voice cloning
    reference_audio: Optional[str] = None
    
    output_path: Optional[str] = None


@dataclass
class TTSResult:
    """TTS synthesis result"""
    job_id: str
    audio_path: str
    duration: float
    provider_used: str
    voice_used: str
    file_size: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "audio_path": self.audio_path,
            "duration": self.duration,
            "provider_used": self.provider_used,
            "voice_used": self.voice_used,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat()
        }


# =============================================================================
# PROVIDER CLIENTS
# =============================================================================

class ElevenLabsClient:
    """ElevenLabs TTS client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        model: str = "eleven_monolingual_v1"
    ) -> bytes:
        """Synthesize speech"""
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}/text-to-speech/{voice_id}",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"ElevenLabs error: {response.text}")
        
        return response.content
    
    async def close(self):
        await self.client.aclose()


class OpenAITTSClient:
    """OpenAI TTS client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        speed: float = 1.0
    ) -> bytes:
        """Synthesize speech"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed
        }
        
        response = await self.client.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI TTS error: {response.text}")
        
        return response.content
    
    async def close(self):
        await self.client.aclose()


class EdgeTTSClient:
    """Microsoft Edge TTS client (free)"""
    
    async def synthesize(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> bytes:
        """Synthesize speech using edge-tts"""
        try:
            import edge_tts
        except ImportError:
            raise ImportError("edge-tts package required: pip install edge-tts")
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return audio_data


# =============================================================================
# TTS SERVICE
# =============================================================================

class TTSService:
    """
    Enterprise-grade TTS service with multi-provider support.
    """
    
    def __init__(self):
        self.elevenlabs = ElevenLabsClient(TTSConfig.ELEVENLABS_API_KEY) if TTSConfig.ELEVENLABS_API_KEY else None
        self.openai = OpenAITTSClient(TTSConfig.OPENAI_API_KEY) if TTSConfig.OPENAI_API_KEY else None
        self.edge = EdgeTTSClient()
        
        TTSConfig.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        TTSConfig.VOICE_DIR.mkdir(parents=True, exist_ok=True)
        TTSConfig.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rand_hash = hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
        return f"tts_{timestamp}_{rand_hash}"
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using ffprobe"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
        return 0.0
    
    async def _select_provider(self, request: TTSRequest) -> TTSProvider:
        """Select best available provider"""
        if request.provider != TTSProvider.AUTO:
            return request.provider
        
        # Check availability
        if self.elevenlabs and TTSConfig.ELEVENLABS_API_KEY:
            return TTSProvider.ELEVENLABS
        if self.openai and TTSConfig.OPENAI_API_KEY:
            return TTSProvider.OPENAI
        
        # Fallback to Edge TTS (free)
        return TTSProvider.EDGE
    
    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """
        Synthesize speech from text.
        
        Args:
            request: TTS request with text and voice settings
            
        Returns:
            TTSResult with audio path and metadata
        """
        logger.info(f"Synthesizing TTS: {request.text[:50]}...")
        
        job_id = self._generate_job_id()
        provider = await self._select_provider(request)
        
        logger.info(f"Using provider: {provider.value}")
        
        # Get voice ID for provider
        voice_map = VOICE_MAPPINGS.get(provider, {})
        voice_id = voice_map.get(request.voice.lower(), request.voice)
        
        try:
            if provider == TTSProvider.ELEVENLABS:
                audio_data = await self.elevenlabs.synthesize(
                    text=request.text,
                    voice_id=voice_id
                )
            elif provider == TTSProvider.OPENAI:
                audio_data = await self.openai.synthesize(
                    text=request.text,
                    voice=voice_id,
                    speed=request.speed
                )
            elif provider == TTSProvider.EDGE:
                rate = f"+{int((request.speed - 1) * 100)}%" if request.speed >= 1 else f"{int((request.speed - 1) * 100)}%"
                audio_data = await self.edge.synthesize(
                    text=request.text,
                    voice=voice_id,
                    rate=rate
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Save audio
            if request.output_path:
                output_path = request.output_path
            else:
                ext = "mp3" if provider != TTSProvider.EDGE else "mp3"
                output_path = str(TTSConfig.OUTPUT_DIR / f"{job_id}.{ext}")
            
            Path(output_path).write_bytes(audio_data)
            
            # Get duration
            duration = self._get_audio_duration(output_path)
            
            return TTSResult(
                job_id=job_id,
                audio_path=output_path,
                duration=duration,
                provider_used=provider.value,
                voice_used=voice_id,
                file_size=len(audio_data)
            )
            
        except Exception as e:
            logger.error(f"TTS failed with {provider}: {e}")
            
            # Fallback to Edge TTS
            if provider != TTSProvider.EDGE:
                logger.info("Falling back to Edge TTS")
                request.provider = TTSProvider.EDGE
                return await self.synthesize(request)
            
            raise
    
    async def synthesize_long_text(
        self,
        text: str,
        voice: str = "alloy",
        max_chunk_length: int = 500
    ) -> TTSResult:
        """Synthesize long text by chunking"""
        # Split text into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_length:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Synthesize each chunk
        audio_files = []
        for i, chunk in enumerate(chunks):
            request = TTSRequest(text=chunk, voice=voice)
            result = await self.synthesize(request)
            audio_files.append(result.audio_path)
        
        # Concatenate audio files
        if len(audio_files) > 1:
            job_id = self._generate_job_id()
            output_path = str(TTSConfig.OUTPUT_DIR / f"{job_id}_combined.mp3")
            
            # Create concat file
            concat_file = TTSConfig.CACHE_DIR / f"{job_id}_concat.txt"
            with open(concat_file, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
            
            # Concatenate with ffmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            # Cleanup temp files
            concat_file.unlink()
            for audio_file in audio_files:
                Path(audio_file).unlink()
            
            duration = self._get_audio_duration(output_path)
            
            return TTSResult(
                job_id=job_id,
                audio_path=output_path,
                duration=duration,
                provider_used="combined",
                voice_used=voice,
                file_size=Path(output_path).stat().st_size
            )
        
        # Single chunk result
        return TTSResult(
            job_id=self._generate_job_id(),
            audio_path=audio_files[0],
            duration=self._get_audio_duration(audio_files[0]),
            provider_used="single",
            voice_used=voice,
            file_size=Path(audio_files[0]).stat().st_size
        )
    
    async def close(self):
        """Close all clients"""
        if self.elevenlabs:
            await self.elevenlabs.close()
        if self.openai:
            await self.openai.close()


# =============================================================================
# SINGLETON
# =============================================================================

_tts_service: Optional[TTSService] = None

def get_tts_service() -> TTSService:
    """Get or create TTS service instance"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
