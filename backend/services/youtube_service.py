"""
Nano Banana Studio Pro - YouTube Publishing Service
=====================================================
Professional one-click YouTube upload with multi-account support.

Features:
- OAuth 2.0 authentication with multiple accounts
- Account dropdown selection
- Professional video metadata (title, description, tags, thumbnails)
- Scheduled publishing
- Playlist management
- Analytics integration
- Shorts support
- Chapter markers from timeline
- Auto-generated descriptions with AI
- SEO optimization

Dependencies:
    pip install google-auth google-auth-oauthlib google-api-python-client httpx
"""

import os
import json
import asyncio
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import httpx

logger = logging.getLogger("youtube-service")

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google API not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")


# =============================================================================
# CONFIGURATION
# =============================================================================

class YouTubeConfig:
    """YouTube service configuration"""
    # OAuth credentials path
    CLIENT_SECRETS_FILE = Path(os.getenv("YOUTUBE_CLIENT_SECRETS", "config/youtube_client_secrets.json"))
    TOKENS_DIR = Path(os.getenv("YOUTUBE_TOKENS_DIR", "config/youtube_tokens"))
    
    # API settings
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtubepartner"
    ]
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"
    
    # Upload settings
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS = 500
    MAX_TAG_LENGTH = 30
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # Chunk size for resumable uploads (10MB)
    CHUNK_SIZE = 10 * 1024 * 1024


# =============================================================================
# ENUMS & DATA MODELS
# =============================================================================

class PrivacyStatus(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class VideoCategory(str, Enum):
    """YouTube video categories"""
    FILM_ANIMATION = "1"
    AUTOS_VEHICLES = "2"
    MUSIC = "10"
    PETS_ANIMALS = "15"
    SPORTS = "17"
    SHORT_MOVIES = "18"
    TRAVEL_EVENTS = "19"
    GAMING = "20"
    VIDEOBLOGGING = "21"
    PEOPLE_BLOGS = "22"
    COMEDY = "23"
    ENTERTAINMENT = "24"
    NEWS_POLITICS = "25"
    HOWTO_STYLE = "26"
    EDUCATION = "27"
    SCIENCE_TECH = "28"
    NONPROFITS = "29"
    MOVIES = "30"
    ANIME = "31"
    ACTION_ADVENTURE = "32"
    CLASSICS = "33"
    DOCUMENTARY = "35"
    DRAMA = "36"
    FAMILY = "37"
    FOREIGN = "38"
    HORROR = "39"
    SCIFI_FANTASY = "40"
    THRILLER = "41"
    SHORTS = "42"
    SHOWS = "43"
    TRAILERS = "44"


class UploadStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class YouTubeAccount:
    """Stored YouTube account credentials"""
    id: str
    email: str
    channel_name: str
    channel_id: str
    token_file: str
    added_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    profile_picture: Optional[str] = None
    subscriber_count: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "email": self.email,
            "channel_name": self.channel_name,
            "channel_id": self.channel_id,
            "token_file": self.token_file,
            "added_at": self.added_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "profile_picture": self.profile_picture,
            "subscriber_count": self.subscriber_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "YouTubeAccount":
        return cls(
            id=data["id"],
            email=data["email"],
            channel_name=data["channel_name"],
            channel_id=data["channel_id"],
            token_file=data["token_file"],
            added_at=datetime.fromisoformat(data["added_at"]),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            profile_picture=data.get("profile_picture"),
            subscriber_count=data.get("subscriber_count")
        )


@dataclass
class VideoMetadata:
    """YouTube video metadata"""
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    category: VideoCategory = VideoCategory.ENTERTAINMENT
    privacy: PrivacyStatus = PrivacyStatus.PRIVATE
    
    # Schedule
    scheduled_publish: Optional[datetime] = None
    
    # Additional metadata
    playlist_id: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    # YouTube Shorts
    is_short: bool = False
    
    # Chapter markers (timestamp, title)
    chapters: List[Tuple[float, str]] = field(default_factory=list)
    
    # SEO
    default_language: str = "en"
    
    # Made for kids
    made_for_kids: bool = False
    
    # License
    license: str = "youtube"  # or "creativeCommon"
    
    def get_formatted_description(self) -> str:
        """Generate description with chapters"""
        desc = self.description
        
        if self.chapters:
            desc += "\n\n📑 Chapters:\n"
            for timestamp, title in self.chapters:
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                desc += f"{minutes}:{seconds:02d} - {title}\n"
        
        return desc[:YouTubeConfig.MAX_DESCRIPTION_LENGTH]
    
    def to_youtube_body(self) -> Dict:
        """Convert to YouTube API request body"""
        body = {
            "snippet": {
                "title": self.title[:YouTubeConfig.MAX_TITLE_LENGTH],
                "description": self.get_formatted_description(),
                "tags": self.tags[:YouTubeConfig.MAX_TAGS],
                "categoryId": self.category.value,
                "defaultLanguage": self.default_language
            },
            "status": {
                "privacyStatus": self.privacy.value,
                "selfDeclaredMadeForKids": self.made_for_kids,
                "license": self.license
            }
        }
        
        if self.scheduled_publish and self.privacy == PrivacyStatus.PRIVATE:
            body["status"]["publishAt"] = self.scheduled_publish.isoformat() + "Z"
        
        return body


@dataclass
class UploadResult:
    """Result of video upload"""
    success: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    status: UploadStatus = UploadStatus.PENDING
    error: Optional[str] = None
    
    # Upload details
    upload_time: Optional[float] = None  # seconds
    file_size: Optional[int] = None
    
    # Processing status
    processing_status: Optional[str] = None
    thumbnail_uploaded: bool = False
    added_to_playlist: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "video_id": self.video_id,
            "video_url": self.video_url,
            "status": self.status.value,
            "error": self.error,
            "upload_time": self.upload_time,
            "file_size": self.file_size,
            "processing_status": self.processing_status,
            "thumbnail_uploaded": self.thumbnail_uploaded,
            "added_to_playlist": self.added_to_playlist
        }


