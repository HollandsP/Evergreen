import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Lightbulb, 
  Zap, 
  Clock, 
  TrendingUp, 
  Sparkles,
  Check,
  X,
  ChevronRight,
  Wand2,
  Film,
  Music,
  Type,
  Palette,
  Volume2,
  Timer,
  Layers,
  ArrowRight
} from 'lucide-react';

interface Suggestion {
  id: string;
  type: 'cut' | 'transition' | 'effect' | 'audio' | 'text' | 'color' | 'timing' | 'optimization';
  title: string;
  description: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high';
  icon: React.ReactNode;
  action: () => void;
  preview?: string;
  estimatedTime?: string;
  category: string;
}

interface SmartSuggestionsProps {
  projectId: string;
  currentScene?: number;
  timelineData?: any;
  onApplySuggestion?: (suggestion: Suggestion) => void;
  className?: string;
}

export default function SmartSuggestions({
  projectId,
  currentScene,
  timelineData,
  onApplySuggestion,
  className = ''
}: SmartSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [appliedSuggestions, setAppliedSuggestions] = useState<Set<string>>(new Set());
  const analysisTimeoutRef = useRef<NodeJS.Timeout>();

  const categories = [
    { id: 'all', label: 'All', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'timing', label: 'Timing', icon: <Clock className="w-4 h-4" /> },
    { id: 'transitions', label: 'Transitions', icon: <Film className="w-4 h-4" /> },
    { id: 'audio', label: 'Audio', icon: <Music className="w-4 h-4" /> },
    { id: 'visual', label: 'Visual', icon: <Palette className="w-4 h-4" /> },
    { id: 'optimization', label: 'Optimize', icon: <Zap className="w-4 h-4" /> }
  ];

  // AI-powered analysis function
  const analyzeContent = useCallback(async () => {
    setIsAnalyzing(true);

    try {
      // Simulate AI analysis - in production, this would call your AI service
      await new Promise(resolve => setTimeout(resolve, 1500));

      const newSuggestions: Suggestion[] = [
        {
          id: '1',
          type: 'cut',
          title: 'Remove Dead Air',
          description: 'Detected 3.2s of silence at scene start. Remove for better pacing.',
          confidence: 0.92,
          impact: 'high',
          icon: <Timer className="w-4 h-4" />,
          action: () => console.log('Removing dead air'),
          estimatedTime: '2s',
          category: 'timing'
        },
        {
          id: '2',
          type: 'transition',
          title: 'Add Smooth Transition',
          description: 'Harsh cut between scenes 2-3. Add crossfade for continuity.',
          confidence: 0.88,
          impact: 'medium',
          icon: <Film className="w-4 h-4" />,
          action: () => console.log('Adding transition'),
          estimatedTime: '1s',
          category: 'transitions'
        },
        {
          id: '3',
          type: 'audio',
          title: 'Balance Audio Levels',
          description: 'Scene 4 audio is 6dB louder. Normalize for consistency.',
          confidence: 0.95,
          impact: 'high',
          icon: <Volume2 className="w-4 h-4" />,
          action: () => console.log('Balancing audio'),
          estimatedTime: '1s',
          category: 'audio'
        },
        {
          id: '4',
          type: 'effect',
          title: 'Enhance Dark Scene',
          description: 'Scene 5 is underexposed. Apply auto-brightness correction.',
          confidence: 0.85,
          impact: 'medium',
          icon: <Palette className="w-4 h-4" />,
          action: () => console.log('Enhancing brightness'),
          estimatedTime: '3s',
          category: 'visual'
        },
        {
          id: '5',
          type: 'text',
          title: 'Add Scene Title',
          description: 'Opening lacks context. Add title card "Chapter 1: The Beginning".',
          confidence: 0.82,
          impact: 'low',
          icon: <Type className="w-4 h-4" />,
          action: () => console.log('Adding title'),
          estimatedTime: '2s',
          category: 'visual'
        },
        {
          id: '6',
          type: 'timing',
          title: 'Match Action Beats',
          description: 'Cut to music beat at 1:23 for dramatic impact.',
          confidence: 0.90,
          impact: 'medium',
          icon: <Music className="w-4 h-4" />,
          action: () => console.log('Matching beats'),
          estimatedTime: '1s',
          category: 'timing'
        },
        {
          id: '7',
          type: 'optimization',
          title: 'Remove Duplicate Frames',
          description: 'Found 120 duplicate frames. Remove to reduce file size by 15%.',
          confidence: 0.98,
          impact: 'low',
          icon: <Layers className="w-4 h-4" />,
          action: () => console.log('Removing duplicates'),
          estimatedTime: '5s',
          category: 'optimization'
        },
        {
          id: '8',
          type: 'color',
          title: 'Apply Color Grading',
          description: 'Inconsistent color temperature. Apply cinematic LUT for cohesion.',
          confidence: 0.87,
          impact: 'high',
          icon: <Palette className="w-4 h-4" />,
          action: () => console.log('Applying color grade'),
          estimatedTime: '4s',
          category: 'visual'
        }
      ];

      setSuggestions(newSuggestions);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  // Auto-analyze on mount and data changes
  useEffect(() => {
    if (analysisTimeoutRef.current) {
      clearTimeout(analysisTimeoutRef.current);
    }

    analysisTimeoutRef.current = setTimeout(() => {
      analyzeContent();
    }, 2000); // 2 second delay as per requirements

    return () => {
      if (analysisTimeoutRef.current) {
        clearTimeout(analysisTimeoutRef.current);
      }
    };
  }, [timelineData, currentScene, analyzeContent]);

  const handleApplySuggestion = (suggestion: Suggestion) => {
    suggestion.action();
    setAppliedSuggestions(prev => new Set(prev).add(suggestion.id));
    
    if (onApplySuggestion) {
      onApplySuggestion(suggestion);
    }
  };

  const filteredSuggestions = suggestions.filter(s => 
    selectedCategory === 'all' || s.category === selectedCategory
  );

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-zinc-400';
    }
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'Very Confident';
    if (confidence >= 0.8) return 'Confident';
    if (confidence >= 0.7) return 'Likely';
    return 'Possible';
  };

  return (
    <Card className={`bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            Smart Suggestions
          </CardTitle>
          {isAnalyzing && (
            <Badge variant="secondary" className="animate-pulse">
              <Zap className="w-3 h-3 mr-1" />
              Analyzing...
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Category Filter */}
        <div className="flex gap-2 flex-wrap">
          {categories.map(category => (
            <Button
              key={category.id}
              size="sm"
              variant={selectedCategory === category.id ? 'default' : 'outline'}
              onClick={() => setSelectedCategory(category.id)}
              className="flex items-center gap-1"
            >
              {category.icon}
              {category.label}
            </Button>
          ))}
        </div>

        {/* Suggestions List */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filteredSuggestions.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              {isAnalyzing ? 'Analyzing your content...' : 'No suggestions available'}
            </div>
          ) : (
            filteredSuggestions.map(suggestion => (
              <div
                key={suggestion.id}
                className={`p-4 rounded-lg border transition-all ${
                  appliedSuggestions.has(suggestion.id)
                    ? 'bg-zinc-800/50 border-zinc-700 opacity-50'
                    : 'bg-zinc-800 border-zinc-700 hover:border-zinc-600'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg bg-zinc-700 ${
                    appliedSuggestions.has(suggestion.id) ? 'opacity-50' : ''
                  }`}>
                    {suggestion.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-white">{suggestion.title}</h4>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {getConfidenceLabel(suggestion.confidence)}
                        </Badge>
                        <span className={`text-xs font-medium ${getImpactColor(suggestion.impact)}`}>
                          {suggestion.impact.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-zinc-400 mb-2">{suggestion.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 text-xs text-zinc-500">
                        {suggestion.estimatedTime && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {suggestion.estimatedTime}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          {Math.round(suggestion.confidence * 100)}% confident
                        </span>
                      </div>
                      {appliedSuggestions.has(suggestion.id) ? (
                        <Badge variant="secondary" className="text-xs">
                          <Check className="w-3 h-3 mr-1" />
                          Applied
                        </Badge>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleApplySuggestion(suggestion)}
                          className="text-xs"
                        >
                          Apply
                          <ArrowRight className="w-3 h-3 ml-1" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Quick Actions */}
        {filteredSuggestions.length > 0 && (
          <div className="pt-4 border-t border-zinc-700">
            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  filteredSuggestions
                    .filter(s => !appliedSuggestions.has(s.id) && s.confidence >= 0.9)
                    .forEach(s => handleApplySuggestion(s));
                }}
                disabled={filteredSuggestions.every(s => appliedSuggestions.has(s.id) || s.confidence < 0.9)}
              >
                <Wand2 className="w-4 h-4 mr-2" />
                Apply High Confidence
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={analyzeContent}
                disabled={isAnalyzing}
              >
                Refresh Analysis
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}