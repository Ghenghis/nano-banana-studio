"""
Nano Banana Studio Pro - Multi-AI Podcast Service
===================================================
Generate podcasts with 3+ AI personalities conversing naturally.

Features:
- Multiple distinct AI personalities (host, experts, guests)
- Natural conversation flow with turn-taking
- Interruptions, reactions ("mmhmm", "exactly!")
- Topic-driven dialogue generation
- Multiple voice synthesis providers
- 15-60+ minute episode generation
- Video podcast with AI avatars (optional)

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
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import httpx
import random

logger = logging.getLogger("podcast-service")


# =============================================================================
# CONFIGURATION
# =============================================================================

class PodcastConfig:
    """Podcast service configuration"""
    LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    XTTS_SERVICE_URL = os.getenv("XTTS_SERVICE_URL", "http://localhost:8003")
    
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/outputs"))
    PODCASTS_DIR = Path(os.getenv("PODCASTS_DIR", "/app/data/podcasts"))
    
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")


# =============================================================================
# DATA MODELS
# =============================================================================

class PersonalityType(str, Enum):
    HOST = "host"
    EXPERT = "expert"
    CREATIVE = "creative"
    SKEPTIC = "skeptic"
    ENTHUSIAST = "enthusiast"
    ANALYST = "analyst"


@dataclass
class PodcastPersonality:
    """AI personality for podcast"""
    name: str
    personality_type: PersonalityType
    description: str
    voice_id: str  # ElevenLabs voice ID or Edge TTS voice
    voice_provider: str = "edge"  # edge, elevenlabs, xtts
    
    # Personality traits
    speaking_style: str = "conversational"
    quirks: List[str] = field(default_factory=list)  # e.g., ["says 'you know'", "laughs often"]
    expertise: List[str] = field(default_factory=list)
    
    # Voice characteristics
    speaking_rate: float = 1.0
    pitch_adjustment: str = "+0Hz"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.personality_type.value,
            "description": self.description,
            "voice_id": self.voice_id,
            "speaking_style": self.speaking_style,
            "quirks": self.quirks,
            "expertise": self.expertise
        }


@dataclass
class DialogueTurn:
    """Single turn in podcast conversation"""
    speaker: str
    text: str
    emotion: str = "neutral"
    audio_path: Optional[str] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "speaker": self.speaker,
            "text": self.text,
            "emotion": self.emotion,
            "duration": self.duration
        }


@dataclass
class PodcastEpisode:
    """Complete podcast episode"""
    id: str
    title: str
    topic: str
    personalities: List[PodcastPersonality]
    dialogue: List[DialogueTurn]
    
    duration: float = 0.0
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "topic": self.topic,
            "personalities": [p.to_dict() for p in self.personalities],
            "dialogue": [d.to_dict() for d in self.dialogue],
            "duration": self.duration,
            "audio_path": self.audio_path,
            "video_path": self.video_path,
            "created_at": self.created_at.isoformat()
        }


# =============================================================================
# PRESET PERSONALITIES
# =============================================================================

PRESET_PERSONALITIES = {
    "alex_host": PodcastPersonality(
        name="Alex",
        personality_type=PersonalityType.HOST,
        description="Curious and engaging podcast host who asks great questions",
        voice_id="en-US-GuyNeural",
        speaking_style="warm and welcoming",
        quirks=["says 'fascinating' often", "summarizes key points"],
        expertise=["interviewing", "storytelling"]
    ),
    "dr_sarah": PodcastPersonality(
        name="Dr. Sarah",
        personality_type=PersonalityType.EXPERT,
        description="Academic expert who explains complex topics clearly",
        voice_id="en-US-JennyNeural",
        speaking_style="professional but approachable",
        quirks=["cites studies", "uses analogies"],
        expertise=["research", "science", "technology"]
    ),
    "marcus_creative": PodcastPersonality(
        name="Marcus",
        personality_type=PersonalityType.CREATIVE,
        description="Creative thinker who brings humor and unexpected perspectives",
        voice_id="en-US-ChristopherNeural",
        speaking_style="energetic and witty",
        quirks=["makes jokes", "uses pop culture references"],
        expertise=["creativity", "entertainment", "trends"]
    ),
    "nina_skeptic": PodcastPersonality(
        name="Nina",
        personality_type=PersonalityType.SKEPTIC,
        description="Devil's advocate who challenges assumptions",
        voice_id="en-US-AriaNeural",
        speaking_style="thoughtful and probing",
        quirks=["plays devil's advocate", "asks 'but what about...'"],
        expertise=["critical thinking", "debate"]
    )
}


# =============================================================================
# REACTIONS & FILLER WORDS
# =============================================================================

REACTIONS = {
    "agreement": ["Mmhmm.", "Exactly!", "Right.", "Absolutely.", "Yeah, totally.", "That's a great point."],
    "surprise": ["Oh wow!", "Really?", "No way!", "That's fascinating!", "I had no idea!"],
    "thinking": ["Hmm...", "Interesting...", "Let me think about that...", "That's a good question..."],
    "disagreement": ["Well, I'm not so sure...", "That's one perspective, but...", "I see it differently..."],
    "laughter": ["Ha!", "*laughs*", "That's funny!", "*chuckles*"]
}


# =============================================================================
# PODCAST SERVICE
# =============================================================================

class PodcastService:
    """
    Multi-AI podcast generation service.
    Creates natural conversations between 3+ AI personalities.
    """
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=120.0)
        PodcastConfig.PODCASTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _generate_id(self) -> str:
        """Generate unique episode ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rand_hash = hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
        return f"podcast_{timestamp}_{rand_hash}"
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.9,
        max_tokens: int = 4000
    ) -> str:
        """Call LLM for dialogue generation"""
        providers = [
            ("lm_studio", f"{PodcastConfig.LM_STUDIO_URL}/chat/completions", None),
            ("ollama", f"{PodcastConfig.OLLAMA_URL}/v1/chat/completions", None),
        ]
        
        if PodcastConfig.OPENAI_API_KEY:
            providers.append(("openai", "https://api.openai.com/v1/chat/completions", PodcastConfig.OPENAI_API_KEY))
        
        for provider_name, url, api_key in providers:
            try:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                payload = {
                    "model": "gpt-4o" if provider_name == "openai" else "local-model",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                response = await self.http_client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                    
            except Exception as e:
                continue
        
        raise Exception("All LLM providers failed")
    
    async def _synthesize_speech_edge(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        rate: str = "+0%"
    ) -> float:
        """Synthesize speech using Edge TTS"""
        try:
            import edge_tts
        except ImportError:
            raise ImportError("edge-tts required: pip install edge-tts")
        
        communicate = edge_tts.Communicate(text, voice_id, rate=rate)
        await communicate.save(output_path)
        
        # Get duration
        duration = self._get_audio_duration(output_path)
        return duration
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using ffprobe"""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
        return 0.0
    
    async def generate_conversation(
        self,
        topic: str,
        personalities: List[PodcastPersonality],
        num_turns: int = 20,
        include_reactions: bool = True
    ) -> List[DialogueTurn]:
        """Generate multi-party conversation"""
        personality_descriptions = "\n".join([
            f"- {p.name} ({p.personality_type.value}): {p.description}. Style: {p.speaking_style}. Quirks: {', '.join(p.quirks)}"
            for p in personalities
        ])
        
        system_prompt = f"""You are generating a natural podcast conversation between multiple hosts.

PERSONALITIES:
{personality_descriptions}

RULES:
1. Each person speaks 1-3 sentences per turn
2. Include natural reactions like "Mmhmm", "Exactly!", "That's interesting..."
3. Have speakers build on each other's points
4. Include occasional interruptions and overlap
5. The HOST should guide the conversation and ask questions
6. Other speakers should share their unique perspectives

Generate {num_turns} turns of natural dialogue about: {topic}

Return JSON array:
[
    {{"speaker": "NAME", "text": "What they say...", "emotion": "neutral/excited/thoughtful/amused"}},
    ...
]"""
        
        response = await self._call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a {num_turns}-turn conversation about: {topic}"}
        ])
        
        # Parse JSON
        import re
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                turns_data = json.loads(json_match.group())
                
                dialogue = []
                for turn in turns_data:
                    # Occasionally add reactions
                    if include_reactions and random.random() < 0.15 and dialogue:
                        # Add a reaction from someone else
                        reactor = random.choice([p for p in personalities if p.name != turn.get("speaker")])
                        reaction_type = random.choice(list(REACTIONS.keys()))
                        reaction = random.choice(REACTIONS[reaction_type])
                        dialogue.append(DialogueTurn(
                            speaker=reactor.name,
                            text=reaction,
                            emotion="agreement" if reaction_type == "agreement" else "neutral"
                        ))
                    
                    dialogue.append(DialogueTurn(
                        speaker=turn.get("speaker", personalities[0].name),
                        text=turn.get("text", ""),
                        emotion=turn.get("emotion", "neutral")
                    ))
                
                return dialogue
        except Exception as e:
            logger.error(f"Failed to parse conversation: {e}")
        
        # Fallback
        return [
            DialogueTurn(speaker=personalities[0].name, text=f"Welcome to our discussion about {topic}!"),
            DialogueTurn(speaker=personalities[1].name, text="Thanks for having me! This is such an interesting topic."),
            DialogueTurn(speaker=personalities[2].name, text="I'm excited to share my thoughts on this.")
        ]
    
    async def synthesize_episode(
        self,
        dialogue: List[DialogueTurn],
        personalities: List[PodcastPersonality],
        output_dir: Path
    ) -> Tuple[str, float]:
        """Synthesize all dialogue turns to audio"""
        personality_map = {p.name: p for p in personalities}
        audio_files = []
        total_duration = 0.0
        
        for i, turn in enumerate(dialogue):
            personality = personality_map.get(turn.speaker, personalities[0])
            
            output_file = output_dir / f"turn_{i:04d}.mp3"
            
            try:
                # Add small pause between turns
                duration = await self._synthesize_speech_edge(
                    text=turn.text,
                    voice_id=personality.voice_id,
                    output_path=str(output_file),
                    rate=f"+{int((personality.speaking_rate - 1) * 50)}%"
                )
                
                turn.audio_path = str(output_file)
                turn.duration = duration
                total_duration += duration
                audio_files.append(str(output_file))
                
            except Exception as e:
                logger.error(f"Failed to synthesize turn {i}: {e}")
        
        # Concatenate all audio files
        final_output = output_dir / "episode.mp3"
        
        # Create concat file
        concat_file = output_dir / "concat.txt"
        with open(concat_file, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
        
        # Concatenate with ffmpeg
        cmd = [
            PodcastConfig.FFMPEG_PATH, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(final_output)
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        return str(final_output), total_duration

    
    async def generate_episode(
        self,
        topic: str,
        title: str,
        target_duration: int = 15,  # minutes
        personalities: Optional[List[PodcastPersonality]] = None,
        synthesize_audio: bool = True
    ) -> PodcastEpisode:
        """
        Generate a complete podcast episode.
        
        Args:
            topic: Main topic for discussion
            title: Episode title
            target_duration: Target duration in minutes (15-60+)
            personalities: List of AI personalities (default: 3-person panel)
            synthesize_audio: Whether to generate audio
            
        Returns:
            Complete PodcastEpisode with dialogue and audio
        """
        logger.info(f"Generating {target_duration}-minute podcast: {title}")
        
        episode_id = self._generate_id()
        
        # Use default personalities if not provided
        if personalities is None:
            personalities = [
                PRESET_PERSONALITIES["alex_host"],
                PRESET_PERSONALITIES["dr_sarah"],
                PRESET_PERSONALITIES["marcus_creative"]
            ]
        
        # Calculate turns needed
        # Average turn = ~10-15 seconds
        turns_needed = int(target_duration * 5)  # ~5 turns per minute
        turns_needed = max(10, min(turns_needed, 300))  # 10-300 turns
        
        logger.info(f"Generating {turns_needed} dialogue turns...")
        
        # Generate conversation in chunks for long podcasts
        all_dialogue = []
        turns_per_chunk = 30
        previous_context = ""
        
        for chunk_start in range(0, turns_needed, turns_per_chunk):
            chunk_turns = min(turns_per_chunk, turns_needed - chunk_start)
            
            if previous_context:
                chunk_topic = f"{topic}\n\nContinuing from: {previous_context}"
            else:
                chunk_topic = topic
            
            dialogue_chunk = await self.generate_conversation(
                topic=chunk_topic,
                personalities=personalities,
                num_turns=chunk_turns
            )
            
            all_dialogue.extend(dialogue_chunk)
            
            # Update context for next chunk
            if dialogue_chunk:
                last_turns = dialogue_chunk[-3:] if len(dialogue_chunk) >= 3 else dialogue_chunk
                previous_context = " ".join([t.text for t in last_turns])
            
            await asyncio.sleep(0.5)  # Rate limit
        
        # Create output directory
        output_dir = PodcastConfig.PODCASTS_DIR / episode_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Synthesize audio
        audio_path = None
        total_duration = 0.0
        
        if synthesize_audio:
            logger.info("Synthesizing audio...")
            audio_path, total_duration = await self.synthesize_episode(
                dialogue=all_dialogue,
                personalities=personalities,
                output_dir=output_dir
            )
        else:
            # Estimate duration
            total_duration = len(all_dialogue) * 10  # ~10 sec per turn
        
        # Create episode
        episode = PodcastEpisode(
            id=episode_id,
            title=title,
            topic=topic,
            personalities=personalities,
            dialogue=all_dialogue,
            duration=total_duration,
            audio_path=audio_path
        )
        
        # Save metadata
        metadata_path = output_dir / "episode.json"
        metadata_path.write_text(json.dumps(episode.to_dict(), indent=2))
        
        logger.info(f"Episode generated: {title} ({total_duration/60:.1f} minutes, {len(all_dialogue)} turns)")
        
        return episode
    
    async def generate_debate(
        self,
        topic: str,
        position_a: str,
        position_b: str,
        title: str,
        target_duration: int = 20
    ) -> PodcastEpisode:
        """Generate a debate-style podcast between two opposing views"""
        
        personalities = [
            PodcastPersonality(
                name="Moderator",
                personality_type=PersonalityType.HOST,
                description="Neutral debate moderator",
                voice_id="en-US-GuyNeural",
                speaking_style="professional and fair"
            ),
            PodcastPersonality(
                name="Advocate A",
                personality_type=PersonalityType.EXPERT,
                description=f"Argues for: {position_a}",
                voice_id="en-US-JennyNeural",
                speaking_style="passionate and well-reasoned"
            ),
            PodcastPersonality(
                name="Advocate B",
                personality_type=PersonalityType.SKEPTIC,
                description=f"Argues for: {position_b}",
                voice_id="en-US-AriaNeural",
                speaking_style="analytical and persuasive"
            )
        ]
        
        debate_topic = f"""
DEBATE TOPIC: {topic}

Position A ({personalities[1].name}): {position_a}
Position B ({personalities[2].name}): {position_b}

The moderator will guide the debate, give each side equal time, and ask probing questions.
"""
        
        return await self.generate_episode(
            topic=debate_topic,
            title=title,
            target_duration=target_duration,
            personalities=personalities
        )
    
    async def generate_interview(
        self,
        guest_name: str,
        guest_expertise: str,
        topic: str,
        target_duration: int = 30
    ) -> PodcastEpisode:
        """Generate an interview-style podcast"""
        
        personalities = [
            PRESET_PERSONALITIES["alex_host"],
            PodcastPersonality(
                name=guest_name,
                personality_type=PersonalityType.EXPERT,
                description=f"Expert in {guest_expertise}",
                voice_id="en-US-JennyNeural",
                speaking_style="knowledgeable and engaging",
                expertise=[guest_expertise]
            )
        ]
        
        return await self.generate_episode(
            topic=f"Interview with {guest_name} about {topic}",
            title=f"Interview: {guest_name} on {topic}",
            target_duration=target_duration,
            personalities=personalities
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# =============================================================================
# SINGLETON
# =============================================================================

_podcast_service: Optional[PodcastService] = None

def get_podcast_service() -> PodcastService:
    """Get or create podcast service instance"""
    global _podcast_service
    if _podcast_service is None:
        _podcast_service = PodcastService()
    return _podcast_service
