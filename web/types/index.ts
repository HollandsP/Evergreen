export interface GenerationJob {
  id: string;
  prompt: string;
  provider: 'dalle3' | 'flux1';
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
  provider: 'dalle3' | 'flux1';
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
    image: number;
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
  flux1Available: boolean;
  runwayAvailable: boolean;
  activeJobs: number;
  queueLength: number;
  systemLoad: number;
}