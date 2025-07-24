# Professional Video Editor Components

This directory contains the professional video editing interface components that transform Evergreen's chat-based editor into a full-featured video editing suite.

## Components Overview

### 1. Timeline.tsx
Professional timeline with virtualization for handling 1000+ scenes efficiently.

**Features:**
- Multi-track editing (video, audio, overlay, effects)
- Frame-accurate positioning
- Zoom levels from 10% to 1000%
- Professional keyboard shortcuts
- Drag-and-drop clip manipulation
- Real-time playback with smooth scrubbing

**Usage:**
```tsx
import Timeline from './Timeline';

<Timeline
  projectId="project-123"
  storyboardData={storyboardData}
  onClipSelected={(clip) => console.log('Selected:', clip)}
  onTimelineChange={(tracks) => console.log('Timeline changed:', tracks)}
  onTimeUpdate={(time) => console.log('Current time:', time)}
/>
```

### 2. OperationQueue.tsx
Visual operation queue with drag-and-drop reordering.

**Features:**
- Real-time operation status
- Drag-and-drop reordering
- Batch execution
- Progress tracking
- Error recovery

**Usage:**
```tsx
import OperationQueue from './OperationQueue';

<OperationQueue
  projectId="project-123"
  onOperationSelect={(op) => console.log('Selected:', op)}
  onQueueReorder={(ops) => console.log('Reordered:', ops)}
  onExecute={(ids) => console.log('Execute:', ids)}
/>
```

### 3. PreviewScrubber.tsx
Frame-accurate video preview with professional controls.

**Features:**
- Frame-by-frame navigation
- Variable playback rates (0.25x to 4x)
- Range selection (in/out points)
- Frame capture to PNG
- Professional timecode display

**Usage:**
```tsx
import PreviewScrubber from './PreviewScrubber';

<PreviewScrubber
  videoUrl="/path/to/video.mp4"
  projectId="project-123"
  frameRate={30}
  onTimeUpdate={(time) => console.log('Time:', time)}
  onFrameCapture={(frame) => console.log('Captured frame')}
  onRangeSelect={(start, end) => console.log('Range:', start, end)}
/>
```

### 4. OperationTemplates.tsx
Library of one-click operation presets.

**Features:**
- Professional templates (YouTube, social media, effects)
- Custom template creation
- Category organization
- Usage tracking
- Import/export

**Usage:**
```tsx
import OperationTemplates from './OperationTemplates';

<OperationTemplates
  projectId="project-123"
  onApplyTemplate={(template) => console.log('Apply:', template)}
  onSaveTemplate={(template) => console.log('Save:', template)}
/>
```

### 5. CollaborativeEditor.tsx
Real-time collaboration system with WebSocket support.

**Features:**
- Live presence indicators
- Role-based permissions
- Chat and commenting
- Activity tracking
- Voice/video/screen sharing

**Usage:**
```tsx
import CollaborativeEditor from './CollaborativeEditor';

<CollaborativeEditor
  projectId="project-123"
  currentUserId="user-123"
  onInviteUser={(email, role) => console.log('Invite:', email, role)}
  onSendComment={(comment) => console.log('Comment:', comment)}
/>
```

### 6. useKeyboardShortcuts Hook
Comprehensive keyboard shortcut system.

**Features:**
- Industry-standard presets
- Customizable shortcuts
- Context awareness
- Conflict resolution

**Usage:**
```tsx
import { useKeyboardShortcuts, DEFAULT_SHORTCUTS } from '../../hooks/useKeyboardShortcuts';

const shortcuts = DEFAULT_SHORTCUTS.map(s => ({
  ...s,
  action: () => console.log('Shortcut:', s.key)
}));

const { formatShortcut } = useKeyboardShortcuts(shortcuts);
```

## Complete Integration Example

Here's how to integrate all components into a professional video editing interface:

