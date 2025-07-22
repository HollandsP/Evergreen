import { ProductionState, ScriptScene, AudioData, ImageData } from '@/types';
import { productionState } from '@/lib/production-state';

// Mock data generators
export const createMockScene = (id: string, overrides?: Partial<ScriptScene>): ScriptScene => ({
  id,
  timestamp: 0,
  narration: `Test narration for ${id}`,
  onScreenText: '',
  imagePrompt: `Test image prompt for ${id}`,
  metadata: {
    sceneType: 'establishing',
    description: `Test scene ${id}`,
    visual: `Visual description for ${id}`,
  },
  ...overrides,
});

export const createMockAudioData = (sceneId: string, overrides?: Partial<AudioData>): AudioData => ({
  sceneId,
  url: `/audio/${sceneId}.mp3`,
  duration: 5,
  status: 'completed',
  ...overrides,
});

export const createMockImageData = (sceneId: string, overrides?: Partial<ImageData>): ImageData => ({
  sceneId,
  url: `/images/${sceneId}.jpg`,
  prompt: `Image prompt for ${sceneId}`,
  provider: 'dalle3',
  status: 'completed',
  ...overrides,
});

// Test state setup helpers
export const setupTestState = (overrides?: Partial<ProductionState>) => {
  productionState.reset();
  
  if (overrides) {
    Object.entries(overrides).forEach(([key, value]) => {
      if (key !== 'currentStage' && key !== 'isLocked' && key !== 'lastSaved' && key !== 'projectId') {
        productionState.updateStage(key as any, value as any);
      }
    });
  }
};

// Mock WebSocket helpers
export const createMockWebSocket = () => {
  const listeners: { [event: string]: Function[] } = {};
  
  return {
    connected: true,
    on: jest.fn((event: string, callback: Function) => {
      if (!listeners[event]) listeners[event] = [];
      listeners[event].push(callback);
    }),
    emit: jest.fn(),
    disconnect: jest.fn(),
    connect: jest.fn(),
    trigger: (event: string, data: any) => {
      if (listeners[event]) {
        listeners[event].forEach(callback => callback(data));
      }
    },
  };
};

// API response mocks
export const mockApiResponses = {
  scriptParse: (scenes: ScriptScene[]) => ({
    ok: true,
    json: async () => ({ scenes, totalDuration: scenes.length * 5 }),
  }),
  
  voiceList: (voices: any[]) => ({
    ok: true,
    json: async () => ({ voices }),
  }),
  
  audioGenerate: (sceneId: string, duration = 5) => ({
    ok: true,
    json: async () => ({
      sceneId,
      url: `/audio/${sceneId}.mp3`,
      duration,
    }),
  }),
  
  audioBatch: (scenes: any[]) => ({
    ok: true,
    json: async () => ({
      success: true,
      results: scenes.map(s => ({
        sceneId: s.sceneId,
        url: `/audio/${s.sceneId}.mp3`,
        duration: 5,
      })),
    }),
  }),
  
  imageGenerate: (sceneId: string, provider = 'dalle3') => ({
    ok: true,
    json: async () => ({
      sceneId,
      url: `/images/${sceneId}.jpg`,
      provider,
      cost: provider === 'dalle3' ? 0.04 : 0,
    }),
  }),
  
  imageBatch: (scenes: any[], provider = 'dalle3') => ({
    ok: true,
    json: async () => ({
      success: true,
      results: scenes.map(s => ({
        sceneId: s.sceneId,
        url: `/images/${s.sceneId}.jpg`,
        provider,
        cost: provider === 'dalle3' ? 0.04 : 0,
      })),
      totalCost: provider === 'dalle3' ? scenes.length * 0.04 : 0,
    }),
  }),
  
  videoGenerate: (sceneId: string, duration: number) => ({
    ok: true,
    json: async () => ({
      sceneId,
      videoUrl: `/videos/${sceneId}.mp4`,
      duration,
    }),
  }),
  
  videoBatch: (scenes: any[]) => ({
    ok: true,
    json: async () => ({
      success: true,
      results: scenes.map(s => ({
        sceneId: s.sceneId,
        videoUrl: `/videos/${s.sceneId}.mp4`,
        duration: s.audioDuration || 5,
      })),
    }),
  }),
  
  assemblyExport: (format = 'mp4') => ({
    ok: true,
    json: async () => ({
      success: true,
      videoUrl: `/final/output.${format}`,
      downloadUrl: `/download/output.${format}`,
    }),
  }),
  
  error: (status: number, message: string) => ({
    ok: false,
    status,
    json: async () => ({ error: message }),
  }),
};

// Wait helpers
export const waitForCondition = async (
  condition: () => boolean,
  timeout = 5000,
  interval = 100,
): Promise<void> => {
  const startTime = Date.now();
  
  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error('Timeout waiting for condition');
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
};

// File upload helpers
export const createMockFile = (
  content: string,
  fileName: string,
  mimeType = 'text/plain',
): File => {
  return new File([content], fileName, { type: mimeType });
};

export const createMockImageFile = (fileName: string): File => {
  const canvas = document.createElement('canvas');
  canvas.width = 100;
  canvas.height = 100;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = 'blue';
  ctx.fillRect(0, 0, 100, 100);
  
  return new File([canvas.toDataURL()], fileName, { type: 'image/jpeg' });
};

// Progress tracking helpers
export class ProgressTracker {
  private values: number[] = [];
  
  record(value: number) {
    this.values.push(value);
  }
  
  get all() {
    return this.values;
  }
  
  get last() {
    return this.values[this.values.length - 1];
  }
  
  get isComplete() {
    return this.last === 100;
  }
  
  get isProgressing() {
    if (this.values.length < 2) return false;
    return this.values[this.values.length - 1] > this.values[this.values.length - 2];
  }
}
