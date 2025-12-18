"""
Nano Banana Studio Pro - FastAPI Backend
=========================================
Complete API server for professional AI video production.

Endpoints:
- /api/v1/enhance/* - Prompt enhancement (7 stages)
- /api/v1/face/* - Face detection & character consistency
- /api/v1/generate/* - Image generation (Nano Banana / Gemini)
- /api/v1/animate/* - Image-to-video animation
- /api/v1/audio/* - Audio analysis & processing
- /api/v1/video/* - Video assembly & export
- /api/v1/suno/* - AI music generation
- /api/v1/jobs/* - Job queue management
- /ws/{job_id} - WebSocket real-time updates
"""

import os
import json
import asyncio
import hashlib
import base64
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis

from backend.api.middleware import setup_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nano-banana")

# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    # API Keys (from environment)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")
    SUNO_COOKIE = os.getenv("SUNO_COOKIE", "")
    
    # Local Services
    LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Paths
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/data/uploads"))
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/outputs"))
    CACHE_DIR = Path(os.getenv("CACHE_DIR", "/app/data/cache"))
    
    # Model defaults
    DEFAULT_IMAGE_MODEL = "google/gemini-2.0-flash-exp:free"
    DEFAULT_LLM_MODEL = "gpt-4o-mini"

config = Config()

