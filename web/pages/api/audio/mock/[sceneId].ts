import type { NextApiRequest, NextApiResponse } from 'next';

// Mock audio file endpoint for development
// Returns a generated audio file based on scene ID

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { sceneId } = req.query;

  // Generate a simple audio tone for testing
  // In production, this would serve actual generated audio files

  // Create a simple WAV file header
  const sampleRate = 44100;
  const duration = 5; // 5 seconds
  const numSamples = sampleRate * duration;
  const bytesPerSample = 2;
  const numChannels = 1;
  
  // WAV file header
  const header = Buffer.allocUnsafe(44);
  
  // "RIFF" chunk descriptor
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + numSamples * numChannels * bytesPerSample, 4);
  header.write('WAVE', 8);
  
  // "fmt " sub-chunk
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16); // Subchunk1Size
  header.writeUInt16LE(1, 20); // AudioFormat (PCM)
  header.writeUInt16LE(numChannels, 22); // NumChannels
  header.writeUInt32LE(sampleRate, 24); // SampleRate
  header.writeUInt32LE(sampleRate * numChannels * bytesPerSample, 28); // ByteRate
  header.writeUInt16LE(numChannels * bytesPerSample, 32); // BlockAlign
  header.writeUInt16LE(bytesPerSample * 8, 34); // BitsPerSample
  
  // "data" sub-chunk
  header.write('data', 36);
  header.writeUInt32LE(numSamples * numChannels * bytesPerSample, 40);
  
  // Generate audio data (simple sine wave)
  const audioData = Buffer.allocUnsafe(numSamples * numChannels * bytesPerSample);
  const frequency = 440; // A4 note
  const amplitude = 0.3;
  
  for (let i = 0; i < numSamples; i++) {
    const sample = Math.sin(2 * Math.PI * frequency * i / sampleRate) * amplitude * 32767;
    audioData.writeInt16LE(Math.floor(sample), i * bytesPerSample);
  }
  
  // Combine header and data
  const wavFile = Buffer.concat([header, audioData]);
  
  // Set response headers
  res.setHeader('Content-Type', 'audio/wav');
  res.setHeader('Content-Length', wavFile.length);
  res.setHeader('Content-Disposition', `inline; filename="scene-${sceneId}.wav"`);
  
  // Send the audio file
  res.status(200).send(wavFile);
}