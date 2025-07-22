import type { NextApiRequest, NextApiResponse } from 'next';
import { GenerationJob } from '@/types';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerationJob[] | { error: string }>,
) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // In a real implementation, fetch from your backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/jobs`, {
        headers: {
          'Authorization': `Bearer ${process.env.API_TOKEN || ''}`,
        },
      });

      if (response.ok) {
        const backendJobs = await response.json();
        
        const jobs: GenerationJob[] = backendJobs.map((backendJob: any) => ({
          id: backendJob.id,
          prompt: backendJob.prompt,
          provider: backendJob.provider,
          status: backendJob.status,
          progress: backendJob.progress || 0,
          createdAt: new Date(backendJob.created_at),
          updatedAt: new Date(backendJob.updated_at),
          imageUrl: backendJob.image_url,
          videoUrl: backendJob.video_url,
          error: backendJob.error,
          cost: backendJob.cost,
          metadata: backendJob.metadata,
        }));

        return res.status(200).json(jobs);
      }
    } catch (backendError) {
      console.error('Backend API error:', backendError);
    }

    // Fallback to empty array for demo
    return res.status(200).json([]);

  } catch (error) {
    console.error('API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