```tsx
import React, { useState } from 'react';
import Timeline from './components/editor/Timeline';
import OperationQueue from './components/editor/OperationQueue';
import PreviewScrubber from './components/editor/PreviewScrubber';
import OperationTemplates from './components/editor/OperationTemplates';
import CollaborativeEditor from './components/editor/CollaborativeEditor';
import ChatInterface from './components/editor/ChatInterface';
import { useKeyboardShortcuts, DEFAULT_SHORTCUTS } from './hooks/useKeyboardShortcuts';

export default function VideoEditor({ projectId, storyboardData }) {
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedClip, setSelectedClip] = useState(null);
  const [videoUrl, setVideoUrl] = useState('/path/to/current-video.mp4');

  // Setup keyboard shortcuts
  const shortcuts = DEFAULT_SHORTCUTS.map(shortcut => ({
    ...shortcut,
    action: () => {
      switch (shortcut.key) {
        case ' ':
          // Toggle play/pause
          console.log('Play/Pause');
          break;
        case 'c':
          // Cut at current time
          console.log('Cut at', currentTime);
          break;
        // ... handle other shortcuts
      }
    }
  }));

  useKeyboardShortcuts(shortcuts);

  return (
    <div className="flex h-screen bg-zinc-950">
      {/* Left Panel - Templates & Chat */}
      <div className="w-80 flex flex-col border-r border-zinc-700">
        <div className="flex-1 overflow-hidden">
          <OperationTemplates
            projectId={projectId}
            onApplyTemplate={(template) => {
              // Apply template operations
              console.log('Applying template:', template);
            }}
          />
        </div>
        <div className="h-96 border-t border-zinc-700">
          <ChatInterface
            projectId={projectId}
            storyboardData={storyboardData}
            onCommandExecuted={(result) => {
              // Handle chat command result
              console.log('Command executed:', result);
            }}
          />
        </div>
      </div>

      {/* Center Panel - Preview & Timeline */}
      <div className="flex-1 flex flex-col">
        {/* Preview Area */}
        <div className="h-1/2 p-4">
          <PreviewScrubber
            videoUrl={videoUrl}
            projectId={projectId}
            currentTime={currentTime}
            frameRate={30}
            onTimeUpdate={setCurrentTime}
            onFrameCapture={(frame) => {
              // Handle frame capture
              console.log('Frame captured');
            }}
            onRangeSelect={(start, end) => {
              // Handle range selection
              console.log('Range selected:', start, end);
            }}
          />
        </div>

        {/* Timeline */}
        <div className="flex-1 border-t border-zinc-700">
          <Timeline
            projectId={projectId}
            storyboardData={storyboardData}
            onClipSelected={setSelectedClip}
            onTimelineChange={(tracks) => {
              // Handle timeline changes
              console.log('Timeline updated:', tracks);
            }}
            onTimeUpdate={setCurrentTime}
            onOperation={(operation) => {
              // Handle timeline operations
              console.log('Timeline operation:', operation);
            }}
          />
        </div>
      </div>

      {/* Right Panel - Operation Queue & Collaboration */}
      <div className="w-96 flex flex-col border-l border-zinc-700">
        <div className="flex-1 overflow-hidden">
          <OperationQueue
            projectId={projectId}
            onOperationSelect={(op) => {
              // Handle operation selection
              console.log('Operation selected:', op);
            }}
            onExecute={(operationIds) => {
              // Execute operations
              console.log('Execute operations:', operationIds);
            }}
          />
        </div>
        <div className="h-96 border-t border-zinc-700">
          <CollaborativeEditor
            projectId={projectId}
            currentUserId="current-user-id"
            onInviteUser={(email, role) => {
              // Handle user invitation
              console.log('Invite user:', email, role);
            }}
            onSendComment={(comment) => {
              // Handle comment
              console.log('New comment:', comment);
            }}
          />
        </div>
      </div>
    </div>
  );
}
```

## Keyboard Shortcuts Reference

| Shortcut | Action | Category |
|----------|--------|----------|
| Space | Play/Pause | Playback |
| J/K/L | Reverse/Pause/Forward | Playback |
| ←/→ | Previous/Next Frame | Navigation |
| Shift+←/→ | Skip 5 Frames | Navigation |
| Ctrl+←/→ | Skip 1 Second | Navigation |
| Home/End | Go to Start/End | Navigation |
| C | Cut/Razor | Editing |
| V | Selection Tool | Editing |
| Delete | Delete Selection | Editing |
| Ctrl+Z/Y | Undo/Redo | Editing |
| +/- | Zoom In/Out | View |
| I/O | Mark In/Out | Selection |
| M | Add Marker | Editing |

## Performance Guidelines

1. **Timeline Performance**
   - The timeline uses virtualization to handle 1000+ clips
   - Only visible clips are rendered for optimal performance
   - Use batch operations when modifying multiple clips

2. **Preview Optimization**
   - Frame caching reduces redundant frame captures
   - Use appropriate playback rates for system capabilities
   - Lower resolution previews for better performance

3. **Collaboration**
   - WebSocket connections auto-reconnect on disconnect
   - Presence updates are throttled to prevent spam
   - Large operations are queued to prevent blocking

## Styling

All components use Tailwind CSS with a dark theme optimized for video editing:
- Background: `bg-zinc-900` / `bg-zinc-950`
- Borders: `border-zinc-700`
- Text: `text-white` / `text-zinc-400`
- Accents: `bg-blue-600` / `bg-green-600`

## Future Enhancements

1. **GPU Acceleration**: WebGL-based preview rendering
2. **Advanced Effects**: Color grading, motion tracking
3. **Plugin System**: Third-party operation support
4. **Mobile Support**: Touch-optimized timeline
5. **Cloud Rendering**: Offload heavy operations
6. **AI Enhancement**: Smart cut detection, auto-editing