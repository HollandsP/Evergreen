import { NextApiRequest, NextApiResponse } from 'next';

// Mock Runway ML Gen-4 Turbo API
// In production, this would integrate with the actual Runway API

interface VideoGenerationRequest {
  imageUrl: string;
  prompt: string;
  duration: number; // in seconds
  cameraMovement?: string;
  motionIntensity?: number;
  lipSync?: boolean;
  audioUrl?: string;
}

interface VideoGenerationResponse {
  videoUrl: string;
  jobId: string;
  status: 'completed' | 'processing' | 'failed';
  duration: number;
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

// Generate mock video URL based on parameters
const generateMockVideoUrl = (_params: VideoGenerationRequest): string => {
  const timestamp = Date.now();
  const videoId = `video_${timestamp}_${Math.random().toString(36).substr(2, 9)}`;
  
  // In production, this would be the actual Runway-generated video URL
  // For now, we'll use a placeholder that indicates the parameters
  const baseUrl = 'https://storage.googleapis.com/evergreen-videos';
  return `${baseUrl}/${videoId}.mp4`;
};

// Simulate Runway API processing time
const simulateProcessing = async (duration: number): Promise<void> => {
  // Simulate longer processing for longer videos
  const processingTime = Math.min(2000 + (duration * 100), 5000);
  await new Promise(resolve => setTimeout(resolve, processingTime));
};

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
    } = req.body as VideoGenerationRequest;

    // Validate required parameters
    if (!imageUrl || !prompt || !duration) {
      return res.status(400).json({ 
        error: 'Missing required parameters: imageUrl, prompt, and duration', 
      });
    }

    // Validate duration (Runway Gen-4 supports up to 10 seconds)
    if (duration < 1 || duration > 10) {
      return res.status(400).json({ 
        error: 'Duration must be between 1 and 10 seconds', 
      });
    }

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

    console.log('Generating video with parameters:', {
      imageUrl,
      fullPrompt,
      duration,
      motionIntensity,
      lipSync,
    });

    // In production, this would be the actual Runway API call:
    /*
    const runwayResponse = await fetch('https://api.runwayml.com/v1/generate/video', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.RUNWAY_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gen-4-turbo',
        input: {
          image_url: imageUrl,
          prompt: fullPrompt,
          duration: duration,
          motion_amount: motionIntensity / 100,
          audio_url: lipSync ? audioUrl : undefined,
          enable_lip_sync: lipSync,
        },
      }),
    });

    const runwayData = await runwayResponse.json();
    */

    // Simulate processing
    await simulateProcessing(duration);

    // Generate mock response
    const videoUrl = generateMockVideoUrl(req.body);
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Return successful response
    res.status(200).json({
      videoUrl,
      jobId,
      status: 'completed',
      duration,
    });

  } catch (error) {
    console.error('Video generation error:', error);
    res.status(500).json({ 
      error: 'Failed to generate video. Please try again.', 
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
