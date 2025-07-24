/**
 * GPT-4 prompt enhancement endpoint
 * Uses AI to improve and optimize prompts for better results
 */

import { NextApiRequest, NextApiResponse } from 'next';
import { z } from 'zod';

const enhanceRequestSchema = z.object({
  prompt: z.string().min(1, 'Prompt is required'),
  type: z.enum(['storyboard', 'image', 'video', 'audio']),
  context: z.object({
    sceneType: z.string().optional(),
    genre: z.string().optional(),
    mood: z.string().optional(),
    audioDuration: z.number().optional(),
    previousPrompts: z.array(z.string()).optional(),
  }).optional(),
  enhancementGoals: z.array(z.enum([
    'clarity',
    'detail',
    'atmosphere',
    'technical_quality',
    'artistic_style',
    'motion_description',
    'emotion',
    'moderation_safety'
  ])).optional(),
});

type EnhanceRequest = z.infer<typeof enhanceRequestSchema>;

interface EnhanceResponse {
  enhancedPrompt: string;
  improvements: string[];
  confidenceScore: number;
  alternatives?: string[];
  warnings?: string[];
}

/**
 * Get enhancement instructions based on prompt type
 */
function getEnhancementInstructions(type: string, goals: string[] = []) {
  const baseInstructions = {
    storyboard: `Enhance this storyboard description to be more visual and specific. Focus on:
- Visual composition and framing
- Character positioning and actions
- Environmental details
- Lighting and atmosphere
- Color palette suggestions`,
    
    image: `Enhance this DALL-E 3 image prompt for better generation results. Focus on:
- Specific visual details and textures
- Professional photography terms
- Lighting and composition techniques
- Style modifiers and quality indicators
- Technical camera specifications`,
    
    video: `Enhance this RunwayML video prompt for better motion generation. Focus on:
- Specific camera movements (dolly, pan, tilt, etc.)
- Motion descriptors and timing
- Atmospheric effects and dynamics
- Professional cinematography terms
- Scene transitions and flow`,
    
    audio: `Enhance this ElevenLabs audio prompt for better voice synthesis. Focus on:
- Emotion tags in brackets [excited], [whispers]
- Pacing and rhythm indicators
- Voice tone descriptors
- Pause markers and effects
- Character voice consistency`,
  };
  
  let instructions = baseInstructions[type as keyof typeof baseInstructions] || baseInstructions.image;
  
  // Add goal-specific instructions
  if (goals.includes('technical_quality')) {
    instructions += '\n- Add technical quality markers (4K, professional, high detail)';
  }
  if (goals.includes('artistic_style')) {
    instructions += '\n- Include artistic style references and aesthetic modifiers';
  }
  if (goals.includes('atmosphere')) {
    instructions += '\n- Enhance atmospheric and mood descriptions';
  }
  if (goals.includes('moderation_safety')) {
    instructions += '\n- Ensure content is appropriate and moderation-safe';
  }
  
  return instructions;
}

/**
 * Create system prompt for GPT-4 enhancement
 */
function createSystemPrompt(type: string, context?: any, goals: string[] = []) {
  return `You are an expert prompt engineer specializing in AI content generation. Your task is to enhance prompts for ${type} generation to achieve better, more consistent results.

${getEnhancementInstructions(type, goals)}

Guidelines:
1. Preserve the original creative intent while adding technical improvements
2. Use industry-standard terminology for the specific medium
3. Add specific, actionable details that improve generation quality
4. Maintain appropriate length for the target platform
5. Ensure content is appropriate and follows platform guidelines

${context ? `Context:
- Scene Type: ${context.sceneType || 'Not specified'}
- Genre: ${context.genre || 'Not specified'}
- Mood: ${context.mood || 'Not specified'}
- Duration: ${context.audioDuration ? `${context.audioDuration}s` : 'Not specified'}` : ''}

Respond with:
1. Enhanced prompt (improved version)
2. List of specific improvements made
3. Confidence score (0-100) for the enhancement
4. Any warnings about potential issues

Format as JSON:
{
  "enhancedPrompt": "enhanced version here",
  "improvements": ["improvement 1", "improvement 2"],
  "confidenceScore": 85,
  "warnings": ["warning if any"]
}`;
}

