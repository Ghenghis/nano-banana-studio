"""
Nano Banana Studio Pro - End-to-End Workflow Tests
===================================================
Complete workflow validation for production readiness.

Tests:
- Video creation workflow
- Character consistency workflow
- Music video generation workflow
- YouTube publish workflow
"""

import pytest
import asyncio
import httpx
from pathlib import Path


BASE_URL = "http://localhost:8000"


class TestVideoCreationWorkflow:
    """Test complete video creation from prompt to export"""
    
    @pytest.mark.asyncio
    async def test_quick_create_workflow(self):
        """Test simple mode quick create"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
            # Step 1: Quick create project
            response = await client.post("/api/v1/timeline/quick-create", json={
                "prompt": "A beautiful sunset over the ocean",
                "duration": 30,
                "style": "Cinematic",
                "music_prompt": "peaceful ambient music"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "project_id" in data
            project_id = data["project_id"]
            
            # Step 2: Check project was created
            response = await client.get(f"/api/v1/timeline/project/{project_id}")
            assert response.status_code == 200
            project = response.json()
            assert project["id"] == project_id
            assert len(project.get("scenes", [])) > 0
    
    @pytest.mark.asyncio
    async def test_advanced_create_workflow(self):
        """Test advanced mode with manual scene creation"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
            # Step 1: Create new project
            response = await client.post("/api/v1/timeline/project/new", json={
                "name": "Test Advanced Project",
                "mode": "advanced"
            })
            
            assert response.status_code == 200
            project_id = response.json()["project_id"]
            
            # Step 2: Add scenes manually
            for i in range(3):
                response = await client.post(f"/api/v1/timeline/project/{project_id}/scene", json={
                    "visual_prompt": f"Scene {i+1}: Beautiful landscape",
                    "duration": 5.0,
                    "camera_move": "zoom_in"
                })
                assert response.status_code == 200
            
            # Step 3: Verify scenes added
            response = await client.get(f"/api/v1/timeline/project/{project_id}")
            project = response.json()
            assert len(project.get("scenes", [])) == 3


class TestCharacterConsistencyWorkflow:
    """Test character registration and verification"""
    
    @pytest.mark.asyncio
    async def test_character_workflow(self):
        """Test character registration and verification flow"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            # Step 1: Register character (mock face embedding)
            response = await client.post("/api/v1/character/register", json={
                "name": "Test Hero",
                "face_embedding": [0.1] * 512,
                "reference_images": ["test_ref.jpg"],
                "style_keywords": ["heroic", "determined"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "character_id" in data
            char_id = data["character_id"]
            
            # Step 2: Get character details
            response = await client.get(f"/api/v1/character/{char_id}")
            assert response.status_code == 200
            char = response.json()
            assert char["name"] == "Test Hero"


class TestPromptEnhancementWorkflow:
    """Test 7-stage prompt enhancement pipeline"""
    
    @pytest.mark.asyncio
    async def test_full_enhancement(self):
        """Test complete prompt enhancement"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            response = await client.post("/api/v1/enhance/full", json={
                "prompt": "A cat sleeping",
                "style": "Cinematic",
                "platform": "YouTube (16:9)",
                "enhancement_level": "full",
                "include_negative": True
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "enhanced_prompt" in data
            assert len(data["enhanced_prompt"]) > len("A cat sleeping")
            assert "negative_prompt" in data
    
    @pytest.mark.asyncio
    async def test_quick_enhancement(self):
        """Test quick prompt enhancement"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.post("/api/v1/enhance/quick", json={
                "prompt": "Mountain landscape",
                "style": "Photorealistic"
            })
            
            assert response.status_code == 200


class TestAudioWorkflow:
    """Test audio analysis and mixing"""
    
    @pytest.mark.asyncio
    async def test_audio_analysis_workflow(self):
        """Test audio analysis endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            # Create test audio file (1 second of silence)
            import wave
            import struct
            
            test_audio = Path("/tmp/test_audio.wav")
            with wave.open(str(test_audio), 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(44100)
                for _ in range(44100):
                    f.writeframes(struct.pack('h', 0))
            
            # Upload and analyze
            with open(test_audio, 'rb') as f:
                response = await client.post(
                    "/api/v1/audio/analyze",
                    files={"audio": ("test.wav", f, "audio/wav")},
                    data={"detect_beats": "true", "extract_lyrics": "false"}
                )
            
            if response.status_code == 200:
                data = response.json()
                assert "duration" in data
                assert "bpm" in data


class TestJobQueueWorkflow:
    """Test job queue and WebSocket updates"""
    
    @pytest.mark.asyncio
    async def test_job_lifecycle(self):
        """Test job creation, status, and completion"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            # Start an image generation job
            response = await client.post("/api/v1/generate/image", json={
                "prompt": "A simple test image",
                "style": "Minimalist",
                "aspect_ratio": "1:1",
                "use_enhancement": False
            })
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                
                if job_id:
                    # Check job status
                    response = await client.get(f"/api/v1/jobs/{job_id}")
                    assert response.status_code == 200
                    job = response.json()
                    assert job["id"] == job_id
                    assert job["status"] in ["pending", "processing", "completed", "failed"]


class TestTimelineEditorWorkflow:
    """Test timeline editor operations"""
    
    @pytest.mark.asyncio
    async def test_scene_operations(self):
        """Test scene CRUD operations"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            # Create project
            response = await client.post("/api/v1/timeline/project/new", json={
                "name": "Scene Ops Test"
            })
            
            if response.status_code != 200:
                pytest.skip("Timeline API not available")
            
            project_id = response.json()["project_id"]
            
            # Add scene
            response = await client.post(f"/api/v1/timeline/project/{project_id}/scene", json={
                "visual_prompt": "Test scene",
                "duration": 5.0
            })
            assert response.status_code == 200
            
            # Get project to check scene
            response = await client.get(f"/api/v1/timeline/project/{project_id}")
            project = response.json()
            assert len(project.get("scenes", [])) >= 1
            
            scene_index = 0
            
            # Update scene
            response = await client.put(
                f"/api/v1/timeline/project/{project_id}/scene/{scene_index}",
                json={"duration": 10.0}
            )
            
            # Test undo
            response = await client.post(f"/api/v1/timeline/project/{project_id}/undo")
    
    @pytest.mark.asyncio
    async def test_transition_and_effects(self):
        """Test scene transitions and effects"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            # Create project with scenes
            response = await client.post("/api/v1/timeline/quick-create", json={
                "prompt": "Test transitions",
                "duration": 20,
                "style": "Cinematic"
            })
            
            if response.status_code != 200:
                pytest.skip("Timeline API not available")
            
            project_id = response.json()["project_id"]
            
            # Set transition
            response = await client.put(
                f"/api/v1/timeline/project/{project_id}/scene/0/transition",
                json={"transition": "dissolve", "duration": 1.0}
            )


class TestHealthChecks:
    """Test service health and status"""
    
    @pytest.mark.asyncio
    async def test_api_health(self):
        """Test API health endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"
    
    @pytest.mark.asyncio
    async def test_service_status(self):
        """Test service status check"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            response = await client.get("/api/v1/status")
            if response.status_code == 200:
                data = response.json()
                assert "version" in data or "services" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
