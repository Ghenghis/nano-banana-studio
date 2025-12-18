"""
Nano Banana Studio Pro - Video Processing Worker
=================================================
Handles FFmpeg video operations in background queue.
"""

import os
import json
import asyncio
import subprocess
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video-worker")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/outputs"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "/app/data/temp"))

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class VideoJob:
    job_id: str
    job_type: str
    params: Dict[str, Any]
    created_at: str
    status: str = "queued"
    progress: float = 0.0
    result: Optional[Dict] = None
    error: Optional[str] = None


class FFmpegProcessor:
    """FFmpeg video processing operations"""
    
    @staticmethod
    def get_ffmpeg_path() -> str:
        """Get FFmpeg binary path"""
        return os.getenv("FFMPEG_PATH", "ffmpeg")
    
    @staticmethod
    def get_ffprobe_path() -> str:
        """Get FFprobe binary path"""
        return os.getenv("FFPROBE_PATH", "ffprobe")
    
    @classmethod
    def probe_media(cls, filepath: str) -> Dict[str, Any]:
        """Get media file information"""
        cmd = [
            cls.get_ffprobe_path(),
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        raise Exception(f"FFprobe failed: {result.stderr}")
    
    @classmethod
    def build_kenburns_filter(
        cls,
        width: int,
        height: int,
        duration: float,
        fps: int = 30,
        zoom_start: float = 1.0,
        zoom_end: float = 1.1,
        pan_x: float = 0,
        pan_y: float = 0
    ) -> str:
        """Build Ken Burns effect filter"""
        frames = int(duration * fps)
        
        # Calculate zoom progression
        zoom_delta = zoom_end - zoom_start
        zoom_expr = f"{zoom_start}+({zoom_delta}*on/{frames})"
        
        # Calculate pan (centered with slight movement)
        x_expr = f"iw/2-(iw/zoom/2)+({pan_x}*iw*on/{frames})"
        y_expr = f"ih/2-(ih/zoom/2)+({pan_y}*ih*on/{frames})"
        
        return f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s={width}x{height}:fps={fps}"
    
    @classmethod
    def build_transition_filter(
        cls,
        transition_type: str,
        duration: float,
        offset: float
    ) -> str:
        """Build transition filter for xfade"""
        valid_transitions = [
            "fade", "wipeleft", "wiperight", "wipeup", "wipedown",
            "slideleft", "slideright", "slideup", "slidedown",
            "circlecrop", "rectcrop", "distance", "fadeblack",
            "fadewhite", "radial", "smoothleft", "smoothright",
            "smoothup", "smoothdown", "circleopen", "circleclose",
            "vertopen", "vertclose", "horzopen", "horzclose",
            "dissolve", "pixelize", "diagtl", "diagtr", "diagbl",
            "diagbr", "hlslice", "hrslice", "vuslice", "vdslice",
            "hblur", "fadegrays", "wipetl", "wipetr", "wipebl",
            "wipebr", "squeezeh", "squeezev", "zoomin", "fadefast",
            "fadeslow"
        ]
        
        if transition_type not in valid_transitions:
            transition_type = "dissolve"
        
        return f"xfade=transition={transition_type}:duration={duration}:offset={offset}"
    
    @classmethod
    async def assemble_video(
        cls,
        job_id: str,
        scenes: List[Dict],
        audio_path: Optional[str],
        output_path: str,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        preset: str = "medium",
        crf: int = 23,
        transition_type: str = "dissolve",
        transition_duration: float = 0.5,
        ken_burns: bool = True,
        color_grading: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assemble video from scenes with transitions"""
        
        logger.info(f"[{job_id}] Starting video assembly: {len(scenes)} scenes")
        
        # Build input list
        inputs = []
        filter_parts = []
        
        # Process each scene
        for i, scene in enumerate(scenes):
            image_path = scene.get("image_path")
            duration = scene.get("duration", 5.0)
            
            if not image_path or not Path(image_path).exists():
                logger.warning(f"[{job_id}] Scene {i}: Image not found: {image_path}")
                continue
            
            # Add input
            inputs.append(f'-loop 1 -t {duration} -i "{image_path}"')
            
            # Build scale and Ken Burns filter
            filter_chain = f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
            
            if ken_burns:
                # Alternate zoom direction
                zoom_start = 1.0 if i % 2 == 0 else 1.1
                zoom_end = 1.1 if i % 2 == 0 else 1.0
                pan_x = 0.02 if i % 4 < 2 else -0.02
                pan_y = 0.01 if i % 2 == 0 else -0.01
                
                kb_filter = cls.build_kenburns_filter(
                    width, height, duration, fps,
                    zoom_start, zoom_end, pan_x, pan_y
                )
                filter_chain += f",{kb_filter}"
            
            filter_chain += f"[v{i}]"
            filter_parts.append(filter_chain)
        
        if not filter_parts:
            raise Exception("No valid scenes to process")
        
        # Build transition chain
        num_scenes = len(filter_parts)
        if num_scenes > 1:
            current_output = "[v0]"
            cumulative_duration = scenes[0].get("duration", 5.0)
            
            for i in range(1, num_scenes):
                scene_duration = scenes[i].get("duration", 5.0)
                offset = cumulative_duration - transition_duration
                
                output_label = "[vout]" if i == num_scenes - 1 else f"[vt{i}]"
                
                xfade = cls.build_transition_filter(
                    transition_type, transition_duration, offset
                )
                filter_parts.append(f"{current_output}[v{i}]{xfade}{output_label}")
                
                current_output = output_label
                cumulative_duration += scene_duration - transition_duration
        else:
            filter_parts.append("[v0]copy[vout]")
        
        # Add color grading if specified
        if color_grading:
            grading_filters = {
                "cinematic_warm": "colortemperature=temperature=6500,eq=saturation=0.9:contrast=1.15",
                "cinematic_cool": "colortemperature=temperature=8000,eq=saturation=0.85:contrast=1.2",
                "vintage": "eq=saturation=0.8:contrast=0.95,colorize=hue=30:saturation=0.1",
                "black_white": "eq=saturation=0:contrast=1.3",
                "neon": "eq=saturation=1.4:contrast=1.25:brightness=0.05"
            }
            
            if color_grading in grading_filters:
                filter_parts.append(f"[vout]{grading_filters[color_grading]}[vout_graded]")
                final_video = "[vout_graded]"
            else:
                final_video = "[vout]"
        else:
            final_video = "[vout]"
        
        # Build filter complex
        filter_complex = ";".join(filter_parts)
        
        # Build FFmpeg command
        cmd_parts = [cls.get_ffmpeg_path()]
        cmd_parts.extend(inputs[0].split())  # Add first input
        
        for inp in inputs[1:]:
            cmd_parts.extend(inp.split())
        
        # Add audio if present
        if audio_path and Path(audio_path).exists():
            cmd_parts.extend(["-i", audio_path])
            audio_index = len(inputs)
            map_audio = f"-map {audio_index}:a"
        else:
            map_audio = "-an"
        
        # Add filter complex and output settings
        cmd_parts.extend([
            "-filter_complex", filter_complex,
            "-map", final_video.strip("[]"),
        ])
        
        if map_audio != "-an":
            cmd_parts.extend(["-map", f"{len(inputs)}:a"])
        else:
            cmd_parts.append("-an")
        
        cmd_parts.extend([
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-y", output_path
        ])
        
        if audio_path:
            cmd_parts.extend(["-c:a", "aac", "-b:a", "192k"])
        
        # Execute FFmpeg
        logger.info(f"[{job_id}] Executing FFmpeg...")
        cmd = " ".join(cmd_parts)
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg failed: {stderr.decode()}")
        
        # Get output file info
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            probe_info = cls.probe_media(output_path)
            duration = float(probe_info.get("format", {}).get("duration", 0))
            
            return {
                "video_path": output_path,
                "duration": duration,
                "file_size": file_size,
                "scene_count": num_scenes,
                "resolution": f"{width}x{height}",
                "fps": fps
            }
        
        raise Exception("Output file not created")


class VideoWorker:
    """Video processing job worker"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.processor = FFmpegProcessor()
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = redis.from_url(REDIS_URL)
        await self.redis.ping()
        logger.info("Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
    
    async def process_job(self, job_data: Dict) -> Dict:
        """Process a single video job"""
        job_id = job_data.get("job_id")
        job_type = job_data.get("job_type")
        params = job_data.get("params", {})
        
        logger.info(f"Processing job: {job_id} ({job_type})")
        
        try:
            if job_type == "assemble":
                result = await self.processor.assemble_video(
                    job_id=job_id,
                    scenes=params.get("scenes", []),
                    audio_path=params.get("audio_path"),
                    output_path=str(OUTPUT_DIR / f"{job_id}_output.mp4"),
                    width=params.get("width", 1920),
                    height=params.get("height", 1080),
                    fps=params.get("fps", 30),
                    preset=params.get("preset", "medium"),
                    crf=params.get("crf", 23),
                    transition_type=params.get("transition", "dissolve"),
                    transition_duration=params.get("transition_duration", 0.5),
                    ken_burns=params.get("ken_burns", True),
                    color_grading=params.get("color_grading")
                )
                return {"status": "completed", "result": result}
            
            else:
                raise Exception(f"Unknown job type: {job_type}")
                
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run(self):
        """Main worker loop"""
        await self.connect()
        self.running = True
        
        logger.info("Video worker started, waiting for jobs...")
        
        while self.running:
            try:
                # Wait for job from queue
                result = await self.redis.blpop("video_jobs", timeout=5)
                
                if result:
                    _, job_json = result
                    job_data = json.loads(job_json)
                    
                    # Process job
                    result = await self.process_job(job_data)
                    
                    # Store result
                    await self.redis.setex(
                        f"job_result:{job_data['job_id']}",
                        3600,
                        json.dumps(result)
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)
        
        await self.disconnect()
        logger.info("Video worker stopped")
    
    def stop(self):
        """Stop the worker"""
        self.running = False


async def main():
    """Main entry point"""
    worker = VideoWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
