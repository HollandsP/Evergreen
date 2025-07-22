import type { NextApiRequest, NextApiResponse } from 'next';
import { GenerationRequest, GenerationJob } from '@/types';

// This would integrate with your backend service
// For now, we'll simulate the API response

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerationJob | { error: string }>,
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const request: GenerationRequest = req.body;

    // Validate request
    if (!request.prompt || !request.provider) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    if (request.prompt.length < 10 || request.prompt.length > 4000) {
      return res.status(400).json({ error: 'Prompt must be between 10 and 4000 characters' });
    }

    // Create job object
    const job: GenerationJob = {
      id: generateJobId(),
      prompt: request.prompt,
      provider: request.provider,
      status: 'pending',
      progress: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      metadata: {
        imageSize: request.settings.imageSize,
        videoDuration: request.settings.videoDuration,
        quality: request.settings.quality,
      },
    };

    // In a real implementation, this would:
    // 1. Submit job to your unified pipeline service
    // 2. Return the job ID for tracking
    // 3. The pipeline service would send WebSocket updates

    // For now, simulate the API call to your backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.API_TOKEN || ''}`,
        },
        body: JSON.stringify({
          prompt: request.prompt,
          provider: request.provider,
          settings: request.settings,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend responded with ${response.status}`);
      }

      const backendJob = await response.json();
      
      // Transform backend response to match our interface
      const transformedJob: GenerationJob = {
        ...job,
        id: backendJob.id || job.id,
        status: backendJob.status || 'pending',
        progress: backendJob.progress || 0,
        cost: backendJob.cost,
        imageUrl: backendJob.image_url,
        videoUrl: backendJob.video_url,
        error: backendJob.error,
      };

      return res.status(200).json(transformedJob);

    } catch (backendError) {
      console.error('Backend API error:', backendError);
      
      // Return the simulated job anyway for demo purposes
      return res.status(200).json(job);
    }

  } catch (error) {
    console.error('API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

function generateJobId(): string {
  return 'job_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
}
