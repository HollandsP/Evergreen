import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const { id } = req.query;

    if (!id || typeof id !== 'string') {
      return res.status(400).json({ message: 'Invalid operation ID' });
    }

    // Try to find the preview file in various locations
    const possiblePaths = [
      // MoviePy wrapper workspace
      path.join(process.cwd(), 'output', 'editor_workspace', 'previews', `${id}_preview.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}.mp4`),
      
      // FastAPI backend paths
      path.join(process.cwd(), '..', 'src', 'services', 'output', 'editor_workspace', 'previews', `${id}_preview.mp4`),
      path.join(process.cwd(), '..', 'output', 'editor_workspace', 'previews', `${id}_preview.mp4`),
      
      // Alternative paths
      path.join(process.cwd(), 'public', 'previews', `${id}.mp4`),
      path.join(process.cwd(), 'output', 'previews', `${id}.mp4`)
    ];

    let videoPath: string | null = null;
    
    // Find the first existing file
    for (const possiblePath of possiblePaths) {
      if (fs.existsSync(possiblePath)) {
        videoPath = possiblePath;
        break;
      }
    }

    if (!videoPath) {
      // If no local file found, try to proxy from Python backend
      try {
        const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000';
        const response = await fetch(`${pythonApiUrl}/api/v1/editor/preview/${id}`);
        
        if (response.ok) {
          // Stream the response from Python backend
          const contentType = response.headers.get('content-type') || 'video/mp4';
          const contentLength = response.headers.get('content-length');
          
          res.setHeader('Content-Type', contentType);
          if (contentLength) {
            res.setHeader('Content-Length', contentLength);
          }
          res.setHeader('Accept-Ranges', 'bytes');
          res.setHeader('Cache-Control', 'public, max-age=3600');
          
          if (response.body) {
            // Stream the video data
            const reader = response.body.getReader();
            
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              res.write(value);
            }
            
            return res.end();
          }
        }
      } catch (fetchError) {
        console.error('Error fetching from Python backend:', fetchError);
      }

      return res.status(404).json({ 
        message: 'Preview not found',
        operation_id: id,
        searched_paths: possiblePaths.map(p => p.replace(process.cwd(), '.')).slice(0, 3) // Don't expose full paths
      });
    }

    // Get file stats
    const stat = fs.statSync(videoPath);
    const fileSize = stat.size;
    const range = req.headers.range;

    // Handle range requests for video streaming
    if (range) {
      const parts = range.replace(/bytes=/, "").split("-");
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
      const chunksize = (end - start) + 1;
      
      const file = fs.createReadStream(videoPath, { start, end });
      
      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mp4',
        'Cache-Control': 'public, max-age=3600'
      });
      
      file.pipe(res);
    } else {
      // Send the entire file
      res.writeHead(200, {
        'Content-Length': fileSize,
        'Content-Type': 'video/mp4',
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=3600'
      });
      
      fs.createReadStream(videoPath).pipe(res);
    }

  } catch (error) {
    console.error('Error serving video preview:', error);
    res.status(500).json({ 
      message: 'Internal server error',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}