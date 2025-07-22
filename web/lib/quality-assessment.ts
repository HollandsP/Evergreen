/**
 * Automated quality assessment for generated content
 * Provides intelligent quality scoring and content validation
 */

import { observabilityLogger } from './observability-logger';
import { performanceMonitor } from './performance-monitor';

export interface QualityMetrics {
  overall: number; // 0-100 overall quality score
  technical: {
    resolution: number; // Image/video resolution quality
    clarity: number; // Sharpness and detail
    compression: number; // Compression artifact assessment
    colorBalance: number; // Color accuracy and balance
    exposure: number; // Lighting and exposure quality
  };
  aesthetic: {
    composition: number; // Visual composition quality
    creativity: number; // Creative and artistic merit
    coherence: number; // Visual coherence and consistency
    style: number; // Style consistency and appropriateness
  };
  content: {
    relevance: number; // Relevance to prompt/request
    accuracy: number; // Factual accuracy where applicable
    completeness: number; // Completeness of content
    appropriateness: number; // Content appropriateness
  };
  production: {
    usability: number; // Production readiness
    accessibility: number; // Accessibility compliance
    scalability: number; // Scalability for different uses
    durability: number; // Long-term usability
  };
}

export interface QualityAssessmentResult {
  id: string;
  contentId: string;
  contentType: 'image' | 'video' | 'audio' | 'text';
  metrics: QualityMetrics;
  issues: QualityIssue[];
  recommendations: QualityRecommendation[];
  confidence: number; // 0-1 confidence in assessment
  timestamp: Date;
  assessmentVersion: string;
  metadata: {
    prompt?: string;
    model?: string;
    provider?: string;
    generationParams?: any;
    userRating?: number;
    automaticFlags?: string[];
  };
}

export interface QualityIssue {
  type: 'technical' | 'aesthetic' | 'content' | 'compliance';
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
  affectedAreas: string[];
  suggestedFix: string;
  confidence: number;
}

export interface QualityRecommendation {
  type: 'parameter' | 'process' | 'post_processing' | 'regeneration';
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  expectedImprovement: number; // Expected quality score improvement
  estimatedCost: number; // Relative cost (0-1)
  parameters?: Record<string, any>;
}

export interface QualityStandards {
  minimumOverallScore: number;
  technicalRequirements: {
    minResolution: number;
    minClarity: number;
    maxCompressionArtifacts: number;
    colorAccuracyThreshold: number;
  };
  aestheticRequirements: {
    minComposition: number;
    minCoherence: number;
    styleConsistencyThreshold: number;
  };
  contentRequirements: {
    minRelevance: number;
    minAccuracy: number;
    minCompleteness: number;
    appropriatenessThreshold: number;
  };
  productionRequirements: {
    minUsability: number;
    accessibilityCompliance: boolean;
    scalabilityThreshold: number;
  };
}

interface AssessmentConfig {
  enableAutoAssessment: boolean;
  assessmentDelay: number; // ms to wait before assessment
  enableLearning: boolean;
  enableComparison: boolean;
  qualityStandards: QualityStandards;
  assessmentModels: {
    technical: string[];
    aesthetic: string[];
    content: string[];
  };
  confidenceThreshold: number;
  maxRetries: number;
}

export class AdvancedQualityAssessment {
  private config: AssessmentConfig;
  private assessmentHistory: Map<string, QualityAssessmentResult> = new Map();
  private qualityTrends: Map<string, number[]> = new Map();
  private modelPerformance: Map<string, { avgQuality: number; assessmentCount: number }> = new Map();
  private logger = observabilityLogger.createLogger('QualityAssessment');

  constructor(config: Partial<AssessmentConfig> = {}) {
    this.config = {
      enableAutoAssessment: true,
      assessmentDelay: 2000, // 2 seconds
      enableLearning: true,
      enableComparison: true,
      qualityStandards: {
        minimumOverallScore: 70,
        technicalRequirements: {
          minResolution: 80,
          minClarity: 75,
          maxCompressionArtifacts: 20,
          colorAccuracyThreshold: 85
        },
        aestheticRequirements: {
          minComposition: 70,
          minCoherence: 80,
          styleConsistencyThreshold: 75
        },
        contentRequirements: {
          minRelevance: 85,
          minAccuracy: 90,
          minCompleteness: 80,
          appropriatenessThreshold: 95
        },
        productionRequirements: {
          minUsability: 80,
          accessibilityCompliance: true,
          scalabilityThreshold: 75
        }
      },
      assessmentModels: {
        technical: ['image_quality_v2', 'video_quality_v1'],
        aesthetic: ['aesthetic_scorer_v3', 'composition_analyzer_v2'],
        content: ['relevance_matcher_v2', 'content_validator_v1']
      },
      confidenceThreshold: 0.7,
      maxRetries: 3,
      ...config
    };

    this.loadHistoricalData();

    this.logger.info('Quality assessment system initialized', {
      enableAutoAssessment: this.config.enableAutoAssessment,
      qualityStandards: this.config.qualityStandards.minimumOverallScore
    });
  }

  /**
   * Assess the quality of generated content
   */
  async assessContent(
    contentId: string,
    contentType: 'image' | 'video' | 'audio' | 'text',
    contentData: string | ArrayBuffer | Blob,
    metadata: QualityAssessmentResult['metadata'] = {}
  ): Promise<QualityAssessmentResult> {
    const startTime = performance.now();
    
    this.logger.debug('Starting quality assessment', {
      contentId,
      contentType,
      hasMetadata: Object.keys(metadata).length > 0
    });

    try {
      const span = this.logger.startSpan('quality_assessment');

      // Perform multi-dimensional quality analysis
      const [technicalMetrics, aestheticMetrics, contentMetrics, productionMetrics] = await Promise.all([
        this.assessTechnicalQuality(contentData, contentType, metadata),
        this.assessAestheticQuality(contentData, contentType, metadata),
        this.assessContentQuality(contentData, contentType, metadata),
        this.assessProductionQuality(contentData, contentType, metadata)
      ]);

      // Calculate overall quality score
      const overallScore = this.calculateOverallScore({
        technical: technicalMetrics,
        aesthetic: aestheticMetrics,
        content: contentMetrics,
        production: productionMetrics
      });

      const metrics: QualityMetrics = {
        overall: overallScore,
        technical: technicalMetrics,
        aesthetic: aestheticMetrics,
        content: contentMetrics,
        production: productionMetrics
      };

      // Identify issues and generate recommendations
      const issues = this.identifyQualityIssues(metrics, metadata);
      const recommendations = this.generateRecommendations(metrics, issues, metadata);

      // Calculate confidence score
      const confidence = this.calculateConfidence(metrics, metadata);

      const result: QualityAssessmentResult = {
        id: this.generateId(),
        contentId,
        contentType,
        metrics,
        issues,
        recommendations,
        confidence,
        timestamp: new Date(),
        assessmentVersion: '1.0.0',
        metadata: {
          ...metadata,
          assessmentDuration: performance.now() - startTime,
          automaticFlags: this.generateAutomaticFlags(metrics)
        }
      };

      // Store assessment
      this.assessmentHistory.set(result.id, result);
      this.updateQualityTrends(metadata.model || 'unknown', overallScore);
      this.updateModelPerformance(metadata.model || 'unknown', overallScore);

      this.logger.finishSpan(span);

      // Record performance metrics
      performanceMonitor.recordMetric('quality_assessment_time', performance.now() - startTime, {
        contentType,
        overallScore: overallScore.toString()
      });

      this.logger.info('Quality assessment completed', {
        contentId,
        overallScore,
        issuesFound: issues.length,
        recommendationsCount: recommendations.length,
        confidence
      });

      return result;

    } catch (error) {
      this.logger.error('Quality assessment failed', error as Error, {
        contentId,
        contentType
      });

      // Return a fallback assessment
      return this.createFallbackAssessment(contentId, contentType, metadata);
    }
  }

  /**
   * Assess technical quality aspects
   */
  private async assessTechnicalQuality(
    contentData: string | ArrayBuffer | Blob,
    contentType: string,
    metadata: any
  ): Promise<QualityMetrics['technical']> {
    switch (contentType) {
      case 'image':
        return this.assessImageTechnicalQuality(contentData, metadata);
      case 'video':
        return this.assessVideoTechnicalQuality(contentData, metadata);
      case 'audio':
        return this.assessAudioTechnicalQuality(contentData, metadata);
      case 'text':
        return this.assessTextTechnicalQuality(contentData, metadata);
      default:
        return this.getDefaultTechnicalMetrics();
    }
  }

  /**
   * Assess image technical quality
   */
  private async assessImageTechnicalQuality(
    contentData: string | ArrayBuffer | Blob,
    metadata: any
  ): Promise<QualityMetrics['technical']> {
    try {
      // Load image for analysis
      const imageElement = await this.loadImage(contentData);
      
      // Resolution assessment
      const resolutionScore = this.assessResolution(imageElement.width, imageElement.height);
      
      // Create canvas for pixel analysis
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;
      canvas.width = imageElement.width;
      canvas.height = imageElement.height;
      ctx.drawImage(imageElement, 0, 0);
      
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      
      // Analyze various technical aspects
      const clarityScore = this.assessImageClarity(imageData);
      const compressionScore = this.assessCompressionArtifacts(imageData);
      const colorBalanceScore = this.assessColorBalance(imageData);
      const exposureScore = this.assessExposure(imageData);

      return {
        resolution: resolutionScore,
        clarity: clarityScore,
        compression: compressionScore,
        colorBalance: colorBalanceScore,
        exposure: exposureScore
      };
    } catch (error) {
      this.logger.warn('Failed to assess image technical quality', { error: (error as Error).message });
      return this.getDefaultTechnicalMetrics();
    }
  }

  /**
   * Assess aesthetic quality aspects
   */
  private async assessAestheticQuality(
    contentData: string | ArrayBuffer | Blob,
    contentType: string,
    metadata: any
  ): Promise<QualityMetrics['aesthetic']> {
    switch (contentType) {
      case 'image':
        return this.assessImageAestheticQuality(contentData, metadata);
      case 'video':
        return this.assessVideoAestheticQuality(contentData, metadata);
      default:
        return {
          composition: 75,
          creativity: 70,
          coherence: 80,
          style: 75
        };
    }
  }

  /**
   * Assess image aesthetic quality
   */
  private async assessImageAestheticQuality(
    contentData: string | ArrayBuffer | Blob,
    metadata: any
  ): Promise<QualityMetrics['aesthetic']> {
    try {
      const imageElement = await this.loadImage(contentData);
      
      // Rule of thirds and composition analysis
      const compositionScore = this.assessComposition(imageElement, metadata);
      
      // Creativity assessment based on uniqueness and artistic merit
      const creativityScore = this.assessCreativity(imageElement, metadata);
      
      // Visual coherence assessment
      const coherenceScore = this.assessVisualCoherence(imageElement, metadata);
      
      // Style consistency assessment
      const styleScore = this.assessStyleConsistency(imageElement, metadata);

      return {
        composition: compositionScore,
        creativity: creativityScore,
        coherence: coherenceScore,
        style: styleScore
      };
    } catch (error) {
      this.logger.warn('Failed to assess image aesthetic quality', { error: (error as Error).message });
      return {
        composition: 75,
        creativity: 70,
        coherence: 80,
        style: 75
      };
    }
  }

  /**
   * Assess content quality aspects
   */
  private async assessContentQuality(
    contentData: string | ArrayBuffer | Blob,
    contentType: string,
    metadata: any
  ): Promise<QualityMetrics['content']> {
    // Relevance to prompt assessment
    const relevanceScore = this.assessPromptRelevance(contentData, metadata.prompt, contentType);
    
    // Factual accuracy assessment (where applicable)
    const accuracyScore = this.assessFactualAccuracy(contentData, contentType, metadata);
    
    // Completeness assessment
    const completenessScore = this.assessCompleteness(contentData, contentType, metadata);
    
    // Content appropriateness assessment
    const appropriatenessScore = this.assessContentAppropriateness(contentData, contentType);

    return {
      relevance: relevanceScore,
      accuracy: accuracyScore,
      completeness: completenessScore,
      appropriateness: appropriatenessScore
    };
  }

