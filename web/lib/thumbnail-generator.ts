/**
 * Thumbnail generation utilities for media assets
 * Generates previews for images, videos, and audio files
 */

interface ThumbnailOptions {
  width?: number;
  height?: number;
  quality?: number;
  format?: 'jpeg' | 'webp' | 'png';
}

interface VideoThumbnailOptions extends ThumbnailOptions {
  timestamp?: number; // Timestamp in seconds to capture frame
}

interface AudioThumbnailOptions extends ThumbnailOptions {
  waveformColor?: string;
  backgroundColor?: string;
  style?: 'waveform' | 'spectrogram' | 'bars';
}

const DEFAULT_THUMBNAIL_SIZE = { width: 320, height: 180 }; // 16:9 aspect ratio

/**
 * Generate thumbnail for an image
 */
export async function generateImageThumbnail(
  imageUrl: string,
  options: ThumbnailOptions = {},
): Promise<string> {
  const {
    width = DEFAULT_THUMBNAIL_SIZE.width,
    height = DEFAULT_THUMBNAIL_SIZE.height,
    quality = 0.8,
    format = 'jpeg',
  } = options;

  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        if (!ctx) {
          reject(new Error('Could not get canvas context'));
          return;
        }

        // Calculate dimensions maintaining aspect ratio
        const aspectRatio = img.width / img.height;
        const targetAspectRatio = width / height;
        
        let drawWidth = width;
        let drawHeight = height;
        let offsetX = 0;
        let offsetY = 0;

        if (aspectRatio > targetAspectRatio) {
          // Image is wider, fit to height
          drawWidth = height * aspectRatio;
          offsetX = (width - drawWidth) / 2;
        } else {
          // Image is taller, fit to width
          drawHeight = width / aspectRatio;
          offsetY = (height - drawHeight) / 2;
        }

        canvas.width = width;
        canvas.height = height;
        
        // Fill background with neutral color
        ctx.fillStyle = '#f3f4f6';
        ctx.fillRect(0, 0, width, height);
        
        // Draw image
        ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
        
        // Convert to desired format
        const mimeType = `image/${format}`;
        const dataUrl = canvas.toDataURL(mimeType, quality);
        resolve(dataUrl);
      } catch (error) {
        reject(error);
      }
    };
    
    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };
    
    img.src = imageUrl;
  });
}

/**
 * Generate thumbnail for a video
 */
export async function generateVideoThumbnail(
  videoUrl: string,
  options: VideoThumbnailOptions = {},
): Promise<string> {
  const {
    width = DEFAULT_THUMBNAIL_SIZE.width,
    height = DEFAULT_THUMBNAIL_SIZE.height,
    quality = 0.8,
    format = 'jpeg',
    timestamp = 1, // Capture frame at 1 second by default
  } = options;

  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.crossOrigin = 'anonymous';
    video.preload = 'metadata';
    
    video.addEventListener('loadedmetadata', () => {
      // Set current time to desired timestamp
      const seekTime = Math.min(timestamp, video.duration - 0.1);
      video.currentTime = seekTime;
    });
    
    video.addEventListener('seeked', () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        if (!ctx) {
          reject(new Error('Could not get canvas context'));
          return;
        }

        // Calculate dimensions maintaining aspect ratio
        const aspectRatio = video.videoWidth / video.videoHeight;
        const targetAspectRatio = width / height;
        
        let drawWidth = width;
        let drawHeight = height;
        let offsetX = 0;
        let offsetY = 0;

        if (aspectRatio > targetAspectRatio) {
          drawWidth = height * aspectRatio;
          offsetX = (width - drawWidth) / 2;
        } else {
          drawHeight = width / aspectRatio;
          offsetY = (height - drawHeight) / 2;
        }

        canvas.width = width;
        canvas.height = height;
        
        // Fill background
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, width, height);
        
        // Draw video frame
        ctx.drawImage(video, offsetX, offsetY, drawWidth, drawHeight);
        
        // Add video play icon overlay
        drawPlayIcon(ctx, width, height);
        
        const mimeType = `image/${format}`;
        const dataUrl = canvas.toDataURL(mimeType, quality);
        resolve(dataUrl);
      } catch (error) {
        reject(error);
      }
    });
    
    video.addEventListener('error', () => {
      reject(new Error('Failed to load video'));
    });
    
    video.src = videoUrl;
  });
}

