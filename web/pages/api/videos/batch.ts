import type { NextApiRequest, NextApiResponse } from 'next';
import { updateProductionStage, VideoScene } from '@/lib/production-state';

interface BatchVideoRequest {
  scenes: Array<{
    sceneId: string;
    imageUrl: string;
    audioUrl: string;
    duration: number;
  }>;
  settings?: {
    motion_bucket_id?: number; // 1-255, higher = more motion
    fps?: number; // 4-30
    aspect_ratio?: string;
  };
}

interface BatchVideoResponse {
  videoData: VideoScene[];
  totalCost: number;
  processingTime: number;
}

// Mock video generation for development
async function generateMockVideo(scene: BatchVideoRequest['scenes'][0]): Promise<VideoScene> {
  // Simulate processing delay (videos take longer)
  await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 3000));
  
  // Generate a mock video URL
  const mockVideoUrl = `https://storage.googleapis.com/evergreen-mock-videos/scene-${scene.sceneId}.mp4`;
  
  return {
    sceneId: scene.sceneId,
    videoUrl: mockVideoUrl,
    imageUrl: scene.imageUrl,
    duration: scene.duration,
    status: 'completed' as const,
  };
}

// Generate video with Runway Gen-2 or similar
async function generateRunwayVideo(
  scene: BatchVideoRequest['scenes'][0],
  settings?: BatchVideoRequest['settings'],
): Promise<VideoScene> {
  const apiKey = process.env.RUNWAY_API_KEY;
  
  if (!apiKey) {
    throw new Error('Runway API key not configured');
  }
  
  try {
    // Note: This is a placeholder for the actual Runway API implementation
    // Runway's API is not publicly available yet, so this would need to be updated
    // when they release their API or use an alternative like Stability AI's video API
    
    const response = await fetch('https://api.runwayml.com/v1/generate/video', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_url: scene.imageUrl,
        audio_url: scene.audioUrl,
        duration: scene.duration,
        motion_bucket_id: settings?.motion_bucket_id || 127, // Medium motion
        fps: settings?.fps || 24,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Runway API error: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Runway typically returns a job ID that needs to be polled
    // For simplicity, we'll assume it returns a video URL directly
    const videoUrl = data.video_url || data.url;
    
    if (!videoUrl) {
      throw new Error('No video URL returned from Runway');
    }
    
    return {
      sceneId: scene.sceneId,
      videoUrl,
      imageUrl: scene.imageUrl,
      duration: scene.duration,
      status: 'completed' as const,
    };
  } catch (error) {
    console.error(`Failed to generate video for scene ${scene.sceneId}:`, error);
    return {
      sceneId: scene.sceneId,
      videoUrl: '',
      imageUrl: scene.imageUrl,
      duration: scene.duration,
      status: 'error' as const,
      error: error instanceof Error ? error.message : 'Failed to generate video',
    };
  }
}

// Alternative: Generate video with image animation (simpler approach)
async function generateSimpleVideo(
  scene: BatchVideoRequest['scenes'][0],
): Promise<VideoScene> {
  // This would use FFmpeg or a similar tool to create a video from an image + audio
  // For now, return a mock result
  
  return {
    sceneId: scene.sceneId,
    videoUrl: `https://storage.googleapis.com/evergreen-videos/simple-${scene.sceneId}.mp4`,
    imageUrl: scene.imageUrl,
    duration: scene.duration,
    status: 'completed' as const,
  };
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version',
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
    return;
  }

  try {
    const { scenes, settings } = req.body as BatchVideoRequest;

    if (!scenes || !Array.isArray(scenes) || scenes.length === 0) {
      return res.status(400).json({ error: 'No scenes provided' });
    }

    const startTime = Date.now();
    
    // Update state to generating
    updateProductionStage('video', {
      status: 'generating',
      progress: 0,
      scenes: [],
      error: undefined,
    });

    // Send WebSocket notification
    if (global.io) {
      global.io.emit('videos:batchStart', {
        sceneCount: scenes.length,
        settings,
        timestamp: new Date().toISOString(),
      });
    }

    const videoResults: VideoScene[] = [];
    const useRunway = process.env.RUNWAY_API_KEY && process.env.USE_RUNWAY === 'true';
    const useMockData = !useRunway || process.env.USE_MOCK_VIDEOS === 'true';

    // Process videos in parallel batches
    const batchSize = useMockData ? 3 : 1; // Video generation is resource-intensive
    
    for (let i = 0; i < scenes.length; i += batchSize) {
      const batch = scenes.slice(i, Math.min(i + batchSize, scenes.length));
      
      // Process batch in parallel
      const batchPromises = batch.map(async (scene) => {
        try {
          if (useMockData) {
            return await generateMockVideo(scene);
          } else if (useRunway) {
            return await generateRunwayVideo(scene, settings);
          } else {
            // Fallback to simple video generation
            return await generateSimpleVideo(scene);
          }
        } catch (error) {
          // Return error result but don't throw
          return {
            sceneId: scene.sceneId,
            videoUrl: '',
            imageUrl: scene.imageUrl,
            duration: scene.duration,
            status: 'error' as const,
            error: error instanceof Error ? error.message : 'Failed to generate video',
          };
        }
      });
      
      const batchResults = await Promise.all(batchPromises);
      videoResults.push(...batchResults);
      
      // Update progress
      const progress = Math.round((videoResults.length / scenes.length) * 100);
      updateProductionStage('video', {
        progress,
        scenes: videoResults,
      });
      
      // Send progress update
      if (global.io) {
        global.io.emit('videos:batchProgress', {
          progress,
          generatedScenes: videoResults.length,
          totalScenes: scenes.length,
          timestamp: new Date().toISOString(),
        });
      }
      
      // Add delay between batches for API rate limits
      if (i + batchSize < scenes.length && useRunway) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5 seconds between batches
      }
    }

    // Calculate totals
    const successCount = videoResults.filter(v => v.status === 'completed').length;
    const errorCount = videoResults.filter(v => v.status === 'error').length;
    
    // Calculate cost (estimated)
    // Runway: ~$0.05 per second of video
    // Simple/FFmpeg: ~$0.01 per video (compute cost)
    let totalCost = 0;
    if (!useMockData) {
      if (useRunway) {
        const totalSeconds = scenes.reduce((sum, scene) => sum + scene.duration, 0);
        totalCost = totalSeconds * 0.05;
      } else {
        totalCost = successCount * 0.01;
      }
    }
    
    const processingTime = (Date.now() - startTime) / 1000;

    // Update state with results
    updateProductionStage('video', {
      status: 'completed',
      progress: 100,
      scenes: videoResults,
    });

    // Send completion notification
    if (global.io) {
      global.io.emit('videos:batchComplete', {
        successCount,
        errorCount,
        processingTime,
        totalCost,
        timestamp: new Date().toISOString(),
      });
    }

    const response: BatchVideoResponse = {
      videoData: videoResults,
      totalCost,
      processingTime,
    };

    res.status(200).json(response);
  } catch (error) {
    console.error('Video batch generation error:', error);
    
    updateProductionStage('video', {
      status: 'error',
      error: error instanceof Error ? error.message : 'Failed to generate videos',
    });

    if (global.io) {
      global.io.emit('videos:batchError', {
        error: error instanceof Error ? error.message : 'Failed to generate videos',
        timestamp: new Date().toISOString(),
      });
    }

    res.status(500).json({
      error: 'Failed to generate videos',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
