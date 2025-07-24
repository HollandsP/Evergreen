import React, { useState, useEffect } from 'react';
import { 
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  ArrowPathIcon,
  SparklesIcon,
  ClockIcon,
  TagIcon,
  BookOpenIcon,
  ChevronDownIcon,
  EyeIcon,
  ArrowRightIcon,
  DocumentDuplicateIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { generateOptimizedPrompt } from '@/lib/prompt-optimizer';
import { 
  getTemplatesByCategory, 
  getCategories, 
  searchTemplates, 
  applyTemplate,
  type PromptTemplate 
} from '@/lib/prompt-templates';
import { 
  inheritImagePrompt, 
  inheritVideoPrompt, 
  type PromptInheritanceChain 
} from '@/lib/prompt-inheritance';

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
   * The type of prompt (storyboard, image, video, audio)
   */
  type: 'storyboard' | 'image' | 'video' | 'audio';
  
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
   * Whether to show template library
   */
  showTemplates?: boolean;
  
  /**
   * Whether to show inheritance flow
   */
  showInheritance?: boolean;
  
  /**
   * Inheritance chain for prompt flow
   */
  inheritanceChain?: PromptInheritanceChain;
  
  /**
   * Callback when inheritance is applied
   */
  onInheritanceApply?: (inheritedPrompt: string) => void;
  
  /**
   * Whether to show cost estimation
   */
  showCostEstimation?: boolean;
  
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
  
  /**
   * Whether to enable syntax highlighting for special tags
   */
  enableSyntaxHighlighting?: boolean;
}

