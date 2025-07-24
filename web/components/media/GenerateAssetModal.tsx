import React, { useState, useEffect } from 'react';
import {
  XMarkIcon,
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  SparklesIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

type AssetType = 'image' | 'video' | 'audio';

interface GenerationSettings {
  // Image settings
  imageSize?: '1024x1024' | '1024x1792' | '1792x1024';
  imageQuality?: 'standard' | 'hd';
  imageStyle?: 'vivid' | 'natural';
  
  // Video settings
  videoDuration?: 5 | 10;
  videoAspectRatio?: '16:9' | '9:16' | '1:1';
  cameraMovement?: 'static' | 'slow_pan' | 'fast_pan' | 'zoom_in' | 'zoom_out';
  motionIntensity?: 'low' | 'medium' | 'high';
  
  // Audio settings
  voiceId?: string;
  stability?: number;
  similarityBoost?: number;
  style?: number;
  speakerBoost?: boolean;
}

interface GenerateAssetModalProps {
  isOpen: boolean;
  onClose: () => void;
  assetType: AssetType;
  sceneId?: string;
  sceneName?: string;
  initialPrompt?: string;
  onGenerate: (prompt: string, settings: GenerationSettings) => Promise<void>;
  isGenerating?: boolean;
  className?: string;
}

const VOICE_OPTIONS = [
  { id: 'rachel', name: 'Rachel (Calm Female)' },
  { id: 'drew', name: 'Drew (Deep Male)' },
  { id: 'clyde', name: 'Clyde (Warm Male)' },
  { id: 'bella', name: 'Bella (Young Female)' },
  { id: 'josh', name: 'Josh (Professional Male)' },
  { id: 'arnold', name: 'Arnold (Authoritative Male)' },
  { id: 'adam', name: 'Adam (Narrative Male)' },
  { id: 'sam', name: 'Sam (Clear Male)' },
];

export const GenerateAssetModal: React.FC<GenerateAssetModalProps> = ({
  isOpen,
  onClose,
  assetType,
  sceneId,
  sceneName,
  initialPrompt = '',
  onGenerate,
  isGenerating = false,
  className,
}) => {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [settings, setSettings] = useState<GenerationSettings>({
    imageSize: '1024x1024',
    imageQuality: 'standard',
    imageStyle: 'vivid',
    videoDuration: 5,
    videoAspectRatio: '16:9',
    cameraMovement: 'static',
    motionIntensity: 'medium',
    voiceId: 'rachel',
    stability: 0.5,
    similarityBoost: 0.75,
    style: 0.5,
    speakerBoost: true,
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    if (initialPrompt !== prompt) {
      setPrompt(initialPrompt);
    }
  }, [initialPrompt]);

  if (!isOpen) return null;

  const getAssetIcon = (type: AssetType) => {
    switch (type) {
      case 'image': return PhotoIcon;
      case 'video': return VideoCameraIcon;
      case 'audio': return SpeakerWaveIcon;
    }
  };

  const getAssetTitle = (type: AssetType) => {
    switch (type) {
      case 'image': return 'Generate Image';
      case 'video': return 'Generate Video';
      case 'audio': return 'Generate Audio';
    }
  };

  const getEstimatedCost = () => {
    switch (assetType) {
      case 'image':
        return settings.imageQuality === 'hd' ? '$0.08' : '$0.04';
      case 'video':
        const baseCost = settings.videoDuration === 10 ? 0.08 : 0.04;
        return `$${baseCost.toFixed(2)}`;
      case 'audio':
        const charCount = prompt.length;
        const cost = (charCount * 0.0005).toFixed(4);
        return `$${cost}`;
      default:
        return '$0.00';
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    try {
      await onGenerate(prompt, settings);
      // Don't close modal automatically - let parent handle it
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  const IconComponent = getAssetIcon(assetType);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={cn(
        'bg-zinc-900 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden border border-zinc-700',
        className,
      )}>
        {/* Header */}
        <div className="bg-zinc-800 px-6 py-4 border-b border-zinc-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <IconComponent className="h-6 w-6 text-blue-400 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-white">
                  {getAssetTitle(assetType)}
                </h3>
                {sceneName && (
                  <p className="text-sm text-zinc-400">
                    Scene: {sceneName}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={isGenerating}
              className="text-zinc-400 hover:text-white transition-colors disabled:opacity-50"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Prompt */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-300">
              {assetType === 'audio' ? 'Text to Speak' : 'Prompt'}
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={
                assetType === 'image' ? 'Describe the image you want to generate...' :
                assetType === 'video' ? 'Describe the video scene and motion...' :
                'Enter the text you want to convert to speech...'
              }
              disabled={isGenerating}
              rows={4}
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            />
            <p className="text-xs text-zinc-500">
              {prompt.length} characters • Estimated cost: {getEstimatedCost()}
            </p>
          </div>

          {/* Settings */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-zinc-300">Settings</h4>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center text-xs text-blue-400 hover:text-blue-300"
              >
                <Cog6ToothIcon className="h-4 w-4 mr-1" />
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </button>
            </div>

            {/* Basic Settings */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {assetType === 'image' && (
                <>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Size</label>
                    <select
                      value={settings.imageSize}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        imageSize: e.target.value as any,
                      }))}
                      disabled={isGenerating}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                    >
                      <option value="1024x1024">Square (1024×1024)</option>
                      <option value="1024x1792">Portrait (1024×1792)</option>
                      <option value="1792x1024">Landscape (1792×1024)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Quality</label>
                    <select
                      value={settings.imageQuality}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        imageQuality: e.target.value as any,
                      }))}
                      disabled={isGenerating}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                    >
                      <option value="standard">Standard ($0.04)</option>
                      <option value="hd">HD ($0.08)</option>
                    </select>
                  </div>
                </>
              )}

              {assetType === 'video' && (
                <>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Duration</label>
                    <select
                      value={settings.videoDuration}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        videoDuration: parseInt(e.target.value) as any,
                      }))}
                      disabled={isGenerating}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                    >
                      <option value={5}>5 seconds</option>
                      <option value={10}>10 seconds</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Camera Movement</label>
                    <select
                      value={settings.cameraMovement}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        cameraMovement: e.target.value as any,
                      }))}
                      disabled={isGenerating}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                    >
                      <option value="static">Static</option>
                      <option value="slow_pan">Slow Pan</option>
                      <option value="fast_pan">Fast Pan</option>
                      <option value="zoom_in">Zoom In</option>
                      <option value="zoom_out">Zoom Out</option>
                    </select>
                  </div>
                </>
              )}

              {assetType === 'audio' && (
                <>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Voice</label>
                    <select
                      value={settings.voiceId}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        voiceId: e.target.value,
                      }))}
                      disabled={isGenerating}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {VOICE_OPTIONS.map(voice => (
                        <option key={voice.id} value={voice.id}>
                          {voice.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">
                      Stability: {settings.stability}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={settings.stability}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        stability: parseFloat(e.target.value),
                      }))}
                      disabled={isGenerating}
                      className="w-full"
                    />
                  </div>
                </>
              )}
            </div>

            {/* Advanced Settings */}
            {showAdvanced && (
              <div className="border-t border-zinc-700 pt-4 space-y-4">
                {assetType === 'image' && (
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Style</label>
                    <select
                      value={settings.imageStyle}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        imageStyle: e.target.value as any,
                      }))}
                      disabled={isGenerating}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                    >
                      <option value="vivid">Vivid (more dramatic)</option>
                      <option value="natural">Natural (more realistic)</option>
                    </select>
                  </div>
                )}

                {assetType === 'video' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-zinc-400 mb-1">Motion Intensity</label>
                      <select
                        value={settings.motionIntensity}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          motionIntensity: e.target.value as any,
                        }))}
                        disabled={isGenerating}
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-zinc-400 mb-1">Aspect Ratio</label>
                      <select
                        value={settings.videoAspectRatio}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          videoAspectRatio: e.target.value as any,
                        }))}
                        disabled={isGenerating}
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                      >
                        <option value="16:9">Landscape (16:9)</option>
                        <option value="9:16">Portrait (9:16)</option>
                        <option value="1:1">Square (1:1)</option>
                      </select>
                    </div>
                  </div>
                )}

                {assetType === 'audio' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-zinc-400 mb-1">
                        Similarity Boost: {settings.similarityBoost}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={settings.similarityBoost}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          similarityBoost: parseFloat(e.target.value),
                        }))}
                        disabled={isGenerating}
                        className="w-full"
                      />
                    </div>
                    <div className="flex items-center">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={settings.speakerBoost}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            speakerBoost: e.target.checked,
                          }))}
                          disabled={isGenerating}
                          className="mr-2"
                        />
                        <span className="text-xs text-zinc-400">Speaker Boost</span>
                      </label>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-zinc-800 px-6 py-4 border-t border-zinc-700">
          <div className="flex items-center justify-between">
            <div className="text-xs text-zinc-400">
              Estimated cost: <span className="text-white font-medium">{getEstimatedCost()}</span>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                disabled={isGenerating}
                className="px-4 py-2 text-zinc-400 hover:text-white transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerate}
                disabled={!prompt.trim() || isGenerating}
                className="flex items-center px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <ArrowPathIcon className="animate-spin h-4 w-4 mr-2" />
                    Generating...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="h-4 w-4 mr-2" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenerateAssetModal;