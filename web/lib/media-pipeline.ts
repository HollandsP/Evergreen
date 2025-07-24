/**
 * Unified Media Generation Pipeline Orchestrator
 * Manages all media generation (images, audio, video) with scene-based batch processing,
 * caching, error handling, and optimized API usage.
 */

import { cacheManager } from './cache-manager';
import { getRunwayClient } from './runway-client';
import wsManager from './websocket';
import crypto from 'crypto';

export interface SceneData {
  id: string;
  title: string;
  description: string;
  narration: string;
  imagePrompt: string;
  videoPrompt: string;
  audioSettings?: {
    voiceId?: string;
    emotion?: string;
    speed?: number;
  };
  videoSettings?: {
    duration?: number;
    cameraMovement?: string;
    motionIntensity?: number;
  };
}

export interface ProjectConfig {
  id: string;
  title: string;
  scenes: SceneData[];
  outputPath: string;
  optimizations: {
    enableCaching: boolean;
    batchSize: number;
    maxRetries: number;
    useOptimizedSettings: boolean;
  };
}

export interface GenerationProgress {
  jobId: string;
  stage: 'images' | 'audio' | 'videos' | 'assembly';
  sceneId: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error?: string;
  generatedUrl?: string;
  estimatedCost?: number;
}

export interface PipelineResult {
  success: boolean;
  jobId: string;
  totalCost: number;
  generatedAssets: {
    images: Array<{ sceneId: string; url: string; cost: number }>;
    audio: Array<{ sceneId: string; url: string; cost: number }>;
    videos: Array<{ sceneId: string; url: string; cost: number }>;
  };
  errors: Array<{ sceneId: string; stage: string; error: string }>;
  cachingStats: {
    cacheHits: number;
    cacheMisses: number;
    costSaved: number;
  };
}

export class MediaPipelineOrchestrator {
  private jobId: string;
  private projectConfig: ProjectConfig;
  private progressCallback?: (progress: GenerationProgress) => void;
  private errors: Array<{ sceneId: string; stage: string; error: string }> = [];
  private totalCost = 0;
  private cachingStats = { cacheHits: 0, cacheMisses: 0, costSaved: 0 };

  constructor(
    projectConfig: ProjectConfig,
    progressCallback?: (progress: GenerationProgress) => void
  ) {
    this.jobId = crypto.randomUUID();
    this.projectConfig = projectConfig;
    this.progressCallback = progressCallback;
  }

  /**
   * Execute the complete media generation pipeline
   */
  async execute(): Promise<PipelineResult> {
    console.log(`Starting media pipeline for project: ${this.projectConfig.title}`);
    
    const result: PipelineResult = {
      success: false,
      jobId: this.jobId,
      totalCost: 0,
      generatedAssets: {
        images: [],
        audio: [],
        videos: []
      },
      errors: [],
      cachingStats: { cacheHits: 0, cacheMisses: 0, costSaved: 0 }
    };

    try {
      // Stage 1: Generate Images
      console.log('Stage 1: Generating images...');
      const imageResults = await this.generateImages();
      result.generatedAssets.images = imageResults;

      // Stage 2: Generate Audio
      console.log('Stage 2: Generating audio...');
      const audioResults = await this.generateAudio();
      result.generatedAssets.audio = audioResults;

      // Stage 3: Generate Videos (image-to-video)
      console.log('Stage 3: Generating videos...');
      const videoResults = await this.generateVideos(imageResults);
      result.generatedAssets.videos = videoResults;

      result.success = this.errors.length === 0;
      result.totalCost = this.totalCost;
      result.errors = this.errors;
      result.cachingStats = this.cachingStats;

      console.log(`Pipeline completed. Success: ${result.success}, Total cost: $${this.totalCost.toFixed(2)}`);
      return result;

    } catch (error) {
      console.error('Pipeline execution failed:', error);
      result.success = false;
      result.errors.push({
        sceneId: 'all',
        stage: 'pipeline',
        error: error instanceof Error ? error.message : 'Unknown pipeline error'
      });
      return result;
    }
  }

