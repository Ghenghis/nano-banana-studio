"""
Nano Banana Studio Pro - MusicGen Local Service
================================================
Local music generation using Meta's MusicGen models.
No API costs, runs entirely on your hardware.

Models:
    - musicgen-small (300M): Fast, 4GB VRAM
    - musicgen-medium (1.5B): Balanced, 6GB VRAM
    - musicgen-large (3.3B): Best quality, 8GB VRAM
    - musicgen-melody (1.5B): Melody conditioning

Install:
    pip install audiocraft torch torchaudio

Usage:
    service = MusicGenService()
    audio = await service.generate("upbeat electronic dance music")
    service.save(audio, "output.wav")
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np

logger = logging.getLogger("musicgen-service")

# Check dependencies
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed")

try:
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
    AUDIOCRAFT_AVAILABLE = True
except ImportError:
    AUDIOCRAFT_AVAILABLE = False
    logger.warning("audiocraft not installed. Run: pip install audiocraft")


class MusicGenModel(str, Enum):
    """Available MusicGen models"""
    SMALL = "facebook/musicgen-small"     # 300M params, fast
    MEDIUM = "facebook/musicgen-medium"   # 1.5B params, balanced
    LARGE = "facebook/musicgen-large"     # 3.3B params, best quality
    MELODY = "facebook/musicgen-melody"   # 1.5B, melody conditioning
    STEREO_SMALL = "facebook/musicgen-stereo-small"
    STEREO_MEDIUM = "facebook/musicgen-stereo-medium"
    STEREO_LARGE = "facebook/musicgen-stereo-large"


@dataclass
class MusicGenConfig:
    """MusicGen configuration"""
    model: str = MusicGenModel.MEDIUM.value
    duration: int = 30  # seconds
    temperature: float = 1.0
    top_k: int = 250
    top_p: float = 0.0
    cfg_coef: float = 3.0  # Classifier-free guidance
    two_step_cfg: bool = False
    extend_stride: int = 18  # For extending beyond max duration
    sample_rate: int = 32000
    channels: int = 1  # 2 for stereo models
    
    # Hardware
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    dtype: str = "float16"  # float16 or float32
    
    # Paths
    cache_dir: str = "G:/models/music"
    output_dir: str = "./outputs/music"


@dataclass
class GeneratedMusic:
    """Generated music result"""
    audio: np.ndarray
    sample_rate: int
    duration: float
    prompt: str
    model: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    melody_conditioned: bool = False
    filepath: Optional[Path] = None


class MusicGenService:
    """
    Local MusicGen service for AI music generation.
    
    Runs entirely on your hardware - no API costs!
    
    Example:
        service = MusicGenService()
        
        # Simple generation
        music = await service.generate("happy upbeat pop song")
        service.save(music, "happy_song.wav")
        
        # With melody conditioning
        music = await service.generate_with_melody(
            "rock version with electric guitars",
            melody_path="reference.wav"
        )
        
        # Long-form generation (extends beyond 30s limit)
        music = await service.generate_long(
            "ambient soundscape for meditation",
            duration=120  # 2 minutes
        )
    """
    
    def __init__(self, config: Optional[MusicGenConfig] = None):
        """
        Initialize MusicGen service.
        
        Args:
            config: MusicGen configuration
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not installed. Run: pip install torch torchaudio")
        
        if not AUDIOCRAFT_AVAILABLE:
            raise ImportError("audiocraft not installed. Run: pip install audiocraft")
        
        self.config = config or MusicGenConfig()
        self._model: Optional[MusicGen] = None
        self._current_model_name: Optional[str] = None
        
        # Ensure directories exist
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MusicGenService initialized (device: {self.config.device})")
    
    def _load_model(self, model_name: str = None) -> MusicGen:
        """Load or switch MusicGen model"""
        model_name = model_name or self.config.model
        
        if self._model is not None and self._current_model_name == model_name:
            return self._model
        
        logger.info(f"Loading MusicGen model: {model_name}")
        
        # Unload previous model
        if self._model is not None:
            del self._model
            torch.cuda.empty_cache()
        
        # Load new model
        self._model = MusicGen.get_pretrained(
            model_name,
            device=self.config.device
        )
        self._current_model_name = model_name
        
        # Configure generation parameters
        self._model.set_generation_params(
            duration=self.config.duration,
            temperature=self.config.temperature,
            top_k=self.config.top_k,
            top_p=self.config.top_p,
            cfg_coef=self.config.cfg_coef,
            two_step_cfg=self.config.two_step_cfg,
            extend_stride=self.config.extend_stride
        )
        
        logger.info(f"Model loaded on {self.config.device}")
        return self._model
    
    async def generate(
        self,
        prompt: str,
        duration: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> GeneratedMusic:
        """
        Generate music from text prompt.
        
        Args:
            prompt: Text description of desired music
            duration: Duration in seconds (max 30 for single generation)
            model: Model to use (defaults to config)
            **kwargs: Additional generation parameters
            
        Returns:
            GeneratedMusic object with audio data
        """
        model_instance = self._load_model(model)
        
        if duration:
            model_instance.set_generation_params(duration=min(duration, 30))
        
        logger.info(f"Generating music: {prompt[:50]}...")
        
        # Run generation in thread pool
        loop = asyncio.get_event_loop()
        wav = await loop.run_in_executor(
            None,
            lambda: model_instance.generate([prompt], progress=True)
        )
        
        # Convert to numpy
        audio = wav[0].cpu().numpy()
        
        result = GeneratedMusic(
            audio=audio,
            sample_rate=model_instance.sample_rate,
            duration=audio.shape[-1] / model_instance.sample_rate,
            prompt=prompt,
            model=self._current_model_name
        )
        
        logger.info(f"Generated {result.duration:.1f}s of audio")
        return result
    
    async def generate_batch(
        self,
        prompts: List[str],
        duration: Optional[int] = None
    ) -> List[GeneratedMusic]:
        """
        Generate multiple tracks in batch.
        
        Args:
            prompts: List of text prompts
            duration: Duration per track
            
        Returns:
            List of GeneratedMusic objects
        """
        model_instance = self._load_model()
        
        if duration:
            model_instance.set_generation_params(duration=min(duration, 30))
        
        logger.info(f"Generating batch of {len(prompts)} tracks...")
        
        loop = asyncio.get_event_loop()
        wavs = await loop.run_in_executor(
            None,
            lambda: model_instance.generate(prompts, progress=True)
        )
        
        results = []
        for i, wav in enumerate(wavs):
            audio = wav.cpu().numpy()
            results.append(GeneratedMusic(
                audio=audio,
                sample_rate=model_instance.sample_rate,
                duration=audio.shape[-1] / model_instance.sample_rate,
                prompt=prompts[i],
                model=self._current_model_name
            ))
        
        return results
    
    async def generate_with_melody(
        self,
        prompt: str,
        melody_path: Union[str, Path],
        duration: Optional[int] = None
    ) -> GeneratedMusic:
        """
        Generate music conditioned on a melody.
        
        Requires musicgen-melody model.
        
        Args:
            prompt: Text description
            melody_path: Path to reference audio file
            duration: Duration in seconds
            
        Returns:
            GeneratedMusic object
        """
        # Load melody model
        model_instance = self._load_model(MusicGenModel.MELODY.value)
        
        if duration:
            model_instance.set_generation_params(duration=min(duration, 30))
        
        # Load melody audio
        melody_path = Path(melody_path)
        if not melody_path.exists():
            raise FileNotFoundError(f"Melody file not found: {melody_path}")
        
        melody_wav, sr = torchaudio.load(str(melody_path))
        
        # Resample if necessary
        if sr != model_instance.sample_rate:
            melody_wav = torchaudio.functional.resample(
                melody_wav, sr, model_instance.sample_rate
            )
        
        # Move to device
        melody_wav = melody_wav.to(self.config.device)
        
        logger.info(f"Generating with melody conditioning: {prompt[:50]}...")
        
        loop = asyncio.get_event_loop()
        wav = await loop.run_in_executor(
            None,
            lambda: model_instance.generate_with_chroma(
                [prompt],
                melody_wav.unsqueeze(0),
                model_instance.sample_rate,
                progress=True
            )
        )
        
        audio = wav[0].cpu().numpy()
        
        return GeneratedMusic(
            audio=audio,
            sample_rate=model_instance.sample_rate,
            duration=audio.shape[-1] / model_instance.sample_rate,
            prompt=prompt,
            model=self._current_model_name,
            melody_conditioned=True
        )
    
    async def generate_long(
        self,
        prompt: str,
        duration: int,
        overlap: int = 5
    ) -> GeneratedMusic:
        """
        Generate long-form music by extending.
        
        Args:
            prompt: Text description
            duration: Total duration in seconds
            overlap: Overlap between segments
            
        Returns:
            GeneratedMusic with full audio
        """
        model_instance = self._load_model()
        segment_duration = 30  # Max per generation
        
        logger.info(f"Generating {duration}s long-form audio...")
        
        segments = []
        remaining = duration
        
        while remaining > 0:
            seg_dur = min(segment_duration, remaining)
            model_instance.set_generation_params(duration=seg_dur)
            
            if not segments:
                # First segment
                loop = asyncio.get_event_loop()
                wav = await loop.run_in_executor(
                    None,
                    lambda: model_instance.generate([prompt], progress=True)
                )
            else:
                # Continue from previous
                # Use last `overlap` seconds as context
                context_samples = int(overlap * model_instance.sample_rate)
                context = segments[-1][:, -context_samples:]
                
                loop = asyncio.get_event_loop()
                wav = await loop.run_in_executor(
                    None,
                    lambda: model_instance.generate_continuation(
                        context.unsqueeze(0),
                        model_instance.sample_rate,
                        [prompt],
                        progress=True
                    )
                )
            
            segments.append(wav[0])
            remaining -= seg_dur
            logger.info(f"  Generated segment, {remaining}s remaining")
        
        # Concatenate with crossfade
        audio = self._crossfade_segments(segments, overlap, model_instance.sample_rate)
        
        return GeneratedMusic(
            audio=audio.cpu().numpy(),
            sample_rate=model_instance.sample_rate,
            duration=audio.shape[-1] / model_instance.sample_rate,
            prompt=prompt,
            model=self._current_model_name
        )
    
    def _crossfade_segments(
        self,
        segments: List[torch.Tensor],
        overlap: int,
        sample_rate: int
    ) -> torch.Tensor:
        """Crossfade audio segments"""
        if len(segments) == 1:
            return segments[0]
        
        overlap_samples = int(overlap * sample_rate)
        
        # Create crossfade weights
        fade_out = torch.linspace(1, 0, overlap_samples)
        fade_in = torch.linspace(0, 1, overlap_samples)
        
        result = segments[0]
        
        for seg in segments[1:]:
            # Apply crossfade
            result_end = result[:, -overlap_samples:] * fade_out
            seg_start = seg[:, :overlap_samples] * fade_in
            
            # Combine
            crossfaded = result_end + seg_start
            result = torch.cat([
                result[:, :-overlap_samples],
                crossfaded,
                seg[:, overlap_samples:]
            ], dim=-1)
        
        return result
    
    def save(
        self,
        music: GeneratedMusic,
        filename: Union[str, Path],
        format: str = "wav"
    ) -> Path:
        """
        Save generated music to file.
        
        Args:
            music: GeneratedMusic object
            filename: Output filename
            format: Audio format (wav, mp3, flac)
            
        Returns:
            Path to saved file
        """
        output_path = Path(self.config.output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to tensor
        audio_tensor = torch.from_numpy(music.audio)
        
        # Use audiocraft's audio_write for quality
        audio_write(
            str(output_path.with_suffix("")),
            audio_tensor,
            music.sample_rate,
            strategy="loudness",
            loudness_compressor=True
        )
        
        # audiocraft adds .wav extension
        final_path = output_path.with_suffix(f".{format}")
        music.filepath = final_path
        
        logger.info(f"Saved to: {final_path}")
        return final_path
    
    def get_device_info(self) -> dict:
        """Get device information"""
        info = {
            "device": self.config.device,
            "cuda_available": torch.cuda.is_available(),
        }
        
        if torch.cuda.is_available():
            info.update({
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB",
                "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1e9:.2f}GB",
            })
        
        return info
    
    def unload_model(self):
        """Unload model to free memory"""
        if self._model is not None:
            del self._model
            self._model = None
            self._current_model_name = None
            torch.cuda.empty_cache()
            logger.info("Model unloaded")


# =============================================================================
# SINGLETON
# =============================================================================

_musicgen_service: Optional[MusicGenService] = None

def get_musicgen_service() -> MusicGenService:
    """Get or create MusicGen service"""
    global _musicgen_service
    if _musicgen_service is None:
        _musicgen_service = MusicGenService()
    return _musicgen_service


# =============================================================================
# CLI TEST
# =============================================================================

async def _test():
    """Test MusicGen service"""
    service = get_musicgen_service()
    
    print(f"Device info: {service.get_device_info()}")
    
    # Generate sample
    music = await service.generate(
        "calm ambient music with soft synths and gentle melody",
        duration=10
    )
    
    print(f"Generated: {music.duration:.1f}s")
    
    # Save
    path = service.save(music, "test_ambient.wav")
    print(f"Saved to: {path}")
    
    service.unload_model()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
