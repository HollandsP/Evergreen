import type { NextApiRequest, NextApiResponse } from 'next';

// Mock ElevenLabs API response for development
// In production, replace with actual ElevenLabs API integration

interface GenerateAudioRequest {
  text: string;
  voice: string;
  sceneId: string;
}

interface GenerateAudioResponse {
  audioUrl: string;
  duration: number;
  sceneId: string;
}

// Voice ID mapping for ElevenLabs
const VOICE_MAP: Record<string, string> = {
  'male_calm': 'pNInz6obpgDQGcFmaJgB', // Adam - calm narrator
  'male_deep': 'VR6AewLTigWG4xSOukaG', // Arnold - deep voice
  'male_british': 'ThT5KcBeYPX3keUQqHPh', // Callum - British accent
};

// Mock duration calculation based on text length
// Rough estimate: ~150 words per minute
const calculateDuration = (text: string): number => {
  const words = text.split(/\s+/).length;
  const wordsPerSecond = 150 / 60; // 2.5 words per second
  return Math.ceil(words / wordsPerSecond);
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<GenerateAudioResponse | { error: string }>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { text, voice, sceneId } = req.body as GenerateAudioRequest;

    if (!text || !voice || !sceneId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Get voice ID
    const voiceId = VOICE_MAP[voice] || VOICE_MAP['male_calm'];

    // In production, make actual API call to ElevenLabs
    if (process.env.ELEVENLABS_API_KEY) {
      const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': process.env.ELEVENLABS_API_KEY
        },
        body: JSON.stringify({
          text,
          model_id: 'eleven_monolingual_v1',
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75
          }
        })
      });

      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.statusText}`);
      }

      // In production, you would:
      // 1. Save the audio buffer to S3 or local storage
      // 2. Return the URL to the saved file
      // 3. Calculate actual duration using audio processing library

      // For now, return mock data
      const duration = calculateDuration(text);
      return res.status(200).json({
        audioUrl: `/api/audio/mock/${sceneId}.mp3`,
        duration,
        sceneId
      });
    }

    // Development mock response
    const duration = calculateDuration(text);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Return mock audio URL
    // In production, this would be the actual generated audio file URL
    return res.status(200).json({
      audioUrl: `/api/audio/mock/${sceneId}.mp3`,
      duration,
      sceneId
    });

  } catch (error) {
    console.error('Audio generation error:', error);
    return res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Failed to generate audio' 
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