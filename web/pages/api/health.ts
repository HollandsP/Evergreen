import type { NextApiRequest, NextApiResponse } from 'next';

interface HealthResponse {
  status: 'ok' | 'error';
  timestamp: string;
  services: {
    [key: string]: 'up' | 'down' | 'unknown';
  };
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>,
) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).end();
  }

  const services: { [key: string]: 'up' | 'down' | 'unknown' } = {};

  // Check backend service
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${backendUrl}/health`, { 
      signal: controller.signal,
      headers: {
        'Authorization': `Bearer ${process.env.API_TOKEN || ''}`,
      },
    });
    
    clearTimeout(timeoutId);
    services.backend = response.ok ? 'up' : 'down';
  } catch {
    services.backend = 'down';
  }

  // Add other service checks as needed
  services.frontend = 'up'; // This API responding means frontend is up
  services.websocket = 'unknown'; // Would need WebSocket check

  const allServicesUp = Object.values(services).every(status => status === 'up');

  const healthResponse: HealthResponse = {
    status: allServicesUp ? 'ok' : 'error',
    timestamp: new Date().toISOString(),
    services,
  };

  const statusCode = allServicesUp ? 200 : 503;
  return res.status(statusCode).json(healthResponse);
}
