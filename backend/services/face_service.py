"""
Nano Banana Studio Pro - Face Detection & Character Consistency Service
========================================================================
Complete face detection, embedding, and character consistency system.

Features:
- MediaPipe face detection (468 landmarks, CPU-friendly)
- InsightFace face embedding (512-dim, GPU accelerated)
- Character registration with multiple reference images
- Face similarity scoring and verification
- Auto-rejection of inconsistent frames

Dependencies:
    pip install mediapipe insightface opencv-python numpy onnxruntime-gpu
"""

import os
import json
import hashlib
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import numpy as np
import cv2

logger = logging.getLogger("face-service")

# Configuration
FACE_DB_PATH = Path(os.getenv("FACE_DB_PATH", "/app/data/face_db.sqlite"))
FACE_CACHE_DIR = Path(os.getenv("FACE_CACHE_DIR", "/app/data/cache/faces"))
SIMILARITY_THRESHOLD = float(os.getenv("FACE_SIMILARITY_THRESHOLD", "0.85"))


@dataclass
class FaceDetection:
    """Detected face with bounding box and landmarks"""
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    landmarks: Optional[List[Tuple[float, float]]] = None
    embedding: Optional[np.ndarray] = None
    image_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "bbox": list(self.bbox),
            "confidence": self.confidence,
            "landmarks": self.landmarks,
            "embedding": self.embedding.tolist() if self.embedding is not None else None
        }


@dataclass
class Character:
    """Registered character with identity information"""
    id: str
    name: str
    embedding: np.ndarray  # 512-dim average embedding
    reference_images: List[str] = field(default_factory=list)
    reference_embeddings: List[np.ndarray] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)
    
    @property
    def num_references(self) -> int:
        return len(self.reference_images)


