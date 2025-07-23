import React, { useRef, useState, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { 
  PencilIcon, 
  XMarkIcon,
  ArrowUturnLeftIcon,
  ArrowUturnRightIcon,
  TrashIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';

interface SketchToolProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (imageData: string) => void;
  initialImage?: string;
  sceneTitle?: string;
}

interface DrawingState {
  isDrawing: boolean;
  currentPath: string[];
  paths: string[][];
  strokeColor: string;
  strokeWidth: number;
}

export const SketchTool: React.FC<SketchToolProps> = ({
  isOpen,
  onClose,
  onSave,
  initialImage,
  sceneTitle = 'Scene',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [drawingState, setDrawingState] = useState<DrawingState>({
    isDrawing: false,
    currentPath: [],
    paths: [],
    strokeColor: '#10b981', // emerald-500
    strokeWidth: 3,
  });
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  const colors = [
    '#10b981', // emerald-500
    '#3b82f6', // blue-500
    '#ef4444', // red-500
    '#f59e0b', // amber-500
    '#8b5cf6', // violet-500
    '#ec4899', // pink-500
    '#ffffff', // white
    '#000000', // black
  ];

  const strokeWidths = [1, 3, 5, 8, 12];

  useEffect(() => {
    if (isOpen && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        // Set canvas size
        canvas.width = 800;
        canvas.height = 450;

        // Set background
        ctx.fillStyle = '#18181b'; // zinc-900
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Load initial image if provided
        if (initialImage) {
          const img = new Image();
          img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            saveToHistory();
          };
          img.src = initialImage;
        } else {
          saveToHistory();
        }
      }
    }
  }, [isOpen, initialImage]);

  const saveToHistory = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (ctx && canvas) {
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      setHistory(prev => [...prev.slice(0, historyIndex + 1), imageData]);
      setHistoryIndex(prev => prev + 1);
    }
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      if (ctx && canvas) {
        const prevState = history[historyIndex - 1];
        ctx.putImageData(prevState, 0, 0);
        setHistoryIndex(prev => prev - 1);
      }
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      if (ctx && canvas) {
        const nextState = history[historyIndex + 1];
        ctx.putImageData(nextState, 0, 0);
        setHistoryIndex(prev => prev + 1);
      }
    }
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (ctx && canvas) {
      ctx.fillStyle = '#18181b';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      saveToHistory();
    }
  };

  const handleSave = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      const imageData = canvas.toDataURL('image/png');
      onSave(imageData);
      onClose();
    }
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setDrawingState(prev => ({
      ...prev,
      isDrawing: true,
      currentPath: [`M ${x} ${y}`],
    }));
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawingState.isDrawing) return;

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.strokeStyle = drawingState.strokeColor;
    ctx.lineWidth = drawingState.strokeWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    if (drawingState.currentPath.length > 0) {
      const lastPoint = drawingState.currentPath[drawingState.currentPath.length - 1];
      const [, lastX, lastY] = lastPoint.split(' ');
      ctx.moveTo(parseFloat(lastX), parseFloat(lastY));
    }
    ctx.lineTo(x, y);
    ctx.stroke();

    setDrawingState(prev => ({
      ...prev,
      currentPath: [...prev.currentPath, `L ${x} ${y}`],
    }));
  };

  const stopDrawing = () => {
    if (drawingState.isDrawing) {
      setDrawingState(prev => ({
        ...prev,
        isDrawing: false,
        paths: [...prev.paths, prev.currentPath],
        currentPath: [],
      }));
      saveToHistory();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-zinc-900 rounded-lg shadow-2xl border border-zinc-800 max-w-5xl w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center space-x-3">
            <PencilIcon className="h-5 w-5 text-emerald-400" />
            <h2 className="text-lg font-semibold text-zinc-100">Sketch Tool - {sceneTitle}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          {/* Color Picker */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-zinc-400 mr-2">Color:</span>
            {colors.map((color) => (
              <button
                key={color}
                onClick={() => setDrawingState(prev => ({ ...prev, strokeColor: color }))}
                className={cn(
                  'w-8 h-8 rounded-full border-2 transition-all',
                  drawingState.strokeColor === color 
                    ? 'border-emerald-400 scale-110' 
                    : 'border-zinc-700 hover:border-zinc-600'
                )}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>

          {/* Stroke Width */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-zinc-400 mr-2">Size:</span>
            {strokeWidths.map((width) => (
              <button
                key={width}
                onClick={() => setDrawingState(prev => ({ ...prev, strokeWidth: width }))}
                className={cn(
                  'w-8 h-8 rounded-md border-2 flex items-center justify-center transition-all',
                  drawingState.strokeWidth === width
                    ? 'border-emerald-400 bg-zinc-800'
                    : 'border-zinc-700 hover:border-zinc-600'
                )}
              >
                <div 
                  className="bg-zinc-400 rounded-full"
                  style={{ width: `${width * 2}px`, height: `${width * 2}px` }}
                />
              </button>
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleUndo}
              disabled={historyIndex <= 0}
              className={cn(
                'p-2 rounded-md transition-colors',
                historyIndex > 0
                  ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                  : 'text-zinc-600 cursor-not-allowed'
              )}
              title="Undo"
            >
              <ArrowUturnLeftIcon className="h-5 w-5" />
            </button>
            <button
              onClick={handleRedo}
              disabled={historyIndex >= history.length - 1}
              className={cn(
                'p-2 rounded-md transition-colors',
                historyIndex < history.length - 1
                  ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                  : 'text-zinc-600 cursor-not-allowed'
              )}
              title="Redo"
            >
              <ArrowUturnRightIcon className="h-5 w-5" />
            </button>
            <button
              onClick={handleClear}
              className="p-2 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Clear"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Canvas */}
        <div className="p-4 flex justify-center">
          <canvas
            ref={canvasRef}
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            className="border-2 border-zinc-700 rounded-lg cursor-crosshair"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-4 border-t border-zinc-800 space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white transition-colors flex items-center space-x-2"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            <span>Save Sketch</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SketchTool;