  /**
   * Generate images for all scenes using DALL-E 3 with caching
   */
  private async generateImages(): Promise<Array<{ sceneId: string; url: string; cost: number }>> {
    const results: Array<{ sceneId: string; url: string; cost: number }> = [];
    const batchSize = this.projectConfig.optimizations.batchSize;

    // Process scenes in batches
    for (let i = 0; i < this.projectConfig.scenes.length; i += batchSize) {
      const batch = this.projectConfig.scenes.slice(i, i + batchSize);
      
      const batchPromises = batch.map(async (scene) => {
        try {
          return await this.generateSingleImage(scene);
        } catch (error) {
          this.handleError(scene.id, 'images', error);
          return null;
        }
      });

      const batchResults = await Promise.allSettled(batchPromises);
      
      batchResults.forEach((result, index) => {
        if (result.status === 'fulfilled' && result.value) {
          results.push(result.value);
        }
      });

      // Small delay between batches to avoid rate limiting
      if (i + batchSize < this.projectConfig.scenes.length) {
        await this.delay(1000);
      }
    }

    return results;
  }

  /**
   * Generate a single image with caching support
   */
  private async generateSingleImage(scene: SceneData): Promise<{ sceneId: string; url: string; cost: number }> {
    // Check cache first
    if (this.projectConfig.optimizations.enableCaching) {
      const cached = cacheManager.getCachedPromptResponse(
        scene.imagePrompt,
        'dall-e-3',
        0.9 // 90% similarity threshold
      );

      if (cached) {
        this.cachingStats.cacheHits++;
        this.cachingStats.costSaved += 0.04; // DALL-E 3 standard cost
        
        this.emitProgress({
          jobId: this.jobId,
          stage: 'images',
          sceneId: scene.id,
          progress: 100,
          status: 'completed',
          generatedUrl: cached.response.url,
          estimatedCost: 0 // Cached, no cost
        });

        return {
          sceneId: scene.id,
          url: cached.response.url,
          cost: 0
        };
      }
      this.cachingStats.cacheMisses++;
    }

    // Generate new image
    this.emitProgress({
      jobId: this.jobId,
      stage: 'images',
      sceneId: scene.id,
      progress: 0,
      status: 'processing',
      estimatedCost: 0.04
    });

    const response = await this.callWithRetry(
      () => this.generateImageWithDallE(scene),
      this.projectConfig.optimizations.maxRetries,
      scene.id
    );

    const cost = 0.04; // DALL-E 3 standard cost
    this.totalCost += cost;

    // Cache the result
    if (this.projectConfig.optimizations.enableCaching) {
      await cacheManager.cachePromptResponse(
        scene.imagePrompt,
        'dall-e-3',
        'openai',
        { url: response.url },
        cost,
        1.0,
        ['scene', scene.id, 'image']
      );
    }

    this.emitProgress({
      jobId: this.jobId,
      stage: 'images',
      sceneId: scene.id,
      progress: 100,
      status: 'completed',
      generatedUrl: response.url,
      estimatedCost: cost
    });

    return {
      sceneId: scene.id,
      url: response.url,
      cost
    };
  }

  /**
   * Generate audio for all scenes using ElevenLabs Turbo v2.5
   */
  private async generateAudio(): Promise<Array<{ sceneId: string; url: string; cost: number }>> {
    const results: Array<{ sceneId: string; url: string; cost: number }> = [];
    const batchSize = this.projectConfig.optimizations.batchSize;

    for (let i = 0; i < this.projectConfig.scenes.length; i += batchSize) {
      const batch = this.projectConfig.scenes.slice(i, i + batchSize);
      
      const batchPromises = batch.map(async (scene) => {
        try {
          return await this.generateSingleAudio(scene);
        } catch (error) {
          this.handleError(scene.id, 'audio', error);
          return null;
        }
      });

      const batchResults = await Promise.allSettled(batchPromises);
      
      batchResults.forEach((result) => {
        if (result.status === 'fulfilled' && result.value) {
          results.push(result.value);
        }
      });

      if (i + batchSize < this.projectConfig.scenes.length) {
        await this.delay(500); // Shorter delay for audio
      }
    }

    return results;
  }

  /**
   * Generate a single audio file with caching support
   */
  private async generateSingleAudio(scene: SceneData): Promise<{ sceneId: string; url: string; cost: number }> {
    const audioKey = `${scene.narration}-${scene.audioSettings?.voiceId || 'default'}`;
    
    // Check cache
    if (this.projectConfig.optimizations.enableCaching) {
      const cached = cacheManager.getCachedPromptResponse(
        audioKey,
        'eleven_turbo_v2_5',
        0.95 // Higher similarity for audio
      );

      if (cached) {
        this.cachingStats.cacheHits++;
        const savedCost = scene.narration.length * 0.0005; // Turbo v2.5 cost
        this.cachingStats.costSaved += savedCost;
        
        this.emitProgress({
          jobId: this.jobId,
          stage: 'audio',
          sceneId: scene.id,
          progress: 100,
          status: 'completed',
          generatedUrl: cached.response.url,
          estimatedCost: 0
        });

        return {
          sceneId: scene.id,
          url: cached.response.url,
          cost: 0
        };
      }
      this.cachingStats.cacheMisses++;
    }

    // Generate new audio
    const estimatedCost = scene.narration.length * 0.0005; // $0.0005 per character for Turbo v2.5
    
    this.emitProgress({
      jobId: this.jobId,
      stage: 'audio',
      sceneId: scene.id,
      progress: 0,
      status: 'processing',
      estimatedCost
    });

    const response = await this.callWithRetry(
      () => this.generateAudioWithElevenLabs(scene),
      this.projectConfig.optimizations.maxRetries,
      scene.id
    );

    this.totalCost += estimatedCost;

    // Cache the result
    if (this.projectConfig.optimizations.enableCaching) {
      await cacheManager.cachePromptResponse(
        audioKey,
        'eleven_turbo_v2_5',
        'elevenlabs',
        { url: response.url },
        estimatedCost,
        1.0,
        ['scene', scene.id, 'audio']
      );
    }

    this.emitProgress({
      jobId: this.jobId,
      stage: 'audio',
      sceneId: scene.id,
      progress: 100,
      status: 'completed',
      generatedUrl: response.url,
      estimatedCost
    });

    return {
      sceneId: scene.id,
      url: response.url,
      cost: estimatedCost
    };
  }

  /**
   * Generate videos using RunwayML Gen-3 Alpha Turbo
   */
  private async generateVideos(
    imageResults: Array<{ sceneId: string; url: string; cost: number }>
  ): Promise<Array<{ sceneId: string; url: string; cost: number }>> {
    const results: Array<{ sceneId: string; url: string; cost: number }> = [];
    
    // Videos are processed sequentially due to RunwayML rate limits
    for (const imageResult of imageResults) {
      const scene = this.projectConfig.scenes.find(s => s.id === imageResult.sceneId);
      if (!scene) continue;

      try {
        const videoResult = await this.generateSingleVideo(scene, imageResult.url);
        if (videoResult) {
          results.push(videoResult);
        }
      } catch (error) {
        this.handleError(scene.id, 'videos', error);
      }

      // Longer delay between video generations
      await this.delay(2000);
    }

    return results;
  }

  /**
   * Generate a single video with caching support
   */
  private async generateSingleVideo(
    scene: SceneData,
    imageUrl: string
  ): Promise<{ sceneId: string; url: string; cost: number }> {
    const videoKey = `${imageUrl}-${scene.videoPrompt}`;
    
    // Check cache
    if (this.projectConfig.optimizations.enableCaching) {
      const cached = cacheManager.getCachedPromptResponse(
        videoKey,
        'gen3a_turbo',
        0.85 // Lower similarity for videos due to uniqueness
      );

      if (cached) {
        this.cachingStats.cacheHits++;
        this.cachingStats.costSaved += 0.25; // 5s video cost
        
        this.emitProgress({
          jobId: this.jobId,
          stage: 'videos',
          sceneId: scene.id,
          progress: 100,
          status: 'completed',
          generatedUrl: cached.response.url,
          estimatedCost: 0
        });

        return {
          sceneId: scene.id,
          url: cached.response.url,
          cost: 0
        };
      }
      this.cachingStats.cacheMisses++;
    }

    // Generate new video
    const duration = scene.videoSettings?.duration || 5; // Default to 5s for cost optimization
    const estimatedCost = duration * 0.05; // Gen-3 Alpha Turbo: 5 credits/second, $0.01/credit
    
    this.emitProgress({
      jobId: this.jobId,
      stage: 'videos',
      sceneId: scene.id,
      progress: 0,
      status: 'processing',
      estimatedCost
    });

    const response = await this.callWithRetry(
      () => this.generateVideoWithRunway(scene, imageUrl),
      this.projectConfig.optimizations.maxRetries,
      scene.id
    );

    this.totalCost += estimatedCost;

    // Cache the result
    if (this.projectConfig.optimizations.enableCaching) {
      await cacheManager.cachePromptResponse(
        videoKey,
        'gen3a_turbo',
        'runway',
        { url: response.url },
        estimatedCost,
        1.0,
        ['scene', scene.id, 'video']
      );
    }

    this.emitProgress({
      jobId: this.jobId,
      stage: 'videos',
      sceneId: scene.id,
      progress: 100,
      status: 'completed',
      generatedUrl: response.url,
      estimatedCost
    });

    return {
      sceneId: scene.id,
      url: response.url,
      cost: estimatedCost
    };
  }

