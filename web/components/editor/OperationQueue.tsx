import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { 
  ListVideo,
  Play,
  Pause,
  X,
  GripVertical,
  CheckCircle,
  AlertCircle,
  Clock,
  Loader2,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  RotateCcw,
  Zap,
  Copy,
  Trash2,
  Settings,
  Filter,
  SortAsc
} from 'lucide-react';

interface Operation {
  id: string;
  type: 'CUT' | 'FADE' | 'SPEED' | 'TRANSITION' | 'OVERLAY' | 'AUDIO_MIX' | 'EFFECT' | 'BATCH';
  name: string;
  description?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'paused';
  progress?: number;
  clips?: string[];
  parameters?: Record<string, any>;
  estimatedTime?: number;
  actualTime?: number;
  error?: string;
  preview?: string;
  priority?: 'low' | 'normal' | 'high';
  dependencies?: string[];
  result?: any;
}

interface OperationGroup {
  id: string;
  name: string;
  operations: Operation[];
  collapsed?: boolean;
}

interface OperationQueueProps {
  projectId: string;
  onOperationSelect?: (operation: Operation) => void;
  onOperationCancel?: (operationId: string) => void;
  onOperationRetry?: (operationId: string) => void;
  onQueueReorder?: (operations: Operation[]) => void;
  onExecute?: (operationIds: string[]) => void;
  className?: string;
}

// Operation type configurations
const OPERATION_CONFIG = {
  CUT: { icon: '✂️', color: 'bg-red-600', estimatedTime: 2 },
  FADE: { icon: '🌅', color: 'bg-blue-600', estimatedTime: 3 },
  SPEED: { icon: '⚡', color: 'bg-green-600', estimatedTime: 5 },
  TRANSITION: { icon: '🔄', color: 'bg-purple-600', estimatedTime: 4 },
  OVERLAY: { icon: '📝', color: 'bg-yellow-600', estimatedTime: 3 },
  AUDIO_MIX: { icon: '🎵', color: 'bg-orange-600', estimatedTime: 6 },
  EFFECT: { icon: '✨', color: 'bg-pink-600', estimatedTime: 8 },
  BATCH: { icon: '📦', color: 'bg-indigo-600', estimatedTime: 10 }
};

