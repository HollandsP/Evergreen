/**
 * Video style templates and presets system
 * Provides predefined styles and customizable templates for video generation
 */

export interface StyleTemplate {
  id: string;
  name: string;
  description: string;
  category: 'cinematic' | 'commercial' | 'artistic' | 'educational' | 'social' | 'corporate';
  preview?: string;
  
  visual: {
    colorPalette: string[];
    mood: string;
    lighting: string;
    composition: string;
    cameraStyle: string;
    postProcessing: string[];
  };
  
  audio: {
    musicGenre?: string;
    mood: string;
    tempo: 'slow' | 'medium' | 'fast' | 'variable';
    instruments: string[];
    effects: string[];
  };
  
  pacing: {
    rhythm: 'slow' | 'medium' | 'fast' | 'dynamic';
    transitionStyle: string;
    cutFrequency: 'minimal' | 'moderate' | 'frequent';
    pauseDuration: number; // seconds
  };
  
  text: {
    fontFamily: string;
    fontSize: 'small' | 'medium' | 'large' | 'variable';
    color: string;
    animation: string;
    position: 'top' | 'center' | 'bottom' | 'overlay';
  };
  
  technical: {
    aspectRatio: '16:9' | '9:16' | '4:3' | '1:1' | 'custom';
    resolution: '720p' | '1080p' | '1440p' | '4K';
    framerate: 24 | 30 | 60;
    duration: 'auto' | number; // seconds
  };
  
  prompts: {
    visualPrompt: string;
    styleModifiers: string[];
    negativePrompts: string[];
  };
  
  usage: {
    popularity: number;
    userRating: number;
    successRate: number;
    lastUsed?: Date;
  };
  
  customization: {
    allowColorChange: boolean;
    allowMoodChange: boolean;
    allowPacingChange: boolean;
    variableElements: string[];
  };
}

export interface StylePreset {
  id: string;
  name: string;
  description: string;
  templateId: string;
  customizations: Record<string, any>;
  createdAt: Date;
  isPublic: boolean;
  tags: string[];
}

export interface StyleGenerationOptions {
  template: StyleTemplate;
  customizations?: Record<string, any>;
  content: {
    script: string;
    duration?: number;
    mood?: string;
  };
  quality: 'draft' | 'standard' | 'premium';
}

const predefinedTemplates: StyleTemplate[] = [
  {
    id: 'cinematic-noir',
    name: 'Cinematic Noir',
    description: 'Dark, moody cinematography with high contrast and dramatic lighting',
    category: 'cinematic',
    
    visual: {
      colorPalette: ['#1a1a1a', '#333333', '#666666', '#ffffff', '#cc9900'],
      mood: 'dark and mysterious',
      lighting: 'dramatic chiaroscuro with deep shadows',
      composition: 'wide shots with strong leading lines',
      cameraStyle: 'steady, purposeful movements with occasional close-ups',
      postProcessing: ['high_contrast', 'film_grain', 'vignette', 'color_desaturation']
    },
    
    audio: {
      musicGenre: 'neo-noir jazz',
      mood: 'suspenseful',
      tempo: 'slow',
      instruments: ['saxophone', 'piano', 'double_bass', 'muted_trumpet'],
      effects: ['reverb', 'echo', 'vinyl_crackle']
    },
    
    pacing: {
      rhythm: 'slow',
      transitionStyle: 'fade_to_black',
      cutFrequency: 'minimal',
      pauseDuration: 2.5
    },
    
    text: {
      fontFamily: 'serif',
      fontSize: 'medium',
      color: '#ffffff',
      animation: 'fade_in_typewriter',
      position: 'bottom'
    },
    
    technical: {
      aspectRatio: '16:9',
      resolution: '1080p',
      framerate: 24,
      duration: 'auto'
    },
    
    prompts: {
      visualPrompt: 'cinematic noir style, dramatic lighting, high contrast, moody shadows, film noir aesthetic',
      styleModifiers: ['black and white', 'venetian blinds shadows', 'smoke effects', 'urban nighttime'],
      negativePrompts: ['bright colors', 'cartoon style', 'cheerful', 'daylight']
    },
    
    usage: {
      popularity: 0.85,
      userRating: 4.3,
      successRate: 0.92
    },
    
    customization: {
      allowColorChange: true,
      allowMoodChange: false,
      allowPacingChange: true,
      variableElements: ['lighting_intensity', 'grain_amount', 'contrast_level']
    }
  },
  
  {
    id: 'modern-commercial',
    name: 'Modern Commercial',
    description: 'Clean, professional style perfect for product showcases and marketing',
    category: 'commercial',
    
    visual: {
      colorPalette: ['#ffffff', '#f8f9fa', '#007bff', '#28a745', '#ffc107'],
      mood: 'bright and confident',
      lighting: 'even, professional studio lighting',
      composition: 'rule of thirds with clean backgrounds',
      cameraStyle: 'smooth tracking shots and steady product focus',
      postProcessing: ['color_correction', 'sharpening', 'clean_edges', 'brightness_boost']
    },
    
    audio: {
      musicGenre: 'corporate pop',
      mood: 'upbeat and motivational',
      tempo: 'medium',
      instruments: ['acoustic_guitar', 'piano', 'light_percussion', 'strings'],
      effects: ['compression', 'eq_brightening']
    },
    
    pacing: {
      rhythm: 'medium',
      transitionStyle: 'smooth_wipe',
      cutFrequency: 'moderate',
      pauseDuration: 1.5
    },
    
    text: {
      fontFamily: 'sans-serif',
      fontSize: 'large',
      color: '#333333',
      animation: 'slide_in_from_left',
      position: 'center'
    },
    
    technical: {
      aspectRatio: '16:9',
      resolution: '1080p',
      framerate: 30,
      duration: 'auto'
    },
    
    prompts: {
      visualPrompt: 'professional commercial style, clean lighting, modern design, high-end product photography',
      styleModifiers: ['minimalist', 'studio quality', 'brand focused', 'premium feel'],
      negativePrompts: ['cluttered', 'low quality', 'amateur', 'dark lighting']
    },
    
    usage: {
      popularity: 0.92,
      userRating: 4.6,
      successRate: 0.95
    },
    
    customization: {
      allowColorChange: true,
      allowMoodChange: true,
      allowPacingChange: true,
      variableElements: ['brand_colors', 'logo_placement', 'text_style']
    }
  },
  
  {
    id: 'artistic-abstract',
    name: 'Artistic Abstract',
    description: 'Creative, experimental style with flowing visuals and artistic flair',
    category: 'artistic',
    
    visual: {
      colorPalette: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b'],
      mood: 'creative and inspiring',
      lighting: 'dynamic with color gels and artistic shadows',
      composition: 'experimental framing with artistic angles',
      cameraStyle: 'flowing movements with creative transitions',
      postProcessing: ['color_grading', 'artistic_filters', 'motion_blur', 'double_exposure']
    },
    
    audio: {
      musicGenre: 'ambient electronic',
      mood: 'dreamy and contemplative',
      tempo: 'variable',
      instruments: ['synthesizer', 'digital_pads', 'processed_vocals', 'electronic_percussion'],
      effects: ['reverb', 'delay', 'modulation', 'spatial_audio']
    },
    
    pacing: {
      rhythm: 'dynamic',
      transitionStyle: 'artistic_morph',
      cutFrequency: 'frequent',
      pauseDuration: 1.0
    },
    
    text: {
      fontFamily: 'artistic',
      fontSize: 'variable',
      color: '#ffffff',
      animation: 'particle_reveal',
      position: 'overlay'
    },
    
    technical: {
      aspectRatio: '16:9',
      resolution: '1080p',
      framerate: 60,
      duration: 'auto'
    },
    
    prompts: {
      visualPrompt: 'artistic abstract style, creative composition, flowing forms, experimental lighting',
      styleModifiers: ['painterly', 'surreal elements', 'color bleeding', 'artistic interpretation'],
      negativePrompts: ['realistic', 'conventional', 'static composition', 'mundane']
    },
    
    usage: {
      popularity: 0.68,
      userRating: 4.1,
      successRate: 0.87
    },
    
    customization: {
      allowColorChange: true,
      allowMoodChange: true,
      allowPacingChange: true,
      variableElements: ['color_scheme', 'abstraction_level', 'motion_intensity']
    }
  },
  
  {
    id: 'social-media-vertical',
    name: 'Social Media Vertical',
    description: 'Optimized for mobile viewing with engaging, fast-paced content',
    category: 'social',
    
    visual: {
      colorPalette: ['#ff0050', '#00d4ff', '#ffed4e', '#ff6b35', '#7209b7'],
      mood: 'energetic and engaging',
      lighting: 'bright and vibrant',
      composition: 'vertical framing with bold graphics',
      cameraStyle: 'dynamic quick cuts and zoom effects',
      postProcessing: ['saturation_boost', 'contrast_enhancement', 'quick_transitions', 'text_overlays']
    },
    
    audio: {
      musicGenre: 'pop electronic',
      mood: 'upbeat and catchy',
      tempo: 'fast',
      instruments: ['electronic_drums', 'bass_synth', 'lead_synth', 'vocal_chops'],
      effects: ['compression', 'sidechain', 'auto_tune', 'beat_sync']
    },
    
    pacing: {
      rhythm: 'fast',
      transitionStyle: 'quick_cut',
      cutFrequency: 'frequent',
      pauseDuration: 0.5
    },
    
    text: {
      fontFamily: 'bold_sans',
      fontSize: 'large',
      color: '#ffffff',
      animation: 'pop_in_scale',
      position: 'center'
    },
    
    technical: {
      aspectRatio: '9:16',
      resolution: '1080p',
      framerate: 30,
      duration: 30
    },
    
    prompts: {
      visualPrompt: 'social media style, vertical format, vibrant colors, mobile-first design',
      styleModifiers: ['trending', 'viral content', 'hook attention', 'scroll-stopping'],
      negativePrompts: ['boring', 'slow paced', 'horizontal format', 'low energy']
    },
    
    usage: {
      popularity: 0.96,
      userRating: 4.4,
      successRate: 0.91
    },
    
    customization: {
      allowColorChange: true,
      allowMoodChange: false,
      allowPacingChange: true,
      variableElements: ['trend_effects', 'text_style', 'transition_speed']
    }
  },
  
  {
    id: 'educational-explainer',
    name: 'Educational Explainer',
    description: 'Clear, informative style designed for learning and comprehension',
    category: 'educational',
    
    visual: {
      colorPalette: ['#2c3e50', '#3498db', '#e74c3c', '#f39c12', '#27ae60'],
      mood: 'clear and informative',
      lighting: 'even, clear visibility',
      composition: 'structured layout with visual hierarchy',
      cameraStyle: 'steady shots with purposeful zooms',
      postProcessing: ['clarity_enhancement', 'text_legibility', 'consistent_exposure']
    },
    
    audio: {
      musicGenre: 'ambient instrumental',
      mood: 'focused and calm',
      tempo: 'medium',
      instruments: ['piano', 'soft_strings', 'light_percussion', 'ambient_pads'],
      effects: ['gentle_compression', 'eq_clarity']
    },
    
    pacing: {
      rhythm: 'medium',
      transitionStyle: 'informative_wipe',
      cutFrequency: 'moderate',
      pauseDuration: 2.0
    },
    
    text: {
      fontFamily: 'readable_sans',
      fontSize: 'medium',
      color: '#2c3e50',
      animation: 'appear_with_highlight',
      position: 'bottom'
    },
    
    technical: {
      aspectRatio: '16:9',
      resolution: '1080p',
      framerate: 30,
      duration: 'auto'
    },
    
    prompts: {
      visualPrompt: 'educational style, clear presentation, informative graphics, learning-focused',
      styleModifiers: ['instructional', 'step-by-step', 'visual aids', 'professional teaching'],
      negativePrompts: ['confusing', 'overwhelming', 'distracting', 'unclear text']
    },
    
    usage: {
      popularity: 0.78,
      userRating: 4.5,
      successRate: 0.94
    },
    
    customization: {
      allowColorChange: true,
      allowMoodChange: false,
      allowPacingChange: true,
      variableElements: ['diagram_style', 'highlight_color', 'text_size']
    }
  },
  
  {
    id: 'corporate-professional',
    name: 'Corporate Professional',
    description: 'Professional, trustworthy style for business communications',
    category: 'corporate',
    
    visual: {
      colorPalette: ['#1f4e79', '#2e74b5', '#70ad47', '#ffc000', '#7030a0'],
      mood: 'professional and trustworthy',
      lighting: 'professional office lighting',
      composition: 'balanced corporate framing',
      cameraStyle: 'stable, professional camera work',
      postProcessing: ['professional_grade', 'brand_consistent', 'corporate_polish']
    },
    
    audio: {
      musicGenre: 'corporate background',
      mood: 'professional and inspiring',
      tempo: 'medium',
      instruments: ['piano', 'strings', 'light_brass', 'subtle_percussion'],
      effects: ['professional_mix', 'clarity_focus']
    },
    
    pacing: {
      rhythm: 'medium',
      transitionStyle: 'professional_dissolve',
      cutFrequency: 'moderate',
      pauseDuration: 1.8
    },
    
    text: {
      fontFamily: 'corporate_sans',
      fontSize: 'medium',
      color: '#1f4e79',
      animation: 'professional_fade',
      position: 'center'
    },
    
    technical: {
      aspectRatio: '16:9',
      resolution: '1080p',
      framerate: 30,
      duration: 'auto'
    },
    
    prompts: {
      visualPrompt: 'corporate professional style, business presentation, executive quality',
      styleModifiers: ['boardroom ready', 'executive presentation', 'corporate branding', 'professional standards'],
      negativePrompts: ['casual', 'unprofessional', 'low quality', 'inappropriate']
    },
    
    usage: {
      popularity: 0.72,
      userRating: 4.2,
      successRate: 0.96
    },
    
    customization: {
      allowColorChange: true,
      allowMoodChange: false,
      allowPacingChange: true,
      variableElements: ['company_branding', 'logo_integration', 'brand_colors']
    }
  }
];

