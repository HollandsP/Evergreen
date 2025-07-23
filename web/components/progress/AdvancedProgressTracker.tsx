/**
 * Advanced progress tracking component with detailed status updates
 * Provides comprehensive insights into pipeline progress and performance
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  Pause, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Activity,
  Zap,
  Target,
  Timer,
  DollarSign,
  Cpu,
  HardDrive,
  Wifi
} from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { performanceMonitor } from '../../lib/performance-monitor';

interface ProgressStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  estimatedDuration?: number;
  actualDuration?: number;
  dependencies?: string[];
  cost?: number;
  resourceUsage?: {
    cpu: number;
    memory: number;
    disk: number;
    network: number;
  };
  metadata?: any;
  substeps?: ProgressStep[];
}

interface PipelineProgress {
  jobId: string;
  totalSteps: number;
  completedSteps: number;
  currentStep?: ProgressStep;
  steps: ProgressStep[];
  overallProgress: number;
  estimatedCompletion: Date;
  actualStartTime: Date;
  status: 'initializing' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';
  performance: {
    averageStepTime: number;
    totalCost: number;
    resourceEfficiency: number;
    errorRate: number;
    throughput: number;
  };
  errors: Array<{
    step: string;
    message: string;
    timestamp: Date;
    severity: 'low' | 'medium' | 'high' | 'critical';
  }>;
  warnings: Array<{
    step: string;
    message: string;
    timestamp: Date;
  }>;
}

interface ProgressTrackerProps {
  jobId: string;
  showDetailedSteps?: boolean;
  showPerformanceMetrics?: boolean;
  showResourceUsage?: boolean;
  showCostTracking?: boolean;
  enableRealTimeUpdates?: boolean;
  updateInterval?: number;
  onStepComplete?: (step: ProgressStep) => void;
  onComplete?: (progress: PipelineProgress) => void;
  onError?: (error: any) => void;
}

export const AdvancedProgressTracker: React.FC<ProgressTrackerProps> = ({
  jobId,
  showDetailedSteps = true,
  showPerformanceMetrics = true,
  showResourceUsage = true,
  showCostTracking = true,
  enableRealTimeUpdates = true,
  updateInterval = 1000,
  onStepComplete,
  onComplete,
  onError
}) => {
  const [progress, setProgress] = useState<PipelineProgress | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [_performanceHistory, setPerformanceHistory] = useState<Array<{
    timestamp: Date;
    throughput: number;
    resourceUsage: number;
    cost: number;
  }>>([]);

  const { socket, isConnected, subscribe, unsubscribe, emit } = useWebSocket();

  // Initialize progress tracking
  useEffect(() => {
    if (jobId && isConnected && enableRealTimeUpdates) {
      requestProgressUpdate();
      
      const interval = setInterval(() => {
        requestProgressUpdate();
      }, updateInterval);

      return () => clearInterval(interval);
    }
    return undefined;
  }, [jobId, isConnected, enableRealTimeUpdates, updateInterval]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!socket) return;

    const handleProgressUpdate = (data: any) => {
      if (data.jobId === jobId) {
        updateProgress(data.progress);
      }
    };

    const handleStepUpdate = (data: any) => {
      if (data.jobId === jobId) {
        updateStep(data.step);
      }
    };

    const handleProgressComplete = (data: any) => {
      if (data.jobId === jobId) {
        handleComplete(data.progress);
      }
    };

    const handleProgressError = (data: any) => {
      if (data.jobId === jobId) {
        handleError(data.error);
      }
    };

    subscribe('progress_update', handleProgressUpdate);
    subscribe('step_update', handleStepUpdate);
    subscribe('progress_complete', handleProgressComplete);
    subscribe('progress_error', handleProgressError);

    return () => {
      unsubscribe('progress_update', handleProgressUpdate);
      unsubscribe('step_update', handleStepUpdate);
      unsubscribe('progress_complete', handleProgressComplete);
      unsubscribe('progress_error', handleProgressError);
    };
  }, [socket, jobId, subscribe, unsubscribe]);

  const requestProgressUpdate = useCallback(() => {
    if (socket && jobId) {
      emit('get_progress', { jobId });
    }
  }, [socket, jobId, emit]);

  const updateProgress = useCallback((newProgress: PipelineProgress) => {
    setProgress(prev => {
      const updated = { ...newProgress };
      
      // Track performance metrics
      if (prev) {
        const perfHistory = {
          timestamp: new Date(),
          throughput: updated.performance.throughput,
          resourceUsage: updated.currentStep?.resourceUsage ? 
            (updated.currentStep.resourceUsage.cpu + updated.currentStep.resourceUsage.memory) / 2 : 0,
          cost: updated.performance.totalCost
        };
        
        setPerformanceHistory(history => [
          ...history.slice(-29), // Keep last 30 data points
          perfHistory
        ]);
      }

      return updated;
    });

    // Record metrics
    performanceMonitor.recordMetric('pipeline_progress', newProgress.overallProgress, {
      jobId,
      status: newProgress.status
    });

    if (newProgress.currentStep) {
      performanceMonitor.recordMetric('step_progress', newProgress.currentStep.progress, {
        stepId: newProgress.currentStep.id,
        stepName: newProgress.currentStep.name
      });
    }
  }, [jobId]);

  const updateStep = useCallback((step: ProgressStep) => {
    setProgress(prev => {
      if (!prev) return null;

      const updatedSteps = prev.steps.map(s => 
        s.id === step.id ? { ...s, ...step } : s
      );

      const updatedProgress = {
        ...prev,
        steps: updatedSteps,
        currentStep: step.status === 'running' ? step : prev.currentStep,
        completedSteps: updatedSteps.filter(s => s.status === 'completed').length
      };

      // Calculate overall progress
      const totalProgress = updatedSteps.reduce((sum, s) => sum + s.progress, 0);
      updatedProgress.overallProgress = totalProgress / updatedSteps.length;

      return updatedProgress;
    });

    if (step.status === 'completed') {
      onStepComplete?.(step);
      performanceMonitor.recordInteraction('step_complete', 'AdvancedProgressTracker', 
        step.actualDuration || 0, true);
    }
  }, [onStepComplete]);

  const handleComplete = useCallback((completedProgress: PipelineProgress) => {
    setProgress(completedProgress);
    onComplete?.(completedProgress);
    
    performanceMonitor.recordInteraction('pipeline_complete', 'AdvancedProgressTracker',
      completedProgress.performance.averageStepTime, true);
  }, [onComplete]);

  const handleError = useCallback((error: any) => {
    onError?.(error);
    
    performanceMonitor.recordInteraction('pipeline_error', 'AdvancedProgressTracker',
      0, false, error.message);
  }, [onError]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'running': return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'pending': return <Clock className="w-4 h-4 text-gray-400" />;
      case 'paused': return <Pause className="w-4 h-4 text-yellow-500" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'running': return 'bg-blue-500';
      case 'failed': return 'bg-red-500';
      case 'pending': return 'bg-gray-300';
      case 'paused': return 'bg-yellow-500';
      default: return 'bg-gray-300';
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  };

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(cost);
  };

  const calculateETA = () => {
    if (!progress || !progress.currentStep) return null;
    
    const remainingSteps = progress.steps.filter(s => 
      s.status === 'pending' || (s.status === 'running' && s.progress < 100)
    );
    
    const avgStepTime = progress.performance.averageStepTime;
    const remainingTime = remainingSteps.length * avgStepTime;
    
    return new Date(Date.now() + remainingTime);
  };

  const getResourceUsageColor = (usage: number) => {
    if (usage > 0.8) return 'text-red-500';
    if (usage > 0.6) return 'text-yellow-500';
    return 'text-green-500';
  };

  if (!progress) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2">
            <Activity className="w-5 h-5 animate-spin" />
            <span>Loading progress...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            {getStatusIcon(progress.status)}
            <span>Pipeline Progress</span>
            <Badge variant={progress.status === 'running' ? 'default' : 'secondary'}>
              {progress.status}
            </Badge>
          </CardTitle>
          
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <span>{progress.completedSteps}/{progress.totalSteps} steps</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </Button>
          </div>
        </div>

        {/* Overall progress bar */}
        <div className="space-y-2">
          <Progress value={progress.overallProgress} className="h-3" />
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>{Math.round(progress.overallProgress)}% complete</span>
            {calculateETA() && (
              <span>ETA: {calculateETA()!.toLocaleTimeString()}</span>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Current step info */}
        {progress.currentStep && (
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-blue-900">
                Current: {progress.currentStep.name}
              </h4>
              <Badge variant="outline">
                {Math.round(progress.currentStep.progress)}%
              </Badge>
            </div>
            <p className="text-sm text-blue-700 mb-2">
              {progress.currentStep.description}
            </p>
            <Progress 
              value={progress.currentStep.progress} 
              className="h-2 bg-blue-200"
            />
            
            {progress.currentStep.estimatedDuration && (
              <div className="flex justify-between mt-2 text-xs text-blue-600">
                <span>
                  Runtime: {progress.currentStep.startTime && 
                    formatDuration(Date.now() - progress.currentStep.startTime.getTime())}
                </span>
                <span>
                  Est. Total: {formatDuration(progress.currentStep.estimatedDuration)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Performance metrics */}
        {showPerformanceMetrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <Timer className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium">Avg Step Time</span>
              </div>
              <p className="text-lg font-semibold">
                {formatDuration(progress.performance.averageStepTime)}
              </p>
            </div>

            {showCostTracking && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <DollarSign className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium">Total Cost</span>
                </div>
                <p className="text-lg font-semibold">
                  {formatCost(progress.performance.totalCost)}
                </p>
              </div>
            )}

            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <Target className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium">Success Rate</span>
              </div>
              <p className="text-lg font-semibold">
                {Math.round((1 - progress.performance.errorRate) * 100)}%
              </p>
            </div>

            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium">Throughput</span>
              </div>
              <p className="text-lg font-semibold">
                {progress.performance.throughput.toFixed(1)}/min
              </p>
            </div>
          </div>
        )}

        {/* Resource usage */}
        {showResourceUsage && progress.currentStep?.resourceUsage && (
          <div className="p-3 bg-gray-50 rounded-lg">
            <h4 className="font-semibold mb-3">Resource Usage</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <Cpu className={`w-5 h-5 mx-auto mb-1 ${getResourceUsageColor(progress.currentStep.resourceUsage.cpu)}`} />
                <p className="text-sm font-medium">CPU</p>
                <p className="text-lg">{Math.round(progress.currentStep.resourceUsage.cpu * 100)}%</p>
              </div>
              <div className="text-center">
                <HardDrive className={`w-5 h-5 mx-auto mb-1 ${getResourceUsageColor(progress.currentStep.resourceUsage.memory)}`} />
                <p className="text-sm font-medium">Memory</p>
                <p className="text-lg">{Math.round(progress.currentStep.resourceUsage.memory * 100)}%</p>
              </div>
              <div className="text-center">
                <HardDrive className={`w-5 h-5 mx-auto mb-1 ${getResourceUsageColor(progress.currentStep.resourceUsage.disk)}`} />
                <p className="text-sm font-medium">Disk</p>
                <p className="text-lg">{Math.round(progress.currentStep.resourceUsage.disk * 100)}%</p>
              </div>
              <div className="text-center">
                <Wifi className={`w-5 h-5 mx-auto mb-1 ${getResourceUsageColor(progress.currentStep.resourceUsage.network)}`} />
                <p className="text-sm font-medium">Network</p>
                <p className="text-lg">{Math.round(progress.currentStep.resourceUsage.network * 100)}%</p>
              </div>
            </div>
          </div>
        )}

        {/* Detailed steps */}
        {isExpanded && showDetailedSteps && (
          <div className="space-y-2">
            <h4 className="font-semibold">All Steps</h4>
            {progress.steps.map((step, index) => (
              <div 
                key={step.id}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedStep === step.id ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedStep(selectedStep === step.id ? null : step.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${getStatusColor(step.status)}`}>
                        {index + 1}
                      </div>
                      {getStatusIcon(step.status)}
                    </div>
                    <div>
                      <p className="font-medium">{step.name}</p>
                      <p className="text-sm text-muted-foreground">{step.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm">
                    <span>{Math.round(step.progress)}%</span>
                    {step.actualDuration && (
                      <span className="text-muted-foreground">
                        {formatDuration(step.actualDuration)}
                      </span>
                    )}
                    {step.cost && showCostTracking && (
                      <span className="text-muted-foreground">
                        {formatCost(step.cost)}
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-2">
                  <Progress value={step.progress} className="h-1" />
                </div>

                {/* Step details (when selected) */}
                {selectedStep === step.id && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {step.startTime && (
                        <div>
                          <span className="font-medium">Start Time:</span>
                          <p>{step.startTime.toLocaleString()}</p>
                        </div>
                      )}
                      {step.endTime && (
                        <div>
                          <span className="font-medium">End Time:</span>
                          <p>{step.endTime.toLocaleString()}</p>
                        </div>
                      )}
                      {step.estimatedDuration && (
                        <div>
                          <span className="font-medium">Est. Duration:</span>
                          <p>{formatDuration(step.estimatedDuration)}</p>
                        </div>
                      )}
                      {step.actualDuration && (
                        <div>
                          <span className="font-medium">Actual Duration:</span>
                          <p>{formatDuration(step.actualDuration)}</p>
                        </div>
                      )}
                    </div>

                    {step.dependencies && step.dependencies.length > 0 && (
                      <div>
                        <span className="font-medium text-sm">Dependencies:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {step.dependencies.map(dep => (
                            <Badge key={dep} variant="outline" className="text-xs">
                              {progress.steps.find(s => s.id === dep)?.name || dep}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {step.substeps && step.substeps.length > 0 && (
                      <div>
                        <span className="font-medium text-sm">Substeps:</span>
                        <div className="space-y-1 mt-2">
                          {step.substeps.map(substep => (
                            <div key={substep.id} className="flex items-center justify-between text-xs">
                              <span>{substep.name}</span>
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(substep.status)}
                                <span>{Math.round(substep.progress)}%</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Errors and warnings */}
        {(progress.errors.length > 0 || progress.warnings.length > 0) && (
          <div className="space-y-2">
            {progress.errors.length > 0 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <h4 className="font-semibold text-red-900 mb-2">
                  Errors ({progress.errors.length})
                </h4>
                <div className="space-y-1">
                  {progress.errors.slice(-3).map((error, index) => (
                    <div key={index} className="text-sm">
                      <div className="font-medium text-red-800">{error.step}</div>
                      <div className="text-red-700">{error.message}</div>
                      <div className="text-red-600 text-xs">
                        {error.timestamp.toLocaleString()} • Severity: {error.severity}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {progress.warnings.length > 0 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h4 className="font-semibold text-yellow-900 mb-2">
                  Warnings ({progress.warnings.length})
                </h4>
                <div className="space-y-1">
                  {progress.warnings.slice(-3).map((warning, index) => (
                    <div key={index} className="text-sm">
                      <div className="font-medium text-yellow-800">{warning.step}</div>
                      <div className="text-yellow-700">{warning.message}</div>
                      <div className="text-yellow-600 text-xs">
                        {warning.timestamp.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AdvancedProgressTracker;