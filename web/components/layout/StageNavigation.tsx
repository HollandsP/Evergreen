import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { 
  DocumentTextIcon,
  SpeakerWaveIcon,
  PhotoIcon,
  VideoCameraIcon,
  FilmIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import { productionState, getProductionState } from '../../lib/production-state';

export interface Stage {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  path: string;
  status: 'pending' | 'in_progress' | 'completed' | 'disabled';
  isAvailable: boolean;
}

interface StageNavigationProps {
  currentStage: string;
  stages: Stage[];
  onStageChange?: (stageId: string) => void;
}

const statusColors = {
  pending: 'border-zinc-700 bg-zinc-800 text-zinc-300',
  in_progress: 'border-emerald-500 bg-emerald-900/20 text-emerald-400',
  completed: 'border-green-500 bg-green-900/20 text-green-400',
  disabled: 'border-zinc-700 bg-zinc-900 text-zinc-600',
};

const statusTextColors = {
  pending: 'text-zinc-400',
  in_progress: 'text-emerald-400',
  completed: 'text-green-400',
  disabled: 'text-zinc-600',
};

export const StageNavigation: React.FC<StageNavigationProps> = ({
  currentStage,
  stages: propStages,
  onStageChange,
}) => {
  const router = useRouter();
  const [stages, setStages] = useState<Stage[]>(propStages);

  useEffect(() => {
    // Update stages based on production state
    const updateStagesFromState = () => {
      const state = getProductionState();
      const updatedStages = propStages.map((stage) => {
        // Determine status based on production state
        let status: Stage['status'] = 'pending';
        let isAvailable = true;

        switch (stage.id) {
          case 'script':
            status = state.script.status === 'completed' ? 'completed' : 
                    state.script.status === 'error' ? 'pending' : 
                    state.script.status === 'idle' ? 'pending' : 'in_progress';
            break;
          case 'audio':
            isAvailable = state.script.status === 'completed';
            status = !isAvailable ? 'disabled' :
                    state.audio.status === 'completed' ? 'completed' :
                    state.audio.status === 'error' ? 'pending' :
                    state.audio.status === 'idle' ? 'pending' : 'in_progress';
            break;
          case 'images':
            isAvailable = state.script.status === 'completed';
            status = !isAvailable ? 'disabled' :
                    state.images.status === 'completed' ? 'completed' :
                    state.images.status === 'error' ? 'pending' :
                    state.images.status === 'idle' ? 'pending' : 'in_progress';
            break;
          case 'videos':
            isAvailable = state.script.status === 'completed' && state.images.generatedImages.length > 0;
            status = !isAvailable ? 'disabled' :
                    state.video.status === 'completed' ? 'completed' :
                    state.video.status === 'error' ? 'pending' :
                    state.video.status === 'idle' ? 'pending' : 'in_progress';
            break;
          case 'assembly':
            isAvailable = state.script.status === 'completed' && 
                         state.audio.generatedAudio.length > 0 &&
                         state.video.scenes.filter(s => s.status === 'completed').length > 0;
            status = !isAvailable ? 'disabled' :
                    state.assembly.status === 'completed' ? 'completed' :
                    state.assembly.status === 'error' ? 'pending' :
                    state.assembly.status === 'idle' ? 'pending' : 'in_progress';
            break;
        }

        // Mark current stage as in_progress
        if (stage.id === currentStage && status !== 'completed' && status !== 'disabled') {
          status = 'in_progress';
        }

        return {
          ...stage,
          status,
          isAvailable,
        };
      });

      setStages(updatedStages);
    };

    updateStagesFromState();

    // Subscribe to production state updates
    const handleStateUpdate = () => {
      updateStagesFromState();
    };

    productionState.on('stateUpdate', handleStateUpdate);
    productionState.on('stageChange', handleStateUpdate);

    return () => {
      productionState.off('stateUpdate', handleStateUpdate);
      productionState.off('stageChange', handleStateUpdate);
    };
  }, [propStages, currentStage]);

  const handleStageClick = (stage: Stage) => {
    if (!stage.isAvailable) return;
    
    if (onStageChange) {
      onStageChange(stage.id);
    } else {
      router.push(stage.path);
    }
  };

  return (
    <div className="bg-zinc-900 border-b border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex space-x-8 overflow-x-auto py-4" aria-label="Production Stages">
          {stages.map((stage, index) => {
            const isActive = currentStage === stage.id;
            const Icon = stage.icon;
            
            return (
              <div key={stage.id} className="flex items-center space-x-4 flex-shrink-0">
                <button
                  onClick={() => handleStageClick(stage)}
                  disabled={!stage.isAvailable}
                  className={cn(
                    'group flex items-center space-x-3 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-600/50'
                      : stage.isAvailable
                        ? 'hover:bg-zinc-800 text-zinc-300 border border-transparent hover:border-zinc-700'
                        : 'cursor-not-allowed opacity-50 text-zinc-600 border border-transparent',
                  )}
                >
                  <div
                    className={cn(
                      'flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors',
                      statusColors[stage.status],
                    )}
                  >
                    {stage.status === 'completed' ? (
                      <CheckCircleIcon className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  
                  <div className="text-left">
                    <div className={cn('font-medium', isActive ? 'text-emerald-400' : '')}>
                      Stage {index + 1}: {stage.name}
                    </div>
                    <div className={cn('text-xs', statusTextColors[stage.status])}>
                      {stage.description}
                    </div>
                  </div>
                </button>
                
                {index < stages.length - 1 && (
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-zinc-600"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>
    </div>
  );
};

// Default stages configuration for production pipeline
export const DEFAULT_PRODUCTION_STAGES: Stage[] = [
  {
    id: 'script',
    name: 'Script Processing',
    description: 'Upload & parse your script',
    icon: DocumentTextIcon,
    path: '/production/script',
    status: 'pending',
    isAvailable: true,
  },
  {
    id: 'audio',
    name: 'Audio Generation',
    description: 'Generate narration with ElevenLabs',
    icon: SpeakerWaveIcon,
    path: '/production/audio',
    status: 'pending',
    isAvailable: true, // Will be updated based on state
  },
  {
    id: 'images',
    name: 'Image Generation',
    description: 'Create scene images with DALL-E 3',
    icon: PhotoIcon,
    path: '/production/images',
    status: 'pending',
    isAvailable: true, // Will be updated based on state
  },
  {
    id: 'videos',
    name: 'Video Generation',
    description: 'Convert images to video with RunwayML',
    icon: VideoCameraIcon,
    path: '/production/videos',
    status: 'pending',
    isAvailable: true, // Will be updated based on state
  },
  {
    id: 'assembly',
    name: 'Final Assembly',
    description: 'Combine clips into final video',
    icon: FilmIcon,
    path: '/production/assembly',
    status: 'pending',
    isAvailable: true, // Will be updated based on state
  },
];

export default StageNavigation;
