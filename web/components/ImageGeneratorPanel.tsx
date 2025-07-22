import React, { useState, useCallback } from 'react';
import { PlusIcon, SparklesIcon, PhotoIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import { GenerationRequest, ProviderConfig, PipelineSettings } from '@/types';
import { validatePrompt, cn } from '@/lib/utils';

interface ImageGeneratorPanelProps {
  onGenerate: (request: GenerationRequest) => void;
  isGenerating: boolean;
  providers: ProviderConfig[];
  settings: PipelineSettings;
  onSettingsChange: (settings: Partial<PipelineSettings>) => void;
}

const DEFAULT_PROMPTS = [
  "A majestic mountain landscape at golden hour with misty valleys",
  "A futuristic city skyline with flying cars and neon lights",
  "An underwater scene with colorful coral reefs and tropical fish",
  "A cozy library with floating books and magical glowing orbs",
  "A steampunk workshop with intricate gears and brass machinery"
];

const ImageGeneratorPanel: React.FC<ImageGeneratorPanelProps> = ({
  onGenerate,
  isGenerating,
  providers,
  settings,
  onSettingsChange,
}) => {
  const [prompt, setPrompt] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<'dalle3'>('dalle3');
  const [showSettings, setShowSettings] = useState(false);
  const [promptError, setPromptError] = useState<string | null>(null);

  const selectedProviderConfig = providers.find(p => p.name === selectedProvider);
  const availableProviders = providers.filter(p => p.available);

  const handlePromptChange = useCallback((value: string) => {
    setPrompt(value);
    if (promptError) {
      const validation = validatePrompt(value);
      if (validation.valid) {
        setPromptError(null);
      }
    }
  }, [promptError]);

  const handleGenerate = useCallback(() => {
    const validation = validatePrompt(prompt);
    if (!validation.valid) {
      setPromptError(validation.error!);
      return;
    }

    const request: GenerationRequest = {
      prompt: prompt.trim(),
      provider: selectedProvider,
      settings: {
        imageSize: settings.imageSize,
        videoDuration: settings.videoDuration,
        quality: settings.quality,
        seed: settings.seed,
      },
    };

    onGenerate(request);
  }, [prompt, selectedProvider, settings, onGenerate]);

  const usePromptExample = useCallback((examplePrompt: string) => {
    setPrompt(examplePrompt);
    setPromptError(null);
  }, []);

  const estimatedCost = selectedProviderConfig
    ? selectedProviderConfig.cost.image + selectedProviderConfig.cost.video
    : 0;

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="h-5 w-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">AI Video Generator</h2>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn-outline p-2"
            title="Settings"
          >
            <Cog6ToothIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="card-body space-y-6">
        {/* Provider Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            AI Provider
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {availableProviders.map((provider) => (
              <button
                key={provider.name}
                onClick={() => setSelectedProvider(provider.name as 'dalle3')}
                className={cn(
                  'p-4 text-left border rounded-lg transition-all duration-200',
                  selectedProvider === provider.name
                    ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{provider.displayName}</h3>
                  <span className="text-xs text-gray-500">
                    ${(provider.cost.image + provider.cost.video).toFixed(4)}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{provider.description}</p>
                <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                  <span>Max: {provider.capabilities.maxImageSize}</span>
                  <span>Duration: {provider.capabilities.maxVideoDuration}s</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Prompt Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={prompt}
            onChange={(e) => handlePromptChange(e.target.value)}
            placeholder="Describe the video you want to create..."
            className={cn(
              'textarea h-32',
              promptError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
            )}
            disabled={isGenerating}
          />
          {promptError && (
            <p className="mt-1 text-sm text-red-600">{promptError}</p>
          )}
          <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
            <span>{prompt.length} / 4000 characters</span>
            <span>Estimated cost: ${estimatedCost.toFixed(4)}</span>
          </div>
        </div>

        {/* Prompt Examples */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Example Prompts
          </label>
          <div className="flex flex-wrap gap-2">
            {DEFAULT_PROMPTS.map((example, index) => (
              <button
                key={index}
                onClick={() => usePromptExample(example)}
                className="inline-flex items-center px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors duration-200"
                disabled={isGenerating}
              >
                <PhotoIcon className="h-3 w-3 mr-1" />
                {example.substring(0, 30)}...
              </button>
            ))}
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="border-t pt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-4">Advanced Settings</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Image Size
                </label>
                <select
                  value={settings.imageSize}
                  onChange={(e) => onSettingsChange({ imageSize: e.target.value })}
                  className="input text-sm"
                  disabled={isGenerating}
                >
                  {selectedProviderConfig?.capabilities.qualityOptions.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Video Duration
                </label>
                <select
                  value={settings.videoDuration}
                  onChange={(e) => onSettingsChange({ videoDuration: parseInt(e.target.value) })}
                  className="input text-sm"
                  disabled={isGenerating}
                >
                  <option value={4}>4 seconds</option>
                  <option value={8}>8 seconds</option>
                  <option value={10}>10 seconds</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Quality
                </label>
                <select
                  value={settings.quality}
                  onChange={(e) => onSettingsChange({ quality: e.target.value })}
                  className="input text-sm"
                  disabled={isGenerating}
                >
                  <option value="standard">Standard</option>
                  <option value="high">High</option>
                  <option value="ultra">Ultra</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Seed (Optional)
                </label>
                <input
                  type="number"
                  value={settings.seed || ''}
                  onChange={(e) => onSettingsChange({ 
                    seed: e.target.value ? parseInt(e.target.value) : undefined 
                  })}
                  placeholder="Random"
                  className="input text-sm"
                  disabled={isGenerating}
                />
              </div>
            </div>

            <div className="mt-4 flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.autoDownload}
                  onChange={(e) => onSettingsChange({ autoDownload: e.target.checked })}
                  className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                />
                <span className="ml-2 text-xs text-gray-600">Auto-download results</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.notifications}
                  onChange={(e) => onSettingsChange({ notifications: e.target.checked })}
                  className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                />
                <span className="ml-2 text-xs text-gray-600">Browser notifications</span>
              </label>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim() || availableProviders.length === 0}
          className={cn(
            'w-full btn-primary py-3 text-base font-medium',
            isGenerating ? 'opacity-50 cursor-not-allowed' : ''
          )}
        >
          {isGenerating ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Generating...
            </div>
          ) : (
            <div className="flex items-center justify-center">
              <PlusIcon className="h-5 w-5 mr-2" />
              Generate Video
            </div>
          )}
        </button>

        {availableProviders.length === 0 && (
          <div className="text-center py-4">
            <p className="text-sm text-gray-500">No AI providers are currently available.</p>
            <p className="text-xs text-gray-400 mt-1">Please check your API keys and try again.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageGeneratorPanel;