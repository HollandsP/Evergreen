import { EventEmitter } from 'events';
import { ScriptScene, AudioData, ImageData } from '@/types';

export interface ProductionState {
  // Script Stage
  script: {
    status: 'idle' | 'uploading' | 'parsing' | 'completed' | 'error';
    fileName?: string;
    fileSize?: number;
    scenes: ScriptScene[];
    parseProgress: number;
    error?: string;
  };
  
  // Voice Selection Stage
  voice: {
    status: 'idle' | 'loading' | 'selecting' | 'completed' | 'error';
    availableVoices: VoiceOption[];
    selectedVoiceId?: string;
    selectedVoiceName?: string;
    error?: string;
  };
  
  // Audio Generation Stage
  audio: {
    status: 'idle' | 'generating' | 'completed' | 'error';
    progress: number;
    generatedAudio: AudioData[];
    totalDuration: number;
    error?: string;
  };
  
  // Image Generation Stage
  images: {
    status: 'idle' | 'generating' | 'completed' | 'error';
    progress: number;
    generatedImages: ImageData[];
    provider: 'dalle3' | 'upload';  // Flux.1 removed due to high subscription costs
    error?: string;
  };
  
  // Video Generation Stage
  video: {
    status: 'idle' | 'generating' | 'completed' | 'error';
    progress: number;
    scenes: VideoScene[];
    provider: 'runway' | 'svd' | 'modelscope';
    error?: string;
  };
  
  // Assembly Stage
  assembly: {
    status: 'idle' | 'assembling' | 'exporting' | 'completed' | 'error';
    progress: number;
    exportFormat: 'mp4' | 'webm' | 'mov';
    exportQuality: 'low' | 'medium' | 'high' | 'ultra';
    finalVideoUrl?: string;
    error?: string;
  };
  
  // Global State
  currentStage: ProductionStage;
  isLocked: boolean;
  lastSaved: Date;
  projectId: string;
}

export interface VoiceOption {
  voice_id: string;
  name: string;
  category: string;
  description?: string;
  preview_url?: string;
  labels?: Record<string, string>;
  is_winston?: boolean;
}

export interface VideoScene {
  sceneId: string;
  status: 'pending' | 'generating' | 'completed' | 'error';
  videoUrl?: string;
  imageUrl: string;
  motionPrompt?: string;
  duration: number;
  error?: string;
  metadata?: {
    provider?: string;
    processingTime?: number;
  };
}

export type ProductionStage = 
  | 'script'
  | 'voice'
  | 'audio'
  | 'images'
  | 'video'
  | 'assembly';

export type StateUpdateEvent = {
  stage: ProductionStage;
  field: string;
  value: any;
  timestamp: Date;
};

class ProductionStateManager extends EventEmitter {
  private state: ProductionState;
  private storageKey = 'evergreen_production_state';
  
  constructor() {
    super();
    this.state = this.loadState() || this.getInitialState();
  }
  
  private getInitialState(): ProductionState {
    return {
      script: {
        status: 'idle',
        scenes: [],
        parseProgress: 0,
      },
      voice: {
        status: 'idle',
        availableVoices: [],
      },
      audio: {
        status: 'idle',
        progress: 0,
        generatedAudio: [],
        totalDuration: 0,
      },
      images: {
        status: 'idle',
        progress: 0,
        generatedImages: [],
        provider: 'dalle3',
      },
      video: {
        status: 'idle',
        progress: 0,
        scenes: [],
        provider: 'runway',
      },
      assembly: {
        status: 'idle',
        progress: 0,
        exportFormat: 'mp4',
        exportQuality: 'high',
      },
      currentStage: 'script',
      isLocked: false,
      lastSaved: new Date(),
      projectId: this.generateProjectId(),
    };
  }
  
