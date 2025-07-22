import React from 'react';
import { Settings, Film, Zap, HardDrive } from 'lucide-react';

interface ExportOptions {
  format: 'mp4' | 'mov' | 'webm';
  resolution: '4K' | '1080p' | '720p';
  frameRate: 24 | 30 | 60;
  quality: 'high' | 'medium' | 'low';
  includeBackgroundMusic: boolean;
  musicVolume: number;
  narrationVolume: number;
}

interface ExportSettingsProps {
  options: ExportOptions;
  onChange: (options: ExportOptions) => void;
  totalDuration: number;
  sceneCount: number;
}

export default function ExportSettings({
  options,
  onChange,
  totalDuration,
  sceneCount
}: ExportSettingsProps) {
  const estimateFileSize = () => {
    // Rough estimation based on settings
    const baseRate = {
      '4K': { high: 60, medium: 40, low: 25 },
      '1080p': { high: 15, medium: 10, low: 6 },
      '720p': { high: 8, medium: 5, low: 3 }
    };

    const rate = baseRate[options.resolution][options.quality];
    const sizeInMB = (totalDuration * rate) / 8; // Convert from Mbps to MB
    
    return sizeInMB;
  };

  const estimateProcessingTime = () => {
    // Rough estimation based on complexity
    const complexityFactor = {
      '4K': 3,
      '1080p': 1.5,
      '720p': 1
    };

    const qualityFactor = {
      high: 2,
      medium: 1.5,
      low: 1
    };

    const baseTime = totalDuration * 0.5; // 30 seconds processing per minute of video
    const estimatedTime = baseTime * complexityFactor[options.resolution] * qualityFactor[options.quality];
    
    return Math.ceil(estimatedTime / 60); // Return in minutes
  };

  const handleChange = (key: keyof ExportOptions, value: any) => {
    onChange({ ...options, [key]: value });
  };

  const formatOptions = [
    { value: 'mp4', label: 'MP4', description: 'Universal compatibility' },
    { value: 'mov', label: 'MOV', description: 'High quality, larger files' },
    { value: 'webm', label: 'WebM', description: 'Web optimized' }
  ];

  const resolutionOptions = [
    { value: '4K', label: '4K (3840×2160)', description: 'Ultra HD quality' },
    { value: '1080p', label: '1080p (1920×1080)', description: 'Full HD, recommended' },
    { value: '720p', label: '720p (1280×720)', description: 'HD, smaller files' }
  ];

  const frameRateOptions = [
    { value: 24, label: '24 fps', description: 'Cinematic look' },
    { value: 30, label: '30 fps', description: 'Standard video' },
    { value: 60, label: '60 fps', description: 'Smooth motion' }
  ];

  const qualityOptions = [
    { value: 'high', label: 'High', description: 'Best quality, larger files' },
    { value: 'medium', label: 'Medium', description: 'Balanced quality and size' },
    { value: 'low', label: 'Low', description: 'Smaller files, faster export' }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <Settings className="h-5 w-5 mr-2" />
        Export Settings
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Format Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Output Format
          </label>
          <div className="space-y-2">
            {formatOptions.map(format => (
              <label key={format.value} className="flex items-start">
                <input
                  type="radio"
                  name="format"
                  value={format.value}
                  checked={options.format === format.value}
                  onChange={(e) => handleChange('format', e.target.value)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium">{format.label}</span>
                  <span className="text-sm text-gray-500 ml-2">{format.description}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Resolution Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Resolution
          </label>
          <div className="space-y-2">
            {resolutionOptions.map(resolution => (
              <label key={resolution.value} className="flex items-start">
                <input
                  type="radio"
                  name="resolution"
                  value={resolution.value}
                  checked={options.resolution === resolution.value}
                  onChange={(e) => handleChange('resolution', e.target.value)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium">{resolution.label}</span>
                  <span className="text-sm text-gray-500 ml-2">{resolution.description}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Frame Rate Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Frame Rate
          </label>
          <div className="space-y-2">
            {frameRateOptions.map(frameRate => (
              <label key={frameRate.value} className="flex items-start">
                <input
                  type="radio"
                  name="frameRate"
                  value={frameRate.value}
                  checked={options.frameRate === frameRate.value}
                  onChange={(e) => handleChange('frameRate', parseInt(e.target.value))}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium">{frameRate.label}</span>
                  <span className="text-sm text-gray-500 ml-2">{frameRate.description}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Quality Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quality
          </label>
          <div className="space-y-2">
            {qualityOptions.map(quality => (
              <label key={quality.value} className="flex items-start">
                <input
                  type="radio"
                  name="quality"
                  value={quality.value}
                  checked={options.quality === quality.value}
                  onChange={(e) => handleChange('quality', e.target.value)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium">{quality.label}</span>
                  <span className="text-sm text-gray-500 ml-2">{quality.description}</span>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Export Summary */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium mb-3">Export Summary</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="flex items-center text-gray-600 mb-1">
              <Film className="h-4 w-4 mr-1" />
              Scenes
            </div>
            <div className="font-semibold">{sceneCount}</div>
          </div>
          <div>
            <div className="flex items-center text-gray-600 mb-1">
              <Zap className="h-4 w-4 mr-1" />
              Duration
            </div>
            <div className="font-semibold">
              {Math.floor(totalDuration / 60)}:{String(Math.floor(totalDuration % 60)).padStart(2, '0')}
            </div>
          </div>
          <div>
            <div className="flex items-center text-gray-600 mb-1">
              <HardDrive className="h-4 w-4 mr-1" />
              Est. Size
            </div>
            <div className="font-semibold">~{Math.round(estimateFileSize())} MB</div>
          </div>
          <div>
            <div className="flex items-center text-gray-600 mb-1">
              <Settings className="h-4 w-4 mr-1" />
              Est. Time
            </div>
            <div className="font-semibold">~{estimateProcessingTime()} min</div>
          </div>
        </div>
        
        <div className="mt-3 text-xs text-gray-500">
          * Estimates based on current settings. Actual values may vary.
        </div>
      </div>
    </div>
  );
}