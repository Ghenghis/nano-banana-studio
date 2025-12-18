"""
Nano Banana Studio Pro - Storyboard Service
=============================================
LLM-driven storyboard generation from lyrics, prompts, or documents.

Features:
- Lyrics-to-scenes conversion with beat synchronization
- Multi-LLM fallback (LM Studio -> Ollama -> OpenAI)
- Style-aware prompt generation
- Automatic scene timing based on audio analysis
- Template-based generation
- Scene sequencing optimization

Dependencies:
    pip install httpx pydantic pyyaml
"""

import os
import json
import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import httpx
from pydantic import BaseModel, Field
import yaml

logger = logging.getLogger("storyboard-service")


# =============================================================================
# CONFIGURATION
# =============================================================================

class StoryboardConfig:
    """Storyboard service configuration"""
    LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_URL = "https://api.openai.com/v1"
    
    TEMPLATES_DIR = Path(os.getenv("TEMPLATES_DIR", "/app/templates"))
    CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/app/config"))
    CACHE_DIR = Path(os.getenv("CACHE_DIR", "/app/data/cache/storyboards"))
    
    DEFAULT_SCENE_DURATION = float(os.getenv("DEFAULT_SCENE_DURATION", "5.0"))
    DEFAULT_TRANSITION = os.getenv("DEFAULT_TRANSITION", "dissolve")
    MAX_SCENES_PER_MINUTE = int(os.getenv("MAX_SCENES_PER_MINUTE", "12"))
    MIN_SCENE_DURATION = float(os.getenv("MIN_SCENE_DURATION", "2.0"))


# =============================================================================
# ENUMS
# =============================================================================

class SceneType(str, Enum):
    ESTABLISHING = "establishing"
    NARRATIVE = "narrative"
    ACTION = "action"
    EMOTIONAL = "emotional"
    TRANSITION = "transition"
    MONTAGE = "montage"
    CLOSEUP = "closeup"
    WIDE = "wide"


class CameraMove(str, Enum):
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACKING = "tracking"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"


class TransitionType(str, Enum):
    CUT = "cut"
    DISSOLVE = "dissolve"
    FADE_BLACK = "fadeblack"
    FADE_WHITE = "fadewhite"
    WIPE_LEFT = "wipeleft"
    WIPE_RIGHT = "wiperight"
    ZOOM_IN = "zoomin"
    ZOOM_OUT = "circleopen"
    PIXELIZE = "pixelize"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Scene:
    """Individual scene in storyboard"""
    index: int
    visual_prompt: str
    duration: float
    scene_type: SceneType = SceneType.NARRATIVE
    camera_move: CameraMove = CameraMove.STATIC
    transition_in: TransitionType = TransitionType.DISSOLVE
    transition_out: TransitionType = TransitionType.DISSOLVE
    transition_duration: float = 0.5
    
    narration: Optional[str] = None
    lyrics_segment: Optional[str] = None
    dialogue: Optional[str] = None
    
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    beat_sync: bool = False
    
    style_keywords: List[str] = field(default_factory=list)
    color_palette: Optional[str] = None
    lighting: Optional[str] = None
    mood: Optional[str] = None
    
    aspect_ratio: str = "16:9"
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    
    character_ids: List[str] = field(default_factory=list)
    reference_images: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "visual_prompt": self.visual_prompt,
            "duration": self.duration,
            "scene_type": self.scene_type.value if isinstance(self.scene_type, SceneType) else self.scene_type,
            "camera_move": self.camera_move.value if isinstance(self.camera_move, CameraMove) else self.camera_move,
            "transition_in": self.transition_in.value if isinstance(self.transition_in, TransitionType) else self.transition_in,
            "transition_out": self.transition_out.value if isinstance(self.transition_out, TransitionType) else self.transition_out,
            "transition_duration": self.transition_duration,
            "narration": self.narration,
            "lyrics_segment": self.lyrics_segment,
            "dialogue": self.dialogue,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "beat_sync": self.beat_sync,
            "style_keywords": self.style_keywords,
            "color_palette": self.color_palette,
            "lighting": self.lighting,
            "mood": self.mood,
            "aspect_ratio": self.aspect_ratio,
            "negative_prompt": self.negative_prompt,
            "seed": self.seed,
            "character_ids": self.character_ids,
            "reference_images": self.reference_images
        }