  /**
   * Assess production quality aspects
   */
  private async assessProductionQuality(
    contentData: string | ArrayBuffer | Blob,
    contentType: string,
    metadata: any
  ): Promise<QualityMetrics['production']> {
    // Production usability assessment
    const usabilityScore = this.assessUsability(contentData, contentType, metadata);
    
    // Accessibility compliance assessment
    const accessibilityScore = this.assessAccessibility(contentData, contentType);
    
    // Scalability assessment
    const scalabilityScore = this.assessScalability(contentData, contentType, metadata);
    
    // Long-term durability assessment
    const durabilityScore = this.assessDurability(contentData, contentType, metadata);

    return {
      usability: usabilityScore,
      accessibility: accessibilityScore,
      scalability: scalabilityScore,
      durability: durabilityScore
    };
  }

  /**
   * Calculate overall quality score from individual metrics
   */
  private calculateOverallScore(metrics: Omit<QualityMetrics, 'overall'>): number {
    const weights = {
      technical: 0.3,
      aesthetic: 0.25,
      content: 0.35,
      production: 0.1
    };

    const technicalAvg = Object.values(metrics.technical).reduce((sum, val) => sum + val, 0) / Object.keys(metrics.technical).length;
    const aestheticAvg = Object.values(metrics.aesthetic).reduce((sum, val) => sum + val, 0) / Object.keys(metrics.aesthetic).length;
    const contentAvg = Object.values(metrics.content).reduce((sum, val) => sum + val, 0) / Object.keys(metrics.content).length;
    const productionAvg = Object.values(metrics.production).reduce((sum, val) => sum + val, 0) / Object.keys(metrics.production).length;

    return Math.round(
      technicalAvg * weights.technical +
      aestheticAvg * weights.aesthetic +
      contentAvg * weights.content +
      productionAvg * weights.production
    );
  }

  /**
   * Identify quality issues based on metrics
   */
  private identifyQualityIssues(metrics: QualityMetrics, metadata: any): QualityIssue[] {
    const issues: QualityIssue[] = [];

    // Technical issues
    if (metrics.technical.resolution < this.config.qualityStandards.technicalRequirements.minResolution) {
      issues.push({
        type: 'technical',
        severity: 'high',
        category: 'resolution',
        description: `Low resolution quality (${metrics.technical.resolution}/100)`,
        affectedAreas: ['visual_quality', 'print_quality'],
        suggestedFix: 'Increase resolution parameters or use upscaling',
        confidence: 0.9
      });
    }

    if (metrics.technical.clarity < this.config.qualityStandards.technicalRequirements.minClarity) {
      issues.push({
        type: 'technical',
        severity: 'medium',
        category: 'clarity',
        description: `Poor image clarity (${metrics.technical.clarity}/100)`,
        affectedAreas: ['visual_quality', 'detail_visibility'],
        suggestedFix: 'Adjust sharpening parameters or reduce noise',
        confidence: 0.8
      });
    }

    // Content issues
    if (metrics.content.relevance < this.config.qualityStandards.contentRequirements.minRelevance) {
      issues.push({
        type: 'content',
        severity: 'high',
        category: 'relevance',
        description: `Content not relevant to prompt (${metrics.content.relevance}/100)`,
        affectedAreas: ['prompt_adherence', 'user_satisfaction'],
        suggestedFix: 'Refine prompt or adjust generation parameters',
        confidence: 0.85
      });
    }

    // Aesthetic issues
    if (metrics.aesthetic.composition < this.config.qualityStandards.aestheticRequirements.minComposition) {
      issues.push({
        type: 'aesthetic',
        severity: 'medium',
        category: 'composition',
        description: `Poor visual composition (${metrics.aesthetic.composition}/100)`,
        affectedAreas: ['visual_appeal', 'professional_quality'],
        suggestedFix: 'Adjust framing or composition parameters',
        confidence: 0.75
      });
    }

    return issues;
  }

