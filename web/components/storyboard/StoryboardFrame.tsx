import React, { useState, useRef } from 'react';
import { cn } from '../../lib/utils';
import { Scene } from './StoryboardHeader';
import { 
  PencilIcon, 
  SparklesIcon, 
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  CheckCircleIcon,
  PlusCircleIcon,
  ArrowUpTrayIcon,
} from '@heroicons/react/24/outline';

interface StoryboardFrameProps {
  scene: Scene;
  isSelected?: boolean;
  onClick?: () => void;
  onUpdate?: (updates: Partial<Scene>) => void;
  className?: string;
}

export const StoryboardFrame: React.FC<StoryboardFrameProps> = ({
  scene,
  isSelected = false,
  onClick,
  onUpdate,
  className,
}) => {
  const [_showSketchTool, setShowSketchTool] = useState(false);
  const [_showUpload, _setShowUpload] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSketchClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowSketchTool(true);
    // Would open sketch tool modal/drawer
  };

  const handleGenerateClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Would trigger AI generation
    if (onUpdate) {
      onUpdate({ status: 'generated' });
    }
  };

  const handleUploadClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    fileInputRef.current?.click();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUpdate) {
      // In real implementation, would upload file and get URL
      const mockUrl = URL.createObjectURL(file);
      onUpdate({ 
        imageUrl: mockUrl,
        status: 'generated' 
      });
    }
  };

  const getStatusColor = () => {
    switch (scene.status) {
      case 'sketch': return 'border-blue-500 bg-blue-900/20';
      case 'generated': return 'border-emerald-500 bg-emerald-900/20';
      case 'video-ready': return 'border-purple-500 bg-purple-900/20';
      case 'complete': return 'border-green-500 bg-green-900/20';
      default: return 'border-zinc-700 bg-zinc-800/50';
    }
  };

  const getStatusIcon = () => {
    switch (scene.status) {
      case 'sketch': return <PencilIcon className="h-4 w-4 text-blue-400" />;
      case 'generated': return <PhotoIcon className="h-4 w-4 text-emerald-400" />;
      case 'video-ready': return <VideoCameraIcon className="h-4 w-4 text-purple-400" />;
      case 'complete': return <CheckCircleIcon className="h-4 w-4 text-green-400" />;
      default: return null;
    }
  };

  return (
    <div
      className={cn(
        'flex-shrink-0 cursor-pointer transition-all duration-200',
        'rounded-lg overflow-hidden',
        isSelected ? 'ring-2 ring-emerald-500 ring-offset-2 ring-offset-zinc-900' : '',
        className
      )}
      onClick={onClick}
    >
      <div className={cn(
        'relative w-48 h-72 border-2 rounded-lg overflow-hidden transition-all',
        getStatusColor(),
        isSelected ? 'scale-105' : 'hover:scale-102'
      )}>
        {/* Scene Number Badge */}
        <div className="absolute top-2 left-2 z-10">
          <div className="bg-zinc-900/90 backdrop-blur-sm rounded-full px-2 py-1 border border-zinc-700">
            <span className="text-xs font-semibold text-zinc-100">S{scene.number}</span>
          </div>
        </div>

        {/* Status Icon */}
        {scene.status !== 'empty' && (
          <div className="absolute top-2 right-2 z-10">
            <div className="bg-zinc-900/90 backdrop-blur-sm rounded-full p-1 border border-zinc-700">
              {getStatusIcon()}
            </div>
          </div>
        )}

        {/* Frame Content */}
        <div className="h-48 bg-zinc-900/50 flex items-center justify-center relative overflow-hidden">
          {scene.imageUrl ? (
            <img 
              src={scene.imageUrl} 
              alt={scene.title}
              className="w-full h-full object-cover"
            />
          ) : scene.status === 'empty' ? (
            <div className="flex flex-col items-center space-y-3 p-4">
              <PlusCircleIcon className="h-12 w-12 text-zinc-600" />
              <div className="flex space-x-2">
                <button
                  onClick={handleSketchClick}
                  className="p-2 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
                  title="Sketch"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={handleGenerateClick}
                  className="p-2 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
                  title="AI Generate"
                >
                  <SparklesIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={handleUploadClick}
                  className="p-2 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
                  title="Upload"
                >
                  <ArrowUpTrayIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="p-4 text-center">
              <div className="h-32 flex items-center justify-center">
                {getStatusIcon()}
              </div>
            </div>
          )}

          {/* Video Indicator */}
          {scene.videoUrl && (
            <div className="absolute bottom-2 right-2">
              <VideoCameraIcon className="h-5 w-5 text-purple-400" />
            </div>
          )}

          {/* Audio Indicator */}
          {scene.audioUrl && (
            <div className="absolute bottom-2 left-2">
              <SpeakerWaveIcon className="h-5 w-5 text-blue-400" />
            </div>
          )}
        </div>

        {/* Scene Info */}
        <div className="p-3 bg-zinc-900/80 backdrop-blur-sm">
          <h3 className="font-medium text-sm text-zinc-100 truncate">{scene.title}</h3>
          <p className="text-xs text-zinc-400 truncate mt-1">{scene.description}</p>
          
          {/* Progress Indicators */}
          <div className="flex items-center space-x-2 mt-2">
            <div className={cn(
              'w-2 h-2 rounded-full',
              scene.imageUrl ? 'bg-emerald-500' : 'bg-zinc-700'
            )} title="Image" />
            <div className={cn(
              'w-2 h-2 rounded-full',
              scene.audioUrl ? 'bg-blue-500' : 'bg-zinc-700'
            )} title="Audio" />
            <div className={cn(
              'w-2 h-2 rounded-full',
              scene.videoUrl ? 'bg-purple-500' : 'bg-zinc-700'
            )} title="Video" />
          </div>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileUpload}
        className="hidden"
      />
    </div>
  );
};

export default StoryboardFrame;