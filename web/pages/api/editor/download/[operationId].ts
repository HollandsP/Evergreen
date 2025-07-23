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
    // Look for output files in the editor workspace
    const outputPaths = [
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_cut.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_fade.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_speed.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_overlay.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_audio_mix.mp4`),
      path.join(process.cwd(), 'output', 'editor_workspace', `${operationId}_transitions.mp4`)
    ];

    // Find the first existing output file
    let outputPath = null;
    for (const candidatePath of outputPaths) {
      if (fs.existsSync(candidatePath)) {
        outputPath = candidatePath;
        break;
      }
    }

    if (!outputPath) {
      // Generate a mock video file for development
      return generateMockVideoDownload(res, operationId);
    }

    // Get file stats
    const stats = fs.statSync(outputPath);
    const fileName = `edited_video_${operationId}.mp4`;

    // Set headers for file download
    res.setHeader('Content-Type', 'video/mp4');
    res.setHeader('Content-Length', stats.size);
    res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
    res.setHeader('Cache-Control', 'no-cache');

    // Stream the file
    const stream = fs.createReadStream(outputPath);
    stream.pipe(res);

  } catch (error) {
    console.error('Error downloading video:', error);
    res.status(500).json({ 
      error: 'Failed to download video',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

function generateMockVideoDownload(res: NextApiResponse, operationId: string) {
  // For development, return a small mock MP4 file
  const mockVideoData = Buffer.from([
    // MP4 header with minimal valid structure
    0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70, // ftyp box
    0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00, // isom brand
    0x69, 0x73, 0x6F, 0x6D, 0x69, 0x73, 0x6F, 0x32, // compatible brands
    0x61, 0x76, 0x63, 0x31, 0x6D, 0x70, 0x34, 0x31, // more brands
  ]);

  const fileName = `edited_video_${operationId}.mp4`;

  res.setHeader('Content-Type', 'video/mp4');
  res.setHeader('Content-Length', mockVideoData.length);
  res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
  res.setHeader('Cache-Control', 'no-cache');

  res.end(mockVideoData);
}