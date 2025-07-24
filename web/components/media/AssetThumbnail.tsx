import React, { useState, useEffect } from 'react';
import {
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  PlayIcon,
  EyeIcon,
  CloudArrowDownIcon,
  TrashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { generateThumbnail, ThumbnailCache } from '@/lib/thumbnail-generator';

interface MediaAsset {
  id: string;
  name: string;
  type: 'image' | 'video' | 'audio';
  url: string;
  thumbnailUrl?: string;
  size: number;
  duration?: number;
  sceneId: string;
  sceneName: string;
  createdAt: Date;
  metadata?: {
    width?: number;
    height?: number;
    format?: string;
    prompt?: string;
    provider?: string;
    cost?: number;
  };
}

interface AssetThumbnailProps {
  asset: MediaAsset;
  onPreview?: (asset: MediaAsset) => void;
  onDownload?: (asset: MediaAsset) => void;
  onDelete?: (assetId: string) => void;
  onRegenerate?: (asset: MediaAsset) => void;
  onSelect?: (asset: MediaAsset) => void;
  compact?: boolean;
  className?: string;
}

export const AssetThumbnail: React.FC<AssetThumbnailProps> = ({
  asset,
  onPreview,
  onDownload,
  onDelete,
  onRegenerate,
  onSelect,
  compact = false,
  className,
}) => {
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(asset.thumbnailUrl || null);
  const [isGeneratingThumbnail, setIsGeneratingThumbnail] = useState(false);
  const [thumbnailError, setThumbnailError] = useState(false);

  useEffect(() => {
    generateThumbnailIfNeeded();
  }, [asset.url, asset.type]);

  const generateThumbnailIfNeeded = async () => {
    // Check if we already have a thumbnail
    if (thumbnailUrl && !thumbnailError) return;

    // For images, the URL itself is the thumbnail
    if (asset.type === 'image') {
      setThumbnailUrl(asset.url);
      return;
    }

    // Check cache first
    const cacheKey = `${asset.id}_${asset.url}`;
    const cachedThumbnail = ThumbnailCache.get(cacheKey);
    if (cachedThumbnail) {
      setThumbnailUrl(cachedThumbnail);
      return;
    }

    // Generate new thumbnail
    try {
      setIsGeneratingThumbnail(true);
      setThumbnailError(false);
      
      const thumbnail = await generateThumbnail(asset.url, asset.type, {
        width: compact ? 160 : 320,
        height: compact ? 90 : 180,
        quality: 0.8,
      });
      
      setThumbnailUrl(thumbnail);
      ThumbnailCache.set(cacheKey, thumbnail);
    } catch (error) {
      console.error('Failed to generate thumbnail:', error);
      setThumbnailError(true);
    } finally {
      setIsGeneratingThumbnail(false);
    }
  };

  const handleRetryThumbnail = () => {
    setThumbnailError(false);
    setThumbnailUrl(null);
    generateThumbnailIfNeeded();
  };

  const getAssetIcon = (type: string) => {
    switch (type) {
      case 'image': return PhotoIcon;
      case 'video': return VideoCameraIcon;
      case 'audio': return SpeakerWaveIcon;
      default: return PhotoIcon;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 KB';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatCost = (cost?: number): string => {
    if (!cost) return '';
    return `$${cost.toFixed(3)}`;
  };

  const IconComponent = getAssetIcon(asset.type);
  const aspectRatio = compact ? 'aspect-video' : 'aspect-video';

  return (
    <div
      className={cn(
        'group relative bg-zinc-900 rounded-lg overflow-hidden hover:bg-zinc-800 transition-colors border border-zinc-700 hover:border-zinc-600',
        className,
      )}
    >
      {/* Thumbnail */}
      <div className={cn('relative', aspectRatio)}>
        {thumbnailUrl && !thumbnailError ? (
          <img
            src={thumbnailUrl}
            alt={asset.name}
            className="w-full h-full object-cover"
            onError={() => setThumbnailError(true)}
          />
        ) : isGeneratingThumbnail ? (
          <div className="flex items-center justify-center h-full bg-zinc-800">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          </div>
        ) : thumbnailError ? (
          <div className="flex flex-col items-center justify-center h-full bg-zinc-800 text-zinc-400">
            <IconComponent className="h-8 w-8 mb-2" />
            <button
              onClick={handleRetryThumbnail}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center"
            >
              <ArrowPathIcon className="h-3 w-3 mr-1" />
              Retry
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full bg-zinc-800">
            <IconComponent className="h-8 w-8 text-zinc-400" />
          </div>
        )}
        
        {/* Play overlay for videos */}
        {asset.type === 'video' && thumbnailUrl && !thumbnailError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-black bg-opacity-60 rounded-full p-2">
              <PlayIcon className="h-6 w-6 text-white" />
            </div>
          </div>
        )}
        
        {/* Duration badge */}
        {asset.duration && (
          <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
            {formatDuration(asset.duration)}
          </div>
        )}
        
        {/* Action overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
          <div className="flex space-x-2">
            {onPreview && (
              <button
                onClick={() => onPreview(asset)}
                className="p-2 bg-white bg-opacity-90 rounded-full text-zinc-700 hover:bg-opacity-100 transition-all"
                title="Preview"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
            )}
            {onDownload && (
              <button
                onClick={() => onDownload(asset)}
                className="p-2 bg-white bg-opacity-90 rounded-full text-zinc-700 hover:bg-opacity-100 transition-all"
                title="Download"
              >
                <CloudArrowDownIcon className="h-4 w-4" />
              </button>
            )}
            {onRegenerate && (
              <button
                onClick={() => onRegenerate(asset)}
                className="p-2 bg-blue-500 bg-opacity-90 rounded-full text-white hover:bg-opacity-100 transition-all"
                title="Regenerate"
              >
                <ArrowPathIcon className="h-4 w-4" />
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(asset.id)}
                className="p-2 bg-red-500 bg-opacity-90 rounded-full text-white hover:bg-opacity-100 transition-all"
                title="Delete"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Asset info */}
      <div className="p-3">
        <p className="text-sm font-medium text-white truncate">
          {asset.name}
        </p>
        <p className="text-xs text-zinc-400 truncate">
          {asset.sceneName}
        </p>
        
        <div className="flex items-center justify-between mt-2">
          <span className={cn(
            'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
            asset.type === 'image' ? 'bg-green-900 text-green-300' :
            asset.type === 'video' ? 'bg-purple-900 text-purple-300' :
            'bg-blue-900 text-blue-300',
          )}>
            {asset.type}
          </span>
          <span className="text-xs text-zinc-500">
            {formatFileSize(asset.size)}
          </span>
        </div>

        {/* Additional metadata */}
        {!compact && (
          <div className="mt-2 space-y-1">
            {asset.metadata?.prompt && (
              <p className="text-xs text-zinc-400 line-clamp-2" title={asset.metadata.prompt}>
                "{asset.metadata.prompt}"
              </p>
            )}
            {asset.metadata?.provider && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-500">
                  {asset.metadata.provider}
                </span>
                {asset.metadata?.cost && (
                  <span className="text-xs text-zinc-500">
                    {formatCost(asset.metadata.cost)}
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Select button for asset picking */}
        {onSelect && (
          <button
            onClick={() => onSelect(asset)}
            className="w-full mt-2 px-3 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
          >
            Select
          </button>
        )}
      </div>
    </div>
  );
};

export default AssetThumbnail;