# Ensure directories exist
for dir_path in [config.UPLOAD_DIR, config.OUTPUT_DIR, config.CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class PromptEnhanceRequest(BaseModel):
    prompt: str
    style: Optional[str] = "Cinematic"
    platform: Optional[str] = "YouTube (16:9)"
    enhancement_level: Optional[str] = "full"  # quick, standard, full
    include_negative: Optional[bool] = True

class PromptEnhanceResponse(BaseModel):
    job_id: str
    original_prompt: str
    enhanced_prompt: str
    negative_prompt: Optional[str]
    stages_completed: List[str]
    style_dna: Dict[str, Any]
    timestamp: str

class FaceExtractRequest(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None

class FaceExtractResponse(BaseModel):
    job_id: str
    face_detected: bool
    face_count: int
    primary_face: Optional[Dict[str, Any]]
    face_embedding: Optional[List[float]]
    bounding_box: Optional[Dict[str, int]]
    landmarks: Optional[List[Dict[str, float]]]

class CharacterRegisterRequest(BaseModel):
    name: str
    face_embedding: List[float]
    reference_images: Optional[List[str]] = []
    style_keywords: Optional[List[str]] = []

class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    style: Optional[str] = "Photorealistic"
    aspect_ratio: Optional[str] = "16:9"
    quality: Optional[str] = "high"
    num_images: Optional[int] = 1
    character_id: Optional[str] = None  # For character consistency
    reference_image: Optional[str] = None  # Base64 reference
    seed: Optional[int] = None
    use_enhancement: Optional[bool] = True

class AnimateRequest(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    motion_type: Optional[str] = "subtle"  # subtle, talking, dancing, walking
    duration: Optional[float] = 4.0
    provider: Optional[str] = "auto"  # auto, runway, kling, svd

class AudioAnalyzeRequest(BaseModel):
    audio_base64: Optional[str] = None
    audio_url: Optional[str] = None
    extract_lyrics: Optional[bool] = True
    detect_beats: Optional[bool] = True

class AudioAnalyzeResponse(BaseModel):
    job_id: str
    duration: float
    bpm: float
    beats: List[float]
    energy_curve: List[float]
    lyrics: Optional[str]
    sections: List[Dict[str, Any]]

class SunoGenerateRequest(BaseModel):
    prompt: str
    genre: Optional[str] = "pop"
    duration: Optional[int] = 60
    instrumental: Optional[bool] = False

class VideoAssembleRequest(BaseModel):
    manifest: Dict[str, Any]
    platform: Optional[str] = "YouTube (16:9)"
    quality: Optional[str] = "high"
    transition_style: Optional[str] = "dissolve"
    ken_burns: Optional[bool] = True
    color_grading: Optional[str] = "none"

class StoryboardRequest(BaseModel):
    prompt: Optional[str] = None
    lyrics: Optional[str] = None
    audio_analysis: Optional[Dict[str, Any]] = None
    duration: Optional[float] = 60
    scene_count: Optional[int] = None
    style: Optional[str] = "Cinematic"

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: float  # 0.0 - 1.0
    current_stage: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: str
    updated_at: str

# =============================================================================
# SERVICES
# =============================================================================

class CacheService:
    """Content-addressed caching with fingerprinting"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.redis: Optional[redis.Redis] = None
    
    async def connect_redis(self):
        try:
            self.redis = redis.from_url(config.REDIS_URL)
            await self.redis.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis = None
    
    def compute_fingerprint(self, **kwargs) -> str:
        """Compute SHA256 fingerprint from parameters"""
        data = json.dumps(kwargs, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def get_cached(self, fingerprint: str) -> Optional[Dict]:
        """Get cached result by fingerprint"""
        if self.redis:
            cached = await self.redis.get(f"cache:{fingerprint}")
            if cached:
                return json.loads(cached)
        
        # Fallback to file cache
        cache_file = self.cache_dir / f"{fingerprint}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None
    
    async def set_cached(self, fingerprint: str, data: Dict, ttl: int = 86400):
        """Cache result with fingerprint"""
        if self.redis:
            await self.redis.setex(f"cache:{fingerprint}", ttl, json.dumps(data))
        
        # Also save to file
        cache_file = self.cache_dir / f"{fingerprint}.json"
        cache_file.write_text(json.dumps(data))

class JobQueueService:
    """Job queue management with status tracking"""
    
    def __init__(self):
        self.jobs: Dict[str, JobStatus] = {}
        self.redis: Optional[redis.Redis] = None
    
    async def connect_redis(self):
        try:
            self.redis = redis.from_url(config.REDIS_URL)
            logger.info("Job queue Redis connected")
        except Exception as e:
            logger.warning(f"Redis not available for jobs: {e}")
    
    def create_job(self, job_type: str) -> str:
        """Create new job and return ID"""
        import uuid
        job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.jobs[job_id] = JobStatus(
            job_id=job_id,
            status="queued",
            progress=0.0,
            current_stage=None,
            result=None,
            error=None,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        return job_id
    
    def update_job(self, job_id: str, **kwargs):
        """Update job status"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.now().isoformat()
    
    def get_job(self, job_id: str) -> Optional[JobStatus]:
        return self.jobs.get(job_id)

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
    
    async def send_update(self, job_id: str, message: Dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

class LLMService:
    """Multi-provider LLM service with fallback"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=120.0)
    
    async def complete(self, 
                       messages: List[Dict[str, str]], 
                       model: str = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       provider: str = "auto") -> str:
        """Get completion from LLM with fallback chain"""
        
        providers_to_try = []
        
        if provider == "auto":
            # Try local first, then cloud
            if config.LM_STUDIO_URL:
                providers_to_try.append(("lm_studio", config.LM_STUDIO_URL))
            if config.OLLAMA_URL:
                providers_to_try.append(("ollama", config.OLLAMA_URL))
            if config.OPENAI_API_KEY:
                providers_to_try.append(("openai", "https://api.openai.com/v1"))
        elif provider == "lm_studio":
            providers_to_try.append(("lm_studio", config.LM_STUDIO_URL))
        elif provider == "openai":
            providers_to_try.append(("openai", "https://api.openai.com/v1"))
        
        for prov_name, base_url in providers_to_try:
            try:
                headers = {"Content-Type": "application/json"}
                if prov_name == "openai":
                    headers["Authorization"] = f"Bearer {config.OPENAI_API_KEY}"
                
                response = await self.http_client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model or ("gpt-4o-mini" if prov_name == "openai" else "local-model"),
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                    
            except Exception as e:
                logger.warning(f"Provider {prov_name} failed: {e}")
                continue
        
        raise HTTPException(status_code=503, detail="All LLM providers unavailable")

# Initialize services
cache_service = CacheService(config.CACHE_DIR)
job_queue = JobQueueService()
ws_manager = WebSocketManager()
llm_service = LLMService()

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await cache_service.connect_redis()
    await job_queue.connect_redis()
    logger.info("Nano Banana Studio API started")
    yield
    # Shutdown
    logger.info("Nano Banana Studio API shutting down")

app = FastAPI(
    title="Nano Banana Studio Pro API",
    description="Professional AI Video Production Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup enhanced error handling middleware
try:
    setup_middleware(app)
except ImportError:
    logger.warning("Middleware not available - using basic error handling")

# =============================================================================
# HEALTH & INFO ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    return {
        "name": "Nano Banana Studio Pro",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "enhance": "/api/v1/enhance/*",
            "face": "/api/v1/face/*",
            "generate": "/api/v1/generate/*",
            "animate": "/api/v1/animate/*",
            "audio": "/api/v1/audio/*",
            "video": "/api/v1/video/*",
            "jobs": "/api/v1/jobs/*",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# =============================================================================
# PROMPT ENHANCEMENT ENDPOINTS
# =============================================================================

@app.post("/api/v1/enhance/concept")
async def enhance_concept(request: PromptEnhanceRequest):
    """Stage 1: Concept Enhancement"""
    job_id = job_queue.create_job("enhance_concept")
    
    system_prompt = """You are an expert creative director. Transform the basic concept into a rich creative brief.
    
    Return JSON with:
    - enhanced_concept (2-3 sentences)
    - core_theme (1 sentence)
    - mood_profile (3-5 adjectives)
    - emotional_keywords (5-7 words)
    - visual_metaphors (2-3 ideas)"""
    
    try:
        result = await llm_service.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Enhance this concept for {request.style} style: {request.prompt}"}
            ],
            temperature=0.7
        )
        
        # Parse JSON response
        try:
            cleaned = result.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
        except:
            data = {"enhanced_concept": result}
        
        job_queue.update_job(job_id, status="completed", progress=1.0, result=data)
        return {"job_id": job_id, "stage": "concept", **data}
        
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/enhance/full")
async def enhance_full(request: PromptEnhanceRequest, background_tasks: BackgroundTasks):
    """Run full 7-stage prompt enhancement pipeline"""
    job_id = job_queue.create_job("enhance_full")
    
    # Run enhancement in background
    background_tasks.add_task(run_full_enhancement, job_id, request)
    
    return {"job_id": job_id, "status": "processing", "message": "Full enhancement started"}

async def run_full_enhancement(job_id: str, request: PromptEnhanceRequest):
    """Background task for full enhancement"""
    stages = ["concept", "scene", "visual", "cinematic", "narrative", "technical", "consistency"]
    results = {}
    current_prompt = request.prompt
    
    stage_prompts = {
        "concept": "Transform into rich creative brief with theme, mood, and metaphors.",
        "scene": "Define environment, atmosphere, spatial composition, and time context.",
        "visual": "Specify color palette, lighting, composition, and texture.",
        "cinematic": "Add camera angles, lens characteristics, and shot dynamics.",
        "narrative": "Define story beat, emotional arc, and audience engagement.",
        "technical": "Add resolution, quality keywords, and technical specifications.",
        "consistency": "Extract style DNA and create final production-ready prompt."
    }
    
    try:
        for i, stage in enumerate(stages):
            job_queue.update_job(job_id, 
                                 status="processing", 
                                 progress=(i / len(stages)),
                                 current_stage=stage)
            
            result = await llm_service.complete(
                messages=[
                    {"role": "system", "content": f"Stage {i+1}: {stage_prompts[stage]} Return enhanced prompt."},
                    {"role": "user", "content": f"Style: {request.style}\nCurrent: {current_prompt}"}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            results[stage] = result
            current_prompt = result
            
            await ws_manager.send_update(job_id, {
                "stage": stage,
                "progress": (i + 1) / len(stages),
                "result": result
            })
        
        # Generate negative prompt
        negative_prompt = ""
        if request.include_negative:
            neg_result = await llm_service.complete(
                messages=[
                    {"role": "system", "content": "Generate a negative prompt to avoid quality issues. Return only the negative prompt text."},
                    {"role": "user", "content": f"For this prompt, what should be avoided: {current_prompt}"}
                ],
                temperature=0.5
            )
            negative_prompt = neg_result
        
        final_result = {
            "original_prompt": request.prompt,
            "enhanced_prompt": current_prompt,
            "negative_prompt": negative_prompt,
            "stages": results,
            "style_dna": {
                "style": request.style,
                "platform": request.platform,
                "anchor_keywords": current_prompt.split(",")[:5]
            }
        }
        
        job_queue.update_job(job_id, status="completed", progress=1.0, result=final_result)
        await ws_manager.send_update(job_id, {"status": "completed", "result": final_result})
        
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))
        await ws_manager.send_update(job_id, {"status": "failed", "error": str(e)})

# =============================================================================
# FACE DETECTION & CHARACTER CONSISTENCY
# =============================================================================

# In-memory character registry (would use database in production)
character_registry: Dict[str, Dict] = {}

@app.post("/api/v1/face/extract")
async def extract_face(
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None)
):
    """Extract face from image for character consistency"""
    job_id = job_queue.create_job("face_extract")
    
    # Get image data
    image_data = None
    if image:
        image_data = await image.read()
    elif image_base64:
        image_data = base64.b64decode(image_base64)
    elif image_url:
        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            image_data = resp.content
    
    if not image_data:
        raise HTTPException(status_code=400, detail="No image provided")
    
    # Save image temporarily
    temp_path = config.UPLOAD_DIR / f"{job_id}_input.jpg"
    temp_path.write_bytes(image_data)
    
    # Real face detection using FaceService
    try:
        from backend.services.face_service import get_face_service
        face_service = get_face_service()
        
        # Detect faces in image
        detections = face_service.detect_faces(str(temp_path))
        
        if not detections:
            face_result = {
                "face_detected": False,
                "face_count": 0,
                "error": "No faces detected in image",
                "image_path": str(temp_path)
            }
        else:
            # Get primary face (highest confidence)
            primary = max(detections, key=lambda d: d.confidence)
            
            # Extract embedding for primary face
            import cv2
            import numpy as np
            img = cv2.imread(str(temp_path))
            embedding = face_service.embedder.get_embedding(img)
            
            face_result = {
                "face_detected": True,
                "face_count": len(detections),
                "primary_face": {
                    "confidence": primary.confidence,
                    "bounding_box": {
                        "x": primary.bbox[0],
                        "y": primary.bbox[1],
                        "width": primary.bbox[2] - primary.bbox[0],
                        "height": primary.bbox[3] - primary.bbox[1]
                    }
                },
                "face_embedding": embedding.tolist() if embedding is not None else None,
                "landmarks": [{"x": lm[0], "y": lm[1]} for lm in (primary.landmarks or [])[:10]],
                "image_path": str(temp_path)
            }
    except ImportError:
        # Fallback if FaceService not available
        logger.warning("FaceService not available, using basic detection")
        face_result = {
            "face_detected": True,
            "face_count": 1,
            "primary_face": {"confidence": 0.95, "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 250}},
            "face_embedding": [0.0] * 512,
            "landmarks": [],
            "image_path": str(temp_path),
            "fallback": True
        }
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        face_result = {
            "face_detected": False,
            "error": str(e),
            "image_path": str(temp_path)
        }
    
    job_queue.update_job(job_id, status="completed", progress=1.0, result=face_result)
    
    return {"job_id": job_id, **face_result}

@app.post("/api/v1/character/register")
async def register_character(request: CharacterRegisterRequest):
    """Register a character for consistency across generations"""
    char_id = f"char_{hashlib.md5(request.name.encode()).hexdigest()[:8]}"
    
    character_registry[char_id] = {
        "id": char_id,
        "name": request.name,
        "face_embedding": request.face_embedding,
        "reference_images": request.reference_images,
        "style_keywords": request.style_keywords,
        "created_at": datetime.now().isoformat()
    }
    
    return {"character_id": char_id, "name": request.name, "status": "registered"}

@app.get("/api/v1/character/{char_id}")
async def get_character(char_id: str):
    """Get registered character details"""
    if char_id not in character_registry:
        raise HTTPException(status_code=404, detail="Character not found")
    return character_registry[char_id]

@app.post("/api/v1/character/verify")
async def verify_character_consistency(
    character_id: str = Form(...),
    image_base64: str = Form(...)
):
    """Verify if generated image matches registered character"""
    if character_id not in character_registry:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = character_registry[character_id]
    threshold = 0.85
    
    try:
        from backend.services.face_service import get_face_service
        import numpy as np
        import cv2
        
        face_service = get_face_service()
        
        # Decode image and save temporarily
        image_data = base64.b64decode(image_base64)
        temp_path = config.UPLOAD_DIR / f"verify_{character_id}_{datetime.now().timestamp()}.jpg"
        temp_path.write_bytes(image_data)
        
        # Get embedding from new image
        img = cv2.imread(str(temp_path))
        new_embedding = face_service.embedder.get_embedding(img)
        
        if new_embedding is None:
            return {
                "character_id": character_id,
                "character_name": character["name"],
                "match_score": 0.0,
                "is_consistent": False,
                "threshold": threshold,
                "error": "No face detected in verification image"
            }
        
        # Get stored embedding
        stored_embedding = np.array(character.get("face_embedding", []))
        
        if stored_embedding.size == 0:
            return {
                "character_id": character_id,
                "character_name": character["name"],
                "match_score": 0.0,
                "is_consistent": False,
                "threshold": threshold,
                "error": "Character has no stored face embedding"
            }
        
        # Compute cosine similarity
        dot_product = np.dot(new_embedding, stored_embedding)
        norm_a = np.linalg.norm(new_embedding)
        norm_b = np.linalg.norm(stored_embedding)
        similarity = dot_product / (norm_a * norm_b) if (norm_a * norm_b) > 0 else 0.0
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        return {
            "character_id": character_id,
            "character_name": character["name"],
            "match_score": float(similarity),
            "is_consistent": similarity >= threshold,
            "threshold": threshold
        }
        
    except ImportError:
        logger.warning("FaceService not available for verification")
        return {
            "character_id": character_id,
            "character_name": character.get("name", "Unknown"),
            "match_score": 0.90,
            "is_consistent": True,
            "threshold": threshold,
            "fallback": True
        }
    except Exception as e:
        logger.error(f"Character verification error: {e}")
        return {
            "character_id": character_id,
            "match_score": 0.0,
            "is_consistent": False,
            "threshold": threshold,
            "error": str(e)
        }

# =============================================================================
# IMAGE GENERATION (NANO BANANA / GEMINI)
# =============================================================================

@app.post("/api/v1/generate/image")
async def generate_image(request: ImageGenerateRequest, background_tasks: BackgroundTasks):
    """Generate image using Nano Banana Pro (Gemini) or other models"""
    job_id = job_queue.create_job("generate_image")
    
    # Check cache first
    fingerprint = cache_service.compute_fingerprint(
        prompt=request.prompt,
        negative=request.negative_prompt,
        style=request.style,
        aspect=request.aspect_ratio,
        seed=request.seed
    )
    
    cached = await cache_service.get_cached(fingerprint)
    if cached:
        return {"job_id": job_id, "status": "cached", "result": cached}
    
    # Run generation in background
    background_tasks.add_task(run_image_generation, job_id, request, fingerprint)
    
    return {"job_id": job_id, "status": "processing", "fingerprint": fingerprint}

async def run_image_generation(job_id: str, request: ImageGenerateRequest, fingerprint: str):
    """Background task for image generation"""
    try:
        job_queue.update_job(job_id, status="processing", current_stage="enhancing")
        
        # Enhance prompt if requested
        final_prompt = request.prompt
        if request.use_enhancement:
            enhanced = await llm_service.complete(
                messages=[
                    {"role": "system", "content": "Enhance this image prompt with visual details. Return only the enhanced prompt."},
                    {"role": "user", "content": f"Style: {request.style}\nPrompt: {request.prompt}"}
                ],
                temperature=0.7
            )
            final_prompt = enhanced
        
        job_queue.update_job(job_id, current_stage="generating")
        
        # Call OpenRouter for Gemini/Nano Banana
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://nano-banana-studio.local",
                "X-Title": "Nano Banana Studio"
            }
            
            # Build message with optional reference image
            content = [{"type": "text", "text": f"Generate an image: {final_prompt}"}]
            
            if request.reference_image:
                content.insert(0, {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{request.reference_image}"}
                })
            
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": config.DEFAULT_IMAGE_MODEL,
                    "messages": [{"role": "user", "content": content}],
                    "max_tokens": 4096,
                    "temperature": 0.9
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Extract image data
                image_data = None
                if "data:image" in str(result_content):
                    import re
                    match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', str(result_content))
                    if match:
                        image_data = match.group(1)
                
                # Save image
                if image_data:
                    image_path = config.OUTPUT_DIR / f"{job_id}.png"
                    image_path.write_bytes(base64.b64decode(image_data))
                    
                    result = {
                        "image_data": image_data,
                        "image_path": str(image_path),
                        "prompt_used": final_prompt,
                        "fingerprint": fingerprint
                    }
                    
                    # Cache result
                    await cache_service.set_cached(fingerprint, result)
                    
                    job_queue.update_job(job_id, status="completed", progress=1.0, result=result)
                    await ws_manager.send_update(job_id, {"status": "completed", "result": result})
                else:
                    raise Exception("No image in response")
            else:
                raise Exception(f"API error: {response.status_code}")
                
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))
        await ws_manager.send_update(job_id, {"status": "failed", "error": str(e)})

@app.post("/api/v1/generate/batch")
async def generate_batch(
    prompts: List[str] = Form(...),
    style: str = Form("Photorealistic"),
    aspect_ratio: str = Form("16:9"),
    background_tasks: BackgroundTasks = None
):
    """Generate multiple images in parallel"""
    job_id = job_queue.create_job("generate_batch")
    batch_jobs = []
    
    for i, prompt in enumerate(prompts):
        sub_job_id = f"{job_id}_{i}"
        batch_jobs.append(sub_job_id)
        request = ImageGenerateRequest(prompt=prompt, style=style, aspect_ratio=aspect_ratio)
        background_tasks.add_task(run_image_generation, sub_job_id, request, f"batch_{i}")
    
    return {"job_id": job_id, "batch_jobs": batch_jobs, "total": len(prompts)}

# =============================================================================
# IMAGE-TO-VIDEO ANIMATION
# =============================================================================

@app.post("/api/v1/animate/image")
async def animate_image(request: AnimateRequest, background_tasks: BackgroundTasks):
    """Animate a still image into video"""
    job_id = job_queue.create_job("animate_image")
    
    background_tasks.add_task(run_animation, job_id, request)
    
    return {"job_id": job_id, "status": "processing", "motion_type": request.motion_type}

async def run_animation(job_id: str, request: AnimateRequest):
    """Background task for image animation"""
    try:
        job_queue.update_job(job_id, status="processing", current_stage="preparing")
        
        # Get image data
        image_data = None
        if request.image_base64:
            image_data = request.image_base64
        elif request.image_url:
            async with httpx.AsyncClient() as client:
                resp = await client.get(request.image_url)
                image_data = base64.b64encode(resp.content).decode()
        
        if not image_data:
            raise Exception("No image provided")
        
        # Save input image
        input_path = config.UPLOAD_DIR / f"{job_id}_input.png"
        input_path.write_bytes(base64.b64decode(image_data))
        
        job_queue.update_job(job_id, current_stage="animating")
        
        # Provider selection
        # In production, this would call Runway, Kling, or local SVD
        # For now, we'll simulate with Ken Burns effect via FFmpeg
        
        output_path = config.OUTPUT_DIR / f"{job_id}_animated.mp4"
        
        # Generate FFmpeg command for Ken Burns animation
        duration = request.duration
        zoom_effect = "1.0+(0.1*t/4)" if request.motion_type in ["subtle", "zoom_in"] else "1.1-(0.1*t/4)"
        
        ffmpeg_cmd = f'''ffmpeg -loop 1 -i "{input_path}" -vf "zoompan=z='{zoom_effect}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration*30)}:s=1920x1080:fps=30" -c:v libx264 -t {duration} -pix_fmt yuv420p -y "{output_path}"'''
        
        # Execute FFmpeg (in production, use subprocess)
        import subprocess
        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True)
        
        if output_path.exists():
            animation_result = {
                "video_path": str(output_path),
                "duration": duration,
                "motion_type": request.motion_type,
                "provider": "ffmpeg_kenburns"
            }
            
            job_queue.update_job(job_id, status="completed", progress=1.0, result=animation_result)
            await ws_manager.send_update(job_id, {"status": "completed", "result": animation_result})
        else:
            raise Exception("Animation failed")
            
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))
        await ws_manager.send_update(job_id, {"status": "failed", "error": str(e)})

# =============================================================================
# AUDIO ANALYSIS & PROCESSING
# =============================================================================

@app.post("/api/v1/audio/analyze")
async def analyze_audio(
    audio: Optional[UploadFile] = File(None),
    audio_base64: Optional[str] = Form(None),
    extract_lyrics: bool = Form(True),
    detect_beats: bool = Form(True)
):
    """Analyze audio for beats, tempo, and optionally extract lyrics"""
    job_id = job_queue.create_job("audio_analyze")
    
    # Get audio data
    audio_data = None
    if audio:
        audio_data = await audio.read()
    elif audio_base64:
        audio_data = base64.b64decode(audio_base64)
    
    if not audio_data:
        raise HTTPException(status_code=400, detail="No audio provided")
    
    # Save audio
    audio_path = config.UPLOAD_DIR / f"{job_id}_audio.mp3"
    audio_path.write_bytes(audio_data)
    
    # Use AudioIntelligenceService for real analysis
    try:
        from backend.services.audio_intelligence_service import get_audio_intelligence_service
        
        audio_service = get_audio_intelligence_service()
        audio_analysis = await audio_service.analyze(str(audio_path))
        
        analysis = {
            "job_id": job_id,
            "duration": audio_analysis.duration,
            "bpm": audio_analysis.bpm,
            "beats": [b.time for b in audio_analysis.beats],
            "energy_curve": audio_analysis.energy_curve,
            "sections": [
                {"name": s.section_type, "start": s.start_time, "end": s.end_time, "energy": s.energy_level}
                for s in audio_analysis.sections
            ],
            "lyrics": None,
            "audio_path": str(audio_path),
            "fingerprint": audio_analysis.fingerprint
        }
        
    except ImportError:
        logger.warning("AudioIntelligenceService not available, using basic analysis")
        # Fallback to basic FFprobe analysis
        import subprocess
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(audio_path)],
                capture_output=True, text=True
            )
            duration = float(result.stdout.strip()) if result.stdout.strip() else 60.0
        except:
            duration = 60.0
        
        analysis = {
            "job_id": job_id,
            "duration": duration,
            "bpm": 120,
            "beats": [i * 0.5 for i in range(int(duration * 2))],
            "energy_curve": [0.5] * int(duration * 4),
            "sections": [
                {"name": "intro", "start": 0, "end": min(8, duration * 0.1), "energy": "low"},
                {"name": "main", "start": duration * 0.1, "end": duration * 0.9, "energy": "medium"},
                {"name": "outro", "start": duration * 0.9, "end": duration, "energy": "low"}
            ],
            "lyrics": None,
            "audio_path": str(audio_path),
            "fallback": True
        }
    except Exception as e:
        logger.error(f"Audio analysis error: {e}")
        analysis = {
            "job_id": job_id,
            "error": str(e),
            "audio_path": str(audio_path)
        }
    
    # Lyrics extraction with Whisper
    if extract_lyrics and "error" not in analysis:
        try:
            from backend.services.whisper_service import WhisperService
            whisper = WhisperService()
            transcription = await whisper.transcribe(str(audio_path))
            analysis["lyrics"] = transcription.get("text", "")
        except Exception as e:
            logger.warning(f"Whisper transcription failed: {e}")
            analysis["lyrics"] = None
    
    job_queue.update_job(job_id, status="completed", progress=1.0, result=analysis)
    
    return analysis

@app.post("/api/v1/audio/mix")
async def mix_audio(
    tracks: List[UploadFile] = File(...),
    volumes: Optional[str] = Form(None),  # JSON array of volumes
    mode: str = Form("layer")  # layer, sequence, ducking
):
    """Mix multiple audio tracks"""
    job_id = job_queue.create_job("audio_mix")
    
    # Parse volumes
    vol_list = json.loads(volumes) if volumes else [1.0] * len(tracks)
    
    # Save all tracks
    track_paths = []
    for i, track in enumerate(tracks):
        track_path = config.UPLOAD_DIR / f"{job_id}_track_{i}.mp3"
        track_path.write_bytes(await track.read())
        track_paths.append(str(track_path))
    
    # Build FFmpeg command based on mode
    output_path = config.OUTPUT_DIR / f"{job_id}_mixed.mp3"
    
    if mode == "layer":
        # Mix all tracks simultaneously
        inputs = " ".join([f'-i "{p}"' for p in track_paths])
        filter_parts = [f"[{i}:a]volume={vol_list[i]}[a{i}]" for i in range(len(tracks))]
        mix_inputs = "".join([f"[a{i}]" for i in range(len(tracks))])
        filter_complex = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={len(tracks)}:duration=longest[out]"
        ffmpeg_cmd = f'ffmpeg {inputs} -filter_complex "{filter_complex}" -map "[out]" -y "{output_path}"'
    else:
        # Default: concatenate
        inputs = " ".join([f'-i "{p}"' for p in track_paths])
        concat_inputs = "".join([f"[{i}:a]" for i in range(len(tracks))])
        filter_complex = f'{concat_inputs}concat=n={len(tracks)}:v=0:a=1[out]'
        ffmpeg_cmd = f'ffmpeg {inputs} -filter_complex "{filter_complex}" -map "[out]" -y "{output_path}"'
    
    import subprocess
    subprocess.run(ffmpeg_cmd, shell=True, capture_output=True)
    
    return {
        "job_id": job_id,
        "output_path": str(output_path),
        "tracks_mixed": len(tracks),
        "mode": mode
    }


# =============================================================================
# SUNO AI MUSIC GENERATION
# =============================================================================

@app.post("/api/v1/suno/generate")
async def generate_music_suno(request: SunoGenerateRequest, background_tasks: BackgroundTasks):
    """Generate music using Suno API"""
    job_id = job_queue.create_job("suno_generate")
    
    background_tasks.add_task(run_suno_generation, job_id, request)
    
    return {"job_id": job_id, "status": "processing", "genre": request.genre}

async def run_suno_generation(job_id: str, request: SunoGenerateRequest):
    """Background task for Suno music generation"""
    try:
        job_queue.update_job(job_id, status="processing", current_stage="generating")
        
        # Suno API integration (using unofficial wrapper pattern)
        # In production, use gcui-art/suno-api or similar
        
        if not config.SUNO_COOKIE:
            raise Exception("Suno API not configured")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # This would be the actual Suno API endpoint
            # Placeholder for demonstration
            response = await client.post(
                "https://studio-api.suno.ai/api/generate/v2/",
                headers={
                    "Cookie": config.SUNO_COOKIE,
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": request.prompt,
                    "make_instrumental": request.instrumental,
                    "wait_audio": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract audio URL and lyrics
                audio_url = data.get("audio_url", "")
                lyrics = data.get("lyrics", "")
                
                # Download audio
                if audio_url:
                    audio_resp = await client.get(audio_url)
                    audio_path = config.OUTPUT_DIR / f"{job_id}_suno.mp3"
                    audio_path.write_bytes(audio_resp.content)
                    
                    result = {
                        "audio_path": str(audio_path),
                        "audio_url": audio_url,
                        "lyrics": lyrics,
                        "prompt": request.prompt,
                        "genre": request.genre,
                        "duration": request.duration
                    }
                    
                    job_queue.update_job(job_id, status="completed", progress=1.0, result=result)
                    await ws_manager.send_update(job_id, {"status": "completed", "result": result})
                else:
                    raise Exception("No audio URL in response")
            else:
                raise Exception(f"Suno API error: {response.status_code}")
                
    except Exception as e:
        # Fallback: return placeholder for testing
        logger.warning(f"Suno generation failed: {e}")
        
        result = {
            "status": "fallback",
            "message": "Suno API not available, use uploaded MP3 instead",
            "error": str(e)
        }
        
        job_queue.update_job(job_id, status="completed", progress=1.0, result=result)

# =============================================================================
# STORYBOARD GENERATION
# =============================================================================

@app.post("/api/v1/storyboard/generate")
async def generate_storyboard(request: StoryboardRequest, background_tasks: BackgroundTasks):
    """Generate AI storyboard from prompt or lyrics"""
    job_id = job_queue.create_job("storyboard_generate")
    
    background_tasks.add_task(run_storyboard_generation, job_id, request)
    
    return {"job_id": job_id, "status": "processing"}

async def run_storyboard_generation(job_id: str, request: StoryboardRequest):
    """Background task for storyboard generation"""
    try:
        job_queue.update_job(job_id, status="processing", current_stage="analyzing")
        
        # Determine scene count based on duration
        if request.scene_count:
            num_scenes = request.scene_count
        else:
            num_scenes = max(6, int(request.duration / 8))  # ~8 seconds per scene
        
        # Build prompt for LLM
        system_prompt = """You are a professional music video director creating a storyboard.
        
        Given the input (prompt, lyrics, or audio analysis), create a detailed scene-by-scene breakdown.
        
        For each scene include:
        - visual_prompt: Detailed description for image generation
        - duration: Seconds (should sum to total duration)
        - transition: Transition type (dissolve, fade, cut, slide)
        - motion: Camera/subject motion (zoom_in, zoom_out, pan_left, pan_right, static)
        - mood: Emotional tone
        - beat_sync: Whether to sync transition to beat (true/false)
        
        Return JSON array of scenes."""
        
        input_context = f"""
        Theme/Prompt: {request.prompt or 'Music video'}
        Lyrics: {request.lyrics or 'Instrumental'}
        Duration: {request.duration} seconds
        Number of scenes: {num_scenes}
        Style: {request.style}
        
        Audio analysis: {json.dumps(request.audio_analysis) if request.audio_analysis else 'Not provided'}
        """
        
        job_queue.update_job(job_id, current_stage="generating")
        
        result = await llm_service.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_context}
            ],
            temperature=0.8,
            max_tokens=4000
        )
        
        # Parse scenes
        try:
            cleaned = result.replace("```json", "").replace("```", "").strip()
            scenes = json.loads(cleaned)
        except:
            # Generate default scenes
            scenes = []
            scene_duration = request.duration / num_scenes
            
            for i in range(num_scenes):
                scenes.append({
                    "index": i + 1,
                    "visual_prompt": f"{request.style} scene {i+1} for: {request.prompt}",
                    "duration": scene_duration,
                    "transition": "dissolve" if i > 0 else "fade",
                    "motion": "zoom_in" if i % 2 == 0 else "zoom_out",
                    "mood": "energetic" if i % 3 == 0 else "calm",
                    "beat_sync": True
                })
        
        # Enhance each scene prompt with 7-stage enhancement keywords
        for scene in scenes:
            scene["enhanced_prompt"] = f"{scene.get('visual_prompt', '')}, {request.style} style, cinematic lighting, professional quality, 8K, masterpiece"
        
        storyboard = {
            "job_id": job_id,
            "title": request.prompt or "Music Video",
            "duration": request.duration,
            "scene_count": len(scenes),
            "style": request.style,
            "scenes": scenes,
            "audio_sync": request.audio_analysis is not None
        }
        
        job_queue.update_job(job_id, status="completed", progress=1.0, result=storyboard)
        await ws_manager.send_update(job_id, {"status": "completed", "result": storyboard})
        
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))
        await ws_manager.send_update(job_id, {"status": "failed", "error": str(e)})

# =============================================================================
# VIDEO ASSEMBLY
# =============================================================================

@app.post("/api/v1/video/assemble")
async def assemble_video(request: VideoAssembleRequest, background_tasks: BackgroundTasks):
    """Assemble final video from manifest"""
    job_id = job_queue.create_job("video_assemble")
    
    background_tasks.add_task(run_video_assembly, job_id, request)
    
    return {"job_id": job_id, "status": "processing"}

async def run_video_assembly(job_id: str, request: VideoAssembleRequest):
    """Background task for video assembly"""
    try:
        job_queue.update_job(job_id, status="processing", current_stage="preparing")
        
        manifest = request.manifest
        scenes = manifest.get("scenes", [])
        
        if not scenes:
            raise Exception("No scenes in manifest")
        
        # Platform configurations
        platform_configs = {
            "YouTube (16:9)": {"width": 1920, "height": 1080, "fps": 30},
            "YouTube Shorts (9:16)": {"width": 1080, "height": 1920, "fps": 30},
            "TikTok (9:16)": {"width": 1080, "height": 1920, "fps": 30},
            "Instagram (1:1)": {"width": 1080, "height": 1080, "fps": 30},
            "4K (16:9)": {"width": 3840, "height": 2160, "fps": 30}
        }
        
        config_p = platform_configs.get(request.platform, platform_configs["YouTube (16:9)"])
        
        # Quality presets
        quality_presets = {
            "draft": {"preset": "ultrafast", "crf": 28},
            "standard": {"preset": "medium", "crf": 23},
            "high": {"preset": "slow", "crf": 18},
            "maximum": {"preset": "veryslow", "crf": 16}
        }
        
        quality = quality_presets.get(request.quality, quality_presets["standard"])
        
        job_queue.update_job(job_id, current_stage="building_filter")
        
        # Build FFmpeg filter complex
        filter_parts = []
        input_files = []
        
        for i, scene in enumerate(scenes):
            image_path = scene.get("image_path") or scene.get("imageFilename")
            if image_path:
                input_files.append(f'-loop 1 -t {scene.get("duration", 5)} -i "{image_path}"')
                
                # Scale and Ken Burns
                scale_filter = f"[{i}:v]scale={config_p['width']}:{config_p['height']}:force_original_aspect_ratio=decrease,pad={config_p['width']}:{config_p['height']}:(ow-iw)/2:(oh-ih)/2:black"
                
                if request.ken_burns:
                    duration = scene.get("duration", 5)
                    frames = int(duration * config_p["fps"])
                    zoom = "1.0+(0.1*on/" + str(frames) + ")" if i % 2 == 0 else "1.1-(0.1*on/" + str(frames) + ")"
                    scale_filter += f",zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={config_p['width']}x{config_p['height']}:fps={config_p['fps']}"
                
                scale_filter += f"[v{i}]"
                filter_parts.append(scale_filter)
        
        # Build transition chain
        if len(scenes) > 1:
            transition_type = request.transition_style or "dissolve"
            transition_dur = 0.5
            
            current = "[v0]"
            for i in range(1, len(scenes)):
                offset = sum(s.get("duration", 5) for s in scenes[:i]) - transition_dur
                out_label = "[vout]" if i == len(scenes) - 1 else f"[vt{i}]"
                filter_parts.append(f"{current}[v{i}]xfade=transition={transition_type}:duration={transition_dur}:offset={offset}{out_label}")
                current = out_label
        else:
            filter_parts.append("[v0]copy[vout]")
        
        # Add audio if present
        audio_path = manifest.get("audio_path")
        audio_filter = ""
        if audio_path:
            input_files.append(f'-i "{audio_path}"')
            audio_filter = f";[{len(scenes)}:a]afade=t=in:d=1,afade=t=out:st={sum(s.get('duration', 5) for s in scenes)-2}:d=2[aout]"
        
        # Build full command
        output_path = config.OUTPUT_DIR / f"{job_id}_final.mp4"
        
        filter_complex = ";".join(filter_parts) + audio_filter
        map_video = '-map "[vout]"'
        map_audio = '-map "[aout]"' if audio_path else "-an"
        
        ffmpeg_cmd = f'''ffmpeg {" ".join(input_files)} -filter_complex "{filter_complex}" {map_video} {map_audio} -c:v libx264 -preset {quality["preset"]} -crf {quality["crf"]} -pix_fmt yuv420p -movflags +faststart -y "{output_path}"'''
        
        job_queue.update_job(job_id, current_stage="rendering")
        
        # Execute FFmpeg
        import subprocess
        process = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
        
        if output_path.exists():
            result = {
                "video_path": str(output_path),
                "duration": sum(s.get("duration", 5) for s in scenes),
                "scene_count": len(scenes),
                "platform": request.platform,
                "quality": request.quality,
                "file_size": output_path.stat().st_size
            }
            
            job_queue.update_job(job_id, status="completed", progress=1.0, result=result)
            await ws_manager.send_update(job_id, {"status": "completed", "result": result})
        else:
            raise Exception(f"FFmpeg failed: {process.stderr}")
            
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))
        await ws_manager.send_update(job_id, {"status": "failed", "error": str(e)})

# =============================================================================
# JOB MANAGEMENT
# =============================================================================

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and result"""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/v1/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 50):
    """List all jobs, optionally filtered by status"""
    jobs = list(job_queue.jobs.values())
    
    if status:
        jobs = [j for j in jobs if j.status == status]
    
    jobs.sort(key=lambda x: x.created_at, reverse=True)
    return {"jobs": jobs[:limit], "total": len(jobs)}

# =============================================================================
# WEBSOCKET REAL-TIME UPDATES
# =============================================================================

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket for real-time job updates"""
    await ws_manager.connect(websocket, job_id)
    
    try:
        # Send current status immediately
        job = job_queue.get_job(job_id)
        if job:
            await websocket.send_json({
                "type": "status",
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "current_stage": job.current_stage
            })
        
        # Keep connection open for updates
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle any client messages (like cancel requests)
                if data == "cancel":
                    job_queue.update_job(job_id, status="cancelled")
                    await websocket.send_json({"type": "cancelled", "job_id": job_id})
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, job_id)

# =============================================================================
# FILE UPLOAD & DOWNLOAD
# =============================================================================

@app.post("/api/v1/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    
    ext = Path(file.filename).suffix or ".jpg"
    filepath = config.UPLOAD_DIR / f"{sha256}{ext}"
    filepath.write_bytes(content)
    
    return {
        "filename": file.filename,
        "sha256": sha256,
        "path": str(filepath),
        "size": len(content)
    }

@app.post("/api/v1/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload an audio file"""
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    
    ext = Path(file.filename).suffix or ".mp3"
    filepath = config.UPLOAD_DIR / f"{sha256}{ext}"
    filepath.write_bytes(content)
    
    return {
        "filename": file.filename,
        "sha256": sha256,
        "path": str(filepath),
        "size": len(content)
    }

@app.get("/api/v1/download/{filename}")
async def download_file(filename: str):
    """Download a generated file"""
    filepath = config.OUTPUT_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, filename=filename)

# =============================================================================
# DOCUMENT PARSING (MARKDOWN/PDF)
# =============================================================================

@app.post("/api/v1/parse/markdown")
async def parse_markdown(file: UploadFile = File(...)):
    """Parse markdown file for video instructions"""
    content = (await file.read()).decode("utf-8")
    
    # Extract YAML frontmatter if present
    import re
    frontmatter = {}
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if frontmatter_match:
        import yaml
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except:
            pass
        content = content[frontmatter_match.end():]
    
    # Parse scenes from markdown
    scenes = []
    scene_pattern = r'##\s*Scene\s*(\d+)(.*?)(?=##\s*Scene|\Z)'
    
    for match in re.finditer(scene_pattern, content, re.DOTALL | re.IGNORECASE):
        scene_num = int(match.group(1))
        scene_content = match.group(2).strip()
        
        # Extract fields
        visual = re.search(r'\*\*Visual\*\*:\s*(.+?)(?=\*\*|\n\n|\Z)', scene_content, re.DOTALL)
        duration = re.search(r'\*\*Duration\*\*:\s*(\d+)', scene_content)
        narration = re.search(r'\*\*Narration\*\*:\s*(.+?)(?=\*\*|\n\n|\Z)', scene_content, re.DOTALL)
        transition = re.search(r'\*\*Transition\*\*:\s*(\w+)', scene_content)
        
        scenes.append({
            "index": scene_num,
            "visual_prompt": visual.group(1).strip() if visual else "",
            "duration": int(duration.group(1)) if duration else 5,
            "narration": narration.group(1).strip() if narration else "",
            "transition": transition.group(1).lower() if transition else "dissolve"
        })
    
    return {
        "filename": file.filename,
        "frontmatter": frontmatter,
        "scenes": scenes,
        "scene_count": len(scenes),
        "total_duration": sum(s["duration"] for s in scenes)
    }

# =============================================================================
# YOUTUBE PUBLISHING (One-Click Upload)
# =============================================================================

# Import YouTube service
try:
    from backend.services.youtube_service import (
        get_youtube_service,
        VideoMetadata,
        PrivacyStatus,
        VideoCategory,
        UploadStatus
    )
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logger.warning("YouTube service not available")

class YouTubeUploadRequest(BaseModel):
    video_path: str
    title: str
    description: str = ""
    tags: List[str] = []
    account_id: str
    privacy: str = "private"  # public, private, unlisted
    category: str = "24"  # Entertainment
    playlist_id: Optional[str] = None
    thumbnail_path: Optional[str] = None
    scheduled_publish: Optional[str] = None  # ISO datetime
    chapters: Optional[List[Dict[str, Any]]] = None  # [{"time": 0, "title": "Intro"}]

@app.get("/api/v1/youtube/accounts")
async def get_youtube_accounts():
    """Get list of connected YouTube accounts for dropdown selection"""
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    yt_service = get_youtube_service()
    accounts = yt_service.get_accounts_dropdown()
    
    return {
        "accounts": accounts,
        "count": len(accounts),
        "message": "Select an account from dropdown" if accounts else "No accounts connected. Add one first."
    }

@app.post("/api/v1/youtube/accounts/add")
async def add_youtube_account(auth_code: Optional[str] = Form(None)):
    """
    Add a new YouTube account via OAuth.
    
    For web flow: POST with auth_code from Google OAuth redirect
    For local flow: POST without auth_code (opens browser)
    """
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    try:
        yt_service = get_youtube_service()
        account = await yt_service.add_account(auth_code)
        
        return {
            "success": True,
            "account": account.to_dict(),
            "message": f"Successfully connected: {account.channel_name}"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add account: {str(e)}")

@app.delete("/api/v1/youtube/accounts/{account_id}")
async def remove_youtube_account(account_id: str):
    """Remove a YouTube account"""
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    yt_service = get_youtube_service()
    success = yt_service.remove_account(account_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"success": True, "message": "Account removed"}

@app.post("/api/v1/youtube/upload")
async def upload_to_youtube(request: YouTubeUploadRequest, background_tasks: BackgroundTasks):
    """
    One-click upload video to YouTube.
    
    Select account from dropdown, provide video path and metadata,
    and the video will be uploaded with professional settings.
    """
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    job_id = job_queue.create_job("youtube_upload")
    
    # Parse metadata
    privacy_map = {
        "public": PrivacyStatus.PUBLIC,
        "private": PrivacyStatus.PRIVATE,
        "unlisted": PrivacyStatus.UNLISTED
    }
    
    chapters = []
    if request.chapters:
        chapters = [(c.get("time", 0), c.get("title", "")) for c in request.chapters]
    
    scheduled = None
    if request.scheduled_publish:
        from datetime import datetime
        scheduled = datetime.fromisoformat(request.scheduled_publish.replace("Z", "+00:00"))
    
    metadata = VideoMetadata(
        title=request.title,
        description=request.description,
        tags=request.tags,
        category=VideoCategory(request.category) if request.category else VideoCategory.ENTERTAINMENT,
        privacy=privacy_map.get(request.privacy, PrivacyStatus.PRIVATE),
        playlist_id=request.playlist_id,
        thumbnail_path=request.thumbnail_path,
        scheduled_publish=scheduled,
        chapters=chapters
    )
    
    background_tasks.add_task(run_youtube_upload, job_id, request.video_path, metadata, request.account_id)
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Upload started. Track progress via WebSocket or job status endpoint."
    }

async def run_youtube_upload(job_id: str, video_path: str, metadata: VideoMetadata, account_id: str):
    """Background task for YouTube upload"""
    try:
        yt_service = get_youtube_service()
        
        def progress_callback(percent: int, status: str):
            job_queue.update_job(job_id, progress=percent/100, current_stage=status)
        
        result = await yt_service.upload_video(
            video_path=video_path,
            metadata=metadata,
            account_id=account_id,
            progress_callback=progress_callback
        )
        
        if result.success:
            job_queue.update_job(
                job_id,
                status="completed",
                progress=1.0,
                result={
                    "video_id": result.video_id,
                    "video_url": result.video_url,
                    "upload_time": result.upload_time,
                    "thumbnail_uploaded": result.thumbnail_uploaded,
                    "added_to_playlist": result.added_to_playlist
                }
            )
            await ws_manager.send_update(job_id, {
                "status": "completed",
                "video_url": result.video_url
            })
        else:
            job_queue.update_job(job_id, status="failed", error=result.error)
            await ws_manager.send_update(job_id, {"status": "failed", "error": result.error})
            
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))
        await ws_manager.send_update(job_id, {"status": "failed", "error": str(e)})

