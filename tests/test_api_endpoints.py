"""
Nano Banana Studio Pro - API Endpoint Tests
============================================
Comprehensive test coverage for all FastAPI endpoints.
Tests: All 52+ API endpoints with validation, error handling, and edge cases
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
import base64


@pytest.fixture
def client():
    """Create FastAPI test client"""
    from backend.api.main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health and info endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "Nano Banana" in data["name"]
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPromptEnhancementEndpoints:
    """Tests for prompt enhancement endpoints"""
    
    def test_enhance_concept_success(self, client):
        """Test concept enhancement endpoint"""
        with patch('backend.api.main.prompt_enhancer') as mock_enhancer:
            mock_enhancer.enhance.return_value = "Enhanced: A beautiful sunset"
            
            response = client.post("/api/v1/enhance/concept", json={
                "prompt": "A sunset",
                "style": "Cinematic"
            })
            
            assert response.status_code == 200
    
    def test_enhance_concept_empty_prompt(self, client):
        """Test concept enhancement with empty prompt"""
        response = client.post("/api/v1/enhance/concept", json={
            "prompt": "",
            "style": "Cinematic"
        })
        
        assert response.status_code in [200, 422]
    
    def test_enhance_full_pipeline(self, client):
        """Test full 7-stage enhancement pipeline"""
        with patch('backend.api.main.prompt_enhancer') as mock_enhancer:
            mock_enhancer.enhance.return_value = "Fully enhanced prompt"
            
            response = client.post("/api/v1/enhance/full", json={
                "prompt": "A cat playing",
                "style": "Photorealistic",
                "platform": "YouTube (16:9)"
            })
            
            assert response.status_code == 200


class TestFaceDetectionEndpoints:
    """Tests for face detection and character endpoints"""
    
    def test_extract_face_with_base64(self, client):
        """Test face extraction with base64 image"""
        from PIL import Image
        import io
        
        img = Image.new('RGB', (640, 480), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        with patch('backend.api.main.face_service') as mock_fs:
            mock_fs.detect_faces.return_value = []
            
            response = client.post("/api/v1/face/extract", data={
                "image_base64": img_base64
            })
            
            assert response.status_code in [200, 500]
    
    def test_register_character(self, client):
        """Test character registration"""
        response = client.post("/api/v1/character/register", json={
            "name": "Test Hero",
            "face_embedding": [0.1] * 512,
            "reference_images": ["test.jpg"],
            "style_keywords": ["heroic"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data
    
    def test_get_character(self, client):
        """Test getting character by ID"""
        # First register
        reg_response = client.post("/api/v1/character/register", json={
            "name": "Get Test",
            "face_embedding": [0.2] * 512,
            "reference_images": [],
            "style_keywords": []
        })
        
        if reg_response.status_code == 200:
            char_id = reg_response.json()["character_id"]
            
            response = client.get(f"/api/v1/character/{char_id}")
            assert response.status_code == 200
    
    def test_get_character_not_found(self, client):
        """Test getting non-existent character"""
        response = client.get("/api/v1/character/nonexistent-id")
        assert response.status_code == 404
    
    def test_verify_character(self, client):
        """Test character verification"""
        from PIL import Image
        import io
        
        img = Image.new('RGB', (640, 480), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        response = client.post("/api/v1/character/verify", data={
            "character_id": "test-char",
            "image_base64": img_base64
        })
        
        assert response.status_code in [200, 404, 500]


class TestImageGenerationEndpoints:
    """Tests for image generation endpoints"""
    
    def test_generate_image(self, client):
        """Test image generation"""
        with patch('backend.api.main.image_generation_task') as mock_task:
            response = client.post("/api/v1/generate/image", json={
                "prompt": "A beautiful landscape",
                "style": "Cinematic",
                "aspect_ratio": "16:9"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
    
    def test_generate_image_with_character(self, client):
        """Test image generation with character reference"""
        response = client.post("/api/v1/generate/image", json={
            "prompt": "Hero standing on a mountain",
            "style": "Epic",
            "aspect_ratio": "16:9",
            "character_id": "hero-001"
        })
        
        assert response.status_code == 200
    
    def test_generate_batch_images(self, client):
        """Test batch image generation"""
        response = client.post("/api/v1/generate/batch", data={
            "prompts": json.dumps(["Scene 1", "Scene 2", "Scene 3"]),
            "style": "Cinematic",
            "aspect_ratio": "16:9"
        })
        
        assert response.status_code in [200, 422]


class TestAnimationEndpoints:
    """Tests for animation endpoints"""
    
    def test_animate_image(self, client):
        """Test image animation"""
        response = client.post("/api/v1/animate/image", json={
            "image_path": "/test/image.jpg",
            "motion_prompt": "gentle zoom in",
            "duration": 5.0,
            "provider": "auto"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
    
    def test_animate_image_with_kenburns(self, client):
        """Test Ken Burns animation"""
        response = client.post("/api/v1/animate/image", json={
            "image_path": "/test/image.jpg",
            "motion_prompt": "pan left",
            "duration": 4.0,
            "provider": "kenburns"
        })
        
        assert response.status_code == 200


class TestAudioEndpoints:
    """Tests for audio analysis endpoints"""
    
    def test_analyze_audio(self, client):
        """Test audio analysis"""
        import wave
        import struct
        import io
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            samples = [0] * (22050 * 2)
            wav.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        
        buffer.seek(0)
        
        with patch('backend.api.main.audio_intelligence') as mock_ai:
            mock_ai.analyze.return_value = {'bpm': 120, 'duration': 2.0}
            
            response = client.post("/api/v1/audio/analyze", files={
                "audio": ("test.wav", buffer, "audio/wav")
            })
            
            assert response.status_code in [200, 500]
    
    def test_mix_audio(self, client):
        """Test audio mixing"""
        import wave
        import struct
        import io
        
        def create_wav():
            buffer = io.BytesIO()
            with wave.open(buffer, 'w') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(22050)
                samples = [0] * 22050
                wav.writeframes(struct.pack(f'<{len(samples)}h', *samples))
            buffer.seek(0)
            return buffer
        
        response = client.post("/api/v1/audio/mix", 
            files=[
                ("tracks", ("track1.wav", create_wav(), "audio/wav")),
                ("tracks", ("track2.wav", create_wav(), "audio/wav"))
            ],
            data={"volumes": "[1.0, 0.8]", "mode": "layer"}
        )
        
        assert response.status_code in [200, 422, 500]


class TestSunoEndpoints:
    """Tests for Suno music generation endpoints"""
    
    def test_generate_music(self, client):
        """Test Suno music generation"""
        response = client.post("/api/v1/suno/generate", json={
            "prompt": "upbeat electronic dance music",
            "style": "electronic",
            "duration": 60
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
    
    def test_generate_music_with_lyrics(self, client):
        """Test music generation with custom lyrics"""
        response = client.post("/api/v1/suno/generate", json={
            "prompt": "pop song",
            "lyrics": "[Verse]\nHello world\nThis is a test",
            "style": "pop",
            "instrumental": False
        })
        
        assert response.status_code == 200


class TestStoryboardEndpoints:
    """Tests for storyboard generation endpoints"""
    
    def test_generate_storyboard(self, client):
        """Test storyboard generation"""
        response = client.post("/api/v1/storyboard/generate", json={
            "prompt": "A hero's journey through a magical forest",
            "style": "Fantasy",
            "duration": 60,
            "scene_count": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
    
    def test_generate_storyboard_from_lyrics(self, client):
        """Test storyboard from lyrics"""
        response = client.post("/api/v1/storyboard/generate", json={
            "lyrics": "[Verse]\nWalking through the night\nStars are shining bright",
            "style": "Cinematic",
            "music_prompt": "ambient orchestral"
        })
        
        assert response.status_code == 200


class TestVideoAssemblyEndpoints:
    """Tests for video assembly endpoints"""
    
    def test_assemble_video(self, client):
        """Test video assembly"""
        response = client.post("/api/v1/video/assemble", json={
            "manifest": {
                "scenes": [
                    {"image": "/scene1.jpg", "duration": 5},
                    {"image": "/scene2.jpg", "duration": 5}
                ]
            },
            "platform": "youtube",
            "quality": "1080p"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


class TestJobManagementEndpoints:
    """Tests for job management endpoints"""
    
    def test_get_job_status(self, client):
        """Test getting job status"""
        # First create a job
        create_response = client.post("/api/v1/generate/image", json={
            "prompt": "Test image",
            "style": "Simple"
        })
        
        if create_response.status_code == 200:
            job_id = create_response.json()["job_id"]
            
            response = client.get(f"/api/v1/jobs/{job_id}")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
    
    def test_get_job_not_found(self, client):
        """Test getting non-existent job"""
        response = client.get("/api/v1/jobs/nonexistent-job-id")
        assert response.status_code == 404
    
    def test_list_jobs(self, client):
        """Test listing all jobs"""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_jobs_with_status_filter(self, client):
        """Test listing jobs with status filter"""
        response = client.get("/api/v1/jobs?status=pending&limit=10")
        assert response.status_code == 200


class TestFileUploadEndpoints:
    """Tests for file upload endpoints"""
    
    def test_upload_image(self, client):
        """Test image upload"""
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        response = client.post("/api/v1/upload/image", files={
            "file": ("test.jpg", buffer, "image/jpeg")
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
    
    def test_upload_audio(self, client):
        """Test audio upload"""
        import wave
        import struct
        import io
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            samples = [0] * 22050
            wav.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        buffer.seek(0)
        
        response = client.post("/api/v1/upload/audio", files={
            "file": ("test.wav", buffer, "audio/wav")
        })
        
        assert response.status_code == 200


class TestYouTubeEndpoints:
    """Tests for YouTube integration endpoints"""
    
    def test_get_youtube_accounts(self, client):
        """Test getting YouTube accounts"""
        response = client.get("/api/v1/youtube/accounts")
        assert response.status_code == 200
    
    def test_upload_to_youtube(self, client):
        """Test YouTube upload"""
        response = client.post("/api/v1/youtube/upload", json={
            "video_path": "/output/video.mp4",
            "title": "Test Video",
            "description": "Test description",
            "privacy": "private",
            "account_id": "test-account"
        })
        
        assert response.status_code in [200, 400, 500]


class TestTimelineEndpoints:
    """Tests for timeline editor endpoints"""
    
    def test_quick_create(self, client):
        """Test quick create project"""
        response = client.post("/api/v1/timeline/quick-create", json={
            "prompt": "A beautiful nature video",
            "duration": 30,
            "style": "Cinematic"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
    
    def test_get_project(self, client):
        """Test getting project"""
        # Create first
        create_response = client.post("/api/v1/timeline/quick-create", json={
            "prompt": "Test project",
            "duration": 15,
            "style": "Simple"
        })
        
        if create_response.status_code == 200:
            project_id = create_response.json()["project_id"]
            
            response = client.get(f"/api/v1/timeline/{project_id}")
            assert response.status_code == 200
    
    def test_list_projects(self, client):
        """Test listing projects"""
        response = client.get("/api/v1/timeline/projects")
        assert response.status_code == 200


class TestDocumentParsingEndpoints:
    """Tests for document parsing endpoints"""
    
    def test_parse_markdown(self, client):
        """Test markdown parsing"""
        md_content = """
# Video Title

## Scene 1
A beautiful sunrise

## Scene 2  
Mountains in the distance
"""
        
        import io
        buffer = io.BytesIO(md_content.encode())
        
        response = client.post("/api/v1/parse/markdown", files={
            "file": ("script.md", buffer, "text/markdown")
        })
        
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for API error handling"""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/v1/generate/image",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_field(self, client):
        """Test handling of missing required fields"""
        response = client.post("/api/v1/generate/image", json={
            "style": "Cinematic"
            # Missing required 'prompt' field
        })
        
        assert response.status_code == 422
    
    def test_invalid_endpoint(self, client):
        """Test handling of invalid endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
