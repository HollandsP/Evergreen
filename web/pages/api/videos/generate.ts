import { NextApiRequest, NextApiResponse } from 'next';
import { getRunwayClient } from '../../../lib/runway-client';
import wsManager from '../../../lib/websocket';
import { fileManager } from '@/lib/file-manager';
import { promises as fs } from 'fs';
import path from 'path';
import fetch from 'node-fetch';

interface VideoGenerationRequest {
  imageUrl: string;
  prompt: string;
  duration: number; // in seconds
  cameraMovement?: string;
  motionIntensity?: number;
  lipSync?: boolean;
  audioUrl?: string;
  projectId?: string;
  sceneId?: string;
}

interface VideoGenerationResponse {
  videoUrl: string;
  jobId: string;
  status: 'completed' | 'processing' | 'failed';
  duration: number;
  error?: string;
  savedPath?: string;
}

// Camera movement parameters based on dalle3_runway_prompts.py
const cameraMovementPrompts: Record<string, string> = {
  static: 'static shot, fixed camera position',
  pan_left: 'slow pan left, smooth horizontal movement',
  pan_right: 'slow pan right, smooth horizontal movement',
  zoom_in: 'gradual zoom in, moving closer to subject',
  zoom_out: 'gradual zoom out, revealing wider view',
  orbit_left: 'orbit camera left around subject, circular movement',
  orbit_right: 'orbit camera right around subject, circular movement',
  dolly_in: 'dolly forward, smooth tracking shot moving in',
  dolly_out: 'dolly backward, smooth tracking shot moving out',
  crane_up: 'crane shot moving upward, vertical elevation',
  crane_down: 'crane shot moving downward, vertical descent',
  handheld: 'handheld camera movement, subtle shake, documentary style',
};

// Save video file and metadata using centralized file manager
async function saveVideoFile(
  projectId: string,
  sceneId: string,
  videoUrl: string,
  metadata: any
): Promise<string | undefined> {
  try {
    // Download the video
    const videoResponse = await fetch(videoUrl);
    if (!videoResponse.ok) {
      throw new Error('Failed to download generated video');
    }
    
    const buffer = await videoResponse.buffer();
    
    // Generate filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `runway_${timestamp}.mp4`;
    
    // Get the path to save the video
    const videoPath = fileManager.getAssetFilePath(projectId, sceneId, 'videos', filename);
    
    // Ensure directory exists
    await fs.mkdir(path.dirname(videoPath), { recursive: true });
    
    // Save the video
    await fs.writeFile(videoPath, buffer);
    
    // Update scene metadata
    await fileManager.addAssetToScene(projectId, sceneId, 'videos', filename);
    
    // Update scene metadata with video generation details
    await fileManager.updateSceneMetadata(projectId, sceneId, {
      status: 'completed',
      prompts: {
        video: metadata.prompt
      }
    });
    
    console.log(`Saved video to: ${videoPath}`);
    return filename;
  } catch (error) {
    console.error('Failed to save video:', error);
    return undefined;
  }
}