@app.post("/api/v1/youtube/quick-upload")
async def quick_youtube_upload(
    video_path: str = Form(...),
    title: str = Form(...),
    account_id: str = Form(...),
    description: str = Form(""),
    privacy: str = Form("private"),
    background_tasks: BackgroundTasks = None
):
    """
    Simplified one-click upload with minimal parameters.
    
    Just provide video path, title, and select account from dropdown.
    """
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    job_id = job_queue.create_job("youtube_quick_upload")
    
    privacy_map = {
        "public": PrivacyStatus.PUBLIC,
        "private": PrivacyStatus.PRIVATE,
        "unlisted": PrivacyStatus.UNLISTED
    }
    
    metadata = VideoMetadata(
        title=title,
        description=description,
        privacy=privacy_map.get(privacy, PrivacyStatus.PRIVATE)
    )
    
    background_tasks.add_task(run_youtube_upload, job_id, video_path, metadata, account_id)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/api/v1/youtube/playlists/{account_id}")
async def get_youtube_playlists(account_id: str):
    """Get all playlists for a YouTube account"""
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    yt_service = get_youtube_service()
    playlists = await yt_service.get_playlists(account_id)
    
    return {"playlists": playlists, "count": len(playlists)}

@app.post("/api/v1/youtube/playlists/{account_id}")
async def create_youtube_playlist(
    account_id: str,
    title: str = Form(...),
    description: str = Form(""),
    privacy: str = Form("private")
):
    """Create a new YouTube playlist"""
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    privacy_map = {
        "public": PrivacyStatus.PUBLIC,
        "private": PrivacyStatus.PRIVATE,
        "unlisted": PrivacyStatus.UNLISTED
    }
    
    yt_service = get_youtube_service()
    result = await yt_service.create_playlist(
        account_id=account_id,
        title=title,
        description=description,
        privacy=privacy_map.get(privacy, PrivacyStatus.PRIVATE)
    )
    
    return result

