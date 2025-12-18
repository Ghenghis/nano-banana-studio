"""
Nano Banana Studio Pro - ComfyUI Integration Service
=====================================================
Headless ComfyUI orchestration for advanced image/video generation.

Supports:
- Nano Banana Pro (Gemini 3 Pro Image) via API node
- LTX-Video 0.9.5 for keyframe video generation
- SDXL/Flux for local generation
- IPAdapter/InstantID for character consistency
- 14-image blending for multi-reference consistency
"""

import os
import json
import uuid
import asyncio
import hashlib
import logging
import websockets
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from enum import Enum
import httpx

logger = logging.getLogger("comfyui-service")

# Configuration
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")
COMFYUI_WS_URL = os.getenv("COMFYUI_WS_URL", "ws://localhost:8188/ws")
COMFYUI_OUTPUT_DIR = Path(os.getenv("COMFYUI_OUTPUT_DIR", "/app/comfyui/output"))


class ComfyUIModel(Enum):
    """Available models in ComfyUI"""
    NANO_BANANA_PRO = "nano_banana_pro"
    SDXL = "sdxl"
    FLUX_SCHNELL = "flux_schnell"
    FLUX_DEV = "flux_dev"
    LTX_VIDEO = "ltx_video"
    STABLE_VIDEO_DIFFUSION = "svd"
    WAN_VIDEO = "wan_video"


@dataclass
class ComfyUIJob:
    """ComfyUI job tracking"""
    prompt_id: str
    client_id: str
    workflow: Dict
    status: str = "queued"
    progress: float = 0.0
    outputs: List[str] = None
    error: Optional[str] = None


