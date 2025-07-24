/**
 * Security validation and protection system
 * Provides API key validation, rate limiting, and security monitoring
 */

import { NextApiRequest, NextApiResponse } from 'next';
import { observabilityLogger } from './observability-logger';

interface SecurityConfig {
  enableRateLimiting: boolean;
  enableApiKeyValidation: boolean;
  enableRequestLogging: boolean;
  rateLimitWindow: number; // minutes
  rateLimitMax: number; // requests per window
  requireApiKeys: string[]; // required environment variables
}

interface RateLimitEntry {
  count: number;
  firstRequest: number;
  lastRequest: number;
}

interface SecurityAlert {
  id: string;
  type: 'rate_limit' | 'invalid_api_key' | 'suspicious_activity' | 'missing_key';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  ip?: string;
  userAgent?: string;
  endpoint?: string;
  timestamp: Date;
  metadata: Record<string, any>;
}

class SecurityManager {
  private config: SecurityConfig;
  private rateLimitStore: Map<string, RateLimitEntry> = new Map();
  private securityAlerts: SecurityAlert[] = [];
  private logger = observabilityLogger.createLogger('Security');

  constructor(config: Partial<SecurityConfig> = {}) {
    this.config = {
      enableRateLimiting: true,
      enableApiKeyValidation: true,
      enableRequestLogging: true,
      rateLimitWindow: 15, // 15 minutes
      rateLimitMax: 100, // 100 requests per 15 minutes
      requireApiKeys: [
        'OPENAI_API_KEY',
        'ELEVENLABS_API_KEY',
        'RUNWAY_API_KEY'
      ],
      ...config
    };

    this.validateEnvironment();
    this.startCleanupInterval();
  }

  /**
   * Validate that all required API keys are present and properly formatted
   */
  private validateEnvironment(): void {
    const missingKeys: string[] = [];
    const invalidKeys: string[] = [];

    this.config.requireApiKeys.forEach(keyName => {
      const keyValue = process.env[keyName];
      
      if (!keyValue) {
        missingKeys.push(keyName);
      } else if (!this.isValidApiKeyFormat(keyName, keyValue)) {
        invalidKeys.push(keyName);
      }
    });

    if (missingKeys.length > 0) {
      this.createSecurityAlert({
        type: 'missing_key',
        severity: 'critical',
        message: `Missing required API keys: ${missingKeys.join(', ')}`,
        metadata: { missingKeys }
      });
      
      this.logger.error('Missing required API keys', {
        missingKeys,
        totalRequired: this.config.requireApiKeys.length
      }, ['security', 'startup']);
    }

    if (invalidKeys.length > 0) {
      this.createSecurityAlert({
        type: 'invalid_api_key',
        severity: 'high',
        message: `Invalid API key format detected: ${invalidKeys.join(', ')}`,
        metadata: { invalidKeys }
      });
      
      this.logger.warn('Invalid API key format detected', {
        invalidKeys,
        hint: 'Check API key format patterns'
      }, ['security', 'startup']);
    }

    if (missingKeys.length === 0 && invalidKeys.length === 0) {
      this.logger.info('Environment validation passed', {
        validatedKeys: this.config.requireApiKeys.length,
        status: 'secure'
      }, ['security', 'startup']);
    }
  }

  /**
   * Validate API key format based on provider patterns
   */
  private isValidApiKeyFormat(keyName: string, keyValue: string): boolean {
    // Check for placeholder values (from .env.example)
    if (keyValue.includes('your_') || keyValue.includes('_here')) {
      return false;
    }

    switch (keyName) {
      case 'OPENAI_API_KEY':
        return keyValue.startsWith('sk-') && keyValue.length > 20;
      case 'ELEVENLABS_API_KEY':
        return keyValue.startsWith('sk_') && keyValue.length > 20;
      case 'RUNWAY_API_KEY':
        return keyValue.startsWith('key_') && keyValue.length > 20;
      default:
        return keyValue.length > 10; // Generic minimum length
    }
  }