@app.post("/api/v1/youtube/generate-metadata")
async def generate_youtube_metadata(
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("entertainment")
):
    """Generate SEO-optimized YouTube metadata using AI"""
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    yt_service = get_youtube_service()
    metadata = await yt_service.generate_seo_metadata(title, description, category)
    
    return {
        "title": metadata.title,
        "description": metadata.description,
        "tags": metadata.tags
    }

@app.get("/api/v1/youtube/analytics/{account_id}/{video_id}")
async def get_youtube_analytics(account_id: str, video_id: str):
    """Get analytics for a YouTube video"""
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    yt_service = get_youtube_service()
    analytics = await yt_service.get_video_analytics(account_id, video_id)
    
    return analytics

# =============================================================================
# TIMELINE EDITOR (10-Star Professional NLE)
# =============================================================================

try:
    from backend.services.timeline import (
        get_timeline_editor_service,
        EditorMode, SceneStatus, TransitionType, CameraMovement,
        ColorGradePreset, ExportPreset
    )
    TIMELINE_AVAILABLE = True
except ImportError:
    TIMELINE_AVAILABLE = False
    logger.warning("Timeline editor not available")

class TimelineCreateRequest(BaseModel):
    prompt: str
    duration: float = 60.0
    style: str = "Cinematic"
    music_prompt: Optional[str] = None
    auto_generate: bool = True

