"""
Nano Banana Studio Pro - Suno Service Tests
============================================
Comprehensive test coverage for SunoMusicService.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch


class TestSunoClient:
    """Tests for Suno API client"""
    
    @pytest.mark.asyncio
    async def test_init_with_cookie(self):
        """Test client initialization with cookie"""
        with patch.dict('os.environ', {'SUNO_COOKIE': 'test-cookie'}):
            from backend.services.suno_service import SunoClient
            client = SunoClient()
            assert client is not None
    
    @pytest.mark.asyncio
    async def test_generate_simple_mode(self):
        """Test simple generation mode"""
        from backend.services.suno_service import SunoClient, SunoGenerateRequest
        
        client = SunoClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'song-123', 'status': 'completed'}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock, return_value=mock_response):
            request = SunoGenerateRequest(prompt='upbeat pop song')
            result = await client.generate(request)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_custom_mode(self):
        """Test custom generation with lyrics"""
        from backend.services.suno_service import SunoClient, SunoGenerateRequest
        
        client = SunoClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'song-456', 'status': 'completed'}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock, return_value=mock_response):
            request = SunoGenerateRequest(
                prompt='ballad',
                lyrics='[Verse]\nTest lyrics here',
                style='acoustic'
            )
            result = await client.generate(request)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_poll_status(self):
        """Test status polling"""
        from backend.services.suno_service import SunoClient
        
        client = SunoClient()
        
        mock_responses = [
            {'status': 'processing'},
            {'status': 'processing'},
            {'status': 'completed', 'audio_url': 'https://example.com/song.mp3'}
        ]
        
        with patch.object(client, '_get_status', new_callable=AsyncMock, side_effect=mock_responses):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await client._poll_until_complete('song-123', timeout=30)
                assert result['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_poll_timeout(self):
        """Test polling timeout"""
        from backend.services.suno_service import SunoClient
        
        client = SunoClient()
        
        with patch.object(client, '_get_status', new_callable=AsyncMock, return_value={'status': 'processing'}):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(Exception):
                    await asyncio.wait_for(client._poll_until_complete('song-123'), timeout=0.1)


class TestSunoMusicService:
    """Tests for SunoMusicService"""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test service initialization"""
        from backend.services.suno_service import SunoMusicService
        service = SunoMusicService()
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_generate_music(self):
        """Test music generation"""
        from backend.services.suno_service import SunoMusicService, SunoGenerateRequest
        
        service = SunoMusicService()
        
        mock_result = {
            'id': 'song-789',
            'audio_url': 'https://example.com/song.mp3',
            'status': 'completed'
        }
        
        with patch.object(service.client, 'generate', new_callable=AsyncMock, return_value=mock_result):
            request = SunoGenerateRequest(prompt='electronic dance music')
            result = await service.generate(request)
            assert result['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_generate_instrumental(self):
        """Test instrumental generation"""
        from backend.services.suno_service import SunoMusicService, SunoGenerateRequest
        
        service = SunoMusicService()
        
        mock_result = {'id': 'inst-123', 'status': 'completed'}
        
        with patch.object(service.client, 'generate', new_callable=AsyncMock, return_value=mock_result):
            request = SunoGenerateRequest(
                prompt='cinematic orchestral',
                instrumental=True
            )
            result = await service.generate(request)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_extend_song(self):
        """Test song extension"""
        from backend.services.suno_service import SunoMusicService, SunoGenerateRequest
        
        service = SunoMusicService()
        
        mock_result = {'id': 'ext-123', 'status': 'completed'}
        
        with patch.object(service.client, 'generate', new_callable=AsyncMock, return_value=mock_result):
            request = SunoGenerateRequest(
                prompt='continue the vibe',
                continue_clip_id='original-song-id',
                continue_at=30.0
            )
            result = await service.generate(request)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_download_audio(self, tmp_path):
        """Test audio download"""
        from backend.services.suno_service import SunoMusicService
        
        service = SunoMusicService()
        output_path = tmp_path / "downloaded.mp3"
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_response = Mock()
            mock_response.content = b'fake-audio-data'
            mock_get.return_value = mock_response
            
            await service.download_audio('https://example.com/song.mp3', str(output_path))
            
            assert output_path.exists()


class TestSunoDataModels:
    """Tests for Suno data models"""
    
    def test_suno_style_enum(self):
        """Test SunoStyle enum"""
        from backend.services.suno_service import SunoStyle
        
        assert SunoStyle.POP.value == 'pop'
        assert SunoStyle.ROCK.value == 'rock'
        assert SunoStyle.ELECTRONIC.value == 'electronic'
    
    def test_suno_mood_enum(self):
        """Test SunoMood enum"""
        from backend.services.suno_service import SunoMood
        
        assert SunoMood.HAPPY.value == 'happy, upbeat'
        assert SunoMood.SAD.value == 'sad, melancholic'
    
    def test_song_status_enum(self):
        """Test SongStatus enum"""
        from backend.services.suno_service import SongStatus
        
        assert SongStatus.PENDING.value == 'pending'
        assert SongStatus.GENERATING.value == 'streaming'
        assert SongStatus.COMPLETE.value == 'complete'
    
    def test_generate_request_defaults(self):
        """Test SunoGenerateRequest defaults"""
        from backend.services.suno_service import SunoGenerateRequest
        
        request = SunoGenerateRequest(prompt='test')
        assert request.prompt == 'test'
        assert request.instrumental == False
        assert request.model == 'chirp-v3-5'
    
    def test_suno_song_model(self):
        """Test SunoSong model"""
        from backend.services.suno_service import SunoSong, SongStatus
        
        song = SunoSong(
            id='song-123',
            title='Test Song',
            status=SongStatus.COMPLETE,
            audio_url='https://example.com/song.mp3',
            duration=180.0
        )
        
        assert song.id == 'song-123'
        assert song.status == SongStatus.COMPLETE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
