import { NextApiRequest, NextApiResponse } from 'next';
import { IncomingForm, File } from 'formidable';
import { promises as fs } from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

// Disable body parser to handle file uploads
export const config = {
  api: {
    bodyParser: false,
  },
};

interface UploadResponse {
  success: boolean;
  url?: string;
  error?: string;
  metadata?: {
    filename: string;
    size: number;
    type: string;
    width?: number;
    height?: number;
  };
}

// Allowed file types for uploads
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/quicktime'];
const ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/ogg'];

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB limit

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<UploadResponse>,
) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
    });
  }

  try {
    // Create uploads directory if it doesn't exist
    const uploadsDir = path.join(process.cwd(), 'public', 'uploads');
    try {
      await fs.access(uploadsDir);
    } catch {
      await fs.mkdir(uploadsDir, { recursive: true });
    }

    // Parse the form data
    const form = new IncomingForm({
      uploadDir: uploadsDir,
      keepExtensions: true,
      maxFileSize: MAX_FILE_SIZE,
    });

    const { fields: _fields, files } = await new Promise<{
      fields: any;
      files: any;
    }>((resolve, reject) => {
      form.parse(req, (err, fields, files) => {
        if (err) reject(err);
        else resolve({ fields, files });
      });
    });

    // Get the uploaded file
    const uploadedFile = Array.isArray(files.file) ? files.file[0] : files.file;
    
    if (!uploadedFile) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
      });
    }

    const file = uploadedFile as File;

    // Validate file type
    const allowedTypes = [
      ...ALLOWED_IMAGE_TYPES,
      ...ALLOWED_VIDEO_TYPES,
      ...ALLOWED_AUDIO_TYPES,
    ];

    if (!allowedTypes.includes(file.mimetype || '')) {
      // Clean up the uploaded file
      await fs.unlink(file.filepath);
      return res.status(400).json({
        success: false,
        error: `File type ${file.mimetype} is not allowed`,
      });
    }

    // Generate a unique filename
    const fileExtension = path.extname(file.originalFilename || '');
    const uniqueFilename = `${uuidv4()}${fileExtension}`;
    const finalPath = path.join(uploadsDir, uniqueFilename);

    // Move the file to its final location
    await fs.rename(file.filepath, finalPath);

    // Generate the public URL
    const publicUrl = `/uploads/${uniqueFilename}`;

    // Get additional metadata for images
    let metadata: any = {
      filename: file.originalFilename || uniqueFilename,
      size: file.size,
      type: file.mimetype || 'unknown',
    };

    // For images, try to get dimensions
    if (ALLOWED_IMAGE_TYPES.includes(file.mimetype || '')) {
      try {
        // You could use a library like 'sharp' here to get image dimensions
        // For now, we'll leave it as undefined
        metadata.width = undefined;
        metadata.height = undefined;
      } catch (error) {
        console.warn('Could not extract image dimensions:', error);
      }
    }

    return res.status(200).json({
      success: true,
      url: publicUrl,
      metadata,
    });

  } catch (error) {
    console.error('Upload error:', error);
    
    let errorMessage = 'Upload failed';
    if (error instanceof Error) {
      if (error.message.includes('maxFileSize')) {
        errorMessage = `File too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB`;
      } else {
        errorMessage = error.message;
      }
    }

    return res.status(500).json({
      success: false,
      error: errorMessage,
    });
  }
}