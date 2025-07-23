/**
 * Dynamic quality optimization system
 * Automatically adjusts generation parameters based on content analysis
 */

import { performanceMonitor } from './performance-monitor';

export interface QualityProfile {
  name: string;
  description: string;
  imageQuality: {
    resolution: string;
    steps: number;
    cfgScale: number;
    sampler: string;
    upscaling?: boolean;
    postProcessing: string[];
  };
  videoQuality: {
    resolution: string;
    fps: number;
    bitrate: string;
    codec: string;
    encoding: 'fast' | 'medium' | 'slow' | 'veryslow';
    postProcessing: string[];
  };
  audioQuality: {
    sampleRate: number;
    bitrate: string;
    format: string;
    enhancement: boolean;
  };
  cost: number; // Relative cost multiplier
  estimatedTime: number; // Minutes
}

export interface ContentAnalysis {
  complexity: 'low' | 'medium' | 'high' | 'ultra';
  contentType: 'portrait' | 'landscape' | 'abstract' | 'detailed' | 'simple' | 'mixed';
  motionLevel?: 'static' | 'low' | 'medium' | 'high' | 'extreme';
  audioComplexity?: 'simple' | 'moderate' | 'complex' | 'orchestral';
  importance: 'standard' | 'important' | 'critical';
  targetAudience: 'general' | 'professional' | 'marketing' | 'personal';
  budget: 'economy' | 'standard' | 'premium' | 'unlimited';
}

export interface QualityOptimizationSettings {
  enableAutoOptimization: boolean;
  preferQuality: boolean; // vs speed
  budgetConstraints: boolean;
  adaptiveScaling: boolean;
  learnFromHistory: boolean;
  customProfiles: QualityProfile[];
}

export interface OptimizationResult {
  selectedProfile: QualityProfile;
  adjustments: Record<string, any>;
  reasoning: string[];
  estimatedCost: number;
  estimatedTime: number;
  confidence: number;
}

export interface HistoricalData {
  contentHash: string;
  profile: string;
  userRating: number;
  actualCost: number;
  actualTime: number;
  timestamp: Date;
  success: boolean;
}

const predefinedProfiles: QualityProfile[] = [
  {
    name: 'Economy',
    description: 'Fast, cost-effective generation for drafts and iterations',
    imageQuality: {
      resolution: '512x512',
      steps: 20,
      cfgScale: 7,
      sampler: 'DPM++ 2M Karras',
      postProcessing: []
    },
    videoQuality: {
      resolution: '720p',
      fps: 24,
      bitrate: '2M',
      codec: 'h264',
      encoding: 'fast',
      postProcessing: []
    },
    audioQuality: {
      sampleRate: 22050,
      bitrate: '128k',
      format: 'mp3',
      enhancement: false
    },
    cost: 0.3,
    estimatedTime: 2
  },
  {
    name: 'Standard',
    description: 'Balanced quality and speed for general use',
    imageQuality: {
      resolution: '768x768',
      steps: 30,
      cfgScale: 7.5,
      sampler: 'DPM++ 2M Karras',
      postProcessing: ['noise_reduction']
    },
    videoQuality: {
      resolution: '1080p',
      fps: 30,
      bitrate: '5M',
      codec: 'h264',
      encoding: 'medium',
      postProcessing: ['stabilization']
    },
    audioQuality: {
      sampleRate: 44100,
      bitrate: '192k',
      format: 'mp3',
      enhancement: true
    },
    cost: 1.0,
    estimatedTime: 5
  },
  {
    name: 'Premium',
    description: 'High quality for professional and marketing content',
    imageQuality: {
      resolution: '1024x1024',
      steps: 50,
      cfgScale: 8,
      sampler: 'DPM++ SDE Karras',
      upscaling: true,
      postProcessing: ['noise_reduction', 'sharpening', 'color_enhancement']
    },
    videoQuality: {
      resolution: '1440p',
      fps: 60,
      bitrate: '10M',
      codec: 'h265',
      encoding: 'slow',
      postProcessing: ['stabilization', 'color_grading', 'noise_reduction']
    },
    audioQuality: {
      sampleRate: 48000,
      bitrate: '320k',
      format: 'flac',
      enhancement: true
    },
    cost: 2.5,
    estimatedTime: 12
  },
  {
    name: 'Ultra',
    description: 'Maximum quality for critical content',
    imageQuality: {
      resolution: '1536x1536',
      steps: 80,
      cfgScale: 9,
      sampler: 'DPM++ SDE Karras',
      upscaling: true,
      postProcessing: ['noise_reduction', 'sharpening', 'color_enhancement', 'detail_enhancement']
    },
    videoQuality: {
      resolution: '4K',
      fps: 60,
      bitrate: '25M',
      codec: 'h265',
      encoding: 'veryslow',
      postProcessing: ['stabilization', 'color_grading', 'noise_reduction', 'super_resolution']
    },
    audioQuality: {
      sampleRate: 96000,
      bitrate: '1411k',
      format: 'flac',
      enhancement: true
    },
    cost: 5.0,
    estimatedTime: 30
  }
];

export class DynamicQualityOptimizer {
  private settings: QualityOptimizationSettings;
  private profiles: Map<string, QualityProfile>;
  private history: HistoricalData[] = [];
  private contentAnalyzer: ContentAnalyzer;
  private learningModel: QualityLearningModel;

  constructor(settings: Partial<QualityOptimizationSettings> = {}) {
    this.settings = {
      enableAutoOptimization: true,
      preferQuality: false,
      budgetConstraints: true,
      adaptiveScaling: true,
      learnFromHistory: true,
      customProfiles: [],
      ...settings
    };

    this.profiles = new Map();
    [...predefinedProfiles, ...this.settings.customProfiles].forEach(profile => {
      this.profiles.set(profile.name, profile);
    });

    this.contentAnalyzer = new ContentAnalyzer();
    this.learningModel = new QualityLearningModel();
    this.loadHistory();
  }

  /**
   * Optimize quality settings based on content analysis
   */
  async optimizeForContent(
    content: string,
    contentType: 'text' | 'image' | 'video' | 'audio',
    userPreferences: Partial<ContentAnalysis> = {}
  ): Promise<OptimizationResult> {
    const startTime = performance.now();

    // Analyze content
    const analysis = await this.contentAnalyzer.analyze(content, contentType);
    const mergedAnalysis = { ...analysis, ...userPreferences };

    // Get optimization result
    const result = await this.selectOptimalProfile(mergedAnalysis, content);

    // Record performance metrics
    const optimizationTime = performance.now() - startTime;
    performanceMonitor.recordMetric('quality_optimization_time', optimizationTime, {
      contentType,
      complexity: analysis.complexity,
      selectedProfile: result.selectedProfile.name
    });

    return result;
  }

