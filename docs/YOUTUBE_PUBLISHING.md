# 🍌 Nano Banana Studio Pro - YouTube Publishing Guide

## Overview

One-click professional YouTube publishing with multi-account support, SEO optimization, and automated metadata generation.

## Features

- ✅ **Multi-Account Support** - Connect unlimited YouTube accounts
- ✅ **Dropdown Selection** - Easy account picker for uploads
- ✅ **One-Click Upload** - Simple or detailed upload options
- ✅ **Professional Metadata** - Title, description, tags, chapters
- ✅ **Scheduled Publishing** - Set future publish dates
- ✅ **Playlist Management** - Create and add to playlists
- ✅ **Thumbnail Upload** - Custom thumbnails
- ✅ **AI SEO Optimization** - AI-generated metadata
- ✅ **YouTube Shorts** - Shorts format support
- ✅ **Analytics** - View video performance

## Quick Start

### 1. Setup Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials (Desktop app type)
5. Download `client_secrets.json`
6. Save to `config/youtube_client_secrets.json`

### 2. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

### 3. Connect Your YouTube Account

```bash
# Via API (opens browser for OAuth)
curl -X POST http://localhost:8000/api/v1/youtube/accounts/add
```

### 4. One-Click Upload

```bash
# Quick upload (minimal params)
curl -X POST http://localhost:8000/api/v1/youtube/quick-upload \
  -F "video_path=/app/data/outputs/my_video.mp4" \
  -F "title=My Amazing Video" \
  -F "account_id=abc123" \
  -F "privacy=public"
```

## API Endpoints

### Account Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/youtube/accounts` | GET | List connected accounts (for dropdown) |
| `/api/v1/youtube/accounts/add` | POST | Add new YouTube account |
| `/api/v1/youtube/accounts/{id}` | DELETE | Remove account |

### Video Upload

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/youtube/upload` | POST | Full upload with all options |
| `/api/v1/youtube/quick-upload` | POST | Simplified one-click upload |

### Playlists

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/youtube/playlists/{account_id}` | GET | List playlists |
| `/api/v1/youtube/playlists/{account_id}` | POST | Create playlist |

### Utilities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/youtube/generate-metadata` | POST | AI-generated SEO metadata |
| `/api/v1/youtube/analytics/{account_id}/{video_id}` | GET | Video analytics |

## Detailed Usage

### Get Accounts for Dropdown

```python
import httpx

async def get_accounts():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/v1/youtube/accounts")
        data = response.json()
        
        # Display in dropdown
        for account in data["accounts"]:
            print(f"{account['id']}: {account['label']}")
```

Response:
```json
{
  "accounts": [
    {
      "id": "abc123def456",
      "label": "My Channel (@mychannel)",
      "channel_name": "My Channel",
      "email": "mychannel@youtube.com",
      "channel_id": "UC...",
      "profile_picture": "https://...",
      "subscriber_count": 10000
    }
  ],
  "count": 1
}
```

### Full Upload with All Options

```python
import httpx

async def upload_video():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/youtube/upload",
            json={
                "video_path": "/app/data/outputs/music_video.mp4",
                "title": "My Epic Music Video | Official 4K",
                "description": "Official music video for...\n\n#music #video",
                "tags": ["music", "video", "4k", "official"],
                "account_id": "abc123def456",
                "privacy": "public",
                "category": "10",  # Music category
                "playlist_id": "PL...",
                "thumbnail_path": "/app/data/outputs/thumbnail.jpg",
                "scheduled_publish": "2025-01-01T12:00:00Z",
                "chapters": [
                    {"time": 0, "title": "Intro"},
                    {"time": 30, "title": "Verse 1"},
                    {"time": 60, "title": "Chorus"},
                    {"time": 90, "title": "Verse 2"},
                    {"time": 120, "title": "Outro"}
                ]
            }
        )
        
        result = response.json()
        print(f"Job ID: {result['job_id']}")
```

### AI-Generated SEO Metadata

```python
async def generate_metadata():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/youtube/generate-metadata",
            data={
                "title": "Cat Playing Piano",
                "description": "My cat learned to play piano",
                "category": "entertainment"
            }
        )
        
        metadata = response.json()
        # Returns optimized title, description, and tags
```

## Video Categories

| ID | Category |
|----|----------|
| 1 | Film & Animation |
| 2 | Autos & Vehicles |
| 10 | Music |
| 15 | Pets & Animals |
| 17 | Sports |
| 20 | Gaming |
| 22 | People & Blogs |
| 23 | Comedy |
| 24 | Entertainment |
| 25 | News & Politics |
| 26 | Howto & Style |
| 27 | Education |
| 28 | Science & Technology |

## Privacy Options

| Value | Description |
|-------|-------------|
| `public` | Visible to everyone |
| `private` | Only you can view |
| `unlisted` | Anyone with link can view |

## Chapter Markers

Chapters are automatically formatted in the description:

```
📑 Chapters:
0:00 - Intro
0:30 - Verse 1
1:00 - Chorus
1:30 - Verse 2
2:00 - Outro
```

## Environment Variables

```env
# Path to OAuth client secrets
YOUTUBE_CLIENT_SECRETS=config/youtube_client_secrets.json

# Directory for account tokens
YOUTUBE_TOKENS_DIR=config/youtube_tokens
```

## Troubleshooting

### "Client secrets not found"
- Download OAuth credentials from Google Cloud Console
- Save to `config/youtube_client_secrets.json`

### "YouTube service not available"
- Install: `pip install google-auth google-auth-oauthlib google-api-python-client`

### "No YouTube channel found"
- Ensure the Google account has an active YouTube channel
- Create a channel at [YouTube Studio](https://studio.youtube.com/)

### Upload fails with quota error
- YouTube API has daily quotas
- Wait 24 hours or request quota increase in Google Cloud Console

## Integration with Video Pipeline

After generating a video with Nano Banana Studio, upload directly:

```python
# Generate video
video_result = await assemble_video(...)

# One-click upload to YouTube
upload_result = await quick_youtube_upload(
    video_path=video_result["video_path"],
    title="My AI Generated Music Video",
    account_id="abc123"  # From dropdown
)

print(f"Video URL: {upload_result['video_url']}")
```

## n8n Workflow Integration

Use in n8n workflows:

```json
{
  "nodes": [
    {
      "name": "Upload to YouTube",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://api:8000/api/v1/youtube/quick-upload",
        "bodyParametersUi": {
          "parameter": [
            {"name": "video_path", "value": "={{ $json.video_path }}"},
            {"name": "title", "value": "={{ $json.title }}"},
            {"name": "account_id", "value": "abc123"}
          ]
        }
      }
    }
  ]
}
```
