"""
Nano Banana Studio Pro - Test Suite
=====================================
Comprehensive test coverage for all services and endpoints.

Run: pytest tests/ -v --cov=backend
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_image_path(tmp_path):
    """Create sample test image"""
    from PIL import Image
    img = Image.new('RGB', (1920, 1080), color='blue')
    path = tmp_path / "test_image.jpg"
    img.save(str(path))
    return str(path)


@pytest.fixture
def sample_audio_path(tmp_path):
    """Create sample test audio (silent)"""
    import wave
    import struct
    
    path = tmp_path / "test_audio.wav"
    with wave.open(str(path), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(22050)
        # 5 seconds of silence
        samples = [0] * (22050 * 5)
        wav.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    
    return str(path)


# =============================================================================
# STORYBOARD SERVICE TESTS
# =============================================================================

class TestStoryboardService:
    """Tests for StoryboardService"""
    
    @pytest.mark.asyncio
    async def test_generate_from_prompt(self):
        """Test storyboard generation from prompt"""
        from backend.services.storyboard_service import StoryboardService
        
        with patch.object(StoryboardService, '_load_styles', return_value={"styles": {}}):
            service = StoryboardService()
            
            # Mock LLM response
            mock_response = json.dumps({
                "title": "Test Storyboard",
                "scenes": [
                    {
                        "index": 1,
                        "visual_prompt": "Test scene 1",
                        "scene_type": "establishing",
                        "camera_move": "zoom_in"
                    }
                ]
            })
            
            with patch.object(service.llm, 'complete', return_value=mock_response):
                storyboard = await service.generate_from_prompt(
                    prompt="A beautiful sunset",
                    style="Cinematic",
                    duration=30.0,
                    scene_count=3
                )
                
                assert storyboard is not None
                assert storyboard.title == "Test Storyboard"
                assert len(storyboard.scenes) >= 1
    
    def test_parse_lyrics_sections(self):
        """Test lyrics parsing into sections"""
        from backend.services.storyboard_service import StoryboardService
        
        service = StoryboardService()
        
        lyrics = """
[Verse 1]
Walking down the street
Under the moonlight

[Chorus]
We are the dreamers
Living in the night
"""
        
        sections = service._parse_lyrics_sections(lyrics)
        
        assert len(sections) >= 2
        assert sections[0]['type'] == 'verse'
        assert sections[1]['type'] == 'chorus'


# =============================================================================
# ANIMATION SERVICE TESTS
# =============================================================================

class TestAnimationService:
    """Tests for AnimationService"""
    
    @pytest.mark.asyncio
    async def test_select_provider_fallback(self):
        """Test provider selection falls back to Ken Burns"""
        from backend.services.animation_service import (
            AnimationService, AnimationRequest, AnimationProvider
        )
        
        service = AnimationService()
        request = AnimationRequest(provider=AnimationProvider.AUTO)
        
        # With no API keys configured, should fallback
        provider = await service._select_provider(request)
        assert provider in [AnimationProvider.KENBURNS, AnimationProvider.SVD]
    
    @pytest.mark.asyncio
    async def test_ken_burns_generator(self, sample_image_path, tmp_path):
        """Test Ken Burns animation generation"""
        from backend.services.animation_service import KenBurnsGenerator, MotionType
        
        output_path = str(tmp_path / "output.mp4")
        
        result = await KenBurnsGenerator.generate(
            image_path=sample_image_path,
            output_path=output_path,
            duration=2.0,
            fps=24,
            motion_type=MotionType.ZOOM_IN
        )
        
        assert Path(output_path).exists()
        assert result['duration'] == 2.0


# =============================================================================
# AUDIO INTELLIGENCE SERVICE TESTS
# =============================================================================

class TestAudioIntelligenceService:
    """Tests for AudioIntelligenceService"""
    
    @pytest.mark.asyncio
    async def test_analyze_audio(self, sample_audio_path):
        """Test audio analysis"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        
        service = AudioIntelligenceService()
        analysis = await service.analyze(sample_audio_path)
        
        assert analysis is not None
        assert analysis.duration > 0
        assert analysis.bpm > 0
        assert len(analysis.energy_curve) > 0
    
    @pytest.mark.asyncio
    async def test_sync_scenes_to_beats(self, sample_audio_path):
        """Test scene timing synchronization"""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        
        service = AudioIntelligenceService()
        scenes = await service.sync_scenes_to_beats(
            audio_path=sample_audio_path,
            scene_count=5
        )
        
        assert len(scenes) == 5
        for scene in scenes:
            assert 'start_time' in scene
            assert 'end_time' in scene
            assert 'duration' in scene


# =============================================================================
# THUMBNAIL SERVICE TESTS
# =============================================================================

class TestThumbnailService:
    """Tests for ThumbnailService"""
    
    @pytest.mark.asyncio
    async def test_generate_thumbnail(self, sample_image_path, tmp_path):
        """Test thumbnail generation"""
        from backend.services.thumbnail_service import (
            ThumbnailService, ThumbnailRequest, ThumbnailStyle, TextOverlay, TextPosition
        )
        
        service = ThumbnailService()
        
        request = ThumbnailRequest(
            source_image=sample_image_path,
            style=ThumbnailStyle.YOUTUBE,
            text_overlays=[
                TextOverlay(text="TEST", position=TextPosition.CENTER)
            ],
            output_path=str(tmp_path / "thumbnail.jpg")
        )
        
        result = await service.generate(request)
        
        assert Path(result.image_path).exists()
        assert result.size == (1920, 1080)


# =============================================================================
# PUBLISHING SERVICE TESTS
# =============================================================================

class TestPublishingService:
    """Tests for PublishingService"""
    
    @pytest.mark.asyncio
    async def test_export_video(self, sample_image_path, tmp_path):
        """Test video export"""
        from backend.services.publishing_service import (
            PublishingService, ExportRequest, Platform, Quality
        )
        
        # First create a test video from image
        test_video = tmp_path / "test_video.mp4"
        
        import subprocess
        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", sample_image_path,
            "-t", "2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(test_video)
        ], capture_output=True)
        
        if not test_video.exists():
            pytest.skip("FFmpeg not available")
        
        service = PublishingService()
        
        request = ExportRequest(
            video_path=str(test_video),
            platform=Platform.YOUTUBE,
            quality=Quality.HD
        )
        
        result = await service.export(request)
        
        assert Path(result.video_path).exists()
        assert result.platform == "youtube"


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