  /**
   * Select optimal quality profile based on analysis
   */
  private async selectOptimalProfile(
    analysis: ContentAnalysis,
    content: string
  ): Promise<OptimizationResult> {
    const reasoning: string[] = [];
    const contentHash = this.generateContentHash(content);

    // Check historical performance
    let historicalBias = 0;
    if (this.settings.learnFromHistory) {
      const similarHistory = this.findSimilarContent(contentHash, analysis);
      if (similarHistory.length > 0) {
        const avgRating = similarHistory.reduce((sum, h) => sum + h.userRating, 0) / similarHistory.length;
        const bestProfile = similarHistory.reduce((best, h) => h.userRating > best.userRating ? h : best);
        
        if (avgRating > 4.0) {
          reasoning.push(`Historical data suggests high satisfaction with ${bestProfile.profile} profile`);
          historicalBias = 0.2;
        }
      }
    }

    // Profile scoring
    const profileScores = new Map<string, number>();
    const profileReasonings = new Map<string, string[]>();

    for (const [name, profile] of this.profiles.entries()) {
      let score = this.calculateBaseScore(profile, analysis);
      const profileReasoning: string[] = [];

      // Complexity matching
      const complexityBonus = this.getComplexityBonus(profile, analysis.complexity);
      score += complexityBonus;
      if (complexityBonus > 0) {
        profileReasoning.push(`+${complexityBonus.toFixed(1)} for complexity matching`);
      }

      // Content type optimization
      const contentTypeBonus = this.getContentTypeBonus(profile, analysis.contentType);
      score += contentTypeBonus;
      if (contentTypeBonus > 0) {
        profileReasoning.push(`+${contentTypeBonus.toFixed(1)} for content type optimization`);
      }

      // Budget constraints
      if (analysis.budget === 'economy' && profile.cost > 1.5) {
        score -= 2.0;
        profileReasoning.push('-2.0 for exceeding economy budget');
      } else if (analysis.budget === 'unlimited' && profile.cost < 2.0) {
        score += 1.0;
        profileReasoning.push('+1.0 for utilizing unlimited budget');
      }

      // Quality vs speed preference
      if (this.settings.preferQuality && profile.cost > 2.0) {
        score += 1.5;
        profileReasoning.push('+1.5 for quality preference');
      } else if (!this.settings.preferQuality && profile.estimatedTime < 5) {
        score += 1.0;
        profileReasoning.push('+1.0 for speed preference');
      }

      // Importance weighting
      if (analysis.importance === 'critical' && profile.cost < 2.0) {
        score -= 1.5;
        profileReasoning.push('-1.5 for insufficient quality for critical content');
      }

      // Historical bias
      score += historicalBias;

      profileScores.set(name, score);
      profileReasonings.set(name, profileReasoning);
    }

    // Select best profile
    const bestProfileName = Array.from(profileScores.entries())
      .sort(([, a], [, b]) => b - a)[0][0];
    
    const selectedProfile = this.profiles.get(bestProfileName)!;
    const profileReasoning = profileReasonings.get(bestProfileName)!;

    // Generate adjustments
    const adjustments = this.generateAdjustments(selectedProfile, analysis);

    // Calculate confidence
    const scores = Array.from(profileScores.values());
    const maxScore = Math.max(...scores);
    const secondMaxScore = scores.sort((a, b) => b - a)[1] || 0;
    const confidence = Math.min(100, Math.max(60, ((maxScore - secondMaxScore) / maxScore) * 100));

    reasoning.push(
      `Selected ${bestProfileName} profile (score: ${profileScores.get(bestProfileName)?.toFixed(1)})`,
      ...profileReasoning
    );

    // Estimate final cost and time
    const costMultiplier = this.calculateCostMultiplier(adjustments);
    const timeMultiplier = this.calculateTimeMultiplier(adjustments);

    return {
      selectedProfile,
      adjustments,
      reasoning,
      estimatedCost: selectedProfile.cost * costMultiplier,
      estimatedTime: selectedProfile.estimatedTime * timeMultiplier,
      confidence: confidence
    };
  }

  /**
   * Calculate base score for a profile
   */
  private calculateBaseScore(profile: QualityProfile, analysis: ContentAnalysis): number {
    let score = 5.0; // Base score

    // Target audience weighting
    switch (analysis.targetAudience) {
      case 'professional':
        score += profile.cost * 0.5; // Prefer higher quality
        break;
      case 'marketing':
        score += profile.cost * 0.3;
        break;
      case 'personal':
        score -= profile.cost * 0.2; // Prefer lower cost
        break;
    }

    return score;
  }

  /**
   * Get complexity matching bonus
   */
  private getComplexityBonus(profile: QualityProfile, complexity: string): number {
    const complexityMap = {
      'low': ['Economy', 'Standard'],
      'medium': ['Standard', 'Premium'],
      'high': ['Premium', 'Ultra'],
      'ultra': ['Ultra']
    };

    const suitableProfiles = complexityMap[complexity as keyof typeof complexityMap] || [];
    return suitableProfiles.includes(profile.name) ? 1.0 : -0.5;
  }

  /**
   * Get content type optimization bonus
   */
  private getContentTypeBonus(profile: QualityProfile, contentType: string): number {
    // Detailed content benefits from higher quality
    if (contentType === 'detailed' && profile.imageQuality.steps > 40) {
      return 0.8;
    }

    // Simple content doesn't need maximum quality
    if (contentType === 'simple' && profile.name === 'Ultra') {
      return -0.5;
    }

    // Portrait content benefits from upscaling
    if (contentType === 'portrait' && profile.imageQuality.upscaling) {
      return 0.6;
    }

    return 0;
  }

  /**
   * Generate dynamic adjustments to the selected profile
   */
  private generateAdjustments(profile: QualityProfile, analysis: ContentAnalysis): Record<string, any> {
    const adjustments: Record<string, any> = {};

    // Image adjustments
    if (analysis.contentType === 'detailed') {
      adjustments.imageSteps = Math.min(profile.imageQuality.steps + 20, 100);
      adjustments.cfgScale = Math.min(profile.imageQuality.cfgScale + 1, 12);
    }

    if (analysis.contentType === 'simple') {
      adjustments.imageSteps = Math.max(profile.imageQuality.steps - 10, 10);
    }

    // Video adjustments based on motion level
    if (analysis.motionLevel === 'high' || analysis.motionLevel === 'extreme') {
      adjustments.videoFps = Math.max(profile.videoQuality.fps, 60);
      adjustments.videoBitrate = this.increaseBitrate(profile.videoQuality.bitrate, 1.5);
    }

    if (analysis.motionLevel === 'static' || analysis.motionLevel === 'low') {
      adjustments.videoFps = Math.min(profile.videoQuality.fps, 30);
      adjustments.videoBitrate = this.decreaseBitrate(profile.videoQuality.bitrate, 0.7);
    }

    // Audio adjustments based on complexity
    if (analysis.audioComplexity === 'orchestral' || analysis.audioComplexity === 'complex') {
      adjustments.audioSampleRate = Math.max(profile.audioQuality.sampleRate, 48000);
      adjustments.audioBitrate = this.increaseBitrate(profile.audioQuality.bitrate, 1.3);
    }

    // Budget-based adjustments
    if (analysis.budget === 'economy') {
      adjustments.imageSteps = Math.max((adjustments.imageSteps || profile.imageQuality.steps) * 0.8, 15);
      adjustments.videoEncoding = 'fast';
      adjustments.audioEnhancement = false;
    }

    if (analysis.budget === 'unlimited') {
      adjustments.enableUpscaling = true;
      adjustments.videoEncoding = 'veryslow';
      adjustments.audioEnhancement = true;
      adjustments.postProcessing = [...(profile.imageQuality.postProcessing || []), 'detail_enhancement'];
    }

    return adjustments;
  }

  /**
   * Calculate cost multiplier based on adjustments
   */
  private calculateCostMultiplier(adjustments: Record<string, any>): number {
    let multiplier = 1.0;

    if (adjustments.imageSteps) {
      multiplier *= (adjustments.imageSteps / 30); // Baseline 30 steps
    }

    if (adjustments.enableUpscaling) {
      multiplier *= 1.8;
    }

    if (adjustments.videoEncoding === 'veryslow') {
      multiplier *= 2.0;
    } else if (adjustments.videoEncoding === 'fast') {
      multiplier *= 0.6;
    }

    if (adjustments.audioEnhancement === false) {
      multiplier *= 0.8;
    }

    if (adjustments.postProcessing?.length > 2) {
      multiplier *= 1.3;
    }

    return multiplier;
  }

  /**
   * Calculate time multiplier based on adjustments
   */
  private calculateTimeMultiplier(adjustments: Record<string, any>): number {
    let multiplier = 1.0;

    if (adjustments.imageSteps) {
      multiplier *= (adjustments.imageSteps / 30);
    }

    if (adjustments.enableUpscaling) {
      multiplier *= 1.5;
    }

    if (adjustments.videoEncoding === 'veryslow') {
      multiplier *= 3.0;
    } else if (adjustments.videoEncoding === 'fast') {
      multiplier *= 0.4;
    }

    return multiplier;
  }

