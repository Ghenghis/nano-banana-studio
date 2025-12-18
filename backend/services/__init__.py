"""
Nano Banana Studio Pro - Services Module
=========================================
Enterprise-grade service layer for AI video production.

Core Services:
- FaceService: Face detection, embedding, character consistency
- SunoMusicService: AI music generation via Suno API
- WhisperService: Speech recognition and transcription
- ComfyUIService: ComfyUI workflow execution
- LTXVideoService: LTX video generation
- MusicGenService: Local music generation

Extended Services (Professional Studio):
- ScreenplayService: Full screenplay generation (10 min - 3 hours)
- PodcastService: Multi-AI podcast generation (3+ voices)
- SceneAssemblyService: Long-form video assembly
- StoryboardService: LLM-driven scene generation
- AnimationService: Multi-provider image-to-video
- AudioIntelligenceService: Advanced audio analysis
- PublishingService: Output publishing and export
- ThumbnailService: Thumbnail generation
- TTSService: Text-to-speech synthesis
"""

# =============================================================================
# CORE SERVICES
# =============================================================================

from .face_service import (
    FaceService,
    FaceDetection,
    Character,
    MediaPipeFaceDetector,
    InsightFaceEmbedder,
    get_face_service,
)

from .suno_service import (
    SunoClient,
    SunoMusicService,
    SunoGenerateRequest,
    SunoSong,
    SunoStyle,
    SunoMood,
    get_suno_service,
)

from .whisper_service import WhisperService
from .comfyui_service import ComfyUIService
from .ltx_video_service import LTXVideoService
from .musicgen_service import MusicGenService


# =============================================================================
# EXTENDED SERVICES - Professional Studio
# =============================================================================

# Screenplay Generator
try:
    from .screenplay_service import (
        ScreenplayService,
        Screenplay,
        Scene as ScreenplayScene,
        Character as ScreenplayCharacter,
        Genre,
        StoryStructure,
        get_screenplay_service,
    )
except ImportError:
    ScreenplayService = None
    get_screenplay_service = None

# Multi-AI Podcast Generator
try:
    from .podcast_service import (
        PodcastService,
        PodcastEpisode,
        PodcastPersonality,
        PersonalityType,
        DialogueTurn,
        get_podcast_service,
    )
except ImportError:
    PodcastService = None
    get_podcast_service = None

# Scene Assembly (Long-Form Video)
try:
    from .scene_assembly_service import (
        SceneAssemblyService,
        Timeline,
        VideoClip,
        AudioTrack,
        Transition,
        TransitionType as AssemblyTransitionType,
        AssemblyResult,
        get_scene_assembly_service,
    )
except ImportError:
    SceneAssemblyService = None
    get_scene_assembly_service = None

# Storyboard Generator
try:
    from .storyboard_service import (
        StoryboardService,
        Storyboard,
        Scene as StoryboardScene,
        SceneType,
        CameraMove,
        get_storyboard_service,
    )
except ImportError:
    StoryboardService = None
    get_storyboard_service = None

# Animation Service
try:
    from .animation_service import (
        AnimationService,
        AnimationRequest,
        AnimationResult,
        AnimationProvider,
        MotionType,
        get_animation_service,
    )
except ImportError:
    AnimationService = None
    get_animation_service = None

# Audio Intelligence
try:
    from .audio_intelligence_service import (
        AudioIntelligenceService,
        AudioAnalysis,
        Beat,
        Section,
        get_audio_intelligence_service,
    )
except ImportError:
    AudioIntelligenceService = None
    get_audio_intelligence_service = None

# Publishing Service
try:
    from .publishing_service import (
        PublishingService,
        ExportRequest,
        ExportResult,
        Platform,
        Quality,
        ExportFormat,
        get_publishing_service,
    )
except ImportError:
    PublishingService = None
    get_publishing_service = None

# Thumbnail Service
try:
    from .thumbnail_service import (
        ThumbnailService,
        ThumbnailRequest,
        ThumbnailResult,
        ThumbnailStyle,
        TextOverlay,
        TextPosition,
        get_thumbnail_service,
    )
except ImportError:
    ThumbnailService = None
    get_thumbnail_service = None