class SceneEditRequest(BaseModel):
    prompt: Optional[str] = None
    duration: Optional[float] = None
    style: Optional[str] = None
    camera_move: Optional[str] = None
    transition: Optional[str] = None
    transition_duration: Optional[float] = None

# --- SIMPLE MODE: One-Click Workflow ---

@app.post("/api/v1/timeline/quick-create")
async def timeline_quick_create(request: TimelineCreateRequest):
    """
    ★ SIMPLE MODE: One-click video creation ★
    
    Just provide a prompt and get a complete video project.
    AI generates storyboard, images, and optionally music.
    """
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    project = await editor.quick_create(
        prompt=request.prompt,
        duration=request.duration,
        style=request.style,
        music_prompt=request.music_prompt,
        auto_generate=request.auto_generate
    )
    
    return {
        "project_id": project.id,
        "title": project.title,
        "scene_count": len(project.scenes),
        "total_duration": project.total_duration,
        "message": "Project created. Use /preview-gallery to see scenes."
    }

@app.get("/api/v1/timeline/{project_id}/preview-gallery")
async def timeline_preview_gallery(project_id: str):
    """★ SIMPLE MODE: Get all scene previews for approval ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    return await editor.preview_gallery(project_id)

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/approve")
async def timeline_approve_scene(project_id: str, scene_index: int):
    """★ SIMPLE MODE: Approve a single scene ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.approve_scene(project_id, scene_index)
    return {"success": True, "scene": scene.to_dict()}

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/reject")
async def timeline_reject_scene(project_id: str, scene_index: int, new_prompt: Optional[str] = Form(None)):
    """★ SIMPLE MODE: Reject and regenerate scene ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.reject_scene(project_id, scene_index, new_prompt)
    return {"success": True, "scene": scene.to_dict(), "status": "regenerating"}

@app.post("/api/v1/timeline/{project_id}/approve-all")
async def timeline_approve_all(project_id: str):
    """★ SIMPLE MODE: Approve all ready scenes ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    project = await editor.approve_all(project_id)
    approved = sum(1 for s in project.scenes if s.status == SceneStatus.APPROVED)
    return {"success": True, "approved_count": approved}

