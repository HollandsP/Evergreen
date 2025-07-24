"""
Intelligent Cropping and Framing Optimization Engine.

This service uses computer vision and AI to:
- Analyze video content and detect important regions
- Suggest optimal crops for different aspect ratios (16:9, 9:16, 1:1, 4:5)
- Detect faces, objects, and text for content-aware cropping
- Provide automatic framing optimization for social media formats
- Generate crop suggestions with confidence scores

Supports automatic optimization for YouTube, Instagram, TikTok, and Twitter formats.
"""

import os
import cv2
import numpy as np
import logging
import asyncio
import tempfile
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import json
import math
from datetime import datetime

logger = logging.getLogger(__name__)

class AspectRatio(Enum):
    """Standard aspect ratios for different platforms."""
    LANDSCAPE_16_9 = "16:9"      # YouTube, landscape
    PORTRAIT_9_16 = "9:16"       # TikTok, Instagram Stories
    SQUARE_1_1 = "1:1"           # Instagram posts
    VERTICAL_4_5 = "4:5"         # Instagram posts (vertical)
    ULTRAWIDE_21_9 = "21:9"      # Cinematic
    STANDARD_4_3 = "4:3"         # Classic TV

class CropStrategy(Enum):
    """Cropping strategies for different content types."""
    CENTER_WEIGHTED = "center_weighted"      # Focus on center with some bias
    FACE_DETECTION = "face_detection"        # Prioritize detected faces
    OBJECT_DETECTION = "object_detection"    # Focus on important objects
    TEXT_AWARE = "text_aware"               # Preserve text regions
    MOTION_TRACKING = "motion_tracking"      # Follow motion in video
    RULE_OF_THIRDS = "rule_of_thirds"       # Artistic composition
    SAFE_CROP = "safe_crop"                 # Conservative, safe cropping