  /**
   * Generate image using DALL-E 3
   */
  private async generateImageWithDallE(scene: SceneData): Promise<{ url: string }> {
    const response = await fetch('/api/images/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: scene.imagePrompt,
        model: 'dall-e-3',
        size: '1024x1024', // Standard size for cost optimization
        quality: 'standard', // Use standard quality to reduce costs
        style: 'vivid',
        projectId: this.projectConfig.id,
        sceneId: scene.id
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Image generation failed');
    }

    const result = await response.json();
    return { url: result.imageUrl };
  }

  /**
   * Generate audio using ElevenLabs Turbo v2.5
   */
  private async generateAudioWithElevenLabs(scene: SceneData): Promise<{ url: string }> {
    const response = await fetch('/api/audio/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: scene.narration,
        voiceId: scene.audioSettings?.voiceId || 'pNInz6obpgDQGcFmaJgB', // Default voice
        model: 'eleven_turbo_v2_5', // Use Turbo v2.5 for 50% cost reduction
        emotion: scene.audioSettings?.emotion,
        speed: scene.audioSettings?.speed || 1.0,
        projectId: this.projectConfig.id,
        sceneId: scene.id
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Audio generation failed');
    }

    const result = await response.json();
    return { url: result.audioUrl };
  }

  /**
   * Generate video using RunwayML Gen-3 Alpha Turbo
   */
  private async generateVideoWithRunway(scene: SceneData, imageUrl: string): Promise<{ url: string }> {
    const response = await fetch('/api/videos/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        imageUrl,
        prompt: scene.videoPrompt,
        duration: scene.videoSettings?.duration || 5, // Default to 5s
        cameraMovement: scene.videoSettings?.cameraMovement || 'static',
        motionIntensity: scene.videoSettings?.motionIntensity || 50,
        projectId: this.projectConfig.id,
        sceneId: scene.id
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Video generation failed');
    }

    const result = await response.json();
    
    // Poll for completion since video generation is async
    return await this.pollForVideoCompletion(result.jobId);
  }

  /**
   * Poll for video completion using WebSocket or polling
   */
  private async pollForVideoCompletion(jobId: string): Promise<{ url: string }> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Video generation timeout'));
      }, 300000); // 5 minutes timeout

      // Listen for completion via WebSocket
      const handleVideoComplete = (data: any) => {
        if (data.jobId === jobId) {
          clearTimeout(timeout);
          if (data.status === 'completed' && data.videoUrl) {
            resolve({ url: data.videoUrl });
          } else {
            reject(new Error(data.error || 'Video generation failed'));
          }
        }
      };

      wsManager.on('video_generation_completed', handleVideoComplete);
      wsManager.on('video_generation_failed', handleVideoComplete);
    });
  }

  /**
   * Retry wrapper with exponential backoff
   */
  private async callWithRetry<T>(
    fn: () => Promise<T>,
    maxRetries: number,
    context: string
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        if (attempt === maxRetries) {
          console.error(`Final retry failed for ${context}:`, lastError);
          throw lastError;
        }

        // Exponential backoff: 2^attempt seconds
        const delay = Math.pow(2, attempt) * 1000;
        console.warn(`Retry ${attempt}/${maxRetries} for ${context} after ${delay}ms:`, lastError.message);
        await this.delay(delay);
      }
    }

    throw lastError!;
  }

  /**
   * Emit progress updates
   */
  private emitProgress(progress: GenerationProgress): void {
    if (this.progressCallback) {
      this.progressCallback(progress);
    }

    // Also emit via WebSocket for real-time updates
    wsManager.emit('pipeline_progress', progress);
  }

  /**
   * Handle and track errors
   */
  private handleError(sceneId: string, stage: string, error: unknown): void {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    this.errors.push({ sceneId, stage, error: errorMessage });
    
    console.error(`Pipeline error in ${stage} for scene ${sceneId}:`, errorMessage);
    
    this.emitProgress({
      jobId: this.jobId,
      stage: stage as any,
      sceneId,
      progress: 0,
      status: 'failed',
      error: errorMessage
    });
  }

  /**
   * Utility delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Factory function to create and execute media pipeline
 */
export async function executeMediaPipeline(
  projectConfig: ProjectConfig,
  progressCallback?: (progress: GenerationProgress) => void
): Promise<PipelineResult> {
  const pipeline = new MediaPipelineOrchestrator(projectConfig, progressCallback);
  return await pipeline.execute();
}

export default MediaPipelineOrchestrator;