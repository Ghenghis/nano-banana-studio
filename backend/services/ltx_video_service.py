"""
Nano Banana Studio Pro - LTX-Video Service
============================================
Local video generation using Lightricks LTX-Video models.

Models:
    - LTX-Video-0.9.7-distilled: Fast 4-step generation
    - LTX-Video-0.9.5: Original model
    - LTX-Video-GGUF: Quantized for lower VRAM

Requirements:
    pip install diffusers torch accelerate transformers

Usage:
    service = LTXVideoService()
    video = await service.generate("a cat walking on the beach")
    service.save(video, "cat_beach.mp4")
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

logger = logging.getLogger("ltx-video-service")

# Check dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from diffusers import DiffusionPipeline, LTXPipeline, LTXImageToVideoPipeline
    from diffusers.utils import export_to_video
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("diffusers not installed. Run: pip install diffusers")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class LTXModel(str, Enum):
    """Available LTX-Video models"""
    DISTILLED_097 = "Lightricks/LTX-Video-0.9.7-distilled"
    ORIGINAL_095 = "Lightricks/LTX-Video"
    GGUF = "city96/LTX-Video-gguf"


@dataclass
class LTXConfig:
    """LTX-Video configuration"""
    model: str = LTXModel.DISTILLED_097.value
    
    # Generation params
    num_frames: int = 121  # ~5 seconds at 24fps
    height: int = 512
    width: int = 768
    fps: int = 24
    num_inference_steps: int = 8  # 4-8 for distilled, 50 for original
    guidance_scale: float = 3.0
    
    # Hardware
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    dtype: str = "bfloat16"  # bfloat16, float16, or float32
    enable_model_cpu_offload: bool = False
    enable_vae_slicing: bool = True
    enable_vae_tiling: bool = True
    
    # Paths
    cache_dir: str = "G:/models/video"
    output_dir: str = "./outputs/video"


@dataclass
class GeneratedVideo:
    """Generated video result"""
    frames: List[np.ndarray]
    fps: int
    duration: float
    prompt: str
    negative_prompt: Optional[str]
    model: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    seed: Optional[int] = None
    filepath: Optional[Path] = None
    
    @property
    def frame_count(self) -> int:
        return len(self.frames)
    
    @property
    def resolution(self) -> Tuple[int, int]:
        if self.frames:
            return self.frames[0].shape[1], self.frames[0].shape[0]
        return (0, 0)


class LTXVideoService:
    """
    Local LTX-Video service for AI video generation.
    
    Features:
        - Text-to-video generation
        - Image-to-video animation
        - Keyframe control
        - Motion guidance
    
    Example:
        service = LTXVideoService()
        
        # Text to video
        video = await service.generate(
            "A golden retriever running through a meadow, slow motion"
        )
        service.save(video, "dog_meadow.mp4")
        
        # Image to video
        video = await service.animate_image(
            image_path="photo.jpg",
            prompt="the person waves and smiles"
        )
    """
    
    def __init__(self, config: Optional[LTXConfig] = None):
        """Initialize LTX-Video service"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required. Run: pip install torch")
        
        if not DIFFUSERS_AVAILABLE:
            raise ImportError("diffusers required. Run: pip install diffusers")
        
        self.config = config or LTXConfig()
        self._pipeline = None
        self._i2v_pipeline = None
        
        # Ensure directories
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LTXVideoService initialized (device: {self.config.device})")
    
    def _get_dtype(self):
        """Get torch dtype from config"""
        dtype_map = {
            "bfloat16": torch.bfloat16,
            "float16": torch.float16,
            "float32": torch.float32,
        }
        return dtype_map.get(self.config.dtype, torch.bfloat16)
    
    def _load_pipeline(self) -> LTXPipeline:
        """Load text-to-video pipeline"""
        if self._pipeline is not None:
            return self._pipeline
        
        logger.info(f"Loading LTX-Video pipeline: {self.config.model}")
        
        self._pipeline = LTXPipeline.from_pretrained(
            self.config.model,
            torch_dtype=self._get_dtype(),
            cache_dir=self.config.cache_dir
        )
        
        # Optimizations
        if self.config.enable_model_cpu_offload:
            self._pipeline.enable_model_cpu_offload()
        else:
            self._pipeline.to(self.config.device)
        
        if self.config.enable_vae_slicing:
            self._pipeline.vae.enable_slicing()
        
        if self.config.enable_vae_tiling:
            self._pipeline.vae.enable_tiling()
        
        logger.info("Pipeline loaded")
        return self._pipeline
    
    def _load_i2v_pipeline(self) -> LTXImageToVideoPipeline:
        """Load image-to-video pipeline"""
        if self._i2v_pipeline is not None:
            return self._i2v_pipeline
        
        logger.info("Loading LTX Image-to-Video pipeline")
        
        self._i2v_pipeline = LTXImageToVideoPipeline.from_pretrained(
            self.config.model,
            torch_dtype=self._get_dtype(),
            cache_dir=self.config.cache_dir
        )
        
        if self.config.enable_model_cpu_offload:
            self._i2v_pipeline.enable_model_cpu_offload()
        else:
            self._i2v_pipeline.to(self.config.device)
        
        return self._i2v_pipeline
    
    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: Optional[int] = None,
        height: Optional[int] = None,
        width: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> GeneratedVideo:
        """
        Generate video from text prompt.
        
        Args:
            prompt: Text description of video
            negative_prompt: What to avoid
            num_frames: Number of frames (default: 121)
            height: Video height (default: 512)
            width: Video width (default: 768)
            num_inference_steps: Denoising steps (default: 8)
            guidance_scale: CFG scale (default: 3.0)
            seed: Random seed for reproducibility
            
        Returns:
            GeneratedVideo object
        """
        pipeline = self._load_pipeline()
        
        # Use config defaults if not specified
        num_frames = num_frames or self.config.num_frames
        height = height or self.config.height
        width = width or self.config.width
        num_inference_steps = num_inference_steps or self.config.num_inference_steps
        guidance_scale = guidance_scale or self.config.guidance_scale
        
        # Default negative prompt
        if negative_prompt is None:
            negative_prompt = "worst quality, inconsistent motion, blurry, jittery, distorted"
        
        # Set seed
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.config.device).manual_seed(seed)
        
        logger.info(f"Generating video: {prompt[:50]}...")
        logger.info(f"  Frames: {num_frames}, Resolution: {width}x{height}")
        
        # Run generation in thread pool
        loop = asyncio.get_event_loop()
        
        def _generate():
            return pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_frames=num_frames,
                height=height,
                width=width,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                **kwargs
            ).frames[0]
        
        frames = await loop.run_in_executor(None, _generate)
        
        # Convert PIL images to numpy arrays
        if isinstance(frames[0], Image.Image):
            frames = [np.array(f) for f in frames]
        
        duration = len(frames) / self.config.fps
        
        result = GeneratedVideo(
            frames=frames,
            fps=self.config.fps,
            duration=duration,
            prompt=prompt,
            negative_prompt=negative_prompt,
            model=self.config.model,
            seed=seed
        )
        
        logger.info(f"Generated {result.frame_count} frames ({result.duration:.1f}s)")
        return result
    
    async def animate_image(
        self,
        image: Union[str, Path, Image.Image],
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: Optional[int] = None,
        **kwargs
    ) -> GeneratedVideo:
        """
        Animate a static image.
        
        Args:
            image: Path to image or PIL Image
            prompt: Motion description
            negative_prompt: What to avoid
            num_frames: Number of frames
            
        Returns:
            GeneratedVideo object
        """
        pipeline = self._load_i2v_pipeline()
        
        # Load image
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        
        # Resize to match config
        image = image.resize((self.config.width, self.config.height))
        
        num_frames = num_frames or self.config.num_frames
        
        if negative_prompt is None:
            negative_prompt = "worst quality, inconsistent motion, blurry"
        
        logger.info(f"Animating image: {prompt[:50]}...")
        
        loop = asyncio.get_event_loop()
        
        def _animate():
            return pipeline(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_frames=num_frames,
                height=self.config.height,
                width=self.config.width,
                num_inference_steps=self.config.num_inference_steps,
                guidance_scale=self.config.guidance_scale,
                **kwargs
            ).frames[0]
        
        frames = await loop.run_in_executor(None, _animate)
        
        if isinstance(frames[0], Image.Image):
            frames = [np.array(f) for f in frames]
        
        return GeneratedVideo(
            frames=frames,
            fps=self.config.fps,
            duration=len(frames) / self.config.fps,
            prompt=prompt,
            negative_prompt=negative_prompt,
            model=self.config.model
        )
    
    async def generate_with_keyframes(
        self,
        prompts: List[Tuple[int, str]],
        total_frames: int = 121,
        **kwargs
    ) -> GeneratedVideo:
        """
        Generate video with keyframe prompts.
        
        Args:
            prompts: List of (frame_number, prompt) tuples
            total_frames: Total video frames
            
        Returns:
            GeneratedVideo object
        """
        # Sort by frame number
        prompts = sorted(prompts, key=lambda x: x[0])
        
        # Interpolate prompts for each segment
        segments = []
        
        for i, (frame, prompt) in enumerate(prompts):
            next_frame = prompts[i + 1][0] if i + 1 < len(prompts) else total_frames
            segment_frames = next_frame - frame
            
            if segment_frames > 0:
                video = await self.generate(
                    prompt=prompt,
                    num_frames=segment_frames,
                    **kwargs
                )
                segments.append(video.frames)
        
        # Concatenate segments
        all_frames = []
        for seg in segments:
            all_frames.extend(seg)
        
        return GeneratedVideo(
            frames=all_frames,
            fps=self.config.fps,
            duration=len(all_frames) / self.config.fps,
            prompt=str(prompts),
            negative_prompt=None,
            model=self.config.model
        )
    
    def save(
        self,
        video: GeneratedVideo,
        filename: Union[str, Path],
        fps: Optional[int] = None
    ) -> Path:
        """
        Save video to file.
        
        Args:
            video: GeneratedVideo object
            filename: Output filename
            fps: Override FPS
            
        Returns:
            Path to saved file
        """
        output_path = Path(self.config.output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fps = fps or video.fps
        
        # Convert numpy arrays back to PIL for export
        pil_frames = [Image.fromarray(f) if isinstance(f, np.ndarray) else f 
                      for f in video.frames]
        
        export_to_video(pil_frames, str(output_path), fps=fps)
        
        video.filepath = output_path
        logger.info(f"Saved to: {output_path}")
        
        return output_path
    
    def get_device_info(self) -> dict:
        """Get device information"""
        info = {
            "device": self.config.device,
            "cuda_available": torch.cuda.is_available(),
            "model": self.config.model,
        }
        
        if torch.cuda.is_available():
            info.update({
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB",
                "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1e9:.2f}GB",
            })
        
        return info
    
    def unload(self):
        """Unload models to free memory"""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
        
        if self._i2v_pipeline is not None:
            del self._i2v_pipeline
            self._i2v_pipeline = None
        
        torch.cuda.empty_cache()
        logger.info("Models unloaded")


# Singleton
_ltx_service: Optional[LTXVideoService] = None

def get_ltx_service() -> LTXVideoService:
    """Get or create LTX-Video service"""
    global _ltx_service
    if _ltx_service is None:
        _ltx_service = LTXVideoService()
    return _ltx_service


# CLI Test
async def _test():
    """Test LTX-Video service"""
    service = get_ltx_service()
    print(f"Device: {service.get_device_info()}")
    
    video = await service.generate(
        "A serene mountain lake at sunset, gentle ripples on the water",
        num_frames=25,  # Short test
        num_inference_steps=4
    )
    
    print(f"Generated: {video.frame_count} frames, {video.duration:.1f}s")
    
    path = service.save(video, "test_lake.mp4")
    print(f"Saved: {path}")
    
    service.unload()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
