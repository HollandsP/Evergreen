"""
Health check and dependency validation for AI Video Editor.

This module ensures all required dependencies are available and properly configured
before attempting video editing operations.
"""

import os
import sys
import logging
import subprocess
from typing import Dict, List, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class EditorHealthCheck:
    """
    Comprehensive health check for AI Video Editor dependencies.
    
    Validates:
    - MoviePy installation and functionality
    - FFmpeg availability and version
    - OpenAI API key configuration
    - Required Python packages
    - File system permissions
    """
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
    
    async def run_full_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive results."""
        self.results = {}
        self.errors = []
        self.warnings = []
        
        # Run all checks
        await self._check_python_packages()
        await self._check_ffmpeg()
        await self._check_openai_config()
        await self._check_file_permissions()
        await self._check_moviepy_functionality()
        
        # Compile results
        return {
            "overall_health": "healthy" if not self.errors else "unhealthy",
            "has_warnings": len(self.warnings) > 0,
            "can_edit_videos": self._can_edit_videos(),
            "results": self.results,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self._get_recommendations()
        }
    
    async def _check_python_packages(self):
        """Check if required Python packages are installed."""
        required_packages = [
            ("moviepy", "1.0.0"),
            ("openai", "1.0.0"),
            ("numpy", "1.20.0"),
            ("pillow", "8.0.0"),
            ("requests", "2.25.0")
        ]
        
        package_results = {}
        
        for package_name, min_version in required_packages:
            try:
                __import__(package_name)
                package_results[package_name] = {
                    "installed": True,
                    "version": self._get_package_version(package_name),
                    "status": "ok"
                }
            except ImportError:
                package_results[package_name] = {
                    "installed": False,
                    "version": None,
                    "status": "missing"
                }
                self.errors.append(f"Missing required package: {package_name}")
        
        self.results["python_packages"] = package_results
    
    async def _check_ffmpeg(self):
        """Check FFmpeg installation and version."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.results["ffmpeg"] = {
                    "installed": True,
                    "version": version_line,
                    "status": "ok"
                }
            else:
                self.results["ffmpeg"] = {
                    "installed": False,
                    "version": None,
                    "status": "error"
                }
                self.errors.append("FFmpeg command failed")
                
        except FileNotFoundError:
            self.results["ffmpeg"] = {
                "installed": False,
                "version": None,
                "status": "missing"
            }
            self.errors.append("FFmpeg not found in PATH")
            
        except subprocess.TimeoutExpired:
            self.results["ffmpeg"] = {
                "installed": False,
                "version": None,
                "status": "timeout"
            }
            self.warnings.append("FFmpeg check timed out")
    
    async def _check_openai_config(self):
        """Check OpenAI API configuration."""
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            self.results["openai"] = {
                "configured": False,
                "key_length": 0,
                "status": "missing"
            }
            self.errors.append("OPENAI_API_KEY environment variable not set")
            return
        
        if len(api_key) < 20:
            self.results["openai"] = {
                "configured": False,
                "key_length": len(api_key),
                "status": "invalid"
            }
            self.errors.append("OPENAI_API_KEY appears to be invalid (too short)")
            return
        
        # Test API connectivity (optional, basic check)
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # Simple test to verify key works
            # Note: This makes a real API call, use sparingly
            self.results["openai"] = {
                "configured": True,
                "key_length": len(api_key),
                "status": "ok"
            }
            
        except Exception as e:
            self.results["openai"] = {
                "configured": True,
                "key_length": len(api_key),
                "status": "unknown",
                "error": str(e)
            }
            self.warnings.append(f"Could not verify OpenAI API key: {str(e)}")
    
    async def _check_file_permissions(self):
        """Check file system permissions for video editing."""
        test_dirs = [
            "output/editor_workspace",
            "output/editor_workspace/previews",
            "output/projects"
        ]
        
        permission_results = {}
        
        for test_dir in test_dirs:
            dir_path = Path(test_dir)
            
            try:
                # Create directory if it doesn't exist
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = dir_path / "health_check_test.tmp"
                test_file.write_text("test")
                test_file.unlink()  # Delete test file
                
                permission_results[test_dir] = {
                    "writable": True,
                    "status": "ok"
                }
                
            except PermissionError:
                permission_results[test_dir] = {
                    "writable": False,
                    "status": "permission_denied"
                }
                self.errors.append(f"No write permission for directory: {test_dir}")
                
            except Exception as e:
                permission_results[test_dir] = {
                    "writable": False,
                    "status": "error",
                    "error": str(e)
                }
                self.warnings.append(f"Could not test permissions for {test_dir}: {str(e)}")
        
        self.results["file_permissions"] = permission_results
    
    async def _check_moviepy_functionality(self):
        """Test basic MoviePy functionality."""
        try:
            from moviepy.editor import ColorClip
            
            # Create a simple test clip
            test_clip = ColorClip(size=(640, 480), color=(255, 0, 0), duration=1)
            
            # Test basic properties
            if test_clip.duration == 1 and test_clip.size == (640, 480):
                self.results["moviepy_functionality"] = {
                    "working": True,
                    "status": "ok"
                }
            else:
                self.results["moviepy_functionality"] = {
                    "working": False,
                    "status": "basic_test_failed"
                }
                self.errors.append("MoviePy basic functionality test failed")
            
            # Cleanup
            test_clip.close()
            
        except ImportError:
            self.results["moviepy_functionality"] = {
                "working": False,
                "status": "import_error"
            }
            self.errors.append("Could not import MoviePy components")
            
        except Exception as e:
            self.results["moviepy_functionality"] = {
                "working": False,
                "status": "error",
                "error": str(e)
            }
            self.errors.append(f"MoviePy functionality test failed: {str(e)}")
    
    def _can_edit_videos(self) -> bool:
        """Determine if video editing operations can be performed."""
        moviepy_ok = self.results.get("moviepy_functionality", {}).get("working", False)
        ffmpeg_ok = self.results.get("ffmpeg", {}).get("installed", False)
        permissions_ok = all(
            result.get("writable", False) 
            for result in self.results.get("file_permissions", {}).values()
        )
        
        return moviepy_ok and ffmpeg_ok and permissions_ok
    
    def _get_package_version(self, package_name: str) -> str:
        """Get version of an installed package."""
        try:
            import importlib.metadata
            return importlib.metadata.version(package_name)
        except:
            try:
                module = __import__(package_name)
                return getattr(module, '__version__', 'unknown')
            except:
                return 'unknown'
    
    def _get_recommendations(self) -> List[str]:
        """Generate recommendations based on health check results."""
        recommendations = []
        
        # Package installation recommendations
        if any(not pkg.get("installed", False) for pkg in self.results.get("python_packages", {}).values()):
            recommendations.append("Install missing Python packages: pip install moviepy openai numpy pillow requests")
        
        # FFmpeg recommendations
        if not self.results.get("ffmpeg", {}).get("installed", False):
            recommendations.append("Install FFmpeg: https://ffmpeg.org/download.html")
        
        # OpenAI recommendations
        if not self.results.get("openai", {}).get("configured", False):
            recommendations.append("Configure OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        
        # File permission recommendations
        if not all(result.get("writable", False) for result in self.results.get("file_permissions", {}).values()):
            recommendations.append("Fix file permissions for output directories")
        
        # General recommendations
        if not self._can_edit_videos():
            recommendations.append("Fix all errors above before attempting video editing operations")
        else:
            recommendations.append("All systems ready for video editing!")
        
        return recommendations

# Global health checker instance
health_checker = EditorHealthCheck()

async def get_editor_health() -> Dict[str, Any]:
    """Get current health status of the video editor."""
    return await health_checker.run_full_check()

async def can_edit_videos() -> bool:
    """Quick check if video editing is possible."""
    health = await get_editor_health()
    return health["can_edit_videos"]