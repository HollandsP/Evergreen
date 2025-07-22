import React from 'react';
import { 
  PhotoIcon, 
  VideoCameraIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { PipelineStep } from '@/types';
import { cn, formatDuration } from '@/lib/utils';

interface WorkflowVisualizerProps {
  steps: PipelineStep[];
  currentStep?: string;
  className?: string;
}

const STEP_ICONS = {
  'image_generation': PhotoIcon,
  'video_generation': VideoCameraIcon,
  'processing': ClockIcon,
  'finalizing': CheckCircleIcon,
};

const STEP_LABELS = {
  'image_generation': 'Generating Image',
  'video_generation': 'Creating Video',
  'processing': 'Processing',
  'finalizing': 'Finalizing',
};

const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  steps,
  currentStep,
  className,
}) => {
  const getStepIcon = (step: PipelineStep) => {
    const IconComponent = STEP_ICONS[step.id as keyof typeof STEP_ICONS] || ClockIcon;
    
    let iconClass = 'h-6 w-6';
    switch (step.status) {
      case 'completed':
        iconClass += ' text-green-600';
        break;
      case 'running':
        iconClass += ' text-blue-600';
        break;
      case 'failed':
        iconClass += ' text-red-600';
        break;
      default:
        iconClass += ' text-gray-400';
    }

    return <IconComponent className={iconClass} />;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircleIcon className="h-4 w-4 text-red-600" />;
      case 'running':
        return (
          <div className="h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
        );
      default:
        return <ClockIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStepDuration = (step: PipelineStep) => {
    if (step.startTime && step.endTime) {
      const duration = (step.endTime.getTime() - step.startTime.getTime()) / 1000;
      return formatDuration(duration);
    }
    if (step.startTime && step.status === 'running') {
      const duration = (Date.now() - step.startTime.getTime()) / 1000;
      return formatDuration(duration);
    }
    return null;
  };

  if (steps.length === 0) {
    return (
      <div className={cn('card', className)}>
        <div className="card-body text-center py-8">
          <ClockIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Waiting for generation to start...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('card', className)}>
      <div className="card-header">
        <h3 className="text-lg font-semibold text-gray-900">Pipeline Progress</h3>
      </div>

      <div className="card-body">
        <div className="space-y-4">
          {steps.map((step, index) => {
            const isActive = step.id === currentStep;
            const isCompleted = step.status === 'completed';
            const isFailed = step.status === 'failed';
            const isRunning = step.status === 'running';
            const duration = getStepDuration(step);

            return (
              <div key={step.id} className="relative">
                {/* Connection Line */}
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      'absolute left-6 top-12 w-0.5 h-8 transition-colors duration-300',
                      isCompleted ? 'bg-green-300' : 'bg-gray-200'
                    )}
                  />
                )}

                <div
                  className={cn(
                    'flex items-start space-x-4 p-4 rounded-lg transition-all duration-300',
                    isActive && 'bg-blue-50 border border-blue-200',
                    isFailed && 'bg-red-50 border border-red-200',
                    isCompleted && 'bg-green-50 border border-green-200',
                    !isActive && !isFailed && !isCompleted && 'hover:bg-gray-50'
                  )}
                >
                  {/* Step Icon */}
                  <div
                    className={cn(
                      'flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300',
                      isCompleted && 'bg-green-100 border-green-300',
                      isRunning && 'bg-blue-100 border-blue-300 shadow-lg',
                      isFailed && 'bg-red-100 border-red-300',
                      step.status === 'pending' && 'bg-gray-100 border-gray-300'
                    )}
                  >
                    {getStepIcon(step)}
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-900">
                        {STEP_LABELS[step.id as keyof typeof STEP_LABELS] || step.name}
                      </h4>
                      <div className="flex items-center space-x-2">
                        {duration && (
                          <span className="text-xs text-gray-500">{duration}</span>
                        )}
                        {getStatusIcon(step.status)}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    {(isRunning || isCompleted) && (
                      <div className="mb-2">
                        <div className="progress-bar">
                          <div
                            className={cn(
                              'progress-fill transition-all duration-500 ease-out',
                              isCompleted && 'bg-green-500',
                              isRunning && 'bg-blue-500'
                            )}
                            style={{ width: `${step.progress}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>{step.progress}% complete</span>
                          {step.status === 'running' && (
                            <span className="flex items-center">
                              <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full mr-1" />
                              In progress
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Error Message */}
                    {step.error && (
                      <div className="flex items-start space-x-2 mt-2 p-2 bg-red-50 border border-red-200 rounded">
                        <ExclamationTriangleIcon className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-red-700">{step.error}</p>
                      </div>
                    )}

                    {/* Step Details */}
                    {step.status !== 'pending' && (
                      <div className="text-xs text-gray-500 space-y-1">
                        {step.startTime && (
                          <div>Started: {step.startTime.toLocaleTimeString()}</div>
                        )}
                        {step.endTime && (
                          <div>Completed: {step.endTime.toLocaleTimeString()}</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Overall Progress Summary */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Overall Progress</span>
            <span className="font-medium text-gray-900">
              {steps.filter(s => s.status === 'completed').length} / {steps.length} steps
            </span>
          </div>
          <div className="progress-bar mt-2">
            <div
              className="progress-fill bg-primary-500"
              style={{
                width: `${(steps.filter(s => s.status === 'completed').length / steps.length) * 100}%`
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowVisualizer;