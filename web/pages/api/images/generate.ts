import type { NextApiRequest, NextApiResponse } from 'next';
import { getOpenAIClient } from '../../../lib/openai-client';
import { getSocketServer, emitProgress } from '@/lib/websocket-server';
import { fileManager } from '@/lib/file-manager';
import fs from 'fs/promises';
import path from 'path';
import fetch from 'node-fetch';

interface GenerateImageRequest {
  prompt: string;
  provider: 'dalle3';  // Flux.1 removed due to high subscription costs
  sceneId: string;
  projectId: string;
  jobId?: string;
  size?: '1024x1024' | '1024x1792' | '1792x1024';
  quality?: 'standard' | 'hd';
  style?: 'vivid' | 'natural';
}

interface GenerateImageResponse {
  url: string;
  provider: string;
  sceneId: string;
  revisedPrompt?: string;
  cost?: number;
  savedPath?: string;
}

async function generateWithDALLE3(
  prompt: string, 
  size: '1024x1024' | '1024x1792' | '1792x1024' = '1792x1024',
  quality: 'standard' | 'hd' = 'standard',
  style: 'vivid' | 'natural' = 'natural'
): Promise<{ url: string; revisedPrompt?: string; cost: number }> {
  const openaiClient = getOpenAIClient();
  
  // Generate image with retry logic
  let retries = 3;
  let lastError: Error | null = null;
  
  while (retries > 0) {
    try {
      const result = await openaiClient.generateImage({
        prompt,
        size,
        quality,
        style,
      });
      
      // Calculate cost
      const cost = size === '1024x1024' ? 0.04 : 0.08;
      
      return {
        url: result.url,
        revisedPrompt: result.revisedPrompt,
        cost,
      };
    } catch (error) {
      console.error(`DALL-E 3 generation attempt ${4 - retries} failed:`, error);
      lastError = error as Error;
      retries--;
      
      // Wait before retry with exponential backoff
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, 3 - retries) * 1000));
      }
    }
  }
  
  throw lastError || new Error('Failed to generate image after 3 attempts');
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerateImageResponse | { error: string }> & { socket?: any },
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { prompt, provider, sceneId, projectId, jobId, size, quality, style } = req.body as GenerateImageRequest;

    if (!prompt || !provider || !sceneId || !projectId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    if (provider !== 'dalle3') {
      return res.status(400).json({ error: 'Invalid provider. Only DALL-E 3 is supported.' });
    }

    // Check for API key
    if (!process.env.OPENAI_API_KEY) {
      return res.status(500).json({ error: 'OpenAI API key not configured' });
    }

    const io = getSocketServer(res as any);

    // Emit start event
    if (jobId) {
      emitProgress(io, {
        jobId,
        stage: 'image_generation',
        progress: 0,
        status: 'started',
        data: {
          message: 'Starting image generation...',
          sceneId,
        },
      });
    }

    // Validate and sanitize prompt
    const sanitizedPrompt = prompt.trim().slice(0, 4000); // DALL-E 3 has a 4000 character limit
    
    if (sanitizedPrompt.length === 0) {
      return res.status(400).json({ error: 'Prompt cannot be empty' });
    }

    // Emit progress - prompt validated
    if (jobId) {
      emitProgress(io, {
        jobId,
        stage: 'image_generation',
        progress: 20,
        status: 'progress',
        data: {
          message: 'Prompt validated, connecting to DALL-E 3...',
          sceneId,
        },
      });
    }

    let result: { url: string; revisedPrompt?: string; cost: number };
    
    try {
      // Generate image with DALL-E 3
      result = await generateWithDALLE3(
        sanitizedPrompt,
        size || '1792x1024',
        quality || 'standard',
        style || 'natural'
      );

      // Emit completion
      if (jobId) {
        emitProgress(io, {
          jobId,
          stage: 'image_generation',
          progress: 100,
          status: 'completed',
          data: {
            message: 'Image generated successfully',
            sceneId,
            imageUrl: result.url,
          },
        });
      }
    } catch (error) {
      console.error('Image generation error:', error);
      
      // Handle specific API errors
      if (error instanceof Error) {
        if (error.message.includes('content policy')) {
          return res.status(400).json({ 
            error: 'The prompt was rejected due to content policy. Please modify your prompt and try again.', 
          });
        }
        if (error.message.includes('rate limit')) {
          return res.status(429).json({ 
            error: 'Rate limit exceeded. Please try again later.', 
          });
        }
        if (error.message.includes('Invalid API key')) {
          return res.status(401).json({ 
            error: 'Invalid OpenAI API key. Please check your configuration.', 
          });
        }
      }
      
      throw error;
    }

    // Log generation for cost tracking
    console.log(`Generated image for scene ${sceneId} using DALL-E 3 - Cost: $${result.cost.toFixed(3)}`);

    // Save image to project folder
    let savedFilename: string | undefined;
    try {
      // Download the image
      const imageResponse = await fetch(result.url);
      if (!imageResponse.ok) {
        throw new Error('Failed to download generated image');
      }
      
      const buffer = await imageResponse.buffer();
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      savedFilename = `dalle3_${timestamp}.png`;
      
      // Get the path to save the image
      const imagePath = fileManager.getAssetFilePath(projectId, sceneId, 'images', savedFilename);
      
      // Ensure directory exists
      await fs.mkdir(path.dirname(imagePath), { recursive: true });
      
      // Save the image
      await fs.writeFile(imagePath, buffer);
      
      // Update scene metadata
      await fileManager.addAssetToScene(projectId, sceneId, 'images', savedFilename);
      
      console.log(`Saved image to: ${imagePath}`);
    } catch (saveError) {
      console.error('Failed to save image:', saveError);
      // Don't fail the entire operation if save fails
    }

    res.status(200).json({
      url: result.url,
      provider,
      sceneId,
      revisedPrompt: result.revisedPrompt,
      cost: result.cost,
      savedPath: savedFilename,
    });
  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Failed to generate image. Please try again.', 
    });
  }
}

// Configuration for larger request bodies (base64 images)
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
  },
};
