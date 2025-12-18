"""
Nano Banana Studio Pro - TTS Service Tests
===========================================
Comprehensive test coverage for TTSService.
Tests: ElevenLabsClient, OpenAITTSClient, EdgeTTSClient, TTSService
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path


class TestElevenLabsClient:
    """Tests for ElevenLabs TTS client"""
    
    @pytest.mark.asyncio
    async def test_init_with_api_key(self):
        """Test client initialization with API key"""
        from backend.services.tts_service import ElevenLabsClient
        client = ElevenLabsClient(api_key='test-key')
        assert client.api_key == 'test-key'
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self):
        """Test successful speech synthesis"""
        from backend.services.tts_service import ElevenLabsClient
        
        client = ElevenLabsClient(api_key='test-key')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'audio-data-bytes'
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            audio = await client.synthesize(
                text='Hello world',
                voice_id='test-voice'
            )
            assert audio == b'audio-data-bytes'
    
    @pytest.mark.asyncio
    async def test_synthesize_api_error(self):
        """Test API error handling"""
        from backend.services.tts_service import ElevenLabsClient
        
        client = ElevenLabsClient(api_key='test-key')
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Exception):
                await client.synthesize(text='Hello', voice_id='test')
    
    @pytest.mark.asyncio
    async def test_synthesize_with_model(self):
        """Test synthesis with specific model"""
        from backend.services.tts_service import ElevenLabsClient
        
        client = ElevenLabsClient(api_key='test-key')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'audio-data'
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response) as mock_post:
            await client.synthesize(
                text='Test',
                voice_id='voice-123',
                model='eleven_multilingual_v2'
            )
            
            call_args = mock_post.call_args
            assert 'eleven_multilingual_v2' in str(call_args)
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test client cleanup"""
        from backend.services.tts_service import ElevenLabsClient
        client = ElevenLabsClient(api_key='test-key')
        await client.close()


class TestOpenAITTSClient:
    """Tests for OpenAI TTS client"""
    
    @pytest.mark.asyncio
    async def test_init_with_api_key(self):
        """Test client initialization"""
        from backend.services.tts_service import OpenAITTSClient
        client = OpenAITTSClient(api_key='test-key')
        assert client.api_key == 'test-key'
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self):
        """Test successful synthesis"""
        from backend.services.tts_service import OpenAITTSClient
        
        client = OpenAITTSClient(api_key='test-key')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'openai-audio-bytes'
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            audio = await client.synthesize(
                text='Hello from OpenAI',
                voice='alloy'
            )
            assert audio == b'openai-audio-bytes'
    
    @pytest.mark.asyncio
    async def test_synthesize_with_speed(self):
        """Test synthesis with speed adjustment"""
        from backend.services.tts_service import OpenAITTSClient
        
        client = OpenAITTSClient(api_key='test-key')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'audio-fast'
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response) as mock_post:
            await client.synthesize(
                text='Fast speech',
                voice='nova',
                speed=1.5
            )
            
            call_args = mock_post.call_args
            assert '1.5' in str(call_args) or 'speed' in str(call_args)
    
    @pytest.mark.asyncio
    async def test_synthesize_all_voices(self):
        """Test all OpenAI voice options"""
        from backend.services.tts_service import OpenAITTSClient
        
        client = OpenAITTSClient(api_key='test-key')
        voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'audio'
        
        for voice in voices:
            with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
                audio = await client.synthesize(text='Test', voice=voice)
                assert audio is not None