# TTS Service
try:
    from .tts_service import (
        TTSService,
        TTSRequest,
        TTSResult,
        TTSProvider,
        Voice,
        SpeechStyle,
        get_tts_service,
    )
except ImportError:
    TTSService = None
    get_tts_service = None

# YouTube Publishing Service
try:
    from .youtube_service import (
        YouTubeService,
        YouTubeAccount,
        VideoMetadata,
        UploadResult,
        PrivacyStatus,
        VideoCategory,
        UploadStatus,
        get_youtube_service,
    )
except ImportError:
    YouTubeService = None
    get_youtube_service = None

# Timeline Editor Service (10-Star Professional NLE)
try:
    from .timeline import (
        TimelineEditorService,
        TimelineProject,
        TimelineScene,
        AudioTrack,
        EditorMode,
        SceneStatus,
        TransitionType,
        CameraMovement,
        ColorGradePreset,
        ToolType,
        ExportPreset,
        get_timeline_editor_service,
    )
except ImportError:
    TimelineEditorService = None
    get_timeline_editor_service = None

# 8K Ultra-Detailed Prompt Enhancer
try:
    from .prompt_enhancer_8k import (
        PromptEnhancer8K,
        EnhancedPrompt,
        CinematicShot,
        ShotType,
        CameraAngle,
        LensType,
        LightingStyle,
        ColorGrade,
        Mood,
        get_prompt_enhancer_8k,
    )
except ImportError:
    PromptEnhancer8K = None
    get_prompt_enhancer_8k = None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Face
    "FaceService",
    "FaceDetection",
    "Character",
    "MediaPipeFaceDetector",
    "InsightFaceEmbedder",
    "get_face_service",
    
    # Suno
    "SunoClient",
    "SunoMusicService",
    "SunoGenerateRequest",
    "SunoSong",
    "SunoStyle",
    "SunoMood",
    "get_suno_service",
    
    # Core
    "WhisperService",
    "ComfyUIService",
    "LTXVideoService",
    "MusicGenService",
    
    # Screenplay
    "ScreenplayService",
    "Screenplay",
    "Genre",
    "StoryStructure",
    "get_screenplay_service",
    
    # Podcast
    "PodcastService",
    "PodcastEpisode",
    "PodcastPersonality",
    "PersonalityType",
    "get_podcast_service",
    
    # Scene Assembly
    "SceneAssemblyService",
    "Timeline",
    "VideoClip",
    "AudioTrack",
    "Transition",
    "AssemblyResult",
    "get_scene_assembly_service",
    
    # Storyboard
    "StoryboardService",
    "Storyboard",
    "SceneType",
    "CameraMove",
    "get_storyboard_service",
    
    # Animation
    "AnimationService",
    "AnimationRequest",
    "AnimationResult",
    "AnimationProvider",
    "MotionType",
    "get_animation_service",
    
    # Audio Intelligence
    "AudioIntelligenceService",
    "AudioAnalysis",
    "get_audio_intelligence_service",
    
    # Publishing
    "PublishingService",
    "ExportRequest",
    "ExportResult",
    "Platform",
    "Quality",
    "get_publishing_service",
    
    # Thumbnail
    "ThumbnailService",
    "ThumbnailRequest",
    "ThumbnailResult",
    "ThumbnailStyle",
    "get_thumbnail_service",
    
    # TTS
    "TTSService",
    "TTSRequest",
    "TTSResult",
    "TTSProvider",
    "get_tts_service",
    
    # YouTube
    "YouTubeService",
    "YouTubeAccount",
    "VideoMetadata",
    "UploadResult",
    "PrivacyStatus",
    "VideoCategory",
    "get_youtube_service",
    
    # Timeline Editor
    "TimelineEditorService",
    "TimelineProject",
    "TimelineScene",
    "AudioTrack",
    "EditorMode",
    "SceneStatus",
    "TransitionType",
    "CameraMovement",
    "ColorGradePreset",
    "ToolType",
    "ExportPreset",
    "get_timeline_editor_service",
    
    # 8K Prompt Enhancer
    "PromptEnhancer8K",
    "EnhancedPrompt",
    "CinematicShot",
    "ShotType",
    "CameraAngle",
    "LensType",
    "LightingStyle",
    "ColorGrade",
    "Mood",
    "get_prompt_enhancer_8k",
]
