import React, { useState, useRef, useEffect } from 'react';
import { Film, Image, Volume2, Scissors, Move, Play } from 'lucide-react';

interface TimelineItem {
  id: string;
  sceneId: string;
  type: 'scene';
  startTime: number;
  duration: number;
  transition: 'cut' | 'fade' | 'dissolve' | 'wipe';
  transitionDuration: number;
  scene: any;
  audio?: any;
  image?: any;
  video?: any;
}

interface TimelineEditorProps {
  items: TimelineItem[];
  currentTime: number;
  totalDuration: number;
  selectedItem: TimelineItem | null;
  onItemsChange: (items: TimelineItem[]) => void;
  onItemSelect: (item: TimelineItem | null) => void;
  onTransitionChange: (itemId: string, transition: TimelineItem['transition'], duration: number) => void;
  onTimeChange: (time: number) => void;
}

export default function TimelineEditor({
  items,
  currentTime,
  totalDuration,
  selectedItem,
  onItemsChange,
  onItemSelect,
  onTransitionChange,
  onTimeChange
}: TimelineEditorProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [draggedItem, setDraggedItem] = useState<TimelineItem | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [pixelsPerSecond, setPixelsPerSecond] = useState(10);
  
  const timelineRef = useRef<HTMLDivElement>(null);
  const playheadRef = useRef<HTMLDivElement>(null);

  const handleDragStart = (e: React.DragEvent, item: TimelineItem, index: number) => {
    setIsDragging(true);
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', ''); // Required for Firefox
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverIndex(index);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    setDraggedItem(null);
    setDragOverIndex(null);
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    
    if (!draggedItem) return;

    const draggedIndex = items.findIndex(item => item.id === draggedItem.id);
    if (draggedIndex === dropIndex) return;

    const newItems = [...items];
    const [removed] = newItems.splice(draggedIndex, 1);
    newItems.splice(dropIndex, 0, removed);

    // Recalculate start times
    let currentStart = 0;
    const updatedItems = newItems.map(item => {
      const updatedItem = { ...item, startTime: currentStart };
      currentStart += item.duration;
      return updatedItem;
    });

    onItemsChange(updatedItems);
    setDragOverIndex(null);
  };

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!timelineRef.current) return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const time = (x / rect.width) * totalDuration;
    onTimeChange(Math.max(0, Math.min(time, totalDuration)));
  };

  const handleTransitionSelect = (itemId: string, transition: TimelineItem['transition']) => {
    const duration = transition === 'cut' ? 0 : 0.5;
    onTransitionChange(itemId, transition, duration);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  const getItemColor = (item: TimelineItem) => {
    if (item.video) return 'bg-purple-500';
    if (item.image) return 'bg-blue-500';
    return 'bg-gray-400';
  };

  const getItemIcon = (item: TimelineItem) => {
    if (item.video) return <Film className="h-4 w-4" />;
    if (item.image) return <Image className="h-4 w-4" />;
    return <Play className="h-4 w-4" />;
  };

  // Calculate timeline width
  const timelineWidth = totalDuration * pixelsPerSecond;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold">Timeline</h3>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Zoom:</span>
              <input
                type="range"
                min="5"
                max="50"
                value={pixelsPerSecond}
                onChange={(e) => setPixelsPerSecond(parseInt(e.target.value))}
                className="w-24"
              />
            </div>
            <span className="text-sm text-gray-600">
              {formatTime(currentTime)} / {formatTime(totalDuration)}
            </span>
          </div>
        </div>
      </div>

      {/* Timeline Ruler */}
      <div className="mb-2 relative" style={{ width: `${timelineWidth}px`, minWidth: '100%' }}>
        <div className="h-6 bg-gray-100 border-b border-gray-300 relative">
          {Array.from({ length: Math.ceil(totalDuration / 5) }).map((_, i) => (
            <div
              key={i}
              className="absolute top-0 h-full border-l border-gray-400"
              style={{ left: `${i * 5 * pixelsPerSecond}px` }}
            >
              <span className="absolute top-1 left-1 text-xs text-gray-600">
                {formatTime(i * 5)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Timeline Container */}
      <div className="relative overflow-x-auto overflow-y-hidden border border-gray-200 rounded-lg">
        <div
          ref={timelineRef}
          className="relative h-32 bg-gray-50"
          style={{ width: `${timelineWidth}px`, minWidth: '100%' }}
          onClick={handleTimelineClick}
        >
          {/* Timeline Tracks */}
          <div className="absolute inset-0">
            {/* Video/Image Track */}
            <div className="h-16 border-b border-gray-200 relative">
              {items.map((item, index) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, item, index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragEnd={handleDragEnd}
                  onDrop={(e) => handleDrop(e, index)}
                  onClick={() => onItemSelect(item)}
                  className={`absolute top-2 h-12 rounded cursor-move transition-all ${
                    getItemColor(item)
                  } ${
                    selectedItem?.id === item.id ? 'ring-2 ring-yellow-400' : ''
                  } ${
                    dragOverIndex === index ? 'opacity-50' : ''
                  }`}
                  style={{
                    left: `${item.startTime * pixelsPerSecond}px`,
                    width: `${item.duration * pixelsPerSecond}px`
                  }}
                >
                  <div className="flex items-center h-full px-2 text-white text-xs">
                    <div className="flex items-center space-x-1">
                      {getItemIcon(item)}
                      <span className="truncate">{item.scene.id}</span>
                    </div>
                  </div>
                  {/* Transition indicator */}
                  {index > 0 && item.transition !== 'cut' && (
                    <div className="absolute -left-1 top-0 h-full w-2 bg-yellow-400 opacity-75" />
                  )}
                </div>
              ))}
            </div>

            {/* Audio Track */}
            <div className="h-16 relative">
              {items.map((item) => (
                item.audio && (
                  <div
                    key={`audio-${item.id}`}
                    className="absolute top-2 h-12 bg-green-500 rounded opacity-75"
                    style={{
                      left: `${item.startTime * pixelsPerSecond}px`,
                      width: `${item.duration * pixelsPerSecond}px`
                    }}
                  >
                    <div className="flex items-center h-full px-2 text-white text-xs">
                      <Volume2 className="h-4 w-4 mr-1" />
                      <span className="truncate">Audio</span>
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>

          {/* Playhead */}
          <div
            ref={playheadRef}
            className="absolute top-0 w-0.5 h-full bg-red-500 pointer-events-none z-10"
            style={{ left: `${currentTime * pixelsPerSecond}px` }}
          >
            <div className="absolute -top-1 -left-2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-red-500" />
          </div>
        </div>
      </div>

      {/* Selected Item Controls */}
      {selectedItem && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium">Scene {selectedItem.sceneId}</h4>
              <p className="text-sm text-gray-600">
                Duration: {formatTime(selectedItem.duration)} | Start: {formatTime(selectedItem.startTime)}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Scissors className="h-4 w-4 text-gray-500" />
                <select
                  value={selectedItem.transition}
                  onChange={(e) => handleTransitionSelect(selectedItem.id, e.target.value as TimelineItem['transition'])}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="cut">Cut</option>
                  <option value="fade">Fade</option>
                  <option value="dissolve">Dissolve</option>
                  <option value="wipe">Wipe</option>
                </select>
              </div>
            </div>
          </div>
          {selectedItem.scene.narration && (
            <p className="mt-2 text-sm text-gray-700 italic">
              "{selectedItem.scene.narration.substring(0, 100)}..."
            </p>
          )}
        </div>
      )}

      {/* Instructions */}
      <div className="mt-4 text-sm text-gray-600">
        <p className="flex items-center">
          <Move className="h-4 w-4 mr-1" />
          Drag and drop scenes to reorder • Click to select • Click timeline to move playhead
        </p>
      </div>
    </div>
  );
}