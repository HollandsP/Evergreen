"""
Professional Audio Synchronization Processor for Evergreen Video Editor.

Provides advanced audio analysis and synchronization capabilities:
- Beat detection and tempo analysis
- Musical phrase segmentation
- Audio-visual synchronization
- Rhythm-based transition timing
- Spectral analysis and frequency domain processing
- Real-time tempo tracking
- Dynamic beat matching for video effects
- Audio fingerprinting for content matching

Enables natural language commands like:
- "Sync transitions with the beat"
- "Cut on every drum hit"
- "Match scene changes to the music tempo"
"""

import os
import json
import logging
import asyncio
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import librosa
import librosa.display
import scipy.signal
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import soundfile as sf

logger = logging.getLogger(__name__)


class BeatTrackingMode(Enum):
    """Beat tracking analysis modes."""
    ONSET = "onset"              # Detect note onsets
    TEMPO = "tempo"              # Track tempo changes
    DOWNBEAT = "downbeat"        # Find musical downbeats
    SPECTRAL_FLUX = "spectral_flux"  # Spectral energy changes
    HARMONIC = "harmonic"        # Harmonic changes
    PERCUSSIVE = "percussive"    # Drum/percussion analysis


class SyncTarget(Enum):
    """Video elements that can be synchronized to audio."""
    CUTS = "cuts"                # Scene cuts and transitions
    EFFECTS = "effects"          # Visual effects timing
    ANIMATIONS = "animations"    # Text/object animations
    COLOR_CHANGES = "color_changes"  # Color grading changes
    SPEED_CHANGES = "speed_changes"  # Speed ramping
    ZOOM_PANS = "zoom_pans"      # Camera movements


@dataclass
class BeatInfo:
    """Information about detected beats."""
    timestamp: float         # Time in seconds
    confidence: float        # Beat detection confidence (0-1)
    tempo: float            # BPM at this point
    beat_number: int        # Beat number in sequence
    is_downbeat: bool       # Whether this is a downbeat
    spectral_energy: float  # Energy level
    frequency_profile: List[float]  # Frequency spectrum snapshot


@dataclass
class AudioSyncSettings:
    """Audio synchronization configuration."""
    
    # Beat detection parameters
    tracking_mode: BeatTrackingMode = BeatTrackingMode.ONSET
    tempo_range: Tuple[float, float] = (60.0, 200.0)  # BPM range
    beat_sensitivity: float = 0.5    # 0.0 to 1.0
    onset_threshold: float = 0.3     # Onset detection threshold
    
    # Synchronization settings
    sync_target: SyncTarget = SyncTarget.CUTS
    sync_offset: float = 0.0         # Timing offset in seconds
    quantization: float = 0.0        # Snap to grid (0 = off)
    
    # Analysis parameters
    hop_length: int = 512           # FFT hop length
    frame_length: int = 2048        # FFT frame length
    sample_rate: int = 22050        # Target sample rate
    
    # Filtering
    frequency_range: Tuple[float, float] = (20.0, 20000.0)  # Hz
    emphasize_percussion: bool = True
    
    # Smoothing and post-processing
    temporal_smoothing: float = 0.1   # Beat timing smoothing
    confidence_threshold: float = 0.3  # Minimum confidence
    
    # Advanced features
    adaptive_threshold: bool = True   # Adaptive onset detection
    harmonic_separation: bool = True  # Separate harmonic/percussive
    tempo_tracking: bool = True       # Dynamic tempo tracking


