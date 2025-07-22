/**
 * Comprehensive logging and observability system
 * Provides structured logging, distributed tracing, and operational insights
 */

export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  message: string;
  context: string;
  traceId?: string;
  spanId?: string;
  userId?: string;
  sessionId?: string;
  metadata: Record<string, any>;
  tags: string[];
  error?: {
    name: string;
    message: string;
    stack?: string;
    code?: string;
  };
}

export interface TraceSpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  operationName: string;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  status: 'started' | 'completed' | 'errored' | 'cancelled';
  tags: Record<string, any>;
  logs: LogEntry[];
  error?: Error;
}

export interface ObservabilityMetrics {
  totalLogs: number;
  logsByLevel: Record<LogLevel, number>;
  totalTraces: number;
  averageTraceDuration: number;
  errorRate: number;
  topErrors: Array<{ error: string; count: number }>;
  topOperations: Array<{ operation: string; count: number; avgDuration: number }>;
  performanceTrends: Array<{ timestamp: Date; averageLatency: number; throughput: number }>;
}

interface LoggerConfig {
  level: LogLevel;
  enableTracing: boolean;
  enableConsoleOutput: boolean;
  enableRemoteLogging: boolean;
  enablePerformanceTracking: boolean;
  maxLogEntries: number;
  maxTraceSpans: number;
  remoteEndpoint?: string;
  batchSize: number;
  flushInterval: number;
  enableSampling: boolean;
  samplingRate: number;
}

