import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Youtube, 
  Instagram, 
  Play, 
  Zap, 
  Film,
  Music,
  Sparkles,
  Clock,
  Monitor,
  Smartphone,
  Square,
  Star,
  TrendingUp,
  Video,
  Camera,
  Tv,
  BookOpen,
  Gamepad2,
  Mic,
  DollarSign,
  Heart,
  Globe,
  Loader2,
  Check,
  Plus,
  Download,
  Upload,
  Share2
} from 'lucide-react';

interface Template {
  id: string;
  name: string;
  category: string;
  platform: string;
  icon: React.ReactNode;
  description: string;
  duration: string;
  aspectRatio: string;
  resolution: string;
  fps: number;
  operations: TemplateOperation[];
  tags: string[];
  popularity: number;
}

interface TemplateOperation {
  type: string;
  params: Record<string, any>;
  description: string;
}

interface QuickTemplatesProps {
  projectId: string;
  onApplyTemplate: (template: Template) => void;
  onSaveTemplate?: (template: Partial<Template>) => void;
  className?: string;
}

export default function QuickTemplates({
  projectId,
  onApplyTemplate,
  onSaveTemplate,
  className = ''
}: QuickTemplatesProps) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [appliedTemplates, setAppliedTemplates] = useState<Set<string>>(new Set());
  const [isApplying, setIsApplying] = useState<string | null>(null);
  const [showCustomDialog, setShowCustomDialog] = useState(false);

  const templates: Template[] = [
    // YouTube Templates
    {
      id: 'yt-standard',
      name: 'YouTube Standard',
      category: 'youtube',
      platform: 'YouTube',
      icon: <Youtube className="w-4 h-4" />,
      description: 'Standard YouTube video with intro, content, and outro',
      duration: '10-15 min',
      aspectRatio: '16:9',
      resolution: '1920x1080',
      fps: 30,
      operations: [
        { type: 'add-intro', params: { duration: 5, style: 'fade' }, description: 'Add 5s intro' },
        { type: 'add-outro', params: { duration: 10, style: 'subscribe' }, description: 'Add subscribe outro' },
        { type: 'add-chapters', params: { auto: true }, description: 'Auto-generate chapters' },
        { type: 'optimize-audio', params: { normalize: true, level: -14 }, description: 'Normalize audio' }
      ],
      tags: ['youtube', 'standard', 'long-form'],
      popularity: 95
    },
    {
      id: 'yt-short',
      name: 'YouTube Shorts',
      category: 'youtube',
      platform: 'YouTube Shorts',
      icon: <Youtube className="w-4 h-4" />,
      description: 'Vertical short-form content for YouTube Shorts',
      duration: '< 60s',
      aspectRatio: '9:16',
      resolution: '1080x1920',
      fps: 30,
      operations: [
        { type: 'crop-vertical', params: { ratio: '9:16' }, description: 'Crop to vertical' },
        { type: 'add-captions', params: { style: 'dynamic', size: 'large' }, description: 'Add dynamic captions' },
        { type: 'add-hook', params: { duration: 3 }, description: 'Add attention hook' },
        { type: 'fast-pacing', params: { cuts: 'aggressive' }, description: 'Fast-paced editing' }
      ],
      tags: ['youtube', 'shorts', 'vertical'],
      popularity: 88
    },
    
    // TikTok Templates
    {
      id: 'tiktok-viral',
      name: 'TikTok Viral',
      category: 'tiktok',
      platform: 'TikTok',
      icon: <Video className="w-4 h-4" />,
      description: 'Optimized for TikTok algorithm and engagement',
      duration: '15-30s',
      aspectRatio: '9:16',
      resolution: '1080x1920',
      fps: 30,
      operations: [
        { type: 'crop-vertical', params: { ratio: '9:16' }, description: 'Crop to vertical' },
        { type: 'add-trending-audio', params: { auto: true }, description: 'Add trending audio' },
        { type: 'add-effects', params: { type: 'transitions', style: 'trendy' }, description: 'Add trendy transitions' },
        { type: 'add-text-overlay', params: { style: 'tiktok', animate: true }, description: 'Add animated text' },
        { type: 'loop-ending', params: { duration: 1 }, description: 'Add loop for replay' }
      ],
      tags: ['tiktok', 'viral', 'trending'],
      popularity: 92
    },
    
    // Instagram Templates
    {
      id: 'ig-reel',
      name: 'Instagram Reel',
      category: 'instagram',
      platform: 'Instagram Reels',
      icon: <Instagram className="w-4 h-4" />,
      description: 'Engaging reel with music and effects',
      duration: '15-90s',
      aspectRatio: '9:16',
      resolution: '1080x1920',
      fps: 30,
      operations: [
        { type: 'crop-vertical', params: { ratio: '9:16' }, description: 'Crop to vertical' },
        { type: 'add-music-beat-sync', params: { auto: true }, description: 'Sync cuts to music' },
        { type: 'add-filters', params: { style: 'instagram' }, description: 'Apply IG filters' },
        { type: 'add-stickers', params: { animate: true }, description: 'Add animated stickers' }
      ],
      tags: ['instagram', 'reels', 'social'],
      popularity: 85
    },
    {
      id: 'ig-story',
      name: 'Instagram Story',
      category: 'instagram',
      platform: 'Instagram Stories',
      icon: <Instagram className="w-4 h-4" />,
      description: 'Quick story with polls and interactions',
      duration: '15s',
      aspectRatio: '9:16',
      resolution: '1080x1920',
      fps: 30,
      operations: [
        { type: 'crop-vertical', params: { ratio: '9:16' }, description: 'Crop to vertical' },
        { type: 'add-poll', params: { position: 'center' }, description: 'Add interactive poll' },
        { type: 'add-location', params: { auto: true }, description: 'Add location tag' },
        { type: 'add-countdown', params: { style: 'minimal' }, description: 'Add countdown timer' }
      ],
      tags: ['instagram', 'story', 'interactive'],
      popularity: 78
    },
    
    // Professional Templates
    {
      id: 'tutorial',
      name: 'Tutorial/How-To',
      category: 'educational',
      platform: 'Multi-platform',
      icon: <BookOpen className="w-4 h-4" />,
      description: 'Step-by-step tutorial with chapters and callouts',
      duration: '5-20 min',
      aspectRatio: '16:9',
      resolution: '1920x1080',
      fps: 30,
      operations: [
        { type: 'add-step-numbers', params: { style: 'circle' }, description: 'Add step numbers' },
        { type: 'add-arrows', params: { color: 'red', animate: true }, description: 'Add pointing arrows' },
        { type: 'add-zoom', params: { areas: 'auto-detect' }, description: 'Add zoom effects' },
        { type: 'add-chapters', params: { numbered: true }, description: 'Add numbered chapters' },
        { type: 'add-summary', params: { position: 'end' }, description: 'Add summary slide' }
      ],
      tags: ['tutorial', 'educational', 'how-to'],
      popularity: 82
    },
    {
      id: 'podcast-clip',
      name: 'Podcast Highlight',
      category: 'podcast',
      platform: 'Multi-platform',
      icon: <Mic className="w-4 h-4" />,
      description: 'Engaging podcast clip with waveforms',
      duration: '30-90s',
      aspectRatio: '16:9',
      resolution: '1920x1080',
      fps: 30,
      operations: [
        { type: 'add-waveform', params: { style: 'animated', color: 'gradient' }, description: 'Add audio waveform' },
        { type: 'add-captions', params: { style: 'karaoke', accuracy: 'high' }, description: 'Add synced captions' },
        { type: 'add-speaker-labels', params: { position: 'bottom' }, description: 'Add speaker names' },
        { type: 'add-branding', params: { logo: true, colors: true }, description: 'Add podcast branding' }
      ],
      tags: ['podcast', 'audio', 'clips'],
      popularity: 76
    },
    
    // Gaming Templates
    {
      id: 'gaming-highlight',
      name: 'Gaming Highlight',
      category: 'gaming',
      platform: 'Multi-platform',
      icon: <Gamepad2 className="w-4 h-4" />,
      description: 'Epic gaming moments with effects',
      duration: '30-60s',
      aspectRatio: '16:9',
      resolution: '1920x1080',
      fps: 60,
      operations: [
        { type: 'add-kill-counter', params: { style: 'modern' }, description: 'Add kill counter' },
        { type: 'add-slow-motion', params: { moments: 'epic' }, description: 'Add slow-mo effects' },
        { type: 'add-hitmarkers', params: { sound: true }, description: 'Add hitmarkers' },
        { type: 'add-replay', params: { angles: 'multi' }, description: 'Add instant replay' },
        { type: 'add-meme-sounds', params: { timing: 'auto' }, description: 'Add meme sounds' }
      ],
      tags: ['gaming', 'highlights', 'epic'],
      popularity: 89
    }
  ];

  const categories = [
    { id: 'all', label: 'All Templates', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'youtube', label: 'YouTube', icon: <Youtube className="w-4 h-4" /> },
    { id: 'tiktok', label: 'TikTok', icon: <Video className="w-4 h-4" /> },
    { id: 'instagram', label: 'Instagram', icon: <Instagram className="w-4 h-4" /> },
    { id: 'educational', label: 'Educational', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'podcast', label: 'Podcast', icon: <Mic className="w-4 h-4" /> },
    { id: 'gaming', label: 'Gaming', icon: <Gamepad2 className="w-4 h-4" /> }
  ];

  const handleApplyTemplate = useCallback(async (template: Template) => {
    setIsApplying(template.id);
    
    try {
      // Simulate applying template operations
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onApplyTemplate(template);
      setAppliedTemplates(prev => new Set(prev).add(template.id));
    } catch (error) {
      console.error('Failed to apply template:', error);
    } finally {
      setIsApplying(null);
    }
  }, [onApplyTemplate]);

  const filteredTemplates = templates.filter(t => 
    selectedCategory === 'all' || t.category === selectedCategory
  );

  return (
    <Card className={`bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-500" />
            Quick Templates
          </CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowCustomDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Custom
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
          <TabsList className="grid grid-cols-4 lg:grid-cols-7 mb-4 h-auto">
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

          <TabsContent value={selectedCategory} className="space-y-4">
            <div className="grid gap-4">
              {filteredTemplates.map(template => (
                <div
                  key={template.id}
                  className={`p-4 rounded-lg border transition-all ${
                    appliedTemplates.has(template.id)
                      ? 'bg-zinc-800/50 border-zinc-700'
                      : 'bg-zinc-800 border-zinc-700 hover:border-zinc-600'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-zinc-700">
                      {template.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h3 className="font-semibold text-white flex items-center gap-2">
                            {template.name}
                            {template.popularity > 85 && (
                              <Badge variant="secondary" className="text-xs">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                Popular
                              </Badge>
                            )}
                          </h3>
                          <p className="text-sm text-zinc-400">{template.description}</p>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-3">
                        <Badge variant="outline" className="text-xs">
                          <Clock className="w-3 h-3 mr-1" />
                          {template.duration}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          <Monitor className="w-3 h-3 mr-1" />
                          {template.resolution}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {template.aspectRatio}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {template.fps} FPS
                        </Badge>
                      </div>

                      <div className="space-y-1 mb-3">
                        <p className="text-xs font-medium text-zinc-400 mb-1">Operations:</p>
                        {template.operations.slice(0, 3).map((op, idx) => (
                          <div key={idx} className="text-xs text-zinc-500 flex items-center gap-2">
                            <Check className="w-3 h-3 text-green-500" />
                            {op.description}
                          </div>
                        ))}
                        {template.operations.length > 3 && (
                          <p className="text-xs text-zinc-500 italic">
                            +{template.operations.length - 3} more operations
                          </p>
                        )}
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          {template.tags.slice(0, 3).map(tag => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                        <div className="flex gap-2">
                          {appliedTemplates.has(template.id) ? (
                            <Badge variant="secondary" className="text-xs">
                              <Check className="w-3 h-3 mr-1" />
                              Applied
                            </Badge>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => handleApplyTemplate(template)}
                              disabled={isApplying === template.id}
                            >
                              {isApplying === template.id ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  Applying...
                                </>
                              ) : (
                                <>
                                  <Play className="w-4 h-4 mr-2" />
                                  Apply
                                </>
                              )}
                            </Button>
                          )}
                          <Button size="sm" variant="ghost">
                            <Share2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}