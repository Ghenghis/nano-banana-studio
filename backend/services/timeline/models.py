"""
Timeline Editor - Data Models & Enums
=====================================
Complete data structures for 10-star timeline editing.
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


# =============================================================================
# CONFIGURATION
# =============================================================================

class TimelineConfig:
    """Production-grade configuration"""
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/outputs"))
    PREVIEW_DIR = Path(os.getenv("PREVIEW_DIR", "data/previews"))
    PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", "data/projects/timelines"))
    CACHE_DIR = Path(os.getenv("CACHE_DIR", "data/cache/timeline"))
    
    PREVIEW_RESOLUTION = (854, 480)
    STANDARD_RESOLUTION = (1920, 1080)
    UHD_RESOLUTION = (3840, 2160)
    
    DEFAULT_SCENE_DURATION = 5.0
    MIN_SCENE_DURATION = 0.5
    MAX_UNDO_STEPS = 100


# =============================================================================
# ENUMS - Complete option sets
# =============================================================================

class EditorMode(str, Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SceneStatus(str, Enum):
    EMPTY = "empty"
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    APPROVED = "approved"
    LOCKED = "locked"
    ERROR = "error"


class TrackType(str, Enum):
    VIDEO = "video"
    AUDIO_DIALOGUE = "audio_dialogue"
    AUDIO_MUSIC = "audio_music"
    AUDIO_SFX = "audio_sfx"
    AUDIO_AMBIENT = "audio_ambient"
    TEXT = "text"
    SUBTITLE = "subtitle"
    MARKER = "marker"


class TransitionType(str, Enum):
    CUT = "cut"
    DISSOLVE = "dissolve"
    FADE_BLACK = "fade_black"
    FADE_WHITE = "fade_white"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    WIPE_UP = "wipe_up"
    WIPE_DOWN = "wipe_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    PIXELIZE = "pixelize"
    BLUR = "blur"
    GLITCH = "glitch"
    FLASH = "flash"
    CIRCLE_OPEN = "circle_open"
    CIRCLE_CLOSE = "circle_close"
    FILM_BURN = "film_burn"
    LIGHT_LEAK = "light_leak"
    MORPH = "morph"
    WHIP_PAN = "whip_pan"


class CameraMovement(str, Enum):
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACKING_LEFT = "tracking_left"
    TRACKING_RIGHT = "tracking_right"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    ORBIT_LEFT = "orbit_left"
    ORBIT_RIGHT = "orbit_right"
    HANDHELD = "handheld"
    DRONE_RISE = "drone_rise"
    VERTIGO = "vertigo"


class ColorGradePreset(str, Enum):
    NONE = "none"
    CINEMATIC = "cinematic"
    BLOCKBUSTER = "blockbuster"
    FILM_NOIR = "film_noir"
    VINTAGE = "vintage"
    RETRO_80S = "retro_80s"
    KODAK_FILM = "kodak_film"
    WARM = "warm"
    COOL = "cool"
    DRAMATIC = "dramatic"
    DREAMY = "dreamy"
    VIBRANT = "vibrant"
    MUTED = "muted"
    ORANGE_TEAL = "orange_teal"
    BLADE_RUNNER = "blade_runner"
    HIGH_CONTRAST = "high_contrast"
    SEPIA = "sepia"
    BLACK_WHITE = "black_white"
    GOLDEN_HOUR = "golden_hour"
    BLUE_HOUR = "blue_hour"


class ToolCategory(str, Enum):
    GENERATION = "generation"
    EDITING = "editing"
    VISUAL = "visual"
    MOTION = "motion"
    AUDIO = "audio"
    TRANSITION = "transition"
    TEXT = "text"
    EXPORT = "export"


class ToolType(str, Enum):
    # Generation (10 tools)
    REGENERATE = "regenerate"
    REGENERATE_WITH_PROMPT = "regenerate_with_prompt"
    STYLE_TRANSFER = "style_transfer"
    UPSCALE_4K = "upscale_4k"
    GENERATE_VARIATIONS = "generate_variations"
    INPAINT = "inpaint"
    OUTPAINT = "outpaint"
    FACE_SWAP = "face_swap"
    REMOVE_BACKGROUND = "remove_background"
    ENHANCE = "enhance"
    # Editing (9 tools)
    TRIM_START = "trim_start"
    TRIM_END = "trim_end"
    SPLIT = "split"
    MERGE = "merge"
    DUPLICATE = "duplicate"
    DELETE = "delete"
    REPLACE_MEDIA = "replace_media"
    COPY = "copy"
    PASTE = "paste"
    # Visual (12 tools)
    COLOR_GRADE = "color_grade"
    CUSTOM_LUT = "custom_lut"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    VIBRANCE = "vibrance"
    WHITE_BALANCE = "white_balance"
    VIGNETTE = "vignette"
    FILM_GRAIN = "film_grain"
    LENS_BLUR = "lens_blur"
    SHARPEN = "sharpen"
    DENOISE = "denoise"
    # Motion (7 tools)
    SET_CAMERA_MOVE = "set_camera_move"
    KEN_BURNS = "ken_burns"
    SPEED_RAMP = "speed_ramp"
    REVERSE = "reverse"
    FREEZE_FRAME = "freeze_frame"
    MOTION_BLUR = "motion_blur"
    STABILIZE = "stabilize"
    # Audio (6 tools)
    ADD_NARRATION = "add_narration"
    ADD_SFX = "add_sfx"
    VOLUME_ADJUST = "volume_adjust"
    FADE_AUDIO = "fade_audio"
    AUDIO_DUCK = "audio_duck"
    SYNC_TO_BEAT = "sync_to_beat"
    # Transition (3 tools)
    SET_TRANSITION = "set_transition"
    TRANSITION_DURATION = "transition_duration"
    TRANSITION_EASING = "transition_easing"
    # Text (4 tools)
    ADD_TEXT = "add_text"
    ADD_SUBTITLE = "add_subtitle"
    ADD_LOWER_THIRD = "add_lower_third"
    ADD_TITLE = "add_title"
    # Markers (2 tools)
    ADD_CHAPTER = "add_chapter"
    ADD_MARKER = "add_marker"


class EasingType(str, Enum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


class ExportPreset(str, Enum):
    YOUTUBE_4K = "youtube_4k"
    YOUTUBE_1080P = "youtube_1080p"
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    PRORES_422 = "prores_422"
    WEB_MP4 = "web_mp4"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Keyframe:
    """Animation keyframe"""
    time: float
    value: Any
    easing: EasingType = EasingType.EASE_IN_OUT
    
    def to_dict(self) -> Dict:
        return {"time": self.time, "value": self.value, "easing": self.easing.value}


@dataclass
class ColorSettings:
    """Complete color grading"""
    preset: ColorGradePreset = ColorGradePreset.NONE
    custom_lut: Optional[str] = None
    brightness: float = 0.0
    contrast: float = 0.0
    saturation: float = 0.0
    vibrance: float = 0.0
    temperature: float = 0.0
    tint: float = 0.0
    highlights: float = 0.0
    shadows: float = 0.0
    vignette_amount: float = 0.0
    grain_amount: float = 0.0
    sharpen: float = 0.0
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["preset"] = self.preset.value
        return d


@dataclass
class MotionSettings:
    """Camera and motion"""
    camera_move: CameraMovement = CameraMovement.STATIC
    camera_intensity: float = 50.0
    ken_burns_enabled: bool = False
    ken_burns_start_zoom: float = 1.0
    ken_burns_end_zoom: float = 1.2
    speed: float = 1.0
    reverse: bool = False
    motion_blur: float = 0.0
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["camera_move"] = self.camera_move.value
        return d


@dataclass
class TransitionSettings:
    """Transition config"""
    type: TransitionType = TransitionType.DISSOLVE
    duration: float = 0.5
    easing: EasingType = EasingType.EASE_IN_OUT
    audio_crossfade: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "duration": self.duration,
            "easing": self.easing.value,
            "audio_crossfade": self.audio_crossfade
        }


@dataclass
class AudioClip:
    """Audio clip"""
    id: str
    path: str
    track_type: TrackType
    start_time: float = 0.0
    duration: float = 0.0
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    muted: bool = False
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["track_type"] = self.track_type.value
        return d


@dataclass
class TextOverlay:
    """Text on scene"""
    id: str
    text: str
    x: float = 0.5
    y: float = 0.9
    font_size: int = 48
    font_color: str = "#FFFFFF"
    bg_enabled: bool = False
    bg_color: str = "#000000"
    animation_in: str = "fade"
    animation_out: str = "fade"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Marker:
    """Timeline marker"""
    id: str
    time: float
    label: str
    marker_type: str = "chapter"
    color: str = "#FF0000"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TimelineScene:
    """Complete scene with all settings"""
    index: int
    visual_prompt: str = ""
    enhanced_prompt: str = ""
    negative_prompt: str = ""
    
    preview_image: Optional[str] = None
    final_image: Optional[str] = None
    video_clip: Optional[str] = None
    variations: List[str] = field(default_factory=list)
    
    status: SceneStatus = SceneStatus.EMPTY
    generation_progress: float = 0.0
    error_message: Optional[str] = None
    
    duration: float = 5.0
    start_time: float = 0.0
    end_time: float = 5.0
    trim_start: float = 0.0
    trim_end: float = 0.0
    
    style: str = "Cinematic"
    aspect_ratio: str = "16:9"
    color: ColorSettings = field(default_factory=ColorSettings)
    motion: MotionSettings = field(default_factory=MotionSettings)
    
    transition_in: TransitionSettings = field(default_factory=TransitionSettings)
    transition_out: TransitionSettings = field(default_factory=TransitionSettings)
    
    audio_clips: List[AudioClip] = field(default_factory=list)
    narration_text: Optional[str] = None
    text_overlays: List[TextOverlay] = field(default_factory=list)
    
    mood: Optional[str] = None
    lighting: Optional[str] = None
    character_ids: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    
    edit_count: int = 0
    locked: bool = False
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def get_effective_duration(self) -> float:
        base = self.duration - self.trim_start - self.trim_end
        return base / self.motion.speed
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "visual_prompt": self.visual_prompt,
            "preview_image": self.preview_image,
            "final_image": self.final_image,
            "status": self.status.value,
            "duration": self.duration,
            "effective_duration": self.get_effective_duration(),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "style": self.style,
            "color": self.color.to_dict(),
            "motion": self.motion.to_dict(),
            "transition_in": self.transition_in.to_dict(),
            "transition_out": self.transition_out.to_dict(),
            "audio_clips": [a.to_dict() for a in self.audio_clips],
            "text_overlays": [t.to_dict() for t in self.text_overlays],
            "mood": self.mood,
            "edit_count": self.edit_count,
            "locked": self.locked
        }
    
    def to_compact(self) -> Dict:
        return {
            "index": self.index,
            "prompt": self.visual_prompt[:60] + "..." if len(self.visual_prompt) > 60 else self.visual_prompt,
            "preview": self.preview_image,
            "status": self.status.value,
            "duration": self.duration,
            "start": self.start_time,
            "transition": self.transition_out.type.value,
            "locked": self.locked
        }


@dataclass
class AudioTrack:
    """Global audio track"""
    id: str
    name: str
    track_type: TrackType
    path: Optional[str] = None
    volume: float = 1.0
    muted: bool = False
    solo: bool = False
    waveform_data: Optional[List[float]] = None
    beat_markers: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "track_type": self.track_type.value,
            "path": self.path,
            "volume": self.volume,
            "muted": self.muted,
            "solo": self.solo
        }


@dataclass
class SceneEdit:
    """Edit record for undo/redo"""
    id: str
    tool: ToolType
    scene_index: int
    timestamp: datetime
    params: Dict[str, Any]
    before_state: Optional[Dict] = None


@dataclass
class TimelineProject:
    """Complete timeline project"""
    id: str
    title: str
    description: str = ""
    mode: EditorMode = EditorMode.SIMPLE
    
    scenes: List[TimelineScene] = field(default_factory=list)
    audio_tracks: List[AudioTrack] = field(default_factory=list)
    markers: List[Marker] = field(default_factory=list)
    
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    aspect_ratio: str = "16:9"
    global_color: Optional[ColorSettings] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    edit_history: List[SceneEdit] = field(default_factory=list)
    undo_position: int = 0
    
    @property
    def total_duration(self) -> float:
        if not self.scenes:
            return 0.0
        total = sum(s.get_effective_duration() for s in self.scenes)
        for scene in self.scenes[:-1]:
            total -= scene.transition_out.duration
        return max(0, total)
    
    def recalculate_timings(self):
        current = 0.0
        for i, scene in enumerate(self.scenes):
            scene.start_time = current
            scene.end_time = current + scene.get_effective_duration()
            if i < len(self.scenes) - 1:
                current = scene.end_time - scene.transition_out.duration
            else:
                current = scene.end_time
        self.updated_at = datetime.utcnow()
    
    def _format_duration(self, seconds: float) -> str:
        h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "mode": self.mode.value,
            "scene_count": len(self.scenes),
            "total_duration": self.total_duration,
            "duration_formatted": self._format_duration(self.total_duration),
            "resolution": list(self.resolution),
            "fps": self.fps,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def to_timeline_view(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "mode": self.mode.value,
            "duration": self.total_duration,
            "duration_formatted": self._format_duration(self.total_duration),
            "resolution": list(self.resolution),
            "fps": self.fps,
            "video_track": [s.to_compact() for s in self.scenes],
            "audio_tracks": [t.to_dict() for t in self.audio_tracks],
            "markers": [m.to_dict() for m in self.markers],
            "can_undo": self.undo_position > 0,
            "can_redo": self.undo_position < len(self.edit_history),
            "status": {
                "pending": sum(1 for s in self.scenes if s.status == SceneStatus.PENDING),
                "generating": sum(1 for s in self.scenes if s.status == SceneStatus.GENERATING),
                "ready": sum(1 for s in self.scenes if s.status == SceneStatus.READY),
                "approved": sum(1 for s in self.scenes if s.status == SceneStatus.APPROVED)
            }
        }