export class StyleTemplateManager {
  private templates: Map<string, StyleTemplate>;
  private presets: Map<string, StylePreset>;
  private userPreferences: Map<string, any>;

  constructor() {
    this.templates = new Map();
    this.presets = new Map();
    this.userPreferences = new Map();

    // Load predefined templates
    predefinedTemplates.forEach(template => {
      this.templates.set(template.id, template);
    });

    this.loadUserData();
  }

  /**
   * Get all available templates
   */
  getTemplates(category?: StyleTemplate['category']): StyleTemplate[] {
    const templates = Array.from(this.templates.values());
    
    if (category) {
      return templates.filter(template => template.category === category);
    }

    return templates.sort((a, b) => b.usage.popularity - a.usage.popularity);
  }

  /**
   * Get template by ID
   */
  getTemplate(id: string): StyleTemplate | undefined {
    return this.templates.get(id);
  }

  /**
   * Get templates recommended for specific content
   */
  getRecommendedTemplates(
    contentAnalysis: {
      mood?: string;
      purpose?: string;
      audience?: string;
      duration?: number;
    }
  ): StyleTemplate[] {
    const templates = Array.from(this.templates.values());
    
    return templates
      .map(template => ({
        template,
        score: this.calculateRecommendationScore(template, contentAnalysis)
      }))
      .filter(({ score }) => score > 0.5)
      .sort((a, b) => b.score - a.score)
      .map(({ template }) => template)
      .slice(0, 5);
  }

  /**
   * Create a custom template
   */
  createCustomTemplate(
    baseTemplateId: string,
    customizations: Partial<StyleTemplate>,
    name: string,
    description: string
  ): StyleTemplate {
    const baseTemplate = this.templates.get(baseTemplateId);
    if (!baseTemplate) {
      throw new Error('Base template not found');
    }

    const customTemplate: StyleTemplate = {
      ...baseTemplate,
      ...customizations,
      id: `custom_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      description,
      usage: {
        popularity: 0,
        userRating: 0,
        successRate: 0
      }
    };

    this.templates.set(customTemplate.id, customTemplate);
    this.saveUserData();

    return customTemplate;
  }

  /**
   * Generate style parameters for content generation
   */
  generateStyleParameters(templateId: string, options: StyleGenerationOptions): any {
    const template = this.templates.get(templateId);
    if (!template) {
      throw new Error('Template not found');
    }

    const params = {
      // Visual parameters
      visual: {
        ...template.visual,
        prompt: this.buildVisualPrompt(template, options),
        negativePrompt: template.prompts.negativePrompts.join(', ')
      },

      // Audio parameters
      audio: {
        ...template.audio,
        duration: options.content.duration || template.technical.duration
      },

      // Technical parameters
      technical: {
        ...template.technical,
        quality: options.quality
      },

      // Text styling
      text: {
        ...template.text,
        content: options.content.script
      }
    };

    // Apply customizations
    if (options.customizations) {
      this.applyCustomizations(params, options.customizations, template);
    }

    // Quality adjustments
    this.adjustForQuality(params, options.quality);

    return params;
  }

  /**
   * Save a style preset
   */
  savePreset(
    templateId: string,
    customizations: Record<string, any>,
    name: string,
    description: string,
    isPublic: boolean = false,
    tags: string[] = []
  ): StylePreset {
    const preset: StylePreset = {
      id: `preset_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      description,
      templateId,
      customizations,
      createdAt: new Date(),
      isPublic,
      tags
    };

    this.presets.set(preset.id, preset);
    this.saveUserData();

    return preset;
  }

