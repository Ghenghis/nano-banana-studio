"""
Nano Banana Studio Pro - Whisper Speech Recognition Service
============================================================
Local speech-to-text using OpenAI Whisper models.

Models:
    - whisper-large-v3: Best accuracy, 99 languages
    - whisper-large-v3-turbo: 8x faster, same quality
    - faster-whisper: CTranslate2 optimized

Install:
    pip install openai-whisper
    # OR for faster inference:
    pip install faster-whisper

Usage:
    service = WhisperService()
    result = await service.transcribe("audio.mp3")
    print(result.text)
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import tempfile

logger = logging.getLogger("whisper-service")

# Check dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Try faster-whisper first (recommended)
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

# Fallback to openai-whisper
try:
    import whisper
    OPENAI_WHISPER_AVAILABLE = True
except ImportError:
    OPENAI_WHISPER_AVAILABLE = False


class WhisperModelSize(str, Enum):
    """Available Whisper model sizes"""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"
    LARGE_V3_TURBO = "large-v3-turbo"


@dataclass
class WhisperConfig:
    """Whisper configuration"""
    model: str = "large-v3-turbo"
    
    # Transcription settings
    language: Optional[str] = None  # Auto-detect if None
    task: str = "transcribe"  # "transcribe" or "translate"
    
    # Performance
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type: str = "float16"  # float16, int8, int8_float16
    beam_size: int = 5
    best_of: int = 5
    
    # VAD (Voice Activity Detection)
    vad_filter: bool = True
    vad_threshold: float = 0.5
    
    # Output
    word_timestamps: bool = True
    
    # Paths
    cache_dir: str = "G:/models/speech"


@dataclass
class TranscriptionSegment:
    """A segment of transcription"""
    id: int
    start: float
    end: float
    text: str
    words: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result"""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    language_probability: float
    duration: float
    model: str
    processed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_srt(self) -> str:
        """Convert to SRT subtitle format"""
        lines = []
        for i, seg in enumerate(self.segments, 1):
            start = self._format_timestamp(seg.start)
            end = self._format_timestamp(seg.end)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(seg.text.strip())
            lines.append("")
        return "\n".join(lines)
    
    def to_vtt(self) -> str:
        """Convert to WebVTT format"""
        lines = ["WEBVTT", ""]
        for seg in self.segments:
            start = self._format_timestamp(seg.start, vtt=True)
            end = self._format_timestamp(seg.end, vtt=True)
            lines.append(f"{start} --> {end}")
            lines.append(seg.text.strip())
            lines.append("")
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float, vtt: bool = False) -> str:
        """Format timestamp for subtitles"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        sep = "." if vtt else ","
        return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{ms:03d}"


class WhisperService:
    """
    Local Whisper speech recognition service.
    
    Features:
        - Multi-language transcription (99 languages)
        - Translation to English
        - Word-level timestamps
        - VAD filtering
        - Subtitle export (SRT, VTT)
    
    Example:
        service = WhisperService()
        
        # Basic transcription
        result = await service.transcribe("speech.mp3")
        print(result.text)
        
        # With language hint
        result = await service.transcribe("speech.mp3", language="es")
        
        # Translate to English
        result = await service.translate("foreign_speech.mp3")
        
        # Export subtitles
        srt = result.to_srt()
        with open("subtitles.srt", "w") as f:
            f.write(srt)
    """
    
    def __init__(self, config: Optional[WhisperConfig] = None):
        """Initialize Whisper service"""
        self.config = config or WhisperConfig()
        self._model = None
        self._use_faster_whisper = FASTER_WHISPER_AVAILABLE
        
        if not FASTER_WHISPER_AVAILABLE and not OPENAI_WHISPER_AVAILABLE:
            raise ImportError(
                "No Whisper implementation found. Install one:\n"
                "  pip install faster-whisper  # Recommended\n"
                "  pip install openai-whisper  # Alternative"
            )
        
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
        
        backend = "faster-whisper" if self._use_faster_whisper else "openai-whisper"
        logger.info(f"WhisperService initialized (backend: {backend})")
    
    def _load_model(self):
        """Load Whisper model"""
        if self._model is not None:
            return self._model
        
        logger.info(f"Loading Whisper model: {self.config.model}")
        
        if self._use_faster_whisper:
            self._model = WhisperModel(
                self.config.model,
                device=self.config.device,
                compute_type=self.config.compute_type,
                download_root=self.config.cache_dir
            )
        else:
            self._model = whisper.load_model(
                self.config.model,
                device=self.config.device,
                download_root=self.config.cache_dir
            )
        
        logger.info("Model loaded")
        return self._model
    
    async def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        word_timestamps: Optional[bool] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.
        
        Args:
            audio: Path to audio file or audio bytes
            language: Language code (e.g., "en", "es", "ja")
            word_timestamps: Include word-level timing
            **kwargs: Additional model parameters
            
        Returns:
            TranscriptionResult with text and segments
        """
        model = self._load_model()
        
        # Handle bytes input
        audio_path = audio
        temp_file = None
        
        if isinstance(audio, bytes):
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_file.write(audio)
            temp_file.close()
            audio_path = temp_file.name
        
        audio_path = str(audio_path)
        
        language = language or self.config.language
        word_timestamps = word_timestamps if word_timestamps is not None else self.config.word_timestamps
        
        logger.info(f"Transcribing: {Path(audio_path).name}")
        
        try:
            loop = asyncio.get_event_loop()
            
            if self._use_faster_whisper:
                result = await loop.run_in_executor(
                    None,
                    lambda: self._transcribe_faster_whisper(
                        audio_path, language, word_timestamps, **kwargs
                    )
                )
            else:
                result = await loop.run_in_executor(
                    None,
                    lambda: self._transcribe_openai_whisper(
                        audio_path, language, word_timestamps, **kwargs
                    )
                )
            
            return result
            
        finally:
            if temp_file:
                os.unlink(temp_file.name)
    
    def _transcribe_faster_whisper(
        self,
        audio_path: str,
        language: Optional[str],
        word_timestamps: bool,
        **kwargs
    ) -> TranscriptionResult:
        """Transcribe using faster-whisper"""
        segments_gen, info = self._model.transcribe(
            audio_path,
            language=language,
            beam_size=self.config.beam_size,
            best_of=self.config.best_of,
            word_timestamps=word_timestamps,
            vad_filter=self.config.vad_filter,
            vad_parameters={"threshold": self.config.vad_threshold},
            **kwargs
        )
        
        segments = []
        full_text = []
        
        for i, seg in enumerate(segments_gen):
            words = None
            if word_timestamps and seg.words:
                words = [
                    {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                    for w in seg.words
                ]
            
            segments.append(TranscriptionSegment(
                id=i,
                start=seg.start,
                end=seg.end,
                text=seg.text,
                words=words,
                confidence=seg.avg_logprob if hasattr(seg, 'avg_logprob') else None
            ))
            full_text.append(seg.text)
        
        return TranscriptionResult(
            text=" ".join(full_text).strip(),
            segments=segments,
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
            model=self.config.model
        )
    
    def _transcribe_openai_whisper(
        self,
        audio_path: str,
        language: Optional[str],
        word_timestamps: bool,
        **kwargs
    ) -> TranscriptionResult:
        """Transcribe using openai-whisper"""
        result = self._model.transcribe(
            audio_path,
            language=language,
            word_timestamps=word_timestamps,
            **kwargs
        )
        
        segments = []
        for i, seg in enumerate(result["segments"]):
            words = None
            if word_timestamps and "words" in seg:
                words = seg["words"]
            
            segments.append(TranscriptionSegment(
                id=i,
                start=seg["start"],
                end=seg["end"],
                text=seg["text"],
                words=words
            ))
        
        # Get audio duration
        import librosa
        duration = librosa.get_duration(path=audio_path)
        
        return TranscriptionResult(
            text=result["text"].strip(),
            segments=segments,
            language=result.get("language", "unknown"),
            language_probability=1.0,
            duration=duration,
            model=self.config.model
        )
    
    async def translate(
        self,
        audio: Union[str, Path, bytes],
        **kwargs
    ) -> TranscriptionResult:
        """
        Translate audio to English.
        
        Args:
            audio: Path to audio file
            **kwargs: Additional parameters
            
        Returns:
            TranscriptionResult with English translation
        """
        if self._use_faster_whisper:
            return await self.transcribe(audio, task="translate", **kwargs)
        else:
            model = self._load_model()
            
            audio_path = str(audio)
            if isinstance(audio, bytes):
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_file.write(audio)
                temp_file.close()
                audio_path = temp_file.name
            
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: model.transcribe(audio_path, task="translate", **kwargs)
                )
                
                segments = [
                    TranscriptionSegment(
                        id=i,
                        start=s["start"],
                        end=s["end"],
                        text=s["text"]
                    )
                    for i, s in enumerate(result["segments"])
                ]
                
                return TranscriptionResult(
                    text=result["text"].strip(),
                    segments=segments,
                    language="en",
                    language_probability=1.0,
                    duration=0,
                    model=self.config.model
                )
            finally:
                if isinstance(audio, bytes):
                    os.unlink(audio_path)
    
    async def detect_language(
        self,
        audio: Union[str, Path, bytes]
    ) -> Dict[str, Any]:
        """
        Detect language of audio.
        
        Args:
            audio: Path to audio file
            
        Returns:
            Dict with language code and probability
        """
        # Transcribe a small portion
        result = await self.transcribe(audio)
        
        return {
            "language": result.language,
            "probability": result.language_probability,
            "language_name": self._get_language_name(result.language)
        }
    
    def _get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        languages = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
            "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "hi": "Hindi",
            # Add more as needed
        }
        return languages.get(code, code)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        if self._use_faster_whisper:
            return list(self._model.supported_languages) if self._model else []
        else:
            return list(whisper.tokenizer.LANGUAGES.keys())
    
    def unload(self):
        """Unload model to free memory"""
        if self._model is not None:
            del self._model
            self._model = None
            if TORCH_AVAILABLE:
                torch.cuda.empty_cache()
            logger.info("Model unloaded")


# Singleton
_whisper_service: Optional[WhisperService] = None

def get_whisper_service() -> WhisperService:
    """Get or create Whisper service"""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service


# CLI Test
async def _test():
    """Test Whisper service"""
    service = get_whisper_service()
    
    # Create test audio (if you have one)
    test_audio = "test.wav"
    
    if Path(test_audio).exists():
        result = await service.transcribe(test_audio)
        print(f"Language: {result.language}")
        print(f"Text: {result.text}")
        print(f"Segments: {len(result.segments)}")
        
        # Export subtitles
        print("\nSRT Preview:")
        print(result.to_srt()[:500])
    else:
        print("No test audio file found")
        print(f"Supported languages: {len(service.get_supported_languages())}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
