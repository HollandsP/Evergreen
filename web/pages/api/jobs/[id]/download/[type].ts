import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { id, type } = req.query;

  if (typeof id !== 'string' || typeof type !== 'string') {
    return res.status(400).json({ error: 'Invalid parameters' });
  }

  if (!['image', 'video'].includes(type)) {
    return res.status(400).json({ error: 'Invalid download type' });
  }

  try {
    // In a real implementation, fetch from your backend or cloud storage
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${backendUrl}/api/v1/jobs/${id}/download/${type}`, {
        headers: {
          'Authorization': `Bearer ${process.env.API_TOKEN || ''}`,
        },
      });

      if (response.ok) {
        const contentType = response.headers.get('content-type');
        const contentLength = response.headers.get('content-length');
        
        // Set appropriate headers
        res.setHeader('Content-Type', contentType || (type === 'image' ? 'image/png' : 'video/mp4'));
        if (contentLength) {
          res.setHeader('Content-Length', contentLength);
        }
        res.setHeader('Content-Disposition', `attachment; filename="${id}_${type}.${type === 'image' ? 'png' : 'mp4'}"`);

        // Stream the response
        if (response.body) {
          const reader = response.body.getReader();
          
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              res.write(Buffer.from(value));
            }
            res.end();
          } finally {
            reader.releaseLock();
          }
        }
        return;
      }
    } catch (backendError) {
      console.error('Backend API error:', backendError);
    }

    // Fallback error
    return res.status(404).json({ error: 'File not found' });

  } catch (error) {
    console.error('Download API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}