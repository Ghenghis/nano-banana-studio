# 🍌 Nano Banana Studio Pro - n8n Workflows Guide

## Overview

Nano Banana Studio Pro includes 14 pre-built n8n workflows for automated AI video production.

## Accessing Workflows

1. Start n8n: `docker compose up -d n8n`
2. Open: http://localhost:5678
3. Login: `admin` / `nanobanana` (default)
4. Import workflows from `n8n/workflows/`

## Workflow Catalog

### Entry Point Workflows

#### 01 - Prompt Enhancer Master
**Trigger:** Webhook  
**Purpose:** 7-stage prompt enhancement pipeline

```
Input → Concept → Scene → Visual → Cinematic → Narrative → Technical → Consistency → Output
```

**Webhook URL:** `POST /webhook/enhance-prompt`

**Input:**
```json
{
  "prompt": "woman singing in a studio",
  "style": "Cinematic",
  "platform": "YouTube (16:9)"
}
```

---

#### 08 - Suno Music Generator
**Trigger:** Webhook  
**Purpose:** Generate AI music with Suno

**Webhook URL:** `POST /webhook/suno-generate`

**Input:**
```json
{
  "prompt": "upbeat pop song about summer",
  "genre": "pop",
  "duration": 60,
  "instrumental": false
}
```

---

#### 99 - Full Music Video Pipeline
**Trigger:** Webhook  
**Purpose:** Complete end-to-end music video generation

**Webhook URL:** `POST /webhook/full-pipeline`

**Input:**
```json
{
  "prompt": "Epic music video concept",
  "style": "Cinematic",
  "duration": 60,
  "generate_music": true
}
```

### Processing Workflows

#### 02 - Image Generation
Multi-model image creation (Gemini, FLUX, SDXL)

#### 03 - Multi-Asset Processor
Batch file upload and processing

#### 04 - Video Assembly Pro
Professional FFmpeg video rendering with transitions

#### 05 - Video Extender
Extend video duration with AI interpolation

#### 06 - Master Pipeline
Job orchestration and workflow coordination

#### 07 - Face Character System
Face extraction and character embedding

### Analysis Workflows

#### 09 - Audio Beat Analyzer
Beat detection, BPM analysis, section identification

#### 11 - PDF/Markdown Parser
Document parsing for video instructions

### Specialized Workflows

#### 10 - Image-to-Video Animation
Multi-provider animation (Runway, Kling, SVD)

#### 12 - ComfyUI Integration
Bridge to ComfyUI for advanced generation

#### 13 - Suno Pipeline v2
Enhanced Suno integration with 5 endpoints

## Creating Custom Workflows

### Best Practices

1. **Use Error Handling:** Add "Error Trigger" nodes
2. **Add Logging:** Use "Set" nodes for debugging
3. **Modular Design:** Create sub-workflows for reusable logic
4. **Webhook Security:** Use authentication in production

### Example: Custom Image Pipeline

```
Webhook Trigger
    ↓
HTTP Request (Enhance Prompt)
    ↓
HTTP Request (Generate Image)
    ↓
HTTP Request (Check Job Status)
    ↓
Wait (Poll for completion)
    ↓
Return Result
```

## Webhook Security

For production, enable webhook authentication:

```env
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=your-username
N8N_BASIC_AUTH_PASSWORD=your-secure-password
```

## Troubleshooting

### Workflow Not Triggering
- Check workflow is activated (toggle on)
- Verify webhook URL is correct
- Check n8n logs: `docker compose logs -f n8n`

### API Timeouts
- Increase timeout in HTTP Request nodes
- Use webhook + polling pattern for long operations

### Data Not Passing
- Check JSON parsing in nodes
- Use "Set" nodes to debug data flow