  /**
   * Middleware for API route protection
   */
  async protect(req: NextApiRequest, res: NextApiResponse, next: () => void): Promise<boolean> {
    const clientIp = this.getClientIp(req);
    const userAgent = req.headers['user-agent'] || 'unknown';
    const endpoint = req.url || 'unknown';

    this.logger.debug('Security check initiated', {
      ip: clientIp,
      method: req.method,
      endpoint,
      userAgent
    }, ['security', 'request']);

    // Rate limiting check
    if (this.config.enableRateLimiting && !this.checkRateLimit(clientIp, endpoint)) {
      this.createSecurityAlert({
        type: 'rate_limit',
        severity: 'medium',
        message: `Rate limit exceeded for IP: ${clientIp}`,
        ip: clientIp,
        userAgent,
        endpoint,
        metadata: { 
          limit: this.config.rateLimitMax,
          window: this.config.rateLimitWindow
        }
      });

      res.status(429).json({
        error: 'Rate limit exceeded',
        message: `Too many requests. Limit: ${this.config.rateLimitMax} requests per ${this.config.rateLimitWindow} minutes`,
        retryAfter: this.config.rateLimitWindow * 60
      });
      return false;
    }

    // API key validation for generation endpoints
    if (this.isGenerationEndpoint(endpoint) && this.config.enableApiKeyValidation) {
      const validationResult = this.validateApiKeysForEndpoint(endpoint);
      
      if (!validationResult.valid) {
        this.createSecurityAlert({
          type: 'invalid_api_key',
          severity: 'high',
          message: `API key validation failed for endpoint: ${endpoint}`,
          ip: clientIp,
          userAgent,
          endpoint,
          metadata: validationResult
        });

        res.status(503).json({
          error: 'Service unavailable',
          message: 'Required services are not properly configured',
          details: validationResult.missingServices
        });
        return false;
      }
    }

    // Log successful request
    if (this.config.enableRequestLogging) {
      this.logger.info('Request authorized', {
        ip: clientIp,
        method: req.method,
        endpoint,
        userAgent
      }, ['security', 'authorized']);
    }

    next();
    return true;
  }

  /**
   * Check rate limit for IP and endpoint combination
   */
  private checkRateLimit(ip: string, endpoint: string): boolean {
    const key = `${ip}:${endpoint}`;
    const now = Date.now();
    const windowMs = this.config.rateLimitWindow * 60 * 1000;

    const entry = this.rateLimitStore.get(key);

    if (!entry) {
      this.rateLimitStore.set(key, {
        count: 1,
        firstRequest: now,
        lastRequest: now
      });
      return true;
    }

    // Reset if window has passed
    if (now - entry.firstRequest > windowMs) {
      this.rateLimitStore.set(key, {
        count: 1,
        firstRequest: now,
        lastRequest: now
      });
      return true;
    }

    // Increment count
    entry.count++;
    entry.lastRequest = now;

    return entry.count <= this.config.rateLimitMax;
  }

  /**
   * Get client IP address from request
   */
  private getClientIp(req: NextApiRequest): string {
    return (
      req.headers['x-forwarded-for'] ||
      req.headers['x-real-ip'] ||
      req.connection.remoteAddress ||
      'unknown'
    ) as string;
  }

  /**
   * Check if endpoint requires AI service API keys
   */
  private isGenerationEndpoint(endpoint: string): boolean {
    const generationPaths = [
      '/api/audio/generate',
      '/api/images/generate',
      '/api/videos/generate',
      '/api/generate',
      '/api/audio/batch',
      '/api/images/batch',
      '/api/videos/batch'
    ];
    
    return generationPaths.some(path => endpoint.includes(path));
  }

  /**
   * Validate API keys for specific endpoint
   */
  private validateApiKeysForEndpoint(endpoint: string): {
    valid: boolean;
    missingServices: string[];
    details: Record<string, boolean>;
  } {
    const requiredKeys: Record<string, string[]> = {
      '/api/audio': ['ELEVENLABS_API_KEY'],
      '/api/images': ['OPENAI_API_KEY'],
      '/api/videos': ['RUNWAY_API_KEY'],
      '/api/generate': ['OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'RUNWAY_API_KEY']
    };

    let requiredForEndpoint: string[] = [];
    
    for (const [path, keys] of Object.entries(requiredKeys)) {
      if (endpoint.includes(path)) {
        requiredForEndpoint = keys;
        break;
      }
    }

    const missingServices: string[] = [];
    const details: Record<string, boolean> = {};

    requiredForEndpoint.forEach(keyName => {
      const keyValue = process.env[keyName];
      const isValid = keyValue && this.isValidApiKeyFormat(keyName, keyValue);
      
      details[keyName] = isValid;
      
      if (!isValid) {
        const serviceName = keyName.replace('_API_KEY', '').toLowerCase();
        missingServices.push(serviceName);
      }
    });

    return {
      valid: missingServices.length === 0,
      missingServices,
      details
    };
  }

  /**
   * Create security alert
   */
  private createSecurityAlert(alert: Omit<SecurityAlert, 'id' | 'timestamp'>): void {
    const securityAlert: SecurityAlert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ...alert
    };

    this.securityAlerts.push(securityAlert);

    // Keep only last 1000 alerts
    if (this.securityAlerts.length > 1000) {
      this.securityAlerts = this.securityAlerts.slice(-1000);
    }

    this.logger.warn('Security alert created', {
      alertId: securityAlert.id,
      type: securityAlert.type,
      severity: securityAlert.severity,
      message: securityAlert.message
    }, ['security', 'alert']);
  }

