import type { NextApiRequest, NextApiResponse } from 'next';
import { VoiceOption } from '@/lib/production-state';
import { updateProductionStage } from '@/lib/production-state';

// Mock voices for development
const MOCK_VOICES: VoiceOption[] = [
  {
    voice_id: 'winston_default',
    name: 'Winston (Default)',
    category: 'custom',
    description: 'Default Winston voice with warm, friendly tone',
    preview_url: '/audio/winston_preview.mp3',
    labels: {
      accent: 'american',
      age: 'middle_aged',
      gender: 'male',
      use_case: 'narration',
    },
    is_winston: true,
  },
  {
    voice_id: 'winston_enthusiastic',
    name: 'Winston (Enthusiastic)',
    category: 'custom',
    description: 'Energetic Winston voice for exciting content',
    preview_url: '/audio/winston_enthusiastic_preview.mp3',
    labels: {
      accent: 'american',
      age: 'middle_aged',
      gender: 'male',
      use_case: 'narration',
      style: 'enthusiastic',
    },
    is_winston: true,
  },
  {
    voice_id: 'winston_calm',
    name: 'Winston (Calm)',
    category: 'custom',
    description: 'Soothing Winston voice for reflective content',
    preview_url: '/audio/winston_calm_preview.mp3',
    labels: {
      accent: 'american',
      age: 'middle_aged',
      gender: 'male',
      use_case: 'narration',
      style: 'calm',
    },
    is_winston: true,
  },
  {
    voice_id: 'josh',
    name: 'Josh',
    category: 'premade',
    description: 'Deep, resonant voice perfect for narration',
    preview_url: '/audio/josh_preview.mp3',
    labels: {
      accent: 'american',
      age: 'young',
      gender: 'male',
      use_case: 'narration',
    },
    is_winston: false,
  },
  {
    voice_id: 'antoni',
    name: 'Antoni',
    category: 'premade',
    description: 'Well-rounded voice with great clarity',
    preview_url: '/audio/antoni_preview.mp3',
    labels: {
      accent: 'american',
      age: 'middle_aged',
      gender: 'male',
      use_case: 'narration',
    },
    is_winston: false,
  },
];

async function fetchElevenLabsVoices(): Promise<VoiceOption[]> {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  
  if (!apiKey) {
    console.warn('ElevenLabs API key not found, using mock voices');
    return MOCK_VOICES;
  }

  try {
    const response = await fetch('https://api.elevenlabs.io/v1/voices', {
      headers: {
        'xi-api-key': apiKey,
      },
    });

    if (!response.ok) {
      throw new Error(`ElevenLabs API error: ${response.status}`);
    }

    const data = await response.json();
    
    // Transform ElevenLabs response to our format
    const voices: VoiceOption[] = data.voices.map((voice: any) => ({
      voice_id: voice.voice_id,
      name: voice.name,
      category: voice.category,
      description: voice.description || '',
      preview_url: voice.preview_url,
      labels: voice.labels || {},
      is_winston: voice.name.toLowerCase().includes('winston') || 
                 voice.labels?.custom === 'winston',
    }));

    // Filter for narration-suitable voices
    const narratorVoices = voices.filter(voice => 
      voice.labels?.use_case === 'narration' ||
      voice.labels?.use_case === 'news' ||
      voice.labels?.gender === 'male' ||
      voice.is_winston,
    );

    // Sort Winston voices first
    return narratorVoices.sort((a, b) => {
      if (a.is_winston && !b.is_winston) return -1;
      if (!a.is_winston && b.is_winston) return 1;
      return a.name.localeCompare(b.name);
    });
  } catch (error) {
    console.error('Failed to fetch ElevenLabs voices:', error);
    return MOCK_VOICES;
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version',
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
    return;
  }

  try {
    // Update state to loading
    updateProductionStage('voice', {
      status: 'loading',
      error: undefined,
    });

    // Fetch voices (from ElevenLabs or mock)
    const voices = await fetchElevenLabsVoices();

    // Update state with available voices
    updateProductionStage('voice', {
      status: 'selecting',
      availableVoices: voices,
    });

    // Send WebSocket notification
    if (global.io) {
      global.io.emit('voice:listLoaded', {
        voiceCount: voices.length,
        winstonVoiceCount: voices.filter(v => v.is_winston).length,
        timestamp: new Date().toISOString(),
      });
    }

    res.status(200).json({
      voices,
      total: voices.length,
      winston_count: voices.filter(v => v.is_winston).length,
    });
  } catch (error) {
    console.error('Voice list error:', error);
    
    updateProductionStage('voice', {
      status: 'error',
      error: error instanceof Error ? error.message : 'Failed to fetch voices',
    });

    if (global.io) {
      global.io.emit('voice:listError', {
        error: error instanceof Error ? error.message : 'Failed to fetch voices',
        timestamp: new Date().toISOString(),
      });
    }

    res.status(500).json({
      error: 'Failed to fetch voices',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
