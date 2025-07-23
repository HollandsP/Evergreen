import React, { useState } from 'react';
import { useVideoGeneration } from '../../lib/hooks/useVideoGeneration';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Card } from '../ui/card';

interface VideoGeneratorExampleProps {
  projectId?: string;
  sceneId?: string;
}

export const VideoGeneratorExample: React.FC<VideoGeneratorExampleProps> = ({
  projectId,
  sceneId,
}) => {
  const [imageUrl, setImageUrl] = useState('');
  const [prompt, setPrompt] = useState('');
  const [duration, setDuration] = useState(5);

  const {
    status,
    progress,
    videoUrl,
    error,
    generateVideo,
    reset,
  } = useVideoGeneration({
    projectId,
    sceneId,
    onProgress: (prog) => console.log('Progress:', prog),
    onComplete: (url) => console.log('Completed! Video URL:', url),
    onError: (err) => console.error('Error:', err),
  });

  const handleGenerate = async () => {
    if (!imageUrl || !prompt) {
      alert('Please provide both image URL and prompt');
      return;
    }

    try {
      await generateVideo({
        imageUrl,
        prompt,
        duration,
        cameraMovement: 'pan_right',
        motionIntensity: 50,
      });
    } catch (error) {
      console.error('Failed to generate video:', error);
    }
  };

  return (
    <Card className="p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">RunwayML Video Generator</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Image URL
          </label>
          <input
            type="text"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://example.com/image.jpg or data:image/jpeg;base64,..."
            className="w-full px-3 py-2 border rounded-md"
            disabled={status === 'processing'}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Video Prompt
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the motion and scene..."
            className="w-full px-3 py-2 border rounded-md h-24"
            disabled={status === 'processing'}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Duration
          </label>
          <select
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-full px-3 py-2 border rounded-md"
            disabled={status === 'processing'}
          >
            <option value={5}>5 seconds</option>
            <option value={10}>10 seconds</option>
          </select>
        </div>

        <div className="flex gap-3">
          <Button
            onClick={handleGenerate}
            disabled={status === 'processing' || !imageUrl || !prompt}
          >
            {status === 'processing' ? 'Generating...' : 'Generate Video'}
          </Button>
          
          {status !== 'idle' && (
            <Button
              onClick={reset}
              variant="outline"
              disabled={status === 'processing'}
            >
              Reset
            </Button>
          )}
        </div>

        {status === 'processing' && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Generating video...</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} />
          </div>
        )}

        {status === 'completed' && videoUrl && (
          <div className="space-y-2">
            <p className="text-green-600 font-medium">Video generated successfully!</p>
            <video
              src={videoUrl}
              controls
              className="w-full rounded-md"
              autoPlay
            />
            <a
              href={videoUrl}
              download
              className="inline-block text-blue-600 hover:underline"
            >
              Download Video
            </a>
          </div>
        )}

        {status === 'failed' && error && (
          <div className="p-4 bg-red-50 text-red-700 rounded-md">
            <p className="font-medium">Generation failed:</p>
            <p>{error}</p>
          </div>
        )}
      </div>

      {projectId && sceneId && (
        <div className="mt-4 p-4 bg-gray-50 rounded-md text-sm">
          <p>Project ID: {projectId}</p>
          <p>Scene ID: {sceneId}</p>
          <p className="mt-2 text-gray-600">
            Videos will be saved to: /exports/{projectId}/{sceneId}/videos/
          </p>
        </div>
      )}
    </Card>
  );
};

export default VideoGeneratorExample;