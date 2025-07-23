import React, { useState, useEffect } from 'react';
import { 
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  ArrowPathIcon,
  SparklesIcon,
  ClockIcon,
  TagIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { generateOptimizedPrompt } from '@/lib/prompt-optimizer';

interface PromptEditorProps {
  /**
   * The current prompt value
   */
  value: string;
  
  /**
   * Callback when prompt value changes
   */
  onChange: (value: string) => void;
  
  /**
   * The type of prompt (storyboard, image, video)
   */
  type: 'storyboard' | 'image' | 'video';
  
  /**
   * Optional scene metadata for prompt optimization
   */
  sceneMetadata?: {
    sceneType?: string;
    audioDuration?: number;
    genre?: string;
    transitionType?: string;
  };
  
  /**
   * Whether editing is currently enabled
   */
  isEditing?: boolean;
  
  /**
   * Callback when edit mode changes
   */
  onEditingChange?: (isEditing: boolean) => void;
  
  /**
   * Whether to show the enhance button
   */
  showEnhance?: boolean;
  
  /**
   * Additional CSS classes
   */
  className?: string;
  
  /**
   * Placeholder text
   */
  placeholder?: string;
  
  /**
   * Maximum number of characters
   */
  maxLength?: number;
  
  /**
   * Whether the prompt is inherited from a previous stage
   */
  isInherited?: boolean;
  
  /**
   * The source of inheritance (e.g., "from storyboard")
   */
  inheritedFrom?: string;
}

const promptTypeInfo = {
  storyboard: {
    label: 'Storyboard Description',
    placeholder: 'Describe the visual composition, characters, and scene elements...',
    maxLength: 500,
    color: 'blue',
  },
  image: {
    label: 'Image Generation Prompt',
    placeholder: 'Detailed description for DALL-E 3 image generation...',
    maxLength: 1000,
    color: 'green',
  },
  video: {
    label: 'Video Motion Prompt',
    placeholder: 'Describe camera movement, animation, and motion for RunwayML...',
    maxLength: 800,
    color: 'purple',
  },
};

export const PromptEditor: React.FC<PromptEditorProps> = ({
  value,
  onChange,
  type,
  sceneMetadata,
  isEditing: controlledEditing,
  onEditingChange,
  showEnhance = true,
  className,
  placeholder,
  maxLength,
  isInherited = false,
  inheritedFrom,
}) => {
  const [internalEditing, setInternalEditing] = useState(false);
  const [editedValue, setEditedValue] = useState(value);
  const [isEnhancing, setIsEnhancing] = useState(false);
  
  const isEditing = controlledEditing !== undefined ? controlledEditing : internalEditing;
  const typeInfo = promptTypeInfo[type];
  const effectiveMaxLength = maxLength || typeInfo.maxLength;
  const effectivePlaceholder = placeholder || typeInfo.placeholder;
  
  useEffect(() => {
    setEditedValue(value);
  }, [value]);
  
  const handleEditStart = () => {
    setEditedValue(value);
    if (onEditingChange) {
      onEditingChange(true);
    } else {
      setInternalEditing(true);
    }
  };
  
  const handleEditSave = () => {
    onChange(editedValue);
    if (onEditingChange) {
      onEditingChange(false);
    } else {
      setInternalEditing(false);
    }
  };
  
  const handleEditCancel = () => {
    setEditedValue(value);
    if (onEditingChange) {
      onEditingChange(false);
    } else {
      setInternalEditing(false);
    }
  };
  
  const handleEnhance = async () => {
    if (!sceneMetadata) return;
    
    setIsEnhancing(true);
    try {
      // Use the existing prompt optimizer
      const enhancedPrompt = generateOptimizedPrompt(value, {
        sceneType: sceneMetadata.sceneType,
        audioDuration: sceneMetadata.audioDuration,
        genre: sceneMetadata.genre,
        transitionType: sceneMetadata.transitionType,
        provider: type === 'image' ? 'dalle3' : undefined,
      });
      
      setEditedValue(enhancedPrompt);
      if (isEditing) {
        // If already editing, just update the edit value
      } else {
        // If not editing, apply immediately
        onChange(enhancedPrompt);
      }
    } catch (error) {
      console.error('Error enhancing prompt:', error);
    } finally {
      setIsEnhancing(false);
    }
  };
  
  const colorClasses = {
    blue: {
      border: 'border-blue-200 focus:border-blue-500',
      ring: 'focus:ring-blue-500',
      button: 'bg-blue-600 hover:bg-blue-700',
      badge: 'bg-blue-100 text-blue-800',
    },
    green: {
      border: 'border-green-200 focus:border-green-500',
      ring: 'focus:ring-green-500',
      button: 'bg-green-600 hover:bg-green-700',
      badge: 'bg-green-100 text-green-800',
    },
    purple: {
      border: 'border-purple-200 focus:border-purple-500',
      ring: 'focus:ring-purple-500',
      button: 'bg-purple-600 hover:bg-purple-700',
      badge: 'bg-purple-100 text-purple-800',
    },
  };
  
  const colors = colorClasses[typeInfo.color as keyof typeof colorClasses];
  
  return (
    <div className={cn('space-y-3', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <label className="block text-sm font-medium text-gray-700">
            {typeInfo.label}
          </label>
          <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', colors.badge)}>
            {type}
          </span>
          {isInherited && inheritedFrom && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
              <ArrowPathIcon className="h-3 w-3 mr-1" />
              {inheritedFrom}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Character count */}
          <span className="text-xs text-gray-500">
            {(isEditing ? editedValue : value).length}/{effectiveMaxLength}
          </span>
          
          {/* Enhance button */}
          {showEnhance && sceneMetadata && (
            <button
              onClick={handleEnhance}
              disabled={isEnhancing}
              className="inline-flex items-center text-xs text-gray-500 hover:text-gray-700 disabled:opacity-50"
            >
              {isEnhancing ? (
                <ArrowPathIcon className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <SparklesIcon className="h-3 w-3 mr-1" />
              )}
              Enhance
            </button>
          )}
          
          {/* Edit button */}
          {!isEditing && (
            <button
              onClick={handleEditStart}
              className="inline-flex items-center text-xs text-gray-500 hover:text-gray-700"
            >
              <PencilIcon className="h-3 w-3 mr-1" />
              Edit
            </button>
          )}
        </div>
      </div>
      
      {/* Content */}
      {isEditing ? (
        <div className="space-y-3">
          <textarea
            value={editedValue}
            onChange={(e) => setEditedValue(e.target.value)}
            placeholder={effectivePlaceholder}
            maxLength={effectiveMaxLength}
            className={cn(
              'w-full text-sm bg-white p-3 rounded-md border resize-none focus:outline-none focus:ring-1',
              colors.border,
              colors.ring,
            )}
            rows={Math.max(3, Math.ceil(editedValue.length / 80))}
          />
          
          {/* Edit actions */}
          <div className="flex justify-end space-x-2">
            <button
              onClick={handleEditCancel}
              className="inline-flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            >
              <XMarkIcon className="h-4 w-4 mr-1" />
              Cancel
            </button>
            <button
              onClick={handleEditSave}
              className={cn(
                'inline-flex items-center px-3 py-1 text-sm text-white rounded-md',
                colors.button,
              )}
            >
              <CheckIcon className="h-4 w-4 mr-1" />
              Save
            </button>
          </div>
        </div>
      ) : (
        <div
          className={cn(
            'text-sm text-gray-700 bg-gray-50 p-3 rounded-md border min-h-[80px] cursor-pointer',
            'hover:bg-gray-100 transition-colors',
          )}
          onClick={handleEditStart}
        >
          {value || (
            <span className="text-gray-400 italic">{effectivePlaceholder}</span>
          )}
        </div>
      )}
      
      {/* Metadata display */}
      {sceneMetadata && (
        <div className="flex flex-wrap gap-2 text-xs">
          {sceneMetadata.sceneType && (
            <span className="inline-flex items-center px-2 py-1 rounded bg-gray-100 text-gray-600">
              <TagIcon className="h-3 w-3 mr-1" />
              {sceneMetadata.sceneType}
            </span>
          )}
          {sceneMetadata.audioDuration && (
            <span className="inline-flex items-center px-2 py-1 rounded bg-gray-100 text-gray-600">
              <ClockIcon className="h-3 w-3 mr-1" />
              {sceneMetadata.audioDuration.toFixed(1)}s
            </span>
          )}
          {sceneMetadata.genre && (
            <span className="inline-flex items-center px-2 py-1 rounded bg-gray-100 text-gray-600">
              {sceneMetadata.genre}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default PromptEditor;