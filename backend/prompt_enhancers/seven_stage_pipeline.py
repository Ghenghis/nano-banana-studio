"""
Nano Banana Studio Pro - 7-Stage Prompt Enhancement System
===========================================================
Advanced prompt engineering pipeline for professional-quality image generation.

Stages:
1. Concept Expansion
2. Scene Definition  
3. Visual Specification
4. Cinematic Language
5. Narrative Context
6. Technical Parameters
7. Consistency & Polish
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("prompt-enhancer")


class Style(Enum):
    PHOTOREALISTIC = "photorealistic"
    CINEMATIC = "cinematic"
    ARTISTIC = "artistic"
    DOCUMENTARY = "documentary"
    ANIME = "anime"
    THREE_D_RENDER = "3d_render"
    VINTAGE_FILM = "vintage_film"
    NEON_CYBERPUNK = "neon_cyberpunk"
    MINIMALIST = "minimalist"
    FANTASY = "fantasy"
    SCIFI = "scifi"
    CHRISTMAS = "christmas"


class Platform(Enum):
    YOUTUBE_LANDSCAPE = "YouTube (16:9)"
    YOUTUBE_SHORTS = "YouTube Shorts (9:16)"
    TIKTOK = "TikTok (9:16)"
    INSTAGRAM_REEL = "Instagram Reel (9:16)"
    INSTAGRAM_POST = "Instagram Post (1:1)"
    CINEMATIC = "Cinematic (2.39:1)"
    FOUR_K = "4K YouTube (16:9)"


@dataclass
class EnhancementConfig:
    """Configuration for prompt enhancement"""
    style: Style = Style.CINEMATIC
    platform: Platform = Platform.YOUTUBE_LANDSCAPE
    quality_level: str = "high"  # draft, standard, high, maximum
    include_negative: bool = True
    include_style_dna: bool = True
    character_reference: Optional[str] = None
    preserve_keywords: List[str] = field(default_factory=list)


@dataclass
class EnhancedPrompt:
    """Result of prompt enhancement"""
    original: str
    enhanced: str
    negative: Optional[str]
    stages: Dict[str, str]
    style_dna: Dict[str, Any]
    fingerprint: str


class PromptEnhancerBase:
    """Base class for prompt enhancement stages"""
    
    stage_name: str = "base"
    
    def __init__(self, config: EnhancementConfig):
        self.config = config
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Override in subclasses"""
        raise NotImplementedError


class ConceptExpander(PromptEnhancerBase):
    """Stage 1: Expand the core concept with creative depth"""
    
    stage_name = "concept"
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Theme analysis
        themes = self._extract_themes(prompt)
        
        # Mood enhancement
        mood_words = self._generate_mood_profile(prompt)
        
        # Visual metaphors
        metaphors = self._generate_metaphors(prompt)
        
        # Build enhanced concept
        enhanced = f"{prompt}"
        
        if themes:
            enhanced += f", {', '.join(themes[:3])}"
        
        if mood_words:
            enhanced += f", {', '.join(mood_words[:3])} atmosphere"
        
        return enhanced
    
    def _extract_themes(self, prompt: str) -> List[str]:
        """Extract thematic elements from prompt"""
        theme_keywords = {
            "love": ["romantic", "passionate", "tender"],
            "power": ["commanding", "authoritative", "dominant"],
            "nature": ["organic", "natural", "wild"],
            "tech": ["futuristic", "digital", "cyber"],
            "music": ["rhythmic", "melodic", "harmonic"],
            "dance": ["dynamic", "fluid", "expressive"],
            "night": ["nocturnal", "mysterious", "shadowy"],
            "day": ["bright", "vibrant", "radiant"]
        }
        
        themes = []
        prompt_lower = prompt.lower()
        
        for keyword, related in theme_keywords.items():
            if keyword in prompt_lower:
                themes.extend(related)
        
        return themes
    
    def _generate_mood_profile(self, prompt: str) -> List[str]:
        """Generate mood descriptors"""
        # Basic sentiment analysis
        positive_words = ["happy", "joy", "bright", "love", "beautiful", "amazing"]
        negative_words = ["dark", "sad", "lonely", "scary", "mysterious"]
        
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in positive_words):
            return ["uplifting", "warm", "inviting"]
        elif any(word in prompt_lower for word in negative_words):
            return ["moody", "atmospheric", "dramatic"]
        else:
            return ["balanced", "professional", "refined"]
    
    def _generate_metaphors(self, prompt: str) -> List[str]:
        """Generate visual metaphors"""
        return []  # Extended in full implementation