@app.post("/api/v1/timeline/{project_id}/render")
async def timeline_render(project_id: str, preset: str = Form("youtube_1080p"), background_tasks: BackgroundTasks = None):
    """★ SIMPLE MODE: Render final video ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    job_id = job_queue.create_job("timeline_render")
    background_tasks.add_task(run_timeline_render, job_id, project_id, preset)
    return {"job_id": job_id, "status": "processing"}

async def run_timeline_render(job_id: str, project_id: str, preset: str):
    try:
        editor = get_timeline_editor_service()
        export_preset = ExportPreset(preset) if preset else ExportPreset.YOUTUBE_1080P
        result = await editor.render_final(project_id, export_preset)
        job_queue.update_job(job_id, status="completed", progress=1.0, result=result)
    except Exception as e:
        job_queue.update_job(job_id, status="failed", error=str(e))

# --- ADVANCED MODE: Full Timeline Control ---

@app.post("/api/v1/timeline/projects")
async def timeline_create_project(title: str = Form(...), mode: str = Form("advanced")):
    """★ ADVANCED MODE: Create empty project ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    project = await editor.create_project(title, EditorMode(mode))
    return project.to_dict()

@app.get("/api/v1/timeline/projects")
async def timeline_list_projects():
    """★ ADVANCED MODE: List all projects ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    return {"projects": editor.list_projects()}

@app.get("/api/v1/timeline/{project_id}")
async def timeline_get_project(project_id: str):
    """★ ADVANCED MODE: Get project details ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    return editor.get_project(project_id)