# =============================================================================
# YOUTUBE SERVICE
# =============================================================================

class YouTubeService:
    """
    Professional YouTube Publishing Service
    
    Features:
    - Multi-account management with dropdown selection
    - One-click upload with professional metadata
    - OAuth 2.0 authentication
    - Scheduled publishing
    - Thumbnail upload
    - Playlist management
    - SEO-optimized descriptions with AI
    """
    
    def __init__(self):
        YouTubeConfig.TOKENS_DIR.mkdir(parents=True, exist_ok=True)
        self.accounts: Dict[str, YouTubeAccount] = {}
        self.accounts_file = YouTubeConfig.TOKENS_DIR / "accounts.json"
        self._load_accounts()
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    def _load_accounts(self):
        """Load saved accounts from disk"""
        if self.accounts_file.exists():
            try:
                data = json.loads(self.accounts_file.read_text())
                for acc_data in data.get("accounts", []):
                    account = YouTubeAccount.from_dict(acc_data)
                    self.accounts[account.id] = account
                logger.info(f"Loaded {len(self.accounts)} YouTube accounts")
            except Exception as e:
                logger.error(f"Failed to load accounts: {e}")
    
    def _save_accounts(self):
        """Save accounts to disk"""
        data = {
            "accounts": [acc.to_dict() for acc in self.accounts.values()]
        }
        self.accounts_file.write_text(json.dumps(data, indent=2))
    
    def _get_credentials(self, account_id: str) -> Optional[Credentials]:
        """Get or refresh OAuth credentials for an account"""
        if not GOOGLE_API_AVAILABLE:
            raise RuntimeError("Google API libraries not installed")
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account not found: {account_id}")
        
        token_path = YouTubeConfig.TOKENS_DIR / account.token_file
        
        if not token_path.exists():
            raise ValueError(f"Token file not found for account: {account_id}")
        
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
        
        return creds
    
    def _build_youtube_client(self, account_id: str):
        """Build authenticated YouTube API client"""
        creds = self._get_credentials(account_id)
        return build(
            YouTubeConfig.API_SERVICE_NAME,
            YouTubeConfig.API_VERSION,
            credentials=creds
        )
    
    # =========================================================================
    # ACCOUNT MANAGEMENT
    # =========================================================================
    
    def get_accounts_dropdown(self) -> List[Dict]:
        """
        Get list of accounts for dropdown selection.
        Returns list with id, name, email for UI dropdown.
        """
        return [
            {
                "id": acc.id,
                "label": f"{acc.channel_name} ({acc.email})",
                "channel_name": acc.channel_name,
                "email": acc.email,
                "channel_id": acc.channel_id,
                "profile_picture": acc.profile_picture,
                "subscriber_count": acc.subscriber_count
            }
            for acc in self.accounts.values()
        ]
    
    async def add_account(self, auth_code: Optional[str] = None) -> YouTubeAccount:
        """
        Add a new YouTube account via OAuth.
        
        For web flow, pass the auth_code from redirect.
        For local flow, this will open browser for authentication.
        """
        if not GOOGLE_API_AVAILABLE:
            raise RuntimeError("Google API libraries not installed")
        
        if not YouTubeConfig.CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"YouTube client secrets not found at {YouTubeConfig.CLIENT_SECRETS_FILE}. "
                "Download from Google Cloud Console."
            )
        
        # OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(YouTubeConfig.CLIENT_SECRETS_FILE),
            scopes=YouTubeConfig.SCOPES
        )
        
        if auth_code:
            # Web flow with auth code
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
        else:
            # Local flow - opens browser
            creds = flow.run_local_server(port=8090)
        
        # Build client and get channel info
        youtube = build(
            YouTubeConfig.API_SERVICE_NAME,
            YouTubeConfig.API_VERSION,
            credentials=creds
        )
        
        # Get channel info
        response = youtube.channels().list(
            part="snippet,statistics",
            mine=True
        ).execute()
        
        if not response.get("items"):
            raise ValueError("No YouTube channel found for this account")
        
        channel = response["items"][0]
        channel_id = channel["id"]
        snippet = channel["snippet"]
        statistics = channel.get("statistics", {})
        
        # Generate account ID
        account_id = hashlib.md5(channel_id.encode()).hexdigest()[:12]
        
        # Save token
        token_file = f"token_{account_id}.pickle"
        token_path = YouTubeConfig.TOKENS_DIR / token_file
        
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)
        
        # Create account
        account = YouTubeAccount(
            id=account_id,
            email=snippet.get("customUrl", "").replace("@", "") + "@youtube.com",
            channel_name=snippet.get("title", "Unknown"),
            channel_id=channel_id,
            token_file=token_file,
            profile_picture=snippet.get("thumbnails", {}).get("default", {}).get("url"),
            subscriber_count=int(statistics.get("subscriberCount", 0))
        )
        
        self.accounts[account_id] = account
        self._save_accounts()
        
        logger.info(f"Added YouTube account: {account.channel_name}")
        
        return account
    
    def remove_account(self, account_id: str) -> bool:
        """Remove a YouTube account"""
        if account_id not in self.accounts:
            return False
        
        account = self.accounts[account_id]
        
        # Delete token file
        token_path = YouTubeConfig.TOKENS_DIR / account.token_file
        if token_path.exists():
            token_path.unlink()
        
        del self.accounts[account_id]
        self._save_accounts()
        
        logger.info(f"Removed YouTube account: {account.channel_name}")
        return True
    
    async def refresh_account_info(self, account_id: str) -> YouTubeAccount:
        """Refresh account information from YouTube"""
        youtube = self._build_youtube_client(account_id)
        
        response = youtube.channels().list(
            part="snippet,statistics",
            mine=True
        ).execute()
        
        if response.get("items"):
            channel = response["items"][0]
            account = self.accounts[account_id]
            account.subscriber_count = int(channel.get("statistics", {}).get("subscriberCount", 0))
            account.profile_picture = channel.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url")
            self._save_accounts()
        
        return self.accounts[account_id]
    
    # =========================================================================
    # ONE-CLICK UPLOAD
    # =========================================================================
    
    async def upload_video(
        self,
        video_path: str,
        metadata: VideoMetadata,
        account_id: str,
        progress_callback: Optional[callable] = None
    ) -> UploadResult:
        """
        One-click upload video to YouTube.
        
        Args:
            video_path: Path to video file
            metadata: Video metadata (title, description, tags, etc.)
            account_id: YouTube account ID from dropdown
            progress_callback: Optional callback(percent, status) for progress updates
            
        Returns:
            UploadResult with video URL and status
        """
        if not GOOGLE_API_AVAILABLE:
            return UploadResult(
                success=False,
                status=UploadStatus.FAILED,
                error="Google API libraries not installed"
            )
        
        video_file = Path(video_path)
        if not video_file.exists():
            return UploadResult(
                success=False,
                status=UploadStatus.FAILED,
                error=f"Video file not found: {video_path}"
            )
        
        start_time = datetime.utcnow()
        
        try:
            # Build client
            youtube = self._build_youtube_client(account_id)
            
            # Update account last used
            self.accounts[account_id].last_used = datetime.utcnow()
            self._save_accounts()
            
            if progress_callback:
                progress_callback(5, "Preparing upload...")
            
            # Create upload body
            body = metadata.to_youtube_body()
            
            # Create media upload
            media = MediaFileUpload(
                str(video_file),
                chunksize=YouTubeConfig.CHUNK_SIZE,
                resumable=True,
                mimetype="video/*"
            )
            
            # Insert video
            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )
            
            if progress_callback:
                progress_callback(10, "Uploading video...")
            
            # Execute upload with progress tracking
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    percent = int(status.progress() * 80) + 10  # 10-90%
                    if progress_callback:
                        progress_callback(percent, f"Uploading: {int(status.progress() * 100)}%")
            
            video_id = response["id"]
            
            if progress_callback:
                progress_callback(90, "Processing...")
            
            # Upload thumbnail if provided
            thumbnail_uploaded = False
            if metadata.thumbnail_path and Path(metadata.thumbnail_path).exists():
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(metadata.thumbnail_path)
                    ).execute()
                    thumbnail_uploaded = True
                except Exception as e:
                    logger.warning(f"Failed to upload thumbnail: {e}")
            
            # Add to playlist if specified
            added_to_playlist = False
            if metadata.playlist_id:
                try:
                    youtube.playlistItems().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "playlistId": metadata.playlist_id,
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": video_id
                                }
                            }
                        }
                    ).execute()
                    added_to_playlist = True
                except Exception as e:
                    logger.warning(f"Failed to add to playlist: {e}")
            
            if progress_callback:
                progress_callback(100, "Complete!")
            
            upload_time = (datetime.utcnow() - start_time).total_seconds()
            
            return UploadResult(
                success=True,
                video_id=video_id,
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                status=UploadStatus.COMPLETED,
                upload_time=upload_time,
                file_size=video_file.stat().st_size,
                processing_status=response.get("status", {}).get("uploadStatus"),
                thumbnail_uploaded=thumbnail_uploaded,
                added_to_playlist=added_to_playlist
            )
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return UploadResult(
                success=False,
                status=UploadStatus.FAILED,
                error=str(e)
            )
    
    async def quick_upload(
        self,
        video_path: str,
        title: str,
        account_id: str,
        description: str = "",
        tags: List[str] = None,
        privacy: PrivacyStatus = PrivacyStatus.PRIVATE,
        category: VideoCategory = VideoCategory.ENTERTAINMENT
    ) -> UploadResult:
        """
        Quick one-click upload with minimal parameters.
        
        This is the simplest upload method for fast publishing.
        """
        metadata = VideoMetadata(
            title=title,
            description=description,
            tags=tags or [],
            category=category,
            privacy=privacy
        )
        
        return await self.upload_video(video_path, metadata, account_id)
    
    # =========================================================================
    # PLAYLIST MANAGEMENT
    # =========================================================================
    
    async def get_playlists(self, account_id: str) -> List[Dict]:
        """Get all playlists for account"""
        youtube = self._build_youtube_client(account_id)
        
        playlists = []
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=50
        )
        
        while request:
            response = request.execute()
            for item in response.get("items", []):
                playlists.append({
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "video_count": item["contentDetails"]["itemCount"],
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
                })
            request = youtube.playlists().list_next(request, response)
        
        return playlists
    
    async def create_playlist(
        self,
        account_id: str,
        title: str,
        description: str = "",
        privacy: PrivacyStatus = PrivacyStatus.PRIVATE
    ) -> Dict:
        """Create a new playlist"""
        youtube = self._build_youtube_client(account_id)
        
        response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": privacy.value
                }
            }
        ).execute()
        
        return {
            "id": response["id"],
            "title": response["snippet"]["title"],
            "url": f"https://www.youtube.com/playlist?list={response['id']}"
        }
    
    # =========================================================================
    # AI-ENHANCED METADATA
    # =========================================================================
    
    async def generate_seo_metadata(
        self,
        video_title: str,
        video_description: str,
        video_category: str = "entertainment"
    ) -> VideoMetadata:
        """
        Generate SEO-optimized metadata using AI.
        
        Enhances title, generates tags, and optimizes description.
        """
        # LLM integration for metadata enhancement
        system_prompt = """You are a YouTube SEO expert. Generate optimized metadata for a video.

Return JSON with:
{
    "title": "SEO-optimized title (max 100 chars)",
    "description": "Engaging description with keywords",
    "tags": ["tag1", "tag2", ...],  // 10-20 relevant tags
    "hashtags": ["#hashtag1", "#hashtag2", ...]  // 3-5 hashtags
}"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:1234/v1/chat/completions",
                    json={
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Title: {video_title}\nDescription: {video_description}\nCategory: {video_category}"}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        data = json.loads(json_match.group())
                        
                        full_desc = data.get("description", video_description)
                        if data.get("hashtags"):
                            full_desc += "\n\n" + " ".join(data["hashtags"])
                        
                        return VideoMetadata(
                            title=data.get("title", video_title),
                            description=full_desc,
                            tags=data.get("tags", [])
                        )
        except Exception as e:
            logger.warning(f"AI metadata generation failed: {e}")
        
        # Fallback to basic metadata
        return VideoMetadata(
            title=video_title,
            description=video_description,
            tags=[]
        )
    
    # =========================================================================
    # ANALYTICS
    # =========================================================================
    
    async def get_video_analytics(self, account_id: str, video_id: str) -> Dict:
        """Get analytics for a specific video"""
        youtube = self._build_youtube_client(account_id)
        
        response = youtube.videos().list(
            part="statistics,status",
            id=video_id
        ).execute()
        
        if not response.get("items"):
            return {"error": "Video not found"}
        
        video = response["items"][0]
        stats = video.get("statistics", {})
        status = video.get("status", {})
        
        return {
            "video_id": video_id,
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "privacy_status": status.get("privacyStatus"),
            "upload_status": status.get("uploadStatus"),
            "made_for_kids": status.get("madeForKids", False)
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# =============================================================================
# SINGLETON
# =============================================================================

_youtube_service: Optional[YouTubeService] = None

def get_youtube_service() -> YouTubeService:
    """Get or create YouTube service instance"""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service