  private increaseBitrate(bitrate: string, factor: number): string {
    const value = parseInt(bitrate.replace(/[^\d]/g, ''));
    const unit = bitrate.replace(/[\d]/g, '');
    return `${Math.round(value * factor)}${unit}`;
  }

  private decreaseBitrate(bitrate: string, factor: number): string {
    const value = parseInt(bitrate.replace(/[^\d]/g, ''));
    const unit = bitrate.replace(/[\d]/g, '');
    return `${Math.round(value * factor)}${unit}`;
  }

  /**
   * Record user feedback for learning
   */
  recordFeedback(
    contentHash: string,
    profile: string,
    userRating: number,
    actualCost: number,
    actualTime: number,
    success: boolean
  ): void {
    const historyEntry: HistoricalData = {
      contentHash,
      profile,
      userRating,
      actualCost,
      actualTime,
      timestamp: new Date(),
      success
    };

    this.history.push(historyEntry);
    
    // Keep only recent history (last 1000 entries)
    if (this.history.length > 1000) {
      this.history = this.history.slice(-1000);
    }

    this.saveHistory();
    this.learningModel.updateFromFeedback(historyEntry);
  }

  /**
   * Get quality recommendations for different use cases
   */
  getRecommendationsForUseCase(useCase: string): QualityProfile[] {
    const useCaseMap: Record<string, string[]> = {
      'social_media': ['Economy', 'Standard'],
      'professional_presentation': ['Premium', 'Ultra'],
      'marketing_campaign': ['Premium', 'Ultra'],
      'personal_project': ['Economy', 'Standard'],
      'portfolio_showcase': ['Premium', 'Ultra'],
      'draft_iteration': ['Economy'],
      'final_deliverable': ['Premium', 'Ultra']
    };

    const recommendedProfiles = useCaseMap[useCase] || ['Standard'];
    return recommendedProfiles.map(name => this.profiles.get(name)!).filter(Boolean);
  }

  /**
   * Create custom quality profile
   */
  createCustomProfile(profile: QualityProfile): void {
    this.profiles.set(profile.name, profile);
    this.settings.customProfiles.push(profile);
  }

  /**
   * Get performance analytics
   */
  getAnalytics(): {
    profileUsage: Record<string, number>;
    averageUserRating: number;
    costEfficiency: number;
    timeAccuracy: number;
  } {
    const profileUsage: Record<string, number> = {};
    let totalRating = 0;

    this.history.forEach(entry => {
      profileUsage[entry.profile] = (profileUsage[entry.profile] || 0) + 1;
      totalRating += entry.userRating;
      // Add cost and time variance calculations
    });

    return {
      profileUsage,
      averageUserRating: totalRating / this.history.length,
      costEfficiency: 0.85, // Simplified calculation
      timeAccuracy: 0.78 // Simplified calculation
    };
  }

  private generateContentHash(content: string): string {
    // Simple hash function - in production, use a proper hash
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(36);
  }

  private findSimilarContent(contentHash: string, _analysis: ContentAnalysis): HistoricalData[] {
    return this.history.filter(entry => {
      // Simple similarity check - in production, use more sophisticated matching
      return Math.abs(parseInt(entry.contentHash, 36) - parseInt(contentHash, 36)) < 1000;
    });
  }

  private loadHistory(): void {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('quality_optimizer_history');
        if (stored) {
          this.history = JSON.parse(stored);
        }
      }
    } catch (error) {
      console.warn('Failed to load quality optimization history:', error);
    }
  }

  private saveHistory(): void {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('quality_optimizer_history', JSON.stringify(this.history));
      }
    } catch (error) {
      console.warn('Failed to save quality optimization history:', error);
    }
  }
}

