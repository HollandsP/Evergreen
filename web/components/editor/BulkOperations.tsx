import React, { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Slider } from '../ui/slider';
import { Switch } from '../ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Layers, 
  Copy, 
  Trash2, 
  Move,
  Palette,
  Volume2,
  Timer,
  Zap,
  Film,
  Type,
  Music,
  Image as ImageIcon,
  Sparkles,
  Clock,
  ArrowUpDown,
  Filter,
  Check,
  X,
  AlertCircle,
  Loader2,
  RotateCw,
  Shuffle,
  Grid,
  CheckSquare,
  Square,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

interface Scene {
  id: string;
  name: string;
  duration: number;
  type: 'video' | 'image' | 'audio' | 'text';
  selected?: boolean;
  thumbnail?: string;
  status?: 'ready' | 'processing' | 'error';
}

interface BulkOperation {
  id: string;
  name: string;
  category: string;
  icon: React.ReactNode;
  description: string;
  params: OperationParam[];
  estimatedTime: string;
  impact: 'low' | 'medium' | 'high';
}

interface OperationParam {
  name: string;
  type: 'number' | 'select' | 'boolean' | 'color' | 'text';
  label: string;
  defaultValue: any;
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  step?: number;
}

interface BulkOperationsProps {
  projectId: string;
  scenes: Scene[];
  onApplyOperation: (operation: BulkOperation, selectedScenes: string[], params: any) => void;
  className?: string;
}

