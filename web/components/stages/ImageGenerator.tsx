import React, { useState, useEffect } from 'react';
import { 
  PhotoIcon, 
  SparklesIcon, 
  ArrowUpTrayIcon,
  CheckIcon,
  XMarkIcon,
  ArrowPathIcon,
  CloudArrowDownIcon,
} from '@heroicons/react/24/outline';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/20/solid';
import { cn } from '@/lib/utils';
import ImageUploader from '../shared/ImageUploader';
import { generateOptimizedPrompt } from '@/lib/prompt-optimizer';
import PromptEditor from '../shared/PromptEditor';

interface SceneData {
  id: string;
  timestamp: number;
  narration: string;
  onScreenText: string;
  imagePrompt: string;
  metadata: {
    sceneType: string;
    description: string;
    visual: string;
  };
}

interface AudioData {
  sceneId: string;
  url: string;
  duration: number;
  status: 'pending' | 'generating' | 'completed' | 'error';
}

interface ImageData {
  sceneId: string;
  url: string;
  prompt: string;
  provider: 'dalle3' | 'upload';  // Flux.1 removed due to high subscription costs
  status: 'pending' | 'generating' | 'completed' | 'error';
  error?: string;
}

interface ImageGeneratorProps {
  onComplete: () => void;
  projectId?: string;
}

// Using DALL-E 3 as the primary image generation provider
const DALLE3_INFO = { 
  id: 'dalle3', 
  name: 'DALL-E 3', 
  description: 'OpenAI\'s latest model - Professional quality photorealistic images',
  cost: '$0.040 per image (1024x1024) / $0.080 per image (1024x1792)',
};