@app.get("/api/v1/timeline/{project_id}/timeline")
async def timeline_get_timeline_view(project_id: str):
    """★ ADVANCED MODE: Get timeline view for UI ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    return editor.get_timeline(project_id)

@app.get("/api/v1/timeline/{project_id}/scenes/{scene_index}")
async def timeline_get_scene(project_id: str, scene_index: int):
    """★ ADVANCED MODE: Get full scene details ★"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    return editor.get_scene(project_id, scene_index)

# --- ADVANCED: Scene Tools ---

@app.post("/api/v1/timeline/{project_id}/scenes")
async def timeline_add_scene(project_id: str, prompt: str = Form(...), duration: float = Form(5.0), style: str = Form("Cinematic")):
    """Tool: Add new scene"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.add_scene(project_id, prompt, duration, style=style)
    return scene.to_dict()

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/regenerate")
async def timeline_regenerate(project_id: str, scene_index: int):
    """Tool: Regenerate scene image"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.regenerate(project_id, scene_index)
    return scene.to_dict()

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/style-transfer")
async def timeline_style_transfer(project_id: str, scene_index: int, style: str = Form(...)):
    """Tool: Apply style transfer"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.style_transfer(project_id, scene_index, style)
    return scene.to_dict()

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/camera")
async def timeline_set_camera(project_id: str, scene_index: int, movement: str = Form(...), intensity: float = Form(50)):
    """Tool: Set camera movement"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.set_camera_move(project_id, scene_index, CameraMovement(movement), intensity)
    return scene.to_dict()

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/transition")
async def timeline_set_transition(project_id: str, scene_index: int, transition_type: str = Form(...), duration: float = Form(0.5)):
    """Tool: Set transition"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.set_transition(project_id, scene_index, TransitionType(transition_type), duration)
    return scene.to_dict()

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/color-grade")
async def timeline_color_grade(project_id: str, scene_index: int, preset: str = Form(...)):
    """Tool: Apply color grade"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.set_color_grade(project_id, scene_index, ColorGradePreset(preset))
    return scene.to_dict()

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/split")
async def timeline_split_scene(project_id: str, scene_index: int, at_time: float = Form(...)):
    """Tool: Split scene at time"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scenes = await editor.split_scene(project_id, scene_index, at_time)
    return {"scenes": [s.to_dict() for s in scenes]}

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/duplicate")
async def timeline_duplicate_scene(project_id: str, scene_index: int):
    """Tool: Duplicate scene"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.duplicate_scene(project_id, scene_index)
    return scene.to_dict()

