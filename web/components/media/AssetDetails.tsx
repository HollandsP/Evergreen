import React from 'react';
import {
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  CalendarIcon,
  ComputerDesktopIcon,
  CurrencyDollarIcon,
  ClockIcon,
  TagIcon,
  DocumentTextIcon,
  CloudArrowDownIcon,
  TrashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

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
    model?: string;
    settings?: Record<string, any>;
  };
}

interface AssetDetailsProps {
  asset: MediaAsset | null;
  onDownload?: (asset: MediaAsset) => void;
  onDelete?: (assetId: string) => void;
  onRegenerate?: (asset: MediaAsset) => void;
  onClose?: () => void;
  className?: string;
}

export const AssetDetails: React.FC<AssetDetailsProps> = ({
  asset,
  onDownload,
  onDelete,
  onRegenerate,
  onClose,
  className,
}) => {
  if (!asset) {
    return (
      <div className={cn('bg-zinc-900 border border-zinc-700 rounded-lg p-6', className)}>
        <div className="text-center text-zinc-400">
          <PhotoIcon className="mx-auto h-12 w-12 mb-3" />
          <p className="text-sm">Select an asset to view details</p>
        </div>
      </div>
    );
  }

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
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatCost = (cost?: number): string => {
    if (!cost) return 'N/A';
    return `$${cost.toFixed(4)}`;
  };

  const formatDate = (date: Date): string => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const formatDimensions = (width?: number, height?: number): string => {
    if (!width || !height) return 'N/A';
    return `${width} × ${height}`;
  };

  const IconComponent = getAssetIcon(asset.type);

  return (
    <div className={cn('bg-zinc-900 border border-zinc-700 rounded-lg overflow-hidden', className)}>
      {/* Header */}
      <div className="bg-zinc-800 px-6 py-4 border-b border-zinc-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <IconComponent className="h-6 w-6 text-zinc-400 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-white truncate">
                {asset.name}
              </h3>
              <p className="text-sm text-zinc-400">
                {asset.sceneName} • {asset.type.toUpperCase()}
              </p>
            </div>
          </div>
          
          {onClose && (
            <button
              onClick={onClose}
              className="text-zinc-400 hover:text-white transition-colors"
            >
              <span className="sr-only">Close</span>
              ×
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Preview */}
        <div className="aspect-video bg-zinc-800 rounded-lg overflow-hidden">
          {asset.type === 'image' && (
            <img
              src={asset.url}
              alt={asset.name}
              className="w-full h-full object-contain"
            />
          )}
          {asset.type === 'video' && (
            <video
              src={asset.url}
              controls
              className="w-full h-full"
              preload="metadata"
            />
          )}
          {asset.type === 'audio' && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <SpeakerWaveIcon className="mx-auto h-16 w-16 text-zinc-400 mb-4" />
                <audio src={asset.url} controls className="w-full max-w-md" />
              </div>
            </div>
          )}
        </div>

        {/* Basic Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-300 flex items-center">
              <TagIcon className="h-4 w-4 mr-2" />
              Basic Information
            </h4>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-400">File Size:</span>
                <span className="text-white">{formatFileSize(asset.size)}</span>
              </div>
              
              {asset.duration && (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Duration:</span>
                  <span className="text-white">{formatDuration(asset.duration)}</span>
                </div>
              )}
              
              {asset.metadata?.width && asset.metadata?.height && (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Dimensions:</span>
                  <span className="text-white">
                    {formatDimensions(asset.metadata.width, asset.metadata.height)}
                  </span>
                </div>
              )}
              
              {asset.metadata?.format && (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Format:</span>
                  <span className="text-white">{asset.metadata.format.toUpperCase()}</span>
                </div>
              )}
              
              <div className="flex justify-between">
                <span className="text-zinc-400">Created:</span>
                <span className="text-white">{formatDate(asset.createdAt)}</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-300 flex items-center">
              <ComputerDesktopIcon className="h-4 w-4 mr-2" />
              Generation Details
            </h4>
            
            <div className="space-y-2 text-sm">
              {asset.metadata?.provider && (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Provider:</span>
                  <span className="text-white">{asset.metadata.provider}</span>
                </div>
              )}
              
              {asset.metadata?.model && (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Model:</span>
                  <span className="text-white">{asset.metadata.model}</span>
                </div>
              )}
              
              {asset.metadata?.cost && (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Cost:</span>
                  <span className="text-white">{formatCost(asset.metadata.cost)}</span>
                </div>
              )}
              
              <div className="flex justify-between">
                <span className="text-zinc-400">Scene ID:</span>
                <span className="text-white font-mono text-xs">{asset.sceneId}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Original Prompt */}
        {asset.metadata?.prompt && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-300 flex items-center">
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Original Prompt
            </h4>
            <div className="bg-zinc-800 rounded-lg p-4">
              <p className="text-sm text-zinc-300 leading-relaxed">
                "{asset.metadata.prompt}"
              </p>
            </div>
          </div>
        )}

        {/* Generation Settings */}
        {asset.metadata?.settings && Object.keys(asset.metadata.settings).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-zinc-300 flex items-center">
              <ComputerDesktopIcon className="h-4 w-4 mr-2" />
              Generation Settings
            </h4>
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                {Object.entries(asset.metadata.settings).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-zinc-400 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}:
                    </span>
                    <span className="text-zinc-300">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3 pt-4 border-t border-zinc-700">
          {onDownload && (
            <button
              onClick={() => onDownload(asset)}
              className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
            >
              <CloudArrowDownIcon className="h-4 w-4 mr-2" />
              Download
            </button>
          )}
          
          {onRegenerate && (
            <button
              onClick={() => onRegenerate(asset)}
              className="flex items-center px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Regenerate
            </button>
          )}
          
          {onDelete && (
            <button
              onClick={() => onDelete(asset.id)}
              className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
            >
              <TrashIcon className="h-4 w-4 mr-2" />
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssetDetails;