import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { 
  Wand2,
  Search,
  Save,
  Upload,
  Download,
  Trash2,
  Edit,
  Copy,
  PlayCircle,
  Star,
  StarOff,
  Clock,
  Zap,
  Film,
  Music,
  Type,
  Sparkles,
  TrendingUp,
  Youtube,
  Instagram,
  Twitter,
  ChevronRight,
  Folder,
  Plus,
  Settings,
  Info
} from 'lucide-react';

interface OperationStep {
  id: string;
  type: string;
  name: string;
  parameters: Record<string, any>;
  optional?: boolean;
}

interface OperationTemplate {
  id: string;
  name: string;
  description: string;
  category: 'youtube' | 'social' | 'effects' | 'audio' | 'color' | 'custom';
  icon?: React.ReactNode;
  duration?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  tags?: string[];
  steps: OperationStep[];
  thumbnail?: string;
  isFavorite?: boolean;
  usageCount?: number;
  lastUsed?: Date;
}

interface OperationTemplatesProps {
  projectId?: string;
  onApplyTemplate?: (template: OperationTemplate) => void;
  onSaveTemplate?: (template: OperationTemplate) => void;
  className?: string;
}

// Predefined professional templates
const DEFAULT_TEMPLATES: OperationTemplate[] = [
  // YouTube Templates
  {
    id: 'yt-intro',
    name: 'YouTube Intro',
    description: 'Professional 5-second intro with logo reveal and sound',
    category: 'youtube',
    icon: <Youtube className="w-4 h-4" />,
    duration: '5s',
    difficulty: 'easy',
    tags: ['intro', 'branding', 'logo'],
    steps: [
      {
        id: '1',
        type: 'OVERLAY',
        name: 'Add logo',
        parameters: { duration: 5, position: 'center', animation: 'fade-scale' }
      },
      {
        id: '2',
        type: 'AUDIO_MIX',
        name: 'Add intro sound',
        parameters: { volume: 0.8, fadeIn: 0.5 }
      },
      {
        id: '3',
        type: 'EFFECT',
        name: 'Add glow effect',
        parameters: { type: 'glow', intensity: 0.6 }
      }
    ]
  },
  {
    id: 'yt-outro',
    name: 'YouTube Outro',
    description: 'End screen with subscribe button and video recommendations',
    category: 'youtube',
    icon: <Youtube className="w-4 h-4" />,
    duration: '20s',
    difficulty: 'medium',
    tags: ['outro', 'endscreen', 'cta'],
    steps: [
      {
        id: '1',
        type: 'TRANSITION',
        name: 'Fade to end screen',
        parameters: { type: 'fade', duration: 1 }
      },
      {
        id: '2',
        type: 'OVERLAY',
        name: 'Add subscribe button',
        parameters: { type: 'subscribe', position: 'bottom-center', animation: 'bounce' }
      },
      {
        id: '3',
        type: 'OVERLAY',
        name: 'Add video cards',
        parameters: { type: 'cards', count: 2, position: 'sides' }
      },
      {
        id: '4',
        type: 'AUDIO_MIX',
        name: 'Background music fade',
        parameters: { fadeOut: 3, targetVolume: 0.3 }
      }
    ]
  },
  {
    id: 'yt-chapter',
    name: 'Chapter Markers',
    description: 'Add chapter transitions with titles for long-form content',
    category: 'youtube',
    icon: <Youtube className="w-4 h-4" />,
    duration: '3s',
    difficulty: 'easy',
    tags: ['chapters', 'navigation', 'longform'],
    steps: [
      {
        id: '1',
        type: 'TRANSITION',
        name: 'Chapter transition',
        parameters: { type: 'wipe', duration: 0.5 }
      },
      {
        id: '2',
        type: 'OVERLAY',
        name: 'Chapter title',
        parameters: { duration: 3, position: 'lower-third', animation: 'slide' }
      },
      {
        id: '3',
        type: 'EFFECT',
        name: 'Blur background',
        parameters: { type: 'blur', intensity: 0.8, duration: 1 }
      }
    ]
  },

  // Social Media Templates
  {
    id: 'ig-reel',
    name: 'Instagram Reel',
    description: 'Vertical format with trendy transitions and text overlays',
    category: 'social',
    icon: <Instagram className="w-4 h-4" />,
    duration: '15-30s',
    difficulty: 'medium',
    tags: ['instagram', 'reel', 'vertical', 'trending'],
    steps: [
      {
        id: '1',
        type: 'EFFECT',
        name: 'Aspect ratio crop',
        parameters: { ratio: '9:16', position: 'center' }
      },
      {
        id: '2',
        type: 'SPEED',
        name: 'Speed ramp',
        parameters: { keyframes: [
          { time: 0, speed: 1 },
          { time: 0.5, speed: 2 },
          { time: 1, speed: 1 }
        ]}
      },
      {
        id: '3',
        type: 'OVERLAY',
        name: 'Trendy text',
        parameters: { style: 'modern', animation: 'typewriter', position: 'center' }
      },
      {
        id: '4',
        type: 'TRANSITION',
        name: 'Quick cuts',
        parameters: { type: 'glitch', duration: 0.1 }
      }
    ]
  },
  {
    id: 'tiktok-trend',
    name: 'TikTok Trend',
    description: 'Popular TikTok style with beat sync and effects',
    category: 'social',
    icon: <Music className="w-4 h-4" />,
    duration: '15-60s',
    difficulty: 'hard',
    tags: ['tiktok', 'viral', 'trending', 'music'],
    steps: [
      {
        id: '1',
        type: 'AUDIO_MIX',
        name: 'Beat detection',
        parameters: { detectBeats: true, sensitivity: 0.8 }
      },
      {
        id: '2',
        type: 'EFFECT',
        name: 'Beat sync zoom',
        parameters: { type: 'zoom-pulse', syncToAudio: true }
      },
      {
        id: '3',
        type: 'OVERLAY',
        name: 'Captions',
        parameters: { type: 'auto-captions', style: 'bold', highlight: true }
      },
      {
        id: '4',
        type: 'EFFECT',
        name: 'Color grade',
        parameters: { preset: 'vibrant', intensity: 0.7 }
      }
    ]
  },
  {
    id: 'twitter-video',
    name: 'Twitter Video',
    description: 'Short, impactful video optimized for Twitter',
    category: 'social',
    icon: <Twitter className="w-4 h-4" />,
    duration: '140s max',
    difficulty: 'easy',
    tags: ['twitter', 'short', 'news'],
    steps: [
      {
        id: '1',
        type: 'OVERLAY',
        name: 'Add captions',
        parameters: { type: 'captions', position: 'bottom', size: 'large' }
      },
      {
        id: '2',
        type: 'EFFECT',
        name: 'Optimize for mobile',
        parameters: { cropSafe: true, enhanceText: true }
      },
      {
        id: '3',
        type: 'AUDIO_MIX',
        name: 'Normalize audio',
        parameters: { normalize: true, targetLUFS: -16 }
      }
    ]
  },

  // Effect Templates
  {
    id: 'cinematic-look',
    name: 'Cinematic Look',
    description: 'Professional film look with letterbox and color grade',
    category: 'effects',
    icon: <Film className="w-4 h-4" />,
    duration: 'Full video',
    difficulty: 'medium',
    tags: ['cinematic', 'film', 'professional'],
    steps: [
      {
        id: '1',
        type: 'EFFECT',
        name: 'Letterbox bars',
        parameters: { ratio: '2.35:1', opacity: 1 }
      },
      {
        id: '2',
        type: 'EFFECT',
        name: 'Film grain',
        parameters: { type: 'grain', intensity: 0.3, size: 'fine' }
      },
      {
        id: '3',
        type: 'EFFECT',
        name: 'Color grade',
        parameters: { 
          preset: 'cinematic',
          shadows: { r: -5, g: -5, b: 0 },
          highlights: { r: 5, g: 3, b: 0 }
        }
      },
      {
        id: '4',
        type: 'EFFECT',
        name: 'Vignette',
        parameters: { intensity: 0.4, feather: 0.8 }
      }
    ]
  },
  {
    id: 'glitch-effect',
    name: 'Glitch Transition',
    description: 'Digital glitch effect for modern edits',
    category: 'effects',
    icon: <Zap className="w-4 h-4" />,
    duration: '0.5s',
    difficulty: 'easy',
    tags: ['glitch', 'digital', 'transition'],
    steps: [
      {
        id: '1',
        type: 'EFFECT',
        name: 'RGB split',
        parameters: { distance: 10, duration: 0.2 }
      },
      {
        id: '2',
        type: 'EFFECT',
        name: 'Digital noise',
        parameters: { type: 'blocks', intensity: 0.8 }
      },
      {
        id: '3',
        type: 'EFFECT',
        name: 'Frame skip',
        parameters: { frames: 3, random: true }
      }
    ]
  },
  {
    id: 'slow-motion',
    name: 'Epic Slow Motion',
    description: 'Smooth slow motion with motion blur',
    category: 'effects',
    icon: <Clock className="w-4 h-4" />,
    duration: 'Variable',
    difficulty: 'medium',
    tags: ['slowmo', 'epic', 'smooth'],
    steps: [
      {
        id: '1',
        type: 'SPEED',
        name: 'Slow down',
        parameters: { speed: 0.25, interpolation: 'optical-flow' }
      },
      {
        id: '2',
        type: 'EFFECT',
        name: 'Motion blur',
        parameters: { intensity: 0.6, samples: 16 }
      },
      {
        id: '3',
        type: 'AUDIO_MIX',
        name: 'Pitch correction',
        parameters: { maintainPitch: true }
      }
    ]
  },

  // Audio Templates
  {
    id: 'podcast-master',
    name: 'Podcast Mastering',
    description: 'Professional audio processing for podcasts',
    category: 'audio',
    icon: <Music className="w-4 h-4" />,
    duration: 'Full audio',
    difficulty: 'medium',
    tags: ['podcast', 'audio', 'voice'],
    steps: [
      {
        id: '1',
        type: 'AUDIO_MIX',
        name: 'Noise reduction',
        parameters: { type: 'denoise', threshold: -40, reduction: 12 }
      },
      {
        id: '2',
        type: 'AUDIO_MIX',
        name: 'EQ voice',
        parameters: { 
          preset: 'voice',
          highpass: 80,
          presence: { freq: 3000, gain: 3, q: 0.7 }
        }
      },
      {
        id: '3',
        type: 'AUDIO_MIX',
        name: 'Compress',
        parameters: { ratio: 3, threshold: -12, attack: 10, release: 100 }
      },
      {
        id: '4',
        type: 'AUDIO_MIX',
        name: 'Normalize',
        parameters: { targetLUFS: -16, truePeak: -1 }
      }
    ]
  },
  {
    id: 'music-video-sync',
    name: 'Music Video Sync',
    description: 'Sync cuts to music beats automatically',
    category: 'audio',
    icon: <Music className="w-4 h-4" />,
    duration: 'Beat-based',
    difficulty: 'hard',
    tags: ['music', 'sync', 'rhythm'],
    steps: [
      {
        id: '1',
        type: 'AUDIO_MIX',
        name: 'Analyze beats',
        parameters: { detectBeats: true, detectTempo: true }
      },
      {
        id: '2',
        type: 'CUT',
        name: 'Cut on beat',
        parameters: { syncToBeat: true, offset: 0 }
      },
      {
        id: '3',
        type: 'EFFECT',
        name: 'Beat flash',
        parameters: { type: 'flash', syncToAudio: true, intensity: 0.5 }
      }
    ]
  }
];

