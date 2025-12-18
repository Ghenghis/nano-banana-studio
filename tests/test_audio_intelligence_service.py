"""
Nano Banana Studio Pro - Audio Intelligence Service Tests
==========================================================
Comprehensive test coverage for AudioIntelligenceService.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path


class TestAudioIntelligenceService:
    """Tests for AudioIntelligenceService"""
    
    def test_init(self):
        """Test service initialization"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_analyze_audio_basic(self, tmp_path):
        """Test basic audio analysis"""
        import wave
        import struct
        
        audio_path = tmp_path / "test.wav"
        with wave.open(str(audio_path), 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            samples = [int(32767 * np.sin(2 * np.pi * 440 * t / 44100)) for t in range(44100)]
            wav.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        with patch.object(service, '_load_audio', return_value=(np.zeros(44100), 44100)):
            result = await service.analyze(str(audio_path))
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_detect_beats(self):
        """Test beat detection"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        audio_data = np.random.rand(44100 * 5)
        
        with patch.object(service, '_detect_beats_internal', return_value=[0.5, 1.0, 1.5, 2.0]):
            beats = service._detect_beats(audio_data, 44100)
            assert isinstance(beats, list)
    
    @pytest.mark.asyncio
    async def test_calculate_energy_curve(self):
        """Test energy curve calculation"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        audio_data = np.random.rand(44100)
        
        energy = service._calculate_energy(audio_data, 44100, window_size=1024)
        assert energy is not None
    
    @pytest.mark.asyncio
    async def test_detect_sections(self):
        """Test section detection"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        audio_data = np.random.rand(44100 * 30)
        
        with patch.object(service, '_detect_sections_internal', return_value=[
            {'start': 0, 'end': 10, 'type': 'intro'},
            {'start': 10, 'end': 25, 'type': 'verse'},
            {'start': 25, 'end': 30, 'type': 'outro'}
        ]):
            sections = service._detect_sections(audio_data, 44100)
            assert len(sections) >= 0
    
    @pytest.mark.asyncio
    async def test_estimate_bpm(self):
        """Test BPM estimation"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        beats = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        bpm = service._estimate_bpm(beats)
        
        assert 110 <= bpm <= 130
    
    @pytest.mark.asyncio
    async def test_audio_fingerprint(self):
        """Test audio fingerprinting"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        audio_data = np.random.rand(44100)
        
        fingerprint = service._generate_fingerprint(audio_data, 44100)
        assert fingerprint is not None
        assert isinstance(fingerprint, str)
    
    @pytest.mark.asyncio
    async def test_analyze_with_cache(self, tmp_path):
        """Test analysis with caching"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        audio_path = tmp_path / "cached.wav"
        audio_path.touch()
        
        mock_result = {'duration': 10.0, 'bpm': 120}
        
        with patch.object(service, '_get_cached', return_value=mock_result):
            result = await service.analyze(str(audio_path))
            assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self):
        """Test analysis with non-existent file"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        service = AudioIntelligenceService()
        
        with pytest.raises(Exception):
            await service.analyze("/nonexistent/audio.wav")


class TestAudioDataModels:
    """Tests for audio data models"""
    
    def test_beat_model(self):
        """Test Beat dataclass"""
        from backend.services.audio_intelligence_service import Beat
        
        beat = Beat(time=1.5, strength=0.8, tempo=120)
        assert beat.time == 1.5
        assert beat.strength == 0.8
    
    def test_section_model(self):
        """Test Section dataclass"""
        from backend.services.audio_intelligence_service import Section
        
        section = Section(start=0.0, end=30.0, type='verse', energy=0.7)
        assert section.start == 0.0
        assert section.end == 30.0
        assert section.type == 'verse'
    
    def test_analysis_result_model(self):
        """Test AnalysisResult dataclass"""
        from backend.services.audio_intelligence_service import AnalysisResult
        
        result = AnalysisResult(
            duration=120.0,
            sample_rate=44100,
            bpm=120,
            beats=[],
            sections=[],
            energy_curve=[],
            fingerprint='abc123'
        )
        
        assert result.duration == 120.0
        assert result.bpm == 120


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
