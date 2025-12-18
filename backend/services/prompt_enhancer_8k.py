"""
Nano Banana Studio Pro - 8K Ultra-Detailed Prompt Enhancer
===========================================================
Based on nano-banana1.txt storytelling techniques.

Creates extremely detailed 8K cinematic prompts with:
- All camera angles (ELS, LS, MLS, MS, MCU, CU, ECU, Low, High)
- All camera movements (pan, tilt, zoom, dolly, crane, orbit, etc.)
- Full cinematic details (lighting, color grade, lens, DoF)
- Story structure (setup → build → turn → payoff)
- Character consistency across all shots

★★★★★★★★★★ 10-STAR PROMPT ENHANCEMENT ★★★★★★★★★★
"""

import re
import json
import asyncio
import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger("prompt-enhancer-8k")


# =============================================================================
# CINEMATIC ENUMS - Complete professional options
# =============================================================================

class ShotType(str, Enum):
    """All standard cinematic shot types"""
    ELS = "extreme_long_shot"      # Subject tiny in vast environment
    LS = "long_shot"               # Full body visible
    MLS = "medium_long_shot"       # Knees up (American shot)
    MS = "medium_shot"             # Waist up
    MCU = "medium_close_up"        # Chest up
    CU = "close_up"                # Face/head
    ECU = "extreme_close_up"       # Eyes, hands, detail
    INSERT = "insert"              # Object detail
    POV = "point_of_view"          # Character's viewpoint
    OTS = "over_the_shoulder"      # Looking over shoulder
    TWO_SHOT = "two_shot"          # Two characters
    GROUP = "group_shot"           # Multiple characters


class CameraAngle(str, Enum):
    """Camera angles relative to subject"""
    EYE_LEVEL = "eye_level"
    LOW_ANGLE = "low_angle"           # Looking up (heroic/powerful)
    HIGH_ANGLE = "high_angle"         # Looking down (vulnerable)
    WORMS_EYE = "worms_eye"           # Extreme low (ground level)
    BIRDS_EYE = "birds_eye"           # Directly above
    DUTCH_ANGLE = "dutch_angle"       # Tilted frame
    OVERHEAD = "overhead"
    GROUND_LEVEL = "ground_level"


class CameraMovement(str, Enum):
    """Camera movements for animation"""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PUSH_IN = "push_in"               # Dolly forward
    PULL_OUT = "pull_out"             # Dolly backward
    DOLLY_LEFT = "dolly_left"
    DOLLY_RIGHT = "dolly_right"
    TRACKING = "tracking"             # Following subject
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    ORBIT_LEFT = "orbit_left"
    ORBIT_RIGHT = "orbit_right"
    HANDHELD = "handheld"
    STEADICAM = "steadicam"
    WHIP_PAN = "whip_pan"
    VERTIGO = "vertigo"               # Dolly zoom
    REVEAL = "reveal"                 # Move to reveal
    FOLLOW = "follow"


class LensType(str, Enum):
    """Lens focal lengths"""
    ULTRA_WIDE = "14mm"
    WIDE = "24mm"
    STANDARD_WIDE = "35mm"
    STANDARD = "50mm"
    PORTRAIT = "85mm"
    TELEPHOTO = "135mm"
    LONG_TELEPHOTO = "200mm"
    MACRO = "macro"
    ANAMORPHIC = "anamorphic"


class LightingStyle(str, Enum):
    """Cinematic lighting setups"""
    NATURAL = "natural_light"
    GOLDEN_HOUR = "golden_hour"
    BLUE_HOUR = "blue_hour"
    HIGH_KEY = "high_key"
    LOW_KEY = "low_key"
    REMBRANDT = "rembrandt"
    SPLIT = "split_lighting"
    BUTTERFLY = "butterfly_lighting"
    LOOP = "loop_lighting"
    BACKLIT = "backlit"
    RIM_LIGHT = "rim_light"
    NEON = "neon_lighting"
    MOONLIGHT = "moonlight"
    CANDLELIGHT = "candlelight"
    FIRELIGHT = "firelight"
    STUDIO = "studio_lighting"
    DRAMATIC = "dramatic_lighting"
    SOFT = "soft_diffused"


