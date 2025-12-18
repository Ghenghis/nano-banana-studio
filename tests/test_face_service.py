"""
Nano Banana Studio Pro - Face Service Tests
============================================
Comprehensive test coverage for FaceService.
Tests: MediaPipeFaceDetector, InsightFaceEmbedder, CharacterStore, FaceService
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path


class TestMediaPipeFaceDetector:
    """Tests for MediaPipe face detector"""
    
    def test_init(self):
        """Test detector initialization"""
        with patch('mediapipe.solutions.face_detection.FaceDetection'):
            from backend.services.face_service import MediaPipeFaceDetector
            detector = MediaPipeFaceDetector()
            assert detector is not None
    
    def test_detect_faces_single(self, tmp_path):
        """Test single face detection"""
        from PIL import Image
        import numpy as np
        
        img = Image.new('RGB', (640, 480), color='white')
        img_array = np.array(img)
        
        with patch('mediapipe.solutions.face_detection.FaceDetection') as mock_mp:
            mock_detector = Mock()
            mock_result = Mock()
            mock_detection = Mock()
            mock_detection.location_data.relative_bounding_box.xmin = 0.2
            mock_detection.location_data.relative_bounding_box.ymin = 0.2
            mock_detection.location_data.relative_bounding_box.width = 0.3
            mock_detection.location_data.relative_bounding_box.height = 0.4
            mock_detection.score = [0.95]
            mock_result.detections = [mock_detection]
            mock_detector.process.return_value = mock_result
            mock_mp.return_value.__enter__ = Mock(return_value=mock_detector)
            mock_mp.return_value.__exit__ = Mock(return_value=False)
            
            from backend.services.face_service import MediaPipeFaceDetector
            detector = MediaPipeFaceDetector()
            
            with patch.object(detector, 'detector', mock_detector):
                faces = detector.detect(img_array)
                assert isinstance(faces, list)
    
    def test_detect_faces_no_faces(self):
        """Test detection with no faces"""
        import numpy as np
        
        img_array = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch('mediapipe.solutions.face_detection.FaceDetection') as mock_mp:
            mock_detector = Mock()
            mock_result = Mock()
            mock_result.detections = None
            mock_detector.process.return_value = mock_result
            
            from backend.services.face_service import MediaPipeFaceDetector
            detector = MediaPipeFaceDetector()
            detector.detector = mock_detector
            
            faces = detector.detect(img_array)
            assert faces == []
    
    def test_detect_faces_multiple(self):
        """Test multiple face detection"""
        import numpy as np
        
        img_array = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch('mediapipe.solutions.face_detection.FaceDetection') as mock_mp:
            mock_detector = Mock()
            mock_result = Mock()
            
            mock_detection1 = Mock()
            mock_detection1.location_data.relative_bounding_box.xmin = 0.1
            mock_detection1.location_data.relative_bounding_box.ymin = 0.2
            mock_detection1.location_data.relative_bounding_box.width = 0.2
            mock_detection1.location_data.relative_bounding_box.height = 0.3
            mock_detection1.score = [0.9]
            
            mock_detection2 = Mock()
            mock_detection2.location_data.relative_bounding_box.xmin = 0.5
            mock_detection2.location_data.relative_bounding_box.ymin = 0.2
            mock_detection2.location_data.relative_bounding_box.width = 0.2
            mock_detection2.location_data.relative_bounding_box.height = 0.3
            mock_detection2.score = [0.85]
            
            mock_result.detections = [mock_detection1, mock_detection2]
            mock_detector.process.return_value = mock_result
            
            from backend.services.face_service import MediaPipeFaceDetector
            detector = MediaPipeFaceDetector()
            detector.detector = mock_detector
            
            faces = detector.detect(img_array)
            assert len(faces) == 2


class TestInsightFaceEmbedder:
    """Tests for InsightFace embedding extractor"""
    
    def test_init(self):
        """Test embedder initialization"""
        with patch('insightface.app.FaceAnalysis'):
            from backend.services.face_service import InsightFaceEmbedder
            embedder = InsightFaceEmbedder()
            assert embedder is not None
    
    def test_get_embedding_success(self):
        """Test successful embedding extraction"""
        import numpy as np
        
        img_array = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch('insightface.app.FaceAnalysis') as mock_fa:
            mock_app = Mock()
            mock_face = Mock()
            mock_face.embedding = np.random.rand(512).astype(np.float32)
            mock_app.get.return_value = [mock_face]
            mock_fa.return_value = mock_app
            
            from backend.services.face_service import InsightFaceEmbedder
            embedder = InsightFaceEmbedder()
            embedder.app = mock_app
            
            embedding = embedder.get_embedding(img_array)
            assert embedding is not None
            assert len(embedding) == 512
    
    def test_get_embedding_no_face(self):
        """Test embedding extraction with no face"""
        import numpy as np
        
        img_array = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch('insightface.app.FaceAnalysis') as mock_fa:
            mock_app = Mock()
            mock_app.get.return_value = []
            
            from backend.services.face_service import InsightFaceEmbedder
            embedder = InsightFaceEmbedder()
            embedder.app = mock_app
            
            embedding = embedder.get_embedding(img_array)
            assert embedding is None
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        import numpy as np
        
        from backend.services.face_service import InsightFaceEmbedder
        
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([1.0, 0.0, 0.0])
        similarity = InsightFaceEmbedder.cosine_similarity(emb1, emb2)
        assert abs(similarity - 1.0) < 0.001
        
        emb3 = np.array([0.0, 1.0, 0.0])
        similarity = InsightFaceEmbedder.cosine_similarity(emb1, emb3)
        assert abs(similarity - 0.0) < 0.001
    
    def test_cosine_similarity_normalized(self):
        """Test cosine similarity with normalized vectors"""
        import numpy as np
        
        from backend.services.face_service import InsightFaceEmbedder
        
        emb1 = np.array([0.5, 0.5, 0.5])
        emb1 = emb1 / np.linalg.norm(emb1)
        
        emb2 = np.array([0.5, 0.5, 0.5])
        emb2 = emb2 / np.linalg.norm(emb2)
        
        similarity = InsightFaceEmbedder.cosine_similarity(emb1, emb2)
        assert abs(similarity - 1.0) < 0.001


class TestCharacterStore:
    """Tests for character database storage"""
    
    def test_init(self, tmp_path):
        """Test store initialization"""
        db_path = tmp_path / "characters.db"
        
        from backend.services.face_service import CharacterStore
        store = CharacterStore(str(db_path))
        assert store is not None
        assert db_path.exists()
    
    def test_save_character(self, tmp_path):
        """Test saving a character"""
        import numpy as np
        
        db_path = tmp_path / "characters.db"
        
        from backend.services.face_service import CharacterStore, Character
        store = CharacterStore(str(db_path))
        
        character = Character(
            id='char-001',
            name='Test Hero',
            embedding=np.random.rand(512).astype(np.float32),
            reference_images=['image1.jpg', 'image2.jpg'],
            reference_embeddings=[np.random.rand(512).astype(np.float32)]
        )
        
        store.save_character(character)
        loaded = store.load_character('char-001')
        
        assert loaded is not None
        assert loaded.name == 'Test Hero'
    
    def test_load_character_not_found(self, tmp_path):
        """Test loading non-existent character"""
        db_path = tmp_path / "characters.db"
        
        from backend.services.face_service import CharacterStore
        store = CharacterStore(str(db_path))
        
        loaded = store.load_character('nonexistent')
        assert loaded is None
    
    def test_list_characters(self, tmp_path):
        """Test listing all characters"""
        import numpy as np
        
        db_path = tmp_path / "characters.db"
        
        from backend.services.face_service import CharacterStore, Character
        store = CharacterStore(str(db_path))
        
        for i in range(3):
            character = Character(
                id=f'char-{i}',
                name=f'Character {i}',
                embedding=np.random.rand(512).astype(np.float32),
                reference_images=[f'image{i}.jpg'],
                reference_embeddings=[]
            )
            store.save_character(character)
        
        characters = store.list_characters()
        assert len(characters) == 3
    
    def test_delete_character(self, tmp_path):
        """Test deleting a character"""
        import numpy as np
        
        db_path = tmp_path / "characters.db"
        
        from backend.services.face_service import CharacterStore, Character
        store = CharacterStore(str(db_path))
        
        character = Character(
            id='char-delete',
            name='To Delete',
            embedding=np.random.rand(512).astype(np.float32),
            reference_images=[],
            reference_embeddings=[]
        )
        store.save_character(character)
        
        store.delete_character('char-delete')
        loaded = store.load_character('char-delete')
        assert loaded is None


class TestFaceService:
    """Tests for main FaceService"""
    
    def test_init(self):
        """Test service initialization"""
        with patch('mediapipe.solutions.face_detection.FaceDetection'):
            with patch('insightface.app.FaceAnalysis'):
                from backend.services.face_service import FaceService
                service = FaceService()
                assert service is not None
    
    def test_detect_faces(self):
        """Test face detection via service"""
        import numpy as np
        
        img_array = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch('mediapipe.solutions.face_detection.FaceDetection'):
            with patch('insightface.app.FaceAnalysis'):
                from backend.services.face_service import FaceService, FaceDetection
                service = FaceService()
                
                mock_detection = FaceDetection(
                    bbox=(100, 100, 200, 200),
                    confidence=0.95,
                    landmarks={}
                )
                
                with patch.object(service.detector, 'detect', return_value=[mock_detection]):
                    faces = service.detect_faces(img_array)
                    assert len(faces) == 1
                    assert faces[0].confidence == 0.95
    
    def test_register_character(self, tmp_path):
        """Test character registration"""
        import numpy as np
        from PIL import Image
        
        img_path = tmp_path / "face.jpg"
        img = Image.new('RGB', (640, 480), color='white')
        img.save(str(img_path))
        
        with patch('mediapipe.solutions.face_detection.FaceDetection'):
            with patch('insightface.app.FaceAnalysis'):
                from backend.services.face_service import FaceService
                service = FaceService()
                
                mock_embedding = np.random.rand(512).astype(np.float32)
                
                with patch.object(service.embedder, 'get_embedding', return_value=mock_embedding):
                    with patch('cv2.imread', return_value=np.zeros((480, 640, 3), dtype=np.uint8)):
                        character = service.register_character(
                            name='Test Character',
                            reference_images=[str(img_path)]
                        )
                        
                        assert character is not None
                        assert character.name == 'Test Character'
    
    def test_verify_character(self, tmp_path):
        """Test character verification"""
        import numpy as np
        
        with patch('mediapipe.solutions.face_detection.FaceDetection'):
            with patch('insightface.app.FaceAnalysis'):
                from backend.services.face_service import FaceService, Character
                service = FaceService()
                
                mock_character = Character(
                    id='char-verify',
                    name='Verify Test',
                    embedding=np.random.rand(512).astype(np.float32),
                    reference_images=[],
                    reference_embeddings=[]
                )
                
                mock_embedding = mock_character.embedding.copy()
                
                with patch.object(service.store, 'load_character', return_value=mock_character):
                    with patch.object(service.embedder, 'get_embedding', return_value=mock_embedding):
                        result = service.verify_character(
                            image=np.zeros((480, 640, 3), dtype=np.uint8),
                            character_id='char-verify'
                        )
                        
                        assert result['verified'] == True
                        assert result['similarity'] > 0.9
    
    def test_verify_character_not_found(self):
        """Test verification with non-existent character"""
        with patch('mediapipe.solutions.face_detection.FaceDetection'):
            with patch('insightface.app.FaceAnalysis'):
                from backend.services.face_service import FaceService
                service = FaceService()
                
                with patch.object(service.store, 'load_character', return_value=None):
                    result = service.verify_character(
                        image=np.zeros((480, 640, 3), dtype=np.uint8),
                        character_id='nonexistent'
                    )
                    
                    assert result['verified'] == False
                    assert 'not found' in result.get('error', '').lower()
    
    def test_find_matching_characters(self):
        """Test finding matching characters"""
        import numpy as np
        
        with patch('mediapipe.solutions.face_detection.FaceDetection'):
            with patch('insightface.app.FaceAnalysis'):
                from backend.services.face_service import FaceService, Character
                service = FaceService()
                
                test_embedding = np.random.rand(512).astype(np.float32)
                test_embedding = test_embedding / np.linalg.norm(test_embedding)
                
                mock_characters = [
                    Character(
                        id='char-1',
                        name='Match',
                        embedding=test_embedding,
                        reference_images=[],
                        reference_embeddings=[]
                    ),
                    Character(
                        id='char-2',
                        name='No Match',
                        embedding=np.random.rand(512).astype(np.float32),
                        reference_images=[],
                        reference_embeddings=[]
                    )
                ]
                
                with patch.object(service.store, 'list_characters', return_value=mock_characters):
                    with patch.object(service.embedder, 'get_embedding', return_value=test_embedding):
                        matches = service.find_matching_characters(
                            image=np.zeros((480, 640, 3), dtype=np.uint8)
                        )
                        
                        assert len(matches) >= 1
                        assert matches[0]['character_id'] == 'char-1'


class TestFaceDataModels:
    """Tests for face service data models"""
    
    def test_face_detection_model(self):
        """Test FaceDetection dataclass"""
        from backend.services.face_service import FaceDetection
        
        detection = FaceDetection(
            bbox=(100, 100, 200, 200),
            confidence=0.95,
            landmarks={'nose': (150, 150)}
        )
        
        assert detection.bbox == (100, 100, 200, 200)
        assert detection.confidence == 0.95
        assert 'nose' in detection.landmarks
    
    def test_character_model(self):
        """Test Character dataclass"""
        import numpy as np
        
        from backend.services.face_service import Character
        
        character = Character(
            id='test-char',
            name='Test',
            embedding=np.zeros(512),
            reference_images=['img.jpg'],
            reference_embeddings=[]
        )
        
        assert character.id == 'test-char'
        assert character.name == 'Test'
        assert len(character.embedding) == 512


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
