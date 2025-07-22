import axios from 'axios';
import { 
  GenerationRequest, 
  GenerationJob, 
  SystemStatus,
  ScriptScene,
  AudioData,
  ImageData,
  ImageGenerationRequest,
  ImageGenerationResponse,
} from '@/types';
import { 
  ProductionState, 
  ProductionStage, 
  VoiceOption,
  VideoScene, 
} from '@/lib/production-state';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const INTERNAL_API_URL = process.env.NEXT_PUBLIC_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate axios instance for internal API routes
const internalApi = axios.create({
  baseURL: INTERNAL_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  },
);

export const apiClient = {
  // Generation endpoints
  async createGeneration(request: GenerationRequest): Promise<GenerationJob> {
    const response = await api.post('/api/generate', request);
    return response.data;
  },

  async getJob(jobId: string): Promise<GenerationJob> {
    const response = await api.get(`/api/jobs/${jobId}`);
    return response.data;
  },

  async getJobs(): Promise<GenerationJob[]> {
    const response = await api.get('/api/jobs');
    return response.data;
  },

  async cancelJob(jobId: string): Promise<void> {
    await api.delete(`/api/jobs/${jobId}`);
  },

  async downloadMedia(jobId: string, type: 'image' | 'video'): Promise<Blob> {
    const response = await api.get(`/api/jobs/${jobId}/download/${type}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // System status
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await api.get('/api/status');
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await api.get('/api/health');
      return true;
    } catch {
      return false;
    }
  },

  // Production state management
  async getProductionState(): Promise<{
    state: ProductionState;
    progress: number;
    validation: any;
  }> {
    const response = await internalApi.get('/api/production/state');
    return response.data;
  },

  async updateProductionState(stage: ProductionStage, updates: any): Promise<void> {
    await internalApi.post('/api/production/state', { stage, updates });
  },

  async setProductionStage(targetStage: ProductionStage): Promise<void> {
    await internalApi.post('/api/production/state', { 
      action: 'setStage', 
      targetStage, 
    });
  },

  async resetProductionState(): Promise<void> {
    await internalApi.post('/api/production/state', { action: 'reset' });
  },

  // Script processing
  async parseScript(content: string, fileName?: string): Promise<{
    scenes: ScriptScene[];
    totalDuration: number;
    characterCount: number;
    metadata: any;
  }> {
    const response = await internalApi.post('/api/script/parse', { content, fileName });
    return response.data;
  },

  async uploadScript(file: File): Promise<{
    scenes: ScriptScene[];
    totalDuration: number;
    fileName: string;
    fileSize: number;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await internalApi.post('/api/script/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Voice management
  async listVoices(): Promise<{
    voices: VoiceOption[];
    total: number;
    winston_count: number;
  }> {
    const response = await internalApi.get('/api/voice/list');
    return response.data;
  },

  // Audio generation
  async generateAudioBatch(
    scenes: ScriptScene[],
    voiceId: string,
    settings?: any,
  ): Promise<{
    audioData: AudioData[];
    totalDuration: number;
    totalCost: number;
    processingTime: number;
  }> {
    const response = await internalApi.post('/api/audio/batch', {
      scenes,
      voiceId,
      settings,
    });
    return response.data;
  },

  // Image generation
  async generateImagesBatch(
    scenes: ScriptScene[],
    settings?: {
      size?: '1024x1024' | '1792x1024' | '1024x1792';
      quality?: 'standard' | 'hd';
      style?: 'vivid' | 'natural';
    },
  ): Promise<{
    imageData: ImageData[];
    totalCost: number;
    processingTime: number;
  }> {
    const response = await internalApi.post('/api/images/batch', {
      scenes,
      settings,
    });
    return response.data;
  },

  // Video generation
  async generateVideosBatch(
    scenes: Array<{
      sceneId: string;
      imageUrl: string;
      audioUrl: string;
      duration: number;
    }>,
    settings?: any,
  ): Promise<{
    videoData: VideoScene[];
    totalCost: number;
    processingTime: number;
  }> {
    const response = await internalApi.post('/api/videos/batch', {
      scenes,
      settings,
    });
    return response.data;
  },

  // Individual image generation (existing)
  async generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
    const response = await internalApi.post('/api/images/generate', request);
    return response.data;
  },
};

export default api;
