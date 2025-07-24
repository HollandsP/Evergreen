import type { NextApiRequest, NextApiResponse } from 'next';
import { getElevenLabsClient } from '../../../lib/elevenlabs-client';
import ElevenLabsClient from '../../../lib/elevenlabs-client';
import { fileManager } from '@/lib/file-manager';
import fs from 'fs/promises';
import path from 'path';
import fetch from 'node-fetch';

interface GenerateAudioRequest {
  text: string;
  voice: string;
  sceneId: string;
  projectId: string;
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
  sceneId: string;
  cost?: number;
  characterCount?: number;
  savedPath?: string;
}

// Voice ID mapping for ElevenLabs - using actual voice IDs
const VOICE_MAP: Record<string, string> = {
  'male_calm': ElevenLabsClient.VOICES.ADAM,      // Adam - calm narrator
  'male_deep': ElevenLabsClient.VOICES.ARNOLD,    // Arnold - deep voice
  'male_british': ElevenLabsClient.VOICES.CALLUM, // Callum - British accent
  'male_narrator': ElevenLabsClient.VOICES.MATTHEW, // Matthew - British audiobook
  'male_news': ElevenLabsClient.VOICES.DANIEL,    // Daniel - news presenter
  'female_calm': ElevenLabsClient.VOICES.EMILY,   // Emily - calm female
  'female_british': ElevenLabsClient.VOICES.CHARLOTTE, // Charlotte - British female
  'female_narrator': ElevenLabsClient.VOICES.RACHEL,   // Rachel - American narrator
  'female_warm': ElevenLabsClient.VOICES.MATILDA,     // Matilda - warm American
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerateAudioResponse | { error: string }>,
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { text, voice, sceneId, projectId, voiceSettings } = req.body as GenerateAudioRequest;

    if (!text || !voice || !sceneId || !projectId) {
      return res.status(400).json({ error: 'Missing required fields' });
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
      return res.status(400).json({ error: 'Text exceeds maximum length of 5000 characters' });
    }

    // Get voice ID
    const voiceId = VOICE_MAP[voice] || VOICE_MAP['male_calm'];
    const elevenlabsClient = getElevenLabsClient();

    let result;
    let retries = 3;
    let lastError: Error | null = null;

    // Retry logic for resilience
    while (retries > 0) {
      try {
        result = await elevenlabsClient.textToSpeech({
          text,
          voice_id: voiceId,
          model_id: 'eleven_turbo_v2_5', // Using Turbo v2.5 for 50% cost reduction
          voice_settings: {
            stability: voiceSettings?.stability ?? 0.5,
            similarity_boost: voiceSettings?.similarity_boost ?? 0.75,
            style: voiceSettings?.style ?? 0.5,
            use_speaker_boost: voiceSettings?.use_speaker_boost ?? true,
          },
        });
        break; // Success, exit retry loop
      } catch (error) {
        console.error(`ElevenLabs attempt ${4 - retries} failed:`, error);
        lastError = error as Error;
        retries--;
        
        // Wait before retry with exponential backoff
        if (retries > 0) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, 3 - retries) * 1000));
        }
      }
    }

    if (!result) {
      throw lastError || new Error('Failed to generate audio after 3 attempts');
    }

    // Log generation for cost tracking
    console.log(`Generated audio for scene ${sceneId} using ElevenLabs - Cost: $${result.cost.toFixed(4)}`);

    // Save audio to project folder
    let savedFilename: string | undefined;
    try {
      // Download the audio
      const audioResponse = await fetch(result.audioUrl);
      if (!audioResponse.ok) {
        throw new Error('Failed to download generated audio');
      }
      
      const buffer = await audioResponse.buffer();
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      savedFilename = `elevenlabs_${voice}_${timestamp}.mp3`;
      
      // Get the path to save the audio
      const audioPath = fileManager.getAssetFilePath(projectId, sceneId, 'audio', savedFilename);
      
      // Ensure directory exists
      await fs.mkdir(path.dirname(audioPath), { recursive: true });
      
      // Save the audio
      await fs.writeFile(audioPath, buffer);
      
      // Update scene metadata
      await fileManager.addAssetToScene(projectId, sceneId, 'audio', savedFilename);
      
      console.log(`Saved audio to: ${audioPath}`);
    } catch (saveError) {
      console.error('Failed to save audio:', saveError);
      // Don't fail the entire operation if save fails
    }

    return res.status(200).json({
      audioUrl: result.audioUrl,
      duration: result.duration,
      sceneId,
      cost: result.cost,
      characterCount: result.characterCount,
      savedPath: savedFilename,
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
