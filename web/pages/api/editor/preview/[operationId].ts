import { NextApiRequest, NextApiResponse } from 'next';
import path from 'path';
import fs from 'fs';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { operationId } = req.query;

  if (!operationId || typeof operationId !== 'string') {
    return res.status(400).json({ error: 'Operation ID is required' });
  }

  try {
    // Look for preview files in the editor workspace
    const previewPaths = [
      path.join(process.cwd(), 'output', 'editor_workspace', 'previews', `${operationId}_preview.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', 'previews', `${operationId}_thumb.jpg`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_cut.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_fade.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_speed.mp4`)
    ];

    // Find the first existing preview file
    let previewPath = null;
    for (const candidatePath of previewPaths) {
      if (fs.existsSync(candidatePath)) {
        previewPath = candidatePath;
        break;
      }
    }

    if (!previewPath) {
      // Generate a mock preview response for development
      return res.status(200).json({
        type: 'mock',
        message: 'Preview not available - mock response for development',
        operation_id: operationId,
        status: 'processing'
      });
    }

    // Get file stats
    const stats = fs.statSync(previewPath);
    const fileExtension = path.extname(previewPath).toLowerCase();

    // Set appropriate content type
    let contentType = 'application/octet-stream';
    if (fileExtension === '.mp4') {
      contentType = 'video/mp4';
    } else if (fileExtension === '.jpg' || fileExtension === '.jpeg') {
      contentType = 'image/jpeg';
    } else if (fileExtension === '.png') {
      contentType = 'image/png';
    }

    // Set headers for video/image streaming
    res.setHeader('Content-Type', contentType);
    res.setHeader('Content-Length', stats.size);
    res.setHeader('Cache-Control', 'public, max-age=3600');
    res.setHeader('Accept-Ranges', 'bytes');

    // Handle range requests for video streaming
    const range = req.headers.range;
    if (range && fileExtension === '.mp4') {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : stats.size - 1;
      const chunksize = (end - start) + 1;

      res.status(206);
      res.setHeader('Content-Range', `bytes ${start}-${end}/${stats.size}`);
      res.setHeader('Content-Length', chunksize);

      const stream = fs.createReadStream(previewPath, { start, end });
      stream.pipe(res);
    } else {
      // Serve the complete file
      const stream = fs.createReadStream(previewPath);
      stream.pipe(res);
    }

  } catch (error) {
    console.error('Error serving preview:', error);
    res.status(500).json({ 
      error: 'Failed to serve preview',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}