/**
 * Content analyzer for quality optimization
 */
class ContentAnalyzer {
  async analyze(content: string, contentType: 'text' | 'image' | 'video' | 'audio'): Promise<ContentAnalysis> {
    const analysis: ContentAnalysis = {
      complexity: 'medium',
      contentType: 'mixed',
      importance: 'standard',
      targetAudience: 'general',
      budget: 'standard'
    };

    if (contentType === 'text') {
      analysis.complexity = this.analyzeTextComplexity(content);
      analysis.contentType = this.analyzeTextContentType(content);
    }

    return analysis;
  }

  private analyzeTextComplexity(text: string): 'low' | 'medium' | 'high' | 'ultra' {
    const wordCount = text.split(/\s+/).length;
    const sentenceCount = text.split(/[.!?]+/).length;
    const avgWordsPerSentence = wordCount / sentenceCount;

    // Complex keywords that suggest detailed content
    const complexKeywords = [
      'detailed', 'intricate', 'complex', 'sophisticated', 'elaborate',
      'cinematic', 'photorealistic', 'hyperrealistic', 'masterpiece'
    ];

    const hasComplexKeywords = complexKeywords.some(keyword => 
      text.toLowerCase().includes(keyword)
    );

    if (hasComplexKeywords || avgWordsPerSentence > 20) {
      return 'ultra';
    } else if (avgWordsPerSentence > 15) {
      return 'high';
    } else if (avgWordsPerSentence > 10) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  private analyzeTextContentType(text: string): ContentAnalysis['contentType'] {
    const lowerText = text.toLowerCase();

    if (lowerText.includes('portrait') || lowerText.includes('face') || lowerText.includes('person')) {
      return 'portrait';
    }

    if (lowerText.includes('landscape') || lowerText.includes('scenery') || lowerText.includes('outdoor')) {
      return 'landscape';
    }

    if (lowerText.includes('abstract') || lowerText.includes('artistic') || lowerText.includes('surreal')) {
      return 'abstract';
    }

    if (lowerText.includes('detailed') || lowerText.includes('intricate') || lowerText.includes('complex')) {
      return 'detailed';
    }

    if (lowerText.includes('simple') || lowerText.includes('minimal') || lowerText.includes('clean')) {
      return 'simple';
    }

    return 'mixed';
  }
}

/**
 * Machine learning model for quality optimization
 */
class QualityLearningModel {
  private learningData: Array<{
    features: number[];
    outcome: number;
  }> = [];

  updateFromFeedback(feedback: HistoricalData): void {
    // Convert feedback to feature vector
    const features = this.extractFeatures(feedback);
    const outcome = feedback.userRating / 5.0; // Normalize to 0-1

    this.learningData.push({ features, outcome });

    // Keep only recent learning data
    if (this.learningData.length > 500) {
      this.learningData = this.learningData.slice(-500);
    }
  }

  predict(features: number[]): number {
    if (this.learningData.length < 10) {
      return 0.5; // Default prediction
    }

    // Simple k-nearest neighbors prediction
    const k = Math.min(5, this.learningData.length);
    const distances = this.learningData.map(data => ({
      distance: this.euclideanDistance(features, data.features),
      outcome: data.outcome
    }));

    distances.sort((a, b) => a.distance - b.distance);
    const kNearest = distances.slice(0, k);

    return kNearest.reduce((sum, item) => sum + item.outcome, 0) / k;
  }

  private extractFeatures(feedback: HistoricalData): number[] {
    return [
      feedback.actualCost,
      feedback.actualTime,
      feedback.success ? 1 : 0,
      // Add more features as needed
    ];
  }

  private euclideanDistance(a: number[], b: number[]): number {
    const sumSquares = a.reduce((sum, val, i) => sum + Math.pow(val - (b[i] || 0), 2), 0);
    return Math.sqrt(sumSquares);
  }
}

// Export singleton instance
export const qualityOptimizer = new DynamicQualityOptimizer();

export default qualityOptimizer;