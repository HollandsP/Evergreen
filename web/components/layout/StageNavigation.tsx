import React from 'react';
import { useRouter } from 'next/router';
import { 
  DocumentTextIcon,
  SpeakerWaveIcon,
  PhotoIcon,
  VideoCameraIcon,
  FilmIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';

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
  pending: 'border-gray-300 bg-white text-gray-500',
  in_progress: 'border-primary-500 bg-primary-50 text-primary-600',
  completed: 'border-green-500 bg-green-50 text-green-600',
  disabled: 'border-gray-200 bg-gray-50 text-gray-400'
};

const statusTextColors = {
  pending: 'text-gray-500',
  in_progress: 'text-primary-600',
  completed: 'text-green-600',
  disabled: 'text-gray-400'
};

export const StageNavigation: React.FC<StageNavigationProps> = ({
  currentStage,
  stages,
  onStageChange
}) => {
  const router = useRouter();

  const handleStageClick = (stage: Stage) => {
    if (!stage.isAvailable) return;
    
    if (onStageChange) {
      onStageChange(stage.id);
    } else {
      router.push(stage.path);
    }
  };

  return (
    <div className="bg-white border-b border-gray-200">
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
                      ? 'bg-primary-100 text-primary-700 border border-primary-200'
                      : stage.isAvailable
                      ? 'hover:bg-gray-50 text-gray-600 border border-transparent hover:border-gray-200'
                      : 'cursor-not-allowed opacity-50 text-gray-400 border border-transparent'
                  )}
                >
                  <div
                    className={cn(
                      'flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors',
                      statusColors[stage.status]
                    )}
                  >
                    {stage.status === 'completed' ? (
                      <CheckCircleIcon className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  
                  <div className="text-left">
                    <div className={cn('font-medium', isActive ? 'text-primary-700' : '')}>
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
                      className="h-5 w-5 text-gray-300"
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

// Default stages configuration for The Descent production pipeline
export const DEFAULT_PRODUCTION_STAGES: Stage[] = [
  {
    id: 'script',
    name: 'Script Processing',
    description: 'Upload & parse "The Descent" script',
    icon: DocumentTextIcon,
    path: '/production/script',
    status: 'pending',
    isAvailable: true
  },
  {
    id: 'audio',
    name: 'Audio Generation',
    description: 'Generate narration with ElevenLabs',
    icon: SpeakerWaveIcon,
    path: '/production/audio',
    status: 'disabled',
    isAvailable: false
  },
  {
    id: 'images',
    name: 'Image Generation',
    description: 'Create scene images with DALL-E 3',
    icon: PhotoIcon,
    path: '/production/images',
    status: 'disabled',
    isAvailable: false
  },
  {
    id: 'videos',
    name: 'Video Generation',
    description: 'Convert images to video with RunwayML',
    icon: VideoCameraIcon,
    path: '/production/videos',
    status: 'disabled',
    isAvailable: false
  },
  {
    id: 'assembly',
    name: 'Final Assembly',
    description: 'Combine clips into final video',
    icon: FilmIcon,
    path: '/production/assembly',
    status: 'disabled',
    isAvailable: false
  }
];

export default StageNavigation;