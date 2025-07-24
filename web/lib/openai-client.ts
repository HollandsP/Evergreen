/**
 * OpenAI API Client for Node.js
 * Implements DALL-E 3 image generation
 */

import OpenAI from 'openai';

export interface ImageGenerationRequest {
  prompt: string;
  size?: '1024x1024' | '1024x1792' | '1792x1024';
  quality?: 'standard' | 'hd';
  style?: 'vivid' | 'natural';
  n?: number;
}

export interface ImageGenerationResponse {
  url: string;
  revisedPrompt?: string;
}

class OpenAIClient {
  private client: OpenAI;

  constructor(apiKey?: string) {
    const key = apiKey || process.env.OPENAI_API_KEY;
    if (!key) {
      throw new Error('OpenAI API key is required');
    }

    this.client = new OpenAI({
      apiKey: key,
    });
  }

  /**
   * Generate image using DALL-E 3
   * Cost: $0.040 for 1024x1024, $0.080 for 1024x1792 or 1792x1024
   */
  async generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
    try {
      console.log('Generating image with DALL-E 3:', {
        promptLength: request.prompt.length,
        size: request.size || '1024x1024',
        quality: request.quality || 'standard',
        style: request.style || 'natural',
      });

      const response = await this.client.images.generate({
        model: 'dall-e-3',
        prompt: request.prompt,
        n: request.n || 1,
        size: request.size || '1024x1024',
        quality: request.quality || 'standard',
        style: request.style || 'natural',
        response_format: 'url',
      });

      if (!response.data || response.data.length === 0) {
        throw new Error('No image generated');
      }

      const imageData = response.data[0];
      
      // Log cost tracking
      const cost = request.size === '1024x1024' ? 0.04 : 0.08;
      console.log(`DALL-E 3 generation cost: $${cost.toFixed(3)}`);

      return {
        url: imageData.url!,
        revisedPrompt: imageData.revised_prompt,
      };
    } catch (error) {
      console.error('OpenAI image generation error:', error);
      
      if (error instanceof OpenAI.APIError) {
        // Handle specific OpenAI API errors
        if (error.status === 400) {
          if (error.message.includes('content_policy_violation')) {
            throw new Error('The prompt was rejected due to content policy. Please modify your prompt and try again.');
          }
          throw new Error(`Invalid request: ${error.message}`);
        } else if (error.status === 401) {
          throw new Error('Invalid API key. Please check your OpenAI API key.');
        } else if (error.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later.');
        } else if (error.status === 500) {
          throw new Error('OpenAI server error. Please try again later.');
        }
      }
      
      throw error;
    }
  }

  /**
   * Validate and sanitize prompt for DALL-E 3
   */
  sanitizePrompt(prompt: string): string {
    // Remove any potential harmful content
    let sanitized = prompt.trim();
    
    // DALL-E 3 has a 4000 character limit
    if (sanitized.length > 4000) {
      sanitized = sanitized.substring(0, 3997) + '...';
    }
    
    return sanitized;
  }

  /**
   * Generate a cinematic prompt for DALL-E 3
   */
  generateCinematicPrompt(
    baseDescription: string,
    options: {
      style?: string;
      lighting?: string;
      mood?: string;
      details?: string[];
      cinematography?: string;
    } = {}
  ): string {
    const parts = [baseDescription];

    // Style descriptions for DALL-E 3
    const styleMap: Record<string, string> = {
      cinematic: 'cinematic quality, professional cinematography, movie still',
      photorealistic: 'photorealistic, highly detailed, professional photography',
      artistic: 'artistic rendering, stylized, creative interpretation',
      animated: 'animated style, cartoon-like, vibrant colors',
      noir: 'film noir style, dramatic shadows, high contrast',
      cyberpunk: 'cyberpunk aesthetic, neon lights, futuristic cityscape',
      fantasy: 'fantasy art style, magical atmosphere, ethereal quality',
    };

    if (options.style && styleMap[options.style]) {
      parts.push(styleMap[options.style]);
    }

    if (options.lighting) {
      parts.push(`${options.lighting} lighting`);
    }

    if (options.mood) {
      parts.push(`${options.mood} mood and atmosphere`);
    }

    if (options.cinematography) {
      parts.push(options.cinematography);
    }

    if (options.details && options.details.length > 0) {
      parts.push(...options.details);
    }

    // DALL-E 3 specific optimizations
    parts.push('high quality', '4K resolution');

    return this.sanitizePrompt(parts.join(', '));
  }
}

// Singleton instance
let clientInstance: OpenAIClient | null = null;

export function getOpenAIClient(): OpenAIClient {
  if (!clientInstance) {
    clientInstance = new OpenAIClient();
  }
  return clientInstance;
}

export default OpenAIClient;