import React, { useEffect, useRef, useState } from 'react';

interface WaveformVisualizerProps {
  audioUrl: string;
  duration: number;
  isPlaying: boolean;
  height?: number;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  audioUrl,
  duration,
  isPlaying,
  height = 60,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const audioContextRef = useRef<AudioContext | null>(null);
  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const waveformDataRef = useRef<Float32Array | null>(null);

  useEffect(() => {
    // Create audio context on mount
    try {
      const context = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = context;
    } catch (error) {
      console.error('Failed to create AudioContext:', error);
      setError('Audio context not supported');
    }

    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!audioContextRef.current || !audioUrl) return;

    let isCancelled = false;
    setIsLoading(true);
    setError(null);

    // Fetch and decode audio
    const loadAudio = async () => {
      try {
        const response = await fetch(audioUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch audio: ${response.statusText}`);
        }
        
        const arrayBuffer = await response.arrayBuffer();
        if (isCancelled) return;
        
        const buffer = await audioContextRef.current!.decodeAudioData(arrayBuffer);
        if (isCancelled) return;
        
        setAudioBuffer(buffer);
        
        // Pre-calculate waveform data for performance
        const channelData = buffer.getChannelData(0);
        const samples = 1000; // Reduce samples for better performance
        const blockSize = Math.floor(channelData.length / samples);
        const waveformData = new Float32Array(samples);
        
        for (let i = 0; i < samples; i++) {
          let sum = 0;
          for (let j = 0; j < blockSize; j++) {
            sum += Math.abs(channelData[i * blockSize + j]);
          }
          waveformData[i] = sum / blockSize;
        }
        
        waveformDataRef.current = waveformData;
        setIsLoading(false);
      } catch (error) {
        if (!isCancelled) {
          console.error('Error loading audio:', error);
          setError(error instanceof Error ? error.message : 'Failed to load audio');
          setIsLoading(false);
        }
      }
    };

    loadAudio();
    
    return () => {
      isCancelled = true;
    };
  }, [audioUrl]);

  useEffect(() => {
    if (!canvasRef.current || !waveformDataRef.current || !audioBuffer) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size with device pixel ratio for crisp rendering
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    
    // Set canvas style size
    canvas.style.width = rect.width + 'px';
    canvas.style.height = height + 'px';

    // Draw static waveform once
    drawOptimizedWaveform(ctx, waveformDataRef.current, rect.width, height);

    // Animation loop for playback indicator (optimized)
    if (isPlaying) {
      const startTime = Date.now();
      let lastFrameTime = 0;
      const targetFPS = 30; // Limit to 30fps for better performance
      const frameInterval = 1000 / targetFPS;
      
      const animate = (currentTime: number) => {
        if (currentTime - lastFrameTime < frameInterval) {
          animationRef.current = requestAnimationFrame(animate);
          return;
        }
        
        lastFrameTime = currentTime;
        const elapsed = (Date.now() - startTime) / 1000;
        const progress = Math.min(elapsed / duration, 1);
        
        // Only redraw the indicator, not the entire waveform
        ctx.clearRect(0, 0, rect.width, height);
        drawOptimizedWaveform(ctx, waveformDataRef.current!, rect.width, height);
        drawPlaybackIndicator(ctx, progress, rect.width, height);
        
        if (progress < 1 && isPlaying) {
          animationRef.current = requestAnimationFrame(animate);
        }
      };
      animationRef.current = requestAnimationFrame(animate);
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [audioBuffer, waveformDataRef.current, isPlaying, duration, height]);

  const drawOptimizedWaveform = (
    ctx: CanvasRenderingContext2D,
    waveformData: Float32Array,
    width: number,
    height: number,
  ) => {
    // Clear canvas with background
    ctx.fillStyle = '#f3f4f6';
    ctx.fillRect(0, 0, width, height);

    const amp = height / 2;
    const barWidth = width / waveformData.length;
    
    // Draw waveform bars (optimized approach)
    ctx.fillStyle = '#6366f1';
    
    for (let i = 0; i < waveformData.length; i++) {
      const barHeight = waveformData[i] * amp;
      const x = i * barWidth;
      const y = amp - barHeight / 2;
      
      ctx.fillRect(x, y, Math.max(barWidth - 1, 1), barHeight);
    }

    // Draw center line
    ctx.beginPath();
    ctx.moveTo(0, amp);
    ctx.lineTo(width, amp);
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth = 1;
    ctx.stroke();
  };

  const drawPlaybackIndicator = (
    ctx: CanvasRenderingContext2D,
    progress: number,
    width: number,
    height: number,
  ) => {
    const x = progress * width;
    
    // Draw progress overlay
    ctx.fillStyle = 'rgba(99, 102, 241, 0.1)';
    ctx.fillRect(0, 0, x, height);
    
    // Draw playhead
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.strokeStyle = '#4f46e5';
    ctx.lineWidth = 2;
    ctx.stroke();
  };

  return (
    <div className="relative w-full" style={{ height: `${height}px` }}>
      <canvas
        ref={canvasRef}
        className="w-full h-full rounded"
        style={{ height: `${height}px` }}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600" />
            <div className="text-sm text-gray-500">Loading waveform...</div>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded border border-red-200">
          <div className="text-sm text-red-600">Error: {error}</div>
        </div>
      )}
    </div>
  );
};

export default WaveformVisualizer;