export default function OperationTemplates({ 
  projectId,
  onApplyTemplate,
  onSaveTemplate,
  className = '' 
}: OperationTemplatesProps) {
  const [templates, setTemplates] = useState<OperationTemplate[]>(DEFAULT_TEMPLATES);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<OperationTemplate | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [customTemplate, setCustomTemplate] = useState<Partial<OperationTemplate>>({
    name: '',
    description: '',
    category: 'custom',
    steps: []
  });

  // Load user templates from localStorage
  useEffect(() => {
    const savedTemplates = localStorage.getItem('userTemplates');
    if (savedTemplates) {
      try {
        const userTemplates = JSON.parse(savedTemplates);
        setTemplates([...DEFAULT_TEMPLATES, ...userTemplates]);
      } catch (error) {
        console.error('Error loading user templates:', error);
      }
    }
  }, []);

  // Filter templates based on search and category
  const filteredTemplates = templates.filter(template => {
    const matchesSearch = 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  // Group templates by category
  const groupedTemplates = filteredTemplates.reduce((acc, template) => {
    if (!acc[template.category]) {
      acc[template.category] = [];
    }
    acc[template.category].push(template);
    return acc;
  }, {} as Record<string, OperationTemplate[]>);

  const handleApplyTemplate = (template: OperationTemplate) => {
    // Update usage stats
    const updatedTemplates = templates.map(t => 
      t.id === template.id 
        ? { 
            ...t, 
            usageCount: (t.usageCount || 0) + 1,
            lastUsed: new Date()
          }
        : t
    );
    setTemplates(updatedTemplates);

    if (onApplyTemplate) {
      onApplyTemplate(template);
    }
  };

  const handleToggleFavorite = (templateId: string) => {
    const updatedTemplates = templates.map(t => 
      t.id === templateId ? { ...t, isFavorite: !t.isFavorite } : t
    );
    setTemplates(updatedTemplates);
  };

  const handleDeleteTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template && DEFAULT_TEMPLATES.find(t => t.id === templateId)) {
      // Can't delete default templates
      return;
    }
    
    const updatedTemplates = templates.filter(t => t.id !== templateId);
    setTemplates(updatedTemplates);
    
    // Update localStorage
    const userTemplates = updatedTemplates.filter(t => 
      !DEFAULT_TEMPLATES.find(dt => dt.id === t.id)
    );
    localStorage.setItem('userTemplates', JSON.stringify(userTemplates));
  };

  const handleSaveCustomTemplate = () => {
    if (!customTemplate.name || !customTemplate.steps?.length) return;

    const newTemplate: OperationTemplate = {
      id: `custom-${Date.now()}`,
      name: customTemplate.name,
      description: customTemplate.description || '',
      category: 'custom',
      steps: customTemplate.steps as OperationStep[],
      tags: [],
      difficulty: 'medium'
    };

    const updatedTemplates = [...templates, newTemplate];
    setTemplates(updatedTemplates);

    // Save to localStorage
    const userTemplates = updatedTemplates.filter(t => 
      !DEFAULT_TEMPLATES.find(dt => dt.id === t.id)
    );
    localStorage.setItem('userTemplates', JSON.stringify(userTemplates));

    if (onSaveTemplate) {
      onSaveTemplate(newTemplate);
    }

    // Reset form
    setIsCreating(false);
    setCustomTemplate({
      name: '',
      description: '',
      category: 'custom',
      steps: []
    });
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'youtube': return <Youtube className="w-4 h-4" />;
      case 'social': return <TrendingUp className="w-4 h-4" />;
      case 'effects': return <Sparkles className="w-4 h-4" />;
      case 'audio': return <Music className="w-4 h-4" />;
      case 'color': return <Type className="w-4 h-4" />;
      case 'custom': return <Settings className="w-4 h-4" />;
      default: return <Folder className="w-4 h-4" />;
    }
  };

  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-500';
      case 'medium': return 'text-yellow-500';
      case 'hard': return 'text-red-500';
      default: return 'text-zinc-400';
    }
  };

  return (
    <Card className={`h-full flex flex-col bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="flex-shrink-0 border-b border-zinc-700">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <Wand2 className="w-5 h-5" />
            Operation Templates
            <Badge variant="outline" className="text-xs">
              {templates.length} templates
            </Badge>
          </div>
          
          <Button
            size="sm"
            onClick={() => setIsCreating(!isCreating)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-1" />
            Create Template
          </Button>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Search and Filters */}
        <div className="p-4 border-b border-zinc-700 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <Input
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-zinc-800 border-zinc-600 text-white"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant={selectedCategory === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('all')}
              className="text-xs"
            >
              All
            </Button>
            <Button
              variant={selectedCategory === 'youtube' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('youtube')}
              className="text-xs"
            >
              <Youtube className="w-3 h-3 mr-1" />
              YouTube
            </Button>
            <Button
              variant={selectedCategory === 'social' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('social')}
              className="text-xs"
            >
              <TrendingUp className="w-3 h-3 mr-1" />
              Social
            </Button>
            <Button
              variant={selectedCategory === 'effects' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('effects')}
              className="text-xs"
            >
              <Sparkles className="w-3 h-3 mr-1" />
              Effects
            </Button>
            <Button
              variant={selectedCategory === 'audio' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('audio')}
              className="text-xs"
            >
              <Music className="w-3 h-3 mr-1" />
              Audio
            </Button>
            <Button
              variant={selectedCategory === 'custom' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('custom')}
              className="text-xs"
            >
              <Settings className="w-3 h-3 mr-1" />
              Custom
            </Button>
          </div>
        </div>

        {/* Template List or Create Form */}
        {isCreating ? (
          <div className="p-4 space-y-4">
            <h3 className="font-medium text-white mb-4">Create Custom Template</h3>
            
            <div className="space-y-3">
              <div>
                <Label htmlFor="template-name" className="text-zinc-300">Template Name</Label>
                <Input
                  id="template-name"
                  placeholder="e.g., My Custom Intro"
                  value={customTemplate.name}
                  onChange={(e) => setCustomTemplate({ ...customTemplate, name: e.target.value })}
                  className="bg-zinc-800 border-zinc-600 text-white"
                />
              </div>
              
              <div>
                <Label htmlFor="template-desc" className="text-zinc-300">Description</Label>
                <Input
                  id="template-desc"
                  placeholder="Brief description of what this template does"
                  value={customTemplate.description}
                  onChange={(e) => setCustomTemplate({ ...customTemplate, description: e.target.value })}
                  className="bg-zinc-800 border-zinc-600 text-white"
                />
              </div>
              
              <div>
                <Label className="text-zinc-300">Steps</Label>
                <div className="text-sm text-zinc-400 mb-2">
                  Add operation steps from your current queue or create manually
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="bg-zinc-800 border-zinc-600"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Step
                </Button>
              </div>
            </div>
            
            <div className="flex gap-2 pt-4">
              <Button
                onClick={handleSaveCustomTemplate}
                disabled={!customTemplate.name || !customTemplate.steps?.length}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Save className="w-4 h-4 mr-1" />
                Save Template
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setIsCreating(false);
                  setCustomTemplate({ name: '', description: '', category: 'custom', steps: [] });
                }}
                className="bg-zinc-800 border-zinc-600"
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4">
            {Object.keys(groupedTemplates).length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-zinc-500">
                <Wand2 className="w-8 h-8 mb-2" />
                <p className="text-sm">No templates found</p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(groupedTemplates).map(([category, categoryTemplates]) => (
                  <div key={category}>
                    <div className="flex items-center gap-2 mb-3">
                      {getCategoryIcon(category)}
                      <h3 className="font-medium text-zinc-300 capitalize">{category}</h3>
                      <Badge variant="secondary" className="text-xs">
                        {categoryTemplates.length}
                      </Badge>
                    </div>
                    
                    <div className="grid gap-3">
                      {categoryTemplates.map(template => (
                        <div
                          key={template.id}
                          className={`relative bg-zinc-800 rounded-lg p-4 border transition-all cursor-pointer ${
                            selectedTemplate?.id === template.id 
                              ? 'border-blue-500 ring-1 ring-blue-500' 
                              : 'border-zinc-700 hover:border-zinc-600'
                          }`}
                          onClick={() => setSelectedTemplate(template)}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-start gap-3">
                              <div className={`w-10 h-10 rounded-lg ${
                                template.category === 'youtube' ? 'bg-red-600' :
                                template.category === 'social' ? 'bg-blue-600' :
                                template.category === 'effects' ? 'bg-purple-600' :
                                template.category === 'audio' ? 'bg-orange-600' :
                                'bg-zinc-600'
                              } flex items-center justify-center text-white`}>
                                {template.icon || getCategoryIcon(template.category)}
                              </div>
                              
                              <div className="flex-1">
                                <h4 className="font-medium text-white flex items-center gap-2">
                                  {template.name}
                                  {template.isFavorite && <Star className="w-3 h-3 text-yellow-500 fill-current" />}
                                </h4>
                                <p className="text-sm text-zinc-400 mt-1">{template.description}</p>
                                
                                <div className="flex items-center gap-3 mt-2">
                                  {template.duration && (
                                    <div className="flex items-center gap-1 text-xs text-zinc-500">
                                      <Clock className="w-3 h-3" />
                                      {template.duration}
                                    </div>
                                  )}
                                  {template.difficulty && (
                                    <div className={`flex items-center gap-1 text-xs ${getDifficultyColor(template.difficulty)}`}>
                                      <Zap className="w-3 h-3" />
                                      {template.difficulty}
                                    </div>
                                  )}
                                  {template.steps && (
                                    <div className="flex items-center gap-1 text-xs text-zinc-500">
                                      <ChevronRight className="w-3 h-3" />
                                      {template.steps.length} steps
                                    </div>
                                  )}
                                  {template.usageCount && template.usageCount > 0 && (
                                    <div className="flex items-center gap-1 text-xs text-zinc-500">
                                      <PlayCircle className="w-3 h-3" />
                                      Used {template.usageCount}x
                                    </div>
                                  )}
                                </div>
                                
                                {template.tags && template.tags.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {template.tags.map(tag => (
                                      <Badge key={tag} variant="secondary" className="text-xs">
                                        {tag}
                                      </Badge>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleToggleFavorite(template.id);
                                }}
                                className="h-8 w-8 p-0"
                              >
                                {template.isFavorite ? 
                                  <Star className="w-4 h-4 text-yellow-500 fill-current" /> : 
                                  <StarOff className="w-4 h-4 text-zinc-400" />
                                }
                              </Button>
                              
                              {!DEFAULT_TEMPLATES.find(t => t.id === template.id) && (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      // Edit template
                                    }}
                                    className="h-8 w-8 p-0"
                                  >
                                    <Edit className="w-4 h-4 text-zinc-400" />
                                  </Button>
                                  
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteTemplate(template.id);
                                    }}
                                    className="h-8 w-8 p-0"
                                  >
                                    <Trash2 className="w-4 h-4 text-red-400" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>
                          
                          {selectedTemplate?.id === template.id && (
                            <div className="mt-4 pt-4 border-t border-zinc-700">
                              <h5 className="text-sm font-medium text-zinc-300 mb-2">Operation Steps:</h5>
                              <div className="space-y-2">
                                {template.steps.map((step, index) => (
                                  <div key={step.id} className="flex items-center gap-2 text-sm">
                                    <Badge variant="outline" className="text-xs">
                                      {index + 1}
                                    </Badge>
                                    <span className="text-zinc-400">{step.name}</span>
                                    <Badge variant="secondary" className="text-xs">
                                      {step.type}
                                    </Badge>
                                    {step.optional && (
                                      <Badge variant="outline" className="text-xs text-zinc-500">
                                        Optional
                                      </Badge>
                                    )}
                                  </div>
                                ))}
                              </div>
                              
                              <div className="flex gap-2 mt-4">
                                <Button
                                  size="sm"
                                  onClick={() => handleApplyTemplate(template)}
                                  className="bg-blue-600 hover:bg-blue-700"
                                >
                                  <PlayCircle className="w-4 h-4 mr-1" />
                                  Apply Template
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    // Duplicate template
                                    const duplicated = {
                                      ...template,
                                      id: `${template.id}-copy-${Date.now()}`,
                                      name: `${template.name} (Copy)`,
                                      category: 'custom' as const
                                    };
                                    setTemplates([...templates, duplicated]);
                                  }}
                                  className="bg-zinc-800 border-zinc-600"
                                >
                                  <Copy className="w-4 h-4 mr-1" />
                                  Duplicate
                                </Button>
                                {template.category === 'custom' && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="bg-zinc-800 border-zinc-600"
                                  >
                                    <Upload className="w-4 h-4 mr-1" />
                                    Export
                                  </Button>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Import/Export */}
        <div className="border-t border-zinc-700 p-3 bg-zinc-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <Info className="w-3 h-3" />
              <span>
                {templates.filter(t => t.isFavorite).length} favorites • 
                {templates.filter(t => !DEFAULT_TEMPLATES.find(dt => dt.id === t.id)).length} custom templates
              </span>
            </div>
            
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="ghost"
                className="text-xs"
              >
                <Download className="w-3 h-3 mr-1" />
                Import
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-xs"
              >
                <Upload className="w-3 h-3 mr-1" />
                Export All
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}