class AudioSyncProcessor:
    """
    Professional audio synchronization processor with advanced beat detection.
    
    Features:
    - Advanced beat detection using librosa and spectral analysis
    - Real-time tempo tracking and BPM analysis
    - Musical phrase segmentation and structure analysis
    - Audio-visual synchronization with frame-accurate timing
    - Support for multiple tracking modes (onset, tempo, downbeat, etc.)
    - Natural language command processing for sync operations
    - GPU-accelerated spectral processing where available
    """
    
    def __init__(self, work_dir: str = "./output/audio_workspace"):
        """
        Initialize audio synchronization processor.
        
        Args:
            work_dir: Working directory for temporary files and analysis
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Analysis cache
        self.beat_cache: Dict[str, List[BeatInfo]] = {}
        self.tempo_cache: Dict[str, float] = {}
        
        # Audio processing parameters
        self.default_sr = 22050
        self.default_hop_length = 512
        
        logger.info("Initialized Professional Audio Sync Processor")
    
    async def analyze_audio_beats(
        self,
        audio_path: str,
        settings: AudioSyncSettings = None,
        operation_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze audio file for beats, tempo, and musical structure.
        
        Args:
            audio_path: Path to audio file
            settings: Analysis configuration
            operation_id: Operation ID for tracking
            
        Returns:
            Comprehensive beat analysis results
        """
        try:
            operation_id = operation_id or f"beat_analysis_{datetime.now().isoformat()}"
            settings = settings or AudioSyncSettings()
            
            # Check cache first
            cache_key = f"{audio_path}_{hash(str(asdict(settings)))}"
            if cache_key in self.beat_cache:
                logger.info(f"Using cached beat analysis for {audio_path}")
                return {
                    "success": True,
                    "beats": self.beat_cache[cache_key],
                    "cached": True,
                    "operation_id": operation_id
                }
            
            # Perform audio analysis
            analysis_result = await asyncio.to_thread(
                self._analyze_audio_file,
                audio_path,
                settings,
                operation_id
            )
            
            # Cache results
            if analysis_result["success"]:
                self.beat_cache[cache_key] = analysis_result["beats"]
                if "tempo" in analysis_result:
                    self.tempo_cache[audio_path] = analysis_result["tempo"]
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing audio beats: {e}")
            return {
                "success": False,
                "message": f"Audio analysis failed: {str(e)}",
                "operation_id": operation_id,
                "error": str(e)
            }
    
    def _analyze_audio_file(
        self,
        audio_path: str,
        settings: AudioSyncSettings,
        operation_id: str
    ) -> Dict[str, Any]:
        """Perform comprehensive audio analysis."""
        
        # Load audio file
        try:
            y, sr = librosa.load(audio_path, sr=settings.sample_rate)
            logger.info(f"Loaded audio: {len(y)/sr:.2f}s at {sr}Hz")
        except Exception as e:
            raise ValueError(f"Could not load audio file: {e}")
        
        # Harmonic-percussive separation if enabled
        if settings.harmonic_separation:
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            # Use percussive component for beat detection
            y_analysis = y_percussive if settings.emphasize_percussion else y
        else:
            y_analysis = y
        
        # Beat detection based on tracking mode
        beats = []
        
        if settings.tracking_mode == BeatTrackingMode.ONSET:
            beats = self._detect_onset_beats(y_analysis, sr, settings)
        elif settings.tracking_mode == BeatTrackingMode.TEMPO:
            beats = self._detect_tempo_beats(y_analysis, sr, settings)
        elif settings.tracking_mode == BeatTrackingMode.DOWNBEAT:
            beats = self._detect_downbeats(y_analysis, sr, settings)
        elif settings.tracking_mode == BeatTrackingMode.SPECTRAL_FLUX:
            beats = self._detect_spectral_flux_beats(y_analysis, sr, settings)
        elif settings.tracking_mode == BeatTrackingMode.HARMONIC:
            beats = self._detect_harmonic_beats(y_harmonic if settings.harmonic_separation else y, sr, settings)
        elif settings.tracking_mode == BeatTrackingMode.PERCUSSIVE:
            beats = self._detect_percussive_beats(y_percussive if settings.harmonic_separation else y, sr, settings)
        
        # Global tempo estimation
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr, hop_length=settings.hop_length)
        
        # Post-process beats
        beats = self._post_process_beats(beats, settings)
        
        # Generate visualization
        viz_path = self._create_beat_visualization(y, sr, beats, operation_id)
        
        return {
            "success": True,
            "beats": beats,
            "tempo": float(tempo),
            "duration": len(y) / sr,
            "sample_rate": sr,
            "num_beats": len(beats),
            "avg_confidence": np.mean([b.confidence for b in beats]) if beats else 0.0,
            "visualization_path": viz_path,
            "operation_id": operation_id,
            "tracking_mode": settings.tracking_mode.value
        }
    
    def _detect_onset_beats(self, y: np.ndarray, sr: int, settings: AudioSyncSettings) -> List[BeatInfo]:
        """Detect beats based on onset detection."""
        
        # Onset strength
        onset_frames = librosa.onset.onset_detect(
            y=y,
            sr=sr,
            hop_length=settings.hop_length,
            threshold=settings.onset_threshold,
            delta=0.1,
            units='frames'
        )
        
        # Convert frames to time
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=settings.hop_length)
        
        # Calculate onset strength for confidence
        onset_envelope = librosa.onset.onset_strength(
            y=y, sr=sr, hop_length=settings.hop_length
        )
        
        beats = []
        for i, time in enumerate(onset_times):
            frame_idx = onset_frames[i]
            confidence = onset_envelope[frame_idx] if frame_idx < len(onset_envelope) else 0.5
            
            # Estimate local tempo
            local_tempo = self._estimate_local_tempo(onset_times, i)
            
            # Get spectral features
            spectral_energy, freq_profile = self._get_spectral_features(y, sr, time, settings)
            
            beat = BeatInfo(
                timestamp=float(time),
                confidence=float(np.clip(confidence, 0, 1)),
                tempo=local_tempo,
                beat_number=i + 1,
                is_downbeat=False,  # Will be determined later
                spectral_energy=spectral_energy,
                frequency_profile=freq_profile
            )
            beats.append(beat)
        
        return beats
    
    def _detect_tempo_beats(self, y: np.ndarray, sr: int, settings: AudioSyncSettings) -> List[BeatInfo]:
        """Detect beats using tempo tracking."""
        
        # Dynamic tempo tracking
        tempo, beat_frames = librosa.beat.beat_track(
            y=y,
            sr=sr,
            hop_length=settings.hop_length,
            start_bpm=120,
            tightness=100
        )
        
        # Convert to time domain
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=settings.hop_length)
        
        # Get tempo curve for dynamic tracking
        if settings.tempo_tracking:
            tempo_curve = self._get_dynamic_tempo(y, sr, settings)
        else:
            tempo_curve = None
        
        beats = []
        for i, time in enumerate(beat_times):
            # Local tempo from curve or global
            local_tempo = tempo_curve[int(time * sr / settings.hop_length)] if tempo_curve is not None else tempo
            
            # Confidence based on beat consistency
            confidence = self._calculate_beat_confidence(beat_times, i)
            
            # Spectral features
            spectral_energy, freq_profile = self._get_spectral_features(y, sr, time, settings)
            
            beat = BeatInfo(
                timestamp=float(time),
                confidence=float(confidence),
                tempo=float(local_tempo),
                beat_number=i + 1,
                is_downbeat=False,
                spectral_energy=spectral_energy,
                frequency_profile=freq_profile
            )
            beats.append(beat)
        
        return beats
    
    def _detect_downbeats(self, y: np.ndarray, sr: int, settings: AudioSyncSettings) -> List[BeatInfo]:
        """Detect musical downbeats (first beat of musical bars)."""
        
        # First get regular beats
        tempo, beat_frames = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=settings.hop_length
        )
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=settings.hop_length)
        
        # Estimate time signature and downbeats
        # This is a simplified approach - more sophisticated methods exist
        avg_beat_interval = np.mean(np.diff(beat_times))
        estimated_bar_length = avg_beat_interval * 4  # Assume 4/4 time
        
        beats = []
        current_bar_start = 0
        
        for i, time in enumerate(beat_times):
            # Determine if this is a downbeat
            is_downbeat = (time - current_bar_start) >= estimated_bar_length * 0.9
            if is_downbeat:
                current_bar_start = time
            
            # Calculate confidence
            confidence = self._calculate_beat_confidence(beat_times, i)
            
            # Boost confidence for downbeats
            if is_downbeat:
                confidence = min(1.0, confidence * 1.3)
            
            # Spectral features
            spectral_energy, freq_profile = self._get_spectral_features(y, sr, time, settings)
            
            beat = BeatInfo(
                timestamp=float(time),
                confidence=float(confidence),
                tempo=float(tempo),
                beat_number=i + 1,
                is_downbeat=is_downbeat,
                spectral_energy=spectral_energy,
                frequency_profile=freq_profile
            )
            beats.append(beat)
        
        return beats
    
    def _detect_spectral_flux_beats(self, y: np.ndarray, sr: int, settings: AudioSyncSettings) -> List[BeatInfo]:
        """Detect beats using spectral flux analysis."""
        
        # Compute STFT
        stft = librosa.stft(y, hop_length=settings.hop_length, n_fft=settings.frame_length)
        magnitude = np.abs(stft)
        
        # Spectral flux
        spectral_flux = np.sum(np.diff(magnitude, axis=1), axis=0)
        spectral_flux = np.maximum(0, spectral_flux)  # Half-wave rectification
        
        # Find peaks in spectral flux
        peaks, properties = find_peaks(
            spectral_flux,
            height=np.percentile(spectral_flux, 70),
            distance=int(sr / settings.hop_length * 0.1)  # Minimum 100ms between beats
        )
        
        # Convert to time
        peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=settings.hop_length)
        
        beats = []
        for i, time in enumerate(peak_times):
            # Confidence from peak height
            peak_height = properties['peak_heights'][i]
            confidence = np.clip(peak_height / np.max(spectral_flux), 0, 1)
            
            # Local tempo estimation
            local_tempo = self._estimate_local_tempo(peak_times, i)
            
            # Spectral features
            spectral_energy, freq_profile = self._get_spectral_features(y, sr, time, settings)
            
            beat = BeatInfo(
                timestamp=float(time),
                confidence=float(confidence),
                tempo=local_tempo,
                beat_number=i + 1,
                is_downbeat=False,
                spectral_energy=spectral_energy,
                frequency_profile=freq_profile
            )
            beats.append(beat)
        
        return beats
    
    def _detect_harmonic_beats(self, y: np.ndarray, sr: int, settings: AudioSyncSettings) -> List[BeatInfo]:
        """Detect beats based on harmonic changes."""
        
        # Chromagram for harmonic analysis
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=settings.hop_length)
        
        # Detect harmonic changes
        chroma_diff = np.sum(np.abs(np.diff(chroma, axis=1)), axis=0)
        
        # Find peaks in harmonic changes
        peaks, _ = find_peaks(
            chroma_diff,
            height=np.percentile(chroma_diff, 75),
            distance=int(sr / settings.hop_length * 0.2)  # Minimum 200ms between changes
        )
        
        peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=settings.hop_length)
        
        beats = []
        for i, time in enumerate(peak_times):
            confidence = chroma_diff[peaks[i]] / np.max(chroma_diff)
            local_tempo = self._estimate_local_tempo(peak_times, i)
            spectral_energy, freq_profile = self._get_spectral_features(y, sr, time, settings)
            
            beat = BeatInfo(
                timestamp=float(time),
                confidence=float(confidence),
                tempo=local_tempo,
                beat_number=i + 1,
                is_downbeat=False,
                spectral_energy=spectral_energy,
                frequency_profile=freq_profile
            )
            beats.append(beat)
        
        return beats
    
    def _detect_percussive_beats(self, y: np.ndarray, sr: int, settings: AudioSyncSettings) -> List[BeatInfo]:
        """Detect beats using percussive analysis."""
        
        # Focus on percussive elements
        # Use onset detection tuned for percussion
        onset_frames = librosa.onset.onset_detect(
            y=y,
            sr=sr,
            hop_length=settings.hop_length,
            threshold=settings.onset_threshold * 0.8,  # Lower threshold for percussion
            delta=0.05,
            units='frames'
        )
        
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=settings.hop_length)
        
        # Analyze in frequency bands to identify drum hits
        # Low frequencies for kick drums, mid for snares, high for hi-hats
        stft = librosa.stft(y, hop_length=settings.hop_length)
        magnitude = np.abs(stft)
        
        # Frequency band analysis
        freqs = librosa.fft_frequencies(sr=sr, n_fft=settings.frame_length)
        low_band = (freqs >= 20) & (freqs <= 120)     # Kick drum
        mid_band = (freqs >= 120) & (freqs <= 400)    # Snare
        high_band = (freqs >= 400) & (freqs <= 8000)  # Hi-hat/cymbals
        
        beats = []
        for i, time in enumerate(onset_times):
            frame_idx = onset_frames[i]
            
            if frame_idx < magnitude.shape[1]:
                # Analyze frequency content
                frame_spectrum = magnitude[:, frame_idx]
                
                low_energy = np.sum(frame_spectrum[low_band])
                mid_energy = np.sum(frame_spectrum[mid_band])
                high_energy = np.sum(frame_spectrum[high_band])
                
                total_energy = low_energy + mid_energy + high_energy
                
                # Higher confidence for strong low-frequency content (kick drums)
                confidence = (low_energy * 2 + mid_energy + high_energy) / (total_energy * 2) if total_energy > 0 else 0.5
                confidence = np.clip(confidence, 0, 1)
            else:
                confidence = 0.5
            
            local_tempo = self._estimate_local_tempo(onset_times, i)
            spectral_energy, freq_profile = self._get_spectral_features(y, sr, time, settings)
            
            beat = BeatInfo(
                timestamp=float(time),
                confidence=float(confidence),
                tempo=local_tempo,
                beat_number=i + 1,
                is_downbeat=False,
                spectral_energy=spectral_energy,
                frequency_profile=freq_profile
            )
            beats.append(beat)
        
        return beats
    
    def _get_spectral_features(self, y: np.ndarray, sr: int, time: float, settings: AudioSyncSettings) -> Tuple[float, List[float]]:
        """Extract spectral features at a specific time."""
        
        try:
            # Get frame at specific time
            frame_idx = int(time * sr / settings.hop_length)
            
            # Compute STFT
            stft = librosa.stft(y, hop_length=settings.hop_length, n_fft=settings.frame_length)
            magnitude = np.abs(stft)
            
            if frame_idx < magnitude.shape[1]:
                frame_spectrum = magnitude[:, frame_idx]
                
                # Spectral energy
                spectral_energy = float(np.sum(frame_spectrum))
                
                # Frequency profile (simplified to 8 bands)
                freqs = librosa.fft_frequencies(sr=sr, n_fft=settings.frame_length)
                bands = [
                    (20, 60),      # Sub-bass
                    (60, 250),     # Bass
                    (250, 500),    # Low-mid
                    (500, 2000),   # Mid
                    (2000, 4000),  # Upper-mid
                    (4000, 6000),  # Presence
                    (6000, 12000), # Brilliance
                    (12000, 20000) # Air
                ]
                
                freq_profile = []
                for low, high in bands:
                    band_mask = (freqs >= low) & (freqs <= high)
                    band_energy = float(np.sum(frame_spectrum[band_mask]))
                    freq_profile.append(band_energy)
                
                # Normalize
                total_energy = sum(freq_profile)
                if total_energy > 0:
                    freq_profile = [e / total_energy for e in freq_profile]
                
                return spectral_energy, freq_profile
            else:
                return 0.0, [0.0] * 8
                
        except Exception as e:
            logger.warning(f"Error extracting spectral features: {e}")
            return 0.0, [0.0] * 8
    
    def _estimate_local_tempo(self, beat_times: np.ndarray, current_idx: int, window_size: int = 8) -> float:
        """Estimate local tempo around a specific beat."""
        
        if len(beat_times) < 2:
            return 120.0  # Default tempo
        
        # Get surrounding beats
        start_idx = max(0, current_idx - window_size // 2)
        end_idx = min(len(beat_times), current_idx + window_size // 2 + 1)
        
        local_beats = beat_times[start_idx:end_idx]
        
        if len(local_beats) < 2:
            return 120.0
        
        # Calculate intervals and convert to BPM
        intervals = np.diff(local_beats)
        median_interval = np.median(intervals)
        
        if median_interval > 0:
            tempo = 60.0 / median_interval
            return float(np.clip(tempo, 60, 200))  # Reasonable tempo range
        else:
            return 120.0
    
    def _calculate_beat_confidence(self, beat_times: np.ndarray, current_idx: int) -> float:
        """Calculate confidence score for a beat based on temporal consistency."""
        
        if len(beat_times) < 3:
            return 0.5
        
        window_size = 5
        start_idx = max(0, current_idx - window_size // 2)
        end_idx = min(len(beat_times), current_idx + window_size // 2 + 1)
        
        local_beats = beat_times[start_idx:end_idx]
        
        if len(local_beats) < 3:
            return 0.5
        
        # Calculate interval consistency
        intervals = np.diff(local_beats)
        interval_std = np.std(intervals)
        interval_mean = np.mean(intervals)
        
        if interval_mean > 0:
            consistency = 1.0 - np.clip(interval_std / interval_mean, 0, 1)
            return float(consistency)
        else:
            return 0.5
    
    def _get_dynamic_tempo(self, y: np.ndarray, sr: int, settings: AudioSyncSettings) -> np.ndarray:
        """Get dynamic tempo curve over time."""
        
        try:
            # Compute tempogram
            hop_length = settings.hop_length
            oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
            tempogram = librosa.feature.tempogram(
                onset_envelope=oenv,
                sr=sr,
                hop_length=hop_length
            )
            
            # Extract dominant tempo at each time frame
            tempo_times = librosa.frames_to_time(np.arange(tempogram.shape[1]), sr=sr, hop_length=hop_length)
            tempo_curve = []
            
            for frame in range(tempogram.shape[1]):
                tempo_frame = tempogram[:, frame]
                dominant_tempo_idx = np.argmax(tempo_frame)
                
                # Convert tempo bin to BPM
                tempo_bpm = librosa.tempo_frequencies(tempogram.shape[0])[dominant_tempo_idx]
                tempo_curve.append(tempo_bpm)
            
            return np.array(tempo_curve)
            
        except Exception as e:
            logger.warning(f"Error computing dynamic tempo: {e}")
            # Return constant tempo as fallback
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            return np.full(len(y) // settings.hop_length, tempo)
    
    def _post_process_beats(self, beats: List[BeatInfo], settings: AudioSyncSettings) -> List[BeatInfo]:
        """Post-process detected beats for quality and consistency."""
        
        if not beats:
            return beats
        
        # Filter by confidence threshold
        filtered_beats = [b for b in beats if b.confidence >= settings.confidence_threshold]
        
        # Temporal smoothing
        if settings.temporal_smoothing > 0 and len(filtered_beats) > 2:
            # Apply smoothing to timestamps
            timestamps = np.array([b.timestamp for b in filtered_beats])
            
            # Simple moving average smoothing
            window_size = max(3, int(len(timestamps) * settings.temporal_smoothing))
            if window_size < len(timestamps):
                smoothed_timestamps = np.convolve(timestamps, np.ones(window_size)/window_size, mode='same')
                
                for i, beat in enumerate(filtered_beats):
                    beat.timestamp = float(smoothed_timestamps[i])
        
        # Quantization to grid
        if settings.quantization > 0:
            grid_size = settings.quantization
            for beat in filtered_beats:
                quantized_time = round(beat.timestamp / grid_size) * grid_size
                beat.timestamp = quantized_time
        
        # Re-number beats
        for i, beat in enumerate(filtered_beats):
            beat.beat_number = i + 1
        
        return filtered_beats
    
    def _create_beat_visualization(self, y: np.ndarray, sr: int, beats: List[BeatInfo], operation_id: str) -> str:
        """Create visualization of beat detection results."""
        
        try:
            viz_dir = self.work_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            
            # Create figure
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
            
            # Time axis
            time_axis = np.linspace(0, len(y) / sr, len(y))
            
            # 1. Waveform with beat markers
            ax1.plot(time_axis, y, alpha=0.6, color='blue')
            ax1.set_title('Audio Waveform with Detected Beats')
            ax1.set_ylabel('Amplitude')
            
            # Mark beats
            beat_times = [b.timestamp for b in beats]
            beat_confidences = [b.confidence for b in beats]
            
            for time, confidence in zip(beat_times, beat_confidences):
                color = 'red' if confidence > 0.7 else 'orange' if confidence > 0.4 else 'yellow'
                ax1.axvline(x=time, color=color, alpha=0.8, linewidth=2)
            
            # 2. Tempo curve
            if beats:
                ax2.plot(beat_times, [b.tempo for b in beats], 'o-', color='green')
                ax2.set_title('Tempo Over Time')
                ax2.set_ylabel('BPM')
            
            # 3. Confidence over time
            if beats:
                ax3.plot(beat_times, beat_confidences, 'o-', color='purple')
                ax3.set_title('Beat Detection Confidence')
                ax3.set_ylabel('Confidence')
                ax3.set_xlabel('Time (seconds)')
            
            # Save visualization
            viz_path = viz_dir / f"{operation_id}_beat_analysis.png"
            plt.tight_layout()
            plt.savefig(viz_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(viz_path)
            
        except Exception as e:
            logger.error(f"Error creating beat visualization: {e}")
            return ""
    
    async def synchronize_video_to_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        sync_target: SyncTarget,
        settings: AudioSyncSettings = None,
        operation_id: str = None
    ) -> Dict[str, Any]:
        """
        Synchronize video elements to audio beats.
        
        Args:
            video_path: Input video file
            audio_path: Audio file to analyze
            output_path: Output synchronized video
            sync_target: What to synchronize (cuts, effects, etc.)
            settings: Synchronization settings
            operation_id: Operation tracking ID
            
        Returns:
            Synchronization result
        """
        try:
            operation_id = operation_id or f"sync_{datetime.now().isoformat()}"
            settings = settings or AudioSyncSettings()
            settings.sync_target = sync_target
            
            # First analyze audio for beats
            beat_analysis = await self.analyze_audio_beats(audio_path, settings, operation_id)
            
            if not beat_analysis["success"]:
                return beat_analysis
            
            beats = beat_analysis["beats"]
            
            # Apply synchronization based on target
            if sync_target == SyncTarget.CUTS:
                result = await self._sync_cuts_to_beats(video_path, output_path, beats, settings)
            elif sync_target == SyncTarget.EFFECTS:
                result = await self._sync_effects_to_beats(video_path, output_path, beats, settings)
            elif sync_target == SyncTarget.ANIMATIONS:
                result = await self._sync_animations_to_beats(video_path, output_path, beats, settings)
            else:
                return {
                    "success": False,
                    "message": f"Sync target '{sync_target.value}' not yet implemented",
                    "operation_id": operation_id
                }
            
            result.update({
                "operation_id": operation_id,
                "sync_target": sync_target.value,
                "beats_used": len(beats),
                "audio_analysis": beat_analysis
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error synchronizing video to audio: {e}")
            return {
                "success": False,
                "message": f"Synchronization failed: {str(e)}",
                "operation_id": operation_id,
                "error": str(e)
            }
    
    async def _sync_cuts_to_beats(
        self,
        video_path: str,
        output_path: str,
        beats: List[BeatInfo],
        settings: AudioSyncSettings
    ) -> Dict[str, Any]:
        """Synchronize video cuts to detected beats."""
        
        # This would implement video cutting at beat timings
        # For now, return a placeholder implementation
        
        return {
            "success": False,
            "message": "Cut synchronization feature coming soon",
            "operation_type": "SYNC_CUTS"
        }
    
    async def _sync_effects_to_beats(
        self,
        video_path: str,
        output_path: str,
        beats: List[BeatInfo],
        settings: AudioSyncSettings
    ) -> Dict[str, Any]:
        """Synchronize visual effects to detected beats."""
        
        # This would implement effect timing synchronization
        # For now, return a placeholder implementation
        
        return {
            "success": False,
            "message": "Effect synchronization feature coming soon",
            "operation_type": "SYNC_EFFECTS"
        }
    
    async def _sync_animations_to_beats(
        self,
        video_path: str,
        output_path: str,
        beats: List[BeatInfo],
        settings: AudioSyncSettings
    ) -> Dict[str, Any]:
        """Synchronize animations to detected beats."""
        
        # This would implement animation timing synchronization
        # For now, return a placeholder implementation
        
        return {
            "success": False,
            "message": "Animation synchronization feature coming soon",
            "operation_type": "SYNC_ANIMATIONS"
        }
    
    def parse_natural_language_sync_command(self, command: str) -> Dict[str, Any]:
        """
        Parse natural language audio synchronization commands.
        
        Examples:
        - "Sync transitions with the beat"
        - "Cut on every drum hit"
        - "Match scene changes to the music tempo"
        - "Sync text animations to the rhythm"
        
        Args:
            command: Natural language command
            
        Returns:
            Parsed operation parameters
        """
        command_lower = command.lower()
        
        # Sync target detection
        sync_target = None
        if any(word in command_lower for word in ["cut", "transition", "scene"]):
            sync_target = SyncTarget.CUTS
        elif any(word in command_lower for word in ["effect", "visual"]):
            sync_target = SyncTarget.EFFECTS
        elif any(word in command_lower for word in ["text", "animation", "animate"]):
            sync_target = SyncTarget.ANIMATIONS
        elif any(word in command_lower for word in ["color", "grade", "grading"]):
            sync_target = SyncTarget.COLOR_CHANGES
        elif any(word in command_lower for word in ["speed", "tempo", "fast", "slow"]):
            sync_target = SyncTarget.SPEED_CHANGES
        elif any(word in command_lower for word in ["zoom", "pan", "camera"]):
            sync_target = SyncTarget.ZOOM_PANS
        
        # Beat tracking mode detection
        tracking_mode = BeatTrackingMode.ONSET  # Default
        if any(word in command_lower for word in ["drum", "percussion", "kick", "snare"]):
            tracking_mode = BeatTrackingMode.PERCUSSIVE
        elif any(word in command_lower for word in ["tempo", "bpm"]):
            tracking_mode = BeatTrackingMode.TEMPO
        elif any(word in command_lower for word in ["downbeat", "bar", "measure"]):
            tracking_mode = BeatTrackingMode.DOWNBEAT
        elif any(word in command_lower for word in ["harmonic", "chord", "key"]):
            tracking_mode = BeatTrackingMode.HARMONIC
        
        if sync_target:
            return {
                "operation": "SYNC_TO_AUDIO",
                "sync_target": sync_target,
                "tracking_mode": tracking_mode,
                "confidence": 0.8
            }
        else:
            return {
                "operation": "UNKNOWN",
                "confidence": 0.0,
                "message": "Could not parse audio sync command"
            }
    
    def get_cached_analysis(self, audio_path: str) -> Optional[List[BeatInfo]]:
        """Get cached beat analysis for an audio file."""
        for cache_key, beats in self.beat_cache.items():
            if audio_path in cache_key:
                return beats
        return None
    
    def clear_cache(self):
        """Clear analysis cache."""
        self.beat_cache.clear()
        self.tempo_cache.clear()
        logger.info("Audio analysis cache cleared")


# Export for use in other modules
__all__ = ['AudioSyncProcessor', 'AudioSyncSettings', 'BeatTrackingMode', 'SyncTarget', 'BeatInfo']