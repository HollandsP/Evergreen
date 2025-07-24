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

    // Try to find the processed video file in various locations
    const possiblePaths = [
      // MoviePy wrapper workspace - processed videos
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}_cut.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}_fade.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}_speed.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}_transitions.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}_overlay.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}_audio_mix.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${id}.mp4`),
      
      // FastAPI backend paths
      path.join(process.cwd(), '..', 'src', 'services', 'output', 'editor_workspace', `${id}_cut.mp4`),
      path.join(process.cwd(), '..', 'src', 'services', 'output', 'editor_workspace', `${id}_fade.mp4`),
      path.join(process.cwd(), '..', 'src', 'services', 'output', 'editor_workspace', `${id}_speed.mp4`),
      path.join(process.cwd(), '..', 'src', 'services', 'output', 'editor_workspace', `${id}_transitions.mp4`),
      path.join(process.cwd(), '..', 'src', 'services', 'output', 'editor_workspace', `${id}_overlay.mp4`),
      path.join(process.cwd(), '..', 'src', 'services', 'output', 'editor_workspace', `${id}_audio_mix.mp4`),
      path.join(process.cwd(), '..', 'output', 'editor_workspace', `${id}.mp4`),
      
      // Alternative paths
      path.join(process.cwd(), 'output', 'editor', `${id}.mp4`),
      path.join(process.cwd(), 'public', 'downloads', `${id}.mp4`)
    ];

    let videoPath: string | null = null;
    let operationType: string = 'edited';
    
    // Find the first existing file and detect operation type
    for (const possiblePath of possiblePaths) {
      if (fs.existsSync(possiblePath)) {
        videoPath = possiblePath;
        
        // Extract operation type from filename
        const filename = path.basename(possiblePath, '.mp4');
        const parts = filename.split('_');
        if (parts.length > 1) {
          operationType = parts[parts.length - 1]; // Get the last part (cut, fade, speed, etc.)
        }
        
        break;
      }
    }

    if (!videoPath) {
      // If no local file found, try to proxy from Python backend
      try {
        const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000';
        const response = await fetch(`${pythonApiUrl}/api/v1/editor/download/${id}`);
        
        if (response.ok) {
          // Get the filename from response headers or generate one
          const contentDisposition = response.headers.get('content-disposition');
          let filename = `edited_video_${id}.mp4`;
          
          if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
              filename = filenameMatch[1];
            }
          }
          
          // Set download headers
          res.setHeader('Content-Type', 'video/mp4');
          res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
          res.setHeader('Cache-Control', 'no-cache');
          
          const contentLength = response.headers.get('content-length');
          if (contentLength) {
            res.setHeader('Content-Length', contentLength);
          }
          
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
        message: 'Processed video not found',
        operation_id: id,
        hint: 'The video might still be processing, or the operation failed'
      });
    }

    // Generate appropriate filename
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `edited_video_${operationType}_${timestamp}_${id}.mp4`;

    // Get file stats
    const stat = fs.statSync(videoPath);
    const fileSize = stat.size;

    // Set download headers
    res.setHeader('Content-Type', 'video/mp4');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Length', fileSize.toString());
    res.setHeader('Cache-Control', 'no-cache');
    
    // Optional: Add metadata headers
    res.setHeader('X-Operation-Type', operationType);
    res.setHeader('X-Operation-ID', id);
    res.setHeader('X-File-Size', fileSize.toString());

    // Stream the file
    const fileStream = fs.createReadStream(videoPath);
    
    fileStream.on('error', (streamError) => {
      console.error('Error streaming file:', streamError);
      if (!res.headersSent) {
        res.status(500).json({ message: 'Error streaming file' });
      }
    });

    fileStream.on('end', () => {
      console.log(`Successfully downloaded: ${filename} (${fileSize} bytes)`);
    });

    fileStream.pipe(res);

  } catch (error) {
    console.error('Error serving video download:', error);
    
    if (!res.headersSent) {
      res.status(500).json({ 
        message: 'Internal server error',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
}