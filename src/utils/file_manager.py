"""
File Manager Utility

Handles file operations with proper path management, cleanup, and error handling.
"""

import os
import shutil
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import structlog

logger = structlog.get_logger()


class FileManager:
    """Utility for managing file operations with cleanup and error handling."""
    
    def __init__(self, base_output_dir: str = "/app/output"):
        """
        Initialize file manager.
        
        Args:
            base_output_dir: Base directory for output files
        """
        self.base_output_dir = Path(base_output_dir)
        
        # Create output directories
        self.audio_dir = self.base_output_dir / "audio"
        self.video_dir = self.base_output_dir / "visuals"
        self.ui_dir = self.base_output_dir / "ui"
        self.export_dir = self.base_output_dir / "exports"
        
        # Ensure directories exist
        self._create_directories()
        
        logger.info(
            "File manager initialized",
            base_output_dir=str(self.base_output_dir),
            directories_created=4
        )
    
    def _create_directories(self):
        """Create all required directories."""
        directories = [
            self.audio_dir,
            self.video_dir,
            self.ui_dir,
            self.export_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
    
    async def save_audio_file(self, filename: str, audio_data: bytes) -> str:
        """
        Save audio file to audio directory.
        
        Args:
            filename: Name of audio file
            audio_data: Audio data bytes
            
        Returns:
            Path to saved file
        """
        file_path = self.audio_dir / filename
        
        try:
            # Ensure filename is safe
            safe_filename = self._sanitize_filename(filename)
            file_path = self.audio_dir / safe_filename
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            logger.debug(
                "Audio file saved",
                filename=safe_filename,
                size_bytes=len(audio_data),
                path=str(file_path)
            )
            
            return str(file_path)
            
        except Exception as e:
            logger.error(
                "Failed to save audio file",
                filename=filename,
                error=str(e)
            )
            raise
    
    async def save_video_file(self, filename: str, video_data: bytes) -> str:
        """
        Save video file to video directory.
        
        Args:
            filename: Name of video file
            video_data: Video data bytes
            
        Returns:
            Path to saved file
        """
        try:
            # Ensure filename is safe
            safe_filename = self._sanitize_filename(filename)
            file_path = self.video_dir / safe_filename
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(video_data)
            
            logger.debug(
                "Video file saved",
                filename=safe_filename,
                size_bytes=len(video_data),
                path=str(file_path)
            )
            
            return str(file_path)
            
        except Exception as e:
            logger.error(
                "Failed to save video file",
                filename=filename,
                error=str(e)
            )
            raise
    
    async def save_video_file_from_temp(self, filename: str, temp_path: str) -> str:
        """
        Move video file from temporary location to video directory.
        
        Args:
            filename: Name for final file
            temp_path: Temporary file path
            
        Returns:
            Path to final file
        """
        try:
            safe_filename = self._sanitize_filename(filename)
            final_path = self.video_dir / safe_filename
            
            # Move file
            shutil.move(temp_path, final_path)
            
            logger.debug(
                "Video file moved from temp",
                filename=safe_filename,
                temp_path=temp_path,
                final_path=str(final_path)
            )
            
            return str(final_path)
            
        except Exception as e:
            logger.error(
                "Failed to move video file from temp",
                filename=filename,
                temp_path=temp_path,
                error=str(e)
            )
            raise
    
    async def save_ui_file(self, filename: str, ui_data: bytes) -> str:
        """
        Save UI animation file to UI directory.
        
        Args:
            filename: Name of UI file
            ui_data: UI animation data bytes
            
        Returns:
            Path to saved file
        """
        try:
            safe_filename = self._sanitize_filename(filename)
            file_path = self.ui_dir / safe_filename
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(ui_data)
            
            logger.debug(
                "UI file saved",
                filename=safe_filename,
                size_bytes=len(ui_data),
                path=str(file_path)
            )
            
            return str(file_path)
            
        except Exception as e:
            logger.error(
                "Failed to save UI file",
                filename=filename,
                error=str(e)
            )
            raise
    
    async def get_output_path(self, filename: str) -> str:
        """
        Get path for final output file.
        
        Args:
            filename: Name of output file
            
        Returns:
            Path for output file
        """
        safe_filename = self._sanitize_filename(filename)
        file_path = self.export_dir / safe_filename
        return str(file_path)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe filesystem use.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # Remove consecutive underscores and leading/trailing underscores
        while '__' in safe_filename:
            safe_filename = safe_filename.replace('__', '_')
        
        safe_filename = safe_filename.strip('_')
        
        # Ensure filename is not too long
        if len(safe_filename) > 200:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:200-len(ext)] + ext
        
        return safe_filename or 'unnamed_file'
    
    async def cleanup_temp_files(self, file_patterns: List[str]) -> int:
        """
        Clean up temporary files matching patterns.
        
        Args:
            file_patterns: List of file patterns to clean up
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        
        for pattern in file_patterns:
            try:
                for file_path in Path("/tmp").glob(pattern):
                    if file_path.is_file():
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug("Cleaned up temp file", file_path=str(file_path))
            except Exception as e:
                logger.warning(
                    "Failed to cleanup temp files",
                    pattern=pattern,
                    error=str(e)
                )
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} temporary files")
        
        return cleaned_count
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            File information or None if file doesn't exist
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return None
            
            stat = path.stat()
            
            return {
                'path': str(path),
                'name': path.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': stat.st_mtime,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'exists': True
            }
            
        except Exception as e:
            logger.warning(
                "Failed to get file info",
                file_path=file_path,
                error=str(e)
            )
            return None
    
    async def list_files_in_directory(self, directory: str, 
                                    pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List files in a directory.
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            
        Returns:
            List of file information dicts
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists() or not dir_path.is_dir():
                return []
            
            files = []
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    file_info = await self.get_file_info(str(file_path))
                    if file_info:
                        files.append(file_info)
            
            # Sort by modification time (newest first)
            files.sort(key=lambda f: f['modified_time'], reverse=True)
            
            return files
            
        except Exception as e:
            logger.warning(
                "Failed to list files",
                directory=directory,
                pattern=pattern,
                error=str(e)
            )
            return []
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file safely.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if file was deleted successfully
        """
        try:
            path = Path(file_path)
            
            if path.exists() and path.is_file():
                path.unlink()
                logger.debug("File deleted", file_path=file_path)
                return True
            else:
                logger.warning("File not found for deletion", file_path=file_path)
                return False
                
        except Exception as e:
            logger.error(
                "Failed to delete file",
                file_path=file_path,
                error=str(e)
            )
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            stats = {}
            
            for name, directory in [
                ("audio", self.audio_dir),
                ("video", self.video_dir),
                ("ui", self.ui_dir),
                ("exports", self.export_dir)
            ]:
                if directory.exists():
                    total_size = sum(
                        f.stat().st_size for f in directory.rglob('*') if f.is_file()
                    )
                    file_count = len([f for f in directory.rglob('*') if f.is_file()])
                    
                    stats[name] = {
                        'total_size_bytes': total_size,
                        'total_size_mb': round(total_size / (1024 * 1024), 2),
                        'file_count': file_count,
                        'directory': str(directory)
                    }
                else:
                    stats[name] = {
                        'total_size_bytes': 0,
                        'total_size_mb': 0,
                        'file_count': 0,
                        'directory': str(directory)
                    }
            
            # Calculate totals
            total_size = sum(s['total_size_bytes'] for s in stats.values())
            total_files = sum(s['file_count'] for s in stats.values())
            
            stats['totals'] = {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_files': total_files
            }
            
            return stats
            
        except Exception as e:
            logger.warning("Failed to get storage stats", error=str(e))
            return {
                'error': str(e),
                'totals': {
                    'total_size_bytes': 0,
                    'total_size_mb': 0,
                    'total_files': 0
                }
            }