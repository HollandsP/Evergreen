import React, { useState } from 'react';
import {
  Cog6ToothIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  TrashIcon,
  ArrowPathIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { GenerationJob, SystemStatus, PipelineSettings } from '@/types';
import { formatCost, formatDuration, cn } from '@/lib/utils';

interface PipelineControlsProps {
  currentJob?: GenerationJob;
  systemStatus: SystemStatus;
  settings: PipelineSettings;
  onSettingsChange: (settings: Partial<PipelineSettings>) => void;
  onCancelJob?: () => void;
  onRetryJob?: () => void;
  onClearHistory?: () => void;
  className?: string;
}

const PipelineControls: React.FC<PipelineControlsProps> = ({
  currentJob,
  systemStatus,
  settings,
  onSettingsChange,
  onCancelJob,
  onRetryJob,
  onClearHistory,
  className,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showSystemInfo, setShowSystemInfo] = useState(false);

  const isJobActive = currentJob && ['pending', 'generating_image', 'generating_video'].includes(currentJob.status);
  const canRetry = currentJob && currentJob.status === 'failed';

  const getSystemStatusColor = () => {
    if (!systemStatus.dalle3Available) {
      return 'text-red-600 bg-red-100';
    }
    if (systemStatus.systemLoad > 0.8) {
      return 'text-yellow-600 bg-yellow-100';
    }
    return 'text-green-600 bg-green-100';
  };

  const getSystemStatusText = () => {
    if (!systemStatus.dalle3Available) {
      return 'DALL-E 3 not available';
    }
    if (systemStatus.systemLoad > 0.8) {
      return 'High system load';
    }
    return 'All systems operational';
  };

  return (
    <div className={cn('card', className)}>
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Pipeline Controls</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSystemInfo(!showSystemInfo)}
              className="btn-outline p-2"
              title="System information"
            >
              <InformationCircleIcon className="h-4 w-4" />
            </button>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="btn-outline p-2"
              title="Advanced settings"
            >
              <Cog6ToothIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="card-body space-y-6">
        {/* System Status */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className={cn('flex items-center space-x-2 px-2 py-1 rounded-full text-xs font-medium', getSystemStatusColor())}>
              <div className="w-2 h-2 rounded-full bg-current" />
              <span>{getSystemStatusText()}</span>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            {systemStatus.activeJobs} active • {systemStatus.queueLength} queued
          </div>
        </div>

        {/* Current Job Controls */}
        {currentJob && (
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-900">Current Job</h4>
              <span className={cn('status-badge', `status-${currentJob.status}`)}>
                {currentJob.status.replace('_', ' ')}
              </span>
            </div>
            
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">{currentJob.prompt}</p>
            
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-500">
                Progress: {currentJob.progress}%
              </div>
              <div className="flex items-center space-x-2">
                {isJobActive && onCancelJob && (
                  <button
                    onClick={onCancelJob}
                    className="btn-outline text-xs py-1 px-2"
                    title="Cancel job"
                  >
                    <StopIcon className="h-3 w-3 mr-1" />
                    Cancel
                  </button>
                )}
                {canRetry && onRetryJob && (
                  <button
                    onClick={onRetryJob}
                    className="btn-primary text-xs py-1 px-2"
                    title="Retry job"
                  >
                    <ArrowPathIcon className="h-3 w-3 mr-1" />
                    Retry
                  </button>
                )}
              </div>
            </div>

            {currentJob.error && (
              <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                <ExclamationTriangleIcon className="h-4 w-4 inline mr-1" />
                {currentJob.error}
              </div>
            )}
          </div>
        )}

        {/* Quick Settings */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Settings</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-600">Auto-download results</label>
              <button
                onClick={() => onSettingsChange({ autoDownload: !settings.autoDownload })}
                className={cn(
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                  settings.autoDownload ? 'bg-primary-600' : 'bg-gray-200'
                )}
              >
                <span
                  className={cn(
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    settings.autoDownload ? 'translate-x-5' : 'translate-x-0'
                  )}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-600">Browser notifications</label>
              <button
                onClick={() => onSettingsChange({ notifications: !settings.notifications })}
                className={cn(
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                  settings.notifications ? 'bg-primary-600' : 'bg-gray-200'
                )}
              >
                <span
                  className={cn(
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    settings.notifications ? 'translate-x-5' : 'translate-x-0'
                  )}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Advanced Settings */}
        {showAdvanced && (
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Advanced Settings</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Default Image Size
                </label>
                <select
                  value={settings.imageSize}
                  onChange={(e) => onSettingsChange({ imageSize: e.target.value })}
                  className="input text-sm"
                >
                  <option value="1024x1024">1024×1024</option>
                  <option value="1024x1792">1024×1792</option>
                  <option value="1792x1024">1792×1024</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Default Video Duration
                </label>
                <select
                  value={settings.videoDuration}
                  onChange={(e) => onSettingsChange({ videoDuration: parseInt(e.target.value) })}
                  className="input text-sm"
                >
                  <option value={4}>4 seconds</option>
                  <option value={8}>8 seconds</option>
                  <option value={10}>10 seconds</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Default Quality
                </label>
                <select
                  value={settings.quality}
                  onChange={(e) => onSettingsChange({ quality: e.target.value })}
                  className="input text-sm"
                >
                  <option value="standard">Standard</option>
                  <option value="high">High</option>
                  <option value="ultra">Ultra</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Random Seed
                </label>
                <input
                  type="number"
                  value={settings.seed || ''}
                  onChange={(e) => onSettingsChange({ 
                    seed: e.target.value ? parseInt(e.target.value) : undefined 
                  })}
                  placeholder="Auto"
                  className="input text-sm"
                />
              </div>
            </div>
          </div>
        )}

        {/* System Information */}
        {showSystemInfo && (
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">System Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">DALL-E 3:</span>
                  <span className={cn('font-medium', systemStatus.dalle3Available ? 'text-green-600' : 'text-red-600')}>
                    {systemStatus.dalle3Available ? 'Available' : 'Offline'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 text-sm italic">Note:</span>
                  <span className="text-gray-500 text-sm">
                    Flux.1 removed (high subscription cost)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">RunwayML:</span>
                  <span className={cn('font-medium', systemStatus.runwayAvailable ? 'text-green-600' : 'text-red-600')}>
                    {systemStatus.runwayAvailable ? 'Available' : 'Offline'}
                  </span>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Active Jobs:</span>
                  <span className="font-medium">{systemStatus.activeJobs}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Queue Length:</span>
                  <span className="font-medium">{systemStatus.queueLength}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">System Load:</span>
                  <span className={cn(
                    'font-medium',
                    systemStatus.systemLoad > 0.8 ? 'text-red-600' : 
                    systemStatus.systemLoad > 0.6 ? 'text-yellow-600' : 'text-green-600'
                  )}>
                    {Math.round(systemStatus.systemLoad * 100)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>System Load</span>
                <span>{Math.round(systemStatus.systemLoad * 100)}%</span>
              </div>
              <div className="progress-bar">
                <div
                  className={cn(
                    'progress-fill transition-all duration-300',
                    systemStatus.systemLoad > 0.8 ? 'bg-red-500' :
                    systemStatus.systemLoad > 0.6 ? 'bg-yellow-500' : 'bg-green-500'
                  )}
                  style={{ width: `${systemStatus.systemLoad * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="border-t pt-4">
          <div className="flex items-center justify-between">
            <button
              onClick={onClearHistory}
              className="btn-outline text-sm"
              title="Clear generation history"
            >
              <TrashIcon className="h-4 w-4 mr-2" />
              Clear History
            </button>

            <button
              onClick={() => window.location.reload()}
              className="btn-outline text-sm"
              title="Refresh application"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelineControls;