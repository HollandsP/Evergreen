"""
Asset Management System for images, textures, and effects.
Handles loading, caching, and organization of visual assets.
"""

import os
import json
import hashlib
import shutil
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from PIL import Image, ImageOps
import numpy as np
import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Types of assets managed by the system."""
    IMAGE = "image"
    TEXTURE = "texture"
    FONT = "font"
    VIDEO = "video"
    AUDIO = "audio"
    EFFECT = "effect"
    SHADER = "shader"
    MODEL_3D = "model_3d"
    ANIMATION = "animation"
    PRESET = "preset"


class AssetCategory(Enum):
    """Categories for organizing assets."""
    BACKGROUND = "background"
    FOREGROUND = "foreground"
    UI = "ui"
    PARTICLE = "particle"
    ENVIRONMENT = "environment"
    CHARACTER = "character"
    PROP = "prop"
    OVERLAY = "overlay"
    TRANSITION = "transition"
    FILTER = "filter"


@dataclass
class AssetMetadata:
    """Metadata for an asset."""
    id: str
    name: str
    type: AssetType
    category: AssetCategory
    path: str
    size: int
    format: str
    dimensions: Optional[Tuple[int, int]] = None
    duration: Optional[float] = None
    tags: List[str] = None
    created_at: str = None
    modified_at: str = None
    checksum: str = None
    thumbnail_path: Optional[str] = None
    properties: Dict[str, Any] = None


@dataclass
class AssetPackage:
    """Collection of related assets."""
    id: str
    name: str
    description: str
    version: str
    assets: List[str]  # Asset IDs
    dependencies: List[str] = None
    created_at: str = None
    author: str = None
    license: str = None


class AssetManager:
    """Manages visual assets with caching and organization."""
    
    def __init__(self, assets_dir: str = None):
        self.assets_dir = Path(assets_dir or os.environ.get('ASSETS_DIR', './assets'))
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Directory structure
        self.dirs = {
            'images': self.assets_dir / 'images',
            'textures': self.assets_dir / 'textures',
            'fonts': self.assets_dir / 'fonts',
            'videos': self.assets_dir / 'videos',
            'audio': self.assets_dir / 'audio',
            'effects': self.assets_dir / 'effects',
            'cache': self.assets_dir / '.cache',
            'thumbnails': self.assets_dir / '.thumbnails',
            'metadata': self.assets_dir / '.metadata'
        }
        
        # Create directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Asset registry
        self.registry: Dict[str, AssetMetadata] = {}
        self.packages: Dict[str, AssetPackage] = {}
        
        # Cache
        self.cache: Dict[str, Any] = {}
        self.cache_size_limit = 500 * 1024 * 1024  # 500MB
        self.current_cache_size = 0
        
        # Load existing metadata
        self._load_metadata()
    
    def _load_metadata(self):
        """Load asset metadata from disk."""
        # Load asset registry
        registry_file = self.dirs['metadata'] / 'registry.json'
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    for asset_data in data.get('assets', []):
                        asset = AssetMetadata(**asset_data)
                        self.registry[asset.id] = asset
            except Exception as e:
                logger.error(f"Failed to load asset registry: {e}")
        
        # Load packages
        packages_file = self.dirs['metadata'] / 'packages.json'
        if packages_file.exists():
            try:
                with open(packages_file, 'r') as f:
                    data = json.load(f)
                    for package_data in data.get('packages', []):
                        package = AssetPackage(**package_data)
                        self.packages[package.id] = package
            except Exception as e:
                logger.error(f"Failed to load packages: {e}")
    
    def _save_metadata(self):
        """Save asset metadata to disk."""
        # Save asset registry
        registry_file = self.dirs['metadata'] / 'registry.json'
        registry_data = {
            'assets': [asdict(asset) for asset in self.registry.values()],
            'updated_at': datetime.utcnow().isoformat()
        }
        
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)
        
        # Save packages
        packages_file = self.dirs['metadata'] / 'packages.json'
        packages_data = {
            'packages': [asdict(package) for package in self.packages.values()],
            'updated_at': datetime.utcnow().isoformat()
        }
        
        with open(packages_file, 'w') as f:
            json.dump(packages_data, f, indent=2)
    
    async def import_asset(
        self,
        source_path: str,
        asset_type: AssetType,
        category: AssetCategory,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> AssetMetadata:
        """Import an asset into the management system."""
        
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Asset not found: {source_path}")
        
        # Generate asset ID
        asset_id = self._generate_asset_id(source_path)
        
        # Determine target directory
        target_dir = self._get_asset_directory(asset_type, category)
        
        # Determine file format and name
        file_format = source_path.suffix[1:].lower()
        asset_name = name or source_path.stem
        target_filename = f"{asset_id}.{file_format}"
        target_path = target_dir / target_filename
        
        # Copy file
        shutil.copy2(source_path, target_path)
        
        # Get file info
        file_size = os.path.getsize(target_path)
        checksum = self._calculate_checksum(target_path)
        
        # Get dimensions for images/videos
        dimensions = None
        duration = None
        
        if asset_type in [AssetType.IMAGE, AssetType.TEXTURE]:
            dimensions = await self._get_image_dimensions(target_path)
            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(
                target_path, asset_id, asset_type
            )
        elif asset_type == AssetType.VIDEO:
            dimensions, duration = await self._get_video_info(target_path)
            thumbnail_path = await self._generate_video_thumbnail(
                target_path, asset_id
            )
        else:
            thumbnail_path = None
        
        # Create metadata
        metadata = AssetMetadata(
            id=asset_id,
            name=asset_name,
            type=asset_type,
            category=category,
            path=str(target_path.relative_to(self.assets_dir)),
            size=file_size,
            format=file_format,
            dimensions=dimensions,
            duration=duration,
            tags=tags or [],
            created_at=datetime.utcnow().isoformat(),
            modified_at=datetime.utcnow().isoformat(),
            checksum=checksum,
            thumbnail_path=str(thumbnail_path.relative_to(self.assets_dir)) if thumbnail_path else None,
            properties=properties or {}
        )
        
        # Register asset
        self.registry[asset_id] = metadata
        self._save_metadata()
        
        logger.info(f"Imported asset: {asset_name} ({asset_id})")
        
        return metadata
    
    def _generate_asset_id(self, file_path: Path) -> str:
        """Generate unique asset ID."""
        # Use file content hash + timestamp
        content_hash = self._calculate_checksum(file_path)[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"{content_hash}_{timestamp}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_asset_directory(self, asset_type: AssetType, category: AssetCategory) -> Path:
        """Get directory for asset type and category."""
        type_dir = self.dirs.get(asset_type.value + 's', self.dirs['images'])
        category_dir = type_dir / category.value
        category_dir.mkdir(parents=True, exist_ok=True)
        return category_dir
    
    async def _get_image_dimensions(self, image_path: Path) -> Tuple[int, int]:
        """Get image dimensions."""
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.error(f"Failed to get image dimensions: {e}")
            return None
    
    async def _get_video_info(self, video_path: Path) -> Tuple[Optional[Tuple[int, int]], Optional[float]]:
        """Get video dimensions and duration."""
        try:
            import cv2
            cap = cv2.VideoCapture(str(video_path))
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            duration = frame_count / fps if fps > 0 else None
            
            cap.release()
            
            return (width, height), duration
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None, None
    
    async def _generate_thumbnail(
        self,
        image_path: Path,
        asset_id: str,
        asset_type: AssetType
    ) -> Optional[Path]:
        """Generate thumbnail for image asset."""
        try:
            thumbnail_dir = self.dirs['thumbnails'] / asset_type.value
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            thumbnail_path = thumbnail_dir / f"{asset_id}_thumb.jpg"
            
            with Image.open(image_path) as img:
                # Create thumbnail
                img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None
    
    async def _generate_video_thumbnail(
        self,
        video_path: Path,
        asset_id: str
    ) -> Optional[Path]:
        """Generate thumbnail for video asset."""
        try:
            import cv2
            
            thumbnail_dir = self.dirs['thumbnails'] / 'video'
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            thumbnail_path = thumbnail_dir / f"{asset_id}_thumb.jpg"
            
            # Extract frame from middle of video
            cap = cv2.VideoCapture(str(video_path))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Seek to middle frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
            ret, frame = cap.read()
            
            if ret:
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Create PIL image
                img = Image.fromarray(frame)
                
                # Create thumbnail
                img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
            cap.release()
            
            return thumbnail_path if ret else None
            
        except Exception as e:
            logger.error(f"Failed to generate video thumbnail: {e}")
            return None
    
    async def load_asset(
        self,
        asset_id: str,
        use_cache: bool = True
    ) -> Union[Image.Image, np.ndarray, str, None]:
        """Load an asset by ID."""
        
        # Check cache first
        if use_cache and asset_id in self.cache:
            logger.debug(f"Loading asset from cache: {asset_id}")
            return self.cache[asset_id]
        
        # Get metadata
        metadata = self.registry.get(asset_id)
        if not metadata:
            logger.error(f"Asset not found: {asset_id}")
            return None
        
        # Load asset
        asset_path = self.assets_dir / metadata.path
        
        try:
            if metadata.type in [AssetType.IMAGE, AssetType.TEXTURE]:
                # Load image
                asset = Image.open(asset_path)
                
                # Cache if enabled
                if use_cache:
                    self._add_to_cache(asset_id, asset, metadata.size)
                
                return asset
                
            elif metadata.type == AssetType.VIDEO:
                # Return video path
                return str(asset_path)
                
            elif metadata.type == AssetType.FONT:
                # Return font path
                return str(asset_path)
                
            elif metadata.type == AssetType.EFFECT:
                # Load effect definition
                with open(asset_path, 'r') as f:
                    effect_data = json.load(f)
                
                if use_cache:
                    self._add_to_cache(asset_id, effect_data, metadata.size)
                
                return effect_data
                
            else:
                # Return file path for other types
                return str(asset_path)
                
        except Exception as e:
            logger.error(f"Failed to load asset {asset_id}: {e}")
            return None
    
    def _add_to_cache(self, asset_id: str, asset: Any, size: int):
        """Add asset to cache with size management."""
        
        # Check if cache size limit would be exceeded
        if self.current_cache_size + size > self.cache_size_limit:
            # Evict oldest items
            self._evict_cache_items(size)
        
        # Add to cache
        self.cache[asset_id] = asset
        self.current_cache_size += size
        
        logger.debug(f"Added to cache: {asset_id} (cache size: {self.current_cache_size / 1024 / 1024:.1f}MB)")
    
    def _evict_cache_items(self, required_size: int):
        """Evict items from cache to make room."""
        
        # Simple FIFO eviction for now
        evicted_size = 0
        items_to_evict = []
        
        for asset_id in self.cache:
            if evicted_size >= required_size:
                break
            
            metadata = self.registry.get(asset_id)
            if metadata:
                items_to_evict.append(asset_id)
                evicted_size += metadata.size
        
        # Evict items
        for asset_id in items_to_evict:
            metadata = self.registry.get(asset_id)
            if metadata:
                del self.cache[asset_id]
                self.current_cache_size -= metadata.size
                logger.debug(f"Evicted from cache: {asset_id}")
    
    def search_assets(
        self,
        query: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        category: Optional[AssetCategory] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> List[AssetMetadata]:
        """Search for assets based on criteria."""
        
        results = []
        
        for asset in self.registry.values():
            # Filter by type
            if asset_type and asset.type != asset_type:
                continue
            
            # Filter by category
            if category and asset.category != category:
                continue
            
            # Filter by tags
            if tags:
                if not any(tag in asset.tags for tag in tags):
                    continue
            
            # Filter by properties
            if properties:
                match = True
                for key, value in properties.items():
                    if asset.properties.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            # Text search
            if query:
                query_lower = query.lower()
                if (query_lower not in asset.name.lower() and
                    not any(query_lower in tag.lower() for tag in asset.tags)):
                    continue
            
            results.append(asset)
        
        return results
    
    async def create_package(
        self,
        name: str,
        description: str,
        asset_ids: List[str],
        version: str = "1.0.0",
        author: Optional[str] = None,
        license: Optional[str] = None
    ) -> AssetPackage:
        """Create an asset package."""
        
        # Verify all assets exist
        for asset_id in asset_ids:
            if asset_id not in self.registry:
                raise ValueError(f"Asset not found: {asset_id}")
        
        # Generate package ID
        package_id = f"pkg_{self._generate_asset_id(Path(name))}"
        
        # Create package
        package = AssetPackage(
            id=package_id,
            name=name,
            description=description,
            version=version,
            assets=asset_ids,
            dependencies=[],
            created_at=datetime.utcnow().isoformat(),
            author=author,
            license=license
        )
        
        # Register package
        self.packages[package_id] = package
        self._save_metadata()
        
        logger.info(f"Created package: {name} ({package_id})")
        
        return package
    
    async def export_package(
        self,
        package_id: str,
        output_path: str,
        include_metadata: bool = True
    ) -> str:
        """Export a package with all its assets."""
        
        package = self.packages.get(package_id)
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create package directory
        package_dir = output_path / f"{package.name}_{package.version}"
        package_dir.mkdir(exist_ok=True)
        
        # Copy assets
        assets_dir = package_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        
        for asset_id in package.assets:
            metadata = self.registry.get(asset_id)
            if metadata:
                source = self.assets_dir / metadata.path
                target = assets_dir / f"{asset_id}.{metadata.format}"
                shutil.copy2(source, target)
        
        # Export metadata
        if include_metadata:
            metadata_file = package_dir / 'package.json'
            package_data = asdict(package)
            
            # Include asset metadata
            package_data['asset_metadata'] = [
                asdict(self.registry[asset_id])
                for asset_id in package.assets
                if asset_id in self.registry
            ]
            
            with open(metadata_file, 'w') as f:
                json.dump(package_data, f, indent=2)
        
        # Create archive
        archive_path = output_path / f"{package.name}_{package.version}.zip"
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'zip',
            package_dir
        )
        
        # Clean up
        shutil.rmtree(package_dir)
        
        logger.info(f"Exported package: {package.name} to {archive_path}")
        
        return str(archive_path)
    
    async def download_asset(
        self,
        url: str,
        asset_type: AssetType,
        category: AssetCategory,
        name: Optional[str] = None
    ) -> AssetMetadata:
        """Download and import asset from URL."""
        
        # Create temporary file
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"download_{datetime.utcnow().timestamp()}"
        
        try:
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    # Save to temporary file
                    async with aiofiles.open(temp_file, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
            
            # Determine file extension from content type
            content_type = response.headers.get('content-type', '')
            extension = self._get_extension_from_content_type(content_type)
            
            if extension:
                temp_file_with_ext = temp_file.with_suffix(extension)
                temp_file.rename(temp_file_with_ext)
                temp_file = temp_file_with_ext
            
            # Import asset
            metadata = await self.import_asset(
                str(temp_file),
                asset_type,
                category,
                name=name or Path(url).stem
            )
            
            return metadata
            
        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type."""
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'font/ttf': '.ttf',
            'font/otf': '.otf',
            'application/json': '.json'
        }
        
        return mime_to_ext.get(content_type.split(';')[0].strip(), '')
    
    def get_asset_stats(self) -> Dict[str, Any]:
        """Get statistics about managed assets."""
        
        stats = {
            'total_assets': len(self.registry),
            'total_packages': len(self.packages),
            'total_size': sum(asset.size for asset in self.registry.values()),
            'cache_size': self.current_cache_size,
            'by_type': {},
            'by_category': {}
        }
        
        # Count by type
        for asset in self.registry.values():
            type_key = asset.type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1
            
            category_key = asset.category.value
            stats['by_category'][category_key] = stats['by_category'].get(category_key, 0) + 1
        
        return stats
    
    def cleanup_orphaned_files(self) -> int:
        """Remove files not in registry."""
        
        orphaned_count = 0
        
        # Check all asset directories
        for asset_type in AssetType:
            type_dir = self.dirs.get(asset_type.value + 's')
            if type_dir and type_dir.exists():
                for category_dir in type_dir.iterdir():
                    if category_dir.is_dir():
                        for file_path in category_dir.iterdir():
                            if file_path.is_file():
                                # Check if file is registered
                                registered = False
                                for asset in self.registry.values():
                                    if self.assets_dir / asset.path == file_path:
                                        registered = True
                                        break
                                
                                if not registered:
                                    logger.info(f"Removing orphaned file: {file_path}")
                                    file_path.unlink()
                                    orphaned_count += 1
        
        return orphaned_count