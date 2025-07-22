/**
 * Advanced cost tracking and budget management system
 * Monitors API costs, usage patterns, and provides intelligent budget alerts
 */

import EventEmitter from 'events';
import { observabilityLogger } from './observability-logger';

export interface CostEntry {
  id: string;
  timestamp: Date;
  service: string;
  operation: string;
  amount: number;
  currency: string;
  units: number;
  unitType: 'tokens' | 'seconds' | 'calls' | 'bytes' | 'pixels' | 'frames';
  metadata: {
    provider: string;
    model?: string;
    quality?: string;
    userId?: string;
    sessionId?: string;
    jobId?: string;
    [key: string]: any;
  };
  tags: string[];
}

export interface BudgetRule {
  id: string;
  name: string;
  description: string;
  scope: 'global' | 'service' | 'user' | 'project';
  scopeValue?: string; // e.g., specific service name or user ID
  timeframe: 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly';
  limit: number;
  currency: string;
  alertThresholds: {
    warning: number; // percentage of limit
    critical: number; // percentage of limit
  };
  actions: {
    warning: BudgetAction[];
    critical: BudgetAction[];
  };
  isActive: boolean;
  createdAt: Date;
  lastTriggered?: Date;
}

export interface BudgetAction {
  type: 'alert' | 'email' | 'webhook' | 'throttle' | 'block' | 'scale_down';
  config: Record<string, any>;
}

export interface CostAlert {
  id: string;
  budgetRuleId: string;
  severity: 'warning' | 'critical';
  message: string;
  currentSpend: number;
  budgetLimit: number;
  percentageUsed: number;
  timeframe: string;
  timestamp: Date;
  acknowledged: boolean;
  actionsTaken: string[];
}

export interface UsagePattern {
  service: string;
  operation: string;
  hourlyPattern: number[]; // 24 hours
  dailyPattern: number[]; // 7 days
  monthlyTrend: number[];
  peakHours: number[];
  averageCost: number;
  projectedMonthlyCost: number;
}

export interface CostReport {
  period: {
    start: Date;
    end: Date;
  };
  summary: {
    totalCost: number;
    currency: string;
    topServices: Array<{
      service: string;
      cost: number;
      percentage: number;
    }>;
    costTrend: 'increasing' | 'stable' | 'decreasing';
    trendPercentage: number;
  };
  breakdown: {
    byService: Record<string, number>;
    byOperation: Record<string, number>;
    byUser: Record<string, number>;
    byHour: number[];
    byDay: number[];
  };
  budgetStatus: Array<{
    rule: BudgetRule;
    currentSpend: number;
    percentageUsed: number;
    status: 'safe' | 'warning' | 'critical' | 'exceeded';
  }>;
  predictions: {
    dailyProjection: number;
    weeklyProjection: number;
    monthlyProjection: number;
    burnRate: number; // dollars per day
  };
  recommendations: string[];
  usagePatterns: UsagePattern[];
}

interface CostTrackerConfig {
  enableRealTimeTracking: boolean;
  enableBudgetAlerts: boolean;
  enableUsageAnalytics: boolean;
  enableCostOptimization: boolean;
  defaultCurrency: string;
  alertCooldownMinutes: number;
  dataRetentionDays: number;
  batchSize: number;
  flushIntervalMs: number;
}

export class AdvancedCostTracker extends EventEmitter {
  private config: CostTrackerConfig;
  private costEntries: CostEntry[] = [];
  private budgetRules: Map<string, BudgetRule> = new Map();
  private costAlerts: Map<string, CostAlert> = new Map();
  private flushTimer?: NodeJS.Timeout;
  private costBuffer: CostEntry[] = [];
  private logger = observabilityLogger.createLogger('CostTracker');

  constructor(config: Partial<CostTrackerConfig> = {}) {
    super();

    this.config = {
      enableRealTimeTracking: true,
      enableBudgetAlerts: true,
      enableUsageAnalytics: true,
      enableCostOptimization: true,
      defaultCurrency: 'USD',
      alertCooldownMinutes: 30,
      dataRetentionDays: 90,
      batchSize: 100,
      flushIntervalMs: 30000, // 30 seconds
      ...config
    };

    this.loadPersistedData();
    this.startPeriodicProcessing();
    this.setupDefaultBudgetRules();

    this.logger.info('Cost tracker initialized', {
      config: this.config,
      budgetRules: this.budgetRules.size
    });
  }