@dataclass
class Storyboard:
    """Complete storyboard with metadata"""
    id: str
    title: str
    scenes: List[Scene]
    total_duration: float
    
    global_style: str = "Cinematic"
    color_grading: Optional[str] = None
    aspect_ratio: str = "16:9"
    
    audio_path: Optional[str] = None
    bpm: Optional[float] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    source_type: str = "prompt"
    source_content: Optional[str] = None
    
    characters: Dict[str, Dict] = field(default_factory=dict)
    
    @property
    def scene_count(self) -> int:
        return len(self.scenes)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "scenes": [s.to_dict() for s in self.scenes],
            "total_duration": self.total_duration,
            "scene_count": self.scene_count,
            "global_style": self.global_style,
            "color_grading": self.color_grading,
            "aspect_ratio": self.aspect_ratio,
            "audio_path": self.audio_path,
            "bpm": self.bpm,
            "created_at": self.created_at.isoformat(),
            "source_type": self.source_type,
            "characters": self.characters
        }


class StoryboardRequest(BaseModel):
    """Request for storyboard generation"""
    prompt: Optional[str] = None
    lyrics: Optional[str] = None
    document_path: Optional[str] = None
    audio_analysis: Optional[Dict[str, Any]] = None
    target_duration: Optional[float] = None
    scene_count: Optional[int] = None
    style: str = "Cinematic"
    mood: Optional[str] = None
    color_palette: Optional[str] = None
    platform: str = "YouTube (16:9)"
    aspect_ratio: str = "16:9"
    character_ids: List[str] = Field(default_factory=list)
    template_name: Optional[str] = None
    custom_instructions: Optional[str] = None


# =============================================================================
# LLM CLIENT
# =============================================================================