// Save video URL metadata
async function saveVideoMetadata(
  projectId: string, 
  sceneId: string, 
  videoUrl: string,
  metadata: any
): Promise<void> {
  const scenePath = path.join(process.cwd(), 'public', 'exports', projectId, sceneId);
  const videoMetadataPath = path.join(scenePath, 'videos', 'metadata.json');
  const sceneMetadataPath = path.join(scenePath, 'metadata', 'scene.json');
  
  try {
    // Save to videos metadata
    let existingVideoData = [];
    try {
      const content = await fs.readFile(videoMetadataPath, 'utf-8');
      existingVideoData = JSON.parse(content);
    } catch {
      // File doesn't exist yet
    }
    
    // Add new video metadata
    const videoMetadata = {
      url: videoUrl,
      timestamp: new Date().toISOString(),
      ...metadata
    };
    existingVideoData.push(videoMetadata);
    
    await fs.writeFile(videoMetadataPath, JSON.stringify(existingVideoData, null, 2));
    
    // Update scene metadata
    try {
      const sceneContent = await fs.readFile(sceneMetadataPath, 'utf-8');
      const sceneData = JSON.parse(sceneContent);
      
      sceneData.assets.videos.push({
        url: videoUrl,
        jobId: metadata.jobId,
        prompt: metadata.prompt,
        duration: metadata.duration,
        timestamp: new Date().toISOString()
      });
      
      sceneData.updatedAt = new Date().toISOString();
      sceneData.status = 'has_content';
      
      await fs.writeFile(sceneMetadataPath, JSON.stringify(sceneData, null, 2));
    } catch (error) {
      console.error('Failed to update scene metadata:', error);
    }
    
  } catch (error) {
    console.error('Failed to save video metadata:', error);
  }
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<VideoGenerationResponse | { error: string }>,
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const {
      imageUrl,
      prompt,
      duration,
      cameraMovement = 'static',
      motionIntensity = 50,
      lipSync = false,
      audioUrl,
      projectId,
      sceneId,
    } = req.body as VideoGenerationRequest;

    // Validate required parameters
    if (!imageUrl || !prompt || !duration) {
      return res.status(400).json({ 
        error: 'Missing required parameters: imageUrl, prompt, and duration', 
      });
    }

    // Check for API key
    if (!process.env.RUNWAY_API_KEY) {
      return res.status(500).json({ error: 'RunwayML API key not configured' });
    }

    // Validate duration (RunwayML supports 5 or 10 seconds)
    const validDuration = duration <= 5 ? 5 : 10;

    // Build the complete prompt
    let fullPrompt = prompt;
    
    // Add camera movement to prompt
    if (cameraMovement && cameraMovementPrompts[cameraMovement]) {
      fullPrompt += `, ${cameraMovementPrompts[cameraMovement]}`;
    }

    // Add motion intensity
    const intensityDescriptor = motionIntensity < 30 ? 'subtle' : 
      motionIntensity < 70 ? 'moderate' : 
        'dynamic';
    fullPrompt += `, ${intensityDescriptor} motion`;

    // Add lip sync instructions if enabled
    if (lipSync && audioUrl) {
      fullPrompt += ', accurate lip sync to audio, natural facial expressions matching speech';
    }

    console.log('Generating video with RunwayML:', {
      imageUrl,
      fullPrompt,
      duration: validDuration,
      motionIntensity,
      lipSync,
    });

    // Initialize RunwayML client
    const runwayClient = getRunwayClient();

    // Generate video using real RunwayML API
    // Using Gen-3 Alpha Turbo (7x faster than standard)
    const task = await runwayClient.generateVideo({
      imageUrl,
      prompt: fullPrompt,
      duration: validDuration,
      model: 'gen3a_turbo', // Gen-3 Alpha Turbo - 7x faster
      ratio: '1280:768', // Gen-3 Alpha Turbo supported aspect ratio
    });

    if (task.status === 'FAILED' || !task.id) {
      console.error('RunwayML task creation failed:', task.error);
      return res.status(500).json({
        error: task.error || 'Failed to create video generation task',
      });
    }

    const jobId = task.id;
    console.log('RunwayML task created:', jobId);
    
    // Log cost estimation
    // Gen-3 Alpha Turbo: 625 credits = 78s video
    // Estimated cost per second: 625/78 = ~8 credits/second
    const estimatedCredits = validDuration * 8;
    console.log(`Estimated RunwayML cost: ${estimatedCredits} credits for ${validDuration}s video`);

    // Note: Video saving will happen after generation completes

    // Send initial WebSocket update
    wsManager.emit('video_generation_started', {
      jobId,
      projectId,
      sceneId,
      status: 'processing',
      progress: 0,
    });

    // Start polling for completion in the background
    (async () => {
      try {
        const videoUrl = await runwayClient.waitForCompletion(
          jobId,
          (progress) => {
            // Send progress updates via WebSocket
            wsManager.emit('video_generation_progress', {
              jobId,
              projectId,
              sceneId,
              progress,
            });
          },
          300, // 5 minutes timeout
          2    // 2 seconds poll interval (Gen-3 Alpha Turbo is 7x faster)
        );

        if (videoUrl) {
          // Save video file if project info provided
          let savedPath: string | undefined;
          if (projectId && sceneId) {
            savedPath = await saveVideoFile(projectId, sceneId, videoUrl, {
              jobId,
              prompt: fullPrompt,
              duration: validDuration,
              cameraMovement,
              motionIntensity,
            });
          }

          // Send completion via WebSocket
          wsManager.emit('video_generation_completed', {
            jobId,
            projectId,
            sceneId,
            videoUrl,
            savedPath,
            status: 'completed',
          });
        } else {
          // Send failure via WebSocket
          wsManager.emit('video_generation_failed', {
            jobId,
            projectId,
            sceneId,
            error: 'Video generation failed or timed out',
          });
        }
      } catch (error) {
        console.error('Background polling error:', error);
        wsManager.emit('video_generation_failed', {
          jobId,
          projectId,
          sceneId,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    })();

    // Return immediate response with job ID
    res.status(200).json({
      videoUrl: '', // Will be available after processing
      jobId,
      status: 'processing',
      duration: validDuration,
    });

  } catch (error) {
    console.error('Video generation error:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Failed to generate video. Please try again.', 
    });
  }
}

// Configuration for larger payload sizes (video generation can have large prompts)
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
  },
};
