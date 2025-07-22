"""
GPU-accelerated FFmpeg service for high-performance video processing.
Supports NVIDIA NVENC, AMD AMF, Intel QuickSync, and Apple VideoToolbox.
"""

import os
import asyncio
import subprocess
import platform
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import tempfile
import json

from ..config import settings

logger = logging.getLogger(__name__)


class GPUAcceleratedFFmpeg:
    """FFmpeg service with GPU acceleration support."""
    
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        self.ffmpeg_path = self._find_ffmpeg()
        self.gpu_capabilities = self._check_gpu_capabilities()
        
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable with GPU support."""
        # Try to find FFmpeg in PATH
        ffmpeg_names = ['ffmpeg']
        
        for name in ffmpeg_names:
            try:
                result = subprocess.run(
                    [name, '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found FFmpeg at: {name}")
                    return name
            except:
                continue
        
        # Default fallback
        return 'ffmpeg'
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect available GPU hardware."""
        gpu_info = {
            'vendor': None,
            'model': None,
            'memory': None,
            'cuda_available': False,
            'opencl_available': False,
            'metal_available': False,
            'vulkan_available': False
        }
        
        system = platform.system()
        
        if system == 'Linux' or system == 'Windows':
            # Check for NVIDIA GPU
            try:
                nvidia_smi = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if nvidia_smi.returncode == 0:
                    output = nvidia_smi.stdout.strip()
                    if output:
                        parts = output.split(', ')
                        gpu_info['vendor'] = 'NVIDIA'
                        gpu_info['model'] = parts[0]
                        gpu_info['memory'] = parts[1] if len(parts) > 1 else None
                        gpu_info['cuda_available'] = True
                        logger.info(f"Detected NVIDIA GPU: {gpu_info['model']}")
            except:
                pass
            
            # Check for AMD GPU
            if not gpu_info['vendor']:
                try:
                    # Check for AMD GPU on Linux
                    if system == 'Linux':
                        lspci = subprocess.run(
                            ['lspci'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if 'AMD' in lspci.stdout and ('VGA' in lspci.stdout or 'Display' in lspci.stdout):
                            gpu_info['vendor'] = 'AMD'
                            gpu_info['opencl_available'] = True
                            logger.info("Detected AMD GPU")
                except:
                    pass
            
            # Check for Intel GPU
            if not gpu_info['vendor']:
                try:
                    if system == 'Linux':
                        if os.path.exists('/dev/dri/renderD128'):
                            gpu_info['vendor'] = 'Intel'
                            gpu_info['opencl_available'] = True
                            logger.info("Detected Intel GPU")
                except:
                    pass
        
        elif system == 'Darwin':  # macOS
            # Check for Metal support
            try:
                system_profiler = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType', '-json'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if system_profiler.returncode == 0:
                    data = json.loads(system_profiler.stdout)
                    if 'SPDisplaysDataType' in data:
                        displays = data['SPDisplaysDataType']
                        if displays:
                            gpu = displays[0]
                            gpu_info['vendor'] = 'Apple' if 'Apple' in str(gpu) else 'Other'
                            gpu_info['model'] = gpu.get('sppci_model', 'Unknown')
                            gpu_info['metal_available'] = True
                            logger.info(f"Detected GPU: {gpu_info['model']}")
            except:
                pass
        
        return gpu_info
    
    def _check_gpu_capabilities(self) -> Dict[str, bool]:
        """Check FFmpeg GPU encoding/decoding capabilities."""
        capabilities = {
            'nvenc': False,
            'nvdec': False,
            'qsv': False,
            'amf': False,
            'videotoolbox': False,
            'vaapi': False,
            'opencl': False,
            'vulkan': False
        }
        
        try:
            # Check encoders
            encoders = subprocess.run(
                [self.ffmpeg_path, '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if encoders.returncode == 0:
                output = encoders.stdout
                
                # NVIDIA
                if 'h264_nvenc' in output:
                    capabilities['nvenc'] = True
                    logger.info("NVENC hardware encoding available")
                
                # Intel QuickSync
                if 'h264_qsv' in output:
                    capabilities['qsv'] = True
                    logger.info("Intel QuickSync encoding available")
                
                # AMD AMF
                if 'h264_amf' in output:
                    capabilities['amf'] = True
                    logger.info("AMD AMF encoding available")
                
                # Apple VideoToolbox
                if 'h264_videotoolbox' in output:
                    capabilities['videotoolbox'] = True
                    logger.info("Apple VideoToolbox encoding available")
                
                # VAAPI (Linux)
                if 'h264_vaapi' in output:
                    capabilities['vaapi'] = True
                    logger.info("VAAPI hardware encoding available")
            
            # Check filters for GPU processing
            filters = subprocess.run(
                [self.ffmpeg_path, '-filters'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if filters.returncode == 0:
                output = filters.stdout
                
                if 'opencl' in output:
                    capabilities['opencl'] = True
                    logger.info("OpenCL filters available")
                
                if 'vulkan' in output:
                    capabilities['vulkan'] = True
                    logger.info("Vulkan filters available")
            
        except Exception as e:
            logger.error(f"Failed to check GPU capabilities: {e}")
        
        return capabilities
    
    def get_gpu_encoder(self, codec: str = 'h264') -> Optional[str]:
        """Get the best available GPU encoder for the specified codec."""
        if codec == 'h264':
            # Priority order based on quality and performance
            if self.gpu_capabilities['nvenc'] and self.gpu_info['vendor'] == 'NVIDIA':
                return 'h264_nvenc'
            elif self.gpu_capabilities['videotoolbox'] and platform.system() == 'Darwin':
                return 'h264_videotoolbox'
            elif self.gpu_capabilities['qsv'] and self.gpu_info['vendor'] == 'Intel':
                return 'h264_qsv'
            elif self.gpu_capabilities['amf'] and self.gpu_info['vendor'] == 'AMD':
                return 'h264_amf'
            elif self.gpu_capabilities['vaapi'] and platform.system() == 'Linux':
                return 'h264_vaapi'
        
        elif codec == 'hevc' or codec == 'h265':
            if self.gpu_capabilities['nvenc'] and self.gpu_info['vendor'] == 'NVIDIA':
                return 'hevc_nvenc'
            elif self.gpu_capabilities['videotoolbox'] and platform.system() == 'Darwin':
                return 'hevc_videotoolbox'
            elif self.gpu_capabilities['qsv'] and self.gpu_info['vendor'] == 'Intel':
                return 'hevc_qsv'
            elif self.gpu_capabilities['amf'] and self.gpu_info['vendor'] == 'AMD':
                return 'hevc_amf'
            elif self.gpu_capabilities['vaapi'] and platform.system() == 'Linux':
                return 'hevc_vaapi'
        
        return None
    
    def get_gpu_decoder(self, codec: str = 'h264') -> Optional[str]:
        """Get the best available GPU decoder for the specified codec."""
        if codec == 'h264':
            if self.gpu_info['vendor'] == 'NVIDIA' and self.gpu_info['cuda_available']:
                return 'h264_cuvid'
            elif platform.system() == 'Darwin':
                return 'h264_videotoolbox'
            elif self.gpu_capabilities['qsv'] and self.gpu_info['vendor'] == 'Intel':
                return 'h264_qsv'
            elif self.gpu_capabilities['vaapi'] and platform.system() == 'Linux':
                return 'h264_vaapi'
        
        elif codec == 'hevc' or codec == 'h265':
            if self.gpu_info['vendor'] == 'NVIDIA' and self.gpu_info['cuda_available']:
                return 'hevc_cuvid'
            elif platform.system() == 'Darwin':
                return 'hevc_videotoolbox'
            elif self.gpu_capabilities['qsv'] and self.gpu_info['vendor'] == 'Intel':
                return 'hevc_qsv'
            elif self.gpu_capabilities['vaapi'] and platform.system() == 'Linux':
                return 'hevc_vaapi'
        
        return None
    
    def get_gpu_filters(self) -> List[str]:
        """Get available GPU-accelerated filters."""
        gpu_filters = []
        
        if self.gpu_capabilities['opencl']:
            gpu_filters.extend([
                'unsharp_opencl',
                'scale_opencl',
                'overlay_opencl',
                'colorkey_opencl',
                'deshake_opencl'
            ])
        
        if self.gpu_info['vendor'] == 'NVIDIA' and self.gpu_info['cuda_available']:
            gpu_filters.extend([
                'scale_cuda',
                'scale_npp',
                'overlay_cuda',
                'thumbnail_cuda',
                'chromakey_cuda',
                'bilateral_cuda'
            ])
        
        if self.gpu_capabilities['vulkan']:
            gpu_filters.extend([
                'scale_vulkan',
                'overlay_vulkan',
                'chromaber_vulkan',
                'flip_vulkan'
            ])
        
        return gpu_filters
    
    async def transcode_with_gpu(
        self,
        input_path: str,
        output_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Transcode video using GPU acceleration."""
        if options is None:
            options = {}
        
        # Build command
        cmd = [self.ffmpeg_path, '-y']
        
        # Hardware decode
        input_codec = options.get('input_codec', 'h264')
        gpu_decoder = self.get_gpu_decoder(input_codec)
        
        if gpu_decoder:
            if 'cuvid' in gpu_decoder:
                cmd.extend(['-hwaccel', 'cuda'])
            elif 'videotoolbox' in gpu_decoder:
                cmd.extend(['-hwaccel', 'videotoolbox'])
            elif 'qsv' in gpu_decoder:
                cmd.extend(['-hwaccel', 'qsv'])
            
            cmd.extend(['-c:v', gpu_decoder])
        
        # Input file
        cmd.extend(['-i', input_path])
        
        # Video encoding settings
        output_codec = options.get('output_codec', 'h264')
        gpu_encoder = self.get_gpu_encoder(output_codec)
        
        if gpu_encoder:
            cmd.extend(['-c:v', gpu_encoder])
            
            # Encoder-specific options
            if 'nvenc' in gpu_encoder:
                cmd.extend([
                    '-preset', options.get('preset', 'p4'),  # p1-p7, higher = better quality
                    '-rc', 'vbr',  # Variable bitrate
                    '-cq', str(options.get('quality', 23)),  # Quality (0-51)
                    '-b:v', options.get('bitrate', '5M'),
                    '-maxrate', options.get('maxrate', '10M'),
                    '-profile:v', 'high',
                    '-level', '4.1',
                    '-rc-lookahead', '32',
                    '-spatial_aq', '1',
                    '-temporal_aq', '1',
                    '-gpu', str(options.get('gpu_id', 0))
                ])
            
            elif 'videotoolbox' in gpu_encoder:
                cmd.extend([
                    '-profile:v', 'high',
                    '-level', '4.1',
                    '-b:v', options.get('bitrate', '5M'),
                    '-maxrate', options.get('maxrate', '10M'),
                    '-allow_sw', '1'  # Allow software fallback
                ])
            
            elif 'qsv' in gpu_encoder:
                cmd.extend([
                    '-preset', options.get('preset', 'medium'),
                    '-profile:v', 'high',
                    '-level', '4.1',
                    '-b:v', options.get('bitrate', '5M'),
                    '-maxrate', options.get('maxrate', '10M'),
                    '-look_ahead', '1',
                    '-look_ahead_depth', '60'
                ])
            
            elif 'amf' in gpu_encoder:
                cmd.extend([
                    '-usage', 'transcoding',
                    '-profile:v', 'high',
                    '-level', '4.1',
                    '-b:v', options.get('bitrate', '5M'),
                    '-maxrate', options.get('maxrate', '10M'),
                    '-rc', 'vbr_peak'
                ])
        else:
            # Fallback to software encoding
            logger.warning("GPU encoder not available, falling back to software encoding")
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', options.get('preset', 'medium'),
                '-crf', str(options.get('quality', 23))
            ])
        
        # Audio settings
        cmd.extend([
            '-c:a', options.get('audio_codec', 'aac'),
            '-b:a', options.get('audio_bitrate', '192k')
        ])
        
        # Output format settings
        cmd.extend([
            '-movflags', '+faststart',  # Web optimization
            '-pix_fmt', 'yuv420p'  # Compatibility
        ])
        
        # Custom filters
        if 'filters' in options:
            cmd.extend(['-vf', options['filters']])
        
        # Output file
        cmd.append(output_path)
        
        # Execute command
        try:
            logger.info(f"GPU transcoding command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"GPU transcoding failed: {stderr.decode()}")
                return False
            
            logger.info("GPU transcoding completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"GPU transcoding error: {e}")
            return False
    
    async def apply_gpu_filters(
        self,
        input_path: str,
        output_path: str,
        filters: List[Dict[str, Any]]
    ) -> bool:
        """Apply GPU-accelerated filters to video."""
        
        filter_chain = []
        
        for filter_spec in filters:
            filter_name = filter_spec['name']
            params = filter_spec.get('params', {})
            
            # Map to GPU filter if available
            gpu_filters = self.get_gpu_filters()
            
            if filter_name == 'scale' and 'scale_cuda' in gpu_filters:
                # Use CUDA scaling
                width = params.get('width', -1)
                height = params.get('height', -1)
                filter_chain.append(f"scale_cuda={width}:{height}")
            
            elif filter_name == 'scale' and 'scale_opencl' in gpu_filters:
                # Use OpenCL scaling
                width = params.get('width', -1)
                height = params.get('height', -1)
                filter_chain.append(f"scale_opencl={width}:{height}")
            
            elif filter_name == 'blur' and 'bilateral_cuda' in gpu_filters:
                # Use CUDA bilateral filter for blur
                sigma = params.get('sigma', 5)
                filter_chain.append(f"bilateral_cuda=sigmaS={sigma}:sigmaR=0.1")
            
            elif filter_name == 'sharpen' and 'unsharp_opencl' in gpu_filters:
                # Use OpenCL unsharp mask
                amount = params.get('amount', 1.5)
                filter_chain.append(f"unsharp_opencl=luma_msize_x=5:luma_amount={amount}")
            
            else:
                # Fallback to CPU filter
                if filter_name == 'scale':
                    width = params.get('width', -1)
                    height = params.get('height', -1)
                    filter_chain.append(f"scale={width}:{height}")
                elif filter_name == 'blur':
                    sigma = params.get('sigma', 5)
                    filter_chain.append(f"gblur=sigma={sigma}")
                elif filter_name == 'sharpen':
                    amount = params.get('amount', 1.5)
                    filter_chain.append(f"unsharp=5:5:{amount}:5:5:0")
        
        # Build FFmpeg command
        cmd = [self.ffmpeg_path, '-y']
        
        # Use hardware decode if available
        gpu_decoder = self.get_gpu_decoder()
        if gpu_decoder:
            if 'cuvid' in gpu_decoder:
                cmd.extend(['-hwaccel', 'cuda'])
            cmd.extend(['-c:v', gpu_decoder])
        
        cmd.extend([
            '-i', input_path,
            '-vf', ','.join(filter_chain),
            '-c:v', self.get_gpu_encoder() or 'libx264',
            '-preset', 'fast',
            '-c:a', 'copy',
            output_path
        ])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"GPU filter processing failed: {stderr.decode()}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"GPU filter error: {e}")
            return False
    
    def get_optimization_params(self, use_case: str = 'general') -> Dict[str, Any]:
        """Get optimized encoding parameters for different use cases."""
        
        base_params = {
            'gpu_encoder': self.get_gpu_encoder(),
            'gpu_decoder': self.get_gpu_decoder()
        }
        
        if use_case == 'streaming':
            # Optimized for low latency streaming
            params = {
                **base_params,
                'preset': 'p1' if 'nvenc' in str(base_params.get('gpu_encoder')) else 'ultrafast',
                'tune': 'zerolatency',
                'bitrate': '2500k',
                'maxrate': '3000k',
                'bufsize': '1000k',
                'g': 60,  # GOP size
                'keyint_min': 60,
                'sc_threshold': 0
            }
        
        elif use_case == 'quality':
            # Maximum quality
            params = {
                **base_params,
                'preset': 'p7' if 'nvenc' in str(base_params.get('gpu_encoder')) else 'slow',
                'quality': 18,
                'bitrate': '10M',
                'maxrate': '15M',
                'profile': 'high',
                'level': '5.1'
            }
        
        elif use_case == 'fast':
            # Fast encoding
            params = {
                **base_params,
                'preset': 'p3' if 'nvenc' in str(base_params.get('gpu_encoder')) else 'fast',
                'quality': 25,
                'bitrate': '4M',
                'maxrate': '6M'
            }
        
        else:  # general
            # Balanced settings
            params = {
                **base_params,
                'preset': 'p4' if 'nvenc' in str(base_params.get('gpu_encoder')) else 'medium',
                'quality': 23,
                'bitrate': '5M',
                'maxrate': '8M'
            }
        
        return params
    
    def benchmark_gpu_performance(self) -> Dict[str, float]:
        """Benchmark GPU encoding performance."""
        results = {}
        
        # Create test video
        test_duration = 5
        test_resolution = "1920x1080"
        test_fps = 30
        
        test_input = tempfile.mktemp(suffix=".mp4")
        
        # Generate test video
        cmd = [
            self.ffmpeg_path, '-y',
            '-f', 'lavfi',
            '-i', f'testsrc2=size={test_resolution}:rate={test_fps}:duration={test_duration}',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            test_input
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Test each available GPU encoder
            for encoder_name in ['h264_nvenc', 'h264_videotoolbox', 'h264_qsv', 'h264_amf']:
                if encoder_name.split('_')[1] in str(self.gpu_capabilities):
                    test_output = tempfile.mktemp(suffix=".mp4")
                    
                    cmd = [
                        self.ffmpeg_path, '-y',
                        '-i', test_input,
                        '-c:v', encoder_name,
                        '-preset', 'fast',
                        test_output
                    ]
                    
                    import time
                    start_time = time.time()
                    
                    result = subprocess.run(cmd, capture_output=True)
                    
                    if result.returncode == 0:
                        encode_time = time.time() - start_time
                        fps = (test_duration * test_fps) / encode_time
                        results[encoder_name] = fps
                        logger.info(f"{encoder_name}: {fps:.1f} fps")
                    
                    if os.path.exists(test_output):
                        os.unlink(test_output)
            
            # Test software encoder for comparison
            test_output = tempfile.mktemp(suffix=".mp4")
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', test_input,
                '-c:v', 'libx264',
                '-preset', 'fast',
                test_output
            ]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                encode_time = time.time() - start_time
                fps = (test_duration * test_fps) / encode_time
                results['libx264'] = fps
                logger.info(f"libx264 (CPU): {fps:.1f} fps")
            
            if os.path.exists(test_output):
                os.unlink(test_output)
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
        
        finally:
            if os.path.exists(test_input):
                os.unlink(test_input)
        
        return results