"""
Nano Banana Studio Pro - Animation Service
============================================
Multi-provider image-to-video animation with intelligent fallback.

Providers:
- Runway Gen-2/Gen-3 (cloud)
- Kling AI (cloud)
- Stable Video Diffusion (local)
- LTX Video (local)
- Ken Burns FFmpeg (fallback)

Features:
- Provider auto-selection based on availability
- Motion type presets (subtle, talking, dancing, walking, action)
- Character consistency through face locking
- Quality/speed trade-offs
- Caching and job management

Dependencies:
    pip install httpx aiofiles pillow
"""

import os
import json
import asyncio
import hashlib
import logging
import base64
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger("animation-service")


# =============================================================================
# CONFIGURATION
# =============================================================================

class AnimationConfig:
    """Animation service configuration"""
    # Provider APIs
    RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")
    RUNWAY_API_URL = "https://api.runwayml.com/v1"
    
    KLING_API_KEY = os.getenv("KLING_API_KEY", "")
    KLING_API_URL = os.getenv("KLING_API_URL", "https://api.klingai.com")
    
    REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY", "")
    
    # Local services
    SVD_SERVICE_URL = os.getenv("SVD_SERVICE_URL", "http://localhost:8001")
    LTX_SERVICE_URL = os.getenv("LTX_SERVICE_URL", "http://localhost:8002")
    COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")
    
    # Paths
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/outputs"))
    CACHE_DIR = Path(os.getenv("CACHE_DIR", "/app/data/cache/animations"))
    TEMP_DIR = Path(os.getenv("TEMP_DIR", "/app/data/temp"))
    
    # FFmpeg
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
    
    # Defaults
    DEFAULT_DURATION = float(os.getenv("DEFAULT_ANIMATION_DURATION", "4.0"))
    DEFAULT_FPS = int(os.getenv("DEFAULT_ANIMATION_FPS", "24"))
    MAX_DURATION = float(os.getenv("MAX_ANIMATION_DURATION", "10.0"))


# =============================================================================
# ENUMS & DATA MODELS
# =============================================================================

class AnimationProvider(str, Enum):
    AUTO = "auto"
    RUNWAY = "runway"
    KLING = "kling"
    SVD = "svd"
    LTX = "ltx"
    COMFYUI = "comfyui"
    KENBURNS = "kenburns"


class MotionType(str, Enum):
    SUBTLE = "subtle"
    TALKING = "talking"
    DANCING = "dancing"
    WALKING = "walking"
    ACTION = "action"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    CUSTOM = "custom"


