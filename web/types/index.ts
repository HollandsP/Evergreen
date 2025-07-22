export interface GenerationJob {
  id: string;
  prompt: string;
  provider: 'dalle3';  // Flux.1 removed due to high subscription costs
  status: 'pending' | 'generating_image' | 'generating_video' | 'completed' | 'failed';
  progress: number;
  imageUrl?: string;
  videoUrl?: string;
  error?: string;
  createdAt: Date;
  updatedAt: Date;
  cost?: {
    imageGeneration: number;
    videoGeneration: number;
    total: number;
  };
  metadata?: {
    imageSize: string;
    videoDuration: number;
    quality: string;
  };
}

export interface PipelineStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  error?: string;
}

export interface GenerationRequest {
  prompt: string;
  provider: 'dalle3';  // Only DALL-E 3 supported
  settings: {
    imageSize: string;
    videoDuration: number;
    quality: string;
    seed?: number;
  };
}

export interface ProviderConfig {
  name: string;
  displayName: string;
  description: string;
  cost: {
    image: number;  // DALL-E 3: $0.040 for 1024x1024, $0.080 for 1792x1024
    video: number;
  };
  capabilities: {
    maxImageSize: string;
    maxVideoDuration: number;
    qualityOptions: string[];
  };
  available: boolean;
}

export interface WebSocketMessage {
  type: 'job_update' | 'step_update' | 'error' | 'connected';
  jobId?: string;
  data?: any;
}

export interface PipelineSettings {
  imageSize: string;
  videoDuration: number;
  quality: string;
  seed?: number;
  autoDownload: boolean;
  notifications: boolean;
}

export interface SystemStatus {
  dalle3Available: boolean;
  runwayAvailable: boolean;
  activeJobs: number;
  queueLength: number;
  systemLoad: number;
}

export interface ImageGenerationRequest {
  prompt: string;
  provider: 'dalle3';  // Only DALL-E 3 supported
  sceneId: string;
  size?: string;
  enhanceWithTiming?: boolean;
  audioDuration?: number;
  sceneType?: string;
}

export interface ImageGenerationResponse {
  url: string;
  provider: string;
  sceneId: string;
  cost?: number;
  processingTime?: number;
}

export interface ScriptScene {
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

export interface AudioData {
  sceneId: string;
  url: string;
  duration: number;
  status: 'pending' | 'generating' | 'completed' | 'error';
  error?: string;
}

export interface ImageData {
  sceneId: string;
  url: string;
  prompt: string;
  provider: 'dalle3' | 'upload';  // Flux.1 removed
  status: 'pending' | 'generating' | 'completed' | 'error';
  error?: string;
}

// Re-export ProductionState from production-state.ts
export type { ProductionState, ProductionStage, VoiceOption, VideoScene } from '@/lib/production-state';
