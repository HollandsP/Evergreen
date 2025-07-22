import React, { useRef, useEffect, useState } from 'react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';
import { Music, Image, Film, Clock } from 'lucide-react';

interface Scene {
  id: string;
  type: string;
  speaker?: string;
  audioUrl?: string;
  audioDuration?: number;
  imageUrl?: string;
  videoUrl?: string;
  videoStatus?: string;
}

interface AudioSyncTimelineProps {
  scenes: Scene[];
  selectedScene: string | null;
  onSceneSelect: (sceneId: string) => void;
}

export default function AudioSyncTimeline({ 
  scenes, 
  selectedScene, 
  onSceneSelect, 
}: AudioSyncTimelineProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [timelineWidth, setTimelineWidth] = useState(800);
  const [hoveredScene, setHoveredScene] = useState<string | null>(null);

  // Calculate total duration
  const totalDuration = scenes.reduce((sum, scene) => sum + (scene.audioDuration || 5), 0);

  // Update timeline width based on container
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setTimelineWidth(containerRef.current.offsetWidth);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Draw audio waveform visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw waveform placeholder
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.beginPath();

    const midY = canvas.height / 2;
    const amplitude = canvas.height * 0.3;

    for (let x = 0; x < canvas.width; x += 2) {
      const t = x / canvas.width;
      const y = midY + Math.sin(t * Math.PI * 20) * amplitude * Math.random();
      
      if (x === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }

    ctx.stroke();

    // Draw center line
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(canvas.width, midY);
    ctx.stroke();
    ctx.setLineDash([]);
  }, [timelineWidth, scenes]);

  // Calculate scene position and width
  const getScenePosition = (sceneIndex: number): number => {
    const prevDuration = scenes
      .slice(0, sceneIndex)
      .reduce((sum, scene) => sum + (scene.audioDuration || 5), 0);
    return (prevDuration / totalDuration) * timelineWidth;
  };

  const getSceneWidth = (scene: Scene): number => {
    return ((scene.audioDuration || 5) / totalDuration) * timelineWidth;
  };

  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card>
      <CardContent className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium flex items-center gap-2">
            <Music className="w-4 h-4" />
            Audio-Visual Timeline
          </h3>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            Total Duration: {formatTime(totalDuration)}
          </div>
        </div>

        <div ref={containerRef} className="relative">
          {/* Waveform Canvas */}
          <canvas
            ref={canvasRef}
            width={timelineWidth}
            height={60}
            className="w-full h-[60px] opacity-20"
          />

          {/* Scene Blocks */}
          <div className="relative h-20 mt-2">
            {scenes.map((scene, index) => {
              const position = getScenePosition(index);
              const width = getSceneWidth(scene);
              const isSelected = scene.id === selectedScene;
              const isHovered = scene.id === hoveredScene;

              return (
                <div
                  key={scene.id}
                  className={cn(
                    'absolute top-0 h-full cursor-pointer transition-all duration-200 rounded-md border-2',
                    isSelected ? 'border-primary z-10' : 'border-border',
                    isHovered && !isSelected && 'border-primary/50',
                    scene.videoStatus === 'completed' ? 'bg-green-500/20' : 'bg-muted',
                  )}
                  style={{
                    left: `${position}px`,
                    width: `${width - 4}px`,
                  }}
                  onClick={() => onSceneSelect(scene.id)}
                  onMouseEnter={() => setHoveredScene(scene.id)}
                  onMouseLeave={() => setHoveredScene(null)}
                >
                  <div className="p-2 h-full flex flex-col justify-between">
                    <div className="flex items-center gap-1">
                      {scene.imageUrl && <Image className="w-3 h-3" />}
                      {scene.videoUrl && <Film className="w-3 h-3 text-green-500" />}
                      <span className="text-xs font-medium truncate">
                        {scene.id}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      {scene.speaker && (
                        <Badge variant="outline" className="text-xs px-1 py-0">
                          {scene.speaker}
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {scene.audioDuration?.toFixed(1)}s
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Time markers */}
          <div className="relative h-6 mt-2 border-t">
            {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
              const time = totalDuration * fraction;
              const position = fraction * timelineWidth;

              return (
                <div
                  key={fraction}
                  className="absolute top-0 flex flex-col items-center"
                  style={{ left: `${position}px`, transform: 'translateX(-50%)' }}
                >
                  <div className="w-px h-2 bg-border" />
                  <span className="text-xs text-muted-foreground mt-1">
                    {formatTime(time)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Legend */}
        <div className="flex gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-muted border rounded" />
            <span>Pending</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500/20 border border-green-500 rounded" />
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-1">
            <Image className="w-3 h-3" />
            <span>Has Image</span>
          </div>
          <div className="flex items-center gap-1">
            <Film className="w-3 h-3 text-green-500" />
            <span>Has Video</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
