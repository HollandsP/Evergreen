import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Slider } from '../ui/slider';
import { Switch } from '../ui/switch';
import { 
  Download, 
  Youtube, 
  Instagram, 
  Twitter,
  Facebook,
  Linkedin,
  Globe,
  Film,
  Settings,
  Zap,
  HardDrive,
  Cpu,
  Gauge,
  FileVideo,
  Volume2,
  Image,
  Loader2,
  Check,
  AlertCircle,
  Info,
  Save,
  Upload
} from 'lucide-react';

interface ExportPreset {
  id: string;
  name: string;
  platform: string;
  icon: React.ReactNode;
  settings: ExportSettings;
  description: string;
  fileSize: string;
  quality: 'low' | 'medium' | 'high' | 'ultra';
  recommended?: boolean;
}

interface ExportSettings {
  format: string;
  resolution: string;
  fps: number;
  bitrate: string;
  codec: string;
  audioCodec: string;
  audioBitrate: string;
  aspectRatio: string;
  profile?: string;
  preset?: string;
  crf?: number;
  maxSize?: string;
  twoPass?: boolean;
  hardwareAccel?: boolean;
}

interface ExportPresetsProps {
  projectId: string;
  duration?: number; // Video duration in seconds
  onExport: (preset: ExportPreset, customSettings?: Partial<ExportSettings>) => void;
  className?: string;
}