export const ImageGenerator: React.FC<ImageGeneratorProps> = ({ onComplete, projectId }) => {
  const [scenes, setScenes] = useState<SceneData[]>([]);
  const [audioData, setAudioData] = useState<Record<string, AudioData>>({});
  const [imageData, setImageData] = useState<Record<string, ImageData>>({});
  // Using DALL-E 3 as the only provider (Flux.1 removed due to high subscription costs)
  const provider = 'dalle3' as const;
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingScene, setGeneratingScene] = useState<string | null>(null);
  const [_editingPrompt, _setEditingPrompt] = useState<string | null>(null);
  const [_editedPromptText, _setEditedPromptText] = useState('');
  const [showUploader, setShowUploader] = useState<string | null>(null);
  const [batchGenerate, setBatchGenerate] = useState(true);

  useEffect(() => {
    // Load script and audio data from localStorage
    const scriptDataStr = localStorage.getItem('scriptData');
    const audioDataStr = localStorage.getItem('audioData');
    
    if (scriptDataStr) {
      const scriptData = JSON.parse(scriptDataStr);
      setScenes(scriptData.scenes);
      
      // Initialize image data
      const initialImageData: Record<string, ImageData> = {};
      scriptData.scenes.forEach((scene: SceneData) => {
        initialImageData[scene.id] = {
          sceneId: scene.id,
          url: '',
          prompt: scene.imagePrompt || '',
          provider: 'dalle3',
          status: 'pending',
        };
      });
      setImageData(initialImageData);
    }
    
    if (audioDataStr) {
      const audio = JSON.parse(audioDataStr);
      setAudioData(audio);
    }

    // Load existing image data if any
    const existingImageStr = localStorage.getItem('imageData');
    if (existingImageStr) {
      const existingImages = JSON.parse(existingImageStr);
      setImageData(prev => ({ ...prev, ...existingImages }));
    }
  }, []);

  const generateImage = async (sceneId: string, prompt: string) => {
    setGeneratingScene(sceneId);
    setImageData(prev => ({
      ...prev,
      [sceneId]: { ...prev[sceneId], status: 'generating', provider: provider },
    }));

    try {
      const response = await fetch('/api/images/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          provider: 'dalle3',
          sceneId,
          size: '1792x1024', // 16:9 aspect ratio for DALL-E 3
          projectId: projectId || JSON.parse(localStorage.getItem('productionState') || '{}').projectId || 'default',
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'Failed to generate image');
      }

      const data = await response.json();
      
      setImageData(prev => ({
        ...prev,
        [sceneId]: {
          sceneId,
          url: data.url,
          prompt,
          provider: 'dalle3',
          status: 'completed',
        },
      }));

      // Save to localStorage
      const updatedImageData = {
        ...imageData,
        [sceneId]: {
          sceneId,
          url: data.url,
          prompt,
          provider: 'dalle3',
          status: 'completed',
        },
      };
      localStorage.setItem('imageData', JSON.stringify(updatedImageData));

    } catch (error) {
      console.error('Image generation error:', error);
      setImageData(prev => ({
        ...prev,
        [sceneId]: {
          ...prev[sceneId],
          status: 'error',
          error: error instanceof Error ? error.message : 'Generation failed',
        },
      }));
    } finally {
      setGeneratingScene(null);
    }
  };

  const generateAllImages = async () => {
    setIsGenerating(true);
    
    for (const scene of scenes) {
      if (imageData[scene.id]?.status !== 'completed') {
        const audioDuration = audioData[scene.id]?.duration || 5;
        const enhancedPrompt = generateOptimizedPrompt(
          imageData[scene.id]?.prompt || scene.imagePrompt,
          {
            sceneType: scene.metadata.sceneType,
            audioDuration,
            provider: provider,
          },
        );
        await generateImage(scene.id, enhancedPrompt);
        
        // Add delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    setIsGenerating(false);
  };



  const handleImageUpload = (sceneId: string, imageUrl: string) => {
    setImageData(prev => ({
      ...prev,
      [sceneId]: {
        sceneId,
        url: imageUrl,
        prompt: 'User uploaded image',
        provider: 'upload',
        status: 'completed',
      },
    }));

    // Save to localStorage
    const updatedImageData = {
      ...imageData,
      [sceneId]: {
        sceneId,
        url: imageUrl,
        prompt: 'User uploaded image',
        provider: 'upload',
        status: 'completed',
      },
    };
    localStorage.setItem('imageData', JSON.stringify(updatedImageData));
    
    setShowUploader(null);
  };

  const allImagesGenerated = scenes.every(
    scene => imageData[scene.id]?.status === 'completed',
  );

  const handleComplete = () => {
    // Update production state
    const currentState = JSON.parse(localStorage.getItem('productionState') || '{}');
    const newState = { ...currentState, imagesGenerated: true };
    localStorage.setItem('productionState', JSON.stringify(newState));
    
    onComplete();
  };

  const formatDuration = (seconds: number): string => {
    return `${seconds.toFixed(1)}s`;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Image Generation Provider Info */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Image Generation Provider</h3>
        <div className="rounded-lg border-2 border-primary-500 bg-primary-50 p-4">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-medium text-gray-900">{DALLE3_INFO.name}</h4>
              <p className="mt-1 text-sm text-gray-500">{DALLE3_INFO.description}</p>
              <p className="mt-2 text-xs font-medium text-primary-600">{DALLE3_INFO.cost}</p>
              <p className="mt-2 text-xs text-gray-500">Note: Flux.1 support was removed due to high subscription costs</p>
            </div>
            <CheckCircleIcon className="h-5 w-5 text-primary-500" />
          </div>
        </div>
      </div>

      {/* Generation Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Scene Images</h3>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={batchGenerate}
                onChange={(e) => setBatchGenerate(e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-600">Batch generation</span>
            </label>
            <button
              onClick={generateAllImages}
              disabled={isGenerating || allImagesGenerated}
              className={cn(
                'inline-flex items-center px-4 py-2 text-sm font-medium rounded-md',
                'border border-transparent shadow-sm',
                isGenerating || allImagesGenerated
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-700',
              )}
            >
              {isGenerating ? (
                <>
                  <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
                  Generating...
                </>
              ) : allImagesGenerated ? (
                <>
                  <CheckIcon className="-ml-1 mr-2 h-4 w-4" />
                  All Generated
                </>
              ) : (
                <>
                  <SparklesIcon className="-ml-1 mr-2 h-4 w-4" />
                  Generate All
                </>
              )}
            </button>
          </div>
        </div>

        {/* Scenes Grid */}
        <div className="space-y-6">
          {scenes.map((scene, index) => {
            const image = imageData[scene.id];
            const audio = audioData[scene.id];
            const isGenerating = generatingScene === scene.id;
            
            return (
              <div key={scene.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-gray-900">
                        Scene {index + 1}: {scene.metadata.sceneType}
                      </span>
                      <span className="ml-3 text-sm text-gray-500">
                        [{Math.floor(scene.timestamp / 60)}:{(scene.timestamp % 60).toString().padStart(2, '0')}]
                      </span>
                      {audio?.duration && (
                        <span className="ml-2 text-sm text-gray-500">
                          • Audio: {formatDuration(audio.duration)}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {image?.status === 'completed' && (
                        <CheckCircleIcon className="h-5 w-5 text-green-500" />
                      )}
                      {image?.status === 'error' && (
                        <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                      )}
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-2 gap-6">
                    {/* Image Preview */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Generated Image
                      </label>
                      <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
                        {image?.url ? (
                          <img 
                            src={image.url} 
                            alt={`Scene ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center">
                            {isGenerating ? (
                              <div className="text-center">
                                <ArrowPathIcon className="animate-spin h-8 w-8 text-primary-500 mx-auto" />
                                <p className="mt-2 text-sm text-gray-500">Generating...</p>
                              </div>
                            ) : (
                              <div className="text-center">
                                <PhotoIcon className="h-12 w-12 text-gray-400 mx-auto" />
                                <p className="mt-2 text-sm text-gray-500">No image yet</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      
                      {/* Action Buttons - Upload First, then Generate */}
                      <div className="mt-3 flex space-x-2">
                        {/* Upload Button - Priority Position */}
                        <button
                          onClick={() => setShowUploader(scene.id)}
                          className="flex-1 inline-flex items-center justify-center px-3 py-2 border-2 border-blue-300 shadow-sm text-sm font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100"
                        >
                          <ArrowUpTrayIcon className="h-4 w-4 mr-1" />
                          Upload Image
                        </button>
                        
                        {/* Generate Button - Secondary Position */}
                        {!batchGenerate && (
                          <button
                            onClick={() => {
                              const audioDuration = audio?.duration || 5;
                              const enhancedPrompt = generateOptimizedPrompt(
                                image?.prompt || scene.imagePrompt,
                                {
                                  sceneType: scene.metadata.sceneType,
                                  audioDuration,
                                  provider: provider,
                                },
                              );
                              generateImage(scene.id, enhancedPrompt);
                            }}
                            disabled={isGenerating || image?.status === 'completed'}
                            className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                          >
                            <SparklesIcon className="h-4 w-4 mr-1" />
                            Generate AI
                          </button>
                        )}
                        {image?.url && (
                          <a
                            href={image.url}
                            download={`scene-${index + 1}.png`}
                            className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                          >
                            <CloudArrowDownIcon className="h-4 w-4" />
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Universal Prompt Editor */}
                    <div>
                      <PromptEditor
                        value={image?.prompt || scene.imagePrompt || ''}
                        onChange={(newPrompt) => {
                          setImageData(prev => ({
                            ...prev,
                            [scene.id]: { ...prev[scene.id], prompt: newPrompt },
                          }));
                        }}
                        type="image"
                        sceneMetadata={{
                          sceneType: scene.metadata.sceneType,
                          audioDuration: audio?.duration,
                          genre: scene.metadata.description,
                        }}
                        showEnhance={true}
                        isInherited={!!scene.imagePrompt}
                        inheritedFrom="from storyboard"
                      />

                      {/* Scene Metadata */}
                      <div className="mt-4 space-y-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-500">Visual Description</label>
                          <p className="text-sm text-gray-600">{scene.metadata.visual}</p>
                        </div>
                        {scene.narration && (
                          <div>
                            <label className="block text-xs font-medium text-gray-500">Narration</label>
                            <p className="text-sm text-gray-600 italic">"{scene.narration}"</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Upload Modal */}
                  {showUploader === scene.id && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                      <div className="bg-white rounded-lg p-6 max-w-md w-full">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold">Upload Image</h3>
                          <button
                            onClick={() => setShowUploader(null)}
                            className="text-gray-400 hover:text-gray-500"
                          >
                            <XMarkIcon className="h-5 w-5" />
                          </button>
                        </div>
                        <ImageUploader
                          onUpload={(url) => handleImageUpload(scene.id, url)}
                          onCancel={() => setShowUploader(null)}
                        />
                      </div>
                    </div>
                  )}

                  {/* Error Display */}
                  {image?.status === 'error' && (
                    <div className="mt-4 rounded-md bg-red-50 p-3">
                      <div className="flex">
                        <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
                        <div className="ml-3">
                          <p className="text-sm text-red-800">{image.error}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Continue Button */}
      {allImagesGenerated && (
        <div className="flex justify-end">
          <button
            onClick={handleComplete}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Continue to Video Generation
            <CheckIcon className="ml-2 h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
};

export default ImageGenerator;
