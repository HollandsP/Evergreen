import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';
import { Badge } from '../ui/badge';
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  Volume2, 
  VolumeX,
  Scissors,
  Move,
  Clock,
  Film,
  Music,
  Type,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize,
  Grid,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronRight,
  Loader2,
  AlertCircle,
  Zap,
  Wand2,
  Sparkles
} from 'lucide-react';

interface TimelineClip {
  id: string;
  type: 'video' | 'audio' | 'text' | 'transition' | 'effect';
  name: string;
  startTime: number;
  duration: number;
  source?: string;
  color?: string;
  locked?: boolean;
  thumbnail?: string;
  effects?: string[];
  volume?: number;
  opacity?: number;
  metadata?: {
    fps?: number;
    resolution?: string;
    bitrate?: string;
    codec?: string;
  };
}

interface TimelineTrack {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'overlay' | 'effects';
  clips: TimelineClip[];
  muted?: boolean;
  volume?: number;
  visible?: boolean;
  locked?: boolean;
  collapsed?: boolean;
  height?: number;
}

interface TimelineProps {
  projectId: string;
  storyboardData?: any;
  onClipSelected?: (clip: TimelineClip) => void;
  onTimelineChange?: (tracks: TimelineTrack[]) => void;
  onTimeUpdate?: (time: number) => void;
  onOperation?: (operation: any) => void;
  className?: string;
}

// Professional zoom levels
const ZOOM_LEVELS = [
  { value: 0.1, label: '10%', unit: 'hours' },
  { value: 0.25, label: '25%', unit: 'minutes' },
  { value: 0.5, label: '50%', unit: 'minutes' },
  { value: 1, label: '100%', unit: 'seconds' },
  { value: 2, label: '200%', unit: 'seconds' },
  { value: 5, label: '500%', unit: 'frames' },
  { value: 10, label: '1000%', unit: 'frames' }
];

// Professional keyboard shortcuts
const SHORTCUTS = {
  PLAY_PAUSE: ' ',
  SKIP_BACK: 'j',
  SKIP_FORWARD: 'l',
  ZOOM_IN: '=',
  ZOOM_OUT: '-',
  CUT: 'c',
  DELETE: 'Delete',
  DUPLICATE: 'd',
  SELECT_ALL: 'a',
  DESELECT: 'Escape'
};