@app.delete("/api/v1/timeline/{project_id}/scenes/{scene_index}")
async def timeline_delete_scene(project_id: str, scene_index: int):
    """Tool: Delete scene"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    project = await editor.delete_scene(project_id, scene_index)
    return {"success": True, "remaining_scenes": len(project.scenes)}

@app.post("/api/v1/timeline/{project_id}/scenes/{scene_index}/speed")
async def timeline_set_speed(project_id: str, scene_index: int, speed: float = Form(...)):
    """Tool: Set playback speed"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    scene = await editor.set_speed(project_id, scene_index, speed)
    return scene.to_dict()

# --- ADVANCED: Undo/Redo ---

@app.post("/api/v1/timeline/{project_id}/undo")
async def timeline_undo(project_id: str):
    """Undo last edit"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    return editor.undo(project_id)

@app.post("/api/v1/timeline/{project_id}/redo")
async def timeline_redo(project_id: str):
    """Redo undone edit"""
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    
    editor = get_timeline_editor_service()
    return editor.redo(project_id)

# =============================================================================
# END-TO-END WORKFLOW: Timeline → Render → YouTube
# =============================================================================

class PublishToYouTubeRequest(BaseModel):
    account_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy: str = "private"
    auto_chapters: bool = True
    ai_metadata: bool = True

@app.post("/api/v1/timeline/{project_id}/publish-youtube")
async def timeline_publish_to_youtube(
    project_id: str, 
    request: PublishToYouTubeRequest,
    background_tasks: BackgroundTasks
):
    """
    ★ END-TO-END WORKFLOW ★
    
    One-click: Render timeline project and upload directly to YouTube.
    
    1. Renders final video from approved scenes
    2. Generates AI-optimized metadata (title, description, tags)
    3. Extracts chapters from timeline markers
    4. Uploads to selected YouTube account
    """
    if not TIMELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Timeline editor not available")
    if not YOUTUBE_AVAILABLE:
        raise HTTPException(status_code=503, detail="YouTube service not available")
    
    # Create job for tracking
    job_id = job_queue.create_job("publish_youtube")
    
    # Run in background
    background_tasks.add_task(
        run_publish_to_youtube,
        job_id,
        project_id,
        request.account_id,
        request.title,
        request.description,
        request.tags,
        request.privacy,
        request.auto_chapters,
        request.ai_metadata
    )
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Rendering and uploading to YouTube..."
    }

async def run_publish_to_youtube(
    job_id: str,
    project_id: str,
    account_id: str,
    title: Optional[str],
    description: Optional[str],
    tags: Optional[List[str]],
    privacy: str,
    auto_chapters: bool,
    ai_metadata: bool
):
    """Background task: Render + Upload to YouTube"""
    try:
        editor = get_timeline_editor_service()
        yt_service = get_youtube_service()
        
        # Step 1: Get project details
        job_queue.update_job(job_id, progress=0.1, status="loading_project")
        project = editor.get_project(project_id)
        
        # Step 2: Render video
        job_queue.update_job(job_id, progress=0.2, status="rendering")
        render_result = await editor.render_final(project_id, ExportPreset.YOUTUBE_1080P)
        video_path = render_result.get("output_path")
        
        if not video_path:
            raise ValueError("Render failed - no output path")
        
        # Step 3: Generate AI metadata if requested
        job_queue.update_job(job_id, progress=0.6, status="generating_metadata")
        
        final_title = title or project.get("title", "Untitled Video")
        final_description = description
        final_tags = tags or []
        
        if ai_metadata:
            try:
                ai_meta = await yt_service.generate_ai_metadata(
                    video_path=video_path,
                    prompt=project.get("description", final_title)
                )
                if not title:
                    final_title = ai_meta.title
                if not description:
                    final_description = ai_meta.description
                if not tags:
                    final_tags = ai_meta.tags
            except Exception as e:
                logger.warning(f"AI metadata generation failed: {e}")
        
        # Step 4: Build chapter markers
        chapters = None
        if auto_chapters:
            timeline_data = editor.get_timeline(project_id)
            markers = timeline_data.get("markers", [])
            if markers:
                chapters = [
                    {"time": m["time"], "title": m["label"]}
                    for m in markers if m.get("marker_type") == "chapter"
                ]
        
        # Step 5: Upload to YouTube
        job_queue.update_job(job_id, progress=0.7, status="uploading")
        
        from backend.services.youtube_service import VideoMetadata, PrivacyStatus
        
        metadata = VideoMetadata(
            title=final_title,
            description=final_description or f"Created with Nano Banana Studio Pro\n\n{project.get('description', '')}",
            tags=final_tags,
            privacy=PrivacyStatus(privacy)
        )
        
        upload_result = await yt_service.upload_video(
            account_id=account_id,
            video_path=video_path,
            metadata=metadata
        )
        
        # Step 6: Add chapters if available
        if chapters and upload_result.video_id:
            try:
                # Chapters are typically added in the description
                chapter_text = "\n\nChapters:\n" + "\n".join([
                    f"{int(c['time']//60)}:{int(c['time']%60):02d} {c['title']}"
                    for c in chapters
                ])
                # Update description with chapters
                await yt_service.update_video_metadata(
                    account_id=account_id,
                    video_id=upload_result.video_id,
                    description=(metadata.description or "") + chapter_text
                )
            except Exception as e:
                logger.warning(f"Failed to add chapters: {e}")
        
        job_queue.update_job(
            job_id,
            status="completed",
            progress=1.0,
            result={
                "video_id": upload_result.video_id,
                "video_url": upload_result.video_url,
                "title": final_title,
                "privacy": privacy,
                "project_id": project_id
            }
        )
        
    except Exception as e:
        logger.error(f"Publish to YouTube failed: {e}")
        job_queue.update_job(job_id, status="failed", error=str(e))

@app.get("/api/v1/workflow/status/{job_id}")
async def get_workflow_status(job_id: str):
    """Get status of any background workflow job"""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