class MediaPipeFaceDetector:
    """
    MediaPipe-based face detection.
    Fast, CPU-friendly, provides 468 facial landmarks.
    """
    
    def __init__(self, min_detection_confidence: float = 0.5, model_selection: int = 1):
        """
        Initialize MediaPipe face detector.
        
        Args:
            min_detection_confidence: Minimum confidence threshold
            model_selection: 0 for short-range (within 2m), 1 for full-range (within 5m)
        """
        import mediapipe as mp
        
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        
        self.detector = self.mp_face_detection.FaceDetection(
            min_detection_confidence=min_detection_confidence,
            model_selection=model_selection
        )
        
        self.mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence
        )
        
        logger.info("MediaPipe face detector initialized")
    
    def detect(self, image: np.ndarray) -> List[FaceDetection]:
        """
        Detect faces in an image.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            List of FaceDetection objects
        """
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w = image.shape[:2]
        
        # Detect faces
        results = self.detector.process(rgb_image)
        
        detections = []
        if results.detections:
            for detection in results.detections:
                # Get bounding box
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Clamp to image bounds
                x = max(0, x)
                y = max(0, y)
                width = min(width, w - x)
                height = min(height, h - y)
                
                confidence = detection.score[0]
                
                detections.append(FaceDetection(
                    bbox=(x, y, width, height),
                    confidence=confidence
                ))
        
        return detections
    
    def detect_with_landmarks(self, image: np.ndarray) -> List[FaceDetection]:
        """
        Detect faces with full 468 landmark mesh.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            List of FaceDetection objects with landmarks
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w = image.shape[:2]
        
        results = self.mesh.process(rgb_image)
        
        detections = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Extract landmarks as (x, y) tuples
                landmarks = []
                xs, ys = [], []
                
                for landmark in face_landmarks.landmark:
                    x = landmark.x * w
                    y = landmark.y * h
                    landmarks.append((x, y))
                    xs.append(x)
                    ys.append(y)
                
                # Calculate bounding box from landmarks
                x_min, x_max = int(min(xs)), int(max(xs))
                y_min, y_max = int(min(ys)), int(max(ys))
                
                # Add padding
                padding = int(max(x_max - x_min, y_max - y_min) * 0.1)
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(w, x_max + padding)
                y_max = min(h, y_max + padding)
                
                detections.append(FaceDetection(
                    bbox=(x_min, y_min, x_max - x_min, y_max - y_min),
                    confidence=0.99,  # Mesh doesn't provide confidence
                    landmarks=landmarks
                ))
        
        return detections
    
    def extract_face(
        self, 
        image: np.ndarray, 
        detection: FaceDetection,
        target_size: Tuple[int, int] = (112, 112),
        expand_ratio: float = 1.3
    ) -> np.ndarray:
        """
        Extract and align face region from image.
        
        Args:
            image: Source image
            detection: Face detection result
            target_size: Output face size
            expand_ratio: How much to expand bounding box
            
        Returns:
            Aligned face image
        """
        x, y, w, h = detection.bbox
        
        # Expand bounding box
        cx, cy = x + w // 2, y + h // 2
        new_size = int(max(w, h) * expand_ratio)
        
        x1 = max(0, cx - new_size // 2)
        y1 = max(0, cy - new_size // 2)
        x2 = min(image.shape[1], cx + new_size // 2)
        y2 = min(image.shape[0], cy + new_size // 2)
        
        face = image[y1:y2, x1:x2]
        face = cv2.resize(face, target_size)
        
        return face
    
    def close(self):
        """Release resources"""
        self.detector.close()
        self.mesh.close()


class InsightFaceEmbedder:
    """
    InsightFace-based face embedding.
    High-accuracy 512-dimensional face embeddings for recognition.
    """
    
    def __init__(self, model_name: str = "buffalo_l", ctx_id: int = 0):
        """
        Initialize InsightFace embedder.
        
        Args:
            model_name: Model pack name (buffalo_l, buffalo_s, etc.)
            ctx_id: GPU context ID (-1 for CPU)
        """
        from insightface.app import FaceAnalysis
        
        self.app = FaceAnalysis(
            name=model_name,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        
        logger.info(f"InsightFace initialized with model: {model_name}")
    
    def get_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Get face embedding from image.
        
        Args:
            image: BGR image with a face
            
        Returns:
            512-dim embedding vector or None if no face found
        """
        faces = self.app.get(image)
        
        if not faces:
            return None
        
        # Return embedding of largest face
        largest = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
        return largest.normed_embedding
    
    def get_all_embeddings(self, image: np.ndarray) -> List[Tuple[FaceDetection, np.ndarray]]:
        """
        Get embeddings for all faces in image.
        
        Args:
            image: BGR image
            
        Returns:
            List of (FaceDetection, embedding) tuples
        """
        faces = self.app.get(image)
        
        results = []
        for face in faces:
            bbox = face.bbox.astype(int)
            detection = FaceDetection(
                bbox=(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]),
                confidence=float(face.det_score),
                embedding=face.normed_embedding
            )
            results.append((detection, face.normed_embedding))
        
        return results
    
    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))


