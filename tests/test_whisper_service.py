"""
Nano Banana Studio Pro - Whisper Service Tests
===============================================
Comprehensive test coverage for WhisperService.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path


class TestWhisperService:
    """Tests for WhisperService"""
    
    def test_init(self):
        """Test service initialization"""
        from backend.services.whisper_service import WhisperService
        service = WhisperService()
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_transcribe_audio(self, tmp_path):
        """Test audio transcription"""
        from backend.services.whisper_service import WhisperService
        
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b'fake-audio')
        
        service = WhisperService()
        
        with patch.object(service, '_transcribe', new_callable=AsyncMock, return_value={
            'text': 'Hello world',
            'segments': [{'start': 0, 'end': 1, 'text': 'Hello world'}]
        }):
            result = await service.transcribe(str(audio_path))
            assert result['text'] == 'Hello world'
    
    @pytest.mark.asyncio
    async def test_transcribe_with_timestamps(self, tmp_path):
        """Test transcription with timestamps"""
        from backend.services.whisper_service import WhisperService
        
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b'fake-audio')
        
        service = WhisperService()
        
        mock_segments = [
            {'start': 0.0, 'end': 2.5, 'text': 'First segment'},
            {'start': 2.5, 'end': 5.0, 'text': 'Second segment'}
        ]
        
        with patch.object(service, '_transcribe', new_callable=AsyncMock, return_value={
            'text': 'First segment Second segment',
            'segments': mock_segments
        }):
            result = await service.transcribe(str(audio_path), timestamps=True)
            assert len(result['segments']) == 2
    
    @pytest.mark.asyncio
    async def test_transcribe_with_language(self, tmp_path):
        """Test transcription with specific language"""
        from backend.services.whisper_service import WhisperService
        
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b'fake-audio')
        
        service = WhisperService()
        
        with patch.object(service, '_transcribe', new_callable=AsyncMock, return_value={
            'text': 'Bonjour le monde',
            'language': 'fr'
        }):
            result = await service.transcribe(str(audio_path), language='fr')
            assert result['language'] == 'fr'
    
    @pytest.mark.asyncio
    async def test_detect_language(self, tmp_path):
        """Test language detection"""
        from backend.services.whisper_service import WhisperService
        
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b'fake-audio')
        
        service = WhisperService()
        
        with patch.object(service, '_detect_language', new_callable=AsyncMock, return_value='en'):
            language = await service.detect_language(str(audio_path))
            assert language == 'en'
    
    @pytest.mark.asyncio
    async def test_extract_lyrics(self, tmp_path):
        """Test lyrics extraction from music"""
        from backend.services.whisper_service import WhisperService
        
        audio_path = tmp_path / "song.mp3"
        audio_path.write_bytes(b'fake-music')
        
        service = WhisperService()
        
        with patch.object(service, '_transcribe', new_callable=AsyncMock, return_value={
            'text': '[Verse]\nWalking down the road\n[Chorus]\nSinging loud',
            'segments': []
        }):
            result = await service.extract_lyrics(str(audio_path))
            assert '[Verse]' in result['text']
    
    @pytest.mark.asyncio
    async def test_word_level_timestamps(self, tmp_path):
        """Test word-level timestamp extraction"""
        from backend.services.whisper_service import WhisperService
        
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b'fake-audio')
        
        service = WhisperService()
        
        mock_words = [
            {'word': 'Hello', 'start': 0.0, 'end': 0.5},
            {'word': 'world', 'start': 0.5, 'end': 1.0}
        ]
        
        with patch.object(service, '_transcribe_words', new_callable=AsyncMock, return_value=mock_words):
            result = await service.transcribe_with_words(str(audio_path))
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """Test with non-existent file"""
        from backend.services.whisper_service import WhisperService
        
        service = WhisperService()
        
        with pytest.raises(Exception):
            await service.transcribe('/nonexistent/audio.wav')


class TestWhisperModels:
    """Tests for Whisper model configurations"""
    
    def test_model_sizes(self):
        """Test available model sizes"""
        from backend.services.whisper_service import WhisperService
        
        service = WhisperService()
        sizes = service.available_models()
        
        assert 'tiny' in sizes
        assert 'base' in sizes
        assert 'small' in sizes
        assert 'medium' in sizes
        assert 'large' in sizes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