/**
 * Generate thumbnail for an audio file
 */
export async function generateAudioThumbnail(
  _audioUrl: string,
  options: AudioThumbnailOptions = {},
): Promise<string> {
  const {
    width = DEFAULT_THUMBNAIL_SIZE.width,
    height = DEFAULT_THUMBNAIL_SIZE.height,
    quality = 0.8,
    format = 'png',
    waveformColor = '#3b82f6',
    backgroundColor = '#f8fafc',
    style = 'waveform',
  } = options;

  try {
    // For basic implementation, we'll create a static waveform-style thumbnail
    // In a real implementation, you'd analyze the audio data using Web Audio API
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Could not get canvas context');
    }

    canvas.width = width;
    canvas.height = height;
    
    // Fill background
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, width, height);
    
    // Draw waveform pattern
    ctx.fillStyle = waveformColor;
    ctx.strokeStyle = waveformColor;
    ctx.lineWidth = 2;
    
    const centerY = height / 2;
    const barWidth = 3;
    const barSpacing = 1;
    const totalBars = Math.floor(width / (barWidth + barSpacing));
    
    if (style === 'waveform') {
      for (let i = 0; i < totalBars; i++) {
        const x = i * (barWidth + barSpacing);
        const amplitude = Math.random() * 0.8 + 0.1; // Random amplitude between 0.1 and 0.9
        const barHeight = amplitude * (height * 0.4);
        
        ctx.fillRect(x, centerY - barHeight / 2, barWidth, barHeight);
      }
    } else if (style === 'bars') {
      const numBars = 12;
      const barWidth = width / numBars - 4;
      
      for (let i = 0; i < numBars; i++) {
        const x = (i * width) / numBars + 2;
        const amplitude = Math.random() * 0.7 + 0.2;
        const barHeight = amplitude * height * 0.8;
        
        ctx.fillRect(x, height - barHeight - 10, barWidth, barHeight);
      }
    }
    
    // Add audio icon
    drawAudioIcon(ctx, width, height);
    
    const mimeType = `image/${format}`;
    const dataUrl = canvas.toDataURL(mimeType, quality);
    return dataUrl;
  } catch (error) {
    throw new Error(`Failed to generate audio thumbnail: ${error}`);
  }
}

/**
 * Generate thumbnail based on media type
 */
export async function generateThumbnail(
  mediaUrl: string,
  mediaType: 'image' | 'video' | 'audio',
  options: ThumbnailOptions & VideoThumbnailOptions & AudioThumbnailOptions = {},
): Promise<string> {
  switch (mediaType) {
    case 'image':
      return generateImageThumbnail(mediaUrl, options);
    case 'video':
      return generateVideoThumbnail(mediaUrl, options);
    case 'audio':
      return generateAudioThumbnail(mediaUrl, options);
    default:
      throw new Error(`Unsupported media type: ${mediaType}`);
  }
}

/**
 * Draw a play icon overlay on canvas
 */
function drawPlayIcon(ctx: CanvasRenderingContext2D, width: number, height: number) {
  const centerX = width / 2;
  const centerY = height / 2;
  const iconSize = Math.min(width, height) * 0.15;
  
  // Draw semi-transparent circle background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
  ctx.beginPath();
  ctx.arc(centerX, centerY, iconSize, 0, 2 * Math.PI);
  ctx.fill();
  
  // Draw play triangle
  ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
  ctx.beginPath();
  ctx.moveTo(centerX - iconSize * 0.3, centerY - iconSize * 0.4);
  ctx.lineTo(centerX - iconSize * 0.3, centerY + iconSize * 0.4);
  ctx.lineTo(centerX + iconSize * 0.4, centerY);
  ctx.closePath();
  ctx.fill();
}

/**
 * Draw an audio icon on canvas
 */