export class AdvancedObservabilityLogger {
  private config: LoggerConfig;
  private logEntries: LogEntry[] = [];
  private traceSpans: Map<string, TraceSpan> = new Map();
  private activeSpans: Map<string, TraceSpan> = new Map();
  private flushTimer?: NodeJS.Timeout;
  private logBuffer: LogEntry[] = [];
  private sessionId: string;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      level: 'info',
      enableTracing: true,
      enableConsoleOutput: true,
      enableRemoteLogging: false,
      enablePerformanceTracking: true,
      maxLogEntries: 10000,
      maxTraceSpans: 1000,
      batchSize: 100,
      flushInterval: 5000, // 5 seconds
      enableSampling: false,
      samplingRate: 0.1, // 10%
      ...config
    };

    this.sessionId = this.generateId();
    this.startPeriodicFlush();
    this.setupErrorHandlers();
  }

  /**
   * Create a logger instance with context
   */
  createLogger(context: string): Logger {
    return new Logger(this, context);
  }

  /**
   * Start a new trace span
   */
  startSpan(operationName: string, parentSpanId?: string, tags: Record<string, any> = {}): TraceSpan {
    if (!this.config.enableTracing) {
      return this.createDummySpan(operationName);
    }

    if (this.config.enableSampling && Math.random() > this.config.samplingRate) {
      return this.createDummySpan(operationName);
    }

    const traceId = parentSpanId ? 
      this.findTraceIdBySpanId(parentSpanId) || this.generateId() : 
      this.generateId();
    
    const spanId = this.generateId();

    const span: TraceSpan = {
      traceId,
      spanId,
      parentSpanId,
      operationName,
      startTime: new Date(),
      status: 'started',
      tags: { ...tags, sessionId: this.sessionId },
      logs: []
    };

    this.activeSpans.set(spanId, span);
    return span;
  }

  /**
   * Finish a trace span
   */
  finishSpan(span: TraceSpan, status: TraceSpan['status'] = 'completed', error?: Error): void {
    if (!span.spanId || span.status !== 'started') return;

    span.endTime = new Date();
    span.duration = span.endTime.getTime() - span.startTime.getTime();
    span.status = status;

    if (error) {
      span.error = error;
      span.tags.error = true;
    }

    this.activeSpans.delete(span.spanId);
    this.traceSpans.set(span.spanId, span);

    // Log span completion
    this.log('debug', `Span completed: ${span.operationName}`, 'tracing', {
      traceId: span.traceId,
      spanId: span.spanId,
      duration: span.duration,
      status: span.status
    });

    // Cleanup old spans
    this.cleanupSpans();
  }

  /**
   * Log an entry
   */
  log(
    level: LogLevel,
    message: string,
    context: string,
    metadata: Record<string, any> = {},
    tags: string[] = [],
    error?: Error,
    traceId?: string,
    spanId?: string
  ): void {
    if (!this.shouldLog(level)) return;

    const logEntry: LogEntry = {
      timestamp: new Date(),
      level,
      message,
      context,
      traceId,
      spanId,
      sessionId: this.sessionId,
      metadata: {
        ...metadata,
        userAgent: typeof window !== 'undefined' ? navigator.userAgent : undefined,
        url: typeof window !== 'undefined' ? window.location.href : undefined
      },
      tags,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
        code: (error as any).code
      } : undefined
    };

    // Add to active span if available
    if (spanId) {
      const span = this.activeSpans.get(spanId);
      if (span) {
        span.logs.push(logEntry);
      }
    }

    this.logEntries.push(logEntry);
    this.logBuffer.push(logEntry);

    // Console output
    if (this.config.enableConsoleOutput) {
      this.outputToConsole(logEntry);
    }

    // Immediate flush for high severity logs
    if (level === 'error' || level === 'fatal') {
      this.flushLogs();
    }

    // Cleanup old entries
    this.cleanupLogs();
  }

  /**
   * Trace an async operation
   */
  async traceOperation<T>(
    operationName: string,
    operation: (span: TraceSpan) => Promise<T>,
    parentSpanId?: string,
    tags: Record<string, any> = {}
  ): Promise<T> {
    const span = this.startSpan(operationName, parentSpanId, tags);

    try {
      const result = await operation(span);
      this.finishSpan(span, 'completed');
      return result;
    } catch (error) {
      this.finishSpan(span, 'errored', error as Error);
      throw error;
    }
  }

  /**
   * Get observability metrics
   */
  getMetrics(): ObservabilityMetrics {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    const recentLogs = this.logEntries.filter(log => log.timestamp > oneHourAgo);
    const recentSpans = Array.from(this.traceSpans.values())
      .filter(span => span.startTime > oneHourAgo);

    const logsByLevel = recentLogs.reduce((acc, log) => {
      acc[log.level] = (acc[log.level] || 0) + 1;
      return acc;
    }, {} as Record<LogLevel, number>);

    const errorLogs = recentLogs.filter(log => log.error);
    const errorRate = recentLogs.length > 0 ? errorLogs.length / recentLogs.length : 0;

    const topErrors = this.getTopErrors(errorLogs);
    const topOperations = this.getTopOperations(recentSpans);
    const performanceTrends = this.getPerformanceTrends();

    const completedSpans = recentSpans.filter(span => span.duration !== undefined);
    const averageTraceDuration = completedSpans.length > 0 
      ? completedSpans.reduce((sum, span) => sum + (span.duration || 0), 0) / completedSpans.length
      : 0;

    return {
      totalLogs: recentLogs.length,
      logsByLevel,
      totalTraces: recentSpans.length,
      averageTraceDuration,
      errorRate,
      topErrors,
      topOperations,
      performanceTrends
    };
  }

  /**
   * Search logs with filters
   */
  searchLogs(filters: {
    level?: LogLevel[];
    context?: string[];
    timeRange?: { start: Date; end: Date };
    message?: string;
    traceId?: string;
    userId?: string;
    tags?: string[];
    limit?: number;
  }): LogEntry[] {
    let results = this.logEntries;

    if (filters.level) {
      results = results.filter(log => filters.level!.includes(log.level));
    }

    if (filters.context) {
      results = results.filter(log => filters.context!.includes(log.context));
    }

    if (filters.timeRange) {
      results = results.filter(log => 
        log.timestamp >= filters.timeRange!.start && 
        log.timestamp <= filters.timeRange!.end
      );
    }

    if (filters.message) {
      const searchTerm = filters.message.toLowerCase();
      results = results.filter(log => 
        log.message.toLowerCase().includes(searchTerm)
      );
    }

    if (filters.traceId) {
      results = results.filter(log => log.traceId === filters.traceId);
    }

    if (filters.userId) {
      results = results.filter(log => log.userId === filters.userId);
    }

    if (filters.tags && filters.tags.length > 0) {
      results = results.filter(log => 
        filters.tags!.some(tag => log.tags.includes(tag))
      );
    }

    // Sort by timestamp descending
    results.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    if (filters.limit) {
      results = results.slice(0, filters.limit);
    }

    return results;
  }

  /**
   * Get trace by ID
   */
  getTrace(traceId: string): TraceSpan[] {
    return Array.from(this.traceSpans.values())
      .filter(span => span.traceId === traceId)
      .sort((a, b) => a.startTime.getTime() - b.startTime.getTime());
  }

  /**
   * Export logs for analysis
   */
  exportLogs(format: 'json' | 'csv' = 'json'): string {
    const data = {
      sessionId: this.sessionId,
      exportTime: new Date(),
      logs: this.logEntries,
      traces: Array.from(this.traceSpans.values()),
      metrics: this.getMetrics()
    };

    if (format === 'json') {
      return JSON.stringify(data, null, 2);
    }

    // CSV format for logs
    const headers = ['timestamp', 'level', 'message', 'context', 'traceId', 'spanId'];
    const csvLines = [headers.join(',')];

    this.logEntries.forEach(log => {
      const row = [
        log.timestamp.toISOString(),
        log.level,
        `"${log.message.replace(/"/g, '""')}"`,
        log.context,
        log.traceId || '',
        log.spanId || ''
      ];
      csvLines.push(row.join(','));
    });

    return csvLines.join('\n');
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['trace', 'debug', 'info', 'warn', 'error', 'fatal'];
    const currentLevelIndex = levels.indexOf(this.config.level);
    const messageLevelIndex = levels.indexOf(level);
    
    return messageLevelIndex >= currentLevelIndex;
  }

  private outputToConsole(logEntry: LogEntry): void {
    const timestamp = logEntry.timestamp.toISOString();
    const prefix = `[${timestamp}] ${logEntry.level.toUpperCase()} [${logEntry.context}]`;
    const message = `${prefix} ${logEntry.message}`;

    switch (logEntry.level) {
      case 'trace':
      case 'debug':
        console.debug(message, logEntry.metadata);
        break;
      case 'info':
        console.info(message, logEntry.metadata);
        break;
      case 'warn':
        console.warn(message, logEntry.metadata);
        break;
      case 'error':
      case 'fatal':
        console.error(message, logEntry.metadata, logEntry.error);
        break;
    }
  }

  private startPeriodicFlush(): void {
    this.flushTimer = setInterval(() => {
      this.flushLogs();
    }, this.config.flushInterval);
  }

  private async flushLogs(): Promise<void> {
    if (this.logBuffer.length === 0) return;

    const logsToFlush = this.logBuffer.splice(0, this.config.batchSize);

    if (this.config.enableRemoteLogging && this.config.remoteEndpoint) {
      try {
        await fetch(this.config.remoteEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            sessionId: this.sessionId,
            logs: logsToFlush
          })
        });
      } catch (error) {
        console.warn('Failed to send logs to remote endpoint:', error);
        // Put logs back in buffer for retry
        this.logBuffer.unshift(...logsToFlush);
      }
    }

    // Store in local storage for persistence
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('observability_logs') || '[]';
        const existingLogs = JSON.parse(stored);
        const updatedLogs = [...existingLogs, ...logsToFlush].slice(-1000); // Keep last 1000 logs
        localStorage.setItem('observability_logs', JSON.stringify(updatedLogs));
      } catch (error) {
        console.warn('Failed to store logs locally:', error);
      }
    }
  }

  private cleanupLogs(): void {
    if (this.logEntries.length > this.config.maxLogEntries) {
      this.logEntries = this.logEntries.slice(-this.config.maxLogEntries);
    }
  }

  private cleanupSpans(): void {
    if (this.traceSpans.size > this.config.maxTraceSpans) {
      const spans = Array.from(this.traceSpans.entries())
        .sort(([, a], [, b]) => b.startTime.getTime() - a.startTime.getTime())
        .slice(0, this.config.maxTraceSpans);
      
      this.traceSpans.clear();
      spans.forEach(([id, span]) => {
        this.traceSpans.set(id, span);
      });
    }
  }

  private findTraceIdBySpanId(spanId: string): string | undefined {
    const span = this.activeSpans.get(spanId) || this.traceSpans.get(spanId);
    return span?.traceId;
  }

  private createDummySpan(operationName: string): TraceSpan {
    return {
      traceId: '',
      spanId: '',
      operationName,
      startTime: new Date(),
      status: 'started',
      tags: {},
      logs: []
    };
  }

  private getTopErrors(errorLogs: LogEntry[]): Array<{ error: string; count: number }> {
    const errorCounts = new Map<string, number>();

    errorLogs.forEach(log => {
      if (log.error) {
        const key = `${log.error.name}: ${log.error.message}`;
        errorCounts.set(key, (errorCounts.get(key) || 0) + 1);
      }
    });

    return Array.from(errorCounts.entries())
      .map(([error, count]) => ({ error, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }

  private getTopOperations(spans: TraceSpan[]): Array<{ operation: string; count: number; avgDuration: number }> {
    const operationStats = new Map<string, { count: number; totalDuration: number }>();

    spans.forEach(span => {
      if (span.duration !== undefined) {
        const stats = operationStats.get(span.operationName) || { count: 0, totalDuration: 0 };
        stats.count++;
        stats.totalDuration += span.duration;
        operationStats.set(span.operationName, stats);
      }
    });

    return Array.from(operationStats.entries())
      .map(([operation, stats]) => ({
        operation,
        count: stats.count,
        avgDuration: stats.totalDuration / stats.count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }

  private getPerformanceTrends(): Array<{ timestamp: Date; averageLatency: number; throughput: number }> {
    // Simplified implementation - would use more sophisticated time series analysis in production
    const now = new Date();
    const trends: Array<{ timestamp: Date; averageLatency: number; throughput: number }> = [];

    for (let i = 23; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000)); // Hourly buckets
      const startTime = new Date(timestamp.getTime() - 30 * 60 * 1000);
      const endTime = new Date(timestamp.getTime() + 30 * 60 * 1000);

      const spansInPeriod = Array.from(this.traceSpans.values())
        .filter(span => span.startTime >= startTime && span.startTime <= endTime && span.duration);

      const averageLatency = spansInPeriod.length > 0 
        ? spansInPeriod.reduce((sum, span) => sum + (span.duration || 0), 0) / spansInPeriod.length
        : 0;

      const throughput = spansInPeriod.length; // Operations per hour

      trends.push({ timestamp, averageLatency, throughput });
    }

    return trends;
  }

  private setupErrorHandlers(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('error', (event) => {
        this.log('error', 'Unhandled JavaScript error', 'global', {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        }, ['unhandled', 'javascript'], event.error);
      });

      window.addEventListener('unhandledrejection', (event) => {
        this.log('error', 'Unhandled promise rejection', 'global', {
          reason: event.reason
        }, ['unhandled', 'promise'], event.reason);
      });
    }
  }

  private generateId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Cleanup and destroy the logger
   */
  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushLogs().catch(console.warn);

    this.logEntries = [];
    this.traceSpans.clear();
    this.activeSpans.clear();
    this.logBuffer = [];
  }
}

/**
 * Context-specific logger instance
 */
export class Logger {
  constructor(
    private observabilityLogger: AdvancedObservabilityLogger,
    private context: string
  ) {}

  trace(message: string, metadata?: Record<string, any>, tags?: string[], traceId?: string, spanId?: string): void {
    this.observabilityLogger.log('trace', message, this.context, metadata, tags, undefined, traceId, spanId);
  }

  debug(message: string, metadata?: Record<string, any>, tags?: string[], traceId?: string, spanId?: string): void {
    this.observabilityLogger.log('debug', message, this.context, metadata, tags, undefined, traceId, spanId);
  }

  info(message: string, metadata?: Record<string, any>, tags?: string[], traceId?: string, spanId?: string): void {
    this.observabilityLogger.log('info', message, this.context, metadata, tags, undefined, traceId, spanId);
  }

  warn(message: string, metadata?: Record<string, any>, tags?: string[], traceId?: string, spanId?: string): void {
    this.observabilityLogger.log('warn', message, this.context, metadata, tags, undefined, traceId, spanId);
  }

  error(message: string, error?: Error, metadata?: Record<string, any>, tags?: string[], traceId?: string, spanId?: string): void {
    this.observabilityLogger.log('error', message, this.context, metadata, tags, error, traceId, spanId);
  }

  fatal(message: string, error?: Error, metadata?: Record<string, any>, tags?: string[], traceId?: string, spanId?: string): void {
    this.observabilityLogger.log('fatal', message, this.context, metadata, tags, error, traceId, spanId);
  }

  startSpan(operationName: string, parentSpanId?: string, tags?: Record<string, any>): TraceSpan {
    return this.observabilityLogger.startSpan(operationName, parentSpanId, tags);
  }

  finishSpan(span: TraceSpan, status?: TraceSpan['status'], error?: Error): void {
    this.observabilityLogger.finishSpan(span, status, error);
  }

  async traceOperation<T>(
    operationName: string,
    operation: (span: TraceSpan) => Promise<T>,
    parentSpanId?: string,
    tags?: Record<string, any>
  ): Promise<T> {
    return this.observabilityLogger.traceOperation(operationName, operation, parentSpanId, tags);
  }
}

// Export singleton instance
export const observabilityLogger = new AdvancedObservabilityLogger();

export default observabilityLogger;