class ComfyUIWorkflowBuilder:
    """Build ComfyUI workflows programmatically"""
    
    def __init__(self):
        self.nodes = {}
        self.node_id = 0
    
    def _next_id(self) -> str:
        self.node_id += 1
        return str(self.node_id)
    
    def add_node(self, class_type: str, inputs: Dict, title: str = None) -> str:
        node_id = self._next_id()
        self.nodes[node_id] = {
            "class_type": class_type,
            "inputs": inputs,
            "_meta": {"title": title or class_type}
        }
        return node_id
    
    def link(self, from_node: str, from_output: int = 0) -> List:
        return [from_node, from_output]
    
    def build(self) -> Dict:
        return self.nodes
    
    @classmethod
    def nano_banana_text_to_image(
        cls, prompt: str, negative_prompt: str = "",
        width: int = 1920, height: int = 1080,
        aspect_ratio: str = "16:9", seed: int = -1
    ) -> Dict:
        """Nano Banana Pro text-to-image workflow"""
        builder = cls()
        
        nano_node = builder.add_node(
            "NanoBananaPro",
            {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "seed": seed if seed >= 0 else -1,
                "output_format": "png"
            },
            title="Nano Banana Pro"
        )
        
        builder.add_node(
            "SaveImage",
            {"images": builder.link(nano_node, 0), "filename_prefix": "nano_banana"},
            title="Save Output"
        )
        
        return builder.build()
    
    @classmethod
    def nano_banana_multi_reference(
        cls, prompt: str, reference_images: List[str],
        blend_mode: str = "balanced", negative_prompt: str = "",
        width: int = 1920, height: int = 1080
    ) -> Dict:
        """Multi-reference blending (up to 14 images)"""
        builder = cls()
        
        image_nodes = []
        for i, img_path in enumerate(reference_images[:14]):
            node_id = builder.add_node(
                "LoadImage", {"image": img_path}, title=f"Reference {i+1}"
            )
            image_nodes.append(node_id)
        
        if len(image_nodes) > 1:
            batch_node = builder.add_node(
                "ImageBatch",
                {"images": [builder.link(n, 0) for n in image_nodes]},
                title="Batch References"
            )
            image_input = builder.link(batch_node, 0)
        else:
            image_input = builder.link(image_nodes[0], 0)
        
        nano_node = builder.add_node(
            "NanoBananaProMultiRef",
            {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "reference_images": image_input,
                "blend_mode": blend_mode,
                "width": width,
                "height": height,
                "maintain_character": True
            },
            title="Multi-Reference Generation"
        )
        
        builder.add_node(
            "SaveImage",
            {"images": builder.link(nano_node, 0), "filename_prefix": "multi_ref"}
        )
        
        return builder.build()
    
    @classmethod
    def ltx_video_from_image(
        cls, image_path: str, prompt: str,
        num_frames: int = 97, fps: int = 24,
        motion_strength: float = 0.8,
        use_keyframes: bool = False,
        keyframe_images: List[str] = None
    ) -> Dict:
        """LTX-Video 0.9.5 image-to-video workflow"""
        builder = cls()
        
        load_node = builder.add_node(
            "LoadImage", {"image": image_path}, title="Start Frame"
        )
        
        model_node = builder.add_node(
            "LTXVideoModelLoader",
            {"model_name": "ltx-video-0.9.5.safetensors", "precision": "fp16"},
            title="Load LTX-Video"
        )
        
        extra_cond = None
        if use_keyframes and keyframe_images:
            kf_nodes = []
            for i, kf_path in enumerate(keyframe_images):
                kf_node = builder.add_node(
                    "LoadImage", {"image": kf_path}, title=f"Keyframe {i+1}"
                )
                kf_nodes.append(kf_node)
            
            kf_cond = builder.add_node(
                "LTXVideoKeyframeConditioning",
                {
                    "keyframes": [builder.link(n, 0) for n in kf_nodes],
                    "frame_indices": list(range(0, num_frames, num_frames // len(kf_nodes)))
                },
                title="Keyframe Control"
            )
            extra_cond = builder.link(kf_cond, 0)
        
        sampler_inputs = {
            "model": builder.link(model_node, 0),
            "image": builder.link(load_node, 0),
            "prompt": prompt,
            "num_frames": num_frames,
            "fps": fps,
            "motion_strength": motion_strength,
            "seed": -1,
            "steps": 30,
            "cfg": 7.0
        }
        
        if extra_cond:
            sampler_inputs["keyframe_conditioning"] = extra_cond
        
        video_node = builder.add_node(
            "LTXVideoSampler", sampler_inputs, title="Generate Video"
        )
        
        builder.add_node(
            "SaveAnimatedWEBP",
            {"images": builder.link(video_node, 0), "filename_prefix": "ltx_video", "fps": fps, "quality": 95},
            title="Save Video"
        )
        
        return builder.build()


class ComfyUIService:
    """Service for interacting with headless ComfyUI"""
    
    def __init__(self, base_url: str = None, ws_url: str = None):
        self.base_url = base_url or COMFYUI_URL
        self.ws_url = ws_url or COMFYUI_WS_URL
        self.client_id = str(uuid.uuid4())
        self.active_jobs: Dict[str, ComfyUIJob] = {}
    
    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/system_stats", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"ComfyUI health check failed: {e}")
            return False
    
    async def upload_image(self, image_path: str, subfolder: str = "input") -> str:
        async with httpx.AsyncClient() as client:
            with open(image_path, "rb") as f:
                files = {"image": (Path(image_path).name, f, "image/png")}
                data = {"subfolder": subfolder, "type": "input"}
                response = await client.post(f"{self.base_url}/upload/image", files=files, data=data)
                if response.status_code == 200:
                    return response.json().get("name")
        raise Exception(f"Failed to upload image: {image_path}")
    
    async def queue_workflow(self, workflow: Dict) -> str:
        payload = {"prompt": workflow, "client_id": self.client_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/prompt", json=payload)
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")
                self.active_jobs[prompt_id] = ComfyUIJob(
                    prompt_id=prompt_id, client_id=self.client_id, workflow=workflow
                )
                return prompt_id
        raise Exception("Failed to queue workflow")
    
    async def wait_for_completion(self, prompt_id: str, timeout: float = 300.0, progress_callback=None) -> Dict[str, Any]:
        outputs = []
        try:
            async with websockets.connect(f"{self.ws_url}?clientId={self.client_id}") as ws:
                start_time = asyncio.get_event_loop().time()
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        raise TimeoutError(f"Workflow timeout after {timeout}s")
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(message)
                        msg_type = data.get("type")
                        msg_data = data.get("data", {})
                        
                        if msg_type == "progress":
                            value = msg_data.get("value", 0)
                            max_val = msg_data.get("max", 100)
                            progress = value / max_val if max_val > 0 else 0
                            if prompt_id in self.active_jobs:
                                self.active_jobs[prompt_id].progress = progress
                            if progress_callback:
                                await progress_callback(progress)
                        elif msg_type == "executing":
                            node_id = msg_data.get("node")
                            if node_id is None and msg_data.get("prompt_id") == prompt_id:
                                break
                        elif msg_type == "executed":
                            if msg_data.get("prompt_id") == prompt_id:
                                output = msg_data.get("output", {})
                                if "images" in output:
                                    for img in output["images"]:
                                        outputs.append({
                                            "filename": img["filename"],
                                            "subfolder": img.get("subfolder", ""),
                                            "type": img.get("type", "output")
                                        })
                        elif msg_type == "execution_error":
                            error = msg_data.get("exception_message", "Unknown error")
                            raise Exception(f"ComfyUI error: {error}")
                    except asyncio.TimeoutError:
                        continue
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        
        if prompt_id in self.active_jobs:
            self.active_jobs[prompt_id].status = "completed"
            self.active_jobs[prompt_id].outputs = outputs
        
        return {"outputs": outputs, "prompt_id": prompt_id}
    
    async def generate_image_nano_banana(
        self, prompt: str, negative_prompt: str = "",
        width: int = 1920, height: int = 1080,
        reference_images: List[str] = None, progress_callback=None
    ) -> Dict[str, Any]:
        uploaded_refs = []
        if reference_images:
            for ref_path in reference_images:
                uploaded = await self.upload_image(ref_path)
                uploaded_refs.append(uploaded)
        
        if uploaded_refs:
            workflow = ComfyUIWorkflowBuilder.nano_banana_multi_reference(
                prompt=prompt, reference_images=uploaded_refs,
                negative_prompt=negative_prompt, width=width, height=height
            )
        else:
            workflow = ComfyUIWorkflowBuilder.nano_banana_text_to_image(
                prompt=prompt, negative_prompt=negative_prompt, width=width, height=height
            )
        
        prompt_id = await self.queue_workflow(workflow)
        return await self.wait_for_completion(prompt_id, progress_callback=progress_callback)
    
    async def generate_video_ltx(
        self, image_path: str, prompt: str,
        duration_seconds: float = 4.0, fps: int = 24,
        keyframe_images: List[str] = None, progress_callback=None
    ) -> Dict[str, Any]:
        uploaded_image = await self.upload_image(image_path)
        uploaded_keyframes = None
        if keyframe_images:
            uploaded_keyframes = [await self.upload_image(kf) for kf in keyframe_images]
        
        num_frames = int(duration_seconds * fps) + 1
        workflow = ComfyUIWorkflowBuilder.ltx_video_from_image(
            image_path=uploaded_image, prompt=prompt, num_frames=num_frames,
            fps=fps, use_keyframes=bool(uploaded_keyframes), keyframe_images=uploaded_keyframes
        )
        
        prompt_id = await self.queue_workflow(workflow)
        return await self.wait_for_completion(prompt_id, timeout=600.0, progress_callback=progress_callback)


_comfyui_service: Optional[ComfyUIService] = None

def get_comfyui_service() -> ComfyUIService:
    global _comfyui_service
    if _comfyui_service is None:
        _comfyui_service = ComfyUIService()
    return _comfyui_service
