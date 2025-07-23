/**
 * Comprehensive health monitoring and alerting system
 * Monitors system health, performance, and generates intelligent alerts
 */

import EventEmitter from 'events';

export interface HealthMetric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  timestamp: Date;
  threshold: {
    warning: number;
    critical: number;
  };
  trend: 'improving' | 'stable' | 'degrading';
  metadata?: any;
}

export interface SystemComponent {
  id: string;
  name: string;
  type: 'service' | 'database' | 'queue' | 'cache' | 'api' | 'storage';
  status: 'online' | 'offline' | 'degraded' | 'maintenance';
  health: number; // 0-100 health score
  lastCheck: Date;
  responseTime?: number;
  errorRate?: number;
  dependencies: string[];
  metrics: HealthMetric[];
}

export interface HealthAlert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  component: string;
  metric?: string;
  timestamp: Date;
  acknowledged: boolean;
  resolvedAt?: Date;
  actions: string[];
  metadata: any;
}

export interface HealthReport {
  overallHealth: number;
  status: 'healthy' | 'warning' | 'critical' | 'degraded';
  components: SystemComponent[];
  alerts: HealthAlert[];
  trends: {
    performance: 'improving' | 'stable' | 'degrading';
    reliability: 'improving' | 'stable' | 'degrading';
    capacity: 'improving' | 'stable' | 'degrading';
  };
  recommendations: string[];
  generatedAt: Date;
}

interface MonitoringConfig {
  checkInterval: number;
  alertCooldown: number;
  metricRetention: number;
  healthThresholds: {
    warning: number;
    critical: number;
  };
  componentTimeouts: Record<string, number>;
  enablePredictiveAlerts: boolean;
  enableAutoRecovery: boolean;
}

export class AdvancedHealthMonitor extends EventEmitter {
  private config: MonitoringConfig;
  private components: Map<string, SystemComponent>;
  private alerts: Map<string, HealthAlert>;
  private metricHistory: Map<string, HealthMetric[]>;
  private monitoringInterval?: NodeJS.Timeout;
  private alertSuppressionMap: Map<string, Date>;
  private healthCheckers: Map<string, () => Promise<Partial<SystemComponent>>>;

  constructor(config: Partial<MonitoringConfig> = {}) {
    super();

    this.config = {
      checkInterval: 30000, // 30 seconds
      alertCooldown: 300000, // 5 minutes
      metricRetention: 24 * 60 * 60 * 1000, // 24 hours
      healthThresholds: {
        warning: 70,
        critical: 50
      },
      componentTimeouts: {
        api: 5000,
        database: 3000,
        queue: 2000,
        cache: 1000,
        service: 10000,
        storage: 5000
      },
      enablePredictiveAlerts: true,
      enableAutoRecovery: false,
      ...config
    };

    this.components = new Map();
    this.alerts = new Map();
    this.metricHistory = new Map();
    this.alertSuppressionMap = new Map();
    this.healthCheckers = new Map();

    this.initializeDefaultComponents();
    this.startMonitoring();
  }

  /**
   * Register a component for health monitoring
   */
  registerComponent(component: Omit<SystemComponent, 'lastCheck' | 'health'>): void {
    const fullComponent: SystemComponent = {
      ...component,
      lastCheck: new Date(),
      health: 100,
      metrics: component.metrics || []
    };

    this.components.set(component.id, fullComponent);
    this.emit('componentRegistered', fullComponent);
  }

  /**
   * Register a custom health checker for a component
   */
  registerHealthChecker(
    componentId: string, 
    checker: () => Promise<Partial<SystemComponent>>
  ): void {
    this.healthCheckers.set(componentId, checker);
  }