class TestEdgeTTSClient:
    """Tests for Microsoft Edge TTS client"""
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self):
        """Test successful Edge TTS synthesis"""
        from backend.services.tts_service import EdgeTTSClient
        
        client = EdgeTTSClient()
        
        with patch('edge_tts.Communicate') as mock_comm:
            mock_instance = Mock()
            mock_instance.stream = AsyncMock(return_value=[
                {'type': 'audio', 'data': b'chunk1'},
                {'type': 'audio', 'data': b'chunk2'}
            ])
            mock_comm.return_value = mock_instance
            
            # Mock async generator
            async def mock_stream():
                yield {'type': 'audio', 'data': b'chunk1'}
                yield {'type': 'audio', 'data': b'chunk2'}
            
            mock_instance.stream = mock_stream
            
            audio = await client.synthesize(
                text='Hello Edge',
                voice='en-US-JennyNeural'
            )
            assert audio == b'chunk1chunk2'
    
    @pytest.mark.asyncio
    async def test_synthesize_with_rate(self):
        """Test synthesis with rate adjustment"""
        from backend.services.tts_service import EdgeTTSClient
        
        client = EdgeTTSClient()
        
        with patch('edge_tts.Communicate') as mock_comm:
            async def mock_stream():
                yield {'type': 'audio', 'data': b'audio'}
            
            mock_instance = Mock()
            mock_instance.stream = mock_stream
            mock_comm.return_value = mock_instance
            
            await client.synthesize(
                text='Test',
                voice='en-US-GuyNeural',
                rate='+20%'
            )
            
            mock_comm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthesize_with_pitch(self):
        """Test synthesis with pitch adjustment"""
        from backend.services.tts_service import EdgeTTSClient
        
        client = EdgeTTSClient()
        
        with patch('edge_tts.Communicate') as mock_comm:
            async def mock_stream():
                yield {'type': 'audio', 'data': b'audio'}
            
            mock_instance = Mock()
            mock_instance.stream = mock_stream
            mock_comm.return_value = mock_instance
            
            await client.synthesize(
                text='High pitch',
                voice='en-US-AriaNeural',
                pitch='+10Hz'
            )


class TestTTSService:
    """Tests for main TTSService"""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test service initialization"""
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': '', 'OPENAI_API_KEY': ''}):
            from backend.services.tts_service import TTSService
            service = TTSService()
            assert service is not None
    
    @pytest.mark.asyncio
    async def test_select_provider_auto_elevenlabs(self):
        """Test auto provider selection prefers ElevenLabs"""
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': 'test-key', 'OPENAI_API_KEY': ''}):
            from backend.services.tts_service import TTSService, TTSProvider, TTSRequest
            service = TTSService()
            
            request = TTSRequest(text='Test', provider=TTSProvider.AUTO)
            provider = await service._select_provider(request)
            assert provider == TTSProvider.ELEVENLABS
    
    @pytest.mark.asyncio
    async def test_select_provider_auto_openai(self):
        """Test auto provider selection falls back to OpenAI"""
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': '', 'OPENAI_API_KEY': 'test-key'}):
            from backend.services.tts_service import TTSService, TTSProvider, TTSRequest
            service = TTSService()
            service.elevenlabs = None
            
            request = TTSRequest(text='Test', provider=TTSProvider.AUTO)
            provider = await service._select_provider(request)
            assert provider == TTSProvider.OPENAI
    
    @pytest.mark.asyncio
    async def test_select_provider_auto_edge_fallback(self):
        """Test auto provider selection falls back to Edge"""
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': '', 'OPENAI_API_KEY': ''}):
            from backend.services.tts_service import TTSService, TTSProvider, TTSRequest
            service = TTSService()
            service.elevenlabs = None
            service.openai = None
            
            request = TTSRequest(text='Test', provider=TTSProvider.AUTO)
            provider = await service._select_provider(request)
            assert provider == TTSProvider.EDGE
    
    @pytest.mark.asyncio
    async def test_synthesize_with_elevenlabs(self, tmp_path):
        """Test synthesis with ElevenLabs"""
        from backend.services.tts_service import TTSService, TTSRequest, TTSProvider
        
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': 'test-key', 'OPENAI_API_KEY': ''}):
            service = TTSService()
            
            with patch.object(service.elevenlabs, 'synthesize', new_callable=AsyncMock, return_value=b'audio-data'):
                with patch.object(service, '_get_audio_duration', return_value=2.5):
                    request = TTSRequest(
                        text='Hello world',
                        voice='rachel',
                        provider=TTSProvider.ELEVENLABS,
                        output_path=str(tmp_path / 'output.mp3')
                    )
                    
                    result = await service.synthesize(request)
                    assert result is not None
                    assert result.duration == 2.5
    
    @pytest.mark.asyncio
    async def test_synthesize_with_openai(self, tmp_path):
        """Test synthesis with OpenAI"""
        from backend.services.tts_service import TTSService, TTSRequest, TTSProvider
        
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': '', 'OPENAI_API_KEY': 'test-key'}):
            service = TTSService()
            
            with patch.object(service.openai, 'synthesize', new_callable=AsyncMock, return_value=b'openai-audio'):
                with patch.object(service, '_get_audio_duration', return_value=3.0):
                    request = TTSRequest(
                        text='OpenAI test',
                        voice='nova',
                        provider=TTSProvider.OPENAI,
                        output_path=str(tmp_path / 'output.mp3')
                    )
                    
                    result = await service.synthesize(request)
                    assert result is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_fallback_on_error(self, tmp_path):
        """Test fallback to Edge TTS on error"""
        from backend.services.tts_service import TTSService, TTSRequest, TTSProvider
        
        service = TTSService()
        service.elevenlabs = Mock()
        service.elevenlabs.synthesize = AsyncMock(side_effect=Exception('API Error'))
        
        with patch.object(service.edge, 'synthesize', new_callable=AsyncMock, return_value=b'edge-audio'):
            with patch.object(service, '_get_audio_duration', return_value=1.5):
                request = TTSRequest(
                    text='Fallback test',
                    provider=TTSProvider.ELEVENLABS,
                    output_path=str(tmp_path / 'output.mp3')
                )
                
                result = await service.synthesize(request)
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_long_text(self, tmp_path):
        """Test long text synthesis with chunking"""
        from backend.services.tts_service import TTSService
        
        service = TTSService()
        
        long_text = "This is sentence one. This is sentence two. This is sentence three. " * 20
        
        with patch.object(service, 'synthesize', new_callable=AsyncMock) as mock_synth:
            mock_synth.return_value = Mock(audio_path=str(tmp_path / 'chunk.mp3'))
            
            with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_proc:
                mock_proc.return_value.communicate = AsyncMock(return_value=(b'', b''))
                mock_proc.return_value.returncode = 0
                
                with patch.object(service, '_get_audio_duration', return_value=10.0):
                    result = await service.synthesize_long_text(
                        text=long_text,
                        voice='alloy'
                    )
    
    @pytest.mark.asyncio
    async def test_get_audio_duration(self, tmp_path):
        """Test audio duration extraction"""
        from backend.services.tts_service import TTSService
        
        service = TTSService()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '5.25\n'
            
            duration = service._get_audio_duration(str(tmp_path / 'test.mp3'))
            assert duration == 5.25
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test service cleanup"""
        from backend.services.tts_service import TTSService
        service = TTSService()
        await service.close()


