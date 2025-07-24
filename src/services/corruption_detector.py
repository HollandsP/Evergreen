"""
File Corruption Detector with Integrity Verification

Provides comprehensive file integrity checking with:
- Multiple checksum algorithms (MD5, SHA256, CRC32)
- Video/audio format validation
- Automatic corruption recovery
- Quarantine management
- Real-time monitoring
"""

import hashlib
import os
import json
import shutil
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import mimetypes
import struct

import aiofiles
import structlog
from moviepy.editor import VideoFileClip, AudioFileClip
import numpy as np
from PIL import Image
import magic

logger = structlog.get_logger()


class FileType(Enum):
    """Supported file types for corruption detection."""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    DATA = "data"
    UNKNOWN = "unknown"


class IntegrityStatus(Enum):
    """File integrity status levels."""
    VALID = "valid"
    CORRUPTED = "corrupted"
    PARTIALLY_CORRUPTED = "partially_corrupted"
    RECOVERABLE = "recoverable"
    UNRECOVERABLE = "unrecoverable"
    QUARANTINED = "quarantined"


@dataclass
class FileIntegrityInfo:
    """Comprehensive file integrity information."""
    file_path: str
    file_type: FileType
    file_size: int
    status: IntegrityStatus
    
    # Checksums
    md5_hash: str
    sha256_hash: str
    crc32: Optional[int] = None
    
    # Validation results
    format_valid: bool = True
    header_valid: bool = True
    content_valid: bool = True
    
    # Media-specific
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    
    # Corruption details
    corruption_type: Optional[str] = None
    corruption_location: Optional[int] = None
    corruption_severity: float = 0.0  # 0-1 scale
    
    # Recovery info
    recovery_possible: bool = False
    recovery_method: Optional[str] = None
    backup_available: bool = False
    
    # Metadata
    last_checked: datetime = None
    check_duration: float = 0.0
    error_details: Optional[str] = None


class CorruptionDetector:
    """
    Advanced file corruption detection and recovery system.
    
    Features:
    - Multi-algorithm integrity checking
    - Format-specific validation
    - Automatic backup management
    - Corruption pattern detection
    - Recovery suggestions
    """
    
    def __init__(self,
                 quarantine_dir: str = "./quarantine",
                 backup_dir: str = "./backups",
                 enable_auto_backup: bool = True,
                 max_backup_size_gb: float = 10.0):
        """
        Initialize corruption detector.
        
        Args:
            quarantine_dir: Directory for corrupted files
            backup_dir: Directory for file backups
            enable_auto_backup: Auto-backup critical files
            max_backup_size_gb: Maximum backup storage size
        """
        self.quarantine_dir = Path(quarantine_dir)
        self.backup_dir = Path(backup_dir)
        self.enable_auto_backup = enable_auto_backup
        self.max_backup_size_bytes = max_backup_size_gb * 1024 * 1024 * 1024
        
        # Create directories
        self.quarantine_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Integrity database
        self.integrity_db: Dict[str, FileIntegrityInfo] = {}
        self.corruption_patterns: Dict[str, List[str]] = {
            'video': ['moov atom', 'codec', 'frame corruption', 'timeline'],
            'audio': ['header', 'sample rate', 'channel corruption'],
            'image': ['header', 'pixel data', 'color profile']
        }
        
        # File type magic
        self.file_magic = magic.Magic(mime=True)
        
        logger.info(
            "Corruption detector initialized",
            quarantine_dir=str(self.quarantine_dir),
            backup_dir=str(self.backup_dir),
            auto_backup=enable_auto_backup
        )
    
    async def check_file_integrity(self, 
                                  file_path: Union[str, Path],
                                  deep_scan: bool = False,
                                  create_backup: bool = None) -> FileIntegrityInfo:
        """
        Check file integrity with multiple validation methods.
        
        Args:
            file_path: Path to file to check
            deep_scan: Perform deep content analysis
            create_backup: Override auto-backup setting
            
        Returns:
            FileIntegrityInfo with validation results
        """
        file_path = Path(file_path)
        start_time = asyncio.get_event_loop().time()
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(
            "Starting integrity check",
            file=str(file_path),
            deep_scan=deep_scan
        )
        
        # Determine file type
        file_type = self._determine_file_type(file_path)
        
        # Calculate checksums
        checksums = await self._calculate_checksums(file_path)
        
        # Create integrity info
        integrity_info = FileIntegrityInfo(
            file_path=str(file_path),
            file_type=file_type,
            file_size=file_path.stat().st_size,
            status=IntegrityStatus.VALID,
            md5_hash=checksums['md5'],
            sha256_hash=checksums['sha256'],
            crc32=checksums.get('crc32'),
            last_checked=datetime.now()
        )
        
        # Validate file format
        try:
            if file_type == FileType.VIDEO:
                await self._validate_video(file_path, integrity_info, deep_scan)
            elif file_type == FileType.AUDIO:
                await self._validate_audio(file_path, integrity_info, deep_scan)
            elif file_type == FileType.IMAGE:
                await self._validate_image(file_path, integrity_info, deep_scan)
            else:
                await self._validate_generic(file_path, integrity_info)
        except Exception as e:
            integrity_info.status = IntegrityStatus.CORRUPTED
            integrity_info.error_details = str(e)
            logger.error(
                "File validation failed",
                file=str(file_path),
                error=str(e)
            )
        
        # Determine final status
        integrity_info.status = self._determine_status(integrity_info)
        
        # Handle corruption
        if integrity_info.status in [IntegrityStatus.CORRUPTED, IntegrityStatus.PARTIALLY_CORRUPTED]:
            await self._handle_corruption(file_path, integrity_info)
        
        # Create backup if needed
        if create_backup or (create_backup is None and self.enable_auto_backup):
            if integrity_info.status == IntegrityStatus.VALID:
                integrity_info.backup_available = await self._create_backup(file_path)
        
        # Update check duration
        integrity_info.check_duration = asyncio.get_event_loop().time() - start_time
        
        # Store in database
        self.integrity_db[str(file_path)] = integrity_info
        
        logger.info(
            "Integrity check completed",
            file=str(file_path),
            status=integrity_info.status.value,
            duration=integrity_info.check_duration
        )
        
        return integrity_info
    
    async def _calculate_checksums(self, file_path: Path) -> Dict[str, str]:
        """Calculate multiple checksums for file."""
        checksums = {
            'md5': hashlib.md5(),
            'sha256': hashlib.sha256(),
            'crc32': 0
        }
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                checksums['md5'].update(chunk)
                checksums['sha256'].update(chunk)
                checksums['crc32'] = self._crc32(chunk, checksums['crc32'])
        
        return {
            'md5': checksums['md5'].hexdigest(),
            'sha256': checksums['sha256'].hexdigest(),
            'crc32': checksums['crc32']
        }
    
    def _crc32(self, data: bytes, crc: int = 0) -> int:
        """Calculate CRC32 checksum."""
        import zlib
        return zlib.crc32(data, crc) & 0xffffffff
    
    def _determine_file_type(self, file_path: Path) -> FileType:
        """Determine file type using magic and extension."""
        mime_type = self.file_magic.from_file(str(file_path))
        extension = file_path.suffix.lower()
        
        if mime_type.startswith('video/') or extension in ['.mp4', '.avi', '.mov', '.mkv']:
            return FileType.VIDEO
        elif mime_type.startswith('audio/') or extension in ['.mp3', '.wav', '.flac', '.aac']:
            return FileType.AUDIO
        elif mime_type.startswith('image/') or extension in ['.jpg', '.png', '.gif', '.bmp']:
            return FileType.IMAGE
        elif mime_type.startswith('text/') or extension in ['.txt', '.md', '.json', '.xml']:
            return FileType.DOCUMENT
        elif extension in ['.dat', '.bin', '.db']:
            return FileType.DATA
        else:
            return FileType.UNKNOWN
    
    async def _validate_video(self, file_path: Path, info: FileIntegrityInfo, deep_scan: bool):
        """Validate video file integrity."""
        try:
            # Quick validation with moviepy
            clip = VideoFileClip(str(file_path))
            
            # Basic metadata
            info.duration = clip.duration
            info.resolution = (clip.w, clip.h)
            info.codec = 'unknown'  # MoviePy doesn't expose codec easily
            
            # Header validation
            info.header_valid = clip.duration > 0 and clip.fps > 0
            
            if deep_scan:
                # Check a few frames
                frame_count = min(10, int(clip.fps * clip.duration))
                frame_step = max(1, int(clip.duration / frame_count))
                
                corrupted_frames = 0
                for i in range(0, int(clip.duration), frame_step):
                    try:
                        frame = clip.get_frame(i)
                        if frame is None or np.all(frame == 0):
                            corrupted_frames += 1
                    except Exception:
                        corrupted_frames += 1
                
                info.content_valid = corrupted_frames < frame_count * 0.1  # Allow 10% corruption
                
                if corrupted_frames > 0:
                    info.corruption_type = "frame corruption"
                    info.corruption_severity = corrupted_frames / frame_count
            
            clip.close()
            
        except Exception as e:
            info.format_valid = False
            info.error_details = f"Video validation error: {str(e)}"
            
            # Try to determine corruption type
            error_msg = str(e).lower()
            if 'codec' in error_msg:
                info.corruption_type = "codec error"
            elif 'header' in error_msg:
                info.corruption_type = "header corruption"
            else:
                info.corruption_type = "unknown video corruption"
    
    async def _validate_audio(self, file_path: Path, info: FileIntegrityInfo, deep_scan: bool):
        """Validate audio file integrity."""
        try:
            # Quick validation with moviepy
            clip = AudioFileClip(str(file_path))
            
            # Basic metadata
            info.duration = clip.duration
            info.bitrate = int(clip.fps * 16)  # Approximate
            
            # Header validation
            info.header_valid = clip.duration > 0 and clip.fps > 0
            
            if deep_scan:
                # Sample audio at intervals
                sample_count = min(10, int(clip.duration))
                corrupted_samples = 0
                
                for i in range(sample_count):
                    try:
                        t = i * clip.duration / sample_count
                        audio_frame = clip.get_frame(t)
                        if audio_frame is None or np.all(audio_frame == 0):
                            corrupted_samples += 1
                    except Exception:
                        corrupted_samples += 1
                
                info.content_valid = corrupted_samples < sample_count * 0.1
                
                if corrupted_samples > 0:
                    info.corruption_type = "audio sample corruption"
                    info.corruption_severity = corrupted_samples / sample_count
            
            clip.close()
            
        except Exception as e:
            info.format_valid = False
            info.error_details = f"Audio validation error: {str(e)}"
            info.corruption_type = "audio format error"
    
    async def _validate_image(self, file_path: Path, info: FileIntegrityInfo, deep_scan: bool):
        """Validate image file integrity."""
        try:
            # Open with PIL
            with Image.open(file_path) as img:
                info.resolution = img.size
                info.format_valid = True
                
                # Verify image can be loaded
                img.verify()
                
                if deep_scan:
                    # Re-open for pixel access (verify closes the file)
                    with Image.open(file_path) as img2:
                        # Try to load pixel data
                        try:
                            pixels = img2.load()
                            # Check a few pixels
                            for x in range(0, img2.width, max(1, img2.width // 10)):
                                for y in range(0, img2.height, max(1, img2.height // 10)):
                                    _ = pixels[x, y]
                            info.content_valid = True
                        except Exception:
                            info.content_valid = False
                            info.corruption_type = "pixel data corruption"
                            info.corruption_severity = 0.5
        
        except Exception as e:
            info.format_valid = False
            info.error_details = f"Image validation error: {str(e)}"
            
            if 'truncated' in str(e).lower():
                info.corruption_type = "truncated image"
            else:
                info.corruption_type = "image format error"
    
    async def _validate_generic(self, file_path: Path, info: FileIntegrityInfo):
        """Generic file validation."""
        try:
            # Check if file is readable
            async with aiofiles.open(file_path, 'rb') as f:
                # Read first and last chunks
                await f.read(1024)
                await f.seek(-1024, 2)  # Seek to end
                await f.read(1024)
            
            info.format_valid = True
            info.content_valid = True
            
        except Exception as e:
            info.format_valid = False
            info.error_details = f"File read error: {str(e)}"
    
    def _determine_status(self, info: FileIntegrityInfo) -> IntegrityStatus:
        """Determine overall file status based on validation results."""
        if not info.format_valid:
            return IntegrityStatus.CORRUPTED
        
        if not info.header_valid:
            return IntegrityStatus.PARTIALLY_CORRUPTED
        
        if not info.content_valid:
            if info.corruption_severity < 0.3:
                return IntegrityStatus.RECOVERABLE
            else:
                return IntegrityStatus.PARTIALLY_CORRUPTED
        
        return IntegrityStatus.VALID
    
    async def _handle_corruption(self, file_path: Path, info: FileIntegrityInfo):
        """Handle corrupted file based on severity."""
        logger.warning(
            "Corruption detected",
            file=str(file_path),
            type=info.corruption_type,
            severity=info.corruption_severity
        )
        
        # Determine recovery options
        if info.file_type == FileType.VIDEO:
            if info.corruption_type == "codec error":
                info.recovery_method = "Re-encode with different codec"
                info.recovery_possible = True
            elif info.corruption_type == "frame corruption":
                info.recovery_method = "Extract valid frames and reconstruct"
                info.recovery_possible = info.corruption_severity < 0.5
            elif info.corruption_type == "header corruption":
                info.recovery_method = "Repair video header with specialized tools"
                info.recovery_possible = True
        
        elif info.file_type == FileType.AUDIO:
            if info.corruption_type == "audio sample corruption":
                info.recovery_method = "Interpolate missing samples"
                info.recovery_possible = info.corruption_severity < 0.3
            else:
                info.recovery_method = "Convert to different format"
                info.recovery_possible = True
        
        elif info.file_type == FileType.IMAGE:
            if info.corruption_type == "truncated image":
                info.recovery_method = "Recover partial image data"
                info.recovery_possible = True
            elif info.corruption_type == "pixel data corruption":
                info.recovery_method = "Use image repair algorithms"
                info.recovery_possible = info.corruption_severity < 0.5
        
        # Check for backup
        backup_path = self.backup_dir / f"{file_path.stem}_backup{file_path.suffix}"
        if backup_path.exists():
            info.backup_available = True
            info.recovery_method = f"Restore from backup: {backup_path}"
            info.recovery_possible = True
    
    async def _create_backup(self, file_path: Path) -> bool:
        """Create backup of valid file."""
        try:
            # Check backup size limit
            current_backup_size = sum(
                f.stat().st_size for f in self.backup_dir.iterdir() if f.is_file()
            )
            
            if current_backup_size + file_path.stat().st_size > self.max_backup_size_bytes:
                logger.warning(
                    "Backup size limit exceeded",
                    current_size=current_backup_size,
                    file_size=file_path.stat().st_size
                )
                return False
            
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Copy file
            shutil.copy2(file_path, backup_path)
            
            logger.info(
                "Backup created",
                original=str(file_path),
                backup=str(backup_path)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Backup creation failed",
                file=str(file_path),
                error=str(e)
            )
            return False
    
    async def quarantine_file(self, file_path: Union[str, Path], reason: str = "Corruption detected"):
        """Move corrupted file to quarantine."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return
        
        # Generate quarantine name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quarantine_name = f"{file_path.stem}_{timestamp}_CORRUPTED{file_path.suffix}"
        quarantine_path = self.quarantine_dir / quarantine_name
        
        # Create quarantine info
        info_path = quarantine_path.with_suffix('.json')
        quarantine_info = {
            'original_path': str(file_path),
            'quarantine_time': datetime.now().isoformat(),
            'reason': reason,
            'file_info': asdict(self.integrity_db.get(str(file_path), {}))
        }
        
        try:
            # Move file
            shutil.move(str(file_path), str(quarantine_path))
            
            # Save info
            with open(info_path, 'w') as f:
                json.dump(quarantine_info, f, indent=2)
            
            logger.warning(
                "File quarantined",
                original=str(file_path),
                quarantine=str(quarantine_path),
                reason=reason
            )
            
            # Update integrity info
            if str(file_path) in self.integrity_db:
                self.integrity_db[str(file_path)].status = IntegrityStatus.QUARANTINED
            
        except Exception as e:
            logger.error(
                "Quarantine failed",
                file=str(file_path),
                error=str(e)
            )
    
    async def recover_file(self, 
                          file_path: Union[str, Path],
                          output_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
        """Attempt to recover corrupted file."""
        file_path = Path(file_path)
        
        # Get integrity info
        if str(file_path) not in self.integrity_db:
            info = await self.check_file_integrity(file_path)
        else:
            info = self.integrity_db[str(file_path)]
        
        if not info.recovery_possible:
            logger.error(
                "Recovery not possible",
                file=str(file_path),
                reason=info.error_details
            )
            return None
        
        output_path = Path(output_path) if output_path else file_path.with_suffix('.recovered' + file_path.suffix)
        
        logger.info(
            "Attempting file recovery",
            file=str(file_path),
            method=info.recovery_method
        )
        
        try:
            # Check for backup first
            if info.backup_available:
                backup_files = list(self.backup_dir.glob(f"{file_path.stem}_*{file_path.suffix}"))
                if backup_files:
                    # Use most recent backup
                    latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                    shutil.copy2(latest_backup, output_path)
                    logger.info(
                        "File recovered from backup",
                        backup=str(latest_backup),
                        output=str(output_path)
                    )
                    return output_path
            
            # Type-specific recovery
            if info.file_type == FileType.VIDEO:
                return await self._recover_video(file_path, output_path, info)
            elif info.file_type == FileType.AUDIO:
                return await self._recover_audio(file_path, output_path, info)
            elif info.file_type == FileType.IMAGE:
                return await self._recover_image(file_path, output_path, info)
            else:
                # Generic recovery - copy what we can
                shutil.copy2(file_path, output_path)
                return output_path
                
        except Exception as e:
            logger.error(
                "Recovery failed",
                file=str(file_path),
                error=str(e)
            )
            return None
    
    async def _recover_video(self, input_path: Path, output_path: Path, info: FileIntegrityInfo) -> Optional[Path]:
        """Attempt video recovery."""
        try:
            # Try re-encoding
            clip = VideoFileClip(str(input_path))
            clip.write_videofile(str(output_path), codec='libx264', audio_codec='aac')
            clip.close()
            return output_path
        except Exception as e:
            logger.error("Video recovery failed", error=str(e))
            return None
    
    async def _recover_audio(self, input_path: Path, output_path: Path, info: FileIntegrityInfo) -> Optional[Path]:
        """Attempt audio recovery."""
        try:
            # Try re-encoding
            clip = AudioFileClip(str(input_path))
            clip.write_audiofile(str(output_path))
            clip.close()
            return output_path
        except Exception as e:
            logger.error("Audio recovery failed", error=str(e))
            return None
    
    async def _recover_image(self, input_path: Path, output_path: Path, info: FileIntegrityInfo) -> Optional[Path]:
        """Attempt image recovery."""
        try:
            # Try to save in different format
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ['RGB', 'RGBA']:
                    img = img.convert('RGB')
                img.save(output_path, 'PNG')
            return output_path
        except Exception as e:
            logger.error("Image recovery failed", error=str(e))
            return None
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """Generate integrity report for all checked files."""
        total_files = len(self.integrity_db)
        
        status_counts = {status: 0 for status in IntegrityStatus}
        type_counts = {file_type: 0 for file_type in FileType}
        
        corrupted_files = []
        recoverable_files = []
        
        for file_path, info in self.integrity_db.items():
            status_counts[info.status] += 1
            type_counts[info.file_type] += 1
            
            if info.status in [IntegrityStatus.CORRUPTED, IntegrityStatus.PARTIALLY_CORRUPTED]:
                corrupted_files.append({
                    'path': file_path,
                    'type': info.corruption_type,
                    'severity': info.corruption_severity,
                    'recoverable': info.recovery_possible
                })
            
            if info.recovery_possible:
                recoverable_files.append(file_path)
        
        return {
            'total_files_checked': total_files,
            'status_distribution': {s.value: c for s, c in status_counts.items()},
            'type_distribution': {t.value: c for t, c in type_counts.items()},
            'corruption_rate': (status_counts[IntegrityStatus.CORRUPTED] + 
                               status_counts[IntegrityStatus.PARTIALLY_CORRUPTED]) / max(1, total_files),
            'corrupted_files': corrupted_files,
            'recoverable_files': recoverable_files,
            'backup_count': len(list(self.backup_dir.iterdir())),
            'quarantine_count': len(list(self.quarantine_dir.iterdir()))
        }
    
    async def monitor_directory(self, 
                               directory: Union[str, Path],
                               interval: int = 3600,
                               recursive: bool = True):
        """Monitor directory for file corruption."""
        directory = Path(directory)
        
        logger.info(
            "Starting directory monitoring",
            directory=str(directory),
            interval=interval,
            recursive=recursive
        )
        
        while True:
            try:
                # Get all files
                if recursive:
                    files = [f for f in directory.rglob('*') if f.is_file()]
                else:
                    files = [f for f in directory.iterdir() if f.is_file()]
                
                # Check each file
                for file_path in files:
                    try:
                        await self.check_file_integrity(file_path)
                    except Exception as e:
                        logger.error(
                            "Failed to check file",
                            file=str(file_path),
                            error=str(e)
                        )
                
                # Generate report
                report = self.get_integrity_report()
                logger.info(
                    "Monitoring cycle completed",
                    files_checked=len(files),
                    corruption_rate=report['corruption_rate']
                )
                
            except Exception as e:
                logger.error(
                    "Monitoring error",
                    error=str(e)
                )
            
            # Wait for next cycle
            await asyncio.sleep(interval)


# Global instance
corruption_detector = CorruptionDetector()