class SceneDefiner(PromptEnhancerBase):
    """Stage 2: Define the environment and spatial composition"""
    
    stage_name = "scene"
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Environment elements
        environment = self._define_environment(prompt)
        
        # Spatial composition
        composition = self._define_composition(prompt)
        
        # Time context
        time_context = self._define_time(prompt)
        
        # Build scene description
        parts = [prompt]
        
        if environment:
            parts.append(environment)
        
        if composition:
            parts.append(composition)
        
        if time_context:
            parts.append(time_context)
        
        return ", ".join(parts)
    
    def _define_environment(self, prompt: str) -> str:
        """Define environmental elements"""
        prompt_lower = prompt.lower()
        
        indoor_keywords = ["room", "studio", "office", "inside", "interior"]
        outdoor_keywords = ["outside", "nature", "city", "street", "landscape"]
        
        if any(word in prompt_lower for word in indoor_keywords):
            return "detailed interior environment"
        elif any(word in prompt_lower for word in outdoor_keywords):
            return "expansive environmental backdrop"
        
        return "professional studio setting"
    
    def _define_composition(self, prompt: str) -> str:
        """Define spatial composition"""
        compositions = {
            "portrait": "centered subject composition with depth",
            "landscape": "wide panoramic composition",
            "action": "dynamic diagonal composition",
            "group": "balanced ensemble arrangement"
        }
        
        return compositions.get("portrait", "thoughtfully composed scene")
    
    def _define_time(self, prompt: str) -> str:
        """Define time context"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["night", "dark", "evening", "sunset"]):
            return "evening golden hour lighting"
        elif any(word in prompt_lower for word in ["morning", "sunrise", "dawn"]):
            return "soft morning light"
        elif any(word in prompt_lower for word in ["noon", "bright", "sunny"]):
            return "bright daylight"
        
        return "optimal professional lighting"


class VisualSpecifier(PromptEnhancerBase):
    """Stage 3: Specify visual parameters - colors, lighting, texture"""
    
    stage_name = "visual"
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Color palette
        colors = self._define_colors()
        
        # Lighting design
        lighting = self._define_lighting()
        
        # Texture profile
        texture = self._define_texture()
        
        parts = [prompt]
        
        parts.append(colors)
        parts.append(lighting)
        parts.append(texture)
        
        return ", ".join(parts)
    
    def _define_colors(self) -> str:
        """Define color palette based on style"""
        style_colors = {
            Style.CINEMATIC: "rich cinematic color palette with deep shadows",
            Style.NEON_CYBERPUNK: "vibrant neon pink and blue color scheme",
            Style.VINTAGE_FILM: "warm sepia tones and muted colors",
            Style.FANTASY: "ethereal magical color gradients",
            Style.CHRISTMAS: "festive red and green with warm golden accents",
            Style.MINIMALIST: "clean monochromatic palette"
        }
        
        return style_colors.get(self.config.style, "harmonious professional color palette")
    
    def _define_lighting(self) -> str:
        """Define lighting setup"""
        style_lighting = {
            Style.CINEMATIC: "three-point cinematic lighting with dramatic shadows",
            Style.DOCUMENTARY: "natural ambient lighting",
            Style.NEON_CYBERPUNK: "neon accent lighting with rim lights",
            Style.VINTAGE_FILM: "soft diffused film lighting",
            Style.CHRISTMAS: "warm holiday lighting with twinkling accents"
        }
        
        return style_lighting.get(self.config.style, "professional studio lighting")
    
    def _define_texture(self) -> str:
        """Define texture profile"""
        quality_textures = {
            "maximum": "ultra-fine detail texture, micro surface details visible",
            "high": "high-resolution detailed textures",
            "standard": "clean detailed textures",
            "draft": "basic textures"
        }
        
        return quality_textures.get(self.config.quality_level, "detailed textures")


class CinematicLanguage(PromptEnhancerBase):
    """Stage 4: Add cinematic camera and lens language"""
    
    stage_name = "cinematic"
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Camera position
        camera = self._define_camera()
        
        # Lens characteristics
        lens = self._define_lens()
        
        # Frame dynamics
        dynamics = self._define_dynamics()
        
        parts = [prompt]
        
        parts.append(camera)
        parts.append(lens)
        parts.append(dynamics)
        
        return ", ".join(parts)
    
    def _define_camera(self) -> str:
        """Define camera position and angle"""
        return "eye-level medium shot"
    
    def _define_lens(self) -> str:
        """Define lens characteristics"""
        style_lens = {
            Style.CINEMATIC: "shot on 35mm anamorphic lens, shallow depth of field, bokeh",
            Style.DOCUMENTARY: "shot on 50mm lens, natural depth",
            Style.PHOTOREALISTIC: "shot on 85mm portrait lens, creamy bokeh",
            Style.THREE_D_RENDER: "virtual camera with perfect focus"
        }
        
        return style_lens.get(self.config.style, "professional camera lens")
    
    def _define_dynamics(self) -> str:
        """Define frame dynamics"""
        return "perfectly composed frame, rule of thirds"


class NarrativeContextualizer(PromptEnhancerBase):
    """Stage 5: Add narrative and emotional context"""
    
    stage_name = "narrative"
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Story position
        story = self._define_story_beat()
        
        # Emotional tone
        emotion = self._define_emotion()
        
        parts = [prompt]
        
        parts.append(story)
        parts.append(emotion)
        
        return ", ".join(parts)
    
    def _define_story_beat(self) -> str:
        """Define narrative moment"""
        scene_index = (context or {}).get("scene_index", 1)
        total_scenes = (context or {}).get("total_scenes", 1)
        
        position = scene_index / total_scenes
        
        if position < 0.2:
            return "establishing moment, introduction"
        elif position < 0.5:
            return "rising action, building intensity"
        elif position < 0.8:
            return "climactic moment, peak emotion"
        else:
            return "resolution, reflective conclusion"
    
    def _define_emotion(self) -> str:
        """Define emotional resonance"""
        return "emotionally resonant, evocative mood"


class TechnicalSpecifier(PromptEnhancerBase):
    """Stage 6: Add technical quality parameters"""
    
    stage_name = "technical"
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Quality keywords
        quality = self._define_quality()
        
        # Resolution
        resolution = self._define_resolution()
        
        parts = [prompt]
        
        parts.append(quality)
        parts.append(resolution)
        
        return ", ".join(parts)
    
    def _define_quality(self) -> str:
        """Define quality keywords"""
        quality_keywords = {
            "maximum": "masterpiece, best quality, ultra-detailed, professional",
            "high": "high quality, detailed, professional",
            "standard": "good quality, clean",
            "draft": "sketch quality"
        }
        
        return quality_keywords.get(self.config.quality_level, "professional quality")
    
    def _define_resolution(self) -> str:
        """Define resolution parameters"""
        platform_res = {
            Platform.FOUR_K: "8K resolution, ultra high definition",
            Platform.YOUTUBE_LANDSCAPE: "4K resolution, sharp details",
            Platform.YOUTUBE_SHORTS: "full HD, crisp mobile display",
            Platform.TIKTOK: "HD quality, optimized for mobile"
        }
        
        return platform_res.get(self.config.platform, "high resolution")
    
    def generate_negative(self) -> str:
        """Generate negative prompt"""
        base_negative = [
            "blurry", "low quality", "distorted", "deformed",
            "watermark", "text", "logo", "signature",
            "amateur", "poorly drawn", "bad anatomy",
            "extra limbs", "mutated", "disfigured"
        ]
        
        style_negative = {
            Style.PHOTOREALISTIC: ["cartoon", "illustration", "anime", "painting"],
            Style.ANIME: ["realistic", "photographic", "3D"],
            Style.CINEMATIC: ["flat lighting", "snapshot", "amateur"],
            Style.MINIMALIST: ["cluttered", "busy", "complex"]
        }
        
        all_negative = base_negative + style_negative.get(self.config.style, [])
        
        return ", ".join(all_negative)


class ConsistencyPolisher(PromptEnhancerBase):
    """Stage 7: Ensure consistency and final polish"""
    
    stage_name = "consistency"
    
    def enhance(self, prompt: str, context: Dict[str, Any] = None) -> str:
        # Style DNA
        style_dna = self._extract_style_dna(prompt)
        
        # Consistency keywords
        consistency = self._add_consistency_keywords()
        
        # Character reference
        character = self._add_character_reference()
        
        parts = [prompt]
        
        parts.append(consistency)
        
        if character:
            parts.append(character)
        
        return ", ".join(parts)
    
    def _extract_style_dna(self, prompt: str) -> Dict[str, Any]:
        """Extract style DNA for consistency across generations"""
        return {
            "style": self.config.style.value,
            "platform": self.config.platform.value,
            "quality": self.config.quality_level,
            "anchor_keywords": prompt.split(",")[:5]
        }
    
    def _add_consistency_keywords(self) -> str:
        """Add consistency-ensuring keywords"""
        return "consistent style, cohesive look, unified aesthetic"
    
    def _add_character_reference(self) -> Optional[str]:
        """Add character reference if available"""
        if self.config.character_reference:
            return f"same person as reference image, maintain facial features, consistent appearance"
        return None


class PromptEnhancementPipeline:
    """Complete 7-stage prompt enhancement pipeline"""
    
    def __init__(self, config: EnhancementConfig = None):
        self.config = config or EnhancementConfig()
        
        # Initialize all stages
        self.stages = [
            ConceptExpander(self.config),
            SceneDefiner(self.config),
            VisualSpecifier(self.config),
            CinematicLanguage(self.config),
            NarrativeContextualizer(self.config),
            TechnicalSpecifier(self.config),
            ConsistencyPolisher(self.config)
        ]
    
    def enhance(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None
    ) -> EnhancedPrompt:
        """Run complete enhancement pipeline"""
        
        current_prompt = prompt
        stage_results = {}
        
        for stage in self.stages:
            current_prompt = stage.enhance(current_prompt, context)
            stage_results[stage.stage_name] = current_prompt
        
        # Generate negative prompt
        technical_stage = self.stages[5]  # TechnicalSpecifier
        negative = technical_stage.generate_negative() if self.config.include_negative else None
        
        # Extract style DNA
        consistency_stage = self.stages[6]  # ConsistencyPolisher
        style_dna = consistency_stage._extract_style_dna(current_prompt)
        
        # Compute fingerprint
        fingerprint = hashlib.sha256(
            f"{prompt}:{self.config.style.value}:{self.config.platform.value}".encode()
        ).hexdigest()[:16]
        
        return EnhancedPrompt(
            original=prompt,
            enhanced=current_prompt,
            negative=negative,
            stages=stage_results,
            style_dna=style_dna,
            fingerprint=fingerprint
        )


# Convenience function
def enhance_prompt(
    prompt: str,
    style: str = "cinematic",
    platform: str = "YouTube (16:9)",
    quality: str = "high",
    character_ref: str = None
) -> EnhancedPrompt:
    """Quick prompt enhancement"""
    
    # Parse style
    try:
        style_enum = Style(style.lower())
    except ValueError:
        style_enum = Style.CINEMATIC
    
    # Parse platform
    platform_enum = Platform.YOUTUBE_LANDSCAPE
    for p in Platform:
        if platform.lower() in p.value.lower():
            platform_enum = p
            break
    
    config = EnhancementConfig(
        style=style_enum,
        platform=platform_enum,
        quality_level=quality,
        include_negative=True,
        character_reference=character_ref
    )
    
    pipeline = PromptEnhancementPipeline(config)
    return pipeline.enhance(prompt)
