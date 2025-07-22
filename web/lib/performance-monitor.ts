/**
 * Comprehensive performance monitoring and metrics collection system
 * Tracks system performance, user experience, and provides actionable insights
 */

import EventEmitter from 'events';

export interface PerformanceMetric {
  id: string;
  name: string;
  value: number;
  timestamp: Date;
  tags: Record<string, string>;
  metadata?: any;
}

export interface UserInteractionMetric {
  id: string;
  action: string;
  component: string;
  duration: number;
  timestamp: Date;
  success: boolean;
  errorMessage?: string;
  userAgent?: string;
  sessionId: string;
}

export interface SystemHealthMetric {
  timestamp: Date;
  cpu: number;
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  network: {
    latency: number;
    bandwidth: number;
    errors: number;
  };
  api: {
    responseTime: number;
    successRate: number;
    activeConnections: number;
  };
  queue: {
    pendingJobs: number;
    processingJobs: number;
    avgWaitTime: number;
  };
}

export interface PerformanceAlert {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  metric: string;
  threshold: number;
  currentValue: number;
  timestamp: Date;
  acknowledged?: boolean;
}

export interface PerformanceReport {
  period: {
    start: Date;
    end: Date;
  };
  summary: {
    totalRequests: number;
    avgResponseTime: number;
    successRate: number;
    totalCost: number;
    costPerRequest: number;
    userSatisfactionScore: number;
  };
  trends: {
    responseTime: number[];
    successRate: number[];
    cost: number[];
    userActions: number[];
  };
  topIssues: Array<{
    category: string;
    count: number;
    impact: number;
  }>;
  recommendations: string[];
}

interface MonitorConfig {
  sampleRate: number;
  metricsRetention: number;
  alertThresholds: Record<string, number>;
  enableRealTimeAnalysis: boolean;
  enableUserTracking: boolean;
  enableSystemHealth: boolean;
  reportingInterval: number;
}

interface MetricsStorage {
  performance: Map<string, PerformanceMetric[]>;
  interactions: Map<string, UserInteractionMetric[]>;
  health: SystemHealthMetric[];
  alerts: Map<string, PerformanceAlert>;
}

export class AdvancedPerformanceMonitor extends EventEmitter {
  private config: MonitorConfig;
  private storage: MetricsStorage;
  private sessionId: string;
  private startTime: Date;
  private intervalIds: NodeJS.Timeout[] = [];
  private observers: Map<string, any> = new Map();

  constructor(config: Partial<MonitorConfig> = {}) {
    super();

    this.config = {
      sampleRate: 1000, // Sample every second
      metricsRetention: 7 * 24 * 60 * 60 * 1000, // 7 days
      alertThresholds: {
        'response_time': 5000, // 5 seconds
        'memory_usage': 0.8, // 80%
        'error_rate': 0.1, // 10%
        'queue_wait_time': 30000, // 30 seconds
        'cost_per_hour': 100 // $100
      },
      enableRealTimeAnalysis: true,
      enableUserTracking: true,
      enableSystemHealth: true,
      reportingInterval: 5 * 60 * 1000, // 5 minutes
      ...config
    };

    this.storage = {
      performance: new Map(),
      interactions: new Map(),
      health: [],
      alerts: new Map()
    };

    this.sessionId = this.generateSessionId();
    this.startTime = new Date();

    this.initialize();
  }

  private initialize(): void {
    if (typeof window !== 'undefined') {
      this.setupWebVitalsTracking();
      this.setupUserInteractionTracking();
      this.setupNetworkMonitoring();
    }

    if (this.config.enableSystemHealth) {
      this.startSystemHealthMonitoring();
    }

    if (this.config.enableRealTimeAnalysis) {
      this.startRealTimeAnalysis();
    }

    this.startPeriodicReporting();
    this.startCleanupTask();
  }

