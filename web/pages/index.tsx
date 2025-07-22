import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { 
  SparklesIcon, 
  ClockIcon, 
  FilmIcon,
  BoltIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';

// Components
import ImageGeneratorPanel from '@/components/ImageGeneratorPanel';
import WorkflowVisualizer from '@/components/WorkflowVisualizer';
import MediaPreview from '@/components/MediaPreview';
import PipelineControls from '@/components/PipelineControls';

// Types and utilities
import { 
  GenerationJob, 
  GenerationRequest, 
  ProviderConfig, 
  PipelineStep, 
  SystemStatus,
  PipelineSettings
} from '@/types';
import { apiClient } from '@/lib/api';
import { wsManager } from '@/lib/websocket';
import { generateId, cn } from '@/lib/utils';

const DEFAULT_PROVIDERS: ProviderConfig[] = [
  {
    name: 'dalle3',
    displayName: 'DALL-E 3',
    description: 'OpenAI\'s most advanced image generation model',
    cost: { image: 0.040, video: 0.095 },
    capabilities: {
      maxImageSize: '1792x1024',
      maxVideoDuration: 10,
      qualityOptions: ['1024x1024', '1024x1792', '1792x1024']
    },
    available: true
  },
  {
    name: 'flux1',
    displayName: 'Flux.1',
    description: 'High-performance open-source image generation',
    cost: { image: 0.025, video: 0.095 },
    capabilities: {
      maxImageSize: '1024x1024',
      maxVideoDuration: 10,
      qualityOptions: ['512x512', '768x768', '1024x1024']
    },
    available: true
  }
];

const DEFAULT_SYSTEM_STATUS: SystemStatus = {
  dalle3Available: true,
  flux1Available: true,
  runwayAvailable: true,
  activeJobs: 0,
  queueLength: 0,
  systemLoad: 0.2
};

const DEFAULT_SETTINGS: PipelineSettings = {
  imageSize: '1024x1024',
  videoDuration: 10,
  quality: 'high',
  autoDownload: false,
  notifications: true
};

export default function Home() {
  // State management
  const [currentJob, setCurrentJob] = useState<GenerationJob | null>(null);
  const [jobHistory, setJobHistory] = useState<GenerationJob[]>([]);
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [providers, setProviders] = useState<ProviderConfig[]>(DEFAULT_PROVIDERS);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>(DEFAULT_SYSTEM_STATUS);
  const [settings, setSettings] = useState<PipelineSettings>(DEFAULT_SETTINGS);
  const [currentStepId, setCurrentStepId] = useState<string>('');

  // Load initial data
  useEffect(() => {
    loadInitialData();
    setupWebSocketListeners();
    
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('pipelineSettings');
    if (savedSettings) {
      try {
        setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(savedSettings) });
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    }

    return () => {
      // Cleanup WebSocket listeners
      wsManager.disconnect();
    };
  }, []);

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('pipelineSettings', JSON.stringify(settings));
  }, [settings]);

  const loadInitialData = async () => {
    try {
      const [jobsResponse, statusResponse] = await Promise.allSettled([
        apiClient.getJobs(),
        apiClient.getSystemStatus()
      ]);

      if (jobsResponse.status === 'fulfilled') {
        setJobHistory(jobsResponse.value);
        const activeJob = jobsResponse.value.find(job => 
          ['pending', 'generating_image', 'generating_video'].includes(job.status)
        );
        if (activeJob) {
          setCurrentJob(activeJob);
          setIsGenerating(true);
        }
      }

      if (statusResponse.status === 'fulfilled') {
        setSystemStatus(statusResponse.value);
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  };

  const setupWebSocketListeners = () => {
    wsManager.subscribe('job_update', handleJobUpdate);
    wsManager.subscribe('step_update', handleStepUpdate);
    wsManager.subscribe('job_completed', handleJobCompleted);
    wsManager.subscribe('job_failed', handleJobFailed);
    wsManager.subscribe('system_status', handleSystemStatusUpdate);
  };

  const handleJobUpdate = useCallback((data: any) => {
    const updatedJob: GenerationJob = {
      ...data,
      createdAt: new Date(data.createdAt),
      updatedAt: new Date(data.updatedAt)
    };

    setCurrentJob(updatedJob);
    setJobHistory(prev => {
      const filtered = prev.filter(job => job.id !== updatedJob.id);
      return [updatedJob, ...filtered];
    });
  }, []);

  const handleStepUpdate = useCallback((data: any) => {
    const step: PipelineStep = {
      ...data,
      startTime: data.startTime ? new Date(data.startTime) : undefined,
      endTime: data.endTime ? new Date(data.endTime) : undefined
    };

    setPipelineSteps(prev => {
      const filtered = prev.filter(s => s.id !== step.id);
      return [...filtered, step].sort((a, b) => a.id.localeCompare(b.id));
    });

    if (step.status === 'running') {
      setCurrentStepId(step.id);
    }
  }, []);

  const handleJobCompleted = useCallback((data: any) => {
    const completedJob: GenerationJob = {
      ...data,
      createdAt: new Date(data.createdAt),
      updatedAt: new Date(data.updatedAt)
    };

    setCurrentJob(completedJob);
    setIsGenerating(false);
    setCurrentStepId('');

    // Show notification if enabled
    if (settings.notifications && 'Notification' in window) {
      new Notification('Video Generation Complete!', {
        body: 'Your AI-generated video is ready.',
        icon: '/favicon.ico'
      });
    }

    // Auto-download if enabled
    if (settings.autoDownload && completedJob.videoUrl) {
      handleDownload('video');
    }
  }, [settings]);

  const handleJobFailed = useCallback((data: any) => {
    const failedJob: GenerationJob = {
      ...data,
      createdAt: new Date(data.createdAt),
      updatedAt: new Date(data.updatedAt)
    };

    setCurrentJob(failedJob);
    setIsGenerating(false);
    setCurrentStepId('');

    // Show error notification
    if (settings.notifications && 'Notification' in window) {
      new Notification('Generation Failed', {
        body: failedJob.error || 'An error occurred during generation.',
        icon: '/favicon.ico'
      });
    }
  }, [settings]);

  const handleSystemStatusUpdate = useCallback((data: SystemStatus) => {
    setSystemStatus(data);
  }, []);

  const handleGenerate = async (request: GenerationRequest) => {
    try {
      setIsGenerating(true);
      setPipelineSteps([]);
      setCurrentStepId('');

      const job = await apiClient.createGeneration(request);
      setCurrentJob(job);
      
      // Subscribe to job updates
      wsManager.subscribeToJob(job.id);

      // Initialize pipeline steps
      const initialSteps: PipelineStep[] = [
        {
          id: 'image_generation',
          name: 'Image Generation',
          status: 'pending',
          progress: 0
        },
        {
          id: 'video_generation',
          name: 'Video Generation',
          status: 'pending',
          progress: 0
        }
      ];
      setPipelineSteps(initialSteps);

    } catch (error) {
      console.error('Generation failed:', error);
      setIsGenerating(false);
    }
  };

  const handleCancelJob = async () => {
    if (currentJob) {
      try {
        await apiClient.cancelJob(currentJob.id);
        setIsGenerating(false);
        setCurrentJob(null);
        setPipelineSteps([]);
        setCurrentStepId('');
      } catch (error) {
        console.error('Failed to cancel job:', error);
      }
    }
  };

  const handleRetryJob = async () => {
    if (currentJob) {
      const request: GenerationRequest = {
        prompt: currentJob.prompt,
        provider: currentJob.provider,
        settings: {
          imageSize: settings.imageSize,
          videoDuration: settings.videoDuration,
          quality: settings.quality,
          seed: settings.seed
        }
      };
      await handleGenerate(request);
    }
  };

  const handleClearHistory = () => {
    setJobHistory([]);
    if (!isGenerating) {
      setCurrentJob(null);
      setPipelineSteps([]);
      setCurrentStepId('');
    }
  };

  const handleDownload = async (type: 'image' | 'video') => {
    // This would be implemented by the MediaPreview component
    console.log(`Downloading ${type}`);
  };

  const handleSettingsChange = (newSettings: Partial<PipelineSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  // Request notification permission
  useEffect(() => {
    if (settings.notifications && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, [settings.notifications]);

  return (
    <>
      <Head>
        <title>Evergreen AI - Video Generation Pipeline</title>
        <meta name="description" content="Create stunning AI-generated videos from text prompts" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg">
                  <SparklesIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Evergreen AI</h1>
                  <p className="text-sm text-gray-500">Video Generation Pipeline</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="hidden sm:flex items-center space-x-6 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <CpuChipIcon className="h-4 w-4" />
                    <span>System Load: {Math.round(systemStatus.systemLoad * 100)}%</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <ClockIcon className="h-4 w-4" />
                    <span>{systemStatus.activeJobs} Active</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <FilmIcon className="h-4 w-4" />
                    <span>{jobHistory.length} Generated</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Generator & Controls */}
            <div className="lg:col-span-1 space-y-6">
              <ImageGeneratorPanel
                onGenerate={handleGenerate}
                isGenerating={isGenerating}
                providers={providers}
                settings={settings}
                onSettingsChange={handleSettingsChange}
              />
              
              <PipelineControls
                currentJob={currentJob || undefined}
                systemStatus={systemStatus}
                settings={settings}
                onSettingsChange={handleSettingsChange}
                onCancelJob={handleCancelJob}
                onRetryJob={handleRetryJob}
                onClearHistory={handleClearHistory}
              />
            </div>

            {/* Right Column - Preview & Workflow */}
            <div className="lg:col-span-2 space-y-6">
              {/* Active Job Preview */}
              {currentJob && (
                <MediaPreview
                  job={currentJob}
                  onDownload={handleDownload}
                />
              )}

              {/* Workflow Visualizer */}
              {(isGenerating || pipelineSteps.length > 0) && (
                <WorkflowVisualizer
                  steps={pipelineSteps}
                  currentStep={currentStepId}
                />
              )}

              {/* Welcome State */}
              {!currentJob && !isGenerating && (
                <div className="card">
                  <div className="card-body text-center py-16">
                    <div className="mx-auto w-24 h-24 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center mb-6">
                      <BoltIcon className="h-12 w-12 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      Ready to Create Amazing Videos
                    </h2>
                    <p className="text-gray-600 mb-8 max-w-md mx-auto">
                      Transform your ideas into stunning AI-generated videos. Simply describe what you want to see, 
                      and our advanced pipeline will bring it to life.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto text-sm">
                      <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                        <SparklesIcon className="h-8 w-8 text-primary-600 mb-2" />
                        <h3 className="font-medium text-gray-900">AI-Powered</h3>
                        <p className="text-gray-600 text-center">
                          Uses DALL-E 3 and Flux.1 for stunning image generation
                        </p>
                      </div>
                      <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                        <FilmIcon className="h-8 w-8 text-primary-600 mb-2" />
                        <h3 className="font-medium text-gray-900">Video Creation</h3>
                        <p className="text-gray-600 text-center">
                          RunwayML integration for smooth video generation
                        </p>
                      </div>
                      <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                        <BoltIcon className="h-8 w-8 text-primary-600 mb-2" />
                        <h3 className="font-medium text-gray-900">Real-time</h3>
                        <p className="text-gray-600 text-center">
                          Live progress tracking and instant previews
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Recent Generations */}
              {jobHistory.length > 0 && !isGenerating && (
                <div className="card">
                  <div className="card-header">
                    <h3 className="text-lg font-semibold text-gray-900">Recent Generations</h3>
                  </div>
                  <div className="divide-y divide-gray-200">
                    {jobHistory.slice(0, 5).map((job) => (
                      <div key={job.id} className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                           onClick={() => setCurrentJob(job)}>
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {job.prompt}
                            </p>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className={cn('status-badge', `status-${job.status}`)}>
                                {job.status}
                              </span>
                              <span className="text-xs text-gray-500">
                                {job.provider === 'dalle3' ? 'DALL-E 3' : 'Flux.1'}
                              </span>
                              {job.cost && (
                                <span className="text-xs text-gray-500">
                                  ${job.cost.total.toFixed(4)}
                                </span>
                              )}
                            </div>
                          </div>
                          {job.videoUrl && (
                            <div className="ml-4">
                              <FilmIcon className="h-5 w-5 text-primary-600" />
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200 bg-white mt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="text-center">
              <p className="text-sm text-gray-500">
                Powered by DALL-E 3, Flux.1, and RunwayML • Built with Next.js and TypeScript
              </p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}