export default function Timeline({ 
  projectId, 
  storyboardData, 
  onClipSelected,
  onTimelineChange,
  onTimeUpdate,
  onOperation,
  className = '' 
}: TimelineProps) {
  // State management
  const [tracks, setTracks] = useState<TimelineTrack[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [totalDuration, setTotalDuration] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [selectedClips, setSelectedClips] = useState<Set<string>>(new Set());
  const [draggedClip, setDraggedClip] = useState<TimelineClip | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [showWaveforms, setShowWaveforms] = useState(false);
  const [rippleEdit, setRippleEdit] = useState(false);
  const [frameRate] = useState(30); // 30fps default

  // Refs for DOM elements
  const timelineRef = useRef<HTMLDivElement>(null);
  const playheadRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const rulerRef = useRef<HTMLDivElement>(null);

  // Virtualization state
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 100 });
  const [renderedClips, setRenderedClips] = useState<Map<string, TimelineClip[]>>(new Map());

  // Load timeline data from storyboard
  useEffect(() => {
    if (storyboardData?.scenes) {
      loadTimelineFromStoryboard();
    }
  }, [storyboardData]);

  // Virtualization: Update visible range on scroll
  useEffect(() => {
    const handleScroll = () => {
      if (!scrollContainerRef.current || !timelineRef.current) return;
      
      const container = scrollContainerRef.current;
      const scrollLeft = container.scrollLeft;
      const containerWidth = container.clientWidth;
      const timelineWidth = timelineRef.current.scrollWidth;
      
      const startTime = (scrollLeft / timelineWidth) * totalDuration;
      const endTime = ((scrollLeft + containerWidth) / timelineWidth) * totalDuration;
      
      setVisibleRange({ 
        start: Math.max(0, startTime - 10), 
        end: Math.min(totalDuration, endTime + 10) 
      });
    };

    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      handleScroll(); // Initial calculation
    }

    return () => {
      if (container) {
        container.removeEventListener('scroll', handleScroll);
      }
    };
  }, [totalDuration, zoom]);

  // Filter clips based on visible range for virtualization
  useEffect(() => {
    const filtered = new Map<string, TimelineClip[]>();
    
    tracks.forEach(track => {
      const visibleClips = track.clips.filter(clip => {
        const clipEnd = clip.startTime + clip.duration;
        return clipEnd >= visibleRange.start && clip.startTime <= visibleRange.end;
      });
      filtered.set(track.id, visibleClips);
    });
    
    setRenderedClips(filtered);
  }, [tracks, visibleRange]);

  const loadTimelineFromStoryboard = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const videoTracks: TimelineTrack[] = [];
      const audioTracks: TimelineTrack[] = [];
      const overlayTracks: TimelineTrack[] = [];
      
      let currentTime = 0;
      
      // Create main video track
      const mainVideoTrack: TimelineTrack = {
        id: 'video-main',
        name: 'Main Video',
        type: 'video',
        clips: [],
        visible: true,
        height: 80
      };

      // Create narration track
      const narrationTrack: TimelineTrack = {
        id: 'audio-narration',
        name: 'Narration',
        type: 'audio',
        clips: [],
        volume: 0.8,
        height: 60
      };

      // Process scenes
      storyboardData.scenes.forEach((scene: any, index: number) => {
        const sceneDuration = scene.duration || 5; // Default 5 seconds

        // Add video clip
        mainVideoTrack.clips.push({
          id: `scene-${index}`,
          type: 'video',
          name: scene.title || `Scene ${index + 1}`,
          startTime: currentTime,
          duration: sceneDuration,
          color: getSceneColor(index),
          thumbnail: scene.thumbnail,
          metadata: {
            fps: 30,
            resolution: '1920x1080',
            codec: 'h264'
          }
        });

        // Add audio clip if exists
        if (scene.audio) {
          narrationTrack.clips.push({
            id: `audio-${index}`,
            type: 'audio',
            name: `${scene.title} Audio`,
            startTime: currentTime,
            duration: sceneDuration,
            color: 'bg-orange-600',
            volume: 1
          });
        }

        // Add transitions between scenes
        if (index < storyboardData.scenes.length - 1) {
          mainVideoTrack.clips.push({
            id: `transition-${index}`,
            type: 'transition',
            name: 'Crossfade',
            startTime: currentTime + sceneDuration - 0.5,
            duration: 1,
            color: 'bg-purple-600'
          });
        }

        currentTime += sceneDuration;
      });

      // Add title overlay if exists
      if (storyboardData.title) {
        const titleTrack: TimelineTrack = {
          id: 'overlay-titles',
          name: 'Titles & Text',
          type: 'overlay',
          clips: [{
            id: 'title-main',
            type: 'text',
            name: storyboardData.title,
            startTime: 1,
            duration: 3,
            color: 'bg-yellow-600'
          }],
          height: 50
        };
        overlayTracks.push(titleTrack);
      }

      videoTracks.push(mainVideoTrack);
      audioTracks.push(narrationTrack);

      setTracks([...videoTracks, ...audioTracks, ...overlayTracks]);
      setTotalDuration(currentTime);
      setIsLoading(false);

    } catch (err) {
      console.error('Error loading timeline:', err);
      setError('Failed to load timeline data');
      setIsLoading(false);
    }
  };

  // Playback control
  useEffect(() => {
    let animationFrame: number;
    let lastTime = performance.now();

    const animate = (currentTime: number) => {
      if (!isPlaying) return;

      const deltaTime = (currentTime - lastTime) / 1000; // Convert to seconds
      lastTime = currentTime;

      setCurrentTime(prev => {
        const newTime = prev + deltaTime;
        if (newTime >= totalDuration) {
          setIsPlaying(false);
          return totalDuration;
        }
        if (onTimeUpdate) {
          onTimeUpdate(newTime);
        }
        return newTime;
      });

      animationFrame = requestAnimationFrame(animate);
    };

    if (isPlaying) {
      lastTime = performance.now();
      animationFrame = requestAnimationFrame(animate);
    }

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [isPlaying, totalDuration, onTimeUpdate]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key) {
        case SHORTCUTS.PLAY_PAUSE:
          e.preventDefault();
          handlePlayPause();
          break;
        case SHORTCUTS.SKIP_BACK:
          e.preventDefault();
          handleSeek(currentTime - 1);
          break;
        case SHORTCUTS.SKIP_FORWARD:
          e.preventDefault();
          handleSeek(currentTime + 1);
          break;
        case SHORTCUTS.ZOOM_IN:
          e.preventDefault();
          handleZoomIn();
          break;
        case SHORTCUTS.ZOOM_OUT:
          e.preventDefault();
          handleZoomOut();
          break;
        case SHORTCUTS.CUT:
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            handleCut();
          }
          break;
        case SHORTCUTS.DELETE:
          e.preventDefault();
          handleDelete();
          break;
        case SHORTCUTS.DUPLICATE:
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            handleDuplicate();
          }
          break;
        case SHORTCUTS.SELECT_ALL:
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            handleSelectAll();
          }
          break;
        case SHORTCUTS.DESELECT:
          e.preventDefault();
          setSelectedClips(new Set());
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentTime, selectedClips]);

  // Timeline notification when tracks change
  useEffect(() => {
    if (onTimelineChange) {
      onTimelineChange(tracks);
    }
  }, [tracks, onTimelineChange]);

  // Helper functions
  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (time: number) => {
    const newTime = Math.max(0, Math.min(time, totalDuration));
    setCurrentTime(newTime);
    if (onTimeUpdate) {
      onTimeUpdate(newTime);
    }
  };

  const handleZoomIn = () => {
    const currentIndex = ZOOM_LEVELS.findIndex(z => z.value === zoom);
    if (currentIndex < ZOOM_LEVELS.length - 1) {
      setZoom(ZOOM_LEVELS[currentIndex + 1].value);
    }
  };

  const handleZoomOut = () => {
    const currentIndex = ZOOM_LEVELS.findIndex(z => z.value === zoom);
    if (currentIndex > 0) {
      setZoom(ZOOM_LEVELS[currentIndex - 1].value);
    }
  };

  const handleClipClick = (clip: TimelineClip, e: React.MouseEvent) => {
    if (e.ctrlKey || e.metaKey) {
      // Multi-select
      const newSelection = new Set(selectedClips);
      if (newSelection.has(clip.id)) {
        newSelection.delete(clip.id);
      } else {
        newSelection.add(clip.id);
      }
      setSelectedClips(newSelection);
    } else {
      // Single select
      setSelectedClips(new Set([clip.id]));
    }
    
    if (onClipSelected) {
      onClipSelected(clip);
    }
  };

  const handleCut = () => {
    if (selectedClips.size === 0) return;
    
    if (onOperation) {
      onOperation({
        type: 'CUT',
        clips: Array.from(selectedClips),
        time: currentTime
      });
    }
  };

  const handleDelete = () => {
    if (selectedClips.size === 0) return;
    
    setTracks(prevTracks => 
      prevTracks.map(track => ({
        ...track,
        clips: track.clips.filter(clip => !selectedClips.has(clip.id))
      }))
    );
    
    setSelectedClips(new Set());
  };

  const handleDuplicate = () => {
    if (selectedClips.size === 0) return;
    
    setTracks(prevTracks => 
      prevTracks.map(track => {
        const newClips = [...track.clips];
        track.clips.forEach(clip => {
          if (selectedClips.has(clip.id)) {
            const duplicatedClip = {
              ...clip,
              id: `${clip.id}-copy-${Date.now()}`,
              startTime: clip.startTime + clip.duration + 0.1
            };
            newClips.push(duplicatedClip);
          }
        });
        return { ...track, clips: newClips };
      })
    );
  };

  const handleSelectAll = () => {
    const allClipIds = new Set<string>();
    tracks.forEach(track => {
      track.clips.forEach(clip => {
        allClipIds.add(clip.id);
      });
    });
    setSelectedClips(allClipIds);
  };

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!timelineRef.current) return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const timelineWidth = rect.width - 250; // Account for track labels
    const clickTime = (x - 250) / (timelineWidth * zoom) * totalDuration;
    
    if (clickTime >= 0 && clickTime <= totalDuration) {
      handleSeek(clickTime);
    }
  };

  const formatTime = (time: number) => {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);
    const frames = Math.floor((time % 1) * frameRate);
    
    if (zoom >= 5) {
      // Show frames for high zoom levels
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
    } else if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
  };

  const getClipWidth = (duration: number) => {
    const baseWidth = 1000; // Base timeline width
    return Math.max(1, (duration / totalDuration) * baseWidth * zoom);
  };

  const getClipPosition = (startTime: number) => {
    const baseWidth = 1000; // Base timeline width
    return (startTime / totalDuration) * baseWidth * zoom;
  };

  const getSceneColor = (index: number) => {
    const colors = [
      'bg-blue-600',
      'bg-green-600',
      'bg-red-600',
      'bg-purple-600',
      'bg-yellow-600',
      'bg-pink-600',
      'bg-indigo-600',
      'bg-teal-600'
    ];
    return colors[index % colors.length];
  };

  const getTrackIcon = (type: string) => {
    switch (type) {
      case 'video': return <Film className="w-4 h-4" />;
      case 'audio': return <Music className="w-4 h-4" />;
      case 'overlay': return <Type className="w-4 h-4" />;
      case 'effects': return <Sparkles className="w-4 h-4" />;
      default: return <Layers className="w-4 h-4" />;
    }
  };

  const getClipTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return <Film className="w-3 h-3" />;
      case 'audio': return <Music className="w-3 h-3" />;
      case 'text': return <Type className="w-3 h-3" />;
      case 'transition': return <Move className="w-3 h-3" />;
      case 'effect': return <Zap className="w-3 h-3" />;
      default: return null;
    }
  };

  // Generate time ruler marks
  const generateRulerMarks = useMemo(() => {
    const marks = [];
    const baseWidth = 1000 * zoom;
    let interval = 1; // 1 second default
    
    // Adjust interval based on zoom
    if (zoom < 0.25) interval = 60; // 1 minute
    else if (zoom < 0.5) interval = 30; // 30 seconds
    else if (zoom < 1) interval = 10; // 10 seconds
    else if (zoom > 5) interval = 1 / frameRate; // Show frames
    
    for (let time = 0; time <= totalDuration; time += interval) {
      const position = (time / totalDuration) * baseWidth;
      marks.push({
        time,
        position,
        major: time % (interval * 10) === 0
      });
    }
    
    return marks;
  }, [totalDuration, zoom, frameRate]);

  if (isLoading) {
    return (
      <Card className={`h-full flex items-center justify-center bg-zinc-900 border-zinc-700 ${className}`}>
        <div className="text-center">
          <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin text-blue-500" />
          <p className="text-zinc-400">Loading timeline...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`h-full flex items-center justify-center bg-zinc-900 border-zinc-700 ${className}`}>
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-4 text-red-500" />
          <p className="text-red-400">{error}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`h-full flex flex-col bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="flex-shrink-0 border-b border-zinc-700">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5" />
            Professional Timeline
            <Badge variant="outline" className="text-xs">
              {tracks.reduce((acc, track) => acc + track.clips.length, 0)} clips
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <Clock className="w-4 h-4" />
              {formatTime(currentTime)} / {formatTime(totalDuration)}
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSnapToGrid(!snapToGrid)}
                className={snapToGrid ? 'text-blue-400' : 'text-zinc-400'}
              >
                <Grid className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowWaveforms(!showWaveforms)}
                className={showWaveforms ? 'text-blue-400' : 'text-zinc-400'}
              >
                <Volume2 className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRippleEdit(!rippleEdit)}
                className={rippleEdit ? 'text-blue-400' : 'text-zinc-400'}
              >
                <Wand2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Transport Controls */}
        <div className="flex items-center gap-4 p-4 border-b border-zinc-700 bg-zinc-950">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSeek(0)}
              className="bg-zinc-800 border-zinc-600"
            >
              <SkipBack className="w-4 h-4" />
              <SkipBack className="w-4 h-4 -ml-2" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSeek(currentTime - 1)}
              className="bg-zinc-800 border-zinc-600"
            >
              <SkipBack className="w-4 h-4" />
            </Button>
            
            <Button
              onClick={handlePlayPause}
              className="bg-blue-600 hover:bg-blue-700 px-4"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSeek(currentTime + 1)}
              className="bg-zinc-800 border-zinc-600"
            >
              <SkipForward className="w-4 h-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSeek(totalDuration)}
              className="bg-zinc-800 border-zinc-600"
            >
              <SkipForward className="w-4 h-4" />
              <SkipForward className="w-4 h-4 -ml-2" />
            </Button>
          </div>

          <div className="flex items-center gap-2 text-zinc-400">
            <Volume2 className="w-4 h-4" />
            <Slider
              value={[100]}
              max={100}
              step={1}
              className="w-20"
            />
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomOut}
              disabled={zoom <= ZOOM_LEVELS[0].value}
              className="bg-zinc-800 border-zinc-600"
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            
            <div className="text-sm text-zinc-400 w-16 text-center">
              {ZOOM_LEVELS.find(z => z.value === zoom)?.label || `${Math.round(zoom * 100)}%`}
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomIn}
              disabled={zoom >= ZOOM_LEVELS[ZOOM_LEVELS.length - 1].value}
              className="bg-zinc-800 border-zinc-600"
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setZoom(1)}
              className="bg-zinc-800 border-zinc-600"
            >
              <Maximize className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Timeline Area */}
        <div 
          ref={scrollContainerRef}
          className="flex-1 overflow-auto bg-zinc-950"
        >
          <div
            ref={timelineRef}
            className="relative min-h-full"
            style={{ width: `${250 + 1000 * zoom}px` }}
            onClick={handleTimelineClick}
          >
            {/* Time Ruler */}
            <div className="sticky top-0 bg-zinc-900 border-b border-zinc-700 z-20">
              <div className="flex">
                <div className="w-[250px] p-2 border-r border-zinc-700 flex items-center justify-between">
                  <span className="text-xs text-zinc-400">Tracks</span>
                  <Badge variant="outline" className="text-xs">
                    {ZOOM_LEVELS.find(z => z.value === zoom)?.unit}
                  </Badge>
                </div>
                <div ref={rulerRef} className="flex-1 relative h-8">
                  {generateRulerMarks.map((mark, index) => (
                    <div
                      key={index}
                      className={`absolute top-0 bottom-0 ${
                        mark.major ? 'border-l-2 border-zinc-400' : 'border-l border-zinc-600'
                      }`}
                      style={{ left: `${mark.position}px` }}
                    >
                      <span className={`absolute top-1 left-1 text-xs ${
                        mark.major ? 'text-zinc-300' : 'text-zinc-500'
                      }`}>
                        {formatTime(mark.time)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Tracks */}
            {tracks.map((track) => (
              <div
                key={track.id}
                className={`flex border-b border-zinc-800 ${
                  track.collapsed ? 'h-10' : ''
                }`}
              >
                {/* Track Header */}
                <div className="w-[250px] p-3 border-r border-zinc-700 bg-zinc-900">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setTracks(prev => prev.map(t => 
                            t.id === track.id 
                              ? { ...t, collapsed: !t.collapsed }
                              : t
                          ));
                        }}
                        className="p-0 h-4 w-4"
                      >
                        {track.collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </Button>
                      {getTrackIcon(track.type)}
                      <span className="text-sm font-medium text-zinc-200">
                        {track.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setTracks(prev => prev.map(t => 
                            t.id === track.id 
                              ? { ...t, visible: !t.visible }
                              : t
                          ));
                        }}
                        className="p-1 h-6 w-6"
                      >
                        {track.visible !== false ? 
                          <Eye className="w-3 h-3 text-zinc-400" /> : 
                          <EyeOff className="w-3 h-3 text-zinc-600" />
                        }
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setTracks(prev => prev.map(t => 
                            t.id === track.id 
                              ? { ...t, locked: !t.locked }
                              : t
                          ));
                        }}
                        className="p-1 h-6 w-6"
                      >
                        {track.locked ? 
                          <Lock className="w-3 h-3 text-zinc-600" /> : 
                          <Unlock className="w-3 h-3 text-zinc-400" />
                        }
                      </Button>
                      {track.type === 'audio' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setTracks(prev => prev.map(t => 
                              t.id === track.id 
                                ? { ...t, muted: !t.muted }
                                : t
                            ));
                          }}
                          className="p-1 h-6 w-6"
                        >
                          {track.muted ? 
                            <VolumeX className="w-3 h-3 text-red-500" /> : 
                            <Volume2 className="w-3 h-3 text-zinc-400" />
                          }
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {!track.collapsed && track.volume !== undefined && (
                    <div className="flex items-center gap-2 mt-2">
                      <Volume2 className="w-3 h-3 text-zinc-400" />
                      <Slider
                        value={[track.volume * 100]}
                        max={100}
                        step={1}
                        className="flex-1"
                        onValueChange={([value]) => {
                          setTracks(prev => prev.map(t => 
                            t.id === track.id 
                              ? { ...t, volume: value / 100 }
                              : t
                          ));
                        }}
                      />
                    </div>
                  )}
                </div>

                {/* Track Content */}
                <div 
                  className="flex-1 relative bg-zinc-950"
                  style={{ 
                    height: track.collapsed ? '40px' : `${track.height || 80}px`,
                    opacity: track.visible === false ? 0.3 : 1
                  }}
                >
                  {!track.collapsed && renderedClips.get(track.id)?.map((clip) => (
                    <div
                      key={clip.id}
                      className={`absolute top-1 bottom-1 rounded cursor-pointer transition-all overflow-hidden ${
                        clip.color || 'bg-zinc-600'
                      } ${
                        selectedClips.has(clip.id) 
                          ? 'ring-2 ring-blue-400 z-10' 
                          : 'hover:brightness-110'
                      } ${
                        clip.locked || track.locked ? 'opacity-50' : ''
                      }`}
                      style={{
                        left: `${getClipPosition(clip.startTime)}px`,
                        width: `${getClipWidth(clip.duration)}px`
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!clip.locked && !track.locked) {
                          handleClipClick(clip, e);
                        }
                      }}
                      draggable={!clip.locked && !track.locked}
                      onDragStart={() => setDraggedClip(clip)}
                      onDragEnd={() => setDraggedClip(null)}
                    >
                      <div className="h-full flex flex-col justify-between p-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1 min-w-0">
                            {getClipTypeIcon(clip.type)}
                            <span className="text-xs text-white truncate">
                              {clip.name}
                            </span>
                          </div>
                          
                          {clip.effects && clip.effects.length > 0 && (
                            <Badge variant="secondary" className="text-xs h-4 px-1">
                              {clip.effects.length}fx
                            </Badge>
                          )}
                        </div>
                        
                        {showWaveforms && clip.type === 'audio' && getClipWidth(clip.duration) > 60 && (
                          <div className="flex-1 flex items-center opacity-50">
                            <div className="w-full h-8 bg-gradient-to-r from-transparent via-white to-transparent" />
                          </div>
                        )}
                        
                        {getClipWidth(clip.duration) > 80 && (
                          <div className="flex items-center justify-between text-xs text-zinc-300">
                            <span>{formatTime(clip.duration)}</span>
                            {clip.metadata?.fps && (
                              <span className="opacity-50">{clip.metadata.fps}fps</span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Resize handles */}
                      {!clip.locked && !track.locked && (
                        <>
                          <div className="absolute left-0 top-0 bottom-0 w-1 bg-white opacity-0 hover:opacity-100 cursor-ew-resize" />
                          <div className="absolute right-0 top-0 bottom-0 w-1 bg-white opacity-0 hover:opacity-100 cursor-ew-resize" />
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Playhead */}
            <div
              ref={playheadRef}
              className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-30 pointer-events-none"
              style={{ left: `${250 + getClipPosition(currentTime)}px` }}
            >
              <div className="absolute -top-2 -left-2 w-4 h-4 bg-red-500 rotate-45" />
              <div className="absolute top-8 -left-12 bg-red-500 text-white text-xs px-2 py-1 rounded">
                {formatTime(currentTime)}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Info Bar */}
        {selectedClips.size > 0 && (
          <div className="border-t border-zinc-700 p-4 bg-zinc-900">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm text-zinc-400">
                  {selectedClips.size} clip{selectedClips.size > 1 ? 's' : ''} selected
                </span>
                
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCut}
                    className="bg-zinc-800 border-zinc-600"
                  >
                    <Scissors className="w-3 h-3 mr-1" />
                    Cut
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleDuplicate}
                    className="bg-zinc-800 border-zinc-600"
                  >
                    <Layers className="w-3 h-3 mr-1" />
                    Duplicate
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleDelete}
                    className="bg-zinc-800 border-zinc-600 text-red-400 hover:text-red-300"
                  >
                    Delete
                  </Button>
                </div>
              </div>
              
              <div className="text-xs text-zinc-500">
                Press <kbd className="px-1 py-0.5 bg-zinc-800 rounded">Space</kbd> to play/pause • 
                <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">J</kbd>/<kbd className="px-1 py-0.5 bg-zinc-800 rounded">L</kbd> to skip • 
                <kbd className="px-1 py-0.5 bg-zinc-800 rounded ml-2">+</kbd>/<kbd className="px-1 py-0.5 bg-zinc-800 rounded">-</kbd> to zoom
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}