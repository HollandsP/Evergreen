import React, { useState, useEffect } from 'react';
import { 
  FolderIcon,
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  CloudArrowDownIcon,
  TrashIcon,
  EyeIcon,
  DocumentDuplicateIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
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
  };
}

interface SceneFolder {
  id: string;
  name: string;
  assets: MediaAsset[];
  totalSize: number;
}

interface AssetLibraryProps {
  /**
   * The current scene ID to filter assets
   */
  sceneId?: string;
  
  /**
   * Whether to show all scenes or just the current one
   */
  showAllScenes?: boolean;
  
  /**
   * Callback when an asset is selected
   */
  onAssetSelect?: (asset: MediaAsset) => void;
  
  /**
   * Callback when an asset is deleted
   */
  onAssetDelete?: (assetId: string) => void;
  
  /**
   * Additional CSS classes
   */
  className?: string;
  
  /**
   * Whether to show the asset browser in compact mode
   */
  compact?: boolean;
}

export const AssetLibrary: React.FC<AssetLibraryProps> = ({
  sceneId,
  showAllScenes = false,
  onAssetSelect,
  onAssetDelete,
  className,
  compact = false,
}) => {
  const [sceneFolders, setSceneFolders] = useState<SceneFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'image' | 'video' | 'audio'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);

  useEffect(() => {
    loadAssets();
  }, [sceneId, showAllScenes]);

  const loadAssets = async () => {
    setIsLoading(true);
    try {
      // Load assets from localStorage and organize by scene
      const scriptData = JSON.parse(localStorage.getItem('scriptData') || '{}');
      const imageData = JSON.parse(localStorage.getItem('imageData') || '{}');
      const audioData = JSON.parse(localStorage.getItem('audioData') || '{}');
      const videoData = JSON.parse(localStorage.getItem('videoData') || '{}');
      
      const scenes = scriptData.scenes || [];
      const folders: SceneFolder[] = [];
      
      for (const scene of scenes) {
        const assets: MediaAsset[] = [];
        
        // Add image assets
        if (imageData[scene.id]?.url) {
          assets.push({
            id: `${scene.id}-image`,
            name: `Scene ${scene.id} Image`,
            type: 'image',
            url: imageData[scene.id].url,
            thumbnailUrl: imageData[scene.id].url, // Images are their own thumbnails
            size: 0, // Would need to fetch actual size
            sceneId: scene.id,
            sceneName: scene.metadata?.sceneType || `Scene ${scene.id}`,
            createdAt: new Date(),
            metadata: {
              prompt: imageData[scene.id].prompt,
              provider: imageData[scene.id].provider,
            },
          });
        }
        
        // Add audio assets
        if (audioData[scene.id]?.url) {
          assets.push({
            id: `${scene.id}-audio`,
            name: `Scene ${scene.id} Audio`,
            type: 'audio',
            url: audioData[scene.id].url,
            size: 0, // Would need to fetch actual size
            duration: audioData[scene.id].duration,
            sceneId: scene.id,
            sceneName: scene.metadata?.sceneType || `Scene ${scene.id}`,
            createdAt: new Date(),
          });
        }
        
        // Add video assets
        if (videoData[scene.id]) {
          assets.push({
            id: `${scene.id}-video`,
            name: `Scene ${scene.id} Video`,
            type: 'video',
            url: videoData[scene.id],
            size: 0, // Would need to fetch actual size
            sceneId: scene.id,
            sceneName: scene.metadata?.sceneType || `Scene ${scene.id}`,
            createdAt: new Date(),
          });
        }
        
        if (assets.length > 0) {
          folders.push({
            id: scene.id,
            name: scene.metadata?.sceneType || `Scene ${scene.id}`,
            assets,
            totalSize: assets.reduce((sum, asset) => sum + asset.size, 0),
          });
        }
      }
      
      setSceneFolders(folders);
      
      // Auto-select the current scene folder if specified
      if (sceneId && folders.find(f => f.id === sceneId)) {
        setSelectedFolder(sceneId);
      } else if (folders.length > 0) {
        setSelectedFolder(folders[0].id);
      }
    } catch (error) {
      console.error('Error loading assets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getAssetIcon = (type: string) => {
    switch (type) {
      case 'image': return PhotoIcon;
      case 'video': return VideoCameraIcon;
      case 'audio': return SpeakerWaveIcon;
      default: return DocumentDuplicateIcon;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '- KB';
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

  const filteredAssets = sceneFolders
    .filter(folder => showAllScenes || !sceneId || folder.id === sceneId)
    .flatMap(folder => folder.assets)
    .filter(asset => {
      const matchesSearch = asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          asset.sceneName.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = typeFilter === 'all' || asset.type === typeFilter;
      return matchesSearch && matchesType;
    });

  const currentFolder = selectedFolder ? sceneFolders.find(f => f.id === selectedFolder) : null;
  const assetsToShow = showAllScenes ? filteredAssets : (currentFolder?.assets || []);

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className={cn('bg-white border border-gray-200 rounded-lg', className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Asset Library</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadAssets}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Refresh
            </button>
          </div>
        </div>
        
        {/* Search and Filter */}
        <div className="flex items-center space-x-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search assets..."
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="relative">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as any)}
              className="appearance-none bg-white border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="image">Images</option>
              <option value="video">Videos</option>
              <option value="audio">Audio</option>
            </select>
            <FunnelIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Scene Folders Sidebar */}
        {showAllScenes && !compact && (
          <div className="w-64 border-r border-gray-200">
            <div className="p-3 bg-gray-50 border-b border-gray-200">
              <h4 className="text-sm font-medium text-gray-700">Scenes</h4>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {sceneFolders.map(folder => (
                <button
                  key={folder.id}
                  onClick={() => setSelectedFolder(folder.id)}
                  className={cn(
                    'w-full flex items-center px-3 py-2 text-left hover:bg-gray-50',
                    selectedFolder === folder.id ? 'bg-blue-50 border-r-2 border-blue-500' : '',
                  )}
                >
                  <FolderIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {folder.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {folder.assets.length} assets • {formatFileSize(folder.totalSize)}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Assets Grid */}
        <div className="flex-1">
          <div className={cn(
            'grid gap-4 p-4',
            compact ? 'grid-cols-2 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
          )}>
            {assetsToShow.map(asset => {
              const IconComponent = getAssetIcon(asset.type);
              
              return (
                <div
                  key={asset.id}
                  className="group relative bg-gray-50 rounded-lg overflow-hidden hover:bg-gray-100 transition-colors"
                >
                  {/* Thumbnail */}
                  <div className="aspect-video bg-gray-200 relative">
                    {asset.thumbnailUrl ? (
                      <img
                        src={asset.thumbnailUrl}
                        alt={asset.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <IconComponent className="h-8 w-8 text-gray-400" />
                      </div>
                    )}
                    
                    {/* Overlay actions */}
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setPreviewAsset(asset)}
                          className="p-2 bg-white rounded-full text-gray-700 hover:bg-gray-100"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                        <a
                          href={asset.url}
                          download={asset.name}
                          className="p-2 bg-white rounded-full text-gray-700 hover:bg-gray-100"
                        >
                          <CloudArrowDownIcon className="h-4 w-4" />
                        </a>
                        {onAssetSelect && (
                          <button
                            onClick={() => onAssetSelect(asset)}
                            className="p-2 bg-white rounded-full text-gray-700 hover:bg-gray-100"
                          >
                            <DocumentDuplicateIcon className="h-4 w-4" />
                          </button>
                        )}
                        {onAssetDelete && (
                          <button
                            onClick={() => onAssetDelete(asset.id)}
                            className="p-2 bg-white rounded-full text-red-600 hover:bg-gray-100"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Duration badge for videos/audio */}
                    {asset.duration && (
                      <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                        {formatDuration(asset.duration)}
                      </div>
                    )}
                  </div>

                  {/* Asset info */}
                  <div className="p-3">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {asset.name}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {asset.sceneName}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className={cn(
                        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                        asset.type === 'image' ? 'bg-green-100 text-green-800' :
                        asset.type === 'video' ? 'bg-purple-100 text-purple-800' :
                        'bg-blue-100 text-blue-800',
                      )}>
                        {asset.type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatFileSize(asset.size)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {assetsToShow.length === 0 && (
            <div className="text-center py-12">
              <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No assets found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchQuery || typeFilter !== 'all'
                  ? 'Try adjusting your search or filter.'
                  : 'Generate some assets to see them here.'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Preview Modal */}
      {previewAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">{previewAsset.name}</h3>
              <button
                onClick={() => setPreviewAsset(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Close</span>
                ×
              </button>
            </div>
            <div className="p-4">
              {previewAsset.type === 'image' && (
                <img
                  src={previewAsset.url}
                  alt={previewAsset.name}
                  className="max-w-full max-h-[60vh] object-contain mx-auto"
                />
              )}
              {previewAsset.type === 'video' && (
                <video
                  src={previewAsset.url}
                  controls
                  className="max-w-full max-h-[60vh] mx-auto"
                />
              )}
              {previewAsset.type === 'audio' && (
                <div className="text-center py-8">
                  <SpeakerWaveIcon className="mx-auto h-16 w-16 text-gray-400" />
                  <audio src={previewAsset.url} controls className="mt-4" />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetLibrary;