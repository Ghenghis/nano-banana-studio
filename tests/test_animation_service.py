"""
Nano Banana Studio Pro - Animation Service Tests
=================================================
Comprehensive test coverage for AnimationService.
Tests: RunwayClient, KlingClient, SVDClient, KenBurnsGenerator, AnimationService
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import base64


class TestRunwayClient:
    """Tests for Runway API client"""
    
    @pytest.mark.asyncio
    async def test_init_with_api_key(self):
        """Test client initialization with API key"""
        with patch.dict('os.environ', {'RUNWAY_API_KEY': 'test-key'}):
            from backend.services.animation_service import RunwayClient
            client = RunwayClient()
            assert client.api_key == 'test-key'
    
    @pytest.mark.asyncio
    async def test_init_without_api_key(self):
        """Test client initialization without API key"""
        with patch.dict('os.environ', {'RUNWAY_API_KEY': ''}, clear=True):
            from backend.services.animation_service import RunwayClient
            client = RunwayClient()
            assert client.api_key == ''
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful video generation"""
        from backend.services.animation_service import RunwayClient
        
        client = RunwayClient()
        client.api_key = 'test-key'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'task-123', 'status': 'completed', 'output': {'video_url': 'https://example.com/video.mp4'}}
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            with patch.object(client, '_poll_task', new_callable=AsyncMock, return_value={'video_url': 'https://example.com/video.mp4'}):
                result = await client.generate(
                    image_base64='base64data',
                    prompt='test animation',
                    duration=4.0
                )
                assert 'video_url' in result
    
    @pytest.mark.asyncio
    async def test_generate_api_error(self):
        """Test API error handling"""
        from backend.services.animation_service import RunwayClient
        
        client = RunwayClient()
        client.api_key = 'test-key'
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Exception):
                await client.generate(image_base64='base64data', prompt='test')
    
    @pytest.mark.asyncio
    async def test_poll_task_timeout(self):
        """Test polling timeout"""
        from backend.services.animation_service import RunwayClient
        
        client = RunwayClient()
        client.api_key = 'test-key'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'processing'}
        
        with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(Exception):
                    await asyncio.wait_for(client._poll_task('task-123'), timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test client cleanup"""
        from backend.services.animation_service import RunwayClient
        client = RunwayClient()
        await client.close()


class TestKlingClient:
    """Tests for Kling API client"""
    
    @pytest.mark.asyncio
    async def test_init_with_credentials(self):
        """Test client initialization with credentials"""
        with patch.dict('os.environ', {'KLING_ACCESS_KEY': 'key', 'KLING_SECRET_KEY': 'secret'}):
            from backend.services.animation_service import KlingClient
            client = KlingClient()
            assert client.access_key == 'key'
            assert client.secret_key == 'secret'
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful Kling generation"""
        from backend.services.animation_service import KlingClient
        
        client = KlingClient()
        client.access_key = 'test-key'
        client.secret_key = 'test-secret'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'task_id': 'kling-123'}
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            with patch.object(client, '_poll_task', new_callable=AsyncMock, return_value={'video_url': 'https://example.com/video.mp4'}):
                result = await client.generate(
                    image_base64='base64data',
                    prompt='test animation',
                    duration=5.0,
                    mode='std'
                )
                assert 'video_url' in result
    
    @pytest.mark.asyncio
    async def test_generate_pro_mode(self):
        """Test Kling pro mode generation"""
        from backend.services.animation_service import KlingClient
        
        client = KlingClient()
        client.access_key = 'test-key'
        client.secret_key = 'test-secret'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'task_id': 'kling-456'}
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            with patch.object(client, '_poll_task', new_callable=AsyncMock, return_value={'video_url': 'https://example.com/video.mp4'}):
                result = await client.generate(
                    image_base64='base64data',
                    prompt='test animation',
                    duration=5.0,
                    mode='pro'
                )
                assert 'video_url' in result