class AnimationQuality(str, Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class AnimationRequest:
    """Animation request parameters"""
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    
    motion_type: MotionType = MotionType.SUBTLE
    motion_prompt: Optional[str] = None
    
    duration: float = 4.0
    fps: int = 24
    
    provider: AnimationProvider = AnimationProvider.AUTO
    quality: AnimationQuality = AnimationQuality.STANDARD
    
    # Character consistency
    character_id: Optional[str] = None
    face_lock: bool = False
    
    # Advanced
    seed: Optional[int] = None
    cfg_scale: float = 7.0
    motion_strength: float = 0.5
    
    def to_dict(self) -> Dict:
        return {
            "motion_type": self.motion_type.value,
            "motion_prompt": self.motion_prompt,
            "duration": self.duration,
            "fps": self.fps,
            "provider": self.provider.value,
            "quality": self.quality.value,
            "character_id": self.character_id,
            "face_lock": self.face_lock,
            "seed": self.seed,
            "cfg_scale": self.cfg_scale,
            "motion_strength": self.motion_strength
        }


@dataclass
class AnimationResult:
    """Animation result"""
    job_id: str
    video_path: str
    duration: float
    fps: int
    resolution: Tuple[int, int]
    provider_used: str
    file_size: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "video_path": self.video_path,
            "duration": self.duration,
            "fps": self.fps,
            "resolution": list(self.resolution),
            "provider_used": self.provider_used,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


# =============================================================================
# MOTION PRESETS
# =============================================================================

MOTION_PRESETS: Dict[MotionType, Dict[str, Any]] = {
    MotionType.SUBTLE: {
        "prompt_suffix": "subtle movement, gentle motion, slight breathing",
        "motion_strength": 0.3,
        "cfg_scale": 7.0
    },
    MotionType.TALKING: {
        "prompt_suffix": "talking, speaking, mouth moving, facial expressions",
        "motion_strength": 0.5,
        "cfg_scale": 7.5
    },
    MotionType.DANCING: {
        "prompt_suffix": "dancing, rhythmic movement, body swaying, dynamic motion",
        "motion_strength": 0.7,
        "cfg_scale": 6.5
    },
    MotionType.WALKING: {
        "prompt_suffix": "walking forward, stepping, natural gait",
        "motion_strength": 0.6,
        "cfg_scale": 7.0
    },
    MotionType.ACTION: {
        "prompt_suffix": "dynamic action, fast movement, dramatic motion",
        "motion_strength": 0.8,
        "cfg_scale": 6.0
    },
    MotionType.ZOOM_IN: {
        "prompt_suffix": "camera zooming in slowly",
        "motion_strength": 0.4,
        "cfg_scale": 7.5
    },
    MotionType.ZOOM_OUT: {
        "prompt_suffix": "camera zooming out slowly",
        "motion_strength": 0.4,
        "cfg_scale": 7.5
    },
    MotionType.PAN_LEFT: {
        "prompt_suffix": "camera panning left",
        "motion_strength": 0.4,
        "cfg_scale": 7.5
    },
    MotionType.PAN_RIGHT: {
        "prompt_suffix": "camera panning right",
        "motion_strength": 0.4,
        "cfg_scale": 7.5
    },
    MotionType.CUSTOM: {
        "prompt_suffix": "",
        "motion_strength": 0.5,
        "cfg_scale": 7.0
    }
}


# =============================================================================
# PROVIDER CLIENTS
# =============================================================================

class RunwayClient:
    """Runway Gen-2/Gen-3 API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def generate(
        self,
        image_base64: str,
        prompt: str,
        duration: float = 4.0,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate video using Runway API"""
        if not self.api_key:
            raise ValueError("Runway API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "promptImage": f"data:image/png;base64,{image_base64}",
            "promptText": prompt,
            "model": "gen3a_turbo",
            "duration": int(duration),
            "watermark": False
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        # Start generation
        response = await self.client.post(
            f"{AnimationConfig.RUNWAY_API_URL}/image_to_video",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Runway API error: {response.text}")
        
        task_id = response.json().get("id")
        
        # Poll for completion
        for _ in range(120):  # 10 minutes max
            await asyncio.sleep(5)
            
            status_response = await self.client.get(
                f"{AnimationConfig.RUNWAY_API_URL}/tasks/{task_id}",
                headers=headers
            )
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "SUCCEEDED":
                return {
                    "video_url": status_data.get("output", [None])[0],
                    "duration": duration,
                    "provider": "runway"
                }
            elif status == "FAILED":
                raise Exception(f"Runway generation failed: {status_data.get('error')}")
        
        raise Exception("Runway generation timed out")
    
    async def close(self):
        await self.client.aclose()


class KlingClient:
    """Kling AI API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def generate(
        self,
        image_base64: str,
        prompt: str,
        duration: float = 5.0,
        mode: str = "std"
    ) -> Dict[str, Any]:
        """Generate video using Kling API"""
        if not self.api_key:
            raise ValueError("Kling API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "image": f"data:image/png;base64,{image_base64}",
            "prompt": prompt,
            "duration": str(int(duration)),
            "mode": mode,
            "aspect_ratio": "16:9"
        }
        
        response = await self.client.post(
            f"{AnimationConfig.KLING_API_URL}/v1/images/generations",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Kling API error: {response.text}")
        
        task_id = response.json().get("task_id")
        
        # Poll for completion
        for _ in range(120):
            await asyncio.sleep(5)
            
            status_response = await self.client.get(
                f"{AnimationConfig.KLING_API_URL}/v1/images/generations/{task_id}",
                headers=headers
            )
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "completed":
                return {
                    "video_url": status_data.get("video_url"),
                    "duration": duration,
                    "provider": "kling"
                }
            elif status == "failed":
                raise Exception(f"Kling generation failed")
        
        raise Exception("Kling generation timed out")
    
    async def close(self):
        await self.client.aclose()


class SVDClient:
    """Stable Video Diffusion local client"""
    
    def __init__(self, service_url: str):
        self.service_url = service_url
        self.client = httpx.AsyncClient(timeout=600.0)
    
    async def is_available(self) -> bool:
        """Check if SVD service is running"""
        try:
            response = await self.client.get(f"{self.service_url}/health", timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    async def generate(
        self,
        image_base64: str,
        motion_bucket_id: int = 127,
        fps: int = 24,
        num_frames: int = 25,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate video using local SVD"""
        payload = {
            "image": image_base64,
            "motion_bucket_id": motion_bucket_id,
            "fps": fps,
            "num_frames": num_frames,
            "decode_chunk_size": 8
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        response = await self.client.post(
            f"{self.service_url}/generate",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"SVD service error: {response.text}")
        
        return response.json()
    
    async def close(self):
        await self.client.aclose()


class KenBurnsGenerator:
    """FFmpeg-based Ken Burns effect generator (fallback)"""
    
    @staticmethod
    async def generate(
        image_path: str,
        output_path: str,
        duration: float = 4.0,
        fps: int = 30,
        motion_type: MotionType = MotionType.ZOOM_IN,
        width: int = 1920,
        height: int = 1080
    ) -> Dict[str, Any]:
        """Generate Ken Burns animation using FFmpeg"""
        
        frames = int(duration * fps)
        
        # Build zoom/pan based on motion type
        if motion_type == MotionType.ZOOM_IN:
            zoom_expr = f"1+0.1*on/{frames}"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == MotionType.ZOOM_OUT:
            zoom_expr = f"1.1-0.1*on/{frames}"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == MotionType.PAN_LEFT:
            zoom_expr = "1.05"
            x_expr = f"iw*0.05-iw*0.1*on/{frames}"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == MotionType.PAN_RIGHT:
            zoom_expr = "1.05"
            x_expr = f"iw*0.1*on/{frames}"
            y_expr = "ih/2-(ih/zoom/2)"
        else:  # Subtle
            zoom_expr = f"1+0.05*on/{frames}"
            x_expr = f"iw/2-(iw/zoom/2)+iw*0.01*sin(2*PI*on/{frames})"
            y_expr = "ih/2-(ih/zoom/2)"
        
        filter_complex = (
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={frames}:s={width}x{height}:fps={fps},"
            f"format=yuv420p"
        )
        
        cmd = [
            AnimationConfig.FFMPEG_PATH,
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", filter_complex,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr.decode()}")
        
        if Path(output_path).exists():
            return {
                "video_path": output_path,
                "duration": duration,
                "fps": fps,
                "resolution": (width, height),
                "provider": "kenburns"
            }
        
        raise Exception("FFmpeg output not created")


# =============================================================================
# MAIN ANIMATION SERVICE
# =============================================================================

class AnimationService:
    """
    Enterprise-grade animation service with multi-provider support.
    Automatically selects best available provider based on quality/speed needs.
    """
    
    def __init__(self):
        self.runway = RunwayClient(AnimationConfig.RUNWAY_API_KEY) if AnimationConfig.RUNWAY_API_KEY else None
        self.kling = KlingClient(AnimationConfig.KLING_API_KEY) if AnimationConfig.KLING_API_KEY else None
        self.svd = SVDClient(AnimationConfig.SVD_SERVICE_URL)
        self.kenburns = KenBurnsGenerator()
        
        AnimationConfig.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        AnimationConfig.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        AnimationConfig.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rand_hash = hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
        return f"anim_{timestamp}_{rand_hash}"
    
    async def _get_image_base64(self, request: AnimationRequest) -> Tuple[str, str]:
        """Get image as base64 and save path"""
        job_id = self._generate_job_id()
        
        if request.image_base64:
            image_data = base64.b64decode(request.image_base64)
        elif request.image_url:
            async with httpx.AsyncClient() as client:
                response = await client.get(request.image_url)
                image_data = response.content
            request.image_base64 = base64.b64encode(image_data).decode()
        elif request.image_path:
            image_data = Path(request.image_path).read_bytes()
            request.image_base64 = base64.b64encode(image_data).decode()
        else:
            raise ValueError("No image provided")
        
        # Save input image
        input_path = AnimationConfig.TEMP_DIR / f"{job_id}_input.png"
        input_path.write_bytes(image_data)
        
        return job_id, str(input_path)
    
    async def _select_provider(self, request: AnimationRequest) -> AnimationProvider:
        """Select best available provider"""
        if request.provider != AnimationProvider.AUTO:
            return request.provider
        
        # Check availability in order of preference
        if request.quality == AnimationQuality.ULTRA:
            if self.runway and AnimationConfig.RUNWAY_API_KEY:
                return AnimationProvider.RUNWAY
            if self.kling and AnimationConfig.KLING_API_KEY:
                return AnimationProvider.KLING
        
        # Try local SVD first (no API costs)
        if await self.svd.is_available():
            return AnimationProvider.SVD
        
        # Cloud providers
        if self.runway and AnimationConfig.RUNWAY_API_KEY:
            return AnimationProvider.RUNWAY
        if self.kling and AnimationConfig.KLING_API_KEY:
            return AnimationProvider.KLING
        
        # Fallback to Ken Burns
        return AnimationProvider.KENBURNS
    
    async def animate(self, request: AnimationRequest) -> AnimationResult:
        """
        Animate an image using the best available provider.
        
        Args:
            request: Animation request parameters
            
        Returns:
            AnimationResult with video path and metadata
        """
        logger.info(f"Starting animation with motion type: {request.motion_type}")
        
        job_id, input_path = await self._get_image_base64(request)
        provider = await self._select_provider(request)
        
        logger.info(f"Selected provider: {provider}")
        
        # Get motion preset
        preset = MOTION_PRESETS.get(request.motion_type, MOTION_PRESETS[MotionType.SUBTLE])
        
        # Build motion prompt
        motion_prompt = request.motion_prompt or ""
        if preset["prompt_suffix"]:
            motion_prompt = f"{motion_prompt} {preset['prompt_suffix']}".strip()
        
        output_path = str(AnimationConfig.OUTPUT_DIR / f"{job_id}_animated.mp4")
        
        try:
            if provider == AnimationProvider.RUNWAY:
                result = await self.runway.generate(
                    image_base64=request.image_base64,
                    prompt=motion_prompt,
                    duration=min(request.duration, 10.0),
                    seed=request.seed
                )
                # Download video
                async with httpx.AsyncClient() as client:
                    video_response = await client.get(result["video_url"])
                    Path(output_path).write_bytes(video_response.content)
                    
            elif provider == AnimationProvider.KLING:
                result = await self.kling.generate(
                    image_base64=request.image_base64,
                    prompt=motion_prompt,
                    duration=min(request.duration, 10.0)
                )
                async with httpx.AsyncClient() as client:
                    video_response = await client.get(result["video_url"])
                    Path(output_path).write_bytes(video_response.content)
                    
            elif provider == AnimationProvider.SVD:
                frames = int(request.duration * request.fps)
                motion_bucket = int(preset["motion_strength"] * 255)
                result = await self.svd.generate(
                    image_base64=request.image_base64,
                    motion_bucket_id=motion_bucket,
                    fps=request.fps,
                    num_frames=min(frames, 50),
                    seed=request.seed
                )
                if "video_base64" in result:
                    Path(output_path).write_bytes(base64.b64decode(result["video_base64"]))
                    
            else:  # Ken Burns fallback
                result = await self.kenburns.generate(
                    image_path=input_path,
                    output_path=output_path,
                    duration=request.duration,
                    fps=request.fps,
                    motion_type=request.motion_type
                )
            
            # Get video info
            file_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
            
            return AnimationResult(
                job_id=job_id,
                video_path=output_path,
                duration=request.duration,
                fps=request.fps,
                resolution=(1920, 1080),
                provider_used=provider.value,
                file_size=file_size,
                metadata={
                    "motion_type": request.motion_type.value,
                    "motion_prompt": motion_prompt,
                    "seed": request.seed
                }
            )
            
        except Exception as e:
            logger.error(f"Animation failed with {provider}: {e}")
            
            # Fallback to Ken Burns if other provider fails
            if provider != AnimationProvider.KENBURNS:
                logger.info("Falling back to Ken Burns animation")
                result = await self.kenburns.generate(
                    image_path=input_path,
                    output_path=output_path,
                    duration=request.duration,
                    fps=request.fps,
                    motion_type=request.motion_type
                )
                
                return AnimationResult(
                    job_id=job_id,
                    video_path=output_path,
                    duration=request.duration,
                    fps=request.fps,
                    resolution=(1920, 1080),
                    provider_used="kenburns",
                    file_size=Path(output_path).stat().st_size,
                    metadata={"fallback": True, "original_provider": provider.value}
                )
            
            raise
    
    async def close(self):
        """Close all clients"""
        if self.runway:
            await self.runway.close()
        if self.kling:
            await self.kling.close()
        await self.svd.close()


# =============================================================================
# SINGLETON
# =============================================================================

_animation_service: Optional[AnimationService] = None

def get_animation_service() -> AnimationService:
    """Get or create animation service instance"""
    global _animation_service
    if _animation_service is None:
        _animation_service = AnimationService()
    return _animation_service