function drawAudioIcon(ctx: CanvasRenderingContext2D, width: number, height: number) {
  const iconSize = Math.min(width, height) * 0.12;
  const x = width - iconSize - 10;
  const y = 10;
  
  // Draw speaker icon
  ctx.fillStyle = 'rgba(59, 130, 246, 0.8)';
  ctx.fillRect(x, y + iconSize * 0.3, iconSize * 0.4, iconSize * 0.4);
  
  // Draw sound waves
  ctx.strokeStyle = 'rgba(59, 130, 246, 0.6)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(x + iconSize * 0.4, y + iconSize * 0.5, iconSize * 0.3, -Math.PI / 4, Math.PI / 4);
  ctx.stroke();
  
  ctx.beginPath();
  ctx.arc(x + iconSize * 0.4, y + iconSize * 0.5, iconSize * 0.5, -Math.PI / 6, Math.PI / 6);
  ctx.stroke();
}

/**
 * Batch generate thumbnails for multiple assets
 */
export async function generateThumbnailsBatch(
  assets: Array<{ url: string; type: 'image' | 'video' | 'audio'; id: string }>,
  options: ThumbnailOptions = {},
): Promise<Map<string, string>> {
  const thumbnails = new Map<string, string>();
  const maxConcurrent = 3; // Limit concurrent operations
  
  for (let i = 0; i < assets.length; i += maxConcurrent) {
    const batch = assets.slice(i, i + maxConcurrent);
    
    const promises = batch.map(async asset => {
      try {
        const thumbnail = await generateThumbnail(asset.url, asset.type, options);
        return { id: asset.id, thumbnail };
      } catch (error) {
        console.error(`Failed to generate thumbnail for ${asset.id}:`, error);
        return { id: asset.id, thumbnail: null };
      }
    });
    
    const results = await Promise.all(promises);
    
    results.forEach(result => {
      if (result.thumbnail) {
        thumbnails.set(result.id, result.thumbnail);
      }
    });
  }
  
  return thumbnails;
}

/**
 * Cache thumbnails in localStorage with size limits
 */
export class ThumbnailCache {
  private static readonly CACHE_KEY = 'evergreen_thumbnails';
  private static readonly MAX_CACHE_SIZE = 10 * 1024 * 1024; // 10MB limit
  
  static get(key: string): string | null {
    try {
      const cache = JSON.parse(localStorage.getItem(this.CACHE_KEY) || '{}');
      return cache[key] || null;
    } catch {
      return null;
    }
  }
  
  static set(key: string, thumbnail: string): void {
    try {
      const cache = JSON.parse(localStorage.getItem(this.CACHE_KEY) || '{}');
      cache[key] = thumbnail;
      
      // Check size and clean if necessary
      const cacheString = JSON.stringify(cache);
      if (cacheString.length > this.MAX_CACHE_SIZE) {
        this.cleanup();
        // Try again with cleaned cache
        const cleanedCache = JSON.parse(localStorage.getItem(this.CACHE_KEY) || '{}');
        cleanedCache[key] = thumbnail;
        localStorage.setItem(this.CACHE_KEY, JSON.stringify(cleanedCache));
      } else {
        localStorage.setItem(this.CACHE_KEY, cacheString);
      }
    } catch (error) {
      console.warn('Failed to cache thumbnail:', error);
    }
  }
  
  static cleanup(): void {
    try {
      const cache = JSON.parse(localStorage.getItem(this.CACHE_KEY) || '{}');
      const keys = Object.keys(cache);
      
      // Remove oldest half of entries (simple cleanup strategy)
      const keysToRemove = keys.slice(0, Math.floor(keys.length / 2));
      keysToRemove.forEach(key => delete cache[key]);
      
      localStorage.setItem(this.CACHE_KEY, JSON.stringify(cache));
    } catch (error) {
      console.warn('Failed to cleanup thumbnail cache:', error);
      localStorage.removeItem(this.CACHE_KEY);
    }
  }
  
  static clear(): void {
    localStorage.removeItem(this.CACHE_KEY);
  }
}

export default {
  generateThumbnail,
  generateImageThumbnail,
  generateVideoThumbnail,
  generateAudioThumbnail,
  generateThumbnailsBatch,
  ThumbnailCache,
};