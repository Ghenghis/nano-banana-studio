"""
Nano Banana Studio Pro - Screenplay Generator Service
=======================================================
Professional screenplay generation for feature-length films.

Features:
- Full screenplay generation (10 min - 3 hours)
- Genre-aware story structure
- Multi-character dialogue
- Scene breakdown with INT/EXT
- Act structure (3-act, 5-act, hero's journey)
- Character arc tracking
- Export to industry formats (Fountain, Final Draft)

Dependencies:
    pip install httpx pyyaml
"""

import os
import json
import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger("screenplay-service")


# =============================================================================
# CONFIGURATION
# =============================================================================

class ScreenplayConfig:
    """Screenplay service configuration"""
    LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/outputs"))
    SCRIPTS_DIR = Path(os.getenv("SCRIPTS_DIR", "/app/data/scripts"))
    
    # 1 page = ~1 minute of screen time
    PAGES_PER_MINUTE = 1.0


# =============================================================================
# ENUMS & DATA MODELS
# =============================================================================

class Genre(str, Enum):
    ACTION = "action"
    COMEDY = "comedy"
    DRAMA = "drama"
    HORROR = "horror"
    SCIFI = "sci-fi"
    FANTASY = "fantasy"
    THRILLER = "thriller"
    ROMANCE = "romance"
    DOCUMENTARY = "documentary"
    ANIMATION = "animation"
    MUSICAL = "musical"


class StoryStructure(str, Enum):
    THREE_ACT = "three_act"
    FIVE_ACT = "five_act"
    HEROS_JOURNEY = "heros_journey"
    SAVE_THE_CAT = "save_the_cat"
    DAN_HARMON = "dan_harmon"


class LocationType(str, Enum):
    INT = "INT"
    EXT = "EXT"
    INT_EXT = "INT/EXT"


class TimeOfDay(str, Enum):
    DAY = "DAY"
    NIGHT = "NIGHT"
    DAWN = "DAWN"
    DUSK = "DUSK"
    CONTINUOUS = "CONTINUOUS"
    LATER = "LATER"
    MOMENTS_LATER = "MOMENTS LATER"


@dataclass
class Character:
    """Character definition"""
    name: str
    age: Optional[int] = None
    description: str = ""
    role: str = "supporting"  # protagonist, antagonist, supporting, minor
    arc: str = ""
    voice_profile: Optional[str] = None  # For TTS
    appearance: str = ""  # For image generation
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "age": self.age,
            "description": self.description,
            "role": self.role,
            "arc": self.arc,
            "voice_profile": self.voice_profile,
            "appearance": self.appearance
        }


@dataclass
class DialogueLine:
    """Single line of dialogue"""
    character: str
    line: str
    parenthetical: Optional[str] = None  # (whispering), (angry), etc.
    
    def to_fountain(self) -> str:
        """Convert to Fountain format"""
        result = f"\n{self.character.upper()}\n"
        if self.parenthetical:
            result += f"({self.parenthetical})\n"
        result += f"{self.line}\n"
        return result


@dataclass
class SceneHeading:
    """Scene heading (slugline)"""
    location_type: LocationType
    location: str
    time: TimeOfDay
    
    def to_fountain(self) -> str:
        return f"\n{self.location_type.value}. {self.location.upper()} - {self.time.value}\n"


@dataclass
class Scene:
    """Complete scene"""
    scene_number: int
    heading: SceneHeading
    action: str
    dialogue: List[DialogueLine] = field(default_factory=list)
    notes: str = ""
    
    # For video generation
    visual_description: str = ""
    camera_notes: str = ""
    estimated_duration: float = 0.0  # seconds
    
    def to_fountain(self) -> str:
        """Convert to Fountain format"""
        result = self.heading.to_fountain()
        result += f"\n{self.action}\n"
        for line in self.dialogue:
            result += line.to_fountain()
        return result
    
    def to_dict(self) -> Dict:
        return {
            "scene_number": self.scene_number,
            "location_type": self.heading.location_type.value,
            "location": self.heading.location,
            "time": self.heading.time.value,
            "action": self.action,
            "dialogue": [
                {"character": d.character, "line": d.line, "parenthetical": d.parenthetical}
                for d in self.dialogue
            ],
            "visual_description": self.visual_description,
            "camera_notes": self.camera_notes,
            "estimated_duration": self.estimated_duration
        }