class TestTTSDataModels:
    """Tests for TTS data models"""
    
    def test_tts_provider_enum(self):
        """Test TTSProvider enum values"""
        from backend.services.tts_service import TTSProvider
        
        assert TTSProvider.AUTO.value == 'auto'
        assert TTSProvider.ELEVENLABS.value == 'elevenlabs'
        assert TTSProvider.OPENAI.value == 'openai'
        assert TTSProvider.EDGE.value == 'edge'
    
    def test_voice_enum(self):
        """Test Voice enum values"""
        from backend.services.tts_service import Voice
        
        assert Voice.ALLOY.value == 'alloy'
        assert Voice.NOVA.value == 'nova'
        assert Voice.JENNY.value == 'en-US-JennyNeural'
    
    def test_speech_style_enum(self):
        """Test SpeechStyle enum values"""
        from backend.services.tts_service import SpeechStyle
        
        assert SpeechStyle.NEUTRAL.value == 'neutral'
        assert SpeechStyle.CHEERFUL.value == 'cheerful'
        assert SpeechStyle.WHISPERING.value == 'whispering'
    
    def test_tts_request_defaults(self):
        """Test TTSRequest default values"""
        from backend.services.tts_service import TTSRequest, TTSProvider, SpeechStyle
        
        request = TTSRequest(text='Hello')
        assert request.voice == 'alloy'
        assert request.provider == TTSProvider.AUTO
        assert request.speed == 1.0
        assert request.style == SpeechStyle.NEUTRAL
    
    def test_tts_result_to_dict(self):
        """Test TTSResult serialization"""
        from backend.services.tts_service import TTSResult
        
        result = TTSResult(
            job_id='tts-123',
            audio_path='/output/speech.mp3',
            duration=5.5,
            provider_used='elevenlabs',
            voice_used='rachel',
            file_size=50000
        )
        
        data = result.to_dict()
        assert data['job_id'] == 'tts-123'
        assert data['duration'] == 5.5
        assert data['provider_used'] == 'elevenlabs'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