  private generateProjectId(): string {
    return `prod_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  private loadState(): ProductionState | null {
    if (typeof window === 'undefined') return null;
    
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) {
        const state = JSON.parse(saved);
        // Convert date strings back to Date objects
        state.lastSaved = new Date(state.lastSaved);
        return state;
      }
    } catch (error) {
      console.error('Failed to load production state:', error);
    }
    
    return null;
  }
  
  private saveState(): void {
    if (typeof window === 'undefined') return;
    
    try {
      this.state.lastSaved = new Date();
      localStorage.setItem(this.storageKey, JSON.stringify(this.state));
    } catch (error) {
      console.error('Failed to save production state:', error);
    }
  }
  
  public getState(): ProductionState {
    return { ...this.state };
  }
  
  public updateStage<K extends keyof ProductionState>(
    stage: K,
    updates: Partial<ProductionState[K]>,
  ): void {
    this.state[stage] = {
      ...(this.state[stage] as object),
      ...updates,
    } as ProductionState[K];
    
    this.saveState();
    
    // Emit update event
    Object.entries(updates).forEach(([field, value]) => {
      this.emit('stateUpdate', {
        stage,
        field,
        value,
        timestamp: new Date(),
      } as StateUpdateEvent);
    });
    
    // Emit WebSocket event for real-time updates
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('productionStateUpdate', {
        detail: { stage, updates },
      }));
    }
  }
  
  public setCurrentStage(stage: ProductionStage): void {
    this.state.currentStage = stage;
    this.saveState();
    this.emit('stageChange', stage);
  }
  
  public lockState(): void {
    this.state.isLocked = true;
    this.saveState();
    this.emit('stateLocked');
  }
  
  public unlockState(): void {
    this.state.isLocked = false;
    this.saveState();
    this.emit('stateUnlocked');
  }
  
  public canProceedToStage(stage: ProductionStage): boolean {
    const stages: ProductionStage[] = ['script', 'voice', 'audio', 'images', 'video', 'assembly'];
    const currentIndex = stages.indexOf(this.state.currentStage);
    const targetIndex = stages.indexOf(stage);
    
    if (targetIndex <= currentIndex) return true;
    
    // Check if previous stage is completed
    const previousStage = stages[targetIndex - 1];
    const previousState = this.state[previousStage];
    
    return previousState.status === 'completed';
  }
  
  public reset(): void {
    this.state = this.getInitialState();
    this.saveState();
    this.emit('stateReset');
  }
  
  public exportState(): string {
    return JSON.stringify(this.state, null, 2);
  }
  
  public importState(jsonState: string): void {
    try {
      const imported = JSON.parse(jsonState);
      this.state = {
        ...imported,
        lastSaved: new Date(imported.lastSaved),
      };
      this.saveState();
      this.emit('stateImported');
    } catch (error) {
      console.error('Failed to import state:', error);
      throw new Error('Invalid state format');
    }
  }
  
  public getProgress(): number {
    const stages: ProductionStage[] = ['script', 'voice', 'audio', 'images', 'video', 'assembly'];
    let totalProgress = 0;
    
    stages.forEach((stage) => {
      const stageState = this.state[stage];
      let stageProgress = 0;
      
      if (stageState.status === 'completed') {
        stageProgress = 100;
      } else if ('progress' in stageState) {
        stageProgress = stageState.progress || 0;
      }
      
      totalProgress += stageProgress;
    });
    
    return Math.round(totalProgress / stages.length);
  }
  
  public validateState(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Script validation
    if (this.state.script.status === 'completed' && this.state.script.scenes.length === 0) {
      errors.push('Script completed but no scenes found');
    }
    
    // Voice validation
    if (this.state.voice.status === 'completed' && !this.state.voice.selectedVoiceId) {
      errors.push('Voice selection completed but no voice selected');
    }
    
    // Audio validation
    if (this.state.audio.status === 'completed') {
      const expectedScenes = this.state.script.scenes.length;
      const generatedAudio = this.state.audio.generatedAudio.filter(a => a.status === 'completed').length;
      if (generatedAudio < expectedScenes) {
        errors.push(`Audio generation incomplete: ${generatedAudio}/${expectedScenes} scenes`);
      }
    }
    
    // Image validation
    if (this.state.images.status === 'completed') {
      const expectedScenes = this.state.script.scenes.length;
      const generatedImages = this.state.images.generatedImages.filter(i => i.status === 'completed').length;
      if (generatedImages < expectedScenes) {
        errors.push(`Image generation incomplete: ${generatedImages}/${expectedScenes} scenes`);
      }
    }
    
    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

// Create singleton instance
export const productionState = new ProductionStateManager();

// Export convenience functions
export const getProductionState = () => productionState.getState();
export const updateProductionStage = <K extends keyof ProductionState>(
  stage: K,
  updates: Partial<ProductionState[K]>,
) => productionState.updateStage(stage, updates);
export const setCurrentStage = (stage: ProductionStage) => productionState.setCurrentStage(stage);
export const canProceedToStage = (stage: ProductionStage) => productionState.canProceedToStage(stage);
export const resetProductionState = () => productionState.reset();
export const getProductionProgress = () => productionState.getProgress();
export const validateProductionState = () => productionState.validateState();