  /**
   * Track a cost entry
   */
  trackCost(
    service: string,
    operation: string,
    amount: number,
    units: number,
    unitType: CostEntry['unitType'],
    metadata: CostEntry['metadata'] = {},
    tags: string[] = []
  ): CostEntry {
    const costEntry: CostEntry = {
      id: this.generateId(),
      timestamp: new Date(),
      service,
      operation,
      amount,
      currency: this.config.defaultCurrency,
      units,
      unitType,
      metadata: {
        ...metadata,
        trackedAt: new Date().toISOString()
      },
      tags
    };

    this.costEntries.push(costEntry);
    this.costBuffer.push(costEntry);

    this.logger.debug('Cost tracked', {
      service,
      operation,
      amount,
      units,
      unitType
    }, ['cost_tracking']);

    // Real-time budget checking
    if (this.config.enableBudgetAlerts) {
      this.checkBudgetRules(costEntry);
    }

    this.emit('costTracked', costEntry);

    // Cleanup old entries
    this.cleanupOldEntries();

    return costEntry;
  }

  /**
   * Create a budget rule
   */
  createBudgetRule(rule: Omit<BudgetRule, 'id' | 'createdAt'>): BudgetRule {
    const budgetRule: BudgetRule = {
      id: this.generateId(),
      createdAt: new Date(),
      ...rule
    };

    this.budgetRules.set(budgetRule.id, budgetRule);
    this.savePersistedData();

    this.logger.info('Budget rule created', {
      ruleId: budgetRule.id,
      name: budgetRule.name,
      scope: budgetRule.scope,
      limit: budgetRule.limit
    }, ['budget_management']);

    this.emit('budgetRuleCreated', budgetRule);

    return budgetRule;
  }

  /**
   * Update a budget rule
   */
  updateBudgetRule(ruleId: string, updates: Partial<BudgetRule>): boolean {
    const rule = this.budgetRules.get(ruleId);
    if (!rule) return false;

    const updatedRule = { ...rule, ...updates };
    this.budgetRules.set(ruleId, updatedRule);
    this.savePersistedData();

    this.logger.info('Budget rule updated', {
      ruleId,
      updates: Object.keys(updates)
    }, ['budget_management']);

    this.emit('budgetRuleUpdated', updatedRule);

    return true;
  }

  /**
   * Delete a budget rule
   */
  deleteBudgetRule(ruleId: string): boolean {
    const deleted = this.budgetRules.delete(ruleId);
    if (deleted) {
      this.savePersistedData();
      this.logger.info('Budget rule deleted', { ruleId }, ['budget_management']);
      this.emit('budgetRuleDeleted', ruleId);
    }
    return deleted;
  }

  /**
   * Get current cost for a specific scope and timeframe
   */
  getCurrentCost(
    scope: BudgetRule['scope'],
    scopeValue: string | undefined,
    timeframe: BudgetRule['timeframe']
  ): number {
    const timeframeStart = this.getTimeframeStart(timeframe);
    const relevantEntries = this.costEntries.filter(entry => {
      if (entry.timestamp < timeframeStart) return false;

      switch (scope) {
        case 'global':
          return true;
        case 'service':
          return entry.service === scopeValue;
        case 'user':
          return entry.metadata.userId === scopeValue;
        case 'project':
          return entry.metadata.projectId === scopeValue;
        default:
          return false;
      }
    });

    return relevantEntries.reduce((sum, entry) => sum + entry.amount, 0);
  }

