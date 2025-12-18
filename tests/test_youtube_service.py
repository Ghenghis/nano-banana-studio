"""
Nano Banana Studio Pro - YouTube Service Tests
===============================================
Comprehensive test coverage for YouTubeService.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestYouTubeService:
    """Tests for YouTubeService"""
    
    def test_init(self):
        """Test service initialization"""
        from backend.services.youtube_service import YouTubeService
        service = YouTubeService()
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_upload_video(self, tmp_path):
        """Test video upload"""
        from backend.services.youtube_service import YouTubeService
        
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b'fake-video-data')
        
        service = YouTubeService()
        
        with patch.object(service, '_get_authenticated_service', return_value=Mock()):
            with patch.object(service, '_execute_upload', new_callable=AsyncMock, return_value={'id': 'video-123'}):
                result = await service.upload(
                    video_path=str(video_path),
                    title='Test Video',
                    description='Test description',
                    privacy='private'
                )
                assert result['id'] == 'video-123'
    
    @pytest.mark.asyncio
    async def test_upload_with_thumbnail(self, tmp_path):
        """Test upload with custom thumbnail"""
        from backend.services.youtube_service import YouTubeService
        
        video_path = tmp_path / "video.mp4"
        thumb_path = tmp_path / "thumb.jpg"
        video_path.write_bytes(b'video')
        thumb_path.write_bytes(b'thumbnail')
        
        service = YouTubeService()
        
        with patch.object(service, '_get_authenticated_service', return_value=Mock()):
            with patch.object(service, '_execute_upload', new_callable=AsyncMock, return_value={'id': 'vid-456'}):
                with patch.object(service, '_set_thumbnail', new_callable=AsyncMock):
                    result = await service.upload(
                        video_path=str(video_path),
                        title='With Thumbnail',
                        thumbnail_path=str(thumb_path)
                    )
                    assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_metadata(self):
        """Test AI metadata generation"""
        from backend.services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        with patch.object(service, '_generate_ai_metadata', return_value={
            'title': 'AI Generated Title',
            'description': 'AI description',
            'tags': ['ai', 'video']
        }):
            metadata = await service.generate_metadata(
                title='My Video',
                description='Short desc',
                category='Entertainment'
            )
            assert 'title' in metadata
    
    @pytest.mark.asyncio
    async def test_get_accounts(self):
        """Test getting connected accounts"""
        from backend.services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        with patch.object(service, '_list_accounts', return_value=[
            {'id': 'acc-1', 'name': 'Channel 1'},
            {'id': 'acc-2', 'name': 'Channel 2'}
        ]):
            accounts = await service.get_accounts()
            assert len(accounts) == 2
    
    @pytest.mark.asyncio
    async def test_add_account(self):
        """Test adding new account"""
        from backend.services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        with patch.object(service, '_oauth_flow', return_value={'id': 'new-acc'}):
            result = await service.add_account(auth_code='test-code')
            assert result['id'] == 'new-acc'
    
    @pytest.mark.asyncio
    async def test_remove_account(self):
        """Test removing account"""
        from backend.services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        with patch.object(service, '_revoke_credentials', return_value=True):
            result = await service.remove_account('acc-123')
            assert result == True
    
    @pytest.mark.asyncio
    async def test_get_playlists(self):
        """Test getting playlists"""
        from backend.services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        with patch.object(service, '_list_playlists', return_value=[
            {'id': 'pl-1', 'title': 'Playlist 1'},
            {'id': 'pl-2', 'title': 'Playlist 2'}
        ]):
            playlists = await service.get_playlists('acc-123')
            assert len(playlists) == 2
    
    @pytest.mark.asyncio
    async def test_create_playlist(self):
        """Test creating playlist"""
        from backend.services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        with patch.object(service, '_create_playlist', return_value={'id': 'pl-new'}):
            result = await service.create_playlist(
                account_id='acc-123',
                title='New Playlist',
                description='Test playlist'
            )
            assert result['id'] == 'pl-new'
    
    @pytest.mark.asyncio
    async def test_add_to_playlist(self):
        """Test adding video to playlist"""
        from backend.services.youtube_service import YouTubeService
        
        service = YouTubeService()
        
        with patch.object(service, '_add_to_playlist', return_value=True):
            result = await service.add_to_playlist('video-123', 'playlist-456')
            assert result == True
    
    @pytest.mark.asyncio
    async def test_schedule_publish(self):
        """Test scheduled publishing"""
        from backend.services.youtube_service import YouTubeService
        from datetime import datetime, timedelta
        
        service = YouTubeService()
        schedule_time = datetime.utcnow() + timedelta(days=1)
        
        with patch.object(service, '_schedule_video', return_value={'scheduled': True}):
            result = await service.schedule_publish(
                video_id='vid-123',
                publish_at=schedule_time.isoformat()
            )
            assert result['scheduled'] == True


class TestYouTubeDataModels:
    """Tests for YouTube data models"""
    
    def test_upload_request_model(self):
        """Test YouTubeUploadRequest"""
        from backend.services.youtube_service import YouTubeUploadRequest
        
        request = YouTubeUploadRequest(
            video_path='/video.mp4',
            title='Test',
            description='Desc',
            privacy='private'
        )
        
        assert request.video_path == '/video.mp4'
        assert request.privacy == 'private'
    
    def test_upload_result_model(self):
        """Test YouTubeUploadResult"""
        from backend.services.youtube_service import YouTubeUploadResult
        
        result = YouTubeUploadResult(
            video_id='abc123',
            video_url='https://youtube.com/watch?v=abc123',
            status='published'
        )
        
        assert result.video_id == 'abc123'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
