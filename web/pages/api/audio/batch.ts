import type { NextApiRequest, NextApiResponse } from 'next';
import { ScriptScene, AudioData } from '@/types';
import { updateProductionStage } from '@/lib/production-state';
// import { v4 as uuidv4 } from 'uuid';

interface BatchAudioRequest {
  scenes: ScriptScene[];
  voiceId: string;
  settings?: {
    stability?: number;
    similarity_boost?: number;
    style?: number;
    use_speaker_boost?: boolean;
  };
}

interface BatchAudioResponse {
  audioData: AudioData[];
  totalDuration: number;
  totalCost: number;
  processingTime: number;
}

// Mock audio generation for development
async function generateMockAudio(scene: ScriptScene): Promise<AudioData> {
  // Simulate processing delay
  await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));
  
  // Calculate duration based on narration length (roughly 150 words per minute)
  const words = scene.narration.split(/\s+/).length;
  const duration = Math.max(2, Math.round((words / 150) * 60 * 10) / 10);
  
  return {
    sceneId: scene.id,
    url: `/api/audio/mock/${scene.id}`,
    duration,
    status: 'completed',
  };
}

// Generate audio with ElevenLabs
async function generateElevenLabsAudio(
  scene: ScriptScene,
  voiceId: string,
  settings?: BatchAudioRequest['settings'],
): Promise<AudioData> {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  
  if (!apiKey) {
    throw new Error('ElevenLabs API key not configured');
  }
  
  try {
    const response = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
      {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': apiKey,
        },
        body: JSON.stringify({
          text: scene.narration,
          model_id: 'eleven_monolingual_v1',
          voice_settings: {
            stability: settings?.stability ?? 0.5,
            similarity_boost: settings?.similarity_boost ?? 0.5,
            style: settings?.style ?? 0,
            use_speaker_boost: settings?.use_speaker_boost ?? true,
          },
        }),
      },
    );
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`ElevenLabs API error: ${response.status} - ${error}`);
    }
    
    // In production, you would upload the audio to S3 or similar
    // For now, we'll return a mock URL
    // const audioBlob = await response.blob();
    // const audioBuffer = await audioBlob.arrayBuffer();
    
    // Calculate actual duration (would need audio processing library in production)
    const words = scene.narration.split(/\s+/).length;
    const estimatedDuration = Math.max(2, Math.round((words / 150) * 60 * 10) / 10);
    
    // TODO: Upload to S3 and get real URL
    const audioUrl = `/api/audio/generated/${scene.id}`;
    
    return {
      sceneId: scene.id,
      url: audioUrl,
      duration: estimatedDuration,
      status: 'completed',
    };
  } catch (error) {
    console.error(`Failed to generate audio for scene ${scene.id}:`, error);
    return {
      sceneId: scene.id,
      url: '',
      duration: 0,
      status: 'error',
      error: error instanceof Error ? error.message : 'Failed to generate audio',
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
    const { scenes, voiceId, settings } = req.body as BatchAudioRequest;

    if (!scenes || !Array.isArray(scenes) || scenes.length === 0) {
      return res.status(400).json({ error: 'No scenes provided' });
    }

    if (!voiceId) {
      return res.status(400).json({ error: 'No voice ID provided' });
    }

    const startTime = Date.now();
    
    // Update state to generating
    updateProductionStage('audio', {
      status: 'generating',
      progress: 0,
      generatedAudio: [],
      totalDuration: 0,
      error: undefined,
    });

    // Send WebSocket notification
    if (global.io) {
      global.io.emit('audio:batchStart', {
        sceneCount: scenes.length,
        voiceId,
        timestamp: new Date().toISOString(),
      });
    }

    const audioResults: AudioData[] = [];
    const useMockData = !process.env.ELEVENLABS_API_KEY || process.env.USE_MOCK_AUDIO === 'true';

    // Process scenes in batches to avoid rate limits
    const batchSize = 3;
    for (let i = 0; i < scenes.length; i += batchSize) {
      const batch = scenes.slice(i, Math.min(i + batchSize, scenes.length));
      
      const batchPromises = batch.map(scene => 
        useMockData 
          ? generateMockAudio(scene)
          : generateElevenLabsAudio(scene, voiceId, settings),
      );
      
      const batchResults = await Promise.all(batchPromises);
      audioResults.push(...batchResults);
      
      // Update progress
      const progress = Math.round((audioResults.length / scenes.length) * 100);
      updateProductionStage('audio', {
        progress,
        generatedAudio: audioResults,
        totalDuration: audioResults.reduce((sum, audio) => sum + audio.duration, 0),
      });
      
      // Send progress update
      if (global.io) {
        global.io.emit('audio:batchProgress', {
          progress,
          generatedScenes: audioResults.length,
          totalScenes: scenes.length,
          timestamp: new Date().toISOString(),
        });
      }
      
      // Add delay between batches to respect rate limits
      if (i + batchSize < scenes.length && !useMockData) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    // Calculate totals
    const totalDuration = audioResults.reduce((sum, audio) => sum + audio.duration, 0);
    const successCount = audioResults.filter(a => a.status === 'completed').length;
    const errorCount = audioResults.filter(a => a.status === 'error').length;
    
    // Calculate cost (ElevenLabs pricing: ~$0.30 per 1000 characters)
    const totalCharacters = scenes.reduce((sum, scene) => sum + scene.narration.length, 0);
    const totalCost = useMockData ? 0 : (totalCharacters / 1000) * 0.30;
    
    const processingTime = (Date.now() - startTime) / 1000;

    // Update state with results
    updateProductionStage('audio', {
      status: 'completed',
      progress: 100,
      generatedAudio: audioResults,
      totalDuration,
    });

    // Send completion notification
    if (global.io) {
      global.io.emit('audio:batchComplete', {
        totalDuration,
        successCount,
        errorCount,
        processingTime,
        totalCost,
        timestamp: new Date().toISOString(),
      });
    }

    const response: BatchAudioResponse = {
      audioData: audioResults,
      totalDuration,
      totalCost,
      processingTime,
    };

    res.status(200).json(response);
  } catch (error) {
    console.error('Audio batch generation error:', error);
    
    updateProductionStage('audio', {
      status: 'error',
      error: error instanceof Error ? error.message : 'Failed to generate audio',
    });

    if (global.io) {
      global.io.emit('audio:batchError', {
        error: error instanceof Error ? error.message : 'Failed to generate audio',
        timestamp: new Date().toISOString(),
      });
    }

    res.status(500).json({
      error: 'Failed to generate audio',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