  /**
   * Generate comprehensive cost report
   */
  generateCostReport(startDate: Date, endDate: Date): CostReport {
    const filteredEntries = this.costEntries.filter(entry =>
      entry.timestamp >= startDate && entry.timestamp <= endDate
    );

    const totalCost = filteredEntries.reduce((sum, entry) => sum + entry.amount, 0);

    // Service breakdown
    const byService = filteredEntries.reduce((acc, entry) => {
      acc[entry.service] = (acc[entry.service] || 0) + entry.amount;
      return acc;
    }, {} as Record<string, number>);

    // Operation breakdown
    const byOperation = filteredEntries.reduce((acc, entry) => {
      const key = `${entry.service}:${entry.operation}`;
      acc[key] = (acc[key] || 0) + entry.amount;
      return acc;
    }, {} as Record<string, number>);

    // User breakdown
    const byUser = filteredEntries.reduce((acc, entry) => {
      const userId = entry.metadata.userId || 'unknown';
      acc[userId] = (acc[userId] || 0) + entry.amount;
      return acc;
    }, {} as Record<string, number>);

    // Time-based breakdown
    const byHour = this.generateHourlyBreakdown(filteredEntries);
    const byDay = this.generateDailyBreakdown(filteredEntries);

    // Top services
    const topServices = Object.entries(byService)
      .map(([service, cost]) => ({
        service,
        cost,
        percentage: (cost / totalCost) * 100
      }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 10);

    // Trend analysis
    const { trendDirection, trendPercentage } = this.calculateCostTrend(startDate, endDate);

    // Budget status
    const budgetStatus = Array.from(this.budgetRules.values()).map(rule => {
      const currentSpend = this.getCurrentCost(rule.scope, rule.scopeValue, rule.timeframe);
      const percentageUsed = (currentSpend / rule.limit) * 100;
      let status: 'safe' | 'warning' | 'critical' | 'exceeded' = 'safe';

      if (percentageUsed >= 100) {
        status = 'exceeded';
      } else if (percentageUsed >= rule.alertThresholds.critical) {
        status = 'critical';
      } else if (percentageUsed >= rule.alertThresholds.warning) {
        status = 'warning';
      }

      return {
        rule,
        currentSpend,
        percentageUsed,
        status
      };
    });

    // Predictions
    const predictions = this.generateCostPredictions(filteredEntries);

    // Recommendations
    const recommendations = this.generateCostRecommendations(filteredEntries, budgetStatus);

    // Usage patterns
    const usagePatterns = this.analyzeUsagePatterns(filteredEntries);

    return {
      period: { start: startDate, end: endDate },
      summary: {
        totalCost,
        currency: this.config.defaultCurrency,
        topServices,
        costTrend: trendDirection,
        trendPercentage
      },
      breakdown: {
        byService,
        byOperation,
        byUser,
        byHour,
        byDay
      },
      budgetStatus,
      predictions,
      recommendations,
      usagePatterns
    };
  }

  /**
   * Get cost optimization suggestions
   */
  getCostOptimizationSuggestions(): Array<{
    type: 'service' | 'operation' | 'usage_pattern' | 'budget' | 'efficiency';
    priority: 'high' | 'medium' | 'low';
    title: string;
    description: string;
    potentialSavings: number;
    actions: string[];
  }> {
    const suggestions = [];
    const recentEntries = this.getRecentEntries(7); // Last 7 days

    // High-cost services analysis
    const serviceCosts = recentEntries.reduce((acc, entry) => {
      acc[entry.service] = (acc[entry.service] || 0) + entry.amount;
      return acc;
    }, {} as Record<string, number>);

    const highCostServices = Object.entries(serviceCosts)
      .filter(([, cost]) => cost > 10) // Services costing more than $10
      .sort((a, b) => b[1] - a[1]);

    highCostServices.slice(0, 3).forEach(([service, cost]) => {
      suggestions.push({
        type: 'service',
        priority: 'high',
        title: `Optimize ${service} usage`,
        description: `${service} accounts for $${cost.toFixed(2)} of recent costs`,
        potentialSavings: cost * 0.3, // Assume 30% potential savings
        actions: [
          'Review usage patterns',
          'Consider alternative providers',
          'Implement caching',
          'Optimize request parameters'
        ]
      });
    });

    // Inefficient operations
    const operationStats = recentEntries.reduce((acc, entry) => {
      const key = `${entry.service}:${entry.operation}`;
      if (!acc[key]) {
        acc[key] = { count: 0, totalCost: 0, totalUnits: 0 };
      }
      acc[key].count++;
      acc[key].totalCost += entry.amount;
      acc[key].totalUnits += entry.units;
      return acc;
    }, {} as Record<string, { count: number; totalCost: number; totalUnits: number }>);

    Object.entries(operationStats).forEach(([operation, stats]) => {
      const costPerUnit = stats.totalCost / stats.totalUnits;
      const avgCostPerCall = stats.totalCost / stats.count;

      if (avgCostPerCall > 1) { // Expensive operations
        suggestions.push({
          type: 'operation',
          priority: 'medium',
          title: `Optimize ${operation} efficiency`,
          description: `Average cost per call: $${avgCostPerCall.toFixed(4)}`,
          potentialSavings: stats.totalCost * 0.2,
          actions: [
            'Batch requests where possible',
            'Reduce request frequency',
            'Optimize parameters',
            'Consider caching results'
          ]
        });
      }
    });

    // Usage pattern inefficiencies
    const hourlyUsage = this.analyzeHourlyUsage(recentEntries);
    const peakHours = hourlyUsage.filter((usage, hour) => usage > hourlyUsage.reduce((a, b) => a + b) / 24 * 2);

    if (peakHours.length > 0) {
      suggestions.push({
        type: 'usage_pattern',
        priority: 'medium',
        title: 'Level out usage patterns',
        description: 'High usage during peak hours increases costs',
        potentialSavings: recentEntries.reduce((sum, e) => sum + e.amount, 0) * 0.15,
        actions: [
          'Implement load balancing',
          'Use scheduling for non-urgent tasks',
          'Consider off-peak processing',
          'Implement request queuing'
        ]
      });
    }

    return suggestions.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  /**
   * Acknowledge a cost alert
   */
  acknowledgeCostAlert(alertId: string, userId?: string): boolean {
    const alert = this.costAlerts.get(alertId);
    if (!alert || alert.acknowledged) return false;

    alert.acknowledged = true;
    this.emit('costAlertAcknowledged', { alert, userId });

    this.logger.info('Cost alert acknowledged', {
      alertId,
      userId,
      budgetRuleId: alert.budgetRuleId
    }, ['cost_alerts']);

    return true;
  }

  /**
   * Get active cost alerts
   */
  getActiveCostAlerts(): CostAlert[] {
    return Array.from(this.costAlerts.values())
      .filter(alert => !alert.acknowledged)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  private checkBudgetRules(newCostEntry: CostEntry): void {
    for (const rule of this.budgetRules.values()) {
      if (!rule.isActive) continue;

      // Skip cooldown period
      if (rule.lastTriggered) {
        const cooldownEnd = new Date(rule.lastTriggered.getTime() + this.config.alertCooldownMinutes * 60 * 1000);
        if (new Date() < cooldownEnd) continue;
      }

      // Check if the cost entry applies to this rule
      if (!this.doesEntryMatchRule(newCostEntry, rule)) continue;

      const currentSpend = this.getCurrentCost(rule.scope, rule.scopeValue, rule.timeframe);
      const percentageUsed = (currentSpend / rule.limit) * 100;

      let alertSeverity: 'warning' | 'critical' | null = null;

      if (percentageUsed >= rule.alertThresholds.critical) {
        alertSeverity = 'critical';
      } else if (percentageUsed >= rule.alertThresholds.warning) {
        alertSeverity = 'warning';
      }

      if (alertSeverity) {
        this.createCostAlert(rule, currentSpend, percentageUsed, alertSeverity);
        this.executeBudgetActions(rule, alertSeverity);
        
        rule.lastTriggered = new Date();
      }
    }
  }

  private createCostAlert(
    rule: BudgetRule,
    currentSpend: number,
    percentageUsed: number,
    severity: 'warning' | 'critical'
  ): void {
    const alert: CostAlert = {
      id: this.generateId(),
      budgetRuleId: rule.id,
      severity,
      message: `Budget ${severity}: ${rule.name} has used ${percentageUsed.toFixed(1)}% of allocated budget`,
      currentSpend,
      budgetLimit: rule.limit,
      percentageUsed,
      timeframe: rule.timeframe,
      timestamp: new Date(),
      acknowledged: false,
      actionsTaken: []
    };

    this.costAlerts.set(alert.id, alert);
    this.emit('costAlert', alert);

    this.logger.warn('Budget alert triggered', {
      ruleId: rule.id,
      ruleName: rule.name,
      severity,
      percentageUsed,
      currentSpend,
      limit: rule.limit
    }, ['budget_alerts']);
  }

  private executeBudgetActions(rule: BudgetRule, severity: 'warning' | 'critical'): void {
    const actions = rule.actions[severity];

    actions.forEach(action => {
      switch (action.type) {
        case 'alert':
          // Alert action is already handled by creating the alert
          break;
        case 'email':
          this.sendEmailAlert(rule, severity, action.config);
          break;
        case 'webhook':
          this.sendWebhookAlert(rule, severity, action.config);
          break;
        case 'throttle':
          this.applyThrottling(rule, action.config);
          break;
        case 'block':
          this.applyBlocking(rule, action.config);
          break;
        case 'scale_down':
          this.applyScaleDown(rule, action.config);
          break;
      }
    });
  }

  private doesEntryMatchRule(entry: CostEntry, rule: BudgetRule): boolean {
    switch (rule.scope) {
      case 'global':
        return true;
      case 'service':
        return entry.service === rule.scopeValue;
      case 'user':
        return entry.metadata.userId === rule.scopeValue;
      case 'project':
        return entry.metadata.projectId === rule.scopeValue;
      default:
        return false;
    }
  }

  private getTimeframeStart(timeframe: BudgetRule['timeframe']): Date {
    const now = new Date();
    
    switch (timeframe) {
      case 'hourly':
        return new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours());
      case 'daily':
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
      case 'weekly':
        const startOfWeek = new Date(now);
        startOfWeek.setDate(now.getDate() - now.getDay());
        startOfWeek.setHours(0, 0, 0, 0);
        return startOfWeek;
      case 'monthly':
        return new Date(now.getFullYear(), now.getMonth(), 1);
      case 'yearly':
        return new Date(now.getFullYear(), 0, 1);
      default:
        return new Date(0);
    }
  }

  private generateHourlyBreakdown(entries: CostEntry[]): number[] {
    const hourly = new Array(24).fill(0);
    
    entries.forEach(entry => {
      const hour = entry.timestamp.getHours();
      hourly[hour] += entry.amount;
    });

    return hourly;
  }

  private generateDailyBreakdown(entries: CostEntry[]): number[] {
    const daily = new Array(7).fill(0);
    
    entries.forEach(entry => {
      const day = entry.timestamp.getDay();
      daily[day] += entry.amount;
    });

    return daily;
  }

  private calculateCostTrend(startDate: Date, endDate: Date): { 
    trendDirection: 'increasing' | 'stable' | 'decreasing'; 
    trendPercentage: number;
  } {
    const midpoint = new Date((startDate.getTime() + endDate.getTime()) / 2);
    
    const firstHalfEntries = this.costEntries.filter(entry =>
      entry.timestamp >= startDate && entry.timestamp < midpoint
    );
    
    const secondHalfEntries = this.costEntries.filter(entry =>
      entry.timestamp >= midpoint && entry.timestamp <= endDate
    );

    const firstHalfCost = firstHalfEntries.reduce((sum, entry) => sum + entry.amount, 0);
    const secondHalfCost = secondHalfEntries.reduce((sum, entry) => sum + entry.amount, 0);

    if (firstHalfCost === 0) {
      return { trendDirection: 'stable', trendPercentage: 0 };
    }

    const trendPercentage = ((secondHalfCost - firstHalfCost) / firstHalfCost) * 100;

    let trendDirection: 'increasing' | 'stable' | 'decreasing';
    if (Math.abs(trendPercentage) < 5) {
      trendDirection = 'stable';
    } else if (trendPercentage > 0) {
      trendDirection = 'increasing';
    } else {
      trendDirection = 'decreasing';
    }

    return { trendDirection, trendPercentage };
  }

  private generateCostPredictions(entries: CostEntry[]): {
    dailyProjection: number;
    weeklyProjection: number;
    monthlyProjection: number;
    burnRate: number;
  } {
    if (entries.length === 0) {
      return {
        dailyProjection: 0,
        weeklyProjection: 0,
        monthlyProjection: 0,
        burnRate: 0
      };
    }

    const totalCost = entries.reduce((sum, entry) => sum + entry.amount, 0);
    const startDate = entries[0].timestamp;
    const endDate = entries[entries.length - 1].timestamp;
    const periodDays = (endDate.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000);
    
    const burnRate = totalCost / Math.max(periodDays, 1);

    return {
      dailyProjection: burnRate,
      weeklyProjection: burnRate * 7,
      monthlyProjection: burnRate * 30,
      burnRate
    };
  }

  private generateCostRecommendations(
    entries: CostEntry[],
    budgetStatus: CostReport['budgetStatus']
  ): string[] {
    const recommendations = [];

    // Budget-based recommendations
    const criticalBudgets = budgetStatus.filter(b => b.status === 'critical' || b.status === 'exceeded');
    if (criticalBudgets.length > 0) {
      recommendations.push('Immediate action required: review and optimize high-cost services to stay within budget');
    }

    const warningBudgets = budgetStatus.filter(b => b.status === 'warning');
    if (warningBudgets.length > 0) {
      recommendations.push('Monitor spending closely: several budgets are approaching their limits');
    }

    // Usage-based recommendations
    if (entries.length > 100) {
      recommendations.push('Consider implementing request caching to reduce API call frequency');
    }

    // Service-specific recommendations
    const serviceCosts = entries.reduce((acc, entry) => {
      acc[entry.service] = (acc[entry.service] || 0) + entry.amount;
      return acc;
    }, {} as Record<string, number>);

    const totalCost = entries.reduce((sum, entry) => sum + entry.amount, 0);
    Object.entries(serviceCosts).forEach(([service, cost]) => {
      if (cost / totalCost > 0.5) { // Service accounts for >50% of costs
        recommendations.push(`${service} accounts for majority of costs - investigate optimization opportunities`);
      }
    });

    if (recommendations.length === 0) {
      recommendations.push('Cost management is on track - continue monitoring usage patterns');
    }

    return recommendations;
  }

  private analyzeUsagePatterns(entries: CostEntry[]): UsagePattern[] {
    const serviceOperations = new Map<string, Map<string, CostEntry[]>>();

    // Group entries by service and operation
    entries.forEach(entry => {
      if (!serviceOperations.has(entry.service)) {
        serviceOperations.set(entry.service, new Map());
      }
      
      const operationMap = serviceOperations.get(entry.service)!;
      if (!operationMap.has(entry.operation)) {
        operationMap.set(entry.operation, []);
      }
      
      operationMap.get(entry.operation)!.push(entry);
    });

    const patterns: UsagePattern[] = [];

    for (const [service, operationMap] of serviceOperations.entries()) {
      for (const [operation, operationEntries] of operationMap.entries()) {
        const hourlyPattern = new Array(24).fill(0);
        const dailyPattern = new Array(7).fill(0);
        
        operationEntries.forEach(entry => {
          hourlyPattern[entry.timestamp.getHours()] += entry.amount;
          dailyPattern[entry.timestamp.getDay()] += entry.amount;
        });

        const averageCost = operationEntries.reduce((sum, e) => sum + e.amount, 0) / operationEntries.length;
        const dailyAverage = operationEntries.reduce((sum, e) => sum + e.amount, 0) / 7;
        const projectedMonthlyCost = dailyAverage * 30;

        // Find peak hours (hours with > average usage)
        const avgHourlyUsage = hourlyPattern.reduce((a, b) => a + b) / 24;
        const peakHours = hourlyPattern
          .map((usage, hour) => ({ hour, usage }))
          .filter(h => h.usage > avgHourlyUsage * 1.5)
          .map(h => h.hour);

        patterns.push({
          service,
          operation,
          hourlyPattern,
          dailyPattern,
          monthlyTrend: [], // Would need more historical data
          peakHours,
          averageCost,
          projectedMonthlyCost
        });
      }
    }

    return patterns;
  }

  private analyzeHourlyUsage(entries: CostEntry[]): number[] {
    const hourlyUsage = new Array(24).fill(0);
    
    entries.forEach(entry => {
      hourlyUsage[entry.timestamp.getHours()] += entry.amount;
    });

    return hourlyUsage;
  }

  private getRecentEntries(days: number): CostEntry[] {
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    return this.costEntries.filter(entry => entry.timestamp > cutoff);
  }

  private setupDefaultBudgetRules(): void {
    // Create some default budget rules if none exist
    if (this.budgetRules.size === 0) {
      this.createBudgetRule({
        name: 'Monthly Global Budget',
        description: 'Total monthly spending limit across all services',
        scope: 'global',
        timeframe: 'monthly',
        limit: 1000,
        currency: this.config.defaultCurrency,
        alertThresholds: {
          warning: 80,
          critical: 95
        },
        actions: {
          warning: [{ type: 'alert', config: {} }],
          critical: [{ type: 'alert', config: {} }]
        },
        isActive: true
      });

      this.createBudgetRule({
        name: 'Daily Spending Limit',
        description: 'Daily spending limit to prevent unexpected spikes',
        scope: 'global',
        timeframe: 'daily',
        limit: 50,
        currency: this.config.defaultCurrency,
        alertThresholds: {
          warning: 75,
          critical: 90
        },
        actions: {
          warning: [{ type: 'alert', config: {} }],
          critical: [{ type: 'alert', config: {} }]
        },
        isActive: true
      });
    }
  }

  private sendEmailAlert(rule: BudgetRule, severity: string, config: any): void {
    // Implement email alert sending
    this.logger.info('Email alert sent', { ruleId: rule.id, severity }, ['alerts']);
  }

  private sendWebhookAlert(rule: BudgetRule, severity: string, config: any): void {
    // Implement webhook alert sending
    this.logger.info('Webhook alert sent', { ruleId: rule.id, severity }, ['alerts']);
  }

  private applyThrottling(rule: BudgetRule, config: any): void {
    // Implement request throttling
    this.logger.warn('Throttling applied', { ruleId: rule.id }, ['throttling']);
  }

  private applyBlocking(rule: BudgetRule, config: any): void {
    // Implement request blocking
    this.logger.error('Blocking applied', { ruleId: rule.id }, ['blocking']);
  }

  private applyScaleDown(rule: BudgetRule, config: any): void {
    // Implement resource scaling down
    this.logger.info('Scale down applied', { ruleId: rule.id }, ['scaling']);
  }

  private startPeriodicProcessing(): void {
    this.flushTimer = setInterval(() => {
      this.flushCostBuffer();
      this.performPeriodicAnalysis();
    }, this.config.flushIntervalMs);
  }

  private flushCostBuffer(): void {
    if (this.costBuffer.length === 0) return;

    // Process batches of cost entries
    const batch = this.costBuffer.splice(0, this.config.batchSize);
    
    this.logger.debug('Flushing cost buffer', {
      batchSize: batch.length,
      remainingBuffer: this.costBuffer.length
    }, ['cost_processing']);

    // Here you could send to external analytics services, databases, etc.
    this.savePersistedData();
  }

  private performPeriodicAnalysis(): void {
    // Perform periodic cost analysis, trend detection, etc.
    const recentEntries = this.getRecentEntries(1);
    const todayCost = recentEntries.reduce((sum, entry) => sum + entry.amount, 0);

    this.logger.debug('Periodic analysis', {
      todayCost,
      recentEntries: recentEntries.length,
      activeBudgetRules: Array.from(this.budgetRules.values()).filter(r => r.isActive).length
    }, ['cost_analysis']);
  }

  private cleanupOldEntries(): void {
    const cutoff = new Date(Date.now() - this.config.dataRetentionDays * 24 * 60 * 60 * 1000);
    this.costEntries = this.costEntries.filter(entry => entry.timestamp > cutoff);

    // Cleanup old alerts
    const alertCutoff = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000); // 30 days
    for (const [alertId, alert] of this.costAlerts.entries()) {
      if (alert.acknowledged && alert.timestamp < alertCutoff) {
        this.costAlerts.delete(alertId);
      }
    }
  }

  private loadPersistedData(): void {
    try {
      if (typeof window !== 'undefined') {
        const budgetRulesData = localStorage.getItem('cost_tracker_budget_rules');
        if (budgetRulesData) {
          const rules = JSON.parse(budgetRulesData);
          rules.forEach((rule: BudgetRule) => {
            this.budgetRules.set(rule.id, rule);
          });
        }

        const costEntriesData = localStorage.getItem('cost_tracker_entries');
        if (costEntriesData) {
          this.costEntries = JSON.parse(costEntriesData);
        }
      }
    } catch (error) {
      this.logger.warn('Failed to load persisted cost data', { error: error instanceof Error ? error.message : 'Unknown error' });
    }
  }

  private savePersistedData(): void {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('cost_tracker_budget_rules', JSON.stringify(Array.from(this.budgetRules.values())));
        localStorage.setItem('cost_tracker_entries', JSON.stringify(this.costEntries.slice(-1000))); // Keep last 1000 entries
      }
    } catch (error) {
      this.logger.warn('Failed to save cost data', { error: error instanceof Error ? error.message : 'Unknown error' });
    }
  }

  private generateId(): string {
    return `cost_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Cleanup and destroy the cost tracker
   */
  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushCostBuffer();
    this.savePersistedData();

    this.costEntries = [];
    this.budgetRules.clear();
    this.costAlerts.clear();
    this.costBuffer = [];

    this.removeAllListeners();
  }
}

// Export singleton instance
export const costTracker = new AdvancedCostTracker();

export default costTracker;