import type { NextApiRequest, NextApiResponse } from 'next';
import formidable from 'formidable';
import fs from 'fs/promises';
import path from 'path';
import { updateProductionStage } from '@/lib/production-state';

export const config = {
  api: {
    bodyParser: false,
  },
};

interface ParsedForm {
  fields: formidable.Fields;
  files: formidable.Files;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
    return;
  }

  try {
    // Update state to uploading
    updateProductionStage('script', {
      status: 'uploading',
      parseProgress: 0,
      error: undefined,
    });

    // Parse the form data
    const form = formidable({
      maxFileSize: 10 * 1024 * 1024, // 10MB max
      allowEmptyFiles: false,
      filter: ({ mimetype }) => {
        // Allow text files, markdown, and common document formats
        const allowed = [
          'text/plain',
          'text/markdown',
          'text/x-markdown',
          'application/x-markdown',
          'application/octet-stream', // For .md files
        ];
        return allowed.includes(mimetype || '');
      },
    });

    const [fields, files] = await form.parse(req);
    
    const file = Array.isArray(files.file) ? files.file[0] : files.file;
    
    if (!file) {
      throw new Error('No file uploaded');
    }

    const fileName = file.originalFilename || 'script.txt';
    const fileSize = file.size;

    // Read file content
    const content = await fs.readFile(file.filepath, 'utf-8');
    
    // Clean up temp file
    await fs.unlink(file.filepath).catch(console.error);

    // Update state with file info
    updateProductionStage('script', {
      fileName,
      fileSize,
    });

    // Send WebSocket notification
    if (global.io) {
      global.io.emit('script:uploadComplete', {
        fileName,
        fileSize,
        timestamp: new Date().toISOString(),
      });
    }

    // Now parse the content
    const parseResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'}/api/script/parse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        fileName,
      }),
    });

    if (!parseResponse.ok) {
      const error = await parseResponse.json();
      throw new Error(error.message || 'Failed to parse script');
    }

    const parseResult = await parseResponse.json();

    res.status(200).json({
      success: true,
      fileName,
      fileSize,
      ...parseResult,
    });
  } catch (error) {
    console.error('Script upload error:', error);
    
    updateProductionStage('script', {
      status: 'error',
      error: error instanceof Error ? error.message : 'Failed to upload script',
    });

    if (global.io) {
      global.io.emit('script:uploadError', {
        error: error instanceof Error ? error.message : 'Failed to upload script',
        timestamp: new Date().toISOString(),
      });
    }

    res.status(500).json({
      error: 'Failed to upload script',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}