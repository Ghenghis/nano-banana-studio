"""
Nano Banana Studio Pro - Audio Processing Worker
=================================================
Handles audio analysis, beat detection, and mixing.
"""

import os
import json
import asyncio
import subprocess
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import struct
import wave

import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio-worker")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/outputs"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/data/uploads"))

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class AudioAnalyzer:
    """Audio analysis using FFmpeg and basic DSP"""
    
    @staticmethod
    def get_ffmpeg_path() -> str:
        return os.getenv("FFMPEG_PATH", "ffmpeg")
    
    @staticmethod
    def get_ffprobe_path() -> str:
        return os.getenv("FFPROBE_PATH", "ffprobe")
    
    @classmethod
    def get_duration(cls, audio_path: str) -> float:
        """Get audio duration in seconds"""
        cmd = [
            cls.get_ffprobe_path(),
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0.0
    
    @classmethod
    def extract_waveform(cls, audio_path: str, sample_rate: int = 22050) -> List[float]:
        """Extract normalized waveform data"""
        temp_wav = str(OUTPUT_DIR / f"temp_{hashlib.md5(audio_path.encode()).hexdigest()}.wav")
        
        # Convert to WAV with specific sample rate
        cmd = [
            cls.get_ffmpeg_path(),
            "-i", audio_path,
            "-ac", "1",  # Mono
            "-ar", str(sample_rate),
            "-f", "wav",
            "-y", temp_wav
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        # Read WAV file
        samples = []
        try:
            with wave.open(temp_wav, 'rb') as wav:
                n_frames = wav.getnframes()
                frames = wav.readframes(n_frames)
                
                # Convert bytes to samples
                fmt = f"<{n_frames}h"  # Little-endian shorts
                raw_samples = struct.unpack(fmt, frames)
                
                # Normalize to -1.0 to 1.0
                max_val = 32768.0
                samples = [s / max_val for s in raw_samples]
        finally:
            if Path(temp_wav).exists():
                Path(temp_wav).unlink()
        
        return samples
    
    @classmethod
    def detect_beats_simple(
        cls, 
        samples: List[float], 
        sample_rate: int = 22050,
        hop_length: int = 512
    ) -> Tuple[List[float], float]:
        """Simple beat detection using energy-based onset detection"""
        
        # Calculate energy in windows
        window_size = hop_length * 2
        energies = []
        
        for i in range(0, len(samples) - window_size, hop_length):
            window = samples[i:i + window_size]
            energy = sum(s * s for s in window) / window_size
            energies.append(energy)
        
        if not energies:
            return [], 120.0
        
        # Calculate moving average
        avg_window = 8
        avg_energies = []
        for i in range(len(energies)):
            start = max(0, i - avg_window)
            end = min(len(energies), i + avg_window)
            avg = sum(energies[start:end]) / (end - start)
            avg_energies.append(avg)
        
        # Find peaks (beats)
        beats = []
        threshold_multiplier = 1.3
        min_beat_interval = int(0.25 * sample_rate / hop_length)  # 240 BPM max
        last_beat_idx = -min_beat_interval
        
        for i in range(1, len(energies) - 1):
            if (energies[i] > energies[i-1] and 
                energies[i] > energies[i+1] and
                energies[i] > avg_energies[i] * threshold_multiplier and
                i - last_beat_idx >= min_beat_interval):
                
                beat_time = i * hop_length / sample_rate
                beats.append(beat_time)
                last_beat_idx = i
        
        # Calculate BPM
        if len(beats) >= 2:
            intervals = [beats[i+1] - beats[i] for i in range(len(beats) - 1)]
            avg_interval = sum(intervals) / len(intervals)
            bpm = 60.0 / avg_interval if avg_interval > 0 else 120.0
            bpm = max(60, min(200, bpm))  # Clamp to reasonable range
        else:
            bpm = 120.0
        
        return beats, round(bpm)
    
    @classmethod
    def calculate_energy_curve(
        cls,
        samples: List[float],
        sample_rate: int = 22050,
        window_ms: int = 250
    ) -> List[float]:
        """Calculate energy curve over time"""
        window_samples = int(sample_rate * window_ms / 1000)
        
        energy_curve = []
        for i in range(0, len(samples), window_samples):
            window = samples[i:i + window_samples]
            if window:
                energy = sum(s * s for s in window) / len(window)
                energy_curve.append(energy)
        
        # Normalize
        if energy_curve:
            max_energy = max(energy_curve)
            if max_energy > 0:
                energy_curve = [e / max_energy for e in energy_curve]
        
        return energy_curve
    
    @classmethod
    def detect_sections(
        cls,
        energy_curve: List[float],
        duration: float
    ) -> List[Dict[str, Any]]:
        """Detect song sections based on energy changes"""
        
        if len(energy_curve) < 4:
            return [{"name": "main", "start": 0, "end": duration, "energy": "medium"}]
        
        # Calculate average energy in chunks
        chunk_size = max(1, len(energy_curve) // 8)
        chunks = []
        
        for i in range(0, len(energy_curve), chunk_size):
            chunk = energy_curve[i:i + chunk_size]
            avg_energy = sum(chunk) / len(chunk) if chunk else 0
            chunks.append(avg_energy)
        
        # Classify sections
        sections = []
        time_per_chunk = duration / len(chunks)
        
        section_names = ["intro", "verse1", "chorus1", "verse2", "chorus2", "bridge", "chorus3", "outro"]
        
        for i, avg_energy in enumerate(chunks):
            start_time = i * time_per_chunk
            end_time = min((i + 1) * time_per_chunk, duration)
            
            if avg_energy < 0.3:
                energy_level = "low"
            elif avg_energy < 0.6:
                energy_level = "medium"
            else:
                energy_level = "high"
            
            section_name = section_names[i] if i < len(section_names) else f"section{i+1}"
            
            sections.append({
                "name": section_name,
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "energy": energy_level,
                "avg_energy": round(avg_energy, 3)
            })
        
        return sections
    
    @classmethod
    async def analyze_audio(cls, audio_path: str) -> Dict[str, Any]:
        """Complete audio analysis"""
        
        logger.info(f"Analyzing audio: {audio_path}")
        
        # Get duration
        duration = cls.get_duration(audio_path)
        
        # Extract waveform
        samples = cls.extract_waveform(audio_path)
        
        # Detect beats
        beats, bpm = cls.detect_beats_simple(samples)
        
        # Calculate energy curve
        energy_curve = cls.calculate_energy_curve(samples)
        
        # Detect sections
        sections = cls.detect_sections(energy_curve, duration)
        
        return {
            "duration": round(duration, 2),
            "bpm": bpm,
            "beat_count": len(beats),
            "beats": [round(b, 3) for b in beats[:200]],  # Limit for response size
            "energy_curve": [round(e, 3) for e in energy_curve],
            "sections": sections,
            "sample_rate": 22050
        }


class AudioMixer:
    """Audio mixing operations using FFmpeg"""
    
    @staticmethod
    def get_ffmpeg_path() -> str:
        return os.getenv("FFMPEG_PATH", "ffmpeg")
    
    @classmethod
    async def mix_tracks(
        cls,
        tracks: List[Dict[str, Any]],
        output_path: str,
        mode: str = "layer"
    ) -> Dict[str, Any]:
        """Mix multiple audio tracks"""
        
        if not tracks:
            raise ValueError("No tracks provided")
        
        # Build FFmpeg command
        inputs = []
        filter_parts = []
        
        for i, track in enumerate(tracks):
            path = track.get("path")
            volume = track.get("volume", 1.0)
            
            if not path or not Path(path).exists():
                continue
            
            inputs.append(f'-i "{path}"')
            filter_parts.append(f"[{i}:a]volume={volume}[a{i}]")
        
        if not inputs:
            raise ValueError("No valid audio files")
        
        num_tracks = len(inputs)
        
        if mode == "layer":
            # Mix all tracks together
            mix_inputs = "".join(f"[a{i}]" for i in range(num_tracks))
            filter_parts.append(f"{mix_inputs}amix=inputs={num_tracks}:duration=longest[out]")
        elif mode == "sequence":
            # Concatenate tracks
            concat_inputs = "".join(f"[a{i}]" for i in range(num_tracks))
            filter_parts.append(f"{concat_inputs}concat=n={num_tracks}:v=0:a=1[out]")
        elif mode == "ducking":
            # Background music ducks under main audio
            if num_tracks >= 2:
                filter_parts.append(f"[a0][a1]sidechaincompress=threshold=0.02:ratio=4:attack=200:release=1000[out]")
            else:
                filter_parts.append("[a0]anull[out]")
        else:
            filter_parts.append(f"[a0]anull[out]")
        
        filter_complex = ";".join(filter_parts)
        
        cmd = f'{cls.get_ffmpeg_path()} {" ".join(inputs)} -filter_complex "{filter_complex}" -map "[out]" -c:a aac -b:a 192k -y "{output_path}"'
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg mix failed: {stderr.decode()}")
        
        if Path(output_path).exists():
            return {
                "output_path": output_path,
                "tracks_mixed": num_tracks,
                "mode": mode,
                "file_size": Path(output_path).stat().st_size
            }
        
        raise Exception("Output file not created")


class AudioWorker:
    """Audio processing job worker"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.analyzer = AudioAnalyzer()
        self.mixer = AudioMixer()
    
    async def connect(self):
        self.redis = redis.from_url(REDIS_URL)
        await self.redis.ping()
        logger.info("Connected to Redis")
    
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
    
    async def process_job(self, job_data: Dict) -> Dict:
        job_id = job_data.get("job_id")
        job_type = job_data.get("job_type")
        params = job_data.get("params", {})
        
        logger.info(f"Processing job: {job_id} ({job_type})")
        
        try:
            if job_type == "analyze":
                audio_path = params.get("audio_path")
                result = await self.analyzer.analyze_audio(audio_path)
                return {"status": "completed", "result": result}
            
            elif job_type == "mix":
                tracks = params.get("tracks", [])
                mode = params.get("mode", "layer")
                output_path = str(OUTPUT_DIR / f"{job_id}_mixed.mp3")
                result = await self.mixer.mix_tracks(tracks, output_path, mode)
                return {"status": "completed", "result": result}
            
            else:
                raise Exception(f"Unknown job type: {job_type}")
                
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run(self):
        await self.connect()
        self.running = True
        
        logger.info("Audio worker started, waiting for jobs...")
        
        while self.running:
            try:
                result = await self.redis.blpop("audio_jobs", timeout=5)
                
                if result:
                    _, job_json = result
                    job_data = json.loads(job_json)
                    
                    result = await self.process_job(job_data)
                    
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
        logger.info("Audio worker stopped")
    
    def stop(self):
        self.running = False


async def main():
    worker = AudioWorker()
    try:
        await worker.run()
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
