/**
 * RunwayML API Client for Node.js
 * Implements image-to-video generation using the official RunwayML API
 */

import fetch from 'node-fetch';

export interface RunwayVideoRequest {
  imageUrl: string;
  prompt: string;
  duration: number; // 5 or 10 seconds
  model?: string; // gen4_turbo or gen3a_turbo
  ratio?: string; // Video aspect ratio
  seed?: number;
  contentModeration?: {
    type: string;
  };
}

export interface RunwayTaskResponse {
  id: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED';
  output?: string[]; // Video URLs when completed
  error?: string;
  failure?: string;
  progress?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface RunwayVideoResponse {
  id: string;
  videoUrl?: string;
  status: 'processing' | 'completed' | 'failed';
  error?: string;
  progress?: number;
}

class RunwayMLClient {
  private apiKey: string;
  private baseUrl: string = 'https://api.dev.runwayml.com';
  private apiVersion: string = '2024-11-06';

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.RUNWAY_API_KEY || '';
    if (!this.apiKey) {
      throw new Error('RunwayML API key is required');
    }
  }

  private get headers() {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'X-Runway-Version': this.apiVersion,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  }

  /**
   * Converts an image URL to base64 data URI if needed
   */
  private async convertToDataUri(imageUrl: string): Promise<string> {
    // If already a data URI, return as is
    if (imageUrl.startsWith('data:')) {
      return imageUrl;
    }

    try {
      // Download the image
      const response = await fetch(imageUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch image: ${response.statusText}`);
      }

      const buffer = await response.buffer();
      const base64 = buffer.toString('base64');
      
      // Determine MIME type from content-type header or URL extension
      const contentType = response.headers.get('content-type') || 'image/jpeg';
      
      return `data:${contentType};base64,${base64}`;
    } catch (error) {
      console.error('Error converting image to data URI:', error);
      throw error;
    }
  }

  /**
   * Generate video from image using RunwayML API
   */
  async generateVideo(request: RunwayVideoRequest): Promise<RunwayTaskResponse> {
    const endpoint = `${this.baseUrl}/v1/image_to_video`;

    // Validate duration
    const duration = [5, 10].includes(request.duration) ? request.duration : 10;

    // Validate model and get valid ratios
    const model = request.model || 'gen4_turbo';
    const validRatios = model === 'gen4_turbo' 
      ? ['1280:720', '720:1280', '1104:832', '832:1104', '960:960', '1584:672']
      : ['1280:768', '768:1280']; // gen3a_turbo

    const ratio = request.ratio && validRatios.includes(request.ratio) 
      ? request.ratio 
      : validRatios[0];

    // Convert image URL to data URI if needed
    let imageData = request.imageUrl;
    if (!request.imageUrl.startsWith('data:')) {
      try {
        imageData = await this.convertToDataUri(request.imageUrl);
        console.log('Successfully converted image URL to data URI');
      } catch (error) {
        console.error('Failed to convert image URL to data URI:', error);
        // Continue with the original URL, API might accept it
        console.log('Continuing with original URL:', request.imageUrl);
      }
    }

    const payload = {
      promptImage: imageData,
      promptText: request.prompt,
      model: model,
      ratio: ratio,
      duration: duration,
      ...(request.seed !== undefined && { seed: request.seed }),
      ...(request.contentModeration && { contentModeration: request.contentModeration })
    };

    console.log('Sending video generation request:', {
      model,
      ratio,
      duration,
      promptLength: request.prompt.length,
      hasImage: !!imageData
    });

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error('RunwayML API error:', response.status, data);
        return {
          id: '',
          status: 'FAILED',
          error: data.error || `API error: ${response.status}`,
          failure: JSON.stringify(data)
        };
      }

      console.log('Video generation task created successfully:', data.id);
      return data as RunwayTaskResponse;
    } catch (error) {
      console.error('Request failed:', error);
      return {
        id: '',
        status: 'FAILED',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get task status
   */
  async getTaskStatus(taskId: string): Promise<RunwayTaskResponse> {
    const endpoint = `${this.baseUrl}/v1/tasks/${taskId}`;

    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: this.headers,
      });

      if (response.status === 404) {
        return {
          id: taskId,
          status: 'FAILED',
          error: 'Task not found'
        };
      }

      const data = await response.json();
      return data as RunwayTaskResponse;
    } catch (error) {
      console.error('Failed to get task status:', error);
      return {
        id: taskId,
        status: 'FAILED',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Poll for task completion with progress updates
   */
  async waitForCompletion(
    taskId: string,
    onProgress?: (progress: number) => void,
    maxWaitTime: number = 600, // 10 minutes
    pollInterval: number = 5    // 5 seconds
  ): Promise<string | null> {
    const startTime = Date.now();
    let lastProgress = 0;
    let pollCount = 0;

    console.log(`Starting to poll for task completion: ${taskId}`);

    while ((Date.now() - startTime) < maxWaitTime * 1000) {
      pollCount++;
      const status = await this.getTaskStatus(taskId);
      
      console.log(`Poll ${pollCount}: Task ${taskId} status: ${status.status}`, 
        status.progress ? `Progress: ${status.progress}%` : '');

      // Update progress if available
      if (status.progress && status.progress !== lastProgress) {
        lastProgress = status.progress;
        onProgress?.(status.progress);
      }

      switch (status.status) {
        case 'SUCCEEDED':
          if (status.output && status.output.length > 0) {
            console.log(`Task ${taskId} completed successfully with output:`, status.output[0]);
            return status.output[0];
          }
          console.error('Task succeeded but no output URL');
          return null;

        case 'FAILED':
          console.error(`Task ${taskId} failed:`, status.failure || status.error);
          return null;

        case 'CANCELLED':
          console.warn(`Task ${taskId} was cancelled`);
          return null;

        case 'PENDING':
        case 'RUNNING':
          // Still processing, continue polling
          break;

        default:
          console.warn(`Unknown task status for ${taskId}:`, status.status);
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
    }

    console.error(`Task ${taskId} timed out after ${maxWaitTime} seconds (${pollCount} polls)`);
    return null;
  }

  /**
   * Cancel a running task
   */
  async cancelTask(taskId: string): Promise<boolean> {
    const endpoint = `${this.baseUrl}/v1/tasks/${taskId}`;

    try {
      const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: this.headers,
      });

      return response.status === 204;
    } catch (error) {
      console.error('Failed to cancel task:', error);
      return false;
    }
  }

  /**
   * Get organization info including credits
   */
  async getOrganizationInfo(): Promise<any> {
    const endpoint = `${this.baseUrl}/v1/organization`;

    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: this.headers,
      });

      if (response.ok) {
        return await response.json();
      }
      
      return null;
    } catch (error) {
      console.error('Failed to get organization info:', error);
      return null;
    }
  }

  /**
   * Generate cinematic prompt with camera movements and style
   */
  generateCinematicPrompt(
    baseDescription: string,
    options: {
      style?: string;
      cameraMovement?: string;
      lighting?: string;
      mood?: string;
      details?: string[];
    } = {}
  ): string {
    const parts = [baseDescription];

    // Style descriptions
    const styleMap: Record<string, string> = {
      cinematic: 'cinematic quality, professional cinematography',
      noir: 'film noir style, high contrast black and white',
      cyberpunk: 'cyberpunk aesthetic, neon lights, futuristic',
      horror: 'horror atmosphere, dark and ominous',
      documentary: 'documentary style, realistic, handheld camera',
      anime: 'anime style animation, vibrant colors',
      retro: 'retro 1980s style, synthwave aesthetic'
    };

    if (options.style && styleMap[options.style]) {
      parts.push(styleMap[options.style]);
    }

    if (options.cameraMovement) {
      parts.push(`${options.cameraMovement} camera movement`);
    }

    if (options.lighting) {
      parts.push(`${options.lighting} lighting`);
    }

    if (options.mood) {
      parts.push(`${options.mood} mood`);
    }

    if (options.details) {
      parts.push(...options.details);
    }

    // Combine and truncate to 1000 chars
    let prompt = parts.join(', ');
    if (prompt.length > 1000) {
      prompt = prompt.substring(0, 997) + '...';
    }

    return prompt;
  }
}

// Singleton instance
let clientInstance: RunwayMLClient | null = null;

export function getRunwayClient(): RunwayMLClient {
  if (!clientInstance) {
    clientInstance = new RunwayMLClient();
  }
  return clientInstance;
}

export default RunwayMLClient;