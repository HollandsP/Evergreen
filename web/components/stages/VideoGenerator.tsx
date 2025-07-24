import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Slider } from '../ui/slider';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import { toast } from 'sonner';
import { Play, Video, Wand2, Loader2, Check, Camera, Film, Zap } from 'lucide-react';
import AudioSyncTimeline from '../video/AudioSyncTimeline';
import LipSyncControls from '../video/LipSyncControls';
import { useRouter } from 'next/router';
import PromptEditor from '../shared/PromptEditor';

interface Scene {
  id: string;
  type: string;
  content: string;
  speaker?: string;
  imageUrl?: string;
  audioUrl?: string;
  audioDuration?: number;
  imagePrompt?: string;
  videoPrompt?: string;
  cameraMovement?: string;
  motionIntensity?: number;
  lipSyncEnabled?: boolean;
  videoUrl?: string;
  videoStatus?: 'pending' | 'generating' | 'completed' | 'error';
}

interface VideoGeneratorProps {
  onComplete?: () => void;
  projectId?: string;
}

export default function VideoGenerator({ onComplete, projectId }: VideoGeneratorProps) {
  const router = useRouter();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [selectedScene, setSelectedScene] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [, setIsBatchMode] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Camera movement options based on dalle3_runway_prompts.py
  const cameraMovements = [
    { value: 'static', label: 'Static Shot' },
    { value: 'pan_left', label: 'Pan Left' },
    { value: 'pan_right', label: 'Pan Right' },
    { value: 'zoom_in', label: 'Zoom In' },
    { value: 'zoom_out', label: 'Zoom Out' },
    { value: 'orbit_left', label: 'Orbit Left' },
    { value: 'orbit_right', label: 'Orbit Right' },
    { value: 'dolly_in', label: 'Dolly In' },
    { value: 'dolly_out', label: 'Dolly Out' },
    { value: 'crane_up', label: 'Crane Up' },
    { value: 'crane_down', label: 'Crane Down' },
    { value: 'handheld', label: 'Handheld' },
  ];

  // Load data from localStorage
  useEffect(() => {
    const loadProductionData = () => {
      try {
        // Load script data
        const scriptData = localStorage.getItem('scriptData');
        const parsedScenes = scriptData ? JSON.parse(scriptData) : [];

        // Load audio data
        const audioData = localStorage.getItem('audioData');
        const audioFiles = audioData ? JSON.parse(audioData) : {};

        // Load image data
        const imageData = localStorage.getItem('imageData');
        const images = imageData ? JSON.parse(imageData) : {};

        // Combine all data with prompt inheritance
        const combinedScenes = parsedScenes.map((scene: any) => {
          const imagePrompt = images[scene.id]?.prompt || '';
          const inheritedVideoPrompt = imagePrompt 
            ? `Convert this image to video: ${imagePrompt}. Add subtle motion and cinematic movement.`
            : generateDefaultPrompt(scene);
            
          return {
            ...scene,
            audioUrl: audioFiles[scene.id]?.url,
            audioDuration: audioFiles[scene.id]?.duration || 5,
            imageUrl: images[scene.id]?.url || images[scene.id],
            imagePrompt: imagePrompt,
            videoPrompt: inheritedVideoPrompt,
            cameraMovement: 'static',
            motionIntensity: 50,
            lipSyncEnabled: scene.type === 'dialogue' && scene.speaker,
            videoStatus: 'pending',
          };
        });

        setScenes(combinedScenes);
        if (combinedScenes.length > 0) {
          setSelectedScene(combinedScenes[0].id);
        }
      } catch (error) {
        console.error('Error loading production data:', error);
        toast.error('Failed to load production data');
      }
    };

    loadProductionData();
  }, []);

  // Generate default video prompt based on scene type
  const generateDefaultPrompt = (scene: any): string => {
    if (scene.type === 'dialogue' && scene.speaker) {
      return `${scene.speaker} speaking, natural facial expressions and lip movement, professional lighting`;
    } else if (scene.type === 'narrative') {
      return 'Cinematic scene, atmospheric lighting, subtle movement and atmosphere';
    } else if (scene.type === 'transition') {
      return 'Smooth transitional movement, elegant motion design';
    }
    return 'Cinematic scene with subtle movement';
  };

  // Update scene data
  const updateScene = (sceneId: string, updates: Partial<Scene>) => {
    setScenes(prev => prev.map(scene => 
      scene.id === sceneId ? { ...scene, ...updates } : scene,
    ));
  };

  // Generate video for a single scene
  const generateVideo = async (scene: Scene) => {
    try {
      updateScene(scene.id, { videoStatus: 'generating' });

      const response = await fetch('/api/videos/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          imageUrl: scene.imageUrl,
          prompt: scene.videoPrompt,
          duration: Math.ceil(scene.audioDuration || 5),
          cameraMovement: scene.cameraMovement,
          motionIntensity: scene.motionIntensity,
          lipSync: scene.lipSyncEnabled,
          audioUrl: scene.audioUrl,
          projectId: projectId || JSON.parse(localStorage.getItem('productionState') || '{}').projectId || 'default',
          sceneId: scene.id,
        }),
      });

      if (!response.ok) throw new Error('Failed to generate video');

      const data = await response.json();
      updateScene(scene.id, { 
        videoUrl: data.videoUrl, 
        videoStatus: 'completed', 
      });

      toast.success(`Video generated for scene ${scene.id}`);
      return data.videoUrl;
    } catch (error) {
      console.error('Error generating video:', error);
      updateScene(scene.id, { videoStatus: 'error' });
      toast.error(`Failed to generate video for scene ${scene.id}`);
      throw error;
    }
  };

  // Generate all videos in batch
  const generateAllVideos = async () => {
    setIsGenerating(true);
    setIsBatchMode(true);
    setGenerationProgress(0);

    try {
      const total = scenes.length;
      let completed = 0;

      for (const scene of scenes) {
        if (scene.videoStatus !== 'completed') {
          await generateVideo(scene);
        }
        completed++;
        setGenerationProgress((completed / total) * 100);
      }

      // Save video data to localStorage
      const videoData = scenes.reduce((acc, scene) => {
        if (scene.videoUrl) {
          acc[scene.id] = scene.videoUrl;
        }
        return acc;
      }, {} as Record<string, string>);

      localStorage.setItem('videoData', JSON.stringify(videoData));
      
      // Update production state
      const productionState = JSON.parse(localStorage.getItem('productionState') || '{}');
      productionState.videosGenerated = true;
      localStorage.setItem('productionState', JSON.stringify(productionState));

      toast.success('All videos generated successfully!');
      onComplete?.();
    } catch (error) {
      console.error('Batch generation error:', error);
      toast.error('Some videos failed to generate');
    } finally {
      setIsGenerating(false);
      setIsBatchMode(false);
      setGenerationProgress(0);
    }
  };

  // Generate single video
  const generateSingleVideo = async () => {
    const scene = scenes.find(s => s.id === selectedScene);
    if (!scene) return;

    setIsGenerating(true);
    try {
      await generateVideo(scene);
    } finally {
      setIsGenerating(false);
    }
  };

  // Preview video with audio
  const previewVideo = (scene: Scene) => {
    if (videoRef.current && scene.videoUrl) {
      videoRef.current.src = scene.videoUrl;
      videoRef.current.play();
    }
    if (audioRef.current && scene.audioUrl) {
      audioRef.current.src = scene.audioUrl;
      audioRef.current.play();
    }
  };

  const currentScene = scenes.find(s => s.id === selectedScene);
  const allVideosGenerated = scenes.every(s => s.videoStatus === 'completed');
  const progress = scenes.filter(s => s.videoStatus === 'completed').length / scenes.length * 100;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Film className="w-5 h-5" />
            Video Generation Studio
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Progress Overview */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Overall Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
            <div className="flex gap-2 mt-2">
              {scenes.map(scene => (
                <Badge
                  key={scene.id}
                  variant={scene.videoStatus === 'completed' ? 'default' : 'outline'}
                  className="text-xs"
                >
                  {scene.id}
                </Badge>
              ))}
            </div>
          </div>

          {/* Audio Timeline */}
          <AudioSyncTimeline
            scenes={scenes}
            selectedScene={selectedScene}
            onSceneSelect={setSelectedScene}
          />

          {/* Scene Editor */}
          {currentScene && (
            <Tabs defaultValue="prompt" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="prompt">Video Prompt</TabsTrigger>
                <TabsTrigger value="motion">Motion Settings</TabsTrigger>
                <TabsTrigger value="preview">Preview</TabsTrigger>
              </TabsList>

              <TabsContent value="prompt" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Image Preview */}
                  <div>
                    <Label>Source Image</Label>
                    {currentScene.imageUrl ? (
                      <img 
                        src={currentScene.imageUrl} 
                        alt={`Scene ${currentScene.id}`}
                        className="w-full rounded-lg border mt-2"
                      />
                    ) : (
                      <div className="w-full h-48 bg-muted rounded-lg flex items-center justify-center mt-2">
                        <span className="text-muted-foreground">No image available</span>
                      </div>
                    )}
                  </div>

                  {/* Universal Prompt Editor with Inheritance */}
                  <div className="space-y-4">
                    <PromptEditor
                      value={currentScene.videoPrompt || ''}
                      onChange={(newPrompt) => updateScene(currentScene.id, { videoPrompt: newPrompt })}
                      type="video"
                      sceneMetadata={{
                        sceneType: currentScene.type,
                        audioDuration: currentScene.audioDuration,
                      }}
                      showEnhance={true}
                      isInherited={!!currentScene.imagePrompt}
                      inheritedFrom="from image prompt"
                    />

                    {currentScene.type === 'dialogue' && currentScene.speaker && (
                      <LipSyncControls
                        enabled={currentScene.lipSyncEnabled || false}
                        onToggle={(enabled) => updateScene(currentScene.id, { lipSyncEnabled: enabled })}
                        speaker={currentScene.speaker}
                      />
                    )}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="motion" className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="camera-movement">Camera Movement</Label>
                    <Select
                      value={currentScene.cameraMovement || 'static'}
                      onValueChange={(value) => updateScene(currentScene.id, { cameraMovement: value })}
                    >
                      <SelectTrigger id="camera-movement" className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {cameraMovements.map(movement => (
                          <SelectItem key={movement.value} value={movement.value}>
                            <div className="flex items-center gap-2">
                              <Camera className="w-4 h-4" />
                              {movement.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="motion-intensity">Motion Intensity</Label>
                    <div className="flex items-center gap-4 mt-2">
                      <Slider
                        id="motion-intensity"
                        value={[currentScene.motionIntensity || 50]}
                        onValueChange={([value]) => updateScene(currentScene.id, { motionIntensity: value })}
                        max={100}
                        step={10}
                        className="flex-1"
                      />
                      <span className="text-sm text-muted-foreground w-12">
                        {currentScene.motionIntensity || 50}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-muted/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Scene Details</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Type:</span>
                      <Badge variant="outline" className="ml-2">{currentScene.type}</Badge>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Duration:</span>
                      <span className="ml-2">{currentScene.audioDuration?.toFixed(1)}s</span>
                    </div>
                    {currentScene.speaker && (
                      <div>
                        <span className="text-muted-foreground">Speaker:</span>
                        <span className="ml-2">{currentScene.speaker}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-muted-foreground">Status:</span>
                      <Badge 
                        variant={currentScene.videoStatus === 'completed' ? 'default' : 'secondary'}
                        className="ml-2"
                      >
                        {currentScene.videoStatus}
                      </Badge>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="preview" className="space-y-4">
                {currentScene.videoUrl ? (
                  <div className="space-y-4">
                    <div className="relative rounded-lg overflow-hidden bg-black">
                      <video
                        ref={videoRef}
                        className="w-full"
                        controls
                        src={currentScene.videoUrl}
                      />
                    </div>
                    <audio
                      ref={audioRef}
                      className="hidden"
                      src={currentScene.audioUrl}
                    />
                    <Button
                      onClick={() => previewVideo(currentScene)}
                      className="w-full"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Play with Synchronized Audio
                    </Button>
                  </div>
                ) : (
                  <div className="w-full h-64 bg-muted rounded-lg flex flex-col items-center justify-center">
                    <Video className="w-12 h-12 text-muted-foreground mb-2" />
                    <span className="text-muted-foreground">No video generated yet</span>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          )}

          {/* Generation Controls */}
          <div className="flex gap-4">
            <Button
              onClick={generateSingleVideo}
              disabled={isGenerating || !currentScene || currentScene.videoStatus === 'completed'}
              className="flex-1"
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Wand2 className="w-4 h-4 mr-2" />
              )}
              Generate Current Scene
            </Button>

            <Button
              onClick={generateAllVideos}
              disabled={isGenerating || allVideosGenerated}
              variant="default"
              className="flex-1"
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Zap className="w-4 h-4 mr-2" />
              )}
              Generate All Videos
            </Button>
          </div>

          {/* Generation Progress */}
          {isGenerating && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Generating videos...</span>
                <span>{Math.round(generationProgress)}%</span>
              </div>
              <Progress value={generationProgress} className="h-2" />
            </div>
          )}

          {/* Continue Button */}
          {allVideosGenerated && (
            <Button
              onClick={() => router.push('/production/assembly')}
              className="w-full"
              size="lg"
            >
              <Check className="w-4 h-4 mr-2" />
              Continue to Final Assembly
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
