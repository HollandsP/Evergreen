/**
 * Batch Media Generation Pipeline API Endpoint
 * Handles complete scene-based media generation with optimized batch processing
 */

import { NextApiRequest, NextApiResponse } from 'next';
import { executeMediaPipeline, ProjectConfig, PipelineResult, GenerationProgress } from '../../../lib/media-pipeline';
import { fileOrganizer } from '../../../lib/file-organizer';
import wsManager from '../../../lib/websocket';
import crypto from 'crypto';

interface BatchGenerationRequest {
  projectId: string;
  projectTitle: string;
  scenes: Array<{
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
  }>;
  optimizations?: {
    enableCaching?: boolean;
    batchSize?: number;
    maxRetries?: number;
    useOptimizedSettings?: boolean;
  };
}

interface BatchGenerationResponse {
  success: boolean;
  jobId: string;
  projectId: string;
  message: string;
  estimatedDuration: number; // in minutes
  estimatedCost: number; // in USD
  sceneCount: number;
}

// Track active pipeline jobs
const activePipelines = new Map<string, {
  jobId: string;
  projectId: string;
  startTime: number;
  status: 'running' | 'completed' | 'failed';
  progress: GenerationProgress[];
}>();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<BatchGenerationResponse | PipelineResult | { error: string }>
) {
  if (req.method === 'POST') {
    return handleBatchGeneration(req, res);
  } else if (req.method === 'GET') {
    return handleJobStatus(req, res);
  } else {
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

/**
 * Handle batch generation request
 */
async function handleBatchGeneration(
  req: NextApiRequest,
  res: NextApiResponse<BatchGenerationResponse | { error: string }>
) {
  try {
    const {
      projectId,
      projectTitle,
      scenes,
      optimizations = {}
    } = req.body as BatchGenerationRequest;

    // Validate required parameters
    if (!projectId || !projectTitle || !scenes || scenes.length === 0) {
      return res.status(400).json({
        error: 'Missing required parameters: projectId, projectTitle, and scenes'
      });
    }

    // Validate scene data
    for (const scene of scenes) {
      if (!scene.id || !scene.narration || !scene.imagePrompt || !scene.videoPrompt) {
        return res.status(400).json({
          error: `Scene ${scene.id || 'unknown'} missing required fields: id, narration, imagePrompt, videoPrompt`
        });
      }
    }

    // Check for existing active pipeline for this project
    const existingPipeline = Array.from(activePipelines.values())
      .find(p => p.projectId === projectId && p.status === 'running');
    
    if (existingPipeline) {
      return res.status(409).json({
        error: `Pipeline already running for project ${projectId}. Job ID: ${existingPipeline.jobId}`
      });
    }

    // Generate job ID and prepare configuration
    const jobId = crypto.randomUUID();
    const outputPath = `projects/${projectId}`;

    // Set default optimizations for cost and performance
    const finalOptimizations = {
      enableCaching: true,
      batchSize: 3, // Process 3 scenes at a time to balance speed and resource usage
      maxRetries: 3,
      useOptimizedSettings: true, // Use Turbo v2.5, Gen-3 Alpha, 5s default
      ...optimizations
    };

    const projectConfig: ProjectConfig = {
      id: projectId,
      title: projectTitle,
      scenes: scenes.map(scene => ({
        ...scene,
        // Apply optimized defaults
        audioSettings: {
          voiceId: scene.audioSettings?.voiceId || 'pNInz6obpgDQGcFmaJgB', // Default voice
          emotion: scene.audioSettings?.emotion,
          speed: scene.audioSettings?.speed || 1.0,
          ...scene.audioSettings
        },
        videoSettings: {
          duration: scene.videoSettings?.duration || 5, // Default to 5s for cost optimization
          cameraMovement: scene.videoSettings?.cameraMovement || 'static',
          motionIntensity: scene.videoSettings?.motionIntensity || 50,
          ...scene.videoSettings
        }
      })),
      outputPath,
      optimizations: finalOptimizations
    };

    // Calculate estimates
    const estimates = calculateEstimates(projectConfig);

    // Initialize project folder structure
    try {
      await fileOrganizer.initializeProject(
        projectId,
        projectTitle,
        scenes.map(s => s.id)
      );
    } catch (error) {
      console.error('Failed to initialize project structure:', error);
      return res.status(500).json({
        error: 'Failed to initialize project folder structure'
      });
    }

    // Track pipeline job
    activePipelines.set(jobId, {
      jobId,
      projectId,
      startTime: Date.now(),
      status: 'running',
      progress: []
    });

    // Start pipeline execution in background
    executePipelineAsync(jobId, projectConfig);

    // Return immediate response
    res.status(200).json({
      success: true,
      jobId,
      projectId,
      message: `Batch generation started for ${scenes.length} scenes`,
      estimatedDuration: estimates.durationMinutes,
      estimatedCost: estimates.totalCost,
      sceneCount: scenes.length
    });

  } catch (error) {
    console.error('Batch generation error:', error);
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to start batch generation'
    });
  }
}

/**
 * Handle job status request
 */
async function handleJobStatus(
  req: NextApiRequest,
  res: NextApiResponse<any>
) {
  const { jobId } = req.query;

  if (!jobId || typeof jobId !== 'string') {
    return res.status(400).json({ error: 'Missing jobId parameter' });
  }

  const pipeline = activePipelines.get(jobId);
  if (!pipeline) {
    return res.status(404).json({ error: 'Job not found' });
  }

  const elapsedTime = Date.now() - pipeline.startTime;
  const stages = ['images', 'audio', 'videos'];
  
  // Calculate overall progress
  const stageProgress = stages.map(stage => {
    const stageItems = pipeline.progress.filter(p => p.stage === stage);
    if (stageItems.length === 0) return 0;
    return stageItems.reduce((sum, item) => sum + item.progress, 0) / stageItems.length;
  });
  
  const overallProgress = stageProgress.reduce((sum, p) => sum + p, 0) / stages.length;

  res.status(200).json({
    jobId,
    projectId: pipeline.projectId,
    status: pipeline.status,
    progress: overallProgress,
    elapsedTime,
    stageProgress: {
      images: stageProgress[0],
      audio: stageProgress[1],
      videos: stageProgress[2]
    },
    recentProgress: pipeline.progress.slice(-10) // Last 10 progress updates
  });
}

/**
 * Execute pipeline asynchronously and handle completion
 */
async function executePipelineAsync(jobId: string, projectConfig: ProjectConfig) {
  const pipeline = activePipelines.get(jobId);
  if (!pipeline) return;

  try {
    console.log(`Starting pipeline execution for job ${jobId}`);
    
    // Progress callback to track and emit updates
    const progressCallback = (progress: GenerationProgress) => {
      pipeline.progress.push(progress);
      
      // Emit progress via WebSocket
      wsManager.emit('batch_generation_progress', {
        jobId,
        projectId: pipeline.projectId,
        ...progress
      });
      
      // Keep only last 50 progress items to prevent memory issues
      if (pipeline.progress.length > 50) {
        pipeline.progress = pipeline.progress.slice(-50);
      }
    };

    // Execute the pipeline
    const result = await executeMediaPipeline(projectConfig, progressCallback);

    // Update pipeline status
    pipeline.status = result.success ? 'completed' : 'failed';

    // Store assets in file organizer
    if (result.success) {
      await storeGeneratedAssets(projectConfig.id, result);
    }

    // Emit completion event
    wsManager.emit('batch_generation_completed', {
      jobId,
      projectId: pipeline.projectId,
      success: result.success,
      totalCost: result.totalCost,
      errors: result.errors,
      cachingStats: result.cachingStats,
      duration: Date.now() - pipeline.startTime
    });

    console.log(`Pipeline ${jobId} completed. Success: ${result.success}, Cost: $${result.totalCost.toFixed(2)}`);

    // Clean up after 1 hour
    setTimeout(() => {
      activePipelines.delete(jobId);
      console.log(`Cleaned up pipeline job ${jobId}`);
    }, 60 * 60 * 1000);

  } catch (error) {
    console.error(`Pipeline ${jobId} failed:`, error);
    
    pipeline.status = 'failed';
    
    wsManager.emit('batch_generation_failed', {
      jobId,
      projectId: pipeline.projectId,
      error: error instanceof Error ? error.message : 'Pipeline execution failed',
      duration: Date.now() - pipeline.startTime
    });
  }
}

