import React, { useState, useEffect } from 'react';
import { ScriptScene, AudioData, ImageData } from '../../types';
import TimelineEditor from '../assembly/TimelineEditor';
import ExportSettings from '../assembly/ExportSettings';
import LoadingSpinner from '../LoadingSpinner';
import { Film, Download, Music, Volume2, Play, Pause } from 'lucide-react';

interface VideoData {
  sceneId: string;
  url: string;
  duration: number;
  status: 'pending' | 'generating' | 'completed' | 'error';
  error?: string;
}

interface FinalAssemblyProps {
  onComplete?: () => void;
}

interface ExportOptions {
  format: 'mp4' | 'mov' | 'webm';
  resolution: '4K' | '1080p' | '720p';
  frameRate: 24 | 30 | 60;
  quality: 'high' | 'medium' | 'low';
  includeBackgroundMusic: boolean;
  musicVolume: number;
  narrationVolume: number;
}

interface TimelineItem {
  id: string;
  sceneId: string;
  type: 'scene';
  startTime: number;
  duration: number;
  transition: 'cut' | 'fade' | 'dissolve' | 'wipe';
  transitionDuration: number;
  scene: ScriptScene;
  audio?: AudioData;
  image?: ImageData;
  video?: VideoData;
}

export default function FinalAssembly({ onComplete }: FinalAssemblyProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  
  // Data from previous stages
  const [, setScenes] = useState<ScriptScene[]>([]);
  const [, setAudioData] = useState<Record<string, AudioData>>({});
  const [, setImageData] = useState<Record<string, ImageData>>({});
  const [, setVideoData] = useState<Record<string, VideoData>>({});
  
  // Timeline state
  const [timelineItems, setTimelineItems] = useState<TimelineItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<TimelineItem | null>(null);
  
  // Export settings
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'mp4',
    resolution: '1080p',
    frameRate: 30,
    quality: 'high',
    includeBackgroundMusic: false,
    musicVolume: 30,
    narrationVolume: 100,
  });
  
  const [backgroundMusic, setBackgroundMusic] = useState<File | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      // Load data from localStorage (in production, this would be from API)
      const savedScript = localStorage.getItem('parsedScript');
      const savedAudio = localStorage.getItem('audioData');
      const savedImages = localStorage.getItem('imageData');
      const savedVideos = localStorage.getItem('videoData');

      if (savedScript) {
        const parsedScenes = JSON.parse(savedScript) as ScriptScene[];
        setScenes(parsedScenes);

        // Initialize timeline items
        const items: TimelineItem[] = [];
        let currentStartTime = 0;

        parsedScenes.forEach((scene, index) => {
          const sceneAudio = savedAudio ? JSON.parse(savedAudio)[scene.id] : null;
          const sceneImage = savedImages ? JSON.parse(savedImages)[scene.id] : null;
          const sceneVideo = savedVideos ? JSON.parse(savedVideos)[scene.id] : null;

          const duration = sceneAudio?.duration || 5; // Default 5 seconds if no audio

          items.push({
            id: `timeline-${scene.id}`,
            sceneId: scene.id,
            type: 'scene',
            startTime: currentStartTime,
            duration,
            transition: index === 0 ? 'cut' : 'fade',
            transitionDuration: index === 0 ? 0 : 0.5,
            scene,
            audio: sceneAudio,
            image: sceneImage,
            video: sceneVideo,
          });

          currentStartTime += duration;
        });

        setTimelineItems(items);

        if (savedAudio) setAudioData(JSON.parse(savedAudio));
        if (savedImages) setImageData(JSON.parse(savedImages));
        if (savedVideos) setVideoData(JSON.parse(savedVideos));
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimelineUpdate = (newItems: TimelineItem[]) => {
    setTimelineItems(newItems);
  };

  const handleTransitionChange = (itemId: string, transition: TimelineItem['transition'], duration: number) => {
    setTimelineItems(items =>
      items.map(item =>
        item.id === itemId
          ? { ...item, transition, transitionDuration: duration }
          : item,
      ),
    );
  };

  const handleExportSettingsChange = (options: ExportOptions) => {
    setExportOptions(options);
  };

  const handleBackgroundMusicUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setBackgroundMusic(file);
      setExportOptions(prev => ({ ...prev, includeBackgroundMusic: true }));
    }
  };

  const calculateTotalDuration = () => {
    return timelineItems.reduce((total, item) => total + item.duration, 0);
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportProgress(0);
    setDownloadUrl(null);

    try {
      // Prepare export data
      const exportData = {
        timeline: timelineItems.map(item => ({
          sceneId: item.sceneId,
          startTime: item.startTime,
          duration: item.duration,
          transition: item.transition,
          transitionDuration: item.transitionDuration,
          audioUrl: item.audio?.url,
          imageUrl: item.image?.url,
          videoUrl: item.video?.url,
          narration: item.scene.narration,
          onScreenText: item.scene.onScreenText,
        })),
        settings: exportOptions,
        totalDuration: calculateTotalDuration(),
      };

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('exportData', JSON.stringify(exportData));
      if (backgroundMusic && exportOptions.includeBackgroundMusic) {
        formData.append('backgroundMusic', backgroundMusic);
      }

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setExportProgress(prev => Math.min(prev + 10, 90));
      }, 1000);

      const response = await fetch('/api/assembly/export', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const result = await response.json();
      setExportProgress(100);
      setDownloadUrl(result.downloadUrl);

      // Mark production as complete
      if (onComplete) {
        localStorage.setItem('productionState', JSON.stringify({
          ...JSON.parse(localStorage.getItem('productionState') || '{}'),
          readyForAssembly: true,
          completed: true,
        }));
        onComplete();
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `evergreen-video-${Date.now()}.${exportOptions.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  const totalDuration = calculateTotalDuration();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Film className="h-6 w-6 text-green-600 mr-2" />
            <h2 className="text-2xl font-bold text-gray-900">Final Assembly</h2>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              Total Duration: {Math.floor(totalDuration / 60)}:{String(Math.floor(totalDuration % 60)).padStart(2, '0')}
            </span>
            {downloadUrl && (
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Video
              </button>
            )}
          </div>
        </div>
        <p className="text-gray-600">
          Arrange your scenes, add transitions, and export your final video.
        </p>
      </div>

      {/* Preview Controls */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={togglePlayback}
              className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
            </button>
            <div className="text-sm text-gray-600">
              {Math.floor(currentTime / 60)}:{String(Math.floor(currentTime % 60)).padStart(2, '0')} / {Math.floor(totalDuration / 60)}:{String(Math.floor(totalDuration % 60)).padStart(2, '0')}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <Volume2 className="h-4 w-4 text-gray-500 mr-2" />
              <input
                type="range"
                min="0"
                max="100"
                value={exportOptions.narrationVolume}
                onChange={(e) => setExportOptions(prev => ({ ...prev, narrationVolume: parseInt(e.target.value) }))}
                className="w-24"
              />
            </div>
            {exportOptions.includeBackgroundMusic && (
              <div className="flex items-center">
                <Music className="h-4 w-4 text-gray-500 mr-2" />
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={exportOptions.musicVolume}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, musicVolume: parseInt(e.target.value) }))}
                  className="w-24"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Timeline Editor */}
      <TimelineEditor
        items={timelineItems}
        currentTime={currentTime}
        totalDuration={totalDuration}
        selectedItem={selectedItem}
        onItemsChange={handleTimelineUpdate}
        onItemSelect={setSelectedItem}
        onTransitionChange={handleTransitionChange}
        onTimeChange={setCurrentTime}
      />

      {/* Background Music */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Music className="h-5 w-5 mr-2" />
          Background Music
        </h3>
        <div className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Upload Background Music (optional)</span>
            <input
              type="file"
              accept="audio/*"
              onChange={handleBackgroundMusicUpload}
              className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
            />
          </label>
          {backgroundMusic && (
            <p className="text-sm text-gray-600">
              Selected: {backgroundMusic.name}
            </p>
          )}
        </div>
      </div>

      {/* Export Settings */}
      <ExportSettings
        options={exportOptions}
        onChange={handleExportSettingsChange}
        totalDuration={totalDuration}
        sceneCount={timelineItems.length}
      />

      {/* Export Progress */}
      {isExporting && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Exporting Video...</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Processing</span>
              <span>{exportProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${exportProgress}%` }}
              />
            </div>
            {exportProgress < 100 && (
              <p className="text-sm text-gray-600 mt-2">
                This may take a few minutes depending on video length and quality settings...
              </p>
            )}
          </div>
        </div>
      )}

      {/* Export Button */}
      {!isExporting && !downloadUrl && (
        <div className="flex justify-end">
          <button
            onClick={handleExport}
            disabled={timelineItems.length === 0}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center"
          >
            <Film className="h-5 w-5 mr-2" />
            Export Final Video
          </button>
        </div>
      )}
    </div>
  );
}