  /**
   * Record a performance metric
   */
  recordMetric(
    name: string,
    value: number,
    tags: Record<string, string> = {},
    metadata?: any
  ): void {
    const metric: PerformanceMetric = {
      id: this.generateId(),
      name,
      value,
      timestamp: new Date(),
      tags: { sessionId: this.sessionId, ...tags },
      metadata
    };

    if (!this.storage.performance.has(name)) {
      this.storage.performance.set(name, []);
    }

    this.storage.performance.get(name)!.push(metric);
    this.checkAlertThresholds(metric);
    this.emit('metricRecorded', metric);

    // Real-time analysis
    if (this.config.enableRealTimeAnalysis) {
      this.analyzeMetricRealTime(metric);
    }
  }

  /**
   * Record user interaction
   */
  recordInteraction(
    action: string,
    component: string,
    duration: number,
    success: boolean = true,
    errorMessage?: string
  ): void {
    const interaction: UserInteractionMetric = {
      id: this.generateId(),
      action,
      component,
      duration,
      timestamp: new Date(),
      success,
      errorMessage,
      userAgent: typeof window !== 'undefined' ? navigator.userAgent : undefined,
      sessionId: this.sessionId
    };

    const key = `${component}:${action}`;
    if (!this.storage.interactions.has(key)) {
      this.storage.interactions.set(key, []);
    }

    this.storage.interactions.get(key)!.push(interaction);
    this.emit('interactionRecorded', interaction);

    // Auto-record performance metric
    this.recordMetric(
      'user_interaction_time',
      duration,
      { action, component, success: success.toString() }
    );
  }

  /**
   * Track API call performance
   */
  async trackApiCall<T>(
    endpoint: string,
    method: string,
    apiCall: () => Promise<T>,
    metadata?: any
  ): Promise<T> {
    const startTime = performance.now();
    const callId = this.generateId();

    try {
      const result = await apiCall();
      const duration = performance.now() - startTime;

      this.recordMetric('api_response_time', duration, {
        endpoint,
        method,
        status: 'success'
      }, { callId, ...metadata });

      this.recordMetric('api_success_rate', 1, { endpoint, method });

      return result;
    } catch (error) {
      const duration = performance.now() - startTime;

      this.recordMetric('api_response_time', duration, {
        endpoint,
        method,
        status: 'error'
      }, { 
        callId, 
        error: error instanceof Error ? error.message : 'Unknown error',
        ...metadata 
      });

      this.recordMetric('api_success_rate', 0, { endpoint, method });

      throw error;
    }
  }

  /**
   * Get performance analytics for a specific time period
   */
  getAnalytics(
    startTime: Date,
    endTime: Date,
    metricNames?: string[]
  ): {
    metrics: Record<string, PerformanceMetric[]>;
    interactions: Record<string, UserInteractionMetric[]>;
    health: SystemHealthMetric[];
    insights: string[];
  } {
    const filteredMetrics: Record<string, PerformanceMetric[]> = {};
    const filteredInteractions: Record<string, UserInteractionMetric[]> = {};

    // Filter performance metrics
    for (const [name, metrics] of this.storage.performance.entries()) {
      if (metricNames && !metricNames.includes(name)) continue;

      const filtered = metrics.filter(m =>
        m.timestamp >= startTime && m.timestamp <= endTime
      );

      if (filtered.length > 0) {
        filteredMetrics[name] = filtered;
      }
    }

    // Filter interactions
    for (const [key, interactions] of this.storage.interactions.entries()) {
      const filtered = interactions.filter(i =>
        i.timestamp >= startTime && i.timestamp <= endTime
      );

      if (filtered.length > 0) {
        filteredInteractions[key] = filtered;
      }
    }

    // Filter health metrics
    const filteredHealth = this.storage.health.filter(h =>
      h.timestamp >= startTime && h.timestamp <= endTime
    );

    // Generate insights
    const insights = this.generateInsights(filteredMetrics, filteredInteractions, filteredHealth);

    return {
      metrics: filteredMetrics,
      interactions: filteredInteractions,
      health: filteredHealth,
      insights
    };
  }