class ColorGrade(str, Enum):
    """Color grading styles"""
    NATURAL = "natural"
    CINEMATIC = "cinematic"
    BLOCKBUSTER = "blockbuster"
    FILM_NOIR = "film_noir"
    VINTAGE = "vintage"
    DESATURATED = "desaturated"
    WARM = "warm_tones"
    COOL = "cool_tones"
    ORANGE_TEAL = "orange_teal"
    BLADE_RUNNER = "blade_runner"
    MATRIX = "matrix_green"
    SEPIA = "sepia"
    BLACK_WHITE = "black_and_white"
    HIGH_CONTRAST = "high_contrast"
    MUTED = "muted_colors"
    VIBRANT = "vibrant"


class Mood(str, Enum):
    """Emotional mood/atmosphere"""
    EPIC = "epic"
    INTIMATE = "intimate"
    TENSE = "tense"
    PEACEFUL = "peaceful"
    MYSTERIOUS = "mysterious"
    DRAMATIC = "dramatic"
    ROMANTIC = "romantic"
    MELANCHOLIC = "melancholic"
    TRIUMPHANT = "triumphant"
    OMINOUS = "ominous"
    WHIMSICAL = "whimsical"
    NOSTALGIC = "nostalgic"
    ENERGETIC = "energetic"
    SERENE = "serene"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CinematicShot:
    """Complete cinematic shot specification"""
    shot_number: int
    shot_type: ShotType
    camera_angle: CameraAngle
    camera_movement: CameraMovement
    
    # Composition
    subject_placement: str         # Rule of thirds, centered, etc.
    foreground: Optional[str] = None
    midground: Optional[str] = None
    background: Optional[str] = None
    
    # Technical
    lens: LensType = LensType.STANDARD
    depth_of_field: str = "shallow"  # shallow, medium, deep
    focus_target: str = "subject"
    
    # Lighting
    lighting: LightingStyle = LightingStyle.CINEMATIC
    key_light_direction: str = "45 degrees camera left"
    
    # Color
    color_grade: ColorGrade = ColorGrade.CINEMATIC
    
    # Mood
    mood: Mood = Mood.DRAMATIC
    
    # Action
    action_description: str = ""
    
    # Duration (for video)
    suggested_duration: float = 3.0
    
    def to_prompt_segment(self) -> str:
        """Convert to detailed prompt text"""
        return f"""Shot {self.shot_number}: {self.shot_type.value.replace('_', ' ').title()}
Camera Angle: {self.camera_angle.value.replace('_', ' ')}
Camera Movement: {self.camera_movement.value.replace('_', ' ')}
Lens: {self.lens.value}, {self.depth_of_field} depth of field, focus on {self.focus_target}
Lighting: {self.lighting.value.replace('_', ' ')}, key light from {self.key_light_direction}
Color Grade: {self.color_grade.value.replace('_', ' ')}
Mood: {self.mood.value}
Composition: {self.subject_placement}
Action: {self.action_description}"""


@dataclass
class StoryBeat:
    """Story structure beat"""
    beat_type: str  # setup, build, turn, payoff
    description: str
    emotional_note: str
    shots: List[CinematicShot] = field(default_factory=list)


@dataclass
class EnhancedPrompt:
    """Complete 8K enhanced prompt package"""
    original_prompt: str
    enhanced_prompt: str
    
    # Technical specs
    resolution: str = "8K"
    aspect_ratio: str = "16:9"
    
    # Shot breakdown
    shots: List[CinematicShot] = field(default_factory=list)
    
    # Story structure
    story_beats: List[StoryBeat] = field(default_factory=list)
    
    # Grid prompt (for 3x3 contact sheet)
    grid_prompt: Optional[str] = None
    
    # Individual frame prompts
    frame_prompts: List[str] = field(default_factory=list)
    
    # Metadata
    style: str = "Cinematic"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "original_prompt": self.original_prompt,
            "enhanced_prompt": self.enhanced_prompt,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "shot_count": len(self.shots),
            "story_beats": len(self.story_beats),
            "grid_prompt": self.grid_prompt,
            "frame_prompts": self.frame_prompts,
            "style": self.style
        }