@dataclass
class Screenplay:
    """Complete screenplay"""
    id: str
    title: str
    logline: str
    genre: Genre
    
    characters: List[Character]
    scenes: List[Scene]
    
    target_runtime: int  # minutes
    page_count: int = 0
    
    structure: StoryStructure = StoryStructure.THREE_ACT
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def estimated_runtime(self) -> float:
        """Estimate runtime from scene durations"""
        return sum(s.estimated_duration for s in self.scenes) / 60.0
    
    def to_fountain(self) -> str:
        """Export to Fountain format"""
        result = f"Title: {self.title}\n"
        result += f"Credit: Written by AI\n"
        result += f"Draft date: {self.created_at.strftime('%Y-%m-%d')}\n"
        result += "\n"
        
        for scene in self.scenes:
            result += scene.to_fountain()
        
        return result
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "logline": self.logline,
            "genre": self.genre.value,
            "characters": [c.to_dict() for c in self.characters],
            "scenes": [s.to_dict() for s in self.scenes],
            "target_runtime": self.target_runtime,
            "estimated_runtime": self.estimated_runtime,
            "scene_count": len(self.scenes),
            "structure": self.structure.value,
            "created_at": self.created_at.isoformat()
        }


# =============================================================================
# STORY STRUCTURE TEMPLATES
# =============================================================================

STRUCTURE_TEMPLATES = {
    StoryStructure.THREE_ACT: {
        "acts": [
            {"name": "Setup", "percentage": 25, "beats": ["Hook", "Inciting Incident", "First Plot Point"]},
            {"name": "Confrontation", "percentage": 50, "beats": ["Rising Action", "Midpoint", "Crisis", "Second Plot Point"]},
            {"name": "Resolution", "percentage": 25, "beats": ["Climax", "Resolution", "Denouement"]}
        ]
    },
    StoryStructure.HEROS_JOURNEY: {
        "acts": [
            {"name": "Departure", "percentage": 30, "beats": ["Ordinary World", "Call to Adventure", "Refusal", "Meeting Mentor", "Crossing Threshold"]},
            {"name": "Initiation", "percentage": 40, "beats": ["Tests/Allies/Enemies", "Approach", "Ordeal", "Reward"]},
            {"name": "Return", "percentage": 30, "beats": ["Road Back", "Resurrection", "Return with Elixir"]}
        ]
    },
    StoryStructure.SAVE_THE_CAT: {
        "acts": [
            {"name": "Act 1", "percentage": 25, "beats": ["Opening Image", "Theme Stated", "Set-Up", "Catalyst", "Debate"]},
            {"name": "Act 2A", "percentage": 25, "beats": ["Break into Two", "B Story", "Fun and Games", "Midpoint"]},
            {"name": "Act 2B", "percentage": 25, "beats": ["Bad Guys Close In", "All Is Lost", "Dark Night of Soul"]},
            {"name": "Act 3", "percentage": 25, "beats": ["Break into Three", "Finale", "Final Image"]}
        ]
    }
}


# =============================================================================
# SCREENPLAY SERVICE
# =============================================================================

class ScreenplayService:
    """
    Enterprise-grade screenplay generation for feature films.
    Generates complete scripts from 10 minutes to 3+ hours.
    """
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=300.0)
        ScreenplayConfig.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _generate_id(self, content: str) -> str:
        """Generate unique screenplay ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"script_{timestamp}_{content_hash}"
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: int = 8000
    ) -> str:
        """Call LLM with fallback chain"""
        providers = [
            ("lm_studio", f"{ScreenplayConfig.LM_STUDIO_URL}/chat/completions", None),
            ("ollama", f"{ScreenplayConfig.OLLAMA_URL}/v1/chat/completions", None),
        ]
        
        if ScreenplayConfig.OPENAI_API_KEY:
            providers.append(("openai", "https://api.openai.com/v1/chat/completions", ScreenplayConfig.OPENAI_API_KEY))
        
        last_error = None
        for provider_name, url, api_key in providers:
            try:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                model = "gpt-4o" if provider_name == "openai" else "local-model"
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                response = await self.http_client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    last_error = f"HTTP {response.status_code}"
                    
            except Exception as e:
                last_error = str(e)
                continue
        
        raise Exception(f"All LLM providers failed: {last_error}")
    
    async def generate_outline(
        self,
        concept: str,
        genre: Genre,
        target_runtime: int,
        structure: StoryStructure = StoryStructure.THREE_ACT
    ) -> Dict[str, Any]:
        """Generate story outline with beats"""
        structure_template = STRUCTURE_TEMPLATES.get(structure, STRUCTURE_TEMPLATES[StoryStructure.THREE_ACT])
        
        system_prompt = f"""You are a professional screenwriter. Create a detailed story outline.

GENRE: {genre.value}
TARGET RUNTIME: {target_runtime} minutes
STRUCTURE: {structure.value}

Structure beats to follow:
{json.dumps(structure_template, indent=2)}