  /**
   * Generate comprehensive performance report
   */
  generateReport(
    startTime: Date,
    endTime: Date
  ): PerformanceReport {
    const analytics = this.getAnalytics(startTime, endTime);
    
    // Calculate summary statistics
    const apiMetrics = analytics.metrics['api_response_time'] || [];
    const successMetrics = analytics.metrics['api_success_rate'] || [];
    const costMetrics = analytics.metrics['cost'] || [];
    const interactionValues = Object.values(analytics.interactions).flat();

    const totalRequests = apiMetrics.length;
    const avgResponseTime = apiMetrics.length > 0
      ? apiMetrics.reduce((sum, m) => sum + m.value, 0) / apiMetrics.length
      : 0;
    
    const successRate = successMetrics.length > 0
      ? successMetrics.reduce((sum, m) => sum + m.value, 0) / successMetrics.length
      : 1;

    const totalCost = costMetrics.reduce((sum, m) => sum + m.value, 0);
    const costPerRequest = totalRequests > 0 ? totalCost / totalRequests : 0;

    // Calculate user satisfaction score based on interaction success rate and response times
    const successfulInteractions = interactionValues.filter(i => i.success).length;
    const userSatisfactionScore = interactionValues.length > 0
      ? (successfulInteractions / interactionValues.length) * (1 - Math.min(avgResponseTime / 10000, 0.5))
      : 1;

    // Generate trends (simplified - last 24 hours in hourly buckets)
    const trends = this.generateTrends(analytics, startTime, endTime);

    // Identify top issues
    const topIssues = this.identifyTopIssues(analytics);

    // Generate recommendations
    const recommendations = this.generateRecommendations(analytics, {
      avgResponseTime,
      successRate,
      totalCost,
      userSatisfactionScore
    });

    return {
      period: { start: startTime, end: endTime },
      summary: {
        totalRequests,
        avgResponseTime,
        successRate,
        totalCost,
        costPerRequest,
        userSatisfactionScore
      },
      trends,
      topIssues,
      recommendations
    };
  }

  /**
   * Get current system performance status
   */
  getCurrentStatus(): {
    health: 'excellent' | 'good' | 'warning' | 'critical';
    score: number;
    issues: string[];
    recommendations: string[];
    alerts: PerformanceAlert[];
  } {
    const recentMetrics = this.getRecentMetrics(5 * 60 * 1000); // Last 5 minutes
    const activeAlerts = Array.from(this.storage.alerts.values())
      .filter(alert => !alert.acknowledged);

    // Calculate health score (0-100)
    let healthScore = 100;
    const issues: string[] = [];
    const recommendations: string[] = [];

    // Check response time
    const responseTime = this.getAverageMetric(recentMetrics['api_response_time']);
    if (responseTime > 5000) {
      healthScore -= 30;
      issues.push('High response time');
      recommendations.push('Optimize API performance or increase resources');
    } else if (responseTime > 2000) {
      healthScore -= 10;
      issues.push('Elevated response time');
      recommendations.push('Monitor API performance trends');
    }

    // Check success rate
    const successRate = this.getAverageMetric(recentMetrics['api_success_rate']);
    if (successRate < 0.9) {
      healthScore -= 40;
      issues.push('Low success rate');
      recommendations.push('Investigate and fix API errors');
    } else if (successRate < 0.95) {
      healthScore -= 15;
      issues.push('Moderate error rate');
      recommendations.push('Review error patterns');
    }

    // Check memory usage
    const memoryUsage = this.getAverageMetric(recentMetrics['memory_usage']);
    if (memoryUsage > 0.9) {
      healthScore -= 25;
      issues.push('High memory usage');
      recommendations.push('Investigate memory leaks and optimize usage');
    } else if (memoryUsage > 0.8) {
      healthScore -= 10;
      issues.push('Elevated memory usage');
      recommendations.push('Monitor memory usage trends');
    }

    // Determine health status
    let health: 'excellent' | 'good' | 'warning' | 'critical';
    if (healthScore >= 90) health = 'excellent';
    else if (healthScore >= 70) health = 'good';
    else if (healthScore >= 50) health = 'warning';
    else health = 'critical';

    return {
      health,
      score: Math.max(0, healthScore),
      issues,
      recommendations,
      alerts: activeAlerts
    };
  }

