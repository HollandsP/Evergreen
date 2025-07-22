import axios from 'axios';
import { GenerationRequest, GenerationJob, SystemStatus } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
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
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
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
};

export default api;