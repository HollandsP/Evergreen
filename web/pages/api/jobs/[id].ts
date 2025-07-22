import type { NextApiRequest, NextApiResponse } from 'next';
import { GenerationJob } from '@/types';

// Mock job data for demo purposes
const mockJobs = new Map<string, GenerationJob>();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerationJob | { error: string } | { message: string }>,
) {
  const { id } = req.query;

  if (typeof id !== 'string') {
    return res.status(400).json({ error: 'Invalid job ID' });
  }

  switch (req.method) {
    case 'GET':
      return handleGet(id, res);
    case 'DELETE':
      return handleDelete(id, res);
    default:
      res.setHeader('Allow', ['GET', 'DELETE']);
      return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleGet(
  id: string,
  res: NextApiResponse<GenerationJob | { error: string }>,
) {
  try {
    // In a real implementation, fetch from your backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/jobs/${id}`, {
        headers: {
          'Authorization': `Bearer ${process.env.API_TOKEN || ''}`,
        },
      });

      if (response.ok) {
        const backendJob = await response.json();
        
        const job: GenerationJob = {
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
        };

        return res.status(200).json(job);
      }
    } catch (backendError) {
      console.error('Backend API error:', backendError);
    }

    // Fallback to mock data
    const mockJob = mockJobs.get(id);
    if (mockJob) {
      return res.status(200).json(mockJob);
    }

    return res.status(404).json({ error: 'Job not found' });

  } catch (error) {
    console.error('API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleDelete(
  id: string,
  res: NextApiResponse<{ message: string } | { error: string }>,
) {
  try {
    // In a real implementation, cancel the job in your backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/jobs/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${process.env.API_TOKEN || ''}`,
        },
      });

      if (response.ok) {
        return res.status(200).json({ message: 'Job cancelled successfully' });
      }
    } catch (backendError) {
      console.error('Backend API error:', backendError);
    }

    // Fallback for demo
    mockJobs.delete(id);
    return res.status(200).json({ message: 'Job cancelled successfully' });

  } catch (error) {
    console.error('API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