/**
 * Enhanced prompt using local optimization (fallback)
 */
function enhancePromptLocally(prompt: string, type: string, context?: any): EnhanceResponse {
  let enhanced = prompt;
  const improvements: string[] = [];
  
  // Add type-specific enhancements
  switch (type) {
    case 'image':
      if (!enhanced.includes('cinematic')) {
        enhanced += ', cinematic composition';
        improvements.push('Added cinematic composition');
      }
      if (!enhanced.includes('high detail')) {
        enhanced += ', high detail, photorealistic';
        improvements.push('Added quality markers');
      }
      if (!enhanced.includes('lighting')) {
        enhanced += ', professional lighting';
        improvements.push('Added lighting specification');
      }
      break;
      
    case 'video':
      if (!enhanced.includes(':')) {
        enhanced = `Smooth camera movement: ${enhanced}`;
        improvements.push('Added camera movement prefix');
      }
      if (!enhanced.includes('professional')) {
        enhanced += ', professional cinematography';
        improvements.push('Added cinematography qualifier');
      }
      break;
      
    case 'audio':
      if (!enhanced.includes('[') && !enhanced.includes(']')) {
        enhanced = `[calm] ${enhanced}`;
        improvements.push('Added emotion tag');
      }
      break;
  }
  
  // Add context-based enhancements
  if (context?.genre) {
    const genreModifiers = {
      horror: ', dark atmosphere, eerie mood',
      'sci-fi': ', futuristic aesthetic, technological elements',
      documentary: ', realistic style, natural lighting',
      cinematic: ', dramatic composition, film-quality'
    };
    
    const modifier = genreModifiers[context.genre as keyof typeof genreModifiers];
    if (modifier && !enhanced.includes(modifier.substring(2))) {
      enhanced += modifier;
      improvements.push(`Added ${context.genre} genre styling`);
    }
  }
  
  return {
    enhancedPrompt: enhanced,
    improvements,
    confidenceScore: 75, // Local enhancement is less confident than AI
    warnings: improvements.length === 0 ? ['No significant improvements identified'] : []
  };
}

/**
 * Main handler
 */
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    // Validate request
    const {
      prompt,
      type,
      context,
      enhancementGoals = ['clarity', 'detail', 'technical_quality']
    } = enhanceRequestSchema.parse(req.body);
    
    // Try to use OpenAI API for enhancement
    if (process.env.OPENAI_API_KEY) {
      try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'gpt-4o-mini', // More cost-effective than GPT-4
            messages: [
              {
                role: 'system',
                content: createSystemPrompt(type, context, enhancementGoals)
              },
              {
                role: 'user',
                content: `Please enhance this ${type} prompt: "${prompt}"`
              }
            ],
            temperature: 0.7,
            max_tokens: 800,
          }),
        });
        
        if (response.ok) {
          const data = await response.json();
          const content = data.choices[0]?.message?.content;
          
          if (content) {
            try {
              // Try to parse as JSON
              const parsed = JSON.parse(content);
              return res.status(200).json({
                ...parsed,
                method: 'ai',
                cost: 0.002 // Estimated cost in USD
              });
            } catch {
              // If JSON parsing fails, return as enhanced prompt
              return res.status(200).json({
                enhancedPrompt: content,
                improvements: ['AI-enhanced prompt'],
                confidenceScore: 90,
                method: 'ai',
                cost: 0.002
              });
            }
          }
        }
      } catch (error) {
        console.error('OpenAI API error:', error);
        // Fall through to local enhancement
      }
    }
    
    // Fallback to local enhancement
    const result = enhancePromptLocally(prompt, type, context);
    return res.status(200).json({
      ...result,
      method: 'local',
      cost: 0
    });
    
  } catch (error) {
    console.error('Prompt enhancement error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        error: 'Invalid request',
        details: error.errors
      });
    }
    
    return res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to enhance prompt'
    });
  }
}