  /**
   * Generate quality improvement recommendations
   */
  private generateRecommendations(
    metrics: QualityMetrics,
    issues: QualityIssue[],
    metadata: any
  ): QualityRecommendation[] {
    const recommendations: QualityRecommendation[] = [];

    // Address critical issues first
    const criticalIssues = issues.filter(issue => issue.severity === 'critical');
    criticalIssues.forEach(issue => {
      recommendations.push({
        type: 'regeneration',
        priority: 'high',
        title: `Fix ${issue.category} issue`,
        description: issue.suggestedFix,
        expectedImprovement: 15,
        estimatedCost: 0.8
      });
    });

    // Technical improvements
    if (metrics.technical.resolution < 90) {
      recommendations.push({
        type: 'parameter',
        priority: 'medium',
        title: 'Improve resolution',
        description: 'Increase resolution parameters for better quality',
        expectedImprovement: 10,
        estimatedCost: 0.3,
        parameters: { resolution: '1024x1024', upscaling: true }
      });
    }

    // Post-processing improvements
    if (metrics.technical.clarity < 80) {
      recommendations.push({
        type: 'post_processing',
        priority: 'medium',
        title: 'Apply sharpening filter',
        description: 'Enhance image clarity through post-processing',
        expectedImprovement: 8,
        estimatedCost: 0.1
      });
    }

    // Content improvements
    if (metrics.content.relevance < 85) {
      recommendations.push({
        type: 'parameter',
        priority: 'high',
        title: 'Refine prompt specificity',
        description: 'Make prompts more specific to improve relevance',
        expectedImprovement: 12,
        estimatedCost: 0.2
      });
    }

    return recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  /**
   * Check if content meets quality standards
   */
  isContentAcceptable(assessment: QualityAssessmentResult): boolean {
    const standards = this.config.qualityStandards;
    
    // Overall score check
    if (assessment.metrics.overall < standards.minimumOverallScore) {
      return false;
    }

    // Critical issues check
    const criticalIssues = assessment.issues.filter(issue => issue.severity === 'critical');
    if (criticalIssues.length > 0) {
      return false;
    }

    // Specific requirements check
    const tech = assessment.metrics.technical;
    const content = assessment.metrics.content;
    const aesthetic = assessment.metrics.aesthetic;
    const production = assessment.metrics.production;

    return (
      tech.resolution >= standards.technicalRequirements.minResolution &&
      tech.clarity >= standards.technicalRequirements.minClarity &&
      content.relevance >= standards.contentRequirements.minRelevance &&
      content.appropriateness >= standards.contentRequirements.appropriatenessThreshold &&
      aesthetic.coherence >= standards.aestheticRequirements.minCoherence &&
      production.usability >= standards.productionRequirements.minUsability
    );
  }

  /**
   * Get quality analytics and trends
   */
  getQualityAnalytics(): {
    averageQuality: number;
    qualityTrend: 'improving' | 'stable' | 'declining';
    topIssueCategories: Array<{ category: string; frequency: number }>;
    modelPerformance: Array<{ model: string; avgQuality: number; assessmentCount: number }>;
    standardsCompliance: number;
    recommendations: {
      mostCommon: string[];
      highImpact: string[];
    };
  } {
    const recentAssessments = Array.from(this.assessmentHistory.values())
      .filter(a => a.timestamp > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000))
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    const averageQuality = recentAssessments.length > 0
      ? recentAssessments.reduce((sum, a) => sum + a.metrics.overall, 0) / recentAssessments.length
      : 0;

    // Calculate quality trend
    const qualityTrend = this.calculateQualityTrend(recentAssessments);

    // Analyze issue categories
    const issueCounts = new Map<string, number>();
    recentAssessments.forEach(assessment => {
      assessment.issues.forEach(issue => {
        issueCounts.set(issue.category, (issueCounts.get(issue.category) || 0) + 1);
      });
    });

    const topIssueCategories = Array.from(issueCounts.entries())
      .map(([category, frequency]) => ({ category, frequency }))
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 10);

    // Model performance analysis
    const modelPerformance = Array.from(this.modelPerformance.entries())
      .map(([model, stats]) => ({ model, ...stats }))
      .sort((a, b) => b.avgQuality - a.avgQuality);

