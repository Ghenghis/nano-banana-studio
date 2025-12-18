"""
Nano Banana Studio Pro - Test Configuration
=============================================
Pytest configuration and shared fixtures.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "gpu: marks tests requiring GPU")


# =============================================================================
# ASYNC SUPPORT
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# ENVIRONMENT FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("THUMBNAILS_DIR", str(tmp_path / "thumbnails"))
    
    # Create directories
    for subdir in ["outputs", "uploads", "cache", "temp", "thumbnails"]:
        (tmp_path / subdir).mkdir(exist_ok=True)


# =============================================================================
# API CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def test_client():
    """Create FastAPI test client"""
    from fastapi.testclient import TestClient
    from backend.api.main import app
    
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing"""
    import httpx
    from backend.api.main import app
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_prompt():
    """Sample prompt for testing"""
    return "A beautiful sunset over the ocean with silhouettes of palm trees"


@pytest.fixture
def sample_lyrics():
    """Sample lyrics for testing"""
    return """
[Verse 1]
Walking down the street tonight
Under the silver moonlight
Every star is shining bright
Everything feels just right

[Chorus]
We are the dreamers of the night
Chasing stars until daylight
Nothing can stop our flight
We are the dreamers of the night
"""


@pytest.fixture
def sample_storyboard_request():
    """Sample storyboard request"""
    return {
        "prompt": "Epic journey through a magical forest",
        "style": "Cinematic",
        "duration": 60.0,
        "scene_count": 6
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for storyboard generation"""
    import json
    return json.dumps({
        "title": "Magical Forest Journey",
        "scenes": [
            {
                "index": 1,
                "visual_prompt": "Wide establishing shot of ancient forest entrance",
                "scene_type": "establishing",
                "camera_move": "zoom_in",
                "mood": "mysterious",
                "lighting": "dappled sunlight"
            },
            {
                "index": 2,
                "visual_prompt": "Close-up of glowing mushrooms on forest floor",
                "scene_type": "closeup",
                "camera_move": "static",
                "mood": "magical",
                "lighting": "bioluminescent"
            }
        ]
    })


@pytest.fixture
def mock_audio_analysis():
    """Mock audio analysis result"""
    return {
        "duration": 60.0,
        "bpm": 120,
        "beats": [i * 0.5 for i in range(120)],
        "energy_curve": [0.5] * 240,
        "sections": [
            {"type": "intro", "start": 0, "end": 10},
            {"type": "verse", "start": 10, "end": 30},
            {"type": "chorus", "start": 30, "end": 50},
            {"type": "outro", "start": 50, "end": 60}
        ]
    }