class CharacterStore:
    """
    SQLite-based character storage with embedding management.
    """
    
    def __init__(self, db_path: Path = FACE_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                embedding BLOB NOT NULL,
                reference_images TEXT,
                reference_embeddings BLOB,
                created_at TEXT,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name)
        """)
        
        conn.commit()
        conn.close()
    
    def save_character(self, character: Character) -> bool:
        """Save or update a character"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Serialize embeddings
            embedding_bytes = character.embedding.tobytes()
            ref_embeddings_bytes = np.array(character.reference_embeddings).tobytes() if character.reference_embeddings else b''
            
            cursor.execute("""
                INSERT OR REPLACE INTO characters 
                (id, name, embedding, reference_images, reference_embeddings, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                character.id,
                character.name,
                embedding_bytes,
                json.dumps(character.reference_images),
                ref_embeddings_bytes,
                character.created_at.isoformat(),
                json.dumps(character.metadata)
            ))
            
            conn.commit()
            logger.info(f"Saved character: {character.name} ({character.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save character: {e}")
            return False
            
        finally:
            conn.close()
    
    def load_character(self, character_id: str) -> Optional[Character]:
        """Load a character by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Deserialize embeddings
            embedding = np.frombuffer(row[2], dtype=np.float32)
            ref_embeddings = []
            if row[4]:
                ref_emb_array = np.frombuffer(row[4], dtype=np.float32)
                if len(ref_emb_array) > 0:
                    ref_embeddings = list(ref_emb_array.reshape(-1, 512))
            
            return Character(
                id=row[0],
                name=row[1],
                embedding=embedding,
                reference_images=json.loads(row[3]) if row[3] else [],
                reference_embeddings=ref_embeddings,
                created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.utcnow(),
                metadata=json.loads(row[6]) if row[6] else {}
            )
            
        except Exception as e:
            logger.error(f"Failed to load character: {e}")
            return None
            
        finally:
            conn.close()
    
    def list_characters(self) -> List[Dict]:
        """List all characters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, name, created_at, reference_images FROM characters")
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "num_references": len(json.loads(row[3])) if row[3] else 0
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    def delete_character(self, character_id: str) -> bool:
        """Delete a character"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()


class FaceService:
    """
    High-level face service combining detection, embedding, and character management.
    """
    
    def __init__(
        self,
        use_gpu: bool = True,
        similarity_threshold: float = SIMILARITY_THRESHOLD
    ):
        """
        Initialize face service.
        
        Args:
            use_gpu: Whether to use GPU for InsightFace
            similarity_threshold: Minimum similarity for face matching
        """
        self.detector = MediaPipeFaceDetector()
        self.embedder = InsightFaceEmbedder(ctx_id=0 if use_gpu else -1)
        self.store = CharacterStore()
        self.similarity_threshold = similarity_threshold
        
        # Cache directory for face crops
        FACE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info("FaceService initialized")
    
    def detect_faces(
        self, 
        image: Union[str, np.ndarray],
        with_landmarks: bool = False,
        with_embeddings: bool = False
    ) -> List[FaceDetection]:
        """
        Detect faces in an image.
        
        Args:
            image: Image path or numpy array
            with_landmarks: Include 468 facial landmarks
            with_embeddings: Include 512-dim embeddings
            
        Returns:
            List of FaceDetection objects
        """
        # Load image if path
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                raise ValueError(f"Could not load image: {image}")
        
        # Detect faces
        if with_landmarks:
            detections = self.detector.detect_with_landmarks(image)
        else:
            detections = self.detector.detect(image)
        
        # Add embeddings if requested
        if with_embeddings and detections:
            emb_results = self.embedder.get_all_embeddings(image)
            
            # Match detections with embeddings by IoU
            for det in detections:
                best_match = None
                best_iou = 0
                
                for emb_det, emb in emb_results:
                    iou = self._calculate_iou(det.bbox, emb_det.bbox)
                    if iou > best_iou:
                        best_iou = iou
                        best_match = emb
                
                if best_match is not None and best_iou > 0.5:
                    det.embedding = best_match
        
        return detections
    
    def _calculate_iou(self, box1: Tuple, box2: Tuple) -> float:
        """Calculate intersection over union of two boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        union = w1 * h1 + w2 * h2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def register_character(
        self,
        name: str,
        reference_images: List[str],
        character_id: Optional[str] = None
    ) -> Optional[Character]:
        """
        Register a new character from reference images.
        
        Args:
            name: Character name
            reference_images: List of image paths
            character_id: Optional custom ID
            
        Returns:
            Registered Character object or None on failure
        """
        if not reference_images:
            raise ValueError("At least one reference image required")
        
        embeddings = []
        valid_images = []
        
        for img_path in reference_images:
            image = cv2.imread(img_path)
            if image is None:
                logger.warning(f"Could not load image: {img_path}")
                continue
            
            embedding = self.embedder.get_embedding(image)
            if embedding is not None:
                embeddings.append(embedding)
                valid_images.append(img_path)
            else:
                logger.warning(f"No face found in: {img_path}")
        
        if not embeddings:
            raise ValueError("No faces found in any reference images")
        
        # Calculate average embedding
        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)  # Normalize
        
        # Generate ID
        if character_id is None:
            character_id = hashlib.sha256(f"{name}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        character = Character(
            id=character_id,
            name=name,
            embedding=avg_embedding,
            reference_images=valid_images,
            reference_embeddings=embeddings
        )
        
        # Save to database
        self.store.save_character(character)
        
        logger.info(f"Registered character '{name}' with {len(embeddings)} reference(s)")
        return character
    
    def verify_character(
        self,
        image: Union[str, np.ndarray],
        character_id: str
    ) -> Dict[str, Any]:
        """
        Verify if an image contains the specified character.
        
        Args:
            image: Image path or numpy array
            character_id: ID of character to verify
            
        Returns:
            Verification result with similarity score
        """
        # Load character
        character = self.store.load_character(character_id)
        if character is None:
            return {
                "verified": False,
                "error": "Character not found",
                "character_id": character_id
            }
        
        # Load image
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                return {
                    "verified": False,
                    "error": "Could not load image"
                }
        
        # Get embedding from image
        embedding = self.embedder.get_embedding(image)
        if embedding is None:
            return {
                "verified": False,
                "error": "No face found in image",
                "character_id": character_id,
                "character_name": character.name
            }
        
        # Calculate similarity
        similarity = InsightFaceEmbedder.cosine_similarity(embedding, character.embedding)
        verified = similarity >= self.similarity_threshold
        
        return {
            "verified": verified,
            "similarity": float(similarity),
            "threshold": self.similarity_threshold,
            "character_id": character_id,
            "character_name": character.name
        }
    
    def find_matching_character(
        self,
        image: Union[str, np.ndarray],
        min_similarity: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching character for a face in an image.
        
        Args:
            image: Image path or numpy array
            min_similarity: Minimum similarity threshold
            
        Returns:
            Best match result or None
        """
        if min_similarity is None:
            min_similarity = self.similarity_threshold
        
        # Load image
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                return None
        
        # Get embedding
        embedding = self.embedder.get_embedding(image)
        if embedding is None:
            return None
        
        # Search all characters
        characters = self.store.list_characters()
        best_match = None
        best_similarity = 0
        
        for char_info in characters:
            character = self.store.load_character(char_info["id"])
            if character is None:
                continue
            
            similarity = InsightFaceEmbedder.cosine_similarity(embedding, character.embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = character
        
        if best_match and best_similarity >= min_similarity:
            return {
                "character_id": best_match.id,
                "character_name": best_match.name,
                "similarity": float(best_similarity),
                "verified": True
            }
        
        return None
    
    def extract_face_region(
        self,
        image: Union[str, np.ndarray],
        output_path: Optional[str] = None,
        size: Tuple[int, int] = (512, 512)
    ) -> Optional[np.ndarray]:
        """
        Extract the primary face region from an image.
        
        Args:
            image: Image path or numpy array
            output_path: Optional path to save extracted face
            size: Output size
            
        Returns:
            Extracted face image or None
        """
        # Load image
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                return None
        
        # Detect faces
        detections = self.detect_faces(image)
        if not detections:
            return None
        
        # Get largest face
        largest = max(detections, key=lambda d: d.bbox[2] * d.bbox[3])
        
        # Extract face
        face = self.detector.extract_face(image, largest, target_size=size)
        
        # Save if requested
        if output_path:
            cv2.imwrite(output_path, face)
        
        return face
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """Get character by ID"""
        return self.store.load_character(character_id)
    
    def list_characters(self) -> List[Dict]:
        """List all registered characters"""
        return self.store.list_characters()
    
    def delete_character(self, character_id: str) -> bool:
        """Delete a character"""
        return self.store.delete_character(character_id)
    
    def close(self):
        """Release resources"""
        self.detector.close()


# Singleton instance
_face_service: Optional[FaceService] = None

def get_face_service() -> FaceService:
    """Get or create face service instance"""
    global _face_service
    if _face_service is None:
        _face_service = FaceService()
    return _face_service