Respond with JSON only:
{{
    "title": "Movie Title",
    "logline": "One sentence pitch",
    "characters": [
        {{"name": "PROTAGONIST", "role": "protagonist", "description": "...", "arc": "..."}},
        {{"name": "ANTAGONIST", "role": "antagonist", "description": "...", "arc": "..."}}
    ],
    "acts": [
        {{
            "name": "Act 1",
            "beats": [
                {{"name": "Opening", "description": "...", "scenes_needed": 3}}
            ]
        }}
    ],
    "themes": ["theme1", "theme2"]
}}"""
        
        response = await self._call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create an outline for: {concept}"}
        ])
        
        # Parse JSON from response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"title": concept, "logline": concept, "characters": [], "acts": []}
    
    async def generate_scene(
        self,
        scene_number: int,
        beat_description: str,
        characters: List[Character],
        previous_scene_summary: str = "",
        genre: Genre = Genre.DRAMA
    ) -> Scene:
        """Generate a single scene with dialogue"""
        character_names = [c.name for c in characters]
        
        system_prompt = f"""You are a professional screenwriter. Write a complete scene.

GENRE: {genre.value}
CHARACTERS AVAILABLE: {', '.join(character_names)}
SCENE NUMBER: {scene_number}

Previous scene: {previous_scene_summary if previous_scene_summary else 'This is the opening scene.'}

Write the scene in JSON format:
{{
    "location_type": "INT" or "EXT",
    "location": "LOCATION NAME",
    "time": "DAY" or "NIGHT",
    "action": "Scene description and action lines...",
    "dialogue": [
        {{"character": "NAME", "line": "Dialogue...", "parenthetical": "optional emotion"}}
    ],
    "visual_description": "Description for AI video generation",
    "camera_notes": "WIDE SHOT, CLOSE-UP, etc.",
    "duration_seconds": 30
}}"""
        
        response = await self._call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write scene for this beat: {beat_description}"}
        ])
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                heading = SceneHeading(
                    location_type=LocationType(data.get("location_type", "INT")),
                    location=data.get("location", "UNKNOWN"),
                    time=TimeOfDay(data.get("time", "DAY"))
                )
                
                dialogue = [
                    DialogueLine(
                        character=d.get("character", ""),
                        line=d.get("line", ""),
                        parenthetical=d.get("parenthetical")
                    )
                    for d in data.get("dialogue", [])
                ]
                
                return Scene(
                    scene_number=scene_number,
                    heading=heading,
                    action=data.get("action", ""),
                    dialogue=dialogue,
                    visual_description=data.get("visual_description", ""),
                    camera_notes=data.get("camera_notes", ""),
                    estimated_duration=float(data.get("duration_seconds", 30))
                )
        except Exception as e:
            logger.error(f"Failed to parse scene: {e}")
        
        # Fallback scene
        return Scene(
            scene_number=scene_number,
            heading=SceneHeading(LocationType.INT, "LOCATION", TimeOfDay.DAY),
            action=beat_description,
            dialogue=[],
            estimated_duration=30.0
        )

    
    async def generate_screenplay(
        self,
        concept: str,
        genre: Genre = Genre.DRAMA,
        target_runtime: int = 90,
        structure: StoryStructure = StoryStructure.THREE_ACT
    ) -> Screenplay:
        """
        Generate a complete screenplay.
        
        Args:
            concept: Story concept/premise
            genre: Film genre
            target_runtime: Target runtime in minutes (10-180+)
            structure: Story structure template
            
        Returns:
            Complete Screenplay with all scenes
        """
        logger.info(f"Generating {target_runtime}-minute {genre.value} screenplay: {concept[:50]}...")
        
        # Step 1: Generate outline
        logger.info("Step 1: Generating story outline...")
        outline = await self.generate_outline(concept, genre, target_runtime, structure)
        
        # Extract characters
        characters = [
            Character(
                name=c.get("name", f"Character {i}"),
                role=c.get("role", "supporting"),
                description=c.get("description", ""),
                arc=c.get("arc", "")
            )
            for i, c in enumerate(outline.get("characters", []))
        ]
        
        if not characters:
            characters = [
                Character(name="PROTAGONIST", role="protagonist", description="Main character"),
                Character(name="SUPPORTING", role="supporting", description="Supporting character")
            ]
        
        # Calculate scenes needed
        # Average scene = 1-2 minutes
        scenes_needed = int(target_runtime * 0.8)  # ~0.8 scenes per minute
        scenes_needed = max(10, min(scenes_needed, 200))  # 10-200 scenes
        
        logger.info(f"Step 2: Generating {scenes_needed} scenes...")
        
        # Collect all beats from outline
        all_beats = []
        for act in outline.get("acts", []):
            for beat in act.get("beats", []):
                beat_name = beat.get("name", "Scene")
                beat_desc = beat.get("description", "Continue the story")
                scenes_for_beat = beat.get("scenes_needed", 2)
                for i in range(scenes_for_beat):
                    all_beats.append(f"{beat_name}: {beat_desc}")
        
        # Pad or trim to match scenes_needed
        while len(all_beats) < scenes_needed:
            all_beats.append("Continue developing the story with character interactions")
        all_beats = all_beats[:scenes_needed]
        
        # Generate scenes
        scenes = []
        previous_summary = ""
        
        for i, beat in enumerate(all_beats):
            logger.info(f"  Generating scene {i+1}/{len(all_beats)}...")
            
            scene = await self.generate_scene(
                scene_number=i + 1,
                beat_description=beat,
                characters=characters,
                previous_scene_summary=previous_summary,
                genre=genre
            )
            
            scenes.append(scene)
            previous_summary = f"Scene {i+1}: {scene.heading.location} - {scene.action[:100]}"
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
        
        # Create screenplay
        screenplay = Screenplay(
            id=self._generate_id(concept),
            title=outline.get("title", concept[:50]),
            logline=outline.get("logline", concept),
            genre=genre,
            characters=characters,
            scenes=scenes,
            target_runtime=target_runtime,
            structure=structure
        )
        
        # Save to file
        output_path = ScreenplayConfig.SCRIPTS_DIR / f"{screenplay.id}.fountain"
        output_path.write_text(screenplay.to_fountain())
        
        json_path = ScreenplayConfig.SCRIPTS_DIR / f"{screenplay.id}.json"
        json_path.write_text(json.dumps(screenplay.to_dict(), indent=2))
        
        logger.info(f"Screenplay generated: {screenplay.title} ({len(scenes)} scenes)")
        
        return screenplay
    
    async def generate_music_video_script(
        self,
        song_title: str,
        artist: str,
        lyrics: str,
        visual_style: str = "cinematic"
    ) -> Screenplay:
        """Generate a music video screenplay from lyrics"""
        logger.info(f"Generating music video script for: {song_title}")
        
        # Parse lyrics into sections
        sections = []
        current_section = {"type": "verse", "lines": []}
        
        for line in lyrics.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("["):
                if current_section["lines"]:
                    sections.append(current_section)
                section_type = "verse"
                if "chorus" in line.lower():
                    section_type = "chorus"
                elif "bridge" in line.lower():
                    section_type = "bridge"
                current_section = {"type": section_type, "lines": []}
            else:
                current_section["lines"].append(line)
        
        if current_section["lines"]:
            sections.append(current_section)
        
        # Generate visual scenes for each section
        scenes = []
        for i, section in enumerate(sections):
            section_lyrics = "\n".join(section["lines"])
            
            system_prompt = f"""You are a music video director. Create a visual scene.

