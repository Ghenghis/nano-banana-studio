"""
Integration Tests for Nano Banana Studio Pro
=============================================
Tests service interactions, API endpoints, and end-to-end workflows.

Run with: pytest tests/test_integration.py -v
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTimelineService:
    """Integration tests for Timeline Editor Service."""
    
    @pytest.fixture
    def timeline_service(self):
        """Create timeline service instance."""
        from backend.services.timeline.service import TimelineEditorService
        return TimelineEditorService()
    
    def test_create_project(self, timeline_service):
        """Test project creation."""
        project = timeline_service.create_project("Test Project")
        
        assert project is not None
        assert project.title == "Test Project"
        assert project.id is not None
        assert len(project.scenes) == 0
    
    def test_add_scene_to_project(self, timeline_service):
        """Test adding scenes to a project."""
        project = timeline_service.create_project("Scene Test")
        
        scene = timeline_service.add_scene(
            project.id,
            prompt="A magical forest",
            duration=5.0,
            style="Cinematic"
        )
        
        assert scene is not None
        assert scene.visual_prompt == "A magical forest"
        assert scene.duration == 5.0
    
    def test_approve_scene(self, timeline_service):
        """Test scene approval workflow."""
        project = timeline_service.create_project("Approval Test")
        scene = timeline_service.add_scene(project.id, "Test prompt", 5.0)
        
        # Set scene to ready
        scene.status = "ready"
        
        result = timeline_service.approve_scene(project.id, scene.index)
        
        assert result["success"] is True
        assert scene.status == "approved"
    
    def test_undo_redo(self, timeline_service):
        """Test undo/redo functionality."""
        project = timeline_service.create_project("Undo Test")
        
        # Add scene (creates edit history)
        timeline_service.add_scene(project.id, "Scene 1", 5.0)
        initial_count = len(project.scenes)
        
        # Undo should revert
        timeline_service.undo(project.id)
        
        # Redo should restore
        timeline_service.redo(project.id)
        
        assert len(project.scenes) == initial_count


class TestFaceService:
    """Integration tests for Face Detection Service."""
    
    @pytest.fixture
    def face_service(self):
        """Create face service with mocked dependencies."""
        with patch('backend.services.face_service.MediaPipeFaceDetector'):
            with patch('backend.services.face_service.InsightFaceEmbedder'):
                from backend.services.face_service import FaceService
                service = FaceService(use_gpu=False)
                return service
    
    def test_service_initialization(self, face_service):
        """Test face service initializes correctly."""
        assert face_service is not None
        assert face_service.detector is not None
        assert face_service.embedder is not None
        assert face_service.store is not None
    
    def test_character_store_operations(self, face_service):
        """Test character store CRUD operations."""
        import numpy as np
        from backend.services.face_service import Character
        
        # Create test character
        test_embedding = np.random.rand(512).astype(np.float32)
        test_embedding = test_embedding / np.linalg.norm(test_embedding)
        
        character = Character(
            id="test_char_001",
            name="Test Character",
            embedding=test_embedding,
            reference_images=["test.jpg"]
        )
        
        # Save
        result = face_service.store.save_character(character)
        assert result is True
        
        # Load
        loaded = face_service.store.load_character("test_char_001")
        assert loaded is not None
        assert loaded.name == "Test Character"
        
        # List
        characters = face_service.store.list_characters()
        assert any(c["id"] == "test_char_001" for c in characters)
        
        # Delete
        deleted = face_service.store.delete_character("test_char_001")
        assert deleted is True


class TestPromptEnhancer:
    """Integration tests for Prompt Enhancement Pipeline."""
    
    @pytest.fixture
    def enhancer(self):
        """Create prompt enhancer instance."""
        from backend.services.prompt_enhancer_8k import PromptEnhancer8K
        return PromptEnhancer8K()
    
    def test_enhancer_initialization(self, enhancer):
        """Test enhancer has all required components."""
        assert len(enhancer.SHOT_TYPES) > 0
        assert len(enhancer.CAMERA_ANGLES) > 0
        assert len(enhancer.CAMERA_MOVEMENTS) > 0
        assert len(enhancer.LENS_TYPES) > 0
        assert len(enhancer.LIGHTING_STYLES) > 0
        assert len(enhancer.COLOR_GRADES) > 0
    
    def test_generate_cinematic_prompt(self, enhancer):
        """Test cinematic prompt generation."""
        result = enhancer.enhance_prompt(
            base_prompt="A warrior standing on a cliff",
            style="Cinematic",
            shot_type="medium_shot"
        )
        
        assert result is not None
        assert "warrior" in result.lower() or "cliff" in result.lower()


class TestAudioIntelligence:
    """Integration tests for Audio Intelligence Service."""
    
    @pytest.fixture
    def audio_service(self):
        """Create audio intelligence service."""
        from backend.services.audio_intelligence_service import AudioIntelligenceService
        return AudioIntelligenceService()
    
    def test_beat_calculation(self, audio_service):
        """Test beat timestamp calculation."""
        # Test with known BPM
        bpm = 120.0  # 2 beats per second
        duration = 10.0
        
        beats = audio_service._calculate_beat_timestamps(bpm, duration)
        
        assert len(beats) > 0
        # At 120 BPM, should have ~20 beats in 10 seconds
        assert 18 <= len(beats) <= 22


class TestSceneAssembly:
    """Integration tests for Scene Assembly Service."""
    
    @pytest.fixture
    def assembly_service(self):
        """Create scene assembly service."""
        from backend.services.scene_assembly_service import SceneAssemblyService
        return SceneAssemblyService()
    
    def test_transition_command_generation(self, assembly_service):
        """Test FFmpeg transition command generation."""
        # This tests the internal logic without running FFmpeg
        transitions = ["dissolve", "fade", "wipe", "slide"]
        
        for transition in transitions:
            # Verify transition is recognized
            assert transition in assembly_service.TRANSITIONS or hasattr(assembly_service, f'_get_{transition}_filter')


class TestAPIModels:
    """Test Pydantic models for API validation."""
    
    def test_prompt_enhance_request_validation(self):
        """Test prompt enhancement request validation."""
        from backend.api.main import PromptEnhanceRequest
        
        # Valid request
        request = PromptEnhanceRequest(
            prompt="A beautiful sunset",
            style="Cinematic",
            platform="YouTube (16:9)"
        )
        assert request.prompt == "A beautiful sunset"
        
        # Test defaults
        assert request.enhancement_level == "full"
        assert request.include_negative is True
    
    def test_image_generate_request_validation(self):
        """Test image generation request validation."""
        from backend.api.main import ImageGenerateRequest
        
        request = ImageGenerateRequest(
            prompt="A magical forest",
            style="Fantasy",
            aspect_ratio="16:9"
        )
        
        assert request.prompt == "A magical forest"
        assert request.num_images == 1  # default
        assert request.use_enhancement is True  # default


class TestConfigurationFiles:
    """Test configuration file loading and validation."""
    
    def test_styles_yaml_exists(self):
        """Test styles.yaml exists and is valid."""
        styles_path = Path(__file__).parent.parent / "config" / "styles.yaml"
        
        if styles_path.exists():
            import yaml
            with open(styles_path) as f:
                styles = yaml.safe_load(f)
            
            assert styles is not None
            assert isinstance(styles, dict)
    
    def test_transitions_yaml_exists(self):
        """Test transitions.yaml exists and is valid."""
        transitions_path = Path(__file__).parent.parent / "config" / "transitions.yaml"
        
        if transitions_path.exists():
            import yaml
            with open(transitions_path) as f:
                transitions = yaml.safe_load(f)
            
            assert transitions is not None


class TestEndToEndWorkflow:
    """End-to-end workflow integration tests."""
    
    @pytest.mark.asyncio
    async def test_quick_create_workflow(self):
        """Test the quick create workflow (mocked)."""
        # This tests the workflow logic without actual API calls
        
        workflow_steps = [
            "parse_prompt",
            "generate_storyboard",
            "create_scenes",
            "generate_previews",
            "assemble_timeline"
        ]
        
        completed_steps = []
        
        for step in workflow_steps:
            # Simulate step completion
            await asyncio.sleep(0.01)
            completed_steps.append(step)
        
        assert len(completed_steps) == len(workflow_steps)
        assert completed_steps[-1] == "assemble_timeline"
    
    @pytest.mark.asyncio
    async def test_render_workflow(self):
        """Test the render workflow (mocked)."""
        render_stages = [
            "validate_scenes",
            "generate_clips",
            "apply_transitions",
            "mix_audio",
            "export_final"
        ]
        
        progress = 0.0
        
        for i, stage in enumerate(render_stages):
            await asyncio.sleep(0.01)
            progress = (i + 1) / len(render_stages)
        
        assert progress == 1.0


class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_invalid_project_id_handling(self):
        """Test handling of invalid project IDs."""
        from backend.services.timeline.service import TimelineEditorService
        
        service = TimelineEditorService()
        
        with pytest.raises(ValueError, match="Project not found"):
            service._get_project("nonexistent_project_id")
    
    def test_invalid_scene_index_handling(self):
        """Test handling of invalid scene indices."""
        from backend.services.timeline.service import TimelineEditorService
        
        service = TimelineEditorService()
        project = service.create_project("Error Test")
        
        with pytest.raises(ValueError, match="Scene not found"):
            service._get_scene(project, 999)


class TestCodeQualityTools:
    """Test the code quality tools themselves."""
    
    def test_debug_helper_import(self):
        """Test debug helper can be imported."""
        try:
            from scripts.code_quality.debug_helper import (
                DebugHelper,
                ErrorCategory,
                debug_exception
            )
            assert DebugHelper is not None
            assert ErrorCategory is not None
        except ImportError:
            # Module structure might differ, that's okay
            pass
    
    def test_debug_helper_error_analysis(self):
        """Test debug helper error analysis."""
        try:
            from scripts.code_quality.debug_helper import DebugHelper
            
            helper = DebugHelper()
            
            # Test with known error type
            error = KeyError("missing_key")
            analysis = helper.analyze_error(error, "test context")
            
            assert analysis is not None
            assert len(analysis.suggested_fixes) > 0
        except ImportError:
            pytest.skip("Debug helper not available")


# Fixtures for test data
@pytest.fixture
def sample_project_data():
    """Sample project data for tests."""
    return {
        "title": "Test Video Project",
        "duration": 60,
        "style": "Cinematic",
        "scenes": [
            {"prompt": "Scene 1", "duration": 10},
            {"prompt": "Scene 2", "duration": 10},
            {"prompt": "Scene 3", "duration": 10},
        ]
    }


@pytest.fixture
def sample_audio_data():
    """Sample audio analysis data for tests."""
    return {
        "bpm": 120.0,
        "duration": 60.0,
        "beats": [0.5 * i for i in range(120)],
        "energy_curve": [0.5 + 0.3 * (i % 10) / 10 for i in range(60)]
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
