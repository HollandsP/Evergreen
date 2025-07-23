import React, { useState, useRef, useEffect } from 'react';
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
  Scissors,
  Move,
  Clock,
  Film,
  Music,
  Type,
  Layers
} from 'lucide-react';

interface TimelineClip {
  id: string;
  type: 'video' | 'audio' | 'text' | 'transition';
  name: string;
  startTime: number;
  duration: number;
  source?: string;
  color?: string;
  locked?: boolean;
}

interface TimelineTrack {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'overlay';
  clips: TimelineClip[];
  muted?: boolean;
  volume?: number;
}

interface EditingTimelineProps {
  projectId: string;
  storyboardData?: any;
  onClipSelected?: (clip: TimelineClip) => void;
  onTimelineChange?: (tracks: TimelineTrack[]) => void;
  className?: string;
}

export default function EditingTimeline({ 
  projectId: _projectId, 
  storyboardData: _storyboardData, 
  onClipSelected,
  onTimelineChange,
  className = '' 
}: EditingTimelineProps) {
  const [tracks, setTracks] = useState<TimelineTrack[]>([
    {
      id: 'video-1',
      name: 'Video Track',
      type: 'video',
      clips: [
        {
          id: 'scene-1',
          type: 'video',
          name: 'Scene 1: Rooftop',
          startTime: 0,
          duration: 8.5,
          color: 'bg-blue-600'
        },
        {
          id: 'transition-1',
          type: 'transition',
          name: 'Fade',
          startTime: 8.5,
          duration: 1,
          color: 'bg-purple-600'
        },
        {
          id: 'scene-2',
          type: 'video',
          name: 'Scene 2: Server Room',
          startTime: 9.5,
          duration: 12.3,
          color: 'bg-green-600'
        },
        {
          id: 'scene-3',
          type: 'video',
          name: 'Scene 3: Control Room',
          startTime: 21.8,
          duration: 10.7,
          color: 'bg-red-600'
        }
      ]
    },
    {
      id: 'audio-1',
      name: 'Narration',
      type: 'audio',
      clips: [
        {
          id: 'narration-1',
          type: 'audio',
          name: 'Scene 1 Audio',
          startTime: 0,
          duration: 8.5,
          color: 'bg-orange-600'
        },
        {
          id: 'narration-2',
          type: 'audio',
          name: 'Scene 2 Audio',
          startTime: 9.5,
          duration: 12.3,
          color: 'bg-orange-600'
        },
        {
          id: 'narration-3',
          type: 'audio',
          name: 'Scene 3 Audio',
          startTime: 21.8,
          duration: 10.7,
          color: 'bg-orange-600'
        }
      ],
      volume: 0.8
    },
    {
      id: 'overlay-1',
      name: 'Text Overlays',
      type: 'overlay',
      clips: [
        {
          id: 'title-1',
          type: 'text',
          name: 'Opening Title',
          startTime: 1,
          duration: 3,
          color: 'bg-yellow-600'
        },
        {
          id: 'ending-1',
          type: 'text',
          name: 'THE END',
          startTime: 29,
          duration: 3.5,
          color: 'bg-yellow-600'
        }
      ]
    }
  ]);

  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [totalDuration] = useState(32.5);
  const [zoom, setZoom] = useState(1);
  const [selectedClip, setSelectedClip] = useState<TimelineClip | null>(null);
  const [_draggedClip, setDraggedClip] = useState<TimelineClip | null>(null);

  const timelineRef = useRef<HTMLDivElement>(null);
  const playheadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTime(prev => {
          if (prev >= totalDuration) {
            setIsPlaying(false);
            return totalDuration;
          }
          return prev + 0.1;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying, totalDuration]);

  useEffect(() => {
    if (onTimelineChange) {
      onTimelineChange(tracks);
    }
  }, [tracks, onTimelineChange]);

  const handlePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (time: number) => {
    setCurrentTime(Math.max(0, Math.min(time, totalDuration)));
  };

  const handleClipClick = (clip: TimelineClip) => {
    setSelectedClip(clip);
    if (onClipSelected) {
      onClipSelected(clip);
    }
  };

  const handleClipDragStart = (clip: TimelineClip) => {
    setDraggedClip(clip);
  };

  const handleClipDragEnd = () => {
    setDraggedClip(null);
  };

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!timelineRef.current) return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const timelineWidth = rect.width - 200; // Account for track labels
    const clickTime = (x - 200) / (timelineWidth * zoom) * totalDuration;
    
    handleSeek(clickTime);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = (time % 60).toFixed(1);
    return `${minutes}:${seconds.padStart(4, '0')}`;
  };

  const getClipWidth = (duration: number) => {
    const timelineWidth = 800; // Base timeline width
    return (duration / totalDuration) * timelineWidth * zoom;
  };

  const getClipPosition = (startTime: number) => {
    const timelineWidth = 800; // Base timeline width
    return (startTime / totalDuration) * timelineWidth * zoom;
  };

  const getTrackIcon = (type: string) => {
    switch (type) {
      case 'video': return <Film className="w-4 h-4" />;
      case 'audio': return <Music className="w-4 h-4" />;
      case 'overlay': return <Type className="w-4 h-4" />;
      default: return <Layers className="w-4 h-4" />;
    }
  };

  const getClipTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return <Film className="w-3 h-3" />;
      case 'audio': return <Music className="w-3 h-3" />;
      case 'text': return <Type className="w-3 h-3" />;
      case 'transition': return <Move className="w-3 h-3" />;
      default: return null;
    }
  };

  return (
    <Card className={`h-full flex flex-col bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="flex-shrink-0 border-b border-zinc-700">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5" />
            Video Timeline
          </div>
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <Clock className="w-4 h-4" />
            {formatTime(currentTime)} / {formatTime(totalDuration)}
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Transport Controls */}
        <div className="flex items-center gap-4 p-4 border-b border-zinc-700">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSeek(currentTime - 5)}
              className="bg-zinc-800 border-zinc-600"
            >
              <SkipBack className="w-4 h-4" />
            </Button>
            
            <Button
              onClick={handlePlay}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSeek(currentTime + 5)}
              className="bg-zinc-800 border-zinc-600"
            >
              <SkipForward className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center gap-2 text-zinc-400">
            <Volume2 className="w-4 h-4" />
            <Slider
              value={[80]}
              max={100}
              step={1}
              className="w-20"
            />
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <span className="text-sm text-zinc-400">Zoom:</span>
            <Slider
              value={[zoom]}
              min={0.5}
              max={3}
              step={0.1}
              onValueChange={([value]) => setZoom(value)}
              className="w-20"
            />
            <span className="text-xs text-zinc-500 w-8">{zoom.toFixed(1)}x</span>
          </div>
        </div>

        {/* Timeline Area */}
        <div className="flex-1 overflow-auto">
          <div
            ref={timelineRef}
            className="relative min-h-full bg-zinc-950"
            onClick={handleTimelineClick}
          >
            {/* Time Ruler */}
            <div className="sticky top-0 bg-zinc-900 border-b border-zinc-700 z-10">
              <div className="flex">
                <div className="w-48 p-2 border-r border-zinc-700">
                  <span className="text-xs text-zinc-400">Time</span>
                </div>
                <div className="flex-1 relative h-8">
                  {Array.from({ length: Math.ceil(totalDuration) + 1 }, (_, i) => (
                    <div
                      key={i}
                      className="absolute top-0 bottom-0 border-l border-zinc-600"
                      style={{ left: `${getClipPosition(i)}px` }}
                    >
                      <span className="absolute top-1 left-1 text-xs text-zinc-400">
                        {formatTime(i)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Tracks */}
            {tracks.map((track, _trackIndex) => (
              <div
                key={track.id}
                className="flex border-b border-zinc-800"
              >
                {/* Track Header */}
                <div className="w-48 p-3 border-r border-zinc-700 bg-zinc-900">
                  <div className="flex items-center gap-2 mb-1">
                    {getTrackIcon(track.type)}
                    <span className="text-sm font-medium text-zinc-200">
                      {track.name}
                    </span>
                  </div>
                  {track.volume !== undefined && (
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
                <div className="flex-1 relative h-16 bg-zinc-950">
                  {track.clips.map((clip) => (
                    <div
                      key={clip.id}
                      className={`absolute top-1 bottom-1 rounded cursor-pointer transition-all ${
                        clip.color || 'bg-zinc-600'
                      } ${
                        selectedClip?.id === clip.id 
                          ? 'ring-2 ring-blue-400' 
                          : 'hover:brightness-110'
                      } ${
                        clip.locked ? 'opacity-50' : ''
                      }`}
                      style={{
                        left: `${getClipPosition(clip.startTime)}px`,
                        width: `${getClipWidth(clip.duration)}px`
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleClipClick(clip);
                      }}
                      draggable={!clip.locked}
                      onDragStart={() => handleClipDragStart(clip)}
                      onDragEnd={handleClipDragEnd}
                    >
                      <div className="h-full flex items-center justify-between px-2 text-white">
                        <div className="flex items-center gap-1 min-w-0">
                          {getClipTypeIcon(clip.type)}
                          <span className="text-xs truncate">
                            {clip.name}
                          </span>
                        </div>
                        
                        {getClipWidth(clip.duration) > 60 && (
                          <div className="flex items-center gap-1">
                            <Badge variant="secondary" className="text-xs">
                              {formatTime(clip.duration)}
                            </Badge>
                            {!clip.locked && (
                              <Scissors className="w-3 h-3 opacity-50 hover:opacity-100" />
                            )}
                          </div>
                        )}
                      </div>

                      {/* Resize handles */}
                      {!clip.locked && (
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
              className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-20 pointer-events-none"
              style={{ left: `${200 + getClipPosition(currentTime)}px` }}
            >
              <div className="absolute -top-2 -left-2 w-4 h-4 bg-red-500 rotate-45" />
            </div>
          </div>
        </div>

        {/* Clip Details Panel */}
        {selectedClip && (
          <div className="border-t border-zinc-700 p-4 bg-zinc-900">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-white">
                Selected: {selectedClip.name}
              </h3>
              <Badge variant="outline">
                {selectedClip.type}
              </Badge>
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-zinc-400">Start:</span>
                <p className="text-white">{formatTime(selectedClip.startTime)}</p>
              </div>
              <div>
                <span className="text-zinc-400">Duration:</span>
                <p className="text-white">{formatTime(selectedClip.duration)}</p>
              </div>
              <div>
                <span className="text-zinc-400">End:</span>
                <p className="text-white">
                  {formatTime(selectedClip.startTime + selectedClip.duration)}
                </p>
              </div>
            </div>

            <div className="flex gap-2 mt-3">
              <Button
                size="sm"
                variant="outline"
                className="bg-zinc-800 border-zinc-600"
              >
                <Scissors className="w-3 h-3 mr-1" />
                Split
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="bg-zinc-800 border-zinc-600"
              >
                <Move className="w-3 h-3 mr-1" />
                Move
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="bg-zinc-800 border-zinc-600"
              >
                <Type className="w-3 h-3 mr-1" />
                Effects
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}