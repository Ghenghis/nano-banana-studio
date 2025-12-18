"""
Timeline Editor API Tests
=========================
Test all timeline editor endpoints.

Run with: python -m pytest tests/test_timeline_editor.py -v
Or standalone: python tests/test_timeline_editor.py
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1/timeline"


async def test_timeline_workflow():
    """Test complete Simple Mode workflow"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "="*60)
        print("★ TIMELINE EDITOR API TESTS ★")
        print("="*60)
        
        # 1. Quick Create (Simple Mode)
        print("\n[1] Testing Quick Create...")
        try:
            resp = await client.post(
                f"{BASE_URL}/quick-create",
                json={
                    "prompt": "A magical cat exploring an enchanted forest",
                    "duration": 30,
                    "style": "Cinematic",
                    "music_prompt": "whimsical orchestral"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                project_id = data.get("project_id")
                print(f"   ✓ Created project: {project_id}")
                print(f"   ✓ Scenes: {data.get('scene_count')}")
                print(f"   ✓ Duration: {data.get('total_duration')}s")
            else:
                print(f"   ✗ Failed: {resp.status_code} - {resp.text}")
                project_id = None
        except Exception as e:
            print(f"   ✗ Error: {e}")
            project_id = None
        
        if not project_id:
            print("\nCannot continue without project_id. Is the server running?")
            return
        
        # 2. Get Preview Gallery
        print("\n[2] Testing Preview Gallery...")
        try:
            resp = await client.get(f"{BASE_URL}/{project_id}/preview-gallery")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Got {len(data.get('scenes', []))} scenes")
                print(f"   ✓ Status: {data.get('status')}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 3. Get Timeline View
        print("\n[3] Testing Timeline View...")
        try:
            resp = await client.get(f"{BASE_URL}/{project_id}/timeline")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Timeline mode: {data.get('mode')}")
                print(f"   ✓ Duration: {data.get('duration_formatted')}")
                print(f"   ✓ Video track: {len(data.get('video_track', []))} scenes")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 4. Get Scene Details
        print("\n[4] Testing Get Scene...")
        try:
            resp = await client.get(f"{BASE_URL}/{project_id}/scenes/1")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Scene 1 prompt: {data.get('visual_prompt', '')[:50]}...")
                print(f"   ✓ Duration: {data.get('duration')}s")
                print(f"   ✓ Status: {data.get('status')}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 5. Approve Scene
        print("\n[5] Testing Approve Scene...")
        try:
            resp = await client.post(f"{BASE_URL}/{project_id}/scenes/1/approve")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Approved: {data.get('success')}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 6. Approve All
        print("\n[6] Testing Approve All...")
        try:
            resp = await client.post(f"{BASE_URL}/{project_id}/approve-all")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Approved count: {data.get('approved_count')}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 7. Add Scene (Advanced)
        print("\n[7] Testing Add Scene...")
        try:
            resp = await client.post(
                f"{BASE_URL}/{project_id}/scenes",
                data={
                    "prompt": "The cat finds a magical crystal",
                    "duration": "5.0",
                    "style": "Cinematic"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Added scene {data.get('index')}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 8. Set Camera Movement
        print("\n[8] Testing Set Camera...")
        try:
            resp = await client.post(
                f"{BASE_URL}/{project_id}/scenes/1/camera",
                data={"movement": "zoom_in", "intensity": "70"}
            )
            if resp.status_code == 200:
                print(f"   ✓ Camera set to zoom_in")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 9. Set Transition
        print("\n[9] Testing Set Transition...")
        try:
            resp = await client.post(
                f"{BASE_URL}/{project_id}/scenes/1/transition",
                data={"transition_type": "dissolve", "duration": "0.5"}
            )
            if resp.status_code == 200:
                print(f"   ✓ Transition set to dissolve")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 10. Set Color Grade
        print("\n[10] Testing Color Grade...")
        try:
            resp = await client.post(
                f"{BASE_URL}/{project_id}/scenes/1/color-grade",
                data={"preset": "cinematic"}
            )
            if resp.status_code == 200:
                print(f"   ✓ Color grade set to cinematic")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 11. Duplicate Scene
        print("\n[11] Testing Duplicate Scene...")
        try:
            resp = await client.post(f"{BASE_URL}/{project_id}/scenes/1/duplicate")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Duplicated to scene {data.get('index')}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 12. Set Speed
        print("\n[12] Testing Set Speed...")
        try:
            resp = await client.post(
                f"{BASE_URL}/{project_id}/scenes/1/speed",
                data={"speed": "0.5"}
            )
            if resp.status_code == 200:
                print(f"   ✓ Speed set to 0.5x (slow motion)")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 13. Undo
        print("\n[13] Testing Undo...")
        try:
            resp = await client.post(f"{BASE_URL}/{project_id}/undo")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Undo result: {data}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 14. Redo
        print("\n[14] Testing Redo...")
        try:
            resp = await client.post(f"{BASE_URL}/{project_id}/redo")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ Redo result: {data}")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # 15. List Projects
        print("\n[15] Testing List Projects...")
        try:
            resp = await client.get(f"{BASE_URL}/projects")
            if resp.status_code == 200:
                data = resp.json()
                projects = data.get("projects", [])
                print(f"   ✓ Found {len(projects)} project(s)")
            else:
                print(f"   ✗ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print("\n" + "="*60)
        print("★ TESTS COMPLETE ★")
        print("="*60)


if __name__ == "__main__":
    print("Timeline Editor API Test Suite")
    print("Make sure the server is running on http://localhost:8000")
    asyncio.run(test_timeline_workflow())