/**
 * Store generated assets in the file organizer
 */
async function storeGeneratedAssets(projectId: string, result: PipelineResult) {
  try {
    // Store images
    for (const image of result.generatedAssets.images) {
      await fileOrganizer.storeAssetFromUrl(
        projectId,
        image.sceneId,
        'image',
        image.url,
        { cost: image.cost, generatedAt: new Date().toISOString() }
      );
    }

    // Store audio
    for (const audio of result.generatedAssets.audio) {
      await fileOrganizer.storeAssetFromUrl(
        projectId,
        audio.sceneId,
        'audio',
        audio.url,
        { cost: audio.cost, generatedAt: new Date().toISOString() }
      );
    }

    // Store videos
    for (const video of result.generatedAssets.videos) {
      await fileOrganizer.storeAssetFromUrl(
        projectId,
        video.sceneId,
        'video',
        video.url,
        { cost: video.cost, generatedAt: new Date().toISOString() }
      );
    }

    console.log(`Successfully stored ${result.generatedAssets.images.length + result.generatedAssets.audio.length + result.generatedAssets.videos.length} assets for project ${projectId}`);
  } catch (error) {
    console.error('Failed to store generated assets:', error);
  }
}

/**
 * Calculate cost and time estimates
 */
function calculateEstimates(config: ProjectConfig): {
  totalCost: number;
  durationMinutes: number;
  breakdown: {
    images: { cost: number; time: number };
    audio: { cost: number; time: number };
    videos: { cost: number; time: number };
  };
} {
  const sceneCount = config.scenes.length;
  
  // Cost calculations (optimized rates)
  const imageCost = sceneCount * 0.04; // DALL-E 3 standard
  const audioCost = config.scenes.reduce((sum, scene) => 
    sum + (scene.narration.length * 0.0005), 0); // ElevenLabs Turbo v2.5
  const videoCost = config.scenes.reduce((sum, scene) => 
    sum + ((scene.videoSettings?.duration || 5) * 0.05), 0); // Gen-3 Alpha Turbo
  
  // Time estimates (with batch processing)
  const batchSize = config.optimizations.batchSize;
  const batches = Math.ceil(sceneCount / batchSize);
  
  const imageTime = batches * 1.5; // 1.5 minutes per batch
  const audioTime = batches * 1.0; // 1 minute per batch (Turbo v2.5 is 32x faster)
  const videoTime = sceneCount * 2.0; // 2 minutes per video (Gen-3 Alpha is 7x faster)
  
  return {
    totalCost: imageCost + audioCost + videoCost,
    durationMinutes: imageTime + audioTime + videoTime,
    breakdown: {
      images: { cost: imageCost, time: imageTime },
      audio: { cost: audioCost, time: audioTime },
      videos: { cost: videoCost, time: videoTime }
    }
  };
}

/**
 * Get active pipeline status (for monitoring)
 */
export function getActivePipelines() {
  return Array.from(activePipelines.entries()).map(([jobId, pipeline]) => ({
    jobId,
    projectId: pipeline.projectId,
    status: pipeline.status,
    startTime: pipeline.startTime,
    elapsedTime: Date.now() - pipeline.startTime,
    progressCount: pipeline.progress.length
  }));
}

// Configuration for larger payload sizes
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '50mb', // Allow large scene data
    },
    responseLimit: '10mb'
  },
};