  /**
   * Get user's saved presets
   */
  getUserPresets(): StylePreset[] {
    return Array.from(this.presets.values())
      .filter(preset => !preset.isPublic)
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  /**
   * Get public/community presets
   */
  getPublicPresets(): StylePreset[] {
    return Array.from(this.presets.values())
      .filter(preset => preset.isPublic)
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  /**
   * Apply a preset to generate parameters
   */
  applyPreset(presetId: string, options: StyleGenerationOptions): any {
    const preset = this.presets.get(presetId);
    if (!preset) {
      throw new Error('Preset not found');
    }

    return this.generateStyleParameters(preset.templateId, {
      ...options,
      customizations: preset.customizations
    });
  }

  /**
   * Record usage feedback
   */
  recordUsageFeedback(
    templateId: string,
    rating: number,
    success: boolean,
    _feedback?: string
  ): void {
    const template = this.templates.get(templateId);
    if (!template) return;

    // Update usage statistics
    template.usage.popularity = (template.usage.popularity * 0.9) + (success ? 0.1 : 0);
    template.usage.userRating = (template.usage.userRating * 0.8) + (rating * 0.2);
    template.usage.successRate = (template.usage.successRate * 0.9) + (success ? 0.1 : 0);
    template.usage.lastUsed = new Date();

    this.saveUserData();
  }

  /**
   * Get style analytics
   */
  getStyleAnalytics(): {
    popularTemplates: Array<{ template: StyleTemplate; usage: number }>;
    categoryUsage: Record<string, number>;
    averageRating: number;
    totalPresets: number;
  } {
    const templates = Array.from(this.templates.values());
    const categoryUsage: Record<string, number> = {};

    templates.forEach(template => {
      categoryUsage[template.category] = (categoryUsage[template.category] || 0) + template.usage.popularity;
    });

    const popularTemplates = templates
      .map(template => ({ template, usage: template.usage.popularity }))
      .sort((a, b) => b.usage - a.usage)
      .slice(0, 10);

    const averageRating = templates.reduce((sum, t) => sum + t.usage.userRating, 0) / templates.length;

    return {
      popularTemplates,
      categoryUsage,
      averageRating,
      totalPresets: this.presets.size
    };
  }

  private calculateRecommendationScore(
    template: StyleTemplate,
    analysis: {
      mood?: string;
      purpose?: string;
      audience?: string;
      duration?: number;
    }
  ): number {
    let score = 0.5; // Base score

    // Mood matching
    if (analysis.mood && template.visual.mood.includes(analysis.mood.toLowerCase())) {
      score += 0.3;
    }

    // Purpose/category matching
    if (analysis.purpose) {
      const purposeMap: Record<string, StyleTemplate['category'][]> = {
        marketing: ['commercial', 'social'],
        education: ['educational'],
        entertainment: ['cinematic', 'artistic'],
        business: ['corporate', 'commercial'],
        creative: ['artistic', 'cinematic']
      };

      const matchingCategories = purposeMap[analysis.purpose.toLowerCase()] || [];
      if (matchingCategories.includes(template.category)) {
        score += 0.2;
      }
    }

    // Audience matching
    if (analysis.audience) {
      const audienceBoosts: Record<string, string[]> = {
        professional: ['corporate-professional', 'educational-explainer'],
        social: ['social-media-vertical', 'modern-commercial'],
        creative: ['artistic-abstract', 'cinematic-noir']
      };

      const boostTemplates = audienceBoosts[analysis.audience.toLowerCase()] || [];
      if (boostTemplates.includes(template.id)) {
        score += 0.25;
      }
    }

    // Duration matching
    if (analysis.duration && typeof template.technical.duration === 'number') {
      const durationDiff = Math.abs(analysis.duration - template.technical.duration);
      if (durationDiff < 10) {
        score += 0.1;
      }
    }

    // Popularity boost
    score += template.usage.popularity * 0.1;

    // Success rate boost
    score += template.usage.successRate * 0.1;

    return Math.min(1.0, score);
  }

  private buildVisualPrompt(template: StyleTemplate, options: StyleGenerationOptions): string {
    let prompt = template.prompts.visualPrompt;

    // Add content-specific modifiers
    if (options.content.mood) {
      prompt += `, ${options.content.mood} mood`;
    }

    // Add style modifiers
    prompt += `, ${template.prompts.styleModifiers.join(', ')}`;

    // Add quality-specific terms
    if (options.quality === 'premium') {
      prompt += ', high quality, professional grade, cinematic';
    } else if (options.quality === 'draft') {
      prompt += ', concept art, sketch style';
    }

    return prompt;
  }

  private applyCustomizations(
    params: any,
    customizations: Record<string, any>,
    template: StyleTemplate
  ): void {
    Object.keys(customizations).forEach(key => {
      if (template.customization.variableElements.includes(key)) {
        // Apply allowed customizations
        const keyPath = key.split('.');
        let target = params;
        
        for (let i = 0; i < keyPath.length - 1; i++) {
          if (!target[keyPath[i]]) target[keyPath[i]] = {};
          target = target[keyPath[i]];
        }
        
        target[keyPath[keyPath.length - 1]] = customizations[key];
      }
    });
  }

  private adjustForQuality(params: any, quality: 'draft' | 'standard' | 'premium'): void {
    const qualityMultipliers = {
      draft: { resolution: 0.7, steps: 0.6, bitrate: 0.5 },
      standard: { resolution: 1.0, steps: 1.0, bitrate: 1.0 },
      premium: { resolution: 1.3, steps: 1.5, bitrate: 1.8 }
    };

    const multiplier = qualityMultipliers[quality];

    // Adjust technical parameters
    if (params.technical.resolution === '1080p' && quality === 'premium') {
      params.technical.resolution = '1440p';
    } else if (params.technical.resolution === '1080p' && quality === 'draft') {
      params.technical.resolution = '720p';
    }

    // Adjust other quality-dependent parameters
    if (params.visual.steps) {
      params.visual.steps = Math.round(params.visual.steps * multiplier.steps);
    }
  }

  private loadUserData(): void {
    try {
      if (typeof window !== 'undefined') {
        const templatesData = localStorage.getItem('style_templates_custom');
        const presetsData = localStorage.getItem('style_presets');
        const preferencesData = localStorage.getItem('style_preferences');

        if (templatesData) {
          const customTemplates = JSON.parse(templatesData);
          customTemplates.forEach((template: StyleTemplate) => {
            this.templates.set(template.id, template);
          });
        }

        if (presetsData) {
          const presets = JSON.parse(presetsData);
          presets.forEach((preset: StylePreset) => {
            this.presets.set(preset.id, preset);
          });
        }

        if (preferencesData) {
          const preferences = JSON.parse(preferencesData);
          Object.entries(preferences).forEach(([key, value]) => {
            this.userPreferences.set(key, value);
          });
        }
      }
    } catch (error) {
      console.warn('Failed to load style template user data:', error);
    }
  }

  private saveUserData(): void {
    try {
      if (typeof window !== 'undefined') {
        const customTemplates = Array.from(this.templates.values())
          .filter(t => t.id.startsWith('custom_'));
        
        localStorage.setItem('style_templates_custom', JSON.stringify(customTemplates));
        localStorage.setItem('style_presets', JSON.stringify(Array.from(this.presets.values())));
        localStorage.setItem('style_preferences', JSON.stringify(Object.fromEntries(this.userPreferences)));
      }
    } catch (error) {
      console.warn('Failed to save style template user data:', error);
    }
  }
}

// Export singleton instance
export const styleTemplateManager = new StyleTemplateManager();

export default styleTemplateManager;