const promptTypeInfo = {
  storyboard: {
    label: 'Storyboard Description',
    placeholder: 'Describe the visual composition, characters, and scene elements...',
    maxLength: 500,
    color: 'blue',
    apiCost: 0,
    example: 'A dystopian cityscape at dusk with towering concrete buildings...',
  },
  image: {
    label: 'Image Generation Prompt',
    placeholder: 'Detailed description for DALL-E 3 image generation...',
    maxLength: 4000,
    color: 'green',
    apiCost: 0.04, // DALL-E 3 standard
    example: 'A {scene_description}, cinematic composition, high detail, photorealistic...',
  },
  video: {
    label: 'Video Motion Prompt',
    placeholder: 'Describe camera movement, animation, and motion for RunwayML...',
    maxLength: 800,
    color: 'purple',
    apiCost: 0.05, // RunwayML per second estimate
    example: 'Slow dolly forward: through {scene_action}. {atmosphere_details}...',
  },
  audio: {
    label: 'Voice Synthesis Prompt',
    placeholder: 'Text to be spoken with emotion tags like [excited] or [whispers]...',
    maxLength: 5000,
    color: 'orange',
    apiCost: 0.0005, // ElevenLabs per character
    example: '[{emotion}] {dialogue_text} [{pause_or_effect}]',
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
  showTemplates = true,
  showInheritance = true,
  inheritanceChain,
  onInheritanceApply,
  showCostEstimation = true,
  className,
  placeholder,
  maxLength,
  isInherited = false,
  inheritedFrom,
  enableSyntaxHighlighting = true,
}) => {
  const [internalEditing, setInternalEditing] = useState(false);
  const [editedValue, setEditedValue] = useState(value);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [showTemplateLibrary, setShowTemplateLibrary] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [promptHistory, setPromptHistory] = useState<string[]>([]);
  
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

  // New methods for enhanced functionality
  const handleApplyTemplate = (template: PromptTemplate) => {
    const variables = {
      scene_description: sceneMetadata?.sceneType || 'scene',
      scene_action: 'the action taking place',
      atmosphere_details: 'atmospheric details',
      camera_movement: 'smooth camera movement',
      emotion: 'calm',
      dialogue_text: 'dialogue text',
      pause_or_effect: 'pause'
    };
    
    const { imagePrompt, videoPrompt } = applyTemplate(template, variables);
    const promptToUse = type === 'image' ? imagePrompt : 
                       type === 'video' ? videoPrompt : 
                       template.imagePrompt; // fallback
    
    setEditedValue(promptToUse);
    if (!isEditing) {
      onChange(promptToUse);
    }
    setShowTemplateLibrary(false);
  };

  const handleApplyInheritance = () => {
    if (!inheritanceChain || !onInheritanceApply) return;
    
    try {
      let inheritedPrompt = '';
      
      if (type === 'image' && inheritanceChain.storyboard) {
        inheritedPrompt = inheritImagePrompt(inheritanceChain);
      } else if (type === 'video' && inheritanceChain.storyboard) {
        inheritedPrompt = inheritVideoPrompt(inheritanceChain);
      }
      
      if (inheritedPrompt) {
        setEditedValue(inheritedPrompt);
        onInheritanceApply(inheritedPrompt);
        
        // Add to history
        setPromptHistory(prev => [value, ...prev.slice(0, 4)]);
      }
    } catch (error) {
      console.error('Error applying inheritance:', error);
    }
  };

  const calculateCost = (promptText: string) => {
    if (!showCostEstimation) return null;
    
    const length = promptText.length;
    let cost = 0;
    
    switch (type) {
      case 'image':
        cost = typeInfo.apiCost; // Fixed cost for DALL-E 3
        break;
      case 'video':
        const estimatedDuration = sceneMetadata?.audioDuration || 5;
        cost = typeInfo.apiCost * estimatedDuration;
        break;
      case 'audio':
        cost = typeInfo.apiCost * length; // Per character
        break;
      default:
        return null;
    }
    
    return cost;
  };

  const getTemplates = () => {
    if (searchQuery) {
      return searchTemplates(searchQuery);
    }
    if (selectedCategory) {
      return getTemplatesByCategory(selectedCategory);
    }
    return [];
  };

  const getSyntaxHighlightedText = (text: string) => {
    if (!enableSyntaxHighlighting) return text;
    
    // Highlight special tags based on prompt type
    if (type === 'audio') {
      // Highlight emotion tags like [excited], [whispers]
      return text.replace(/\[([^\]]+)\]/g, '<span class="text-orange-600 font-medium">[$1]</span>');
    } else if (type === 'video') {
      // Highlight camera movements at start
      return text.replace(/^([^:]+:)/, '<span class="text-purple-600 font-medium">$1</span>');
    }
    
    return text;
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
    orange: {
      border: 'border-orange-200 focus:border-orange-500',
      ring: 'focus:ring-orange-500',
      button: 'bg-orange-600 hover:bg-orange-700',
      badge: 'bg-orange-100 text-orange-800',
    },
  };
  
  const colors = colorClasses[typeInfo.color as keyof typeof colorClasses];
  
  return (
    <div className={cn('space-y-4', className)}>
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
              <ArrowRightIcon className="h-3 w-3 mr-1" />
              {inheritedFrom}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Cost estimation */}
          {showCostEstimation && (() => {
            const cost = calculateCost(isEditing ? editedValue : value);
            return cost !== null && cost > 0 ? (
              <span className="inline-flex items-center text-xs text-gray-500">
                <CurrencyDollarIcon className="h-3 w-3 mr-1" />
                ${cost.toFixed(3)}
              </span>
            ) : null;
          })()}
          
          {/* Character count */}
          <span className="text-xs text-gray-500">
            {(isEditing ? editedValue : value).length}/{effectiveMaxLength}
          </span>
          
          {/* Template library button */}
          {showTemplates && (
            <button
              onClick={() => setShowTemplateLibrary(!showTemplateLibrary)}
              className="inline-flex items-center text-xs text-gray-500 hover:text-gray-700"
            >
              <BookOpenIcon className="h-3 w-3 mr-1" />
              Templates
            </button>
          )}
          
          {/* Inheritance button */}
          {showInheritance && inheritanceChain && (
            <button
              onClick={handleApplyInheritance}
              className="inline-flex items-center text-xs text-gray-500 hover:text-gray-700"
            >
              <ArrowPathIcon className="h-3 w-3 mr-1" />
              Inherit
            </button>
          )}
          
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

      {/* Template Library */}
      {showTemplateLibrary && (
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-900">Template Library</h3>
            <button
              onClick={() => setShowTemplateLibrary(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
          
          <div className="flex space-x-2 mb-3">
            <input
              type="text"
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              {getCategories().map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
          
          <div className="max-h-48 overflow-y-auto space-y-2">
            {getTemplates().map(template => (
              <div
                key={template.id}
                className="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                onClick={() => handleApplyTemplate(template)}
              >
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-medium text-gray-900">{template.name}</h4>
                  <span className="text-xs text-gray-500">{template.category}</span>
                </div>
                <p className="text-xs text-gray-600 mb-2">{template.description}</p>
                <div className="flex flex-wrap gap-1">
                  {template.tags.map(tag => (
                    <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
            {getTemplates().length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                No templates found. Try a different search or category.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Inheritance Flow Indicator */}
      {showInheritance && inheritanceChain && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-center space-x-2 text-sm">
            <span className="text-blue-700 font-medium">Inheritance Flow:</span>
            {inheritanceChain.storyboard && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                Storyboard
              </span>
            )}
            {(type === 'image' || type === 'video') && (
              <ArrowRightIcon className="h-3 w-3 text-blue-500" />
            )}
            {(type === 'image' || type === 'video') && (
              <span className={cn(
                'px-2 py-1 rounded text-xs',
                type === 'image' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
              )}>
                Image
              </span>
            )}
            {type === 'video' && (
              <>
                <ArrowRightIcon className="h-3 w-3 text-blue-500" />
                <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                  Video
                </span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Example prompt display */}
      {!value && !isEditing && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
          <div className="flex items-center space-x-2 mb-2">
            <EyeIcon className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-600 font-medium">Example {type} prompt:</span>
          </div>
          <p className="text-sm text-gray-600 italic font-mono">
            {typeInfo.example}
          </p>
        </div>
      )}
      
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
            rows={Math.max(4, Math.ceil(editedValue.length / 80))}
          />
          
          {/* Prompt history */}
          {promptHistory.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">History:</span>
              <div className="flex space-x-1">
                {promptHistory.slice(0, 3).map((historyPrompt, index) => (
                  <button
                    key={index}
                    onClick={() => setEditedValue(historyPrompt)}
                    className="text-xs text-blue-600 hover:text-blue-800 underline"
                    title={historyPrompt.substring(0, 100) + '...'}
                  >
                    v{index + 1}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Edit actions */}
          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              {/* Copy button */}
              <button
                onClick={() => navigator.clipboard.writeText(editedValue)}
                className="inline-flex items-center text-xs text-gray-500 hover:text-gray-700"
              >
                <DocumentDuplicateIcon className="h-3 w-3 mr-1" />
                Copy
              </button>
            </div>
            
            <div className="flex space-x-2">
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
        </div>
      ) : (
        <div
          className={cn(
            'text-sm text-gray-700 bg-gray-50 p-3 rounded-md border min-h-[80px] cursor-pointer',
            'hover:bg-gray-100 transition-colors',
            'relative'
          )}
          onClick={handleEditStart}
        >
          {value ? (
            <div 
              className="whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ 
                __html: enableSyntaxHighlighting ? getSyntaxHighlightedText(value) : value 
              }}
            />
          ) : (
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