export default function OperationQueue({ 
  projectId,
  onOperationSelect,
  onOperationCancel,
  onOperationRetry,
  onQueueReorder,
  onExecute,
  className = '' 
}: OperationQueueProps) {
  const [operations, setOperations] = useState<Operation[]>([]);
  const [groups, setGroups] = useState<OperationGroup[]>([]);
  const [selectedOperations, setSelectedOperations] = useState<Set<string>>(new Set());
  const [draggedOperation, setDraggedOperation] = useState<Operation | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'processing' | 'completed' | 'failed'>('all');
  const [sortBy, setSortBy] = useState<'order' | 'priority' | 'type'>('order');
  const [showPreview, setShowPreview] = useState(true);
  const [autoExecute, setAutoExecute] = useState(true);
  
  const queueRef = useRef<HTMLDivElement>(null);
  const dragCounter = useRef(0);

  // Initialize with sample operations
  useEffect(() => {
    const sampleOps: Operation[] = [
      {
        id: 'op1',
        type: 'CUT',
        name: 'Cut first 3 seconds',
        description: 'Remove first 3 seconds from Scene 2',
        status: 'completed',
        progress: 100,
        clips: ['scene-2'],
        parameters: { start: 0, duration: 3 },
        estimatedTime: 2,
        actualTime: 1.8,
        priority: 'normal'
      },
      {
        id: 'op2',
        type: 'FADE',
        name: 'Add fade transitions',
        description: 'Fade between all scenes',
        status: 'processing',
        progress: 65,
        clips: ['scene-1', 'scene-2', 'scene-3'],
        parameters: { duration: 1, type: 'crossfade' },
        estimatedTime: 3,
        priority: 'high'
      },
      {
        id: 'op3',
        type: 'SPEED',
        name: 'Speed up Scene 4',
        description: 'Increase playback speed by 1.5x',
        status: 'pending',
        clips: ['scene-4'],
        parameters: { speed: 1.5 },
        estimatedTime: 5,
        priority: 'normal',
        dependencies: ['op2']
      },
      {
        id: 'op4',
        type: 'OVERLAY',
        name: 'Add end title',
        description: 'Add "THE END" text overlay',
        status: 'pending',
        clips: ['scene-8'],
        parameters: { text: 'THE END', duration: 3, position: 'center' },
        estimatedTime: 3,
        priority: 'low'
      },
      {
        id: 'op5',
        type: 'AUDIO_MIX',
        name: 'Adjust audio levels',
        description: 'Reduce background music to 50%',
        status: 'failed',
        error: 'Audio track not found',
        clips: ['audio-track-1'],
        parameters: { volume: 0.5 },
        estimatedTime: 6,
        priority: 'normal'
      }
    ];
    
    setOperations(sampleOps);

    // Create a batch group
    const batchGroup: OperationGroup = {
      id: 'batch1',
      name: 'Scene Optimization Batch',
      operations: [
        {
          id: 'batch-op1',
          type: 'BATCH',
          name: 'Optimize all scenes',
          status: 'pending',
          priority: 'high'
        }
      ]
    };
    
    setGroups([batchGroup]);
  }, []);

  // Auto-execute pending operations
  useEffect(() => {
    if (!autoExecute) return;

    const pendingOps = operations.filter(op => op.status === 'pending' && !op.dependencies?.length);
    if (pendingOps.length > 0 && !operations.some(op => op.status === 'processing')) {
      // Start the next operation
      const nextOp = pendingOps[0];
      handleExecuteOperation(nextOp.id);
    }
  }, [operations, autoExecute]);

  // Simulate operation progress
  useEffect(() => {
    const interval = setInterval(() => {
      setOperations(prev => prev.map(op => {
        if (op.status === 'processing' && op.progress !== undefined) {
          const newProgress = Math.min(100, op.progress + Math.random() * 10);
          if (newProgress >= 100) {
            // Complete the operation
            return {
              ...op,
              status: 'completed',
              progress: 100,
              actualTime: op.estimatedTime ? op.estimatedTime * (0.8 + Math.random() * 0.4) : undefined
            };
          }
          return { ...op, progress: newProgress };
        }
        return op;
      }));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const handleExecuteOperation = (operationId: string) => {
    setOperations(prev => prev.map(op => 
      op.id === operationId ? { ...op, status: 'processing', progress: 0 } : op
    ));
    
    if (onExecute) {
      onExecute([operationId]);
    }
  };

  const handleDragStart = (e: React.DragEvent, operation: Operation) => {
    setDraggedOperation(operation);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', ''); // Firefox fix
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverIndex(index);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounter.current++;
  };

  const handleDragLeave = (e: React.DragEvent) => {
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setDragOverIndex(null);
    }
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    setDragOverIndex(null);
    dragCounter.current = 0;

    if (!draggedOperation) return;

    const dragIndex = operations.findIndex(op => op.id === draggedOperation.id);
    if (dragIndex === dropIndex) return;

    const newOperations = [...operations];
    newOperations.splice(dragIndex, 1);
    newOperations.splice(dropIndex, 0, draggedOperation);

    setOperations(newOperations);
    setDraggedOperation(null);

    if (onQueueReorder) {
      onQueueReorder(newOperations);
    }
  };

  const handleOperationClick = (operation: Operation, e: React.MouseEvent) => {
    if (e.ctrlKey || e.metaKey) {
      // Multi-select
      const newSelection = new Set(selectedOperations);
      if (newSelection.has(operation.id)) {
        newSelection.delete(operation.id);
      } else {
        newSelection.add(operation.id);
      }
      setSelectedOperations(newSelection);
    } else {
      // Single select
      setSelectedOperations(new Set([operation.id]));
    }

    if (onOperationSelect) {
      onOperationSelect(operation);
    }
  };

  const handleCancelOperation = (operationId: string) => {
    setOperations(prev => prev.map(op => 
      op.id === operationId ? { ...op, status: 'paused', progress: op.progress || 0 } : op
    ));

    if (onOperationCancel) {
      onOperationCancel(operationId);
    }
  };

  const handleRetryOperation = (operationId: string) => {
    setOperations(prev => prev.map(op => 
      op.id === operationId ? { ...op, status: 'pending', progress: 0, error: undefined } : op
    ));

    if (onOperationRetry) {
      onOperationRetry(operationId);
    }
  };

  const handleBatchExecute = () => {
    const operationIds = Array.from(selectedOperations);
    operationIds.forEach(id => handleExecuteOperation(id));
    setSelectedOperations(new Set());
  };

  const handleClearCompleted = () => {
    setOperations(prev => prev.filter(op => op.status !== 'completed'));
  };

  const handleDuplicateOperations = () => {
    const duplicated: Operation[] = [];
    operations.forEach(op => {
      if (selectedOperations.has(op.id)) {
        duplicated.push({
          ...op,
          id: `${op.id}-copy-${Date.now()}`,
          status: 'pending',
          progress: 0,
          error: undefined,
          actualTime: undefined
        });
      }
    });
    setOperations(prev => [...prev, ...duplicated]);
    setSelectedOperations(new Set());
  };

  const getFilteredOperations = () => {
    let filtered = operations;
    
    if (filter !== 'all') {
      filtered = filtered.filter(op => op.status === filter);
    }

    switch (sortBy) {
      case 'priority':
        const priorityOrder = { high: 0, normal: 1, low: 2 };
        filtered.sort((a, b) => (priorityOrder[a.priority || 'normal'] - priorityOrder[b.priority || 'normal']));
        break;
      case 'type':
        filtered.sort((a, b) => a.type.localeCompare(b.type));
        break;
      // 'order' is the default, no sorting needed
    }

    return filtered;
  };

  const getStatusIcon = (status: Operation['status']) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-zinc-400" />;
      case 'processing': return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'paused': return <Pause className="w-4 h-4 text-yellow-500" />;
      default: return null;
    }
  };

  const getOperationStats = () => {
    const stats = {
      total: operations.length,
      pending: operations.filter(op => op.status === 'pending').length,
      processing: operations.filter(op => op.status === 'processing').length,
      completed: operations.filter(op => op.status === 'completed').length,
      failed: operations.filter(op => op.status === 'failed').length
    };
    
    const estimatedTime = operations
      .filter(op => op.status === 'pending' || op.status === 'processing')
      .reduce((total, op) => total + (op.estimatedTime || 0), 0);

    return { ...stats, estimatedTime };
  };

  const stats = getOperationStats();
  const filteredOperations = getFilteredOperations();

  return (
    <Card className={`h-full flex flex-col bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="flex-shrink-0 border-b border-zinc-700">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <ListVideo className="w-5 h-5" />
            Operation Queue
            <Badge variant="outline" className="text-xs">
              {stats.total} operations
            </Badge>
          </div>
          
          <div className="flex items-center gap-2">
            {stats.estimatedTime > 0 && (
              <div className="flex items-center gap-1 text-sm text-zinc-400">
                <Clock className="w-4 h-4" />
                ~{Math.ceil(stats.estimatedTime / 60)}m remaining
              </div>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setAutoExecute(!autoExecute)}
              className={autoExecute ? 'text-green-400' : 'text-zinc-400'}
            >
              {autoExecute ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowPreview(!showPreview)}
              className={showPreview ? 'text-blue-400' : 'text-zinc-400'}
            >
              {showPreview ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Toolbar */}
        <div className="flex items-center justify-between p-3 border-b border-zinc-700 bg-zinc-950">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 bg-zinc-800 rounded-lg p-1">
              <Button
                variant={filter === 'all' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('all')}
                className="h-7 px-2 text-xs"
              >
                All ({stats.total})
              </Button>
              <Button
                variant={filter === 'pending' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('pending')}
                className="h-7 px-2 text-xs"
              >
                Pending ({stats.pending})
              </Button>
              <Button
                variant={filter === 'processing' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('processing')}
                className="h-7 px-2 text-xs"
              >
                Processing ({stats.processing})
              </Button>
              <Button
                variant={filter === 'completed' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('completed')}
                className="h-7 px-2 text-xs"
              >
                Completed ({stats.completed})
              </Button>
              {stats.failed > 0 && (
                <Button
                  variant={filter === 'failed' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setFilter('failed')}
                  className="h-7 px-2 text-xs text-red-400"
                >
                  Failed ({stats.failed})
                </Button>
              )}
            </div>
            
            <div className="flex items-center gap-1">
              <Filter className="w-4 h-4 text-zinc-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-zinc-800 text-zinc-200 text-xs px-2 py-1 rounded border border-zinc-700"
              >
                <option value="order">Order</option>
                <option value="priority">Priority</option>
                <option value="type">Type</option>
              </select>
            </div>
          </div>

          {selectedOperations.size > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-zinc-400">
                {selectedOperations.size} selected
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={handleBatchExecute}
                className="bg-zinc-800 border-zinc-600"
              >
                <Play className="w-3 h-3 mr-1" />
                Execute
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleDuplicateOperations}
                className="bg-zinc-800 border-zinc-600"
              >
                <Copy className="w-3 h-3 mr-1" />
                Duplicate
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSelectedOperations(new Set())}
                className="bg-zinc-800 border-zinc-600"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          )}
        </div>

        {/* Operation List */}
        <div 
          ref={queueRef}
          className="flex-1 overflow-y-auto p-3 space-y-2"
          onDragEnter={handleDragEnter}
        >
          {/* Batch Groups */}
          {groups.map(group => (
            <div key={group.id} className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setGroups(prev => prev.map(g => 
                      g.id === group.id ? { ...g, collapsed: !g.collapsed } : g
                    ));
                  }}
                  className="p-0 h-5 w-5"
                >
                  {group.collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </Button>
                <span className="text-sm font-medium text-zinc-300">{group.name}</span>
                <Badge variant="outline" className="text-xs">
                  {group.operations.length} operations
                </Badge>
              </div>
              
              {!group.collapsed && (
                <div className="ml-6 space-y-2">
                  {group.operations.map((op, index) => (
                    <OperationItem
                      key={op.id}
                      operation={op}
                      index={index}
                      isSelected={selectedOperations.has(op.id)}
                      isDragOver={dragOverIndex === index}
                      showPreview={showPreview}
                      onDragStart={handleDragStart}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      onClick={handleOperationClick}
                      onCancel={handleCancelOperation}
                      onRetry={handleRetryOperation}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Individual Operations */}
          {filteredOperations.map((operation, index) => (
            <OperationItem
              key={operation.id}
              operation={operation}
              index={index}
              isSelected={selectedOperations.has(operation.id)}
              isDragOver={dragOverIndex === operations.indexOf(operation)}
              showPreview={showPreview}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={handleOperationClick}
              onCancel={handleCancelOperation}
              onRetry={handleRetryOperation}
            />
          ))}

          {filteredOperations.length === 0 && (
            <div className="flex flex-col items-center justify-center h-32 text-zinc-500">
              <ListVideo className="w-8 h-8 mb-2" />
              <p className="text-sm">No operations in queue</p>
            </div>
          )}
        </div>

        {/* Bottom Stats Bar */}
        <div className="border-t border-zinc-700 p-3 bg-zinc-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-xs text-zinc-400">
              <div className="flex items-center gap-1">
                <CheckCircle className="w-3 h-3 text-green-500" />
                {stats.completed} completed
              </div>
              {stats.processing > 0 && (
                <div className="flex items-center gap-1">
                  <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
                  {stats.processing} processing
                </div>
              )}
              {stats.pending > 0 && (
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {stats.pending} pending
                </div>
              )}
              {stats.failed > 0 && (
                <div className="flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 text-red-500" />
                  {stats.failed} failed
                </div>
              )}
            </div>

            {stats.completed > 0 && (
              <Button
                size="sm"
                variant="ghost"
                onClick={handleClearCompleted}
                className="text-xs"
              >
                <Trash2 className="w-3 h-3 mr-1" />
                Clear completed
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Separate component for operation items
function OperationItem({
  operation,
  index,
  isSelected,
  isDragOver,
  showPreview,
  onDragStart,
  onDragOver,
  onDrop,
  onClick,
  onCancel,
  onRetry
}: {
  operation: Operation;
  index: number;
  isSelected: boolean;
  isDragOver: boolean;
  showPreview: boolean;
  onDragStart: (e: React.DragEvent, operation: Operation) => void;
  onDragOver: (e: React.DragEvent, index: number) => void;
  onDrop: (e: React.DragEvent, index: number) => void;
  onClick: (operation: Operation, e: React.MouseEvent) => void;
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
}) {
  const config = OPERATION_CONFIG[operation.type];
  const canDrag = operation.status === 'pending' || operation.status === 'paused';

  return (
    <div
      className={`relative bg-zinc-800 rounded-lg border transition-all ${
        isSelected ? 'border-blue-500 ring-1 ring-blue-500' : 'border-zinc-700'
      } ${
        isDragOver ? 'border-t-2 border-t-blue-400' : ''
      } ${
        operation.status === 'failed' ? 'border-red-500/50' : ''
      }`}
      draggable={canDrag}
      onDragStart={(e) => onDragStart(e, operation)}
      onDragOver={(e) => onDragOver(e, index)}
      onDragLeave={(e) => e.preventDefault()}
      onDrop={(e) => onDrop(e, index)}
      onClick={(e) => onClick(operation, e)}
    >
      <div className="p-3">
        <div className="flex items-start gap-3">
          {/* Drag Handle */}
          {canDrag && (
            <div className="cursor-move text-zinc-500 hover:text-zinc-300">
              <GripVertical className="w-4 h-4" />
            </div>
          )}

          {/* Operation Icon */}
          <div className={`w-10 h-10 rounded-lg ${config.color} flex items-center justify-center text-lg`}>
            {config.icon}
          </div>

          {/* Operation Details */}
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <h4 className="font-medium text-white">{operation.name}</h4>
                {operation.priority && operation.priority !== 'normal' && (
                  <Badge 
                    variant={operation.priority === 'high' ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {operation.priority}
                  </Badge>
                )}
                {operation.dependencies && operation.dependencies.length > 0 && (
                  <Badge variant="outline" className="text-xs">
                    {operation.dependencies.length} deps
                  </Badge>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                {operation.status === 'processing' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onCancel(operation.id);
                    }}
                    className="h-6 px-2"
                  >
                    <Pause className="w-3 h-3" />
                  </Button>
                )}
                
                {operation.status === 'failed' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRetry(operation.id);
                    }}
                    className="h-6 px-2 text-red-400 hover:text-red-300"
                  >
                    <RotateCcw className="w-3 h-3" />
                  </Button>
                )}
                
                {getStatusIcon(operation.status)}
              </div>
            </div>

            {operation.description && (
              <p className="text-sm text-zinc-400 mb-2">{operation.description}</p>
            )}

            {/* Clips */}
            {operation.clips && operation.clips.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {operation.clips.map(clip => (
                  <Badge key={clip} variant="secondary" className="text-xs">
                    {clip}
                  </Badge>
                ))}
              </div>
            )}

            {/* Progress Bar */}
            {operation.status === 'processing' && operation.progress !== undefined && (
              <div className="mb-2">
                <Progress value={operation.progress} className="h-1" />
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-zinc-500">{Math.round(operation.progress)}%</span>
                  {operation.estimatedTime && (
                    <span className="text-xs text-zinc-500">
                      ~{Math.ceil((operation.estimatedTime * (100 - operation.progress) / 100) * 60)}s remaining
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Error Message */}
            {operation.error && (
              <div className="flex items-center gap-2 p-2 bg-red-900/20 rounded text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {operation.error}
              </div>
            )}

            {/* Preview */}
            {showPreview && operation.preview && operation.status === 'completed' && (
              <div className="mt-2">
                <img 
                  src={operation.preview} 
                  alt="Operation preview" 
                  className="rounded h-16 object-cover"
                />
              </div>
            )}

            {/* Parameters */}
            {operation.parameters && (
              <details className="mt-2">
                <summary className="text-xs text-zinc-500 cursor-pointer hover:text-zinc-400">
                  <Settings className="w-3 h-3 inline mr-1" />
                  Parameters
                </summary>
                <pre className="mt-1 p-2 bg-zinc-900 rounded text-xs text-zinc-400 overflow-x-auto">
                  {JSON.stringify(operation.parameters, null, 2)}
                </pre>
              </details>
            )}

            {/* Timing */}
            {operation.actualTime && (
              <div className="flex items-center gap-2 mt-2 text-xs text-zinc-500">
                <Zap className="w-3 h-3" />
                Completed in {operation.actualTime.toFixed(1)}s
                {operation.estimatedTime && (
                  <span className={
                    operation.actualTime < operation.estimatedTime 
                      ? 'text-green-500' 
                      : 'text-red-500'
                  }>
                    ({operation.actualTime < operation.estimatedTime ? '-' : '+'}{Math.abs(operation.actualTime - operation.estimatedTime).toFixed(1)}s)
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}