import React, { useState } from 'react';
import { cn } from '../../lib/utils';
import StoryboardFrame from './StoryboardFrame';
import { ChevronLeftIcon, ChevronRightIcon, FilmIcon } from '@heroicons/react/24/outline';

export interface Scene {
  id: string;
  number: number;
  title: string;
  description: string;
  prompt?: string;
  imageUrl?: string;
  videoUrl?: string;
  audioUrl?: string;
  status: 'empty' | 'sketch' | 'generated' | 'video-ready' | 'complete';
  selected?: boolean;
}

interface StoryboardHeaderProps {
  scenes: Scene[];
  currentScene?: string;
  onSceneSelect?: (sceneId: string) => void;
  onSceneUpdate?: (sceneId: string, updates: Partial<Scene>) => void;
  className?: string;
}

export const StoryboardHeader: React.FC<StoryboardHeaderProps> = ({
  scenes = [],
  currentScene,
  onSceneSelect,
  onSceneUpdate,
  className,
}) => {
  const [scrollPosition, setScrollPosition] = useState(0);
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);

  const handleScroll = (direction: 'left' | 'right') => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const scrollAmount = 300;
    const newPosition = direction === 'left' 
      ? Math.max(0, scrollPosition - scrollAmount)
      : scrollPosition + scrollAmount;

    container.scrollTo({
      left: newPosition,
      behavior: 'smooth'
    });
    setScrollPosition(newPosition);
  };

  const handleSceneClick = (sceneId: string) => {
    if (onSceneSelect) {
      onSceneSelect(sceneId);
    }
  };

  const handleSceneUpdate = (sceneId: string, updates: Partial<Scene>) => {
    if (onSceneUpdate) {
      onSceneUpdate(sceneId, updates);
    }
  };

  // Mock scenes for development - replace with actual data
  const mockScenes: Scene[] = scenes.length > 0 ? scenes : [
    { id: 's1', number: 1, title: 'Opening', description: 'Cave entrance', status: 'empty' },
    { id: 's2', number: 2, title: 'Descent', description: 'Going deeper', status: 'empty' },
    { id: 's3', number: 3, title: 'Discovery', description: 'Ancient ruins', status: 'empty' },
    { id: 's4', number: 4, title: 'Challenge', description: 'Narrow passage', status: 'empty' },
    { id: 's5', number: 5, title: 'Climax', description: 'Underground lake', status: 'empty' },
    { id: 's6', number: 6, title: 'Resolution', description: 'Finding exit', status: 'empty' },
  ];

  const displayScenes = mockScenes;

  return (
    <div className={cn(
      'bg-zinc-900 border-b border-zinc-800 shadow-lg',
      className
    )}>
      <div className="px-4 py-3">
        {/* Header Title */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <FilmIcon className="h-6 w-6 text-emerald-400" />
            <h2 className="text-lg font-semibold text-zinc-100">Visual Storyboard</h2>
            <span className="text-sm text-zinc-400">
              {displayScenes.length} scenes
            </span>
          </div>
          
          {/* Navigation Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleScroll('left')}
              className="p-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
              aria-label="Scroll left"
            >
              <ChevronLeftIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => handleScroll('right')}
              className="p-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
              aria-label="Scroll right"
            >
              <ChevronRightIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Storyboard Frames */}
        <div className="relative">
          <div 
            ref={scrollContainerRef}
            className="flex space-x-4 overflow-x-auto scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-zinc-800 pb-2"
            style={{ scrollbarWidth: 'thin' }}
          >
            {displayScenes.map((scene) => (
              <StoryboardFrame
                key={scene.id}
                scene={scene}
                isSelected={currentScene === scene.id}
                onClick={() => handleSceneClick(scene.id)}
                onUpdate={(updates) => handleSceneUpdate(scene.id, updates)}
              />
            ))}
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="mt-3 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-4 text-zinc-400">
            <span className="flex items-center">
              <span className="w-2 h-2 bg-zinc-600 rounded-full mr-1"></span>
              Empty
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-1"></span>
              Sketch
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-emerald-500 rounded-full mr-1"></span>
              Generated
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-purple-500 rounded-full mr-1"></span>
              Video Ready
            </span>
          </div>
          
          <div className="text-zinc-400">
            Progress: {Math.round((displayScenes.filter(s => s.status !== 'empty').length / displayScenes.length) * 100)}%
          </div>
        </div>
      </div>
    </div>
  );
};

export default StoryboardHeader;