export default function BulkOperations({
  projectId,
  scenes = [],
  onApplyOperation,
  className = ''
}: BulkOperationsProps) {
  const [selectedScenes, setSelectedScenes] = useState<Set<string>>(new Set());
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isApplying, setIsApplying] = useState(false);
  const [operationParams, setOperationParams] = useState<Record<string, any>>({});
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['timing', 'visual']));

  const operations: BulkOperation[] = [
    // Timing Operations
    {
      id: 'adjust-duration',
      name: 'Adjust Duration',
      category: 'timing',
      icon: <Clock className="w-4 h-4" />,
      description: 'Change duration of selected scenes',
      params: [
        {
          name: 'duration',
          type: 'number',
          label: 'Duration (seconds)',
          defaultValue: 5,
          min: 0.1,
          max: 60,
          step: 0.1
        },
        {
          name: 'mode',
          type: 'select',
          label: 'Adjustment Mode',
          defaultValue: 'set',
          options: [
            { value: 'set', label: 'Set to' },
            { value: 'add', label: 'Add' },
            { value: 'subtract', label: 'Subtract' },
            { value: 'multiply', label: 'Multiply by' }
          ]
        }
      ],
      estimatedTime: '2s per scene',
      impact: 'medium'
    },
    {
      id: 'speed-ramp',
      name: 'Speed Ramp',
      category: 'timing',
      icon: <Zap className="w-4 h-4" />,
      description: 'Apply speed changes to scenes',
      params: [
        {
          name: 'speed',
          type: 'number',
          label: 'Speed Factor',
          defaultValue: 1.5,
          min: 0.25,
          max: 4,
          step: 0.25
        },
        {
          name: 'smoothing',
          type: 'boolean',
          label: 'Smooth Transitions',
          defaultValue: true
        }
      ],
      estimatedTime: '3s per scene',
      impact: 'high'
    },

    // Visual Operations
    {
      id: 'color-correction',
      name: 'Color Correction',
      category: 'visual',
      icon: <Palette className="w-4 h-4" />,
      description: 'Apply color adjustments to scenes',
      params: [
        {
          name: 'brightness',
          type: 'number',
          label: 'Brightness',
          defaultValue: 0,
          min: -100,
          max: 100,
          step: 5
        },
        {
          name: 'contrast',
          type: 'number',
          label: 'Contrast',
          defaultValue: 0,
          min: -100,
          max: 100,
          step: 5
        },
        {
          name: 'saturation',
          type: 'number',
          label: 'Saturation',
          defaultValue: 0,
          min: -100,
          max: 100,
          step: 5
        },
        {
          name: 'preset',
          type: 'select',
          label: 'Color Preset',
          defaultValue: 'none',
          options: [
            { value: 'none', label: 'None' },
            { value: 'cinematic', label: 'Cinematic' },
            { value: 'vintage', label: 'Vintage' },
            { value: 'noir', label: 'Black & White' }
          ]
        }
      ],
      estimatedTime: '4s per scene',
      impact: 'medium'
    },
    {
      id: 'add-filter',
      name: 'Add Filter',
      category: 'visual',
      icon: <Filter className="w-4 h-4" />,
      description: 'Apply visual filters to scenes',
      params: [
        {
          name: 'filter',
          type: 'select',
          label: 'Filter Type',
          defaultValue: 'blur',
          options: [
            { value: 'blur', label: 'Blur' },
            { value: 'sharpen', label: 'Sharpen' },
            { value: 'vignette', label: 'Vignette' },
            { value: 'grain', label: 'Film Grain' }
          ]
        },
        {
          name: 'intensity',
          type: 'number',
          label: 'Intensity',
          defaultValue: 50,
          min: 0,
          max: 100,
          step: 10
        }
      ],
      estimatedTime: '3s per scene',
      impact: 'medium'
    },

    // Audio Operations
    {
      id: 'normalize-audio',
      name: 'Normalize Audio',
      category: 'audio',
      icon: <Volume2 className="w-4 h-4" />,
      description: 'Balance audio levels across scenes',
      params: [
        {
          name: 'targetLevel',
          type: 'number',
          label: 'Target Level (dB)',
          defaultValue: -14,
          min: -30,
          max: 0,
          step: 1
        },
        {
          name: 'preservePeaks',
          type: 'boolean',
          label: 'Preserve Peaks',
          defaultValue: true
        }
      ],
      estimatedTime: '2s per scene',
      impact: 'low'
    },
    {
      id: 'add-music',
      name: 'Add Background Music',
      category: 'audio',
      icon: <Music className="w-4 h-4" />,
      description: 'Add music track to scenes',
      params: [
        {
          name: 'musicStyle',
          type: 'select',
          label: 'Music Style',
          defaultValue: 'ambient',
          options: [
            { value: 'ambient', label: 'Ambient' },
            { value: 'upbeat', label: 'Upbeat' },
            { value: 'dramatic', label: 'Dramatic' },
            { value: 'corporate', label: 'Corporate' }
          ]
        },
        {
          name: 'volume',
          type: 'number',
          label: 'Volume Level',
          defaultValue: 30,
          min: 0,
          max: 100,
          step: 10
        },
        {
          name: 'fadeIn',
          type: 'boolean',
          label: 'Fade In/Out',
          defaultValue: true
        }
      ],
      estimatedTime: '3s per scene',
      impact: 'medium'
    },

    // Transition Operations
    {
      id: 'add-transitions',
      name: 'Add Transitions',
      category: 'transitions',
      icon: <Film className="w-4 h-4" />,
      description: 'Add transitions between scenes',
      params: [
        {
          name: 'type',
          type: 'select',
          label: 'Transition Type',
          defaultValue: 'crossfade',
          options: [
            { value: 'crossfade', label: 'Crossfade' },
            { value: 'dip-to-black', label: 'Dip to Black' },
            { value: 'slide', label: 'Slide' },
            { value: 'wipe', label: 'Wipe' }
          ]
        },
        {
          name: 'duration',
          type: 'number',
          label: 'Duration (seconds)',
          defaultValue: 0.5,
          min: 0.1,
          max: 2,
          step: 0.1
        }
      ],
      estimatedTime: '2s per transition',
      impact: 'low'
    },

    // Text Operations
    {
      id: 'add-captions',
      name: 'Add Captions',
      category: 'text',
      icon: <Type className="w-4 h-4" />,
      description: 'Add text captions to scenes',
      params: [
        {
          name: 'style',
          type: 'select',
          label: 'Caption Style',
          defaultValue: 'subtitle',
          options: [
            { value: 'subtitle', label: 'Subtitle' },
            { value: 'title', label: 'Title' },
            { value: 'lower-third', label: 'Lower Third' },
            { value: 'animated', label: 'Animated' }
          ]
        },
        {
          name: 'position',
          type: 'select',
          label: 'Position',
          defaultValue: 'bottom',
          options: [
            { value: 'top', label: 'Top' },
            { value: 'center', label: 'Center' },
            { value: 'bottom', label: 'Bottom' }
          ]
        },
        {
          name: 'autoGenerate',
          type: 'boolean',
          label: 'Auto-generate from audio',
          defaultValue: true
        }
      ],
      estimatedTime: '5s per scene',
      impact: 'medium'
    },

    // Organization Operations
    {
      id: 'reorder-scenes',
      name: 'Reorder Scenes',
      category: 'organization',
      icon: <ArrowUpDown className="w-4 h-4" />,
      description: 'Reorder selected scenes',
      params: [
        {
          name: 'order',
          type: 'select',
          label: 'Order By',
          defaultValue: 'duration',
          options: [
            { value: 'duration', label: 'Duration' },
            { value: 'name', label: 'Name' },
            { value: 'type', label: 'Type' },
            { value: 'random', label: 'Random' }
          ]
        },
        {
          name: 'direction',
          type: 'select',
          label: 'Direction',
          defaultValue: 'asc',
          options: [
            { value: 'asc', label: 'Ascending' },
            { value: 'desc', label: 'Descending' }
          ]
        }
      ],
      estimatedTime: '1s',
      impact: 'low'
    }
  ];

  const categories = [
    { id: 'all', label: 'All', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'timing', label: 'Timing', icon: <Clock className="w-4 h-4" /> },
    { id: 'visual', label: 'Visual', icon: <Palette className="w-4 h-4" /> },
    { id: 'audio', label: 'Audio', icon: <Volume2 className="w-4 h-4" /> },
    { id: 'transitions', label: 'Transitions', icon: <Film className="w-4 h-4" /> },
    { id: 'text', label: 'Text', icon: <Type className="w-4 h-4" /> },
    { id: 'organization', label: 'Organize', icon: <Layers className="w-4 h-4" /> }
  ];

  const toggleSceneSelection = useCallback((sceneId: string) => {
    setSelectedScenes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sceneId)) {
        newSet.delete(sceneId);
      } else {
        newSet.add(sceneId);
      }
      return newSet;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedScenes(new Set(scenes.map(s => s.id)));
  }, [scenes]);

  const selectNone = useCallback(() => {
    setSelectedScenes(new Set());
  }, []);

  const toggleCategory = useCallback((categoryId: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  }, []);

  const handleApplyOperation = useCallback(async (operation: BulkOperation) => {
    if (selectedScenes.size === 0) {
      alert('Please select at least one scene');
      return;
    }

    setIsApplying(true);
    
    try {
      // Get params for this operation
      const params = operation.params.reduce((acc, param) => {
        acc[param.name] = operationParams[`${operation.id}-${param.name}`] ?? param.defaultValue;
        return acc;
      }, {} as Record<string, any>);

      await onApplyOperation(
        operation,
        Array.from(selectedScenes),
        params
      );

      // Clear selection after successful operation
      setSelectedScenes(new Set());
    } catch (error) {
      console.error('Bulk operation failed:', error);
    } finally {
      setIsApplying(false);
    }
  }, [selectedScenes, operationParams, onApplyOperation]);

  const filteredOperations = useMemo(() => {
    if (selectedCategory === 'all') return operations;
    return operations.filter(op => op.category === selectedCategory);
  }, [selectedCategory]);

  const groupedOperations = useMemo(() => {
    return filteredOperations.reduce((acc, op) => {
      if (!acc[op.category]) {
        acc[op.category] = [];
      }
      acc[op.category].push(op);
      return acc;
    }, {} as Record<string, BulkOperation[]>);
  }, [filteredOperations]);

  const getSceneIcon = (type: string) => {
    switch (type) {
      case 'video': return <Film className="w-3 h-3" />;
      case 'image': return <ImageIcon className="w-3 h-3" />;
      case 'audio': return <Music className="w-3 h-3" />;
      case 'text': return <Type className="w-3 h-3" />;
      default: return <Layers className="w-3 h-3" />;
    }
  };

  return (
    <Card className={`bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-purple-500" />
            Bulk Operations
          </CardTitle>
          <Badge variant="secondary">
            {selectedScenes.size} of {scenes.length} selected
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Scene Selection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Select Scenes</Label>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={selectAll}>
                <CheckSquare className="w-4 h-4 mr-1" />
                All
              </Button>
              <Button size="sm" variant="outline" onClick={selectNone}>
                <Square className="w-4 h-4 mr-1" />
                None
              </Button>
            </div>
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 bg-zinc-800 rounded-lg">
            {scenes.map(scene => (
              <button
                key={scene.id}
                onClick={() => toggleSceneSelection(scene.id)}
                className={`p-2 rounded border text-left transition-all ${
                  selectedScenes.has(scene.id)
                    ? 'bg-blue-600/20 border-blue-600 text-blue-400'
                    : 'bg-zinc-700 border-zinc-600 hover:border-zinc-500'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    {selectedScenes.has(scene.id) ? (
                      <CheckSquare className="w-4 h-4" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                    {getSceneIcon(scene.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{scene.name}</p>
                    <p className="text-xs text-zinc-500">{scene.duration}s</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Category Filter */}
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
          <TabsList className="grid grid-cols-4 lg:grid-cols-7">
            {categories.map(cat => (
              <TabsTrigger
                key={cat.id}
                value={cat.id}
                className="flex items-center gap-1 text-xs"
              >
                {cat.icon}
                <span className="hidden lg:inline">{cat.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {/* Operations */}
        <div className="space-y-4">
          {Object.entries(groupedOperations).map(([category, ops]) => (
            <div key={category} className="border border-zinc-700 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleCategory(category)}
                className="w-full p-3 bg-zinc-800 hover:bg-zinc-700 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  {expandedCategories.has(category) ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                  <span className="font-medium capitalize">{category}</span>
                  <Badge variant="secondary" className="text-xs">
                    {ops.length}
                  </Badge>
                </div>
              </button>
              
              {expandedCategories.has(category) && (
                <div className="p-3 space-y-3">
                  {ops.map(operation => (
                    <div
                      key={operation.id}
                      className="p-4 bg-zinc-800 rounded-lg border border-zinc-700"
                    >
                      <div className="flex items-start gap-3 mb-3">
                        <div className="p-2 rounded bg-zinc-700">
                          {operation.icon}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-white">{operation.name}</h4>
                          <p className="text-sm text-zinc-400">{operation.description}</p>
                        </div>
                      </div>

                      {/* Operation Parameters */}
                      <div className="space-y-3 mb-4">
                        {operation.params.map(param => (
                          <div key={param.name}>
                            <Label className="text-xs">{param.label}</Label>
                            {param.type === 'number' && (
                              <div className="flex items-center gap-3">
                                <Slider
                                  value={[operationParams[`${operation.id}-${param.name}`] ?? param.defaultValue]}
                                  onValueChange={([value]) => 
                                    setOperationParams(prev => ({
                                      ...prev,
                                      [`${operation.id}-${param.name}`]: value
                                    }))
                                  }
                                  min={param.min}
                                  max={param.max}
                                  step={param.step}
                                  className="flex-1"
                                />
                                <span className="text-sm w-12 text-right">
                                  {operationParams[`${operation.id}-${param.name}`] ?? param.defaultValue}
                                </span>
                              </div>
                            )}
                            {param.type === 'select' && (
                              <Select
                                value={operationParams[`${operation.id}-${param.name}`] ?? param.defaultValue}
                                onValueChange={(value) => 
                                  setOperationParams(prev => ({
                                    ...prev,
                                    [`${operation.id}-${param.name}`]: value
                                  }))
                                }
                              >
                                <SelectTrigger className="w-full">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {param.options?.map(option => (
                                    <SelectItem key={option.value} value={option.value}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            )}
                            {param.type === 'boolean' && (
                              <Switch
                                checked={operationParams[`${operation.id}-${param.name}`] ?? param.defaultValue}
                                onCheckedChange={(checked) => 
                                  setOperationParams(prev => ({
                                    ...prev,
                                    [`${operation.id}-${param.name}`]: checked
                                  }))
                                }
                              />
                            )}
                          </div>
                        ))}
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 text-xs text-zinc-500">
                          <span className="flex items-center gap-1">
                            <Timer className="w-3 h-3" />
                            {operation.estimatedTime}
                          </span>
                          <span className={`flex items-center gap-1 ${
                            operation.impact === 'high' ? 'text-red-500' :
                            operation.impact === 'medium' ? 'text-yellow-500' :
                            'text-green-500'
                          }`}>
                            <Zap className="w-3 h-3" />
                            {operation.impact} impact
                          </span>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleApplyOperation(operation)}
                          disabled={isApplying || selectedScenes.size === 0}
                        >
                          {isApplying ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Applying...
                            </>
                          ) : (
                            <>
                              Apply to {selectedScenes.size} scenes
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Warning */}
        {selectedScenes.size > 10 && (
          <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5" />
            <p className="text-xs text-yellow-400">
              Bulk operations on {selectedScenes.size} scenes may take some time. The operation will run in the background.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}