  /**
   * Get current health report
   */
  async getHealthReport(): Promise<HealthReport> {
    await this.checkAllComponents();

    const components = Array.from(this.components.values());
    const activeAlerts = Array.from(this.alerts.values()).filter(a => !a.resolvedAt);
    
    const overallHealth = this.calculateOverallHealth(components);
    const status = this.determineOverallStatus(overallHealth, activeAlerts);
    const trends = this.analyzeTrends();
    const recommendations = this.generateRecommendations(components, activeAlerts);

    return {
      overallHealth,
      status,
      components: components.sort((a, b) => a.name.localeCompare(b.name)),
      alerts: activeAlerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()),
      trends,
      recommendations,
      generatedAt: new Date()
    };
  }

  /**
   * Get detailed component health
   */
  getComponentHealth(componentId: string): SystemComponent | null {
    return this.components.get(componentId) || null;
  }

  /**
   * Get health metrics for a component
   */
  getComponentMetrics(
    componentId: string, 
    metricName?: string, 
    timeRange?: { start: Date; end: Date }
  ): HealthMetric[] {
    const key = metricName ? `${componentId}.${metricName}` : componentId;
    const metrics = this.metricHistory.get(key) || [];

    if (timeRange) {
      return metrics.filter(m => 
        m.timestamp >= timeRange.start && m.timestamp <= timeRange.end
      );
    }

    return metrics;
  }

  /**
   * Create a manual alert
   */
  createAlert(
    severity: HealthAlert['severity'],
    title: string,
    message: string,
    component: string,
    actions: string[] = [],
    metadata: any = {}
  ): HealthAlert {
    const alert: HealthAlert = {
      id: this.generateAlertId(),
      severity,
      title,
      message,
      component,
      timestamp: new Date(),
      acknowledged: false,
      actions,
      metadata
    };

    this.alerts.set(alert.id, alert);
    this.emit('alert', alert);

    // Send notifications
    this.sendAlertNotification(alert);

    return alert;
  }

  /**
   * Acknowledge an alert
   */
  acknowledgeAlert(alertId: string, userId?: string): boolean {
    const alert = this.alerts.get(alertId);
    if (!alert || alert.acknowledged) {
      return false;
    }

    alert.acknowledged = true;
    alert.metadata.acknowledgedBy = userId;
    alert.metadata.acknowledgedAt = new Date();

    this.emit('alertAcknowledged', alert);
    return true;
  }

  /**
   * Resolve an alert
   */
  resolveAlert(alertId: string, resolution?: string, userId?: string): boolean {
    const alert = this.alerts.get(alertId);
    if (!alert || alert.resolvedAt) {
      return false;
    }

    alert.resolvedAt = new Date();
    alert.metadata.resolution = resolution;
    alert.metadata.resolvedBy = userId;

    this.emit('alertResolved', alert);
    return true;
  }

  /**
   * Force a health check for all components
   */
  async performHealthCheck(): Promise<HealthReport> {
    await this.checkAllComponents();
    return this.getHealthReport();
  }

  /**
   * Get system capacity and performance predictions
   */
  getPredictions(): {
    capacityExhaustion: { metric: string; estimatedTime: Date; confidence: number }[];
    performanceDegradation: { component: string; prediction: string; confidence: number }[];
    recommendedActions: string[];
  } {
    const predictions = {
      capacityExhaustion: [] as any[],
      performanceDegradation: [] as any[],
      recommendedActions: [] as string[]
    };

    if (!this.config.enablePredictiveAlerts) {
      return predictions;
    }

    // Analyze trends for capacity predictions
    for (const [componentId, component] of this.components.entries()) {
      for (const metric of component.metrics) {
        if (metric.trend === 'degrading' && metric.name.includes('usage')) {
          const history = this.getComponentMetrics(componentId, metric.name);
          if (history.length > 10) {
            const trend = this.calculateTrend(history.slice(-10).map(h => h.value));
            if (trend > 0) {
              const currentValue = metric.value;
              const timeToExhaustion = (100 - currentValue) / trend; // Simplified calculation
              
              predictions.capacityExhaustion.push({
                metric: `${component.name} - ${metric.name}`,
                estimatedTime: new Date(Date.now() + timeToExhaustion * 60 * 60 * 1000),
                confidence: Math.min(0.9, Math.max(0.3, trend / 10))
              });
            }
          }
        }
      }
    }

    // Analyze performance degradation
    for (const [, component] of this.components.entries()) {
      const responseTimeMetric = component.metrics.find(m => m.name === 'response_time');
      if (responseTimeMetric && responseTimeMetric.trend === 'degrading') {
        predictions.performanceDegradation.push({
          component: component.name,
          prediction: 'Response times trending upward, potential performance issues',
          confidence: 0.7
        });
      }

      if (component.errorRate && component.errorRate > 0.05) {
        predictions.performanceDegradation.push({
          component: component.name,
          prediction: 'Error rate increasing, investigate failure patterns',
          confidence: 0.8
        });
      }
    }

    // Generate recommended actions
    if (predictions.capacityExhaustion.length > 0) {
      predictions.recommendedActions.push('Review capacity planning and consider scaling resources');
    }
    if (predictions.performanceDegradation.length > 0) {
      predictions.recommendedActions.push('Investigate performance bottlenecks and optimize critical paths');
    }

    return predictions;
  }

  /**
   * Initialize default system components
   */
  private initializeDefaultComponents(): void {
    const defaultComponents: Omit<SystemComponent, 'lastCheck' | 'health'>[] = [
      {
        id: 'web-frontend',
        name: 'Web Frontend',
        type: 'service',
        status: 'online',
        dependencies: ['api-backend'],
        metrics: []
      },
      {
        id: 'api-backend',
        name: 'API Backend',
        type: 'api',
        status: 'online',
        dependencies: ['database', 'cache', 'queue'],
        metrics: []
      },
      {
        id: 'database',
        name: 'Database',
        type: 'database',
        status: 'online',
        dependencies: [],
        metrics: []
      },
      {
        id: 'cache',
        name: 'Cache Service',
        type: 'cache',
        status: 'online',
        dependencies: [],
        metrics: []
      },
      {
        id: 'queue',
        name: 'Job Queue',
        type: 'queue',
        status: 'online',
        dependencies: [],
        metrics: []
      },
      {
        id: 'storage',
        name: 'File Storage',
        type: 'storage',
        status: 'online',
        dependencies: [],
        metrics: []
      }
    ];

    defaultComponents.forEach(component => {
      this.registerComponent(component);
    });

    // Register default health checkers
    this.registerDefaultHealthCheckers();
  }

  /**
   * Register default health checkers
   */
  private registerDefaultHealthCheckers(): void {
    // Web Frontend health check
    this.registerHealthChecker('web-frontend', async () => {
      try {
        const start = Date.now();
        const response = await fetch('/api/health', { 
          method: 'GET',
          signal: AbortSignal.timeout(this.config.componentTimeouts.service)
        });
        const responseTime = Date.now() - start;
        
        const isHealthy = response.ok;
        
        return {
          status: isHealthy ? 'online' : 'degraded',
          responseTime,
          metrics: [
            {
              name: 'response_time',
              value: responseTime,
              unit: 'ms',
              status: responseTime < 1000 ? 'healthy' : responseTime < 3000 ? 'warning' : 'critical',
              timestamp: new Date(),
              threshold: { warning: 1000, critical: 3000 },
              trend: 'stable'
            },
            {
              name: 'availability',
              value: isHealthy ? 100 : 0,
              unit: '%',
              status: isHealthy ? 'healthy' : 'critical',
              timestamp: new Date(),
              threshold: { warning: 95, critical: 90 },
              trend: 'stable'
            }
          ]
        };
      } catch (error) {
        return {
          status: 'offline',
          metrics: [
            {
              name: 'availability',
              value: 0,
              unit: '%',
              status: 'critical',
              timestamp: new Date(),
              threshold: { warning: 95, critical: 90 },
              trend: 'degrading'
            }
          ]
        };
      }
    });

    // Database health check (simulated)
    this.registerHealthChecker('database', async () => {
      // Simulate database health check
      const connectionTime = Math.random() * 100 + 20;
      const connectionPool = Math.random() * 100;
      
      return {
        status: connectionTime < 200 ? 'online' : 'degraded',
        responseTime: connectionTime,
        metrics: [
          {
            name: 'connection_time',
            value: connectionTime,
            unit: 'ms',
            status: connectionTime < 100 ? 'healthy' : connectionTime < 200 ? 'warning' : 'critical',
            timestamp: new Date(),
            threshold: { warning: 100, critical: 200 },
            trend: 'stable'
          },
          {
            name: 'connection_pool_usage',
            value: connectionPool,
            unit: '%',
            status: connectionPool < 70 ? 'healthy' : connectionPool < 90 ? 'warning' : 'critical',
            timestamp: new Date(),
            threshold: { warning: 70, critical: 90 },
            trend: 'stable'
          }
        ]
      };
    });

    // Add more default health checkers as needed...
  }

  /**
   * Start continuous monitoring
   */
  private startMonitoring(): void {
    this.monitoringInterval = setInterval(() => {
      this.checkAllComponents().catch(error => {
        console.error('Health monitoring error:', error);
        this.emit('monitoringError', error);
      });
    }, this.config.checkInterval);

    // Cleanup old metrics
    setInterval(() => {
      this.cleanupOldMetrics();
    }, 60 * 60 * 1000); // Cleanup every hour
  }

  /**
   * Check health of all registered components
   */
  private async checkAllComponents(): Promise<void> {
    const checkPromises = Array.from(this.components.keys()).map(componentId =>
      this.checkComponent(componentId).catch(error => {
        console.error(`Health check failed for ${componentId}:`, error);
        return null;
      })
    );

    await Promise.all(checkPromises);
  }

  /**
   * Check health of a specific component
   */
  private async checkComponent(componentId: string): Promise<void> {
    const component = this.components.get(componentId);
    if (!component) return;

    const checker = this.healthCheckers.get(componentId);
    if (!checker) return;

    try {
      const healthData = await checker();
      
      // Update component
      const updatedComponent = {
        ...component,
        ...healthData,
        lastCheck: new Date(),
        health: this.calculateComponentHealth(healthData.metrics || [])
      };

      this.components.set(componentId, updatedComponent);

      // Store metrics history
      if (healthData.metrics) {
        healthData.metrics.forEach(metric => {
          this.storeMetric(componentId, metric);
          this.checkMetricAlerts(componentId, metric);
        });
      }

      // Check component status alerts
      this.checkComponentStatusAlerts(updatedComponent);

      this.emit('componentChecked', updatedComponent);

    } catch (error) {
      // Mark component as offline/error
      component.status = 'offline';
      component.lastCheck = new Date();
      component.health = 0;

      this.createAlert(
        'critical',
        `${component.name} Health Check Failed`,
        `Failed to perform health check: ${error instanceof Error ? error.message : 'Unknown error'}`,
        componentId,
        ['Investigate component', 'Check logs', 'Restart service'],
        { error: error instanceof Error ? error.message : 'Unknown error' }
      );
    }
  }

  /**
   * Store a metric in history
   */
  private storeMetric(componentId: string, metric: HealthMetric): void {
    const key = `${componentId}.${metric.name}`;
    
    if (!this.metricHistory.has(key)) {
      this.metricHistory.set(key, []);
    }

    const history = this.metricHistory.get(key)!;
    history.push(metric);

    // Update trend
    if (history.length > 5) {
      const recent = history.slice(-5).map(h => h.value);
      metric.trend = this.determineTrend(recent);
    }

    // Limit history size
    if (history.length > 1000) {
      history.splice(0, history.length - 1000);
    }
  }

  /**
   * Check for metric-based alerts
   */
  private checkMetricAlerts(componentId: string, metric: HealthMetric): void {
    const component = this.components.get(componentId);
    if (!component) return;

    const alertKey = `${componentId}.${metric.name}`;
    const now = new Date();

    // Check if alert is suppressed
    const lastAlert = this.alertSuppressionMap.get(alertKey);
    if (lastAlert && (now.getTime() - lastAlert.getTime()) < this.config.alertCooldown) {
      return;
    }

    let severity: HealthAlert['severity'] | null = null;
    let threshold = 0;

    if (metric.status === 'critical') {
      severity = 'critical';
      threshold = metric.threshold.critical;
    } else if (metric.status === 'warning') {
      severity = 'warning';
      threshold = metric.threshold.warning;
    }

    if (severity) {
      this.alertSuppressionMap.set(alertKey, now);

      this.createAlert(
        severity,
        `${component.name} - ${metric.name} Alert`,
        `${metric.name} is ${metric.value}${metric.unit}, exceeding ${severity} threshold of ${threshold}${metric.unit}`,
        componentId,
        this.getRecommendedActions(componentId, metric.name, severity),
        { 
          metric: metric.name,
          value: metric.value,
          threshold,
          trend: metric.trend
        }
      );
    }
  }

  /**
   * Check for component status alerts
   */
  private checkComponentStatusAlerts(component: SystemComponent): void {
    const previousStatus = this.components.get(component.id)?.status;
    
    if (previousStatus !== component.status) {
      let severity: HealthAlert['severity'] = 'info';
      
      if (component.status === 'offline') {
        severity = 'critical';
      } else if (component.status === 'degraded') {
        severity = 'warning';
      }

      if (severity !== 'info') {
        this.createAlert(
          severity,
          `${component.name} Status Change`,
          `Component status changed from ${previousStatus} to ${component.status}`,
          component.id,
          this.getRecommendedActions(component.id, 'status', severity),
          { previousStatus, newStatus: component.status }
        );
      }
    }
  }

  /**
   * Calculate component health score
   */
  private calculateComponentHealth(metrics: HealthMetric[]): number {
    if (metrics.length === 0) return 100;

    const scores = metrics.map(metric => {
      switch (metric.status) {
        case 'healthy': return 100;
        case 'warning': return 70;
        case 'critical': return 30;
        case 'unknown': return 50;
        default: return 50;
      }
    });

    return scores.reduce((sum, score) => sum + score, 0) / scores.length;
  }

  /**
   * Calculate overall system health
   */
  private calculateOverallHealth(components: SystemComponent[]): number {
    if (components.length === 0) return 100;

    // Weight components by importance (critical services get higher weight)
    const weightedScores = components.map(component => {
      const weight = component.dependencies.length > 0 ? 1.5 : 1.0; // Components with dependencies are more critical
      return component.health * weight;
    });

    const totalWeight = components.reduce((sum, component) => 
      sum + (component.dependencies.length > 0 ? 1.5 : 1.0), 0
    );

    return weightedScores.reduce((sum, score) => sum + score, 0) / totalWeight;
  }

  /**
   * Determine overall system status
   */
  private determineOverallStatus(
    health: number, 
    alerts: HealthAlert[]
  ): HealthReport['status'] {
    const criticalAlerts = alerts.filter(a => a.severity === 'critical');
    const warningAlerts = alerts.filter(a => a.severity === 'warning');

    if (criticalAlerts.length > 0 || health < this.config.healthThresholds.critical) {
      return 'critical';
    } else if (warningAlerts.length > 0 || health < this.config.healthThresholds.warning) {
      return 'warning';
    } else if (health < 95) {
      return 'degraded';
    } else {
      return 'healthy';
    }
  }

  /**
   * Analyze system trends
   */
  private analyzeTrends(): HealthReport['trends'] {
    const performanceMetrics = [];
    const reliabilityMetrics = [];
    const capacityMetrics = [];

    for (const component of this.components.values()) {
      for (const metric of component.metrics) {
        if (metric.name.includes('response_time') || metric.name.includes('latency')) {
          performanceMetrics.push(metric.trend);
        } else if (metric.name.includes('availability') || metric.name.includes('uptime')) {
          reliabilityMetrics.push(metric.trend);
        } else if (metric.name.includes('usage') || metric.name.includes('utilization')) {
          capacityMetrics.push(metric.trend);
        }
      }
    }

    return {
      performance: this.aggregateTrends(performanceMetrics),
      reliability: this.aggregateTrends(reliabilityMetrics),
      capacity: this.aggregateTrends(capacityMetrics)
    };
  }

  /**
   * Generate system recommendations
   */
  private generateRecommendations(
    components: SystemComponent[], 
    alerts: HealthAlert[]
  ): string[] {
    const recommendations: string[] = [];

    // Critical alert recommendations
    const criticalAlerts = alerts.filter(a => a.severity === 'critical');
    if (criticalAlerts.length > 0) {
      recommendations.push('Immediate attention required: resolve critical alerts to restore system stability');
    }

    // Capacity recommendations
    const capacityIssues = components.filter(c => 
      c.metrics.some(m => m.name.includes('usage') && m.value > 80)
    );
    if (capacityIssues.length > 0) {
      recommendations.push('Consider scaling resources for components approaching capacity limits');
    }

    // Performance recommendations
    const performanceIssues = components.filter(c =>
      c.responseTime && c.responseTime > 1000
    );
    if (performanceIssues.length > 0) {
      recommendations.push('Investigate performance bottlenecks in slow-responding components');
    }

    // Reliability recommendations
    const unreliableComponents = components.filter(c => c.health < 90);
    if (unreliableComponents.length > 0) {
      recommendations.push('Review and improve reliability of underperforming components');
    }

    // Default recommendations if system is healthy
    if (recommendations.length === 0) {
      recommendations.push('System is operating within normal parameters - continue monitoring');
      recommendations.push('Consider implementing predictive maintenance based on current trends');
    }

    return recommendations;
  }

  private determineTrend(values: number[]): 'improving' | 'stable' | 'degrading' {
    if (values.length < 3) return 'stable';

    const trend = this.calculateTrend(values);
    
    if (trend > 0.1) return 'degrading';
    if (trend < -0.1) return 'improving';
    return 'stable';
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

  private aggregateTrends(trends: string[]): 'improving' | 'stable' | 'degrading' {
    if (trends.length === 0) return 'stable';

    const improving = trends.filter(t => t === 'improving').length;
    const degrading = trends.filter(t => t === 'degrading').length;

    if (degrading > improving) return 'degrading';
    if (improving > degrading) return 'improving';
    return 'stable';
  }

  private getRecommendedActions(
    _componentId: string, 
    metric: string, 
    _severity: HealthAlert['severity']
  ): string[] {
    const actionMap: Record<string, string[]> = {
      'response_time': [
        'Check for resource bottlenecks',
        'Review recent deployments',
        'Analyze database query performance',
        'Consider scaling resources'
      ],
      'memory_usage': [
        'Investigate memory leaks',
        'Review application memory usage',
        'Consider increasing available memory',
        'Restart service if necessary'
      ],
      'cpu_usage': [
        'Identify CPU-intensive processes',
        'Scale horizontally if possible',
        'Optimize application performance',
        'Review system load'
      ],
      'disk_usage': [
        'Clean up temporary files',
        'Archive old logs',
        'Increase storage capacity',
        'Review data retention policies'
      ],
      'error_rate': [
        'Review application logs',
        'Identify error patterns',
        'Fix underlying issues',
        'Implement error handling'
      ],
      'status': [
        'Check service logs',
        'Verify configuration',
        'Restart service',
        'Contact system administrator'
      ]
    };

    return actionMap[metric] || [
      'Investigate the issue',
      'Check system logs',
      'Contact technical support'
    ];
  }

  private cleanupOldMetrics(): void {
    const cutoffTime = new Date(Date.now() - this.config.metricRetention);

    for (const [key, metrics] of this.metricHistory.entries()) {
      const filtered = metrics.filter(m => m.timestamp > cutoffTime);
      this.metricHistory.set(key, filtered);
    }

    // Clean up resolved alerts older than 7 days
    const alertCutoff = new Date(Date.now() - (7 * 24 * 60 * 60 * 1000));
    for (const [alertId, alert] of this.alerts.entries()) {
      if (alert.resolvedAt && alert.resolvedAt < alertCutoff) {
        this.alerts.delete(alertId);
      }
    }
  }

  private sendAlertNotification(alert: HealthAlert): void {
    // Implement notification sending (email, Slack, webhooks, etc.)
    this.emit('notification', {
      type: 'alert',
      alert,
      channels: this.determineNotificationChannels(alert.severity)
    });
  }

  private determineNotificationChannels(severity: HealthAlert['severity']): string[] {
    switch (severity) {
      case 'critical':
        return ['email', 'sms', 'slack', 'webhook'];
      case 'error':
        return ['email', 'slack', 'webhook'];
      case 'warning':
        return ['slack', 'webhook'];
      case 'info':
        return ['webhook'];
      default:
        return [];
    }
  }

  private generateAlertId(): string {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Stop monitoring and cleanup
   */
  destroy(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    this.components.clear();
    this.alerts.clear();
    this.metricHistory.clear();
    this.alertSuppressionMap.clear();
    this.healthCheckers.clear();

    this.removeAllListeners();
  }
}

// Export singleton instance
export const healthMonitor = new AdvancedHealthMonitor();

export default healthMonitor;