class LLMClient:
    """Multi-provider LLM client with fallback"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=120.0)
        self._provider_order = ["lm_studio", "ollama", "openai"]
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        provider: str = "auto",
        response_format: Optional[Dict] = None
    ) -> str:
        """Get completion from LLM with automatic fallback"""
        providers = []
        
        if provider == "auto":
            if StoryboardConfig.LM_STUDIO_URL:
                providers.append(("lm_studio", StoryboardConfig.LM_STUDIO_URL, None))
            if StoryboardConfig.OLLAMA_URL:
                providers.append(("ollama", f"{StoryboardConfig.OLLAMA_URL}/v1", None))
            if StoryboardConfig.OPENAI_API_KEY:
                providers.append(("openai", StoryboardConfig.OPENAI_URL, StoryboardConfig.OPENAI_API_KEY))
        else:
            if provider == "lm_studio":
                providers.append(("lm_studio", StoryboardConfig.LM_STUDIO_URL, None))
            elif provider == "ollama":
                providers.append(("ollama", f"{StoryboardConfig.OLLAMA_URL}/v1", None))
            elif provider == "openai":
                providers.append(("openai", StoryboardConfig.OPENAI_URL, StoryboardConfig.OPENAI_API_KEY))
        
        last_error = None
        for prov_name, base_url, api_key in providers:
            try:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                if model is None:
                    if prov_name == "openai":
                        model = "gpt-4o-mini"
                    elif prov_name == "ollama":
                        model = "llama3.2"
                    else:
                        model = "local-model"
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                if response_format:
                    payload["response_format"] = response_format
                
                response = await self.http_client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {prov_name} failed: {e}")
                continue
        
        raise Exception(f"All LLM providers failed. Last error: {last_error}")
    
    async def close(self):
        await self.http_client.aclose()


# =============================================================================
# STORYBOARD SERVICE
# =============================================================================

class StoryboardService:
    """
    Enterprise-grade storyboard generation service.
    Converts prompts, lyrics, or documents into detailed visual storyboards.
    """
    
    def __init__(self):
        self.llm = LLMClient()
        self.config = StoryboardConfig()
        self._styles_cache: Optional[Dict] = None
        self._transitions_cache: Optional[Dict] = None
        StoryboardConfig.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    async def _load_styles(self) -> Dict:
        """Load style definitions from config"""
        if self._styles_cache:
            return self._styles_cache
        
        styles_path = StoryboardConfig.CONFIG_DIR / "styles.yaml"
        if styles_path.exists():
            self._styles_cache = yaml.safe_load(styles_path.read_text())
        else:
            self._styles_cache = {"styles": {}}
        return self._styles_cache
    
    async def _load_transitions(self) -> Dict:
        """Load transition definitions from config"""
        if self._transitions_cache:
            return self._transitions_cache
        
        transitions_path = StoryboardConfig.CONFIG_DIR / "transitions.yaml"
        if transitions_path.exists():
            self._transitions_cache = yaml.safe_load(transitions_path.read_text())
        else:
            self._transitions_cache = {"transitions": {}}
        return self._transitions_cache
    
    def _generate_storyboard_id(self, content: str) -> str:
        """Generate unique storyboard ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"sb_{timestamp}_{content_hash}"
    
    def _parse_lyrics_sections(self, lyrics: str) -> List[Dict[str, Any]]:
        """Parse lyrics into sections (verses, choruses, bridges)"""
        sections = []
        section_patterns = [
            (r'\[(?:Verse|V)\s*\d*\]', 'verse'),
            (r'\[(?:Chorus|C|Hook)\s*\d*\]', 'chorus'),
            (r'\[(?:Bridge|B)\s*\d*\]', 'bridge'),
            (r'\[(?:Pre-?Chorus|PC)\s*\d*\]', 'prechorus'),
            (r'\[(?:Intro|I)\]', 'intro'),
            (r'\[(?:Outro|O)\]', 'outro'),
            (r'\[(?:Instrumental|Inst)\]', 'instrumental'),
        ]
        
        lines = lyrics.strip().split('\n')
        current_section = {'type': 'verse', 'lines': [], 'index': 0}
        section_index = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            found_section = False
            for pattern, section_type in section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    if current_section['lines']:
                        sections.append(current_section)
                        section_index += 1
                    current_section = {'type': section_type, 'lines': [], 'index': section_index}
                    found_section = True
                    break
            
            if not found_section and line:
                current_section['lines'].append(line)
        
        if current_section['lines']:
            sections.append(current_section)
        
        if not sections:
            sections.append({
                'type': 'verse',
                'lines': [l.strip() for l in lyrics.split('\n') if l.strip()],
                'index': 0
            })
        
        return sections
    
    def _calculate_scene_timings(
        self,
        scenes: List[Scene],
        audio_analysis: Optional[Dict],
        target_duration: float
    ) -> List[Scene]:
        """Calculate and apply scene timings based on audio analysis"""
        if not scenes:
            return scenes
        
        beats = audio_analysis.get("beats", []) if audio_analysis else []
        bpm = audio_analysis.get("bpm", 120) if audio_analysis else 120
        base_duration = target_duration / len(scenes)
        min_dur = StoryboardConfig.MIN_SCENE_DURATION
        
        cumulative_time = 0.0
        for i, scene in enumerate(scenes):
            scene.start_time = cumulative_time
            
            if beats and scene.beat_sync:
                target_end = cumulative_time + base_duration
                nearest_beat = min(beats, key=lambda b: abs(b - target_end)) if beats else target_end
                if abs(nearest_beat - target_end) < 1.0:
                    scene.duration = max(min_dur, nearest_beat - cumulative_time)
                else:
                    scene.duration = max(min_dur, base_duration)
            else:
                scene.duration = max(min_dur, base_duration)
            
            scene.end_time = cumulative_time + scene.duration
            cumulative_time = scene.end_time - scene.transition_duration
        
        return scenes

    
    def _generate_fallback_scenes(self, prompt: str, scene_count: int, style: str) -> Dict:
        """Generate fallback scenes when LLM fails"""
        return {
            "title": f"Storyboard: {prompt[:30]}...",
            "scenes": [
                {
                    "index": i + 1,
                    "visual_prompt": f"Scene {i+1}: {prompt}. {style} style, cinematic composition.",
                    "scene_type": "narrative",
                    "camera_move": ["static", "zoom_in", "pan_left", "pan_right"][i % 4],
                    "mood": "dramatic",
                    "lighting": "cinematic"
                }
                for i in range(scene_count)
            ]
        }
    
    async def generate_from_prompt(
        self,
        prompt: str,
        style: str = "Cinematic",
        duration: float = 60.0,
        scene_count: Optional[int] = None,
        audio_analysis: Optional[Dict] = None,
        character_ids: List[str] = None,
        custom_instructions: Optional[str] = None
    ) -> Storyboard:
        """Generate storyboard from a text prompt"""
        logger.info(f"Generating storyboard from prompt: {prompt[:50]}...")
        
        if scene_count is None:
            max_scenes = int(duration / 60 * StoryboardConfig.MAX_SCENES_PER_MINUTE)
            scene_count = min(max_scenes, max(3, int(duration / StoryboardConfig.DEFAULT_SCENE_DURATION)))
        
        styles = await self._load_styles()
        style_config = styles.get("styles", {}).get(style.lower(), {})
        
        system_prompt = f"""You are an expert visual storyteller. Generate a storyboard with exactly {scene_count} scenes.

STYLE: {style}
{f'STYLE KEYWORDS: {", ".join(style_config.get("keywords", []))}' if style_config else ''}

For each scene provide:
1. Visual prompt (detailed cinematic description for AI image generation)
2. Scene type (establishing, narrative, action, emotional, transition, montage, closeup, wide)
3. Camera movement (static, pan_left, pan_right, tilt_up, tilt_down, zoom_in, zoom_out, tracking)
4. Mood and lighting
5. Color palette suggestion

{f'ADDITIONAL INSTRUCTIONS: {custom_instructions}' if custom_instructions else ''}

Return ONLY valid JSON:
{{"title": "Title", "scenes": [{{"index": 1, "visual_prompt": "...", "scene_type": "establishing", "camera_move": "zoom_in", "mood": "dramatic", "lighting": "golden hour", "color_palette": "warm"}}]}}"""
        
        user_prompt = f"Create a {scene_count}-scene storyboard for: {prompt}"
        
        response = await self.llm.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=4000
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            data = self._generate_fallback_scenes(prompt, scene_count, style)
        
        scenes = []
        for i, scene_data in enumerate(data.get("scenes", [])):
            scene = Scene(
                index=i + 1,
                visual_prompt=scene_data.get("visual_prompt", f"Scene {i+1} of {prompt}"),
                duration=duration / scene_count,
                scene_type=SceneType(scene_data.get("scene_type", "narrative")),
                camera_move=CameraMove(scene_data.get("camera_move", "static")),
                mood=scene_data.get("mood"),
                lighting=scene_data.get("lighting"),
                color_palette=scene_data.get("color_palette"),
                style_keywords=style_config.get("keywords", []),
                character_ids=character_ids or [],
                beat_sync=audio_analysis is not None
            )
            scenes.append(scene)
        
        scenes = self._calculate_scene_timings(scenes, audio_analysis, duration)
        
        storyboard = Storyboard(
            id=self._generate_storyboard_id(prompt),
            title=data.get("title", f"Storyboard: {prompt[:30]}..."),
            scenes=scenes,
            total_duration=duration,
            global_style=style,
            bpm=audio_analysis.get("bpm") if audio_analysis else None,
            source_type="prompt",
            source_content=prompt
        )
        
        logger.info(f"Generated storyboard {storyboard.id} with {len(scenes)} scenes")
        return storyboard

    
    async def generate_from_lyrics(
        self,
        lyrics: str,
        style: str = "Cinematic",
        audio_analysis: Optional[Dict] = None,
        character_ids: List[str] = None,
        mood: Optional[str] = None
    ) -> Storyboard:
        """Generate storyboard synchronized to song lyrics"""
        logger.info("Generating storyboard from lyrics...")
        
        sections = self._parse_lyrics_sections(lyrics)
        
        if audio_analysis:
            total_duration = audio_analysis.get("duration", 180.0)
        else:
            total_lines = sum(len(s["lines"]) for s in sections)
            total_duration = total_lines * 3.0
        
        styles = await self._load_styles()
        style_config = styles.get("styles", {}).get(style.lower(), {})
        
        system_prompt = f"""You are an expert music video director. Create visual scenes for song lyrics.

STYLE: {style}
{f'MOOD: {mood}' if mood else ''}

For each lyrics section, create a visual scene that:
1. Captures the emotional content
2. Uses visual metaphors
3. Maintains continuity
4. Matches music energy with camera movement

Return ONLY valid JSON:
{{"title": "Music Video Title", "scenes": [{{"index": 1, "lyrics_segment": "...", "visual_prompt": "...", "scene_type": "narrative", "camera_move": "tracking", "mood": "emotional", "lighting": "soft"}}]}}"""
        
        sections_text = ""
        for i, section in enumerate(sections):
            section_lyrics = "\n".join(section["lines"])
            sections_text += f"\n[{section['type'].upper()} {i+1}]\n{section_lyrics}\n"
        
        user_prompt = f"Create music video scenes for these lyrics:\n{sections_text}"
        
        response = await self.llm.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=4000
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found")
        except json.JSONDecodeError:
            data = {
                "title": "Music Video",
                "scenes": [
                    {
                        "index": i + 1,
                        "lyrics_segment": "\n".join(s["lines"]),
                        "visual_prompt": f"Visual scene for {s['type']}: {s['lines'][0] if s['lines'] else 'instrumental'}"
                    }
                    for i, s in enumerate(sections)
                ]
            }
        
        scenes = []
        duration_per_scene = total_duration / max(len(data.get("scenes", [])), 1)
        
        for i, scene_data in enumerate(data.get("scenes", [])):
            scene = Scene(
                index=i + 1,
                visual_prompt=scene_data.get("visual_prompt", ""),
                duration=duration_per_scene,
                scene_type=SceneType(scene_data.get("scene_type", "narrative")),
                camera_move=CameraMove(scene_data.get("camera_move", "static")),
                lyrics_segment=scene_data.get("lyrics_segment"),
                mood=scene_data.get("mood"),
                lighting=scene_data.get("lighting"),
                style_keywords=style_config.get("keywords", []),
                character_ids=character_ids or [],
                beat_sync=audio_analysis is not None
            )
            scenes.append(scene)
        
        scenes = self._calculate_scene_timings(scenes, audio_analysis, total_duration)
        
        storyboard = Storyboard(
            id=self._generate_storyboard_id(lyrics[:100]),
            title=data.get("title", "Music Video"),
            scenes=scenes,
            total_duration=total_duration,
            global_style=style,
            bpm=audio_analysis.get("bpm") if audio_analysis else None,
            source_type="lyrics",
            source_content=lyrics
        )
        
        logger.info(f"Generated music video storyboard with {len(scenes)} scenes")
        return storyboard
    
    async def generate_from_document(
        self,
        document_path: str,
        style: str = "Cinematic",
        duration: float = 120.0
    ) -> Storyboard:
        """Generate storyboard from markdown or PDF document"""
        logger.info(f"Generating storyboard from document: {document_path}")
        
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        content = ""
        if doc_path.suffix.lower() == ".md":
            content = doc_path.read_text(encoding="utf-8")
        elif doc_path.suffix.lower() == ".pdf":
            try:
                import fitz
                pdf = fitz.open(document_path)
                content = "\n".join(page.get_text() for page in pdf)
                pdf.close()
            except ImportError:
                raise ImportError("PyMuPDF required for PDF processing")
        else:
            content = doc_path.read_text(encoding="utf-8")
        
        return await self.generate_from_prompt(content, style=style, duration=duration)
    
    async def close(self):
        """Close service resources"""
        await self.llm.close()


# =============================================================================
# SINGLETON
# =============================================================================

_storyboard_service: Optional[StoryboardService] = None

def get_storyboard_service() -> StoryboardService:
    """Get or create storyboard service instance"""
    global _storyboard_service
    if _storyboard_service is None:
        _storyboard_service = StoryboardService()
    return _storyboard_service
