import React, { useState, useEffect, useRef } from 'react';
import { SpeakerWaveIcon, PlayIcon, PauseIcon, ArrowDownTrayIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/20/solid';
import { cn } from '@/lib/utils';
import WaveformVisualizer from '../audio/WaveformVisualizer';
import ErrorBoundary from '../ErrorBoundary';
import LoadingSpinner from '../LoadingSpinner';

interface SceneData {
  id: string;
  timestamp: number;
  narration: string;
  metadata: {
    sceneType: string;
    description: string;
  };
}

interface AudioData {
  sceneId: string;
  url: string;
  duration: number;
  status: 'pending' | 'generating' | 'completed' | 'error';
  error?: string;
}

interface AudioGeneratorProps {
  onComplete: () => void;
}

const VOICE_OPTIONS = [
  { id: 'male_calm', name: 'Winston - Calm', description: 'Main narrator voice' },
  { id: 'male_deep', name: 'Winston - Deep', description: 'Dramatic emphasis' },
  { id: 'male_british', name: 'Winston - British', description: 'Alternative accent' },
];

export const AudioGenerator: React.FC<AudioGeneratorProps> = ({ onComplete }) => {
  const [scenes, setScenes] = useState<SceneData[]>([]);
  const [audioData, setAudioData] = useState<Record<string, AudioData>>({});
  const [selectedVoice, setSelectedVoice] = useState('male_calm');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingScene, setGeneratingScene] = useState<string | null>(null);
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  const audioRefs = useRef<Record<string, HTMLAudioElement>>({});

  useEffect(() => {
    // Load script data from localStorage
    const scriptDataStr = localStorage.getItem('scriptData');
    if (scriptDataStr) {
      const scriptData = JSON.parse(scriptDataStr);
      const scenesWithNarration = scriptData.scenes.filter((scene: SceneData) => scene.narration);
      setScenes(scenesWithNarration);

      // Initialize audio data
      const initialAudioData: Record<string, AudioData> = {};
      scenesWithNarration.forEach((scene: SceneData) => {
        initialAudioData[scene.id] = {
          sceneId: scene.id,
          url: '',
          duration: 0,
          status: 'pending',
        };
      });
      setAudioData(initialAudioData);

      // Load existing audio data if any
      const existingAudioStr = localStorage.getItem('audioData');
      if (existingAudioStr) {
        const existingAudio = JSON.parse(existingAudioStr);
        setAudioData(prev => ({ ...prev, ...existingAudio }));
      }
    }
  }, []);

  const generateAudio = async (sceneId: string, narration: string) => {
    setGeneratingScene(sceneId);
    setAudioData(prev => ({
      ...prev,
      [sceneId]: { ...prev[sceneId], status: 'generating' },
    }));

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

      const response = await fetch('/api/audio/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: narration,
          voice: selectedVoice,
          sceneId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.audioUrl) {
        throw new Error('No audio URL returned from server');
      }
      
      setAudioData(prev => ({
        ...prev,
        [sceneId]: {
          sceneId,
          url: data.audioUrl,
          duration: data.duration || 0,
          status: 'completed',
        },
      }));

      // Save to localStorage with error handling
      try {
        const updatedAudioData = {
          ...audioData,
          [sceneId]: {
            sceneId,
            url: data.audioUrl,
            duration: data.duration || 0,
            status: 'completed',
          },
        };
        localStorage.setItem('audioData', JSON.stringify(updatedAudioData));
      } catch (storageError) {
        console.warn('Failed to save audio data to localStorage:', storageError);
      }

    } catch (error) {
      let errorMessage = 'Unknown error occurred';
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Request timed out after 60 seconds';
        } else {
          errorMessage = error.message;
        }
      }
      
      setAudioData(prev => ({
        ...prev,
        [sceneId]: {
          ...prev[sceneId],
          status: 'error',
          error: errorMessage,
        },
      }));
      
      console.error(`Audio generation failed for scene ${sceneId}:`, error);
    } finally {
      setGeneratingScene(null);
    }
  };

  const generateAllAudio = async () => {
    setIsGenerating(true);
    
    try {
      // Process scenes in parallel for better performance
      const scenesToGenerate = scenes.filter(scene => 
        audioData[scene.id]?.status !== 'completed',
      );
      
      const generatePromises = scenesToGenerate.map(scene =>
        generateAudio(scene.id, scene.narration),
      );
      
      await Promise.all(generatePromises);
    } catch (error) {
      console.error('Error during batch audio generation:', error);
    } finally {
      setIsGenerating(false);
    }
    
    // Check if all completed
    const allCompleted = Object.values(audioData).every(
      audio => audio.status === 'completed',
    );
    
    if (allCompleted) {
      // Update production state
      const currentState = JSON.parse(localStorage.getItem('productionState') || '{}');
      const newState = { ...currentState, audioGenerated: true };
      localStorage.setItem('productionState', JSON.stringify(newState));
    }
  };

  const playAudio = (sceneId: string) => {
    const audioUrl = audioData[sceneId]?.url;
    if (!audioUrl) return;

    // Stop any currently playing audio
    if (playingAudio && audioRefs.current[playingAudio]) {
      audioRefs.current[playingAudio].pause();
    }

    if (playingAudio === sceneId) {
      setPlayingAudio(null);
    } else {
      if (!audioRefs.current[sceneId]) {
        audioRefs.current[sceneId] = new Audio(audioUrl);
        audioRefs.current[sceneId].addEventListener('ended', () => {
          setPlayingAudio(null);
        });
      }
      audioRefs.current[sceneId].play();
      setPlayingAudio(sceneId);
    }
  };

  const downloadAudio = (sceneId: string, sceneType: string) => {
    const audioUrl = audioData[sceneId]?.url;
    if (!audioUrl) return;

    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = `scene-${sceneId}-${sceneType.toLowerCase().replace(/\s+/g, '-')}.mp3`;
    link.click();
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const completedCount = Object.values(audioData).filter(a => a.status === 'completed').length;
  const totalCount = scenes.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Progress Overview */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Audio Generation Progress</h2>
            <p className="text-sm text-gray-500 mt-1">
              {completedCount} of {totalCount} scenes completed
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Voice Selection */}
            <select
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              disabled={isGenerating}
              className="block w-48 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
            >
              {VOICE_OPTIONS.map(voice => (
                <option key={voice.id} value={voice.id}>
                  {voice.name}
                </option>
              ))}
            </select>
            
            {/* Generate All Button */}
            <button
              onClick={generateAllAudio}
              disabled={isGenerating || completedCount === totalCount}
              className={cn(
                'inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white',
                isGenerating || completedCount === totalCount
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700',
              )}
            >
              <SparklesIcon className="h-5 w-5 mr-2" />
              {isGenerating ? 'Generating...' : 'Generate All Audio'}
            </button>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Scenes List */}
      <div className="space-y-4">
        {scenes.map((scene, index) => {
          const audio = audioData[scene.id];
          const isGeneratingThis = generatingScene === scene.id;
          
          return (
            <div
              key={scene.id}
              className="bg-white rounded-lg border border-gray-200 overflow-hidden"
            >
              <div className="p-6">
                {/* Scene Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Scene {index + 1}: {scene.metadata.sceneType}
                      </h3>
                      {audio?.status === 'completed' && (
                        <CheckCircleIcon className="h-5 w-5 text-green-500 ml-2" />
                      )}
                      {audio?.status === 'error' && (
                        <ExclamationCircleIcon className="h-5 w-5 text-red-500 ml-2" />
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Timestamp: {formatDuration(scene.timestamp)}
                    </p>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex items-center space-x-2 ml-4">
                    {audio?.status === 'completed' && (
                      <>
                        <button
                          onClick={() => playAudio(scene.id)}
                          className="inline-flex items-center p-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50"
                        >
                          {playingAudio === scene.id ? (
                            <PauseIcon className="h-5 w-5" />
                          ) : (
                            <PlayIcon className="h-5 w-5" />
                          )}
                        </button>
                        <button
                          onClick={() => downloadAudio(scene.id, scene.metadata.sceneType)}
                          className="inline-flex items-center p-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <ArrowDownTrayIcon className="h-5 w-5" />
                        </button>
                      </>
                    )}
                    
                    {audio?.status !== 'completed' && !isGeneratingThis && (
                      <button
                        onClick={() => generateAudio(scene.id, scene.narration)}
                        disabled={isGenerating}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
                      >
                        <SpeakerWaveIcon className="h-4 w-4 mr-2" />
                        Generate Audio
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Narration Text */}
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <p className="text-sm text-gray-700 italic">"{scene.narration}"</p>
                </div>
                
                {/* Status Messages */}
                {isGeneratingThis && (
                  <LoadingSpinner 
                    size="sm" 
                    text="Generating audio..." 
                    className="text-sm text-gray-600"
                    inline 
                  />
                )}
                
                {audio?.status === 'error' && (
                  <div className="text-sm text-red-600">
                    Error: {audio.error}
                  </div>
                )}
                
                {/* Waveform Visualization */}
                {audio?.status === 'completed' && audio.url && (
                  <div className="mt-4">
                    <ErrorBoundary
                      fallback={
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <p className="text-sm text-yellow-800">
                            Unable to load waveform visualization
                          </p>
                        </div>
                      }
                    >
                      <WaveformVisualizer
                        audioUrl={audio.url}
                        duration={audio.duration}
                        isPlaying={playingAudio === scene.id}
                      />
                    </ErrorBoundary>
                    <p className="text-sm text-gray-500 mt-2">
                      Duration: {formatDuration(audio.duration)}
                    </p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Continue Button */}
      {completedCount === totalCount && totalCount > 0 && (
        <div className="flex justify-end pt-6">
          <button
            onClick={onComplete}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Continue to Image Generation
            <CheckCircleIcon className="ml-2 h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
};

export default AudioGenerator;
