import { Server as SocketIOServer } from 'socket.io';
import type { NextApiResponse } from 'next';
import type { Server as HttpServer } from 'http';

type ExtendedNextApiResponse = NextApiResponse & {
  socket: {
    server: HttpServer & {
      io?: SocketIOServer;
    };
  };
};

export interface ProgressEvent {
  jobId: string;
  stage: 'script_parsing' | 'image_generation' | 'audio_generation' | 'video_generation';
  progress: number;
  status: 'started' | 'progress' | 'completed' | 'failed';
  data?: any;
}

export interface ScriptParsingProgress {
  progress: number;
  currentScene: number;
  totalScenes: number;
  message?: string;
}

export interface ImageGenerationProgress {
  progress: number;
  imageUrl?: string;
  sceneId: string;
  message?: string;
}

export interface AudioGenerationProgress {
  progress: number;
  audioUrl?: string;
  duration?: number;
  voiceId?: string;
  message?: string;
}

export interface VideoGenerationProgress {
  progress: number;
  status: string;
  eta?: number;
  videoUrl?: string;
  message?: string;
}

export function getSocketServer(res: ExtendedNextApiResponse): SocketIOServer | null {
  if (!res.socket.server.io) {
    console.warn('Socket.IO server not initialized');
    return null;
  }
  return res.socket.server.io;
}

export function emitProgress(
  io: SocketIOServer | null,
  event: ProgressEvent
) {
  if (!io) {
    console.warn('Cannot emit progress: Socket.IO server not available');
    return;
  }

  const { jobId, stage, progress, status, data } = event;
  
  // Emit to job-specific room
  io.to(`job:${jobId}`).emit('job_update', {
    id: jobId,
    stage,
    progress,
    status,
    updatedAt: new Date().toISOString(),
  });

  // Emit stage-specific update
  switch (stage) {
    case 'script_parsing':
      io.to(`job:${jobId}`).emit('script_parsing_progress', {
        ...data as ScriptParsingProgress,
        jobId,
        progress,
        status,
        timestamp: new Date().toISOString(),
      });
      break;

    case 'image_generation':
      io.to(`job:${jobId}`).emit('image_generation_progress', {
        ...data as ImageGenerationProgress,
        jobId,
        progress,
        status,
        timestamp: new Date().toISOString(),
      });
      break;

    case 'audio_generation':
      io.to(`job:${jobId}`).emit('audio_generation_progress', {
        ...data as AudioGenerationProgress,
        jobId,
        progress,
        status,
        timestamp: new Date().toISOString(),
      });
      break;

    case 'video_generation':
      io.to(`job:${jobId}`).emit('video_generation_progress', {
        ...data as VideoGenerationProgress,
        jobId,
        progress,
        status,
        timestamp: new Date().toISOString(),
      });
      break;
  }

  // Emit step update for workflow visualizer
  io.to(`job:${jobId}`).emit('step_update', {
    id: stage,
    name: getStageDisplayName(stage),
    status: mapStatusToStepStatus(status),
    progress,
    startTime: status === 'started' ? new Date().toISOString() : undefined,
    endTime: status === 'completed' || status === 'failed' ? new Date().toISOString() : undefined,
    error: status === 'failed' ? data?.message : undefined,
  });
}

function getStageDisplayName(stage: string): string {
  const names: Record<string, string> = {
    script_parsing: 'Script Parsing',
    image_generation: 'Image Generation',
    audio_generation: 'Audio Generation',
    video_generation: 'Video Generation',
  };
  return names[stage] || stage;
}

function mapStatusToStepStatus(status: string): 'pending' | 'running' | 'completed' | 'failed' {
  switch (status) {
    case 'started':
    case 'progress':
      return 'running';
    case 'completed':
      return 'completed';
    case 'failed':
      return 'failed';
    default:
      return 'pending';
  }
}

// Helper to emit job completion
export function emitJobCompleted(
  io: SocketIOServer | null,
  jobId: string,
  jobData: any
) {
  if (!io) return;

  io.to(`job:${jobId}`).emit('job_completed', {
    ...jobData,
    status: 'completed',
    completedAt: new Date().toISOString(),
  });
}

// Helper to emit job failure
export function emitJobFailed(
  io: SocketIOServer | null,
  jobId: string,
  error: string
) {
  if (!io) return;

  io.to(`job:${jobId}`).emit('job_failed', {
    id: jobId,
    status: 'failed',
    error,
    failedAt: new Date().toISOString(),
  });
}

// Helper to emit system status updates
export function emitSystemStatus(
  io: SocketIOServer | null,
  status: any
) {
  if (!io) return;

  io.to('system').emit('system_status', {
    ...status,
    timestamp: new Date().toISOString(),
  });
}