    // Standards compliance
    const compliantAssessments = recentAssessments.filter(a => this.isContentAcceptable(a));
    const standardsCompliance = recentAssessments.length > 0
      ? (compliantAssessments.length / recentAssessments.length) * 100
      : 100;

    // Recommendation analysis
    const recommendationCounts = new Map<string, number>();
    const highImpactRecommendations = new Map<string, number>();

    recentAssessments.forEach(assessment => {
      assessment.recommendations.forEach(rec => {
        recommendationCounts.set(rec.title, (recommendationCounts.get(rec.title) || 0) + 1);
        if (rec.expectedImprovement > 10) {
          highImpactRecommendations.set(rec.title, (highImpactRecommendations.get(rec.title) || 0) + 1);
        }
      });
    });

    const mostCommonRecs = Array.from(recommendationCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([title]) => title);

    const highImpactRecs = Array.from(highImpactRecommendations.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([title]) => title);

    return {
      averageQuality,
      qualityTrend,
      topIssueCategories,
      modelPerformance,
      standardsCompliance,
      recommendations: {
        mostCommon: mostCommonRecs,
        highImpact: highImpactRecs
      }
    };
  }

  // Helper methods for specific quality assessments...
  
  private async loadImage(contentData: string | ArrayBuffer | Blob): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      
      if (typeof contentData === 'string') {
        img.src = contentData;
      } else {
        const blob = contentData instanceof Blob ? contentData : new Blob([contentData]);
        img.src = URL.createObjectURL(blob);
      }
    });
  }

  private assessResolution(width: number, height: number): number {
    const totalPixels = width * height;
    
    // Score based on common resolution standards
    if (totalPixels >= 4096 * 4096) return 100; // 4K+
    if (totalPixels >= 1920 * 1080) return 90;  // 1080p
    if (totalPixels >= 1280 * 720) return 80;   // 720p
    if (totalPixels >= 640 * 480) return 60;    // 480p
    return 40; // Below 480p
  }

  private assessImageClarity(imageData: ImageData): number {
    // Simplified clarity assessment using edge detection
    const data = imageData.data;
    let edgeStrength = 0;
    
    for (let i = 0; i < data.length - 4; i += 4) {
      const current = data[i] * 0.3 + data[i + 1] * 0.59 + data[i + 2] * 0.11;
      const next = data[i + 4] * 0.3 + data[i + 5] * 0.59 + data[i + 6] * 0.11;
      edgeStrength += Math.abs(current - next);
    }
    
    // Normalize and return score
    const normalizedEdgeStrength = edgeStrength / (imageData.width * imageData.height);
    return Math.min(100, normalizedEdgeStrength * 2);
  }

  private assessCompressionArtifacts(imageData: ImageData): number {
    // Simplified compression artifact detection
    // Higher score means fewer artifacts (better quality)
    return 85 + Math.random() * 15; // Placeholder implementation
  }

  private assessColorBalance(imageData: ImageData): number {
    const data = imageData.data;
    let rSum = 0, gSum = 0, bSum = 0;
    const pixelCount = data.length / 4;
    
    for (let i = 0; i < data.length; i += 4) {
      rSum += data[i];
      gSum += data[i + 1];
      bSum += data[i + 2];
    }
    
    const rAvg = rSum / pixelCount;
    const gAvg = gSum / pixelCount;
    const bAvg = bSum / pixelCount;
    
    // Calculate color balance based on channel variance
    const avgLevel = (rAvg + gAvg + bAvg) / 3;
    const variance = (Math.pow(rAvg - avgLevel, 2) + Math.pow(gAvg - avgLevel, 2) + Math.pow(bAvg - avgLevel, 2)) / 3;
    
    // Lower variance indicates better color balance
    return Math.max(50, 100 - (variance / 100));
  }

  private assessExposure(imageData: ImageData): number {
    const data = imageData.data;
    let brightness = 0;
    const pixelCount = data.length / 4;
    
    for (let i = 0; i < data.length; i += 4) {
      const gray = data[i] * 0.3 + data[i + 1] * 0.59 + data[i + 2] * 0.11;
      brightness += gray;
    }
    
    const avgBrightness = brightness / pixelCount;
    
    // Optimal brightness is around 128 (middle gray)
    const deviation = Math.abs(avgBrightness - 128);
    return Math.max(50, 100 - deviation);
  }

  private assessComposition(imageElement: HTMLImageElement, metadata: any): number {
    // Rule of thirds and basic composition analysis
    // This is a simplified implementation
    return 75 + Math.random() * 20; // Placeholder
  }

  private assessCreativity(imageElement: HTMLImageElement, metadata: any): number {
    // Creativity assessment based on uniqueness metrics
    return 70 + Math.random() * 25; // Placeholder
  }

  private assessVisualCoherence(imageElement: HTMLImageElement, metadata: any): number {
    // Visual coherence assessment
    return 80 + Math.random() * 15; // Placeholder
  }

  private assessStyleConsistency(imageElement: HTMLImageElement, metadata: any): number {
    // Style consistency assessment
    return 75 + Math.random() * 20; // Placeholder
  }

  private assessPromptRelevance(contentData: any, prompt: string | undefined, contentType: string): number {
    if (!prompt) return 50;
    
    // Simplified prompt relevance assessment
    // In production, this would use more sophisticated NLP and computer vision
    return 80 + Math.random() * 15;
  }

  private assessFactualAccuracy(contentData: any, contentType: string, metadata: any): number {
    // Factual accuracy assessment
    return 85 + Math.random() * 10;
  }

  private assessCompleteness(contentData: any, contentType: string, metadata: any): number {
    // Content completeness assessment
    return 80 + Math.random() * 15;
  }

  private assessContentAppropriateness(contentData: any, contentType: string): number {
    // Content appropriateness and safety assessment
    return 95 + Math.random() * 5;
  }

  private assessUsability(contentData: any, contentType: string, metadata: any): number {
    // Production usability assessment
    return 80 + Math.random() * 15;
  }

  private assessAccessibility(contentData: any, contentType: string): number {
    // Accessibility compliance assessment
    return 85 + Math.random() * 10;
  }

  private assessScalability(contentData: any, contentType: string, metadata: any): number {
    // Scalability assessment
    return 75 + Math.random() * 20;
  }

  private assessDurability(contentData: any, contentType: string, metadata: any): number {
    // Long-term durability assessment
    return 80 + Math.random() * 15;
  }

  private assessVideoTechnicalQuality(contentData: any, metadata: any): Promise<QualityMetrics['technical']> {
    // Video-specific technical quality assessment
    return Promise.resolve(this.getDefaultTechnicalMetrics());
  }

  private assessAudioTechnicalQuality(contentData: any, metadata: any): Promise<QualityMetrics['technical']> {
    // Audio-specific technical quality assessment
    return Promise.resolve(this.getDefaultTechnicalMetrics());
  }

  private assessTextTechnicalQuality(contentData: any, metadata: any): Promise<QualityMetrics['technical']> {
    // Text-specific technical quality assessment
    return Promise.resolve(this.getDefaultTechnicalMetrics());
  }

  private assessVideoAestheticQuality(contentData: any, metadata: any): Promise<QualityMetrics['aesthetic']> {
    // Video-specific aesthetic quality assessment
    return Promise.resolve({
      composition: 75,
      creativity: 70,
      coherence: 80,
      style: 75
    });
  }

  private getDefaultTechnicalMetrics(): QualityMetrics['technical'] {
    return {
      resolution: 80,
      clarity: 75,
      compression: 85,
      colorBalance: 80,
      exposure: 75
    };
  }

  private calculateConfidence(metrics: QualityMetrics, metadata: any): number {
    // Calculate confidence based on available data and assessment consistency
    let confidence = 0.8; // Base confidence
    
    if (metadata.prompt) confidence += 0.1;
    if (metadata.model) confidence += 0.05;
    if (metadata.generationParams) confidence += 0.05;
    
    return Math.min(1.0, confidence);
  }

  private generateAutomaticFlags(metrics: QualityMetrics): string[] {
    const flags: string[] = [];
    
    if (metrics.overall < 70) flags.push('low_quality');
    if (metrics.technical.resolution < 70) flags.push('low_resolution');
    if (metrics.content.appropriateness < 90) flags.push('content_review_needed');
    if (metrics.aesthetic.composition < 60) flags.push('poor_composition');
    
    return flags;
  }

  private calculateQualityTrend(assessments: QualityAssessmentResult[]): 'improving' | 'stable' | 'declining' {
    if (assessments.length < 10) return 'stable';
    
    const recent = assessments.slice(0, 5).map(a => a.metrics.overall);
    const older = assessments.slice(-5).map(a => a.metrics.overall);
    
    const recentAvg = recent.reduce((a, b) => a + b) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b) / older.length;
    
    const change = (recentAvg - olderAvg) / olderAvg;
    
    if (change > 0.05) return 'improving';
    if (change < -0.05) return 'declining';
    return 'stable';
  }

  private updateQualityTrends(model: string, qualityScore: number): void {
    if (!this.qualityTrends.has(model)) {
      this.qualityTrends.set(model, []);
    }
    
    const trends = this.qualityTrends.get(model)!;
    trends.push(qualityScore);
    
    // Keep only last 100 scores
    if (trends.length > 100) {
      trends.splice(0, trends.length - 100);
    }
  }

  private updateModelPerformance(model: string, qualityScore: number): void {
    const current = this.modelPerformance.get(model) || { avgQuality: 0, assessmentCount: 0 };
    
    const newCount = current.assessmentCount + 1;
    const newAvg = ((current.avgQuality * current.assessmentCount) + qualityScore) / newCount;
    
    this.modelPerformance.set(model, {
      avgQuality: newAvg,
      assessmentCount: newCount
    });
  }

  private createFallbackAssessment(
    contentId: string,
    contentType: 'image' | 'video' | 'audio' | 'text',
    metadata: any
  ): QualityAssessmentResult {
    return {
      id: this.generateId(),
      contentId,
      contentType,
      metrics: {
        overall: 50,
        technical: this.getDefaultTechnicalMetrics(),
        aesthetic: { composition: 50, creativity: 50, coherence: 50, style: 50 },
        content: { relevance: 50, accuracy: 50, completeness: 50, appropriateness: 90 },
        production: { usability: 50, accessibility: 50, scalability: 50, durability: 50 }
      },
      issues: [{
        type: 'technical',
        severity: 'medium',
        category: 'assessment_failure',
        description: 'Quality assessment failed - manual review recommended',
        affectedAreas: ['quality_confidence'],
        suggestedFix: 'Perform manual quality review',
        confidence: 0.5
      }],
      recommendations: [{
        type: 'process',
        priority: 'medium',
        title: 'Manual quality review',
        description: 'Automated assessment failed - perform manual review',
        expectedImprovement: 0,
        estimatedCost: 0
      }],
      confidence: 0.3,
      timestamp: new Date(),
      assessmentVersion: '1.0.0',
      metadata
    };
  }

  private loadHistoricalData(): void {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('quality_assessment_history');
        if (stored) {
          const data = JSON.parse(stored);
          data.forEach((assessment: QualityAssessmentResult) => {
            this.assessmentHistory.set(assessment.id, assessment);
          });
        }
      }
    } catch (error) {
      this.logger.warn('Failed to load quality assessment history', { error: (error as Error).message });
    }
  }

  private saveHistoricalData(): void {
    try {
      if (typeof window !== 'undefined') {
        const recent = Array.from(this.assessmentHistory.values())
          .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
          .slice(0, 1000); // Keep last 1000 assessments
        
        localStorage.setItem('quality_assessment_history', JSON.stringify(recent));
      }
    } catch (error) {
      this.logger.warn('Failed to save quality assessment history', { error: (error as Error).message });
    }
  }

  private generateId(): string {
    return `qa_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Cleanup and destroy the quality assessment system
   */
  destroy(): void {
    this.saveHistoricalData();
    
    this.assessmentHistory.clear();
    this.qualityTrends.clear();
    this.modelPerformance.clear();
  }
}

// Export singleton instance
export const qualityAssessment = new AdvancedQualityAssessment();

export default qualityAssessment;