# =============================================================================
# 8K PROMPT ENHANCER SERVICE
# =============================================================================

class PromptEnhancer8K:
    """
    ★★★★★★★★★★ 8K ULTRA-DETAILED PROMPT ENHANCER ★★★★★★★★★★
    
    Creates extremely detailed cinematic prompts with:
    - 8K resolution specifications
    - Complete camera angles and movements
    - Professional lighting setups
    - Color grading presets
    - Story structure (4-beat emotional arc)
    - 3x3 contact sheet generation
    - Per-frame detailed prompts
    """
    
    # 8K Quality Keywords
    QUALITY_8K = [
        "8K resolution", "ultra high definition", "extreme detail",
        "photorealistic", "hyperrealistic", "RAW photo quality",
        "professional photography", "cinema quality", "masterpiece",
        "incredibly detailed", "sharp focus", "HDR", "high dynamic range",
        "studio quality", "award winning", "National Geographic quality"
    ]
    
    # Texture/Detail Keywords
    TEXTURE_DETAIL = [
        "natural skin texture", "subtle imperfections", "visible pores",
        "fine hair detail", "fabric texture visible", "material authenticity",
        "realistic surface detail", "subsurface scattering", "micro details",
        "environmental detail", "atmospheric particles", "dust motes in light"
    ]
    
    # Cinematic Keywords
    CINEMATIC_KEYWORDS = [
        "cinematic composition", "film still", "movie frame",
        "professional color grading", "anamorphic lens flare",
        "cinematic lighting", "Hollywood production value",
        "film grain texture", "professional cinematography"
    ]
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=120.0)
    
    async def enhance_prompt(
        self,
        prompt: str,
        style: str = "Cinematic",
        shot_count: int = 9,
        include_story: bool = True,
        resolution: str = "8K"
    ) -> EnhancedPrompt:
        """
        Enhance a simple prompt to 8K ultra-detailed cinematic quality.
        
        Args:
            prompt: Original simple prompt
            style: Visual style (Cinematic, Anime, etc.)
            shot_count: Number of shots to generate (default 9 for 3x3 grid)
            include_story: Whether to add story structure
            resolution: Target resolution (8K, 4K, etc.)
            
        Returns:
            EnhancedPrompt with full cinematic breakdown
        """
        logger.info(f"Enhancing prompt to {resolution}: {prompt[:50]}...")
        
        # Build the enhanced base prompt
        enhanced_base = self._build_8k_base(prompt, style, resolution)
        
        # Generate story structure if requested
        story_beats = []
        if include_story:
            story_beats = await self._generate_story_beats(prompt)
        
        # Generate shot breakdown
        shots = self._generate_shot_breakdown(prompt, shot_count, story_beats)
        
        # Generate grid prompt (for 3x3 contact sheet)
        grid_prompt = self._build_grid_prompt(prompt, shots, style)
        
        # Generate individual frame prompts
        frame_prompts = [
            self._build_frame_prompt(prompt, shot, style, resolution)
            for shot in shots
        ]
        
        return EnhancedPrompt(
            original_prompt=prompt,
            enhanced_prompt=enhanced_base,
            resolution=resolution,
            shots=shots,
            story_beats=story_beats,
            grid_prompt=grid_prompt,
            frame_prompts=frame_prompts,
            style=style
        )
    
    def _build_8k_base(self, prompt: str, style: str, resolution: str) -> str:
        """Build 8K quality base prompt"""
        quality = ", ".join(self.QUALITY_8K[:6])
        texture = ", ".join(self.TEXTURE_DETAIL[:4])
        cinematic = ", ".join(self.CINEMATIC_KEYWORDS[:4])
        
        return f"""Ultra-realistic {resolution} cinematic {style.lower()} visualization of {prompt}.

{quality}.
{texture}.
{cinematic}.

Shot on professional cinema camera with anamorphic lens.
Natural volumetric lighting with clear key light and rim separation.
Film-inspired color grade, high dynamic range, subtle film grain.
Grounded realism, accurate proportions, no distortion.
Perfect composition following rule of thirds."""
    
    def _generate_shot_breakdown(
        self,
        prompt: str,
        shot_count: int,
        story_beats: List[StoryBeat]
    ) -> List[CinematicShot]:
        """Generate complete shot breakdown"""
        
        # Standard 9-shot breakdown (3x3 grid)
        if shot_count == 9:
            return self._standard_9_shot_breakdown(prompt)
        
        # Custom shot count
        shots = []
        shot_types = list(ShotType)
        angles = list(CameraAngle)
        movements = list(CameraMovement)
        
        for i in range(shot_count):
            shot = CinematicShot(
                shot_number=i + 1,
                shot_type=shot_types[i % len(shot_types)],
                camera_angle=angles[i % len(angles)],
                camera_movement=movements[i % len(movements)],
                subject_placement="Rule of thirds" if i % 2 == 0 else "Centered",
                action_description=f"Scene {i+1} of: {prompt}"
            )
            shots.append(shot)
        
        return shots
    
    def _standard_9_shot_breakdown(self, prompt: str) -> List[CinematicShot]:
        """Standard 9-shot cinematic breakdown (3x3 grid)"""
        return [
            # Row 1: Establishing Context
            CinematicShot(
                shot_number=1,
                shot_type=ShotType.ELS,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC,
                subject_placement="Subject small in vast environment, centered",
                lens=LensType.WIDE,
                depth_of_field="deep",
                lighting=LightingStyle.NATURAL,
                mood=Mood.EPIC,
                action_description=f"Establishing shot: {prompt}",
                suggested_duration=4.0
            ),
            CinematicShot(
                shot_number=2,
                shot_type=ShotType.LS,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_movement=CameraMovement.PUSH_IN,
                subject_placement="Full body visible, rule of thirds left",
                lens=LensType.STANDARD_WIDE,
                depth_of_field="medium",
                lighting=LightingStyle.CINEMATIC,
                mood=Mood.DRAMATIC,
                action_description=f"Full view: {prompt}",
                suggested_duration=3.0
            ),
            CinematicShot(
                shot_number=3,
                shot_type=ShotType.MLS,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_movement=CameraMovement.TRACKING,
                subject_placement="Knees up framing, rule of thirds right",
                lens=LensType.STANDARD,
                depth_of_field="medium",
                lighting=LightingStyle.CINEMATIC,
                mood=Mood.DRAMATIC,
                action_description=f"American shot: {prompt}",
                suggested_duration=3.0
            ),
            
            # Row 2: Core Coverage
            CinematicShot(
                shot_number=4,
                shot_type=ShotType.MS,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_movement=CameraMovement.ORBIT_LEFT,
                subject_placement="Waist up, centered with breathing room",
                lens=LensType.STANDARD,
                depth_of_field="shallow",
                lighting=LightingStyle.REMBRANDT,
                mood=Mood.INTIMATE,
                action_description=f"Medium shot: {prompt}",
                suggested_duration=3.0
            ),
            CinematicShot(
                shot_number=5,
                shot_type=ShotType.MCU,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_movement=CameraMovement.PUSH_IN,
                subject_placement="Chest up, intimate framing",
                lens=LensType.PORTRAIT,
                depth_of_field="shallow",
                focus_target="eyes",
                lighting=LightingStyle.SOFT,
                mood=Mood.INTIMATE,
                action_description=f"Medium close-up: {prompt}",
                suggested_duration=3.0
            ),
            CinematicShot(
                shot_number=6,
                shot_type=ShotType.CU,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC,
                subject_placement="Face filling frame, eyes on upper third",
                lens=LensType.PORTRAIT,
                depth_of_field="very shallow",
                focus_target="eyes",
                lighting=LightingStyle.BUTTERFLY,
                mood=Mood.INTIMATE,
                action_description=f"Close-up: {prompt}",
                suggested_duration=2.5
            ),
            
            # Row 3: Details & Angles
            CinematicShot(
                shot_number=7,
                shot_type=ShotType.ECU,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC,
                subject_placement="Macro detail, key feature filling frame",
                lens=LensType.MACRO,
                depth_of_field="extremely shallow",
                focus_target="key detail",
                lighting=LightingStyle.SOFT,
                mood=Mood.INTIMATE,
                action_description=f"Extreme close-up detail: {prompt}",
                suggested_duration=2.0
            ),
            CinematicShot(
                shot_number=8,
                shot_type=ShotType.LS,
                camera_angle=CameraAngle.LOW_ANGLE,
                camera_movement=CameraMovement.CRANE_UP,
                subject_placement="Subject towering above camera, heroic",
                lens=LensType.WIDE,
                depth_of_field="medium",
                lighting=LightingStyle.DRAMATIC,
                mood=Mood.TRIUMPHANT,
                action_description=f"Low angle heroic: {prompt}",
                suggested_duration=3.0
            ),
            CinematicShot(
                shot_number=9,
                shot_type=ShotType.LS,
                camera_angle=CameraAngle.HIGH_ANGLE,
                camera_movement=CameraMovement.CRANE_DOWN,
                subject_placement="Subject below camera, full context visible",
                lens=LensType.WIDE,
                depth_of_field="deep",
                lighting=LightingStyle.NATURAL,
                mood=Mood.EPIC,
                action_description=f"High angle overview: {prompt}",
                suggested_duration=3.0
            ),
        ]
    
    async def _generate_story_beats(self, prompt: str) -> List[StoryBeat]:
        """Generate 4-beat story structure from prompt"""
        return [
            StoryBeat(
                beat_type="setup",
                description=f"Establishing the world and {prompt}",
                emotional_note="Curiosity, intrigue"
            ),
            StoryBeat(
                beat_type="build",
                description=f"Developing tension or interest in {prompt}",
                emotional_note="Rising anticipation"
            ),
            StoryBeat(
                beat_type="turn",
                description=f"Key moment or revelation in {prompt}",
                emotional_note="Surprise, impact"
            ),
            StoryBeat(
                beat_type="payoff",
                description=f"Resolution or climax of {prompt}",
                emotional_note="Satisfaction, completion"
            ),
        ]
    
    def _build_grid_prompt(
        self,
        prompt: str,
        shots: List[CinematicShot],
        style: str
    ) -> str:
        """Build 3x3 contact sheet grid prompt"""
        
        quality = ", ".join(self.QUALITY_8K[:4])
        
        shot_descriptions = []
        for shot in shots[:9]:
            desc = f"{shot.shot_number}. {shot.shot_type.value.replace('_', ' ').upper()}: {shot.action_description}"
            shot_descriptions.append(desc)
        
        grid_layout = """
**Row 1 (Establishing):**
1. Extreme Long Shot - Subject small in vast environment
2. Long Shot - Full body/form visible
3. Medium Long Shot - Knees up / 3/4 view

**Row 2 (Core Coverage):**
4. Medium Shot - Waist up, action focus
5. Medium Close-Up - Chest up, intimate
6. Close-Up - Face/front detail

**Row 3 (Details & Angles):**
7. Extreme Close-Up - Macro detail (eyes, hands, texture)
8. Low Angle Shot - Looking up, heroic/imposing
9. High Angle Shot - Looking down, overview
"""
        
        return f"""Professional 3x3 cinematic storyboard grid for: {prompt}

{quality}, {style} style.

{grid_layout}

Global Requirements:
- Same subject in all 9 frames
- Consistent clothing, lighting, and color grading
- Realistic depth of field per shot type
- Photorealistic textures throughout
- Cinematic camera behavior
- Each panel clearly labeled with shot type

Create a single cohesive image containing all 9 shots in a 3x3 grid format."""
    
    def _build_frame_prompt(
        self,
        base_prompt: str,
        shot: CinematicShot,
        style: str,
        resolution: str
    ) -> str:
        """Build individual frame prompt with full 8K detail"""
        
        quality = ", ".join(self.QUALITY_8K)
        texture = ", ".join(self.TEXTURE_DETAIL)
        
        return f"""Ultra-realistic {resolution} cinematic {style.lower()} frame.

SUBJECT: {base_prompt}

SHOT TYPE: {shot.shot_type.value.replace('_', ' ').title()}
CAMERA ANGLE: {shot.camera_angle.value.replace('_', ' ')}
CAMERA MOVEMENT: {shot.camera_movement.value.replace('_', ' ')} (implied motion)

LENS: {shot.lens.value} cinema lens
DEPTH OF FIELD: {shot.depth_of_field}
FOCUS: Sharp focus on {shot.focus_target}

LIGHTING: {shot.lighting.value.replace('_', ' ')}
Key light: {shot.key_light_direction}
Rim light for separation, fill light for shadow detail

COLOR GRADE: {shot.color_grade.value.replace('_', ' ')}
High dynamic range, film-inspired tones, subtle grain

COMPOSITION: {shot.subject_placement}
Foreground: {shot.foreground or 'Environmental elements'}
Background: {shot.background or 'Contextual environment, softly blurred'}

MOOD/ATMOSPHERE: {shot.mood.value}

ACTION: {shot.action_description}

TECHNICAL QUALITY:
{quality}

TEXTURE DETAIL:
{texture}

Grounded realism, accurate proportions, no distortion, professional cinematography."""
    
    def enhance_for_character(
        self,
        character_description: str,
        environment: str,
        outfit: str,
        age_ethnicity: str,
        expression: str = "intentional, focused",
        style: str = "Cinematic"
    ) -> str:
        """
        Build foundational character prompt per nano-banana1.txt template.
        
        This is the BASE image prompt for character consistency.
        """
        return f"""Ultra-realistic waist-up cinematic portrait of {character_description} in {environment}.

Wearing {outfit}.

{age_ethnicity}, natural skin texture and subtle imperfections.

Facing the camera with {expression} expression.

Cinematic lighting with clear key light and rim separation.

Shot on 50mm cinema lens, shallow depth of field, softly blurred background.

Film-inspired color grade, high dynamic range, subtle grain.

Grounded realism, accurate proportions, no distortion.

{style} style, 8K resolution, photorealistic, masterpiece quality."""
    
    async def generate_story_storyboard(
        self,
        synopsis: str,
        base_character: str,
        style: str = "Cinematic"
    ) -> EnhancedPrompt:
        """
        Director's Cut: Generate full storyboard from story synopsis.
        
        This is Version 3 from nano-banana1.txt - the most powerful mode.
        
        Args:
            synopsis: Short story description
            base_character: Character description for consistency
            style: Visual style
            
        Returns:
            EnhancedPrompt with story-driven shots
        """
        logger.info(f"Generating story storyboard: {synopsis[:50]}...")
        
        # Generate story-aware shots via LLM
        shots = await self._generate_story_shots_llm(synopsis, base_character, style)
        
        # Build story beats
        story_beats = await self._generate_story_beats(synopsis)
        
        # Build grid prompt
        grid_prompt = self._build_story_grid_prompt(synopsis, base_character, shots, style)
        
        # Build frame prompts
        frame_prompts = [
            self._build_story_frame_prompt(synopsis, base_character, shot, style)
            for shot in shots
        ]
        
        return EnhancedPrompt(
            original_prompt=synopsis,
            enhanced_prompt=f"Story storyboard for: {synopsis}",
            shots=shots,
            story_beats=story_beats,
            grid_prompt=grid_prompt,
            frame_prompts=frame_prompts,
            style=style
        )
    
    async def _generate_story_shots_llm(
        self,
        synopsis: str,
        base_character: str,
        style: str
    ) -> List[CinematicShot]:
        """Use LLM to generate story-specific shots"""
        
        system_prompt = f"""You are an award-winning cinematographer creating a 9-shot storyboard.

Story Synopsis: {synopsis}
Character: {base_character}
Style: {style}

Create 9 shots that tell this story with a clear emotional arc:
1-2: Setup/establishing
3-4: Build tension/interest
5-6: Turn/key moment
7-9: Payoff/resolution

For each shot, specify:
- Shot type (ELS, LS, MLS, MS, MCU, CU, ECU, Low Angle, High Angle)
- Camera angle
- Camera movement
- Action description
- Mood

Return as JSON array."""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "http://localhost:1234/v1/chat/completions",
                    json={
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Create 9 shots for: {synopsis}"}
                        ],
                        "temperature": 0.8
                    }
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    match = re.search(r'\[[\s\S]*\]', content)
                    if match:
                        shots_data = json.loads(match.group())
                        return self._parse_llm_shots(shots_data)
        except Exception as e:
            logger.warning(f"LLM shot generation failed: {e}")
        
        # Fallback to standard breakdown
        return self._standard_9_shot_breakdown(synopsis)
    
    def _parse_llm_shots(self, shots_data: List[Dict]) -> List[CinematicShot]:
        """Parse LLM-generated shots into CinematicShot objects"""
        shots = []
        
        shot_type_map = {
            "els": ShotType.ELS,
            "ls": ShotType.LS,
            "mls": ShotType.MLS,
            "ms": ShotType.MS,
            "mcu": ShotType.MCU,
            "cu": ShotType.CU,
            "ecu": ShotType.ECU,
            "low": ShotType.LS,
            "high": ShotType.LS,
        }
        
        for i, data in enumerate(shots_data[:9]):
            shot_type_str = data.get("shot_type", "ms").lower().replace(" ", "_").replace("angle", "")
            shot_type = shot_type_map.get(shot_type_str.split("_")[0], ShotType.MS)
            
            angle = CameraAngle.EYE_LEVEL
            if "low" in data.get("camera_angle", "").lower():
                angle = CameraAngle.LOW_ANGLE
            elif "high" in data.get("camera_angle", "").lower():
                angle = CameraAngle.HIGH_ANGLE
            
            shot = CinematicShot(
                shot_number=i + 1,
                shot_type=shot_type,
                camera_angle=angle,
                camera_movement=CameraMovement.STATIC,
                subject_placement="Rule of thirds",
                action_description=data.get("action", data.get("description", f"Shot {i+1}"))
            )
            shots.append(shot)
        
        return shots
    
    def _build_story_grid_prompt(
        self,
        synopsis: str,
        base_character: str,
        shots: List[CinematicShot],
        style: str
    ) -> str:
        """Build story-driven grid prompt"""
        
        shot_list = "\n".join([
            f"{s.shot_number}. {s.shot_type.value.replace('_', ' ').upper()}: {s.action_description}"
            for s in shots
        ])
        
        return f"""Professional 3x3 cinematic storyboard grid.

STORY: {synopsis}
CHARACTER: {base_character}
STYLE: {style}

SHOTS:
{shot_list}

REQUIREMENTS:
- Same character in all 9 frames
- Consistent appearance, clothing, lighting
- Story progression visible across frames
- Photorealistic 8K quality
- Cinematic color grading
- Each panel labeled with shot number and type

Create ONE single image containing all 9 shots in a 3x3 grid."""
    
    def _build_story_frame_prompt(
        self,
        synopsis: str,
        base_character: str,
        shot: CinematicShot,
        style: str
    ) -> str:
        """Build story-driven individual frame prompt"""
        
        return f"""8K cinematic {style} frame from story: {synopsis}

CHARACTER: {base_character}

SHOT {shot.shot_number}: {shot.shot_type.value.replace('_', ' ').title()}
Camera: {shot.camera_angle.value.replace('_', ' ')}, {shot.camera_movement.value.replace('_', ' ')}
Lens: {shot.lens.value}, {shot.depth_of_field} depth of field

ACTION: {shot.action_description}
MOOD: {shot.mood.value}

QUALITY: Ultra-realistic, 8K resolution, photorealistic, hyperdetailed,
natural skin texture, visible fabric texture, atmospheric depth,
cinematic lighting with key and rim light, film grain, HDR.

Consistent character appearance throughout sequence."""


# =============================================================================
# SINGLETON
# =============================================================================

_prompt_enhancer: Optional[PromptEnhancer8K] = None

def get_prompt_enhancer_8k() -> PromptEnhancer8K:
    global _prompt_enhancer
    if _prompt_enhancer is None:
        _prompt_enhancer = PromptEnhancer8K()
    return _prompt_enhancer
