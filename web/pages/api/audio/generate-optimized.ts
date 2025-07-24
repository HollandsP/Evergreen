/**
 * Optimized Audio Generation API using ElevenLabs Turbo v2.5
 * 50% cost reduction compared to standard model
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { getElevenLabsClient } from '../../../lib/elevenlabs-client';
import ElevenLabsClient from '../../../lib/elevenlabs-client';
import wsManager from '../../../lib/websocket';

interface GenerateAudioRequest {
  text: string;
  voiceId?: string;
  voice?: string; // Legacy support
  model?: string;
  emotion?: string;
  speed?: number;
  sceneId?: string;
  projectId?: string;
  voiceSettings?: {
    stability?: number;
    similarity_boost?: number;
    style?: number;
    use_speaker_boost?: boolean;
  };
}

interface GenerateAudioResponse {
  audioUrl: string;
  duration: number;
  sceneId?: string;
  cost?: number;
  characterCount?: number;
  jobId?: string;
  status: 'completed' | 'processing' | 'failed';
  model?: string;
}

// Optimized voice ID mapping for ElevenLabs
const VOICE_MAP: Record<string, string> = {
  'male_calm': 'pNInz6obpgDQGcFmaJgB',      // Adam - calm narrator
  'male_deep': 'VR6AewLTigWG4xSOukaG',      // Arnold - deep voice
  'male_british': 'N2lVS1w4EtoT3dr4eOWO',   // Callum - British accent
  'male_narrator': 'EXAVITQu4vr4xnSDxMaL',  // Matthew - British audiobook
  'male_news': 'onwK4e9ZLuTAKqWW03F9',      // Daniel - news presenter
  'female_calm': 'LcfcDJNUP1GQjkzn1xUU',    // Emily - calm female
  'female_british': 'XB0fDUnXU5powFXDhCwa', // Charlotte - British female
  'female_narrator': '21m00Tcm4TlvDq8ikWAM', // Rachel - American narrator
  'female_warm': 'XrExE9yKIg1WjnnlVkGX',    // Matilda - warm American
  'default': 'pNInz6obpgDQGcFmaJgB',         // Default to Adam
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerateAudioResponse | { error: string }>,
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { 
      text, 
      voiceId, 
      voice, 
      model = 'eleven_turbo_v2_5', // Default to Turbo v2.5 for 50% cost reduction
      emotion,
      speed = 1.0,
      sceneId, 
      projectId,
      voiceSettings 
    } = req.body as GenerateAudioRequest;

    if (!text) {
      return res.status(400).json({ error: 'Missing required field: text' });
    }

    // Check for API key
    if (!process.env.ELEVENLABS_API_KEY) {
      return res.status(500).json({ error: 'ElevenLabs API key not configured' });
    }

    // Validate text length
    if (text.length === 0) {
      return res.status(400).json({ error: 'Text cannot be empty' });
    }

    if (text.length > 5000) {
      return res.status(400).json({ error: 'Text exceeds maximum length of 5000 characters for ElevenLabs Turbo v2.5' });
    }

    // Get voice ID - prefer explicit voiceId, fallback to voice mapping
    const finalVoiceId = voiceId || VOICE_MAP[voice || 'default'] || VOICE_MAP['default'];
    
    // Apply emotion tags if specified
    let finalText = text;
    if (emotion) {
      finalText = `[${emotion}] ${text}`;
    }
    
    // Generate job ID for tracking
    const jobId = `audio_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const elevenlabsClient = getElevenLabsClient();

    let result;
    let retries = 3;
    let lastError: Error | null = null;

    // Emit progress start
    if (sceneId && projectId) {
      wsManager.emit('audio_generation_started', {
        jobId,
        projectId,
        sceneId,
        status: 'processing',
        progress: 0,
        model,
        voiceId: finalVoiceId,
        characterCount: finalText.length,
        estimatedCost: finalText.length * 0.0005 // Turbo v2.5 pricing
      });
    }

    // Retry logic for resilience
    while (retries > 0) {
      try {
        result = await elevenlabsClient.textToSpeech({
          text: finalText,
          voice_id: finalVoiceId,
          model_id: model,
          voice_settings: {
            stability: voiceSettings?.stability ?? 0.5,
            similarity_boost: voiceSettings?.similarity_boost ?? 0.75,
            style: voiceSettings?.style ?? 0.5,
            use_speaker_boost: voiceSettings?.use_speaker_boost ?? true,
          },
          output_format: 'mp3_44100_128', // Optimized format for quality/size balance
        });
        break; // Success, exit retry loop
      } catch (error) {
        console.error(`ElevenLabs attempt ${4 - retries} failed:`, error);
        lastError = error as Error;
        retries--;
        
        // Emit progress update for retries
        if (retries > 0 && sceneId && projectId) {
          wsManager.emit('audio_generation_retry', {
            jobId,
            projectId,
            sceneId,
            attempt: 4 - retries,
            maxRetries: 3,
            error: (error as Error).message
          });
        }
        
        // Wait before retry with exponential backoff
        if (retries > 0) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, 3 - retries) * 1000));
        }
      }
    }

    if (!result) {
      if (sceneId && projectId) {
        wsManager.emit('audio_generation_failed', {
          jobId,
          projectId,
          sceneId,
          error: lastError?.message || 'Failed to generate audio after 3 attempts'
        });
      }
      throw lastError || new Error('Failed to generate audio after 3 attempts');
    }

    // Calculate cost (Turbo v2.5: $0.0005 per character, 50% cheaper than standard)
    const characterCount = finalText.length;
    const cost = characterCount * 0.0005; // Turbo v2.5 pricing
    
    // Log generation for cost tracking
    console.log(`Generated audio using ${model} - Characters: ${characterCount}, Cost: $${cost.toFixed(4)}, Voice: ${finalVoiceId}`);
    
    // Emit completion event
    if (sceneId && projectId) {
      wsManager.emit('audio_generation_completed', {
        jobId,
        projectId,
        sceneId,
        audioUrl: result.audioUrl,
        status: 'completed',
        cost,
        duration: result.duration,
        characterCount,
        model,
        voiceId: finalVoiceId
      });
    }

    return res.status(200).json({
      audioUrl: result.audioUrl,
      duration: result.duration,
      sceneId,
      cost,
      characterCount,
      jobId,
      status: 'completed' as const,
      model
    });

  } catch (error) {
    console.error('Audio generation error:', error);
    
    // Handle specific errors
    if (error instanceof Error) {
      if (error.message.includes('Invalid API key')) {
        return res.status(401).json({ 
          error: 'Invalid ElevenLabs API key. Please check your configuration.', 
        });
      }
      if (error.message.includes('Rate limit')) {
        return res.status(429).json({ 
          error: 'Rate limit exceeded. Please try again later.', 
        });
      }
      if (error.message.includes('Invalid request parameters')) {
        return res.status(400).json({ 
          error: 'Invalid voice or settings. Please check your request.', 
        });
      }
      if (error.message.includes('insufficient_quota')) {
        return res.status(402).json({
          error: 'ElevenLabs quota exceeded. Please add more credits to your account.'
        });
      }
    }
    
    return res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Failed to generate audio', 
    });
  }
}

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '1mb',
    },
  },
};