  /**
   * Get active security alerts
   */
  getSecurityAlerts(severity?: SecurityAlert['severity']): SecurityAlert[] {
    const recentAlerts = this.securityAlerts.filter(alert => {
      const ageHours = (Date.now() - alert.timestamp.getTime()) / (1000 * 60 * 60);
      return ageHours <= 24; // Last 24 hours
    });

    if (severity) {
      return recentAlerts.filter(alert => alert.severity === severity);
    }

    return recentAlerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Get security status summary
   */
  getSecurityStatus(): {
    status: 'secure' | 'warning' | 'critical';
    apiKeysValid: boolean;
    recentAlerts: number;
    rateLimitActive: boolean;
    recommendations: string[];
  } {
    const recentAlerts = this.getSecurityAlerts();
    const criticalAlerts = recentAlerts.filter(a => a.severity === 'critical');
    const highAlerts = recentAlerts.filter(a => a.severity === 'high');

    let status: 'secure' | 'warning' | 'critical' = 'secure';
    
    if (criticalAlerts.length > 0) {
      status = 'critical';
    } else if (highAlerts.length > 0 || recentAlerts.length > 10) {
      status = 'warning';
    }

    const apiKeysValid = this.config.requireApiKeys.every(keyName => {
      const keyValue = process.env[keyName];
      return keyValue && this.isValidApiKeyFormat(keyName, keyValue);
    });

    const recommendations: string[] = [];
    
    if (!apiKeysValid) {
      recommendations.push('Update invalid or missing API keys');
    }
    
    if (criticalAlerts.length > 0) {
      recommendations.push('Address critical security alerts immediately');
    }
    
    if (recentAlerts.length > 5) {
      recommendations.push('Review recent security alerts for patterns');
    }
    
    if (this.rateLimitStore.size > 100) {
      recommendations.push('Consider implementing IP-based blocking for repeated violations');
    }

    return {
      status,
      apiKeysValid,
      recentAlerts: recentAlerts.length,
      rateLimitActive: this.config.enableRateLimiting,
      recommendations
    };
  }

  /**
   * Update security configuration
   */
  updateConfig(newConfig: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    this.logger.info('Security configuration updated', {
      updatedFields: Object.keys(newConfig),
      newConfig: this.config
    }, ['security', 'config']);
  }

  /**
   * Clear rate limit entries older than window
   */
  private cleanupRateLimits(): void {
    const now = Date.now();
    const windowMs = this.config.rateLimitWindow * 60 * 1000;

    for (const [key, entry] of this.rateLimitStore.entries()) {
      if (now - entry.lastRequest > windowMs) {
        this.rateLimitStore.delete(key);
      }
    }
  }

  /**
   * Start periodic cleanup
   */
  private startCleanupInterval(): void {
    setInterval(() => {
      this.cleanupRateLimits();
    }, 60000); // Clean up every minute
  }

  /**
   * Create middleware function for Next.js API routes
   */
  middleware() {
    return async (req: NextApiRequest, res: NextApiResponse, next: () => void) => {
      return this.protect(req, res, next);
    };
  }
}

// Export singleton instance
export const securityManager = new SecurityManager();

// Helper function for API route protection
export async function withSecurity(
  handler: (req: NextApiRequest, res: NextApiResponse) => Promise<void>
) {
  return async (req: NextApiRequest, res: NextApiResponse) => {
    const isAuthorized = await securityManager.protect(req, res, () => {});
    
    if (isAuthorized) {
      return handler(req, res);
    }
  };
}

export default securityManager;