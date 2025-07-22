import type { NextApiRequest, NextApiResponse } from 'next';

interface GenerateImageRequest {
  prompt: string;
  provider: 'dalle3';  // Flux.1 removed due to high subscription costs
  sceneId: string;
  size?: string;
}

interface GenerateImageResponse {
  url: string;
  provider: string;
  sceneId: string;
}

// Mock implementation for development
// In production, this would integrate with OpenAI's DALL-E 3 API
// Note: Flux.1 support was removed due to high subscription costs
async function generateWithDALLE3(prompt: string): Promise<string> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // In production:
  // const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  // const response = await openai.images.generate({
  //   model: "dall-e-3",
  //   prompt: prompt,
  //   n: 1,
  //   size: size as any,
  //   quality: "standard",
  //   style: "natural"
  // });
  // return response.data[0].url;
  
  // Mock response - return a placeholder image
  const encodedPrompt = encodeURIComponent(prompt.slice(0, 100));
  return `https://via.placeholder.com/1792x1024/1a1a1a/00ff00?text=${encodedPrompt}`;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerateImageResponse | { error: string }>,
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { prompt, provider, sceneId } = req.body as GenerateImageRequest;

    if (!prompt || !provider || !sceneId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    if (provider !== 'dalle3') {
      return res.status(400).json({ error: 'Invalid provider. Only DALL-E 3 is supported.' });
    }

    // Validate and sanitize prompt
    const sanitizedPrompt = prompt.trim().slice(0, 4000); // DALL-E 3 has a 4000 character limit
    
    if (sanitizedPrompt.length === 0) {
      return res.status(400).json({ error: 'Prompt cannot be empty' });
    }

    let imageUrl: string;
    
    try {
      // Only DALL-E 3 is supported (Flux.1 removed due to high subscription costs)
      imageUrl = await generateWithDALLE3(sanitizedPrompt);
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
      }
      
      throw error;
    }

    // Log generation for analytics (in production)
    console.log(`Generated image for scene ${sceneId} using DALL-E 3`);
    // Note: Cost for DALL-E 3 - $0.040 for 1024x1024, $0.080 for 1792x1024

    res.status(200).json({
      url: imageUrl,
      provider,
      sceneId,
    });
  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({ 
      error: 'Failed to generate image. Please try again.', 
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