STYLE: {visual_style}
SECTION TYPE: {section['type']}

Create JSON for this lyrics section:
{{
    "location_type": "INT" or "EXT",
    "location": "LOCATION",
    "time": "DAY" or "NIGHT",
    "action": "Visual description of what happens...",
    "visual_description": "Detailed description for AI image generation",
    "camera_notes": "Camera movements",
    "duration_seconds": estimated duration
}}"""
            
            response = await self._call_llm([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create visuals for:\n{section_lyrics}"}
            ])
            
            try:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    data = json.loads(json_match.group())
                    
                    scene = Scene(
                        scene_number=i + 1,
                        heading=SceneHeading(
                            LocationType(data.get("location_type", "EXT")),
                            data.get("location", "MUSIC VIDEO SET"),
                            TimeOfDay(data.get("time", "DAY"))
                        ),
                        action=data.get("action", ""),
                        visual_description=data.get("visual_description", ""),
                        camera_notes=data.get("camera_notes", ""),
                        estimated_duration=float(data.get("duration_seconds", 20)),
                        notes=section_lyrics
                    )
                    scenes.append(scene)
            except:
                # Fallback
                scenes.append(Scene(
                    scene_number=i + 1,
                    heading=SceneHeading(LocationType.EXT, "MUSIC VIDEO SET", TimeOfDay.DAY),
                    action=section_lyrics,
                    estimated_duration=20.0,
                    notes=section_lyrics
                ))
        
        screenplay = Screenplay(
            id=self._generate_id(f"{song_title}_{artist}"),
            title=f"{song_title} - Music Video",
            logline=f"Music video for {song_title} by {artist}",
            genre=Genre.MUSICAL,
            characters=[Character(name="ARTIST", role="protagonist", description=artist)],
            scenes=scenes,
            target_runtime=4,  # typical music video
            structure=StoryStructure.THREE_ACT
        )
        
        return screenplay
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# =============================================================================
# SINGLETON
# =============================================================================

_screenplay_service: Optional[ScreenplayService] = None

def get_screenplay_service() -> ScreenplayService:
    """Get or create screenplay service instance"""
    global _screenplay_service
    if _screenplay_service is None:
        _screenplay_service = ScreenplayService()
    return _screenplay_service
