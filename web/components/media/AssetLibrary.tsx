import React, { useState, useEffect, useRef } from 'react';
import { 
  FolderIcon,
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  CloudArrowDownIcon,
  TrashIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  SparklesIcon,
  ArrowUpTrayIcon,
  PlusIcon,
  ArrowPathIcon,
  EllipsisVerticalIcon,
  CheckIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import AssetThumbnail from './AssetThumbnail';
import AssetDetails from './AssetDetails';
import GenerateAssetModal from './GenerateAssetModal';

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
   * Callback when an asset is regenerated
   */
  onAssetRegenerate?: (asset: MediaAsset) => void;
  
  /**
   * Callback when a new asset is uploaded
   */
  onAssetUpload?: (files: FileList, sceneId?: string) => void;
  
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
  onAssetRegenerate,
  onAssetUpload,
  className,
  compact = false,
}) => {
  const [sceneFolders, setSceneFolders] = useState<SceneFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'image' | 'video' | 'audio'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<MediaAsset | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generationAssetType, setGenerationAssetType] = useState<'image' | 'video' | 'audio'>('image');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showBatchActions, setShowBatchActions] = useState(false);
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set());
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
            thumbnailUrl: imageData[scene.id].url,
            size: 0,
            sceneId: scene.id,
            sceneName: scene.metadata?.sceneType || `Scene ${scene.id}`,
            createdAt: new Date(),
            metadata: {
              prompt: imageData[scene.id].prompt,
              provider: imageData[scene.id].provider,
              cost: imageData[scene.id].cost,
              model: imageData[scene.id].model,
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
            size: 0,
            duration: audioData[scene.id].duration,
            sceneId: scene.id,
            sceneName: scene.metadata?.sceneType || `Scene ${scene.id}`,
            createdAt: new Date(),
            metadata: {
              prompt: audioData[scene.id].text,
              provider: 'ElevenLabs',
              cost: audioData[scene.id].cost,
              model: audioData[scene.id].model,
            },
          });
        }
        
        // Add video assets
        if (videoData[scene.id]) {
          assets.push({
            id: `${scene.id}-video`,
            name: `Scene ${scene.id} Video`,
            type: 'video',
            url: videoData[scene.id].url || videoData[scene.id],
            size: 0,
            sceneId: scene.id,
            sceneName: scene.metadata?.sceneType || `Scene ${scene.id}`,
            createdAt: new Date(),
            metadata: {
              prompt: videoData[scene.id].prompt,
              provider: 'RunwayML',
              cost: videoData[scene.id].cost,
              model: videoData[scene.id].model,
            },
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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && onAssetUpload) {
      onAssetUpload(files, selectedFolder || sceneId);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0 && onAssetUpload) {
      onAssetUpload(files, selectedFolder || sceneId);
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleGenerate = async (prompt: string, settings: any) => {
    setIsGenerating(true);
    try {
      // TODO: Implement actual AI generation API calls
      console.log('Generating', generationAssetType, 'with prompt:', prompt, 'settings:', settings);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Refresh assets after generation
      await loadAssets();
      setShowGenerateModal(false);
    } catch (error) {
      console.error('Generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleBatchDelete = () => {
    if (selectedAssets.size === 0) return;
    
    selectedAssets.forEach(assetId => {
      if (onAssetDelete) {
        onAssetDelete(assetId);
      }
    });
    
    setSelectedAssets(new Set());
    setShowBatchActions(false);
    loadAssets();
  };

  const toggleAssetSelection = (assetId: string) => {
    const newSelected = new Set(selectedAssets);
    if (newSelected.has(assetId)) {
      newSelected.delete(assetId);
    } else {
      newSelected.add(assetId);
    }
    setSelectedAssets(newSelected);
  };

  const filteredAssets = sceneFolders
    .filter(folder => showAllScenes || !sceneId || folder.id === sceneId)
    .flatMap(folder => folder.assets)
    .filter(asset => {
      const matchesSearch = asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          asset.sceneName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (asset.metadata?.prompt && asset.metadata.prompt.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesType = typeFilter === 'all' || asset.type === typeFilter;
      return matchesSearch && matchesType;
    });

  const currentFolder = selectedFolder ? sceneFolders.find(f => f.id === selectedFolder) : null;
  const assetsToShow = showAllScenes ? filteredAssets : (currentFolder?.assets.filter(asset => {
    const matchesSearch = asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        asset.sceneName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        (asset.metadata?.prompt && asset.metadata.prompt.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = typeFilter === 'all' || asset.type === typeFilter;
    return matchesSearch && matchesType;
  }) || []);

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className={cn('bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden', className)}>
      {/* Header with AI-first design */}
      <div className="bg-zinc-900 border-b border-zinc-800 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <h3 className="text-lg font-semibold text-white">Asset Library</h3>
            {selectedFolder && (
              <span className="ml-3 text-sm text-zinc-400">
                • {sceneFolders.find(f => f.id === selectedFolder)?.name}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {selectedAssets.size > 0 && (
              <div className="flex items-center space-x-2 mr-4">
                <span className="text-sm text-zinc-400">
                  {selectedAssets.size} selected
                </span>
                <button
                  onClick={handleBatchDelete}
                  className="text-sm text-red-400 hover:text-red-300"
                >
                  Delete Selected
                </button>
                <button
                  onClick={() => setSelectedAssets(new Set())}
                  className="text-sm text-zinc-400 hover:text-zinc-300"
                >
                  Clear
                </button>
              </div>
            )}
            
            <button
              onClick={loadAssets}
              className="p-2 text-zinc-400 hover:text-white transition-colors"
              title="Refresh"
            >
              <ArrowPathIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
        
        {/* AI Generation Buttons (Primary) */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <button
            onClick={() => {
              setGenerationAssetType('image');
              setShowGenerateModal(true);
            }}
            className="flex items-center justify-center px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors group"
          >
            <SparklesIcon className="h-5 w-5 mr-2 group-hover:animate-pulse" />
            <PhotoIcon className="h-4 w-4 mr-2" />
            Generate Image
          </button>
          
          <button
            onClick={() => {
              setGenerationAssetType('video');
              setShowGenerateModal(true);
            }}
            className="flex items-center justify-center px-4 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors group"
          >
            <SparklesIcon className="h-5 w-5 mr-2 group-hover:animate-pulse" />
            <VideoCameraIcon className="h-4 w-4 mr-2" />
            Generate Video
          </button>
          
          <button
            onClick={() => {
              setGenerationAssetType('audio');
              setShowGenerateModal(true);
            }}
            className="flex items-center justify-center px-4 py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors group"
          >
            <SparklesIcon className="h-5 w-5 mr-2 group-hover:animate-pulse" />
            <SpeakerWaveIcon className="h-4 w-4 mr-2" />
            Generate Audio
          </button>
        </div>

        {/* Upload Section (Secondary) */}
        <div className="flex items-center space-x-3 mb-4">
          <div
            className={cn(
              'flex-1 relative border-2 border-dashed rounded-lg p-3 transition-colors',
              isDragOver ? 'border-blue-500 bg-blue-500/10' : 'border-zinc-600 hover:border-zinc-500',
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,video/*,audio/*"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex items-center justify-center">
              <ArrowUpTrayIcon className="h-4 w-4 text-zinc-400 mr-2" />
              <span className="text-sm text-zinc-400">
                {isDragOver ? 'Drop files here' : 'Upload files or drag and drop'}
              </span>
            </div>
          </div>
        </div>
        
        {/* Search and Filter */}
        <div className="flex items-center space-x-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search assets, prompts..."
              className="w-full pl-9 pr-3 py-2 bg-zinc-800 border border-zinc-600 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div className="relative">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as any)}
              className="appearance-none bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="image">Images</option>
              <option value="video">Videos</option>
              <option value="audio">Audio</option>
            </select>
            <FunnelIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" />
          </div>
          
          {showAllScenes && (
            <div className="relative">
              <select
                value={selectedFolder || 'all'}
                onChange={(e) => setSelectedFolder(e.target.value === 'all' ? null : e.target.value)}
                className="appearance-none bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Scenes</option>
                {sceneFolders.map(folder => (
                  <option key={folder.id} value={folder.id}>
                    {folder.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="flex h-[600px]">
        {/* Scene Folders Sidebar */}
        {showAllScenes && !compact && (
          <div className="w-64 border-r border-zinc-800 bg-zinc-900">
            <div className="p-3 bg-zinc-800 border-b border-zinc-700">
              <h4 className="text-sm font-medium text-zinc-300">Scenes</h4>
            </div>
            <div className="max-h-full overflow-y-auto">
              <button
                onClick={() => setSelectedFolder(null)}
                className={cn(
                  'w-full flex items-center px-3 py-2 text-left hover:bg-zinc-800',
                  selectedFolder === null ? 'bg-zinc-800 border-r-2 border-blue-500' : '',
                )}
              >
                <FolderIcon className="h-4 w-4 text-zinc-400 mr-2" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    All Scenes
                  </p>
                  <p className="text-xs text-zinc-500">
                    {filteredAssets.length} assets
                  </p>
                </div>
              </button>
              
              {sceneFolders.map(folder => (
                <button
                  key={folder.id}
                  onClick={() => setSelectedFolder(folder.id)}
                  className={cn(
                    'w-full flex items-center px-3 py-2 text-left hover:bg-zinc-800',
                    selectedFolder === folder.id ? 'bg-zinc-800 border-r-2 border-blue-500' : '',
                  )}
                >
                  <FolderIcon className="h-4 w-4 text-zinc-400 mr-2" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {folder.name}
                    </p>
                    <p className="text-xs text-zinc-500">
                      {folder.assets.length} assets
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 flex">
          {/* Assets Grid */}
          <div className="flex-1 p-4">
            {assetsToShow.length > 0 ? (
              <div className={cn(
                'grid gap-4',
                compact ? 'grid-cols-2 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
              )}>
                {assetsToShow.map(asset => (
                  <div key={asset.id} className="relative">
                    {/* Selection checkbox */}
                    <div className="absolute top-2 left-2 z-10">
                      <button
                        onClick={() => toggleAssetSelection(asset.id)}
                        className={cn(
                          'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                          selectedAssets.has(asset.id) 
                            ? 'bg-blue-500 border-blue-500' 
                            : 'border-zinc-400 hover:border-zinc-300 bg-black bg-opacity-50',
                        )}
                      >
                        {selectedAssets.has(asset.id) && (
                          <CheckIcon className="w-3 h-3 text-white" />
                        )}
                      </button>
                    </div>
                    
                    <AssetThumbnail
                      asset={asset}
                      onPreview={setPreviewAsset}
                      onDownload={(asset) => {
                        const a = document.createElement('a');
                        a.href = asset.url;
                        a.download = asset.name;
                        a.click();
                      }}
                      onDelete={onAssetDelete}
                      onRegenerate={onAssetRegenerate}
                      onSelect={() => setSelectedAsset(asset)}
                      compact={compact}
                      className="cursor-pointer"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <SparklesIcon className="mx-auto h-12 w-12 text-zinc-400 mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">No assets found</h3>
                <p className="text-zinc-400 mb-6">
                  {searchQuery || typeFilter !== 'all'
                    ? 'Try adjusting your search or filter.'
                    : 'Generate or upload assets to get started.'}
                </p>
                
                {!searchQuery && typeFilter === 'all' && (
                  <div className="flex justify-center space-x-3">
                    <button
                      onClick={() => {
                        setGenerationAssetType('image');
                        setShowGenerateModal(true);
                      }}
                      className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                    >
                      <SparklesIcon className="h-4 w-4 mr-2" />
                      Generate Image
                    </button>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg transition-colors"
                    >
                      <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                      Upload Files
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Asset Details Panel */}
          {!compact && (
            <div className="w-80 border-l border-zinc-800 bg-zinc-900">
              <AssetDetails
                asset={selectedAsset}
                onDownload={(asset) => {
                  const a = document.createElement('a');
                  a.href = asset.url;
                  a.download = asset.name;
                  a.click();
                }}
                onDelete={onAssetDelete}
                onRegenerate={onAssetRegenerate}
                onClose={() => setSelectedAsset(null)}
                className="h-full border-0 rounded-none"
              />
            </div>
          )}
        </div>
      </div>

      {/* Generation Modal */}
      <GenerateAssetModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        assetType={generationAssetType}
        sceneId={selectedFolder || sceneId}
        sceneName={selectedFolder ? sceneFolders.find(f => f.id === selectedFolder)?.name : undefined}
        onGenerate={handleGenerate}
        isGenerating={isGenerating}
      />

      {/* Preview Modal */}
      {previewAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-zinc-900 rounded-lg max-w-4xl max-h-[90vh] overflow-hidden border border-zinc-700">
            <div className="flex items-center justify-between p-4 border-b border-zinc-700">
              <h3 className="text-lg font-semibold text-white">{previewAsset.name}</h3>
              <button
                onClick={() => setPreviewAsset(null)}
                className="text-zinc-400 hover:text-white transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
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
                  <SpeakerWaveIcon className="mx-auto h-16 w-16 text-zinc-400 mb-4" />
                  <audio src={previewAsset.url} controls className="w-full max-w-md" />
                </div>
              )}
              
              {/* Preview metadata */}
              {previewAsset.metadata?.prompt && (
                <div className="mt-4 p-3 bg-zinc-800 rounded">
                  <p className="text-xs text-zinc-400 mb-1">Original Prompt:</p>
                  <p className="text-sm text-zinc-300">"{previewAsset.metadata.prompt}"</p>
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