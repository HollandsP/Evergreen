/**
 * ElevenLabs API Client for Node.js
 * Implements text-to-speech using Turbo v2.5 model
 */

import fetch from 'node-fetch';
import { promises as fs } from 'fs';
import path from 'path';

export interface VoiceSettings {
  stability: number;
  similarity_boost: number;
  style?: number;
  use_speaker_boost?: boolean;
}

export interface TextToSpeechRequest {
  text: string;
  voice_id: string;
  model_id?: string;
  voice_settings?: VoiceSettings;
  output_format?: string;
  optimize_streaming_latency?: number;
}

export interface VoiceInfo {
  voice_id: string;
  name: string;
  labels?: Record<string, string>;
  description?: string;
  preview_url?: string;
}

export interface TextToSpeechResponse {
  audioUrl: string;
  duration: number;
  cost: number;
  characterCount: number;
}

class ElevenLabsClient {
  private apiKey: string;
  private baseUrl: string = 'https://api.elevenlabs.io/v1';
  
  // Default voice IDs
  static readonly VOICES = {
    ADAM: '21m00Tcm4TlvDq8ikWAM',     // Calm narrator
    ANTONI: 'ErXwobaYiN019PkySvjV',  // Well-rounded
    ARNOLD: 'VR6AewLTigWG4xSOukaG',  // Deep voice
    CALLUM: 'N2lVS1w4EtoT3dr4eOWO',  // British accent
    CHARLIE: 'IKne3meq5aSn9XLyUdCD', // Casual
    CHARLOTTE: 'XB0fDUnXU5powFXDhCwa', // Female British
    CLYDE: '2EiwWnXFnvU5JabPnv8n',   // War veteran
    DANIEL: 'onwK4e9ZLuTAKqWW03F9',  // British news presenter
    DAVE: 'CYw3kZ02Hs0563khs1Fj',    // British/Essex
    DOMI: 'AZnzlk1XvdvUeBnXmlld',    // Female, strong
    DOROTHY: 'ThT5KcBeYPX3keUQqHPh', // Female, pleasant
    ELLI: 'MF3mGyEYCl7XYWbV9V6O',    // Female, emotional
    EMILY: 'LcfcDJNUP1GQjkzn1xUU',   // Female, calm
    ETHAN: 'g5CIjZEefAph4nQFvHAz',   // American
    FIN: 'D38z5RcWu1voky8WS1ja',     // Irish sailor
    FREYA: 'jsCqWAovK2LkecY7zXl4',   // Female, American
    GIGI: 'jBpfuIE2acCO8z3wKNLl',    // Female, childish
    GIOVANNI: 'zcAOhNBS3c14rBihAFp1', // Italian foreigner
    GRACE: 'oWAxZDx7w5VEj9dCyTzz',   // Female, Southern US
    HARRY: 'SOYHLrjzK2X1ezoPC6cr',   // American, anxious
    JAMES: 'ZQe5CZNOzWyzPSCn5a3c',    // Australian
    JEREMY: 'bVMeCyTHy58xNoL34h3p',   // Irish/American nerd
    JESSIE: 't0jbNlBVZ17f02VDIeMI',  // Female, old American
    JOSEPH: 'Zlb1dXrM653N07WRdFW3',  // British
    JOSH: 'TxGEqnHWrfWFTfGW9XjX',    // Young American
    LIAM: 'TX3LPaxmHKxFdv7VOQHJ',    // American, young
    LILY: 'pFZP5JQG7iQjIQuC4Bku',    // Female, British
    MATILDA: 'XrExE9yKIg1WjnnlVkGX', // Female, warm American
    MATTHEW: 'Yko7PKHZNXotIFUBG7I9',  // British audiobook
    MICHAEL: 'flq6f7yk4E4fJM5XTYuZ', // American, orator
    MIMI: 'zrHiDhphv9ZnVXBqCLjz',    // Female, childish
    NICOLE: 'piTKgcLEGmPE4e6mEKli',  // Female, whispery
    PATRICK: 'ODq5zmih8GrVes37Dizd',  // Male, video game
    RACHEL: '21m00Tcm4TlvDq8ikWAM',  // Female, American
    SAM: 'yoZ06aMxZJJ28mfd3POQ',     // American, raspy
    SERENA: 'pMsXgVXv3BLzUgSXRplE',  // Female, middle-aged
    THOMAS: 'GBv7mTt0atIp3Br8iCZE',  // American, calm
  };

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.ELEVENLABS_API_KEY || '';
    if (!this.apiKey) {
      throw new Error('ElevenLabs API key is required');
    }
  }

  /**
   * Convert text to speech using ElevenLabs API
   * Using Turbo v2.5 model for 50% cost reduction
   */
  async textToSpeech(request: TextToSpeechRequest): Promise<TextToSpeechResponse> {
    const endpoint = `${this.baseUrl}/text-to-speech/${request.voice_id}`;
    
    // Use Turbo v2.5 model for cost efficiency
    const model_id = request.model_id || 'eleven_turbo_v2_5';
    
    // Default voice settings
    const voice_settings = request.voice_settings || {
      stability: 0.5,
      similarity_boost: 0.75,
      style: 0.5,
      use_speaker_boost: true,
    };

    const payload = {
      text: request.text,
      model_id,
      voice_settings,
      output_format: request.output_format || 'mp3_44100_128',
      optimize_streaming_latency: request.optimize_streaming_latency || 3,
    };

    console.log('Generating audio with ElevenLabs:', {
      voice_id: request.voice_id,
      model: model_id,
      characterCount: request.text.length,
      format: payload.output_format,
    });

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': this.apiKey,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('ElevenLabs API error:', response.status, errorText);
        
        if (response.status === 401) {
          throw new Error('Invalid API key. Please check your ElevenLabs API key.');
        } else if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later.');
        } else if (response.status === 422) {
          throw new Error('Invalid request parameters. Please check voice ID and settings.');
        }
        
        throw new Error(`ElevenLabs API error: ${response.statusText}`);
      }

      // Get audio buffer
      const audioBuffer = await response.buffer();
      
      // Calculate duration (approximate based on text length)
      // This is a rough estimate - actual duration would require audio analysis
      const wordsPerMinute = 150;
      const words = request.text.split(/\s+/).length;
      const duration = Math.ceil((words / wordsPerMinute) * 60);
      
      // Calculate cost using Turbo v2.5 pricing
      // $0.0005 per character (50% cheaper than standard)
      const characterCount = request.text.length;
      const cost = characterCount * 0.0005;
      
      console.log(`ElevenLabs generation cost: $${cost.toFixed(4)} for ${characterCount} characters`);
      
      // Generate temporary filename
      const tempFileName = `elevenlabs_${Date.now()}_${Math.random().toString(36).substring(7)}.mp3`;
      const tempFilePath = path.join(process.cwd(), 'public', 'temp', tempFileName);
      
      // Ensure temp directory exists
      await fs.mkdir(path.dirname(tempFilePath), { recursive: true });
      
      // Save audio file
      await fs.writeFile(tempFilePath, audioBuffer);
      
      // Return public URL
      const audioUrl = `/temp/${tempFileName}`;
      
      return {
        audioUrl,
        duration,
        cost,
        characterCount,
      };
    } catch (error) {
      console.error('ElevenLabs text-to-speech error:', error);
      throw error;
    }
  }

  /**
   * Get list of available voices
   */
  async getVoices(): Promise<VoiceInfo[]> {
    const endpoint = `${this.baseUrl}/voices`;
    
    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'xi-api-key': this.apiKey,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch voices: ${response.statusText}`);
      }

      const data = await response.json() as { voices: VoiceInfo[] };
      return data.voices;
    } catch (error) {
      console.error('Failed to get voices:', error);
      throw error;
    }
  }

  /**
   * Get remaining character quota
   */
  async getQuota(): Promise<{ character_count: number; character_limit: number }> {
    const endpoint = `${this.baseUrl}/user`;
    
    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'xi-api-key': this.apiKey,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch user info: ${response.statusText}`);
      }

      const data = await response.json() as any;
      return {
        character_count: data.subscription.character_count,
        character_limit: data.subscription.character_limit,
      };
    } catch (error) {
      console.error('Failed to get quota:', error);
      throw error;
    }
  }

  /**
   * Helper to select best voice for content
   */
  selectVoiceForContent(_content: string, options?: {
    gender?: 'male' | 'female';
    accent?: 'american' | 'british' | 'australian' | 'irish';
    style?: 'narrator' | 'conversational' | 'news' | 'character';
  }): string {
    // Default to Adam (calm narrator)
    let selectedVoice = ElevenLabsClient.VOICES.ADAM;
    
    if (options) {
      // Gender and accent-based selection
      if (options.gender === 'female') {
        if (options.accent === 'british') {
          selectedVoice = ElevenLabsClient.VOICES.CHARLOTTE;
        } else if (options.style === 'narrator') {
          selectedVoice = ElevenLabsClient.VOICES.RACHEL;
        } else {
          selectedVoice = ElevenLabsClient.VOICES.EMILY;
        }
      } else {
        if (options.accent === 'british') {
          selectedVoice = options.style === 'news' 
            ? ElevenLabsClient.VOICES.DANIEL 
            : ElevenLabsClient.VOICES.CALLUM;
        } else if (options.accent === 'australian') {
          selectedVoice = ElevenLabsClient.VOICES.JAMES;
        }
      }
    }
    
    return selectedVoice;
  }
}

// Singleton instance
let clientInstance: ElevenLabsClient | null = null;

export function getElevenLabsClient(): ElevenLabsClient {
  if (!clientInstance) {
    clientInstance = new ElevenLabsClient();
  }
  return clientInstance;
}

export default ElevenLabsClient;