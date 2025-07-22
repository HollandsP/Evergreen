import type { NextApiRequest, NextApiResponse } from 'next';
import { SystemStatus } from '@/types';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<SystemStatus | { error: string }>
) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // In a real implementation, fetch from your backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/status`, {
        headers: {
          'Authorization': `Bearer ${process.env.API_TOKEN || ''}`,
        },
      });

      if (response.ok) {
        const backendStatus = await response.json();
        
        const status: SystemStatus = {
          dalle3Available: backendStatus.dalle3_available ?? true,
          flux1Available: backendStatus.flux1_available ?? true,
          runwayAvailable: backendStatus.runway_available ?? true,
          activeJobs: backendStatus.active_jobs ?? 0,
          queueLength: backendStatus.queue_length ?? 0,
          systemLoad: backendStatus.system_load ?? 0.2,
        };

        return res.status(200).json(status);
      }
    } catch (backendError) {
      console.error('Backend API error:', backendError);
    }

    // Fallback status for demo
    const fallbackStatus: SystemStatus = {
      dalle3Available: true,
      flux1Available: true,
      runwayAvailable: true,
      activeJobs: 0,
      queueLength: 0,
      systemLoad: 0.2,
    };

    return res.status(200).json(fallbackStatus);

  } catch (error) {
    console.error('Status API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}