  /**
   * Setup Web Vitals tracking
   */
  private setupWebVitalsTracking(): void {
    if (typeof window === 'undefined') return;

    // Track Core Web Vitals
    if ('PerformanceObserver' in window) {
      // Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordMetric('core_web_vitals_lcp', entry.startTime, {
            type: 'lcp'
          });
        }
      });

      try {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.set('lcp', lcpObserver);
      } catch (error) {
        console.warn('LCP monitoring not supported');
      }

      // First Input Delay
      const fidObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          // @ts-ignore
          this.recordMetric('core_web_vitals_fid', entry.processingStart - entry.startTime, {
            type: 'fid'
          });
        }
      });

      try {
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('fid', fidObserver);
      } catch (error) {
        console.warn('FID monitoring not supported');
      }

      // Cumulative Layout Shift
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          // @ts-ignore
          if (!entry.hadRecentInput) {
            // @ts-ignore
            clsValue += entry.value;
            this.recordMetric('core_web_vitals_cls', clsValue, {
              type: 'cls'
            });
          }
        }
      });

      try {
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('cls', clsObserver);
      } catch (error) {
        console.warn('CLS monitoring not supported');
      }
    }

    // Track page load metrics
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        this.recordMetric('page_load_time', navigation.loadEventEnd - navigation.fetchStart, {
          type: 'page_load'
        });

        this.recordMetric('dom_content_loaded', navigation.domContentLoadedEventEnd - navigation.fetchStart, {
          type: 'dom_ready'
        });

        this.recordMetric('first_paint', navigation.responseStart - navigation.fetchStart, {
          type: 'first_paint'
        });
      }, 0);
    });
  }

  /**
   * Setup user interaction tracking
   */
  private setupUserInteractionTracking(): void {
    if (typeof window === 'undefined' || !this.config.enableUserTracking) return;

    // Track clicks with timing
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      const component = target.closest('[data-component]')?.getAttribute('data-component') || 'unknown';
      
      this.recordInteraction('click', component, 0, true);
    });

    // Track form submissions
    document.addEventListener('submit', (event) => {
      const form = event.target as HTMLFormElement;
      const component = form.getAttribute('data-component') || 'form';
      
      this.recordInteraction('submit', component, 0, true);
    });

    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      this.recordMetric('page_visibility', document.hidden ? 0 : 1, {
        type: 'visibility'
      });
    });
  }

  /**
   * Setup network monitoring
   */
  private setupNetworkMonitoring(): void {
    if (typeof window === 'undefined') return;

    // Monitor network information
    // @ts-ignore
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    
    if (connection) {
      this.recordMetric('network_downlink', connection.downlink, {
        type: 'network',
        effectiveType: connection.effectiveType
      });

      connection.addEventListener('change', () => {
        this.recordMetric('network_downlink', connection.downlink, {
          type: 'network',
          effectiveType: connection.effectiveType
        });
      });
    }
  }

  private startSystemHealthMonitoring(): void {
    const interval = setInterval(() => {
      this.collectSystemHealthMetrics();
    }, this.config.sampleRate);

    this.intervalIds.push(interval);
  }

  private collectSystemHealthMetrics(): void {
    if (typeof window === 'undefined') return;

    const health: Partial<SystemHealthMetric> = {
      timestamp: new Date()
    };

    // Memory metrics
    // @ts-ignore
    if (performance.memory) {
      // @ts-ignore
      const memory = performance.memory;
      health.memory = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        percentage: memory.usedJSHeapSize / memory.totalJSHeapSize
      };

      this.recordMetric('memory_usage', health.memory.percentage, {
        type: 'memory'
      });
    }

    // Network timing
    if (performance.timing) {
      const timing = performance.timing;
      health.network = {
        latency: timing.responseStart - timing.requestStart,
        bandwidth: 0, // Would need actual implementation
        errors: 0 // Would need actual implementation
      };
    }

    this.storage.health.push(health as SystemHealthMetric);
  }

  private startRealTimeAnalysis(): void {
    const interval = setInterval(() => {
      this.performRealTimeAnalysis();
    }, this.config.reportingInterval);

    this.intervalIds.push(interval);
  }

  private performRealTimeAnalysis(): void {
    const recentMetrics = this.getRecentMetrics(this.config.reportingInterval);
    
    // Analyze trends and patterns
    for (const [name, metrics] of Object.entries(recentMetrics)) {
      if (metrics.length < 2) continue;

      // Detect sudden spikes
      const recent = metrics.slice(-5).map(m => m.value);
      const average = recent.reduce((sum, val) => sum + val, 0) / recent.length;
      const lastValue = recent[recent.length - 1];

      if (lastValue > average * 2 && lastValue > this.config.alertThresholds[name]) {
        this.createAlert('warning', `Spike detected in ${name}`, name, average, lastValue);
      }
    }
  }

  private startPeriodicReporting(): void {
    const interval = setInterval(() => {
      const report = this.generateReport(
        new Date(Date.now() - this.config.reportingInterval),
        new Date()
      );
      
      this.emit('periodicReport', report);
    }, this.config.reportingInterval);

    this.intervalIds.push(interval);
  }

  private startCleanupTask(): void {
    const interval = setInterval(() => {
      this.cleanupOldMetrics();
    }, 60 * 60 * 1000); // Cleanup every hour

    this.intervalIds.push(interval);
  }

  private cleanupOldMetrics(): void {
    const cutoff = new Date(Date.now() - this.config.metricsRetention);

    // Clean performance metrics
    for (const [name, metrics] of this.storage.performance.entries()) {
      const filtered = metrics.filter(m => m.timestamp > cutoff);
      this.storage.performance.set(name, filtered);
    }

    // Clean interaction metrics
    for (const [name, interactions] of this.storage.interactions.entries()) {
      const filtered = interactions.filter(i => i.timestamp > cutoff);
      this.storage.interactions.set(name, filtered);
    }

    // Clean health metrics
    this.storage.health = this.storage.health.filter(h => h.timestamp > cutoff);

    // Clean acknowledged alerts older than 1 day
    const alertCutoff = new Date(Date.now() - 24 * 60 * 60 * 1000);
    for (const [id, alert] of this.storage.alerts.entries()) {
      if (alert.acknowledged && alert.timestamp < alertCutoff) {
        this.storage.alerts.delete(id);
      }
    }
  }

  private checkAlertThresholds(metric: PerformanceMetric): void {
    const threshold = this.config.alertThresholds[metric.name];
    if (!threshold) return;

    let shouldAlert = false;
    let level: 'info' | 'warning' | 'error' | 'critical' = 'info';

    if (metric.value > threshold * 2) {
      shouldAlert = true;
      level = 'critical';
    } else if (metric.value > threshold * 1.5) {
      shouldAlert = true;
      level = 'error';
    } else if (metric.value > threshold) {
      shouldAlert = true;
      level = 'warning';
    }

    if (shouldAlert) {
      this.createAlert(
        level,
        `${metric.name} exceeded threshold`,
        metric.name,
        threshold,
        metric.value
      );
    }
  }

  private createAlert(
    level: 'info' | 'warning' | 'error' | 'critical',
    message: string,
    metric: string,
    threshold: number,
    currentValue: number
  ): void {
    const alertId = this.generateId();
    
    const alert: PerformanceAlert = {
      id: alertId,
      level,
      message,
      metric,
      threshold,
      currentValue,
      timestamp: new Date(),
      acknowledged: false
    };

    this.storage.alerts.set(alertId, alert);
    this.emit('alert', alert);
  }

  private analyzeMetricRealTime(metric: PerformanceMetric): void {
    // Get recent metrics of the same type for trend analysis
    const recentMetrics = this.getRecentMetrics(60000)[metric.name] || [];
    
    if (recentMetrics.length > 5) {
      const values = recentMetrics.slice(-5).map(m => m.value);
      const trend = this.calculateTrend(values);
      
      if (trend > 0.5) { // Increasing trend
        this.emit('metricTrendAlert', {
          metric: metric.name,
          trend: 'increasing',
          strength: trend,
          currentValue: metric.value
        });
      } else if (trend < -0.5) { // Decreasing trend
        this.emit('metricTrendAlert', {
          metric: metric.name,
          trend: 'decreasing',
          strength: Math.abs(trend),
          currentValue: metric.value
        });
      }
    }
  }

  private getRecentMetrics(timeWindowMs: number): Record<string, PerformanceMetric[]> {
    const cutoff = new Date(Date.now() - timeWindowMs);
    const result: Record<string, PerformanceMetric[]> = {};

    for (const [name, metrics] of this.storage.performance.entries()) {
      const recent = metrics.filter(m => m.timestamp > cutoff);
      if (recent.length > 0) {
        result[name] = recent;
      }
    }

    return result;
  }

  private getAverageMetric(metrics: PerformanceMetric[]): number {
    if (!metrics || metrics.length === 0) return 0;
    return metrics.reduce((sum, m) => sum + m.value, 0) / metrics.length;
  }

  private calculateTrend(values: number[]): number {
    if (values.length < 2) return 0;

    // Simple linear regression slope
    const n = values.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = values.reduce((sum, y, x) => sum + x * y, 0);
    const sumXX = (n * (n - 1) * (2 * n - 1)) / 6;

    return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  }

  private generateTrends(
    analytics: any,
    startTime: Date,
    endTime: Date
  ): { responseTime: number[]; successRate: number[]; cost: number[]; userActions: number[] } {
    // Simplified trend generation - would be more sophisticated in production
    const buckets = 24; // 24 hourly buckets
    const bucketSize = (endTime.getTime() - startTime.getTime()) / buckets;

    const trends = {
      responseTime: new Array(buckets).fill(0),
      successRate: new Array(buckets).fill(1),
      cost: new Array(buckets).fill(0),
      userActions: new Array(buckets).fill(0)
    };

    // Fill trends with actual data
    const responseTimeMetrics = analytics.metrics['api_response_time'] || [];
    for (const metric of responseTimeMetrics) {
      const bucketIndex = Math.floor(
        (metric.timestamp.getTime() - startTime.getTime()) / bucketSize
      );
      if (bucketIndex >= 0 && bucketIndex < buckets) {
        trends.responseTime[bucketIndex] = metric.value;
      }
    }

    return trends;
  }

  private identifyTopIssues(analytics: any): Array<{ category: string; count: number; impact: number }> {
    const issues: Array<{ category: string; count: number; impact: number }> = [];

    // Analyze error rates
    const errorCount = Object.values(analytics.interactions)
      .flat()
      .filter((i: any) => !i.success).length;

    if (errorCount > 0) {
      issues.push({
        category: 'User Experience Errors',
        count: errorCount,
        impact: errorCount * 0.1 // Simplified impact calculation
      });
    }

    // Analyze performance issues
    const slowRequests = (analytics.metrics['api_response_time'] || [])
      .filter((m: any) => m.value > 5000).length;

    if (slowRequests > 0) {
      issues.push({
        category: 'Slow API Responses',
        count: slowRequests,
        impact: slowRequests * 0.15
      });
    }

    return issues.sort((a, b) => b.impact - a.impact);
  }

  private generateRecommendations(analytics: any, summary: any): string[] {
    const recommendations: string[] = [];

    if (summary.avgResponseTime > 2000) {
      recommendations.push('Consider implementing API response caching to improve response times');
    }

    if (summary.successRate < 0.95) {
      recommendations.push('Investigate and fix API error patterns to improve reliability');
    }

    if (summary.costPerRequest > 1) {
      recommendations.push('Optimize API usage patterns to reduce costs per request');
    }

    if (summary.userSatisfactionScore < 0.8) {
      recommendations.push('Focus on improving user experience and interaction response times');
    }

    return recommendations;
  }

  private generateInsights(
    metrics: Record<string, PerformanceMetric[]>,
    interactions: Record<string, UserInteractionMetric[]>,
    health: SystemHealthMetric[]
  ): string[] {
    const insights: string[] = [];

    // Analyze performance trends
    const responseTimeMetrics = metrics['api_response_time'] || [];
    if (responseTimeMetrics.length > 1) {
      const recent = responseTimeMetrics.slice(-10).map(m => m.value);
      const trend = this.calculateTrend(recent);
      
      if (trend > 10) {
        insights.push('API response times are trending upward - investigate performance bottlenecks');
      } else if (trend < -10) {
        insights.push('API response times are improving - recent optimizations are working');
      }
    }

    // Analyze user behavior
    const totalInteractions = Object.values(interactions).flat().length;
    if (totalInteractions > 0) {
      const successfulInteractions = Object.values(interactions)
        .flat()
        .filter(i => i.success).length;
      
      const successRate = successfulInteractions / totalInteractions;
      if (successRate < 0.9) {
        insights.push(`User interaction success rate is ${(successRate * 100).toFixed(1)}% - focus on error reduction`);
      }
    }

    return insights;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Acknowledge an alert
   */
  acknowledgeAlert(alertId: string): boolean {
    const alert = this.storage.alerts.get(alertId);
    if (alert) {
      alert.acknowledged = true;
      this.emit('alertAcknowledged', alert);
      return true;
    }
    return false;
  }

  /**
   * Get all active alerts
   */
  getActiveAlerts(): PerformanceAlert[] {
    return Array.from(this.storage.alerts.values())
      .filter(alert => !alert.acknowledged);
  }

  /**
   * Export performance data
   */
  exportData(format: 'json' | 'csv' = 'json'): any {
    const data = {
      metadata: {
        sessionId: this.sessionId,
        startTime: this.startTime,
        exportTime: new Date(),
        format
      },
      metrics: Object.fromEntries(this.storage.performance),
      interactions: Object.fromEntries(this.storage.interactions),
      health: this.storage.health,
      alerts: Array.from(this.storage.alerts.values())
    };

    if (format === 'json') {
      return JSON.stringify(data, null, 2);
    }

    // CSV export would be implemented here
    return data;
  }

  /**
   * Cleanup and destroy the monitor
   */
  destroy(): void {
    // Clear all intervals
    this.intervalIds.forEach(id => clearInterval(id));
    this.intervalIds = [];

    // Disconnect observers
    this.observers.forEach(observer => {
      if (observer && typeof observer.disconnect === 'function') {
        observer.disconnect();
      }
    });
    this.observers.clear();

    // Clear storage
    this.storage.performance.clear();
    this.storage.interactions.clear();
    this.storage.health = [];
    this.storage.alerts.clear();

    this.emit('destroyed');
    this.removeAllListeners();
  }
}

// Export singleton instance
export const performanceMonitor = new AdvancedPerformanceMonitor();

export default performanceMonitor;