class TestSVDClient:
    """Tests for Stable Video Diffusion client"""
    
    @pytest.mark.asyncio
    async def test_init_with_url(self):
        """Test client initialization with service URL"""
        with patch.dict('os.environ', {'SVD_SERVICE_URL': 'http://localhost:8001'}):
            from backend.services.animation_service import SVDClient
            client = SVDClient()
            assert 'localhost:8001' in client.service_url
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful SVD generation"""
        from backend.services.animation_service import SVDClient
        
        client = SVDClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'video_path': '/output/video.mp4'}
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await client.generate(
                image_base64='base64data',
                motion_bucket_id=127,
                fps=24,
                num_frames=25
            )
            assert 'video_path' in result
    
    @pytest.mark.asyncio
    async def test_generate_with_seed(self):
        """Test SVD generation with seed"""
        from backend.services.animation_service import SVDClient
        
        client = SVDClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'video_path': '/output/video.mp4'}
        
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await client.generate(
                image_base64='base64data',
                motion_bucket_id=127,
                fps=24,
                num_frames=25,
                seed=42
            )
            assert 'video_path' in result


class TestKenBurnsGenerator:
    """Tests for Ken Burns effect generator"""
    
    @pytest.mark.asyncio
    async def test_generate_zoom_in(self, tmp_path):
        """Test Ken Burns zoom in effect"""
        from backend.services.animation_service import KenBurnsGenerator, MotionType
        from PIL import Image
        
        img = Image.new('RGB', (1920, 1080), color='blue')
        input_path = tmp_path / "input.jpg"
        output_path = tmp_path / "output.mp4"
        img.save(str(input_path))
        
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value.communicate = AsyncMock(return_value=(b'', b''))
            mock_proc.return_value.returncode = 0
            
            result = await KenBurnsGenerator.generate(
                image_path=str(input_path),
                output_path=str(output_path),
                duration=5.0,
                fps=24,
                motion_type=MotionType.ZOOM_IN
            )
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_zoom_out(self, tmp_path):
        """Test Ken Burns zoom out effect"""
        from backend.services.animation_service import KenBurnsGenerator, MotionType
        from PIL import Image
        
        img = Image.new('RGB', (1920, 1080), color='red')
        input_path = tmp_path / "input.jpg"
        output_path = tmp_path / "output.mp4"
        img.save(str(input_path))
        
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value.communicate = AsyncMock(return_value=(b'', b''))
            mock_proc.return_value.returncode = 0
            
            result = await KenBurnsGenerator.generate(
                image_path=str(input_path),
                output_path=str(output_path),
                duration=5.0,
                fps=24,
                motion_type=MotionType.ZOOM_OUT
            )
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_pan_left(self, tmp_path):
        """Test Ken Burns pan left effect"""
        from backend.services.animation_service import KenBurnsGenerator, MotionType
        from PIL import Image
        
        img = Image.new('RGB', (1920, 1080), color='green')
        input_path = tmp_path / "input.jpg"
        output_path = tmp_path / "output.mp4"
        img.save(str(input_path))
        
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value.communicate = AsyncMock(return_value=(b'', b''))
            mock_proc.return_value.returncode = 0
            
            result = await KenBurnsGenerator.generate(
                image_path=str(input_path),
                output_path=str(output_path),
                duration=5.0,
                fps=24,
                motion_type=MotionType.PAN_LEFT
            )
            assert result is not None


class TestAnimationService:
    """Tests for main AnimationService"""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test service initialization"""
        from backend.services.animation_service import AnimationService
        service = AnimationService()
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_select_provider_auto(self):
        """Test automatic provider selection"""
        from backend.services.animation_service import AnimationService, AnimationProvider
        
        service = AnimationService()
        provider = await service._select_provider(AnimationProvider.AUTO)
        assert provider in [AnimationProvider.RUNWAY, AnimationProvider.KLING, AnimationProvider.SVD, AnimationProvider.KENBURNS]
    
    @pytest.mark.asyncio
    async def test_select_provider_explicit(self):
        """Test explicit provider selection"""
        from backend.services.animation_service import AnimationService, AnimationProvider
        
        service = AnimationService()
        provider = await service._select_provider(AnimationProvider.KENBURNS)
        assert provider == AnimationProvider.KENBURNS
    
    @pytest.mark.asyncio
    async def test_animate_with_kenburns_fallback(self, tmp_path):
        """Test animation with Ken Burns fallback"""
        from backend.services.animation_service import AnimationService, AnimationRequest, MotionType
        from PIL import Image
        
        img = Image.new('RGB', (1920, 1080), color='purple')
        input_path = tmp_path / "input.jpg"
        img.save(str(input_path))
        
        service = AnimationService()
        
        request = AnimationRequest(
            image_path=str(input_path),
            motion_prompt="zoom in slowly",
            motion_type=MotionType.ZOOM_IN,
            duration=5.0,
            fps=24
        )
        
        with patch.object(service.kenburns, 'generate', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {'video_path': str(tmp_path / 'output.mp4')}
            
            result = await service.animate(request)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test service cleanup"""
        from backend.services.animation_service import AnimationService
        service = AnimationService()
        await service.close()


class TestAnimationDataModels:
    """Tests for animation data models"""
    
    def test_motion_type_enum(self):
        """Test MotionType enum values"""
        from backend.services.animation_service import MotionType
        
        assert MotionType.ZOOM_IN.value == 'zoom_in'
        assert MotionType.ZOOM_OUT.value == 'zoom_out'
        assert MotionType.PAN_LEFT.value == 'pan_left'
        assert MotionType.PAN_RIGHT.value == 'pan_right'
    
    def test_animation_provider_enum(self):
        """Test AnimationProvider enum values"""
        from backend.services.animation_service import AnimationProvider
        
        assert AnimationProvider.AUTO.value == 'auto'
        assert AnimationProvider.RUNWAY.value == 'runway'
        assert AnimationProvider.KLING.value == 'kling'
        assert AnimationProvider.SVD.value == 'svd'
        assert AnimationProvider.KENBURNS.value == 'kenburns'
    
    def test_animation_request_defaults(self):
        """Test AnimationRequest default values"""
        from backend.services.animation_service import AnimationRequest, MotionType, AnimationProvider
        
        request = AnimationRequest(image_path='/test/image.jpg')
        assert request.duration == 5.0
        assert request.fps == 24
        assert request.motion_type == MotionType.ZOOM_IN
        assert request.provider == AnimationProvider.AUTO
    
    def test_animation_result_to_dict(self):
        """Test AnimationResult serialization"""
        from backend.services.animation_service import AnimationResult
        
        result = AnimationResult(
            job_id='test-123',
            video_path='/output/video.mp4',
            duration=5.0,
            fps=24,
            resolution=(1920, 1080),
            provider_used='kenburns',
            file_size=1000000
        )
        
        data = result.to_dict()
        assert data['job_id'] == 'test-123'
        assert data['video_path'] == '/output/video.mp4'
        assert data['duration'] == 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
