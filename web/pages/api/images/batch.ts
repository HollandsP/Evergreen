import type { NextApiRequest, NextApiResponse } from 'next';
import { ScriptScene, ImageData } from '@/types';
import { updateProductionStage } from '@/lib/production-state';

interface BatchImageRequest {
  scenes: ScriptScene[];
  settings?: {
    size?: '1024x1024' | '1792x1024' | '1024x1792';
    quality?: 'standard' | 'hd';
    style?: 'vivid' | 'natural';
  };
}

interface BatchImageResponse {
  imageData: ImageData[];
  totalCost: number;
  processingTime: number;
}

// Mock image generation for development
async function generateMockImage(scene: ScriptScene): Promise<ImageData> {
  // Simulate processing delay
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
  
  // Return a placeholder image URL
  const placeholderImages = [
    'https://via.placeholder.com/1792x1024/0f172a/e2e8f0?text=Scene+1',
    'https://via.placeholder.com/1792x1024/1e293b/e2e8f0?text=Scene+2',
    'https://via.placeholder.com/1792x1024/334155/e2e8f0?text=Scene+3',
    'https://via.placeholder.com/1792x1024/475569/e2e8f0?text=Scene+4',
    'https://via.placeholder.com/1792x1024/64748b/e2e8f0?text=Scene+5',
  ];
  
  const randomIndex = Math.floor(Math.random() * placeholderImages.length);
  
  return {
    sceneId: scene.id,
    url: placeholderImages[randomIndex].replace('Scene+', `Scene+${scene.id.slice(-2)}`),
    prompt: scene.imagePrompt,
    provider: 'dalle3',
    status: 'completed',
  };
}

// Generate image with DALL-E 3
async function generateDalle3Image(
  scene: ScriptScene,
  settings?: BatchImageRequest['settings'],
): Promise<ImageData> {
  const apiKey = process.env.OPENAI_API_KEY;
  
  if (!apiKey) {
    throw new Error('OpenAI API key not configured');
  }
  
  try {
    const response = await fetch('https://api.openai.com/v1/images/generations', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'dall-e-3',
        prompt: scene.imagePrompt,
        n: 1,
        size: settings?.size || '1792x1024', // 16:9 aspect ratio
        quality: settings?.quality || 'standard',
        style: settings?.style || 'vivid',
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      
      // Check for specific OpenAI errors
      if (response.status === 400 && errorData.error?.code === 'content_policy_violation') {
        return {
          sceneId: scene.id,
          url: '',
          prompt: scene.imagePrompt,
          provider: 'dalle3',
          status: 'error',
          error: 'Content policy violation: Please modify the prompt',
        };
      }
      
      throw new Error(errorData.error?.message || `API error: ${response.status}`);
    }
    
    const data = await response.json();
    const imageUrl = data.data?.[0]?.url;
    
    if (!imageUrl) {
      throw new Error('No image URL returned from DALL-E 3');
    }
    
    // TODO: In production, download and upload to S3 for persistence
    
    return {
      sceneId: scene.id,
      url: imageUrl,
      prompt: scene.imagePrompt,
      provider: 'dalle3',
      status: 'completed',
    };
  } catch (error: any) {
    console.error(`Failed to generate image for scene ${scene.id}:`, error);
    
    return {
      sceneId: scene.id,
      url: '',
      prompt: scene.imagePrompt,
      provider: 'dalle3',
      status: 'error',
      error: error.message || 'Failed to generate image',
    };
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version',
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
    const { scenes, settings } = req.body as BatchImageRequest;

    if (!scenes || !Array.isArray(scenes) || scenes.length === 0) {
      return res.status(400).json({ error: 'No scenes provided' });
    }

    const startTime = Date.now();
    
    // Update state to generating
    updateProductionStage('images', {
      status: 'generating',
      progress: 0,
      generatedImages: [],
      error: undefined,
    });

    // Send WebSocket notification
    if (global.io) {
      global.io.emit('images:batchStart', {
        sceneCount: scenes.length,
        settings,
        timestamp: new Date().toISOString(),
      });
    }

    const imageResults: ImageData[] = [];
    const useMockData = !process.env.OPENAI_API_KEY || process.env.USE_MOCK_IMAGES === 'true';

    // Process scenes in parallel batches to optimize speed while respecting rate limits
    const batchSize = useMockData ? 5 : 2; // DALL-E 3 has rate limits, process 2 at a time
    
    for (let i = 0; i < scenes.length; i += batchSize) {
      const batch = scenes.slice(i, Math.min(i + batchSize, scenes.length));
      
      // Process batch in parallel
      const batchPromises = batch.map(async (scene) => {
        try {
          return useMockData 
            ? await generateMockImage(scene)
            : await generateDalle3Image(scene, settings);
        } catch (error) {
          // Return error result but don't throw
          return {
            sceneId: scene.id,
            url: '',
            prompt: scene.imagePrompt,
            provider: 'dalle3' as const,
            status: 'error' as const,
            error: error instanceof Error ? error.message : 'Failed to generate image',
          };
        }
      });
      
      const batchResults = await Promise.all(batchPromises);
      imageResults.push(...batchResults);
      
      // Update progress
      const progress = Math.round((imageResults.length / scenes.length) * 100);
      updateProductionStage('images', {
        progress,
        generatedImages: imageResults,
      });
      
      // Send progress update
      if (global.io) {
        global.io.emit('images:batchProgress', {
          progress,
          generatedScenes: imageResults.length,
          totalScenes: scenes.length,
          timestamp: new Date().toISOString(),
        });
      }
      
      // Add delay between batches to respect rate limits
      // DALL-E 3: 5 images per minute for Tier 1
      if (i + batchSize < scenes.length && !useMockData) {
        await new Promise(resolve => setTimeout(resolve, 12000)); // 12 seconds between batches
      }
    }

    // Calculate totals
    const successCount = imageResults.filter(img => img.status === 'completed').length;
    const errorCount = imageResults.filter(img => img.status === 'error').length;
    
    // Calculate cost based on settings
    const sizeMultiplier = settings?.size === '1024x1024' ? 1 : 2; // 1792x1024 costs 2x
    const qualityMultiplier = settings?.quality === 'hd' ? 2 : 1; // HD costs 2x standard
    const costPerImage = 0.04 * sizeMultiplier * qualityMultiplier; // Base: $0.04 for 1024x1024 standard
    const totalCost = useMockData ? 0 : successCount * costPerImage;
    
    const processingTime = (Date.now() - startTime) / 1000;

    // Update state with results
    updateProductionStage('images', {
      status: 'completed',
      progress: 100,
      generatedImages: imageResults,
    });

    // Send completion notification
    if (global.io) {
      global.io.emit('images:batchComplete', {
        successCount,
        errorCount,
        processingTime,
        totalCost,
        timestamp: new Date().toISOString(),
      });
    }

    const response: BatchImageResponse = {
      imageData: imageResults,
      totalCost,
      processingTime,
    };

    res.status(200).json(response);
  } catch (error) {
    console.error('Image batch generation error:', error);
    
    updateProductionStage('images', {
      status: 'error',
      error: error instanceof Error ? error.message : 'Failed to generate images',
    });

    if (global.io) {
      global.io.emit('images:batchError', {
        error: error instanceof Error ? error.message : 'Failed to generate images',
        timestamp: new Date().toISOString(),
      });
    }

    res.status(500).json({
      error: 'Failed to generate images',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