export default function ExportPresets({
  projectId,
  duration = 60,
  onExport,
  className = ''
}: ExportPresetsProps) {
  const [selectedPlatform, setSelectedPlatform] = useState('youtube');
  const [isExporting, setIsExporting] = useState(false);
  const [customSettings, setCustomSettings] = useState<Partial<ExportSettings>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  const presets: ExportPreset[] = [
    // YouTube Presets
    {
      id: 'youtube-4k',
      name: 'YouTube 4K',
      platform: 'youtube',
      icon: <Youtube className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '3840x2160',
        fps: 30,
        bitrate: '45M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '320k',
        aspectRatio: '16:9',
        profile: 'high',
        preset: 'slow',
        crf: 18
      },
      description: 'Best quality for 4K displays',
      fileSize: '~3.3 GB/min',
      quality: 'ultra',
      recommended: true
    },
    {
      id: 'youtube-1080p',
      name: 'YouTube HD',
      platform: 'youtube',
      icon: <Youtube className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1920x1080',
        fps: 30,
        bitrate: '8M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '192k',
        aspectRatio: '16:9',
        profile: 'high',
        preset: 'medium',
        crf: 23
      },
      description: 'Standard HD quality',
      fileSize: '~600 MB/min',
      quality: 'high'
    },
    {
      id: 'youtube-shorts',
      name: 'YouTube Shorts',
      platform: 'youtube',
      icon: <Youtube className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1080x1920',
        fps: 30,
        bitrate: '10M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '192k',
        aspectRatio: '9:16',
        profile: 'high',
        preset: 'medium'
      },
      description: 'Vertical format for Shorts',
      fileSize: '~750 MB/min',
      quality: 'high'
    },

    // Instagram Presets
    {
      id: 'instagram-reel',
      name: 'Instagram Reel',
      platform: 'instagram',
      icon: <Instagram className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1080x1920',
        fps: 30,
        bitrate: '5M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '128k',
        aspectRatio: '9:16',
        maxSize: '100MB'
      },
      description: 'Optimized for Reels',
      fileSize: '~375 MB/min',
      quality: 'medium'
    },
    {
      id: 'instagram-feed',
      name: 'Instagram Feed',
      platform: 'instagram',
      icon: <Instagram className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1080x1080',
        fps: 30,
        bitrate: '5M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '128k',
        aspectRatio: '1:1',
        maxSize: '100MB'
      },
      description: 'Square format for feed',
      fileSize: '~375 MB/min',
      quality: 'medium'
    },

    // TikTok Presets
    {
      id: 'tiktok-hd',
      name: 'TikTok HD',
      platform: 'tiktok',
      icon: <Film className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1080x1920',
        fps: 30,
        bitrate: '6M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '128k',
        aspectRatio: '9:16',
        maxSize: '287MB'
      },
      description: 'High quality TikTok',
      fileSize: '~450 MB/min',
      quality: 'high'
    },

    // Twitter/X Presets
    {
      id: 'twitter-video',
      name: 'Twitter/X Video',
      platform: 'twitter',
      icon: <Twitter className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1920x1080',
        fps: 30,
        bitrate: '5M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '128k',
        aspectRatio: '16:9',
        maxSize: '512MB'
      },
      description: 'Optimized for Twitter',
      fileSize: '~375 MB/min',
      quality: 'medium'
    },

    // LinkedIn Presets
    {
      id: 'linkedin-video',
      name: 'LinkedIn Video',
      platform: 'linkedin',
      icon: <Linkedin className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1920x1080',
        fps: 30,
        bitrate: '10M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '192k',
        aspectRatio: '16:9',
        maxSize: '5GB'
      },
      description: 'Professional quality',
      fileSize: '~750 MB/min',
      quality: 'high'
    },

    // Web/General Presets
    {
      id: 'web-standard',
      name: 'Web Standard',
      platform: 'web',
      icon: <Globe className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1920x1080',
        fps: 30,
        bitrate: '5M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '128k',
        aspectRatio: '16:9',
        preset: 'fast'
      },
      description: 'Universal compatibility',
      fileSize: '~375 MB/min',
      quality: 'medium'
    },
    {
      id: 'web-compressed',
      name: 'Web Compressed',
      platform: 'web',
      icon: <Globe className="w-4 h-4" />,
      settings: {
        format: 'mp4',
        resolution: '1280x720',
        fps: 30,
        bitrate: '2.5M',
        codec: 'h264',
        audioCodec: 'aac',
        audioBitrate: '96k',
        aspectRatio: '16:9',
        preset: 'fast',
        crf: 28
      },
      description: 'Fast loading, smaller size',
      fileSize: '~188 MB/min',
      quality: 'low'
    }
  ];

  const platforms = [
    { id: 'youtube', label: 'YouTube', icon: <Youtube className="w-4 h-4" /> },
    { id: 'instagram', label: 'Instagram', icon: <Instagram className="w-4 h-4" /> },
    { id: 'tiktok', label: 'TikTok', icon: <Film className="w-4 h-4" /> },
    { id: 'twitter', label: 'Twitter', icon: <Twitter className="w-4 h-4" /> },
    { id: 'linkedin', label: 'LinkedIn', icon: <Linkedin className="w-4 h-4" /> },
    { id: 'web', label: 'Web/Other', icon: <Globe className="w-4 h-4" /> }
  ];

  const handleExport = useCallback(async (preset: ExportPreset) => {
    setIsExporting(true);
    
    try {
      // Merge custom settings with preset
      const finalSettings = { ...preset.settings, ...customSettings };
      
      await onExport(preset, customSettings);
      
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  }, [customSettings, onExport]);

  const calculateFileSize = (bitrate: string, duration: number): string => {
    const bitrateNum = parseInt(bitrate);
    const sizeInMB = (bitrateNum * duration) / 8 / 1024 / 1024;
    
    if (sizeInMB < 1024) {
      return `~${sizeInMB.toFixed(0)} MB`;
    } else {
      return `~${(sizeInMB / 1024).toFixed(1)} GB`;
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'ultra': return 'text-purple-500';
      case 'high': return 'text-green-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-orange-500';
      default: return 'text-zinc-400';
    }
  };

  const filteredPresets = presets.filter(p => p.platform === selectedPlatform);

  return (
    <Card className={`bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-500" />
            Export Settings
          </CardTitle>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <Settings className="w-4 h-4 mr-2" />
            {showAdvanced ? 'Simple' : 'Advanced'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={selectedPlatform} onValueChange={setSelectedPlatform}>
          <TabsList className="grid grid-cols-3 lg:grid-cols-6 mb-4">
            {platforms.map(platform => (
              <TabsTrigger
                key={platform.id}
                value={platform.id}
                className="flex items-center gap-1"
              >
                {platform.icon}
                <span className="hidden lg:inline">{platform.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value={selectedPlatform} className="space-y-4">
            {/* Preset Cards */}
            <div className="grid gap-4">
              {filteredPresets.map(preset => (
                <div
                  key={preset.id}
                  className="p-4 rounded-lg border bg-zinc-800 border-zinc-700 hover:border-zinc-600 transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-zinc-700">
                        {preset.icon}
                      </div>
                      <div>
                        <h3 className="font-semibold text-white flex items-center gap-2">
                          {preset.name}
                          {preset.recommended && (
                            <Badge variant="secondary" className="text-xs">
                              Recommended
                            </Badge>
                          )}
                        </h3>
                        <p className="text-sm text-zinc-400">{preset.description}</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                    <div>
                      <Label className="text-xs text-zinc-500">Resolution</Label>
                      <p className="text-sm font-medium">{preset.settings.resolution}</p>
                    </div>
                    <div>
                      <Label className="text-xs text-zinc-500">Format</Label>
                      <p className="text-sm font-medium">{preset.settings.format.toUpperCase()}</p>
                    </div>
                    <div>
                      <Label className="text-xs text-zinc-500">Quality</Label>
                      <p className={`text-sm font-medium ${getQualityColor(preset.quality)}`}>
                        {preset.quality.charAt(0).toUpperCase() + preset.quality.slice(1)}
                      </p>
                    </div>
                    <div>
                      <Label className="text-xs text-zinc-500">Est. Size</Label>
                      <p className="text-sm font-medium">
                        {calculateFileSize(preset.settings.bitrate, duration)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-zinc-500 mb-3">
                    <FileVideo className="w-3 h-3" />
                    {preset.settings.codec} @ {preset.settings.bitrate}
                    <Volume2 className="w-3 h-3 ml-2" />
                    {preset.settings.audioCodec} @ {preset.settings.audioBitrate}
                    <Gauge className="w-3 h-3 ml-2" />
                    {preset.settings.fps} FPS
                  </div>

                  <Button
                    className="w-full"
                    onClick={() => handleExport(preset)}
                    disabled={isExporting}
                  >
                    {isExporting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Exporting...
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4 mr-2" />
                        Export with {preset.name}
                      </>
                    )}
                  </Button>
                </div>
              ))}
            </div>

            {/* Advanced Settings */}
            {showAdvanced && (
              <div className="mt-6 p-4 rounded-lg bg-zinc-800 border border-zinc-700">
                <h4 className="font-medium mb-4 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Custom Export Settings
                </h4>
                
                <div className="grid gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Video Bitrate</Label>
                      <Select
                        value={customSettings.bitrate || '5M'}
                        onValueChange={(value) => setCustomSettings(prev => ({ ...prev, bitrate: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="2M">2 Mbps (Low)</SelectItem>
                          <SelectItem value="5M">5 Mbps (Medium)</SelectItem>
                          <SelectItem value="10M">10 Mbps (High)</SelectItem>
                          <SelectItem value="20M">20 Mbps (Very High)</SelectItem>
                          <SelectItem value="50M">50 Mbps (Ultra)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label>Audio Bitrate</Label>
                      <Select
                        value={customSettings.audioBitrate || '128k'}
                        onValueChange={(value) => setCustomSettings(prev => ({ ...prev, audioBitrate: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="96k">96 kbps</SelectItem>
                          <SelectItem value="128k">128 kbps</SelectItem>
                          <SelectItem value="192k">192 kbps</SelectItem>
                          <SelectItem value="320k">320 kbps</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label>Quality (CRF)</Label>
                    <div className="flex items-center gap-4">
                      <Slider
                        value={[customSettings.crf || 23]}
                        onValueChange={([value]) => setCustomSettings(prev => ({ ...prev, crf: value }))}
                        max={51}
                        min={0}
                        step={1}
                        className="flex-1"
                      />
                      <span className="text-sm w-12 text-right">{customSettings.crf || 23}</span>
                    </div>
                    <p className="text-xs text-zinc-500 mt-1">
                      Lower = Better quality, larger file
                    </p>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="two-pass" className="flex items-center gap-2">
                      <Cpu className="w-4 h-4" />
                      Two-Pass Encoding
                    </Label>
                    <Switch
                      id="two-pass"
                      checked={customSettings.twoPass || false}
                      onCheckedChange={(checked) => setCustomSettings(prev => ({ ...prev, twoPass: checked }))}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="hw-accel" className="flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Hardware Acceleration
                    </Label>
                    <Switch
                      id="hw-accel"
                      checked={customSettings.hardwareAccel || false}
                      onCheckedChange={(checked) => setCustomSettings(prev => ({ ...prev, hardwareAccel: checked }))}
                    />
                  </div>
                </div>

                <div className="mt-4 p-3 rounded bg-zinc-700/50 flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-500 mt-0.5" />
                  <p className="text-xs text-zinc-400">
                    Custom settings will override the selected preset. Two-pass encoding provides better quality but takes longer.
                  </p>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}