@dataclass
class CropRegion:
    """Represents a crop region with coordinates and metadata."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    strategy: CropStrategy
    aspect_ratio: AspectRatio
    content_score: float  # How much important content is preserved
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'confidence': self.confidence,
            'strategy': self.strategy.value,
            'aspect_ratio': self.aspect_ratio.value,
            'content_score': self.content_score
        }

@dataclass
class DetectionResult:
    """Results from content detection (faces, objects, text)."""
    faces: List[Tuple[int, int, int, int]]  # (x, y, w, h) rectangles
    objects: List[Tuple[int, int, int, int, float]]  # (x, y, w, h, confidence)
    text_regions: List[Tuple[int, int, int, int]]  # (x, y, w, h) rectangles
    motion_areas: List[Tuple[int, int, int, int]]  # (x, y, w, h) rectangles
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'faces': self.faces,
            'objects': [list(obj) for obj in self.objects],
            'text_regions': self.text_regions,
            'motion_areas': self.motion_areas
        }

@dataclass
class CropSuggestion:
    """Complete crop suggestion with multiple options."""
    original_size: Tuple[int, int]
    target_aspect_ratio: AspectRatio
    recommended_crop: CropRegion
    alternative_crops: List[CropRegion]
    detection_results: DetectionResult
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'original_size': list(self.original_size),
            'target_aspect_ratio': self.target_aspect_ratio.value,
            'recommended_crop': self.recommended_crop.to_dict(),
            'alternative_crops': [crop.to_dict() for crop in self.alternative_crops],
            'detection_results': self.detection_results.to_dict(),
            'processing_time': self.processing_time
        }

class IntelligentCropper:
    """
    AI-powered intelligent cropping system for video content optimization.
    
    Features:
    - Face detection with priority weighting
    - Object detection for content awareness
    - Text region preservation
    - Motion tracking for dynamic content
    - Multi-strategy crop suggestions
    - Platform-specific aspect ratio optimization
    - Confidence scoring for all suggestions
    """
    
    def __init__(self):
        """Initialize intelligent cropper with detection models."""
        self.face_cascade = None
        self.text_detector = None
        self._initialize_detectors()
        
        # Platform-specific aspect ratio mappings
        self.platform_ratios = {
            'youtube': AspectRatio.LANDSCAPE_16_9,
            'tiktok': AspectRatio.PORTRAIT_9_16,
            'instagram_post': AspectRatio.SQUARE_1_1,
            'instagram_story': AspectRatio.PORTRAIT_9_16,
            'instagram_vertical': AspectRatio.VERTICAL_4_5,
            'twitter': AspectRatio.LANDSCAPE_16_9,
            'cinematic': AspectRatio.ULTRAWIDE_21_9
        }
        
        logger.info("Intelligent Cropper initialized")
    
    def _initialize_detectors(self):
        """Initialize computer vision detection models."""
        try:
            # Load Haar cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                logger.info("Face detection model loaded")
            else:
                logger.warning("Face detection model not found")
            
            # Initialize text detector (using EAST or similar)
            # Note: In production, this could use more sophisticated models
            logger.info("Text detection initialized")
            
        except Exception as e:
            logger.error(f"Error initializing detectors: {e}")
    
    async def suggest_crops_for_video(self, 
                                    video_path: str,
                                    target_aspect_ratios: List[AspectRatio],
                                    sample_frames: int = 5) -> Dict[AspectRatio, CropSuggestion]:
        """
        Suggest optimal crops for a video across multiple aspect ratios.
        
        Args:
            video_path: Path to input video
            target_aspect_ratios: List of desired aspect ratios
            sample_frames: Number of frames to analyze
            
        Returns:
            Dictionary mapping aspect ratios to crop suggestions
        """
        try:
            start_time = datetime.now()
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video not found: {video_path}")
            
            logger.info(f"Analyzing video for cropping: {video_path}")
            
            # Extract sample frames for analysis
            frames = await self._extract_sample_frames(video_path, sample_frames)
            
            if not frames:
                raise ValueError("No frames could be extracted from video")
            
            # Get video dimensions
            cap = cv2.VideoCapture(video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            original_size = (width, height)
            
            # Generate crop suggestions for each aspect ratio
            suggestions = {}
            
            for aspect_ratio in target_aspect_ratios:
                suggestion = await self._generate_crop_suggestion(
                    frames, original_size, aspect_ratio
                )
                suggestions[aspect_ratio] = suggestion
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Crop analysis completed in {processing_time:.2f}s")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in crop suggestion: {e}")
            return {}
    
    async def suggest_crop_for_frame(self, 
                                   frame: np.ndarray,
                                   target_aspect_ratio: AspectRatio,
                                   strategy: Optional[CropStrategy] = None) -> CropSuggestion:
        """
        Suggest crop for a single frame.
        
        Args:
            frame: Input frame as numpy array
            target_aspect_ratio: Desired aspect ratio
            strategy: Optional specific cropping strategy
            
        Returns:
            Crop suggestion for the frame
        """
        start_time = datetime.now()
        
        original_size = (frame.shape[1], frame.shape[0])  # (width, height)
        
        # Detect content in frame
        detection_results = await self._detect_content(frame)
        
        # Generate crop suggestions using different strategies
        if strategy:
            strategies = [strategy]
        else:
            strategies = [
                CropStrategy.FACE_DETECTION,
                CropStrategy.CENTER_WEIGHTED,
                CropStrategy.RULE_OF_THIRDS,
                CropStrategy.SAFE_CROP
            ]
        
        crop_regions = []
        
        for crop_strategy in strategies:
            region = await self._generate_crop_region(
                frame, original_size, target_aspect_ratio, 
                crop_strategy, detection_results
            )
            if region:
                crop_regions.append(region)
        
        # Select best crop as recommended
        recommended_crop = self._select_best_crop(crop_regions)
        alternative_crops = [crop for crop in crop_regions if crop != recommended_crop]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return CropSuggestion(
            original_size=original_size,
            target_aspect_ratio=target_aspect_ratio,
            recommended_crop=recommended_crop,
            alternative_crops=alternative_crops,
            detection_results=detection_results,
            processing_time=processing_time
        )
    
    async def _extract_sample_frames(self, video_path: str, num_frames: int) -> List[np.ndarray]:
        """Extract evenly distributed sample frames from video."""
        try:
            cap = cv2.VideoCapture(video_path)
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count <= 0:
                cap.release()
                return []
            
            # Calculate frame indices to sample
            frame_indices = np.linspace(0, frame_count - 1, num_frames, dtype=int)
            
            frames = []
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            
            cap.release()
            logger.info(f"Extracted {len(frames)} sample frames")
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return []
    
    async def _detect_content(self, frame: np.ndarray) -> DetectionResult:
        """Detect faces, objects, text, and motion areas in frame."""
        faces = []
        objects = []
        text_regions = []
        motion_areas = []
        
        try:
            # Face detection
            if self.face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detected_faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                faces = [tuple(face) for face in detected_faces]
            
            # Object detection (simplified - could use YOLO, etc.)
            objects = await self._detect_objects_simple(frame)
            
            # Text detection (simplified)
            text_regions = await self._detect_text_regions(frame)
            
            # Motion detection (if this is part of a sequence)
            # For single frame, we'll skip motion detection
            
        except Exception as e:
            logger.error(f"Error in content detection: {e}")
        
        return DetectionResult(
            faces=faces,
            objects=objects,
            text_regions=text_regions,
            motion_areas=motion_areas
        )
    
    async def _detect_objects_simple(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """Simple object detection using edge detection and contours."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            objects = []
            min_area = frame.shape[0] * frame.shape[1] * 0.01  # At least 1% of frame
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    confidence = min(1.0, area / (frame.shape[0] * frame.shape[1] * 0.1))
                    objects.append((x, y, w, h, confidence))
            
            # Sort by confidence and return top objects
            objects.sort(key=lambda obj: obj[4], reverse=True)
            return objects[:10]  # Top 10 objects
            
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return []
    
    async def _detect_text_regions(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect text regions using morphological operations."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Use morphological operations to find text-like regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            
            # Gradient operation
            gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
            
            # Threshold
            _, thresh = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological closing
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter based on aspect ratio and size (typical for text)
                aspect_ratio = w / h if h > 0 else 0
                if 2 < aspect_ratio < 20 and w > 20 and h > 8:
                    text_regions.append((x, y, w, h))
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Error in text detection: {e}")
            return []
    
    async def _generate_crop_suggestion(self, 
                                      frames: List[np.ndarray],
                                      original_size: Tuple[int, int],
                                      target_aspect_ratio: AspectRatio) -> CropSuggestion:
        """Generate crop suggestion for multiple frames."""
        start_time = datetime.now()
        
        # Analyze all frames and aggregate results
        all_detections = []
        all_crops = []
        
        for frame in frames:
            detection = await self._detect_content(frame)
            all_detections.append(detection)
            
            # Generate crops for this frame
            for strategy in [CropStrategy.FACE_DETECTION, CropStrategy.CENTER_WEIGHTED, 
                           CropStrategy.RULE_OF_THIRDS]:
                crop = await self._generate_crop_region(
                    frame, original_size, target_aspect_ratio, strategy, detection
                )
                if crop:
                    all_crops.append(crop)
        
        # Aggregate detection results
        aggregated_detection = self._aggregate_detections(all_detections)
        
        # Select best crops
        recommended_crop = self._select_best_crop(all_crops)
        alternative_crops = [crop for crop in all_crops if crop != recommended_crop][:3]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return CropSuggestion(
            original_size=original_size,
            target_aspect_ratio=target_aspect_ratio,
            recommended_crop=recommended_crop,
            alternative_crops=alternative_crops,
            detection_results=aggregated_detection,
            processing_time=processing_time
        )
    
    async def _generate_crop_region(self,
                                  frame: np.ndarray,
                                  original_size: Tuple[int, int],
                                  target_aspect_ratio: AspectRatio,
                                  strategy: CropStrategy,
                                  detection_results: DetectionResult) -> Optional[CropRegion]:
        """Generate a crop region using specified strategy."""
        try:
            orig_width, orig_height = original_size
            target_ratio = self._get_aspect_ratio_value(target_aspect_ratio)
            
            # Calculate target dimensions
            if orig_width / orig_height > target_ratio:
                # Original is wider, crop width
                target_height = orig_height
                target_width = int(target_height * target_ratio)
            else:
                # Original is taller, crop height
                target_width = orig_width
                target_height = int(target_width / target_ratio)
            
            # Ensure dimensions don't exceed original
            target_width = min(target_width, orig_width)
            target_height = min(target_height, orig_height)
            
            # Generate crop based on strategy
            if strategy == CropStrategy.FACE_DETECTION:
                crop_region = self._crop_for_faces(
                    original_size, (target_width, target_height), detection_results.faces
                )
            elif strategy == CropStrategy.CENTER_WEIGHTED:
                crop_region = self._crop_center_weighted(
                    original_size, (target_width, target_height)
                )
            elif strategy == CropStrategy.RULE_OF_THIRDS:
                crop_region = self._crop_rule_of_thirds(
                    original_size, (target_width, target_height), detection_results
                )
            elif strategy == CropStrategy.SAFE_CROP:
                crop_region = self._crop_safe(
                    original_size, (target_width, target_height)
                )
            else:
                crop_region = self._crop_center_weighted(
                    original_size, (target_width, target_height)
                )
            
            if crop_region:
                # Calculate content score
                content_score = self._calculate_content_score(
                    crop_region, detection_results, original_size
                )
                
                # Calculate confidence
                confidence = self._calculate_crop_confidence(
                    strategy, detection_results, content_score
                )
                
                return CropRegion(
                    x=crop_region[0],
                    y=crop_region[1],
                    width=crop_region[2],
                    height=crop_region[3],
                    confidence=confidence,
                    strategy=strategy,
                    aspect_ratio=target_aspect_ratio,
                    content_score=content_score
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating crop region: {e}")
            return None
    
    def _get_aspect_ratio_value(self, aspect_ratio: AspectRatio) -> float:
        """Convert aspect ratio enum to numeric value."""
        ratio_map = {
            AspectRatio.LANDSCAPE_16_9: 16/9,
            AspectRatio.PORTRAIT_9_16: 9/16,
            AspectRatio.SQUARE_1_1: 1.0,
            AspectRatio.VERTICAL_4_5: 4/5,
            AspectRatio.ULTRAWIDE_21_9: 21/9,
            AspectRatio.STANDARD_4_3: 4/3
        }
        return ratio_map.get(aspect_ratio, 1.0)
    
    def _crop_for_faces(self, 
                       original_size: Tuple[int, int],
                       target_size: Tuple[int, int],
                       faces: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
        """Generate crop that optimally includes detected faces."""
        if not faces:
            return self._crop_center_weighted(original_size, target_size)
        
        orig_width, orig_height = original_size
        target_width, target_height = target_size
        
        # Calculate bounding box that includes all faces
        min_x = min(face[0] for face in faces)
        min_y = min(face[1] for face in faces)
        max_x = max(face[0] + face[2] for face in faces)
        max_y = max(face[1] + face[3] for face in faces)
        
        # Add padding around faces
        padding_x = int((max_x - min_x) * 0.3)
        padding_y = int((max_y - min_y) * 0.3)
        
        min_x = max(0, min_x - padding_x)
        min_y = max(0, min_y - padding_y)
        max_x = min(orig_width, max_x + padding_x)
        max_y = min(orig_height, max_y + padding_y)
        
        # Center the crop around the face region
        face_center_x = (min_x + max_x) // 2
        face_center_y = (min_y + max_y) // 2
        
        # Calculate crop position
        crop_x = max(0, min(face_center_x - target_width // 2, orig_width - target_width))
        crop_y = max(0, min(face_center_y - target_height // 2, orig_height - target_height))
        
        return (crop_x, crop_y, target_width, target_height)
    
    def _crop_center_weighted(self,
                             original_size: Tuple[int, int],
                             target_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """Generate center-weighted crop with slight bias toward rule of thirds."""
        orig_width, orig_height = original_size
        target_width, target_height = target_size
        
        # Start with center
        center_x = orig_width // 2
        center_y = orig_height // 2
        
        # Add slight bias toward rule of thirds
        bias_x = orig_width * 0.05  # 5% bias
        bias_y = orig_height * 0.05
        
        # Randomly choose upper/lower third bias
        import random
        bias_x *= random.choice([-1, 1])
        bias_y *= random.choice([-1, 1])
        
        center_x += int(bias_x)
        center_y += int(bias_y)
        
        # Calculate crop position
        crop_x = max(0, min(center_x - target_width // 2, orig_width - target_width))
        crop_y = max(0, min(center_y - target_height // 2, orig_height - target_height))
        
        return (crop_x, crop_y, target_width, target_height)
    
    def _crop_rule_of_thirds(self,
                           original_size: Tuple[int, int],
                           target_size: Tuple[int, int],
                           detection_results: DetectionResult) -> Tuple[int, int, int, int]:
        """Generate crop using rule of thirds composition."""
        orig_width, orig_height = original_size
        target_width, target_height = target_size
        
        # Rule of thirds positions
        third_x = orig_width // 3
        third_y = orig_height // 3
        
        # Choose the third position that captures most content
        positions = [
            (third_x, third_y),      # Upper left third
            (third_x * 2, third_y),  # Upper right third
            (third_x, third_y * 2),  # Lower left third
            (third_x * 2, third_y * 2)  # Lower right third
        ]
        
        best_position = positions[0]
        best_score = 0
        
        for pos_x, pos_y in positions:
            # Calculate crop around this position
            crop_x = max(0, min(pos_x - target_width // 2, orig_width - target_width))
            crop_y = max(0, min(pos_y - target_height // 2, orig_height - target_height))
            
            # Score this crop based on content overlap
            crop_region = (crop_x, crop_y, target_width, target_height)
            score = self._calculate_content_score(crop_region, detection_results, original_size)
            
            if score > best_score:
                best_score = score
                best_position = (crop_x, crop_y)
        
        return (best_position[0], best_position[1], target_width, target_height)
    
    def _crop_safe(self,
                   original_size: Tuple[int, int],
                   target_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """Generate conservative center crop."""
        orig_width, orig_height = original_size
        target_width, target_height = target_size
        
        # Simple center crop
        crop_x = (orig_width - target_width) // 2
        crop_y = (orig_height - target_height) // 2
        
        return (crop_x, crop_y, target_width, target_height)
    
    def _calculate_content_score(self,
                               crop_region: Tuple[int, int, int, int],
                               detection_results: DetectionResult,
                               original_size: Tuple[int, int]) -> float:
        """Calculate how much important content is preserved in crop."""
        crop_x, crop_y, crop_w, crop_h = crop_region
        score = 0.0
        total_weight = 0.0
        
        # Score faces (highest priority)
        face_weight = 1.0
        for face in detection_results.faces:
            face_x, face_y, face_w, face_h = face
            overlap = self._calculate_overlap_ratio(
                (face_x, face_y, face_w, face_h),
                (crop_x, crop_y, crop_w, crop_h)
            )
            score += overlap * face_weight
            total_weight += face_weight
        
        # Score objects
        object_weight = 0.6
        for obj in detection_results.objects:
            obj_x, obj_y, obj_w, obj_h, confidence = obj
            overlap = self._calculate_overlap_ratio(
                (obj_x, obj_y, obj_w, obj_h),
                (crop_x, crop_y, crop_w, crop_h)
            )
            score += overlap * object_weight * confidence
            total_weight += object_weight * confidence
        
        # Score text regions
        text_weight = 0.4
        for text in detection_results.text_regions:
            text_x, text_y, text_w, text_h = text
            overlap = self._calculate_overlap_ratio(
                (text_x, text_y, text_w, text_h),
                (crop_x, crop_y, crop_w, crop_h)
            )
            score += overlap * text_weight
            total_weight += text_weight
        
        # If no content detected, give center bias
        if total_weight == 0:
            orig_width, orig_height = original_size
            center_x, center_y = orig_width // 2, orig_height // 2
            crop_center_x = crop_x + crop_w // 2
            crop_center_y = crop_y + crop_h // 2
            
            # Distance from center (normalized)
            distance = np.sqrt((crop_center_x - center_x)**2 + (crop_center_y - center_y)**2)
            max_distance = np.sqrt((orig_width // 2)**2 + (orig_height // 2)**2)
            
            score = 1.0 - (distance / max_distance)
            return max(0.0, min(1.0, score))
        
        return max(0.0, min(1.0, score / total_weight))
    
    def _calculate_overlap_ratio(self,
                               rect1: Tuple[int, int, int, int],
                               rect2: Tuple[int, int, int, int]) -> float:
        """Calculate overlap ratio between two rectangles."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        # Calculate intersection
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left >= right or top >= bottom:
            return 0.0
        
        intersection_area = (right - left) * (bottom - top)
        rect1_area = w1 * h1
        
        if rect1_area == 0:
            return 0.0
        
        return intersection_area / rect1_area
    
    def _calculate_crop_confidence(self,
                                 strategy: CropStrategy,
                                 detection_results: DetectionResult,
                                 content_score: float) -> float:
        """Calculate confidence score for crop suggestion."""
        base_confidence = 0.5
        
        # Strategy-specific confidence adjustments
        strategy_bonus = {
            CropStrategy.FACE_DETECTION: 0.3 if detection_results.faces else 0.0,
            CropStrategy.CENTER_WEIGHTED: 0.2,
            CropStrategy.RULE_OF_THIRDS: 0.25,
            CropStrategy.SAFE_CROP: 0.15
        }
        
        confidence = base_confidence + strategy_bonus.get(strategy, 0.0)
        
        # Content score bonus
        confidence += content_score * 0.2
        
        return max(0.1, min(0.99, confidence))
    
    def _aggregate_detections(self, detections: List[DetectionResult]) -> DetectionResult:
        """Aggregate detection results from multiple frames."""
        all_faces = []
        all_objects = []
        all_text = []
        all_motion = []
        
        for detection in detections:
            all_faces.extend(detection.faces)
            all_objects.extend(detection.objects)
            all_text.extend(detection.text_regions)
            all_motion.extend(detection.motion_areas)
        
        return DetectionResult(
            faces=all_faces,
            objects=all_objects,
            text_regions=all_text,
            motion_areas=all_motion
        )
    
    def _select_best_crop(self, crop_regions: List[CropRegion]) -> CropRegion:
        """Select the best crop from available options."""
        if not crop_regions:
            # Return default center crop
            return CropRegion(
                x=0, y=0, width=100, height=100,
                confidence=0.1, strategy=CropStrategy.SAFE_CROP,
                aspect_ratio=AspectRatio.SQUARE_1_1, content_score=0.1
            )
        
        # Score crops based on confidence and content score
        best_crop = max(crop_regions, key=lambda crop: crop.confidence * 0.6 + crop.content_score * 0.4)
        return best_crop
    
    def get_platform_aspect_ratio(self, platform: str) -> Optional[AspectRatio]:
        """Get recommended aspect ratio for platform."""
        return self.platform_ratios.get(platform.lower())
    
    async def apply_crop_to_video(self,
                                input_path: str,
                                output_path: str,
                                crop_region: CropRegion) -> bool:
        """Apply crop to video file using FFmpeg."""
        try:
            import subprocess
            
            cmd = [
                'ffmpeg', '-y',
                '-i', input_path,
                '-filter:v', f'crop={crop_region.width}:{crop_region.height}:{crop_region.x}:{crop_region.y}',
                '-c:a', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully applied crop to {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying crop: {e}")
            return False


# Global instance
_intelligent_cropper = None

def get_intelligent_cropper() -> IntelligentCropper:
    """Get global intelligent cropper instance."""
    global _intelligent_cropper
    if _intelligent_cropper is None:
        _intelligent_cropper = IntelligentCropper()
    return _intelligent_cropper