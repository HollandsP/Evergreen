# AI Video Editor - Implementation Documentation

## Overview

The AI Video Editor is a sophisticated video editing system that combines natural language processing with programmatic video editing. It allows users to edit videos using chat-based commands like "Cut the first 3 seconds of scene 2" or "Add fade transition between all scenes".

## Architecture

### Core Components

1. **AI Video Editor Service** (`src/services/ai_video_editor.py`)
   - Main orchestrator using GPT-4 for natural language understanding
   - Integrates with MoviePy and FFmpeg for video processing
   - Manages chat history and project context
   - Provides storyboard-aware editing decisions

2. **MoviePy Wrapper Service** (`src/services/moviepy_wrapper.py`)
   - Clean interface to MoviePy functionality
   - Handles video trimming, speed changes, transitions, overlays
   - Optimized for AI editor's programmatic needs

3. **Chat Interface Component** (`web/components/editor/ChatInterface.tsx`)
   - React-based chat UI for natural language commands
   - Real-time command processing with confidence scoring
   - Preview and download capabilities for edited videos

4. **Editing Timeline Component** (`web/components/editor/EditingTimeline.tsx`)
   - Visual timeline with drag-and-drop functionality
   - Multi-track editing (video, audio, overlays)
   - Interactive playhead and clip selection

5. **API Integration** (`web/pages/api/editor/process-command.ts`, `api/routes/editor.py`)
   - RESTful endpoints for command processing
   - Mock responses for development when Python service unavailable
   - File serving for previews and downloads

## Features

### Natural Language Commands Supported

#### Cutting and Trimming
- "Cut the first 3 seconds of scene 2"
- "Trim 5 seconds from the beginning"
- "Remove the last 2 seconds of scene 1"

#### Speed Adjustments
- "Speed up scene 4 by 1.5x"
- "Slow down scene 2 to 0.5x speed"
- "Make scene 3 play twice as fast"

#### Fade Effects
- "Add fade in to scene 1"
- "Add fade out at the end"
- "Add fade transition between all scenes"

#### Text Overlays
- "Add text overlay 'THE END' to the last scene"
- "Put title 'Chapter 1' at the beginning"
- "Add subtitle 'Two years later...' to scene 3"

#### Audio Mixing
- "Reduce audio volume to 50% for scene 3"
- "Mute the audio in scene 2"
- "Increase volume by 20% for the narration"

#### Transitions
- "Add crossfade between scene 1 and 2"
- "Put a 2-second fade transition between all scenes"
- "Add slide transition from scene 3 to 4"

### Advanced Features

#### Storyboard-Aware Editing
- AI considers project storyboard data for context-aware decisions
- Understands scene relationships and narrative flow
- Makes intelligent suggestions based on video content

#### Real-time Previews
- Generate preview clips for all editing operations
- Thumbnail generation for quick visual feedback
- Progressive preview updates during editing

#### Chat-based Interface
- Conversational editing experience
- Command confidence scoring (AI tells you how confident it is)
- Suggestion system for common operations
- Chat history preservation across sessions

## Installation and Setup

### Prerequisites

1. **Python Dependencies** (already in requirements.txt):
   ```
   moviepy==1.0.3
   openai==1.3.5
   ffmpeg-python==0.2.0
   ```

2. **System Dependencies**:
   ```bash
   # FFmpeg (required by MoviePy)
   sudo apt update
   sudo apt install ffmpeg
   
   # On macOS with Homebrew
   brew install ffmpeg
   
   # On Windows, download from https://ffmpeg.org/
   ```

3. **Environment Variables**:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   PYTHON_API_URL=http://localhost:8000  # Python backend URL
   ```

### Installation Steps

1. **Install Python dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Node.js dependencies** (if not already installed):
   ```bash
   cd web
   npm install
   ```

3. **Start the services**:
   ```bash
   # Start Python API (in one terminal)
   uvicorn api.main:app --reload --port 8000
   
   # Start Next.js frontend (in another terminal)
   cd web
   npm run dev
   ```

## Usage

### Accessing the AI Video Editor

1. Navigate to the production pipeline: `http://localhost:3000/production`
2. Complete the earlier stages (Script → Audio → Images → Video)
3. Reach the "Final Assembly" stage where the AI editor is integrated

### Using Natural Language Commands

1. **Chat Interface**: Use the right panel to type natural language commands
2. **Confidence Scoring**: AI shows how confident it is about understanding your command
3. **Preview Results**: Click "Preview" to see the result before applying
4. **Download Edits**: Download individual edited clips or the full video

### Timeline Editing

1. **Visual Timeline**: See all video clips, audio tracks, and overlays
2. **Drag and Drop**: Move clips around (future enhancement)
3. **Clip Selection**: Click clips to see details and editing options
4. **Playback Controls**: Play, pause, scrub through the timeline

## Technical Implementation

### AI Command Processing Pipeline

1. **User Input**: Natural language command received via chat interface
2. **GPT-4 Processing**: Command parsed into structured operation with parameters
3. **Confidence Check**: If confidence < 70%, ask for clarification
4. **Operation Execution**: Execute using MoviePy wrapper or FFmpeg
5. **Preview Generation**: Create preview clip and thumbnail
6. **Response**: Return success/failure with preview links

### Command Parsing Example

Input: `"Cut the first 3 seconds of scene 2"`

GPT-4 Output:
```json
{
  "operation": "CUT",
  "parameters": {
    "target": "scene_2",
    "start_time": 0,
    "duration": 3
  },
  "confidence": 0.95,
  "explanation": "Will remove the first 3 seconds from scene 2"
}
```

### File Management

- **Working Directory**: `./output/editor_workspace/`
- **Preview Files**: `./output/editor_workspace/previews/`
- **Operation Results**: Named with operation IDs for tracking
- **Automatic Cleanup**: Old files cleaned periodically

## API Endpoints

### Python API (FastAPI)

- `POST /api/v1/editor/process-command` - Process natural language command
- `GET /api/v1/editor/chat-history/{project_id}` - Get chat history
- `DELETE /api/v1/editor/chat-history` - Clear chat history
- `GET /api/v1/editor/suggestions` - Get command suggestions
- `GET /api/v1/editor/health` - Health check

### Next.js API

- `POST /api/editor/process-command` - Proxy to Python API with fallback
- `GET /api/editor/preview/[operationId]` - Serve preview files
- `GET /api/editor/download/[operationId]` - Download edited videos

## Development and Testing

### Mock Responses

When the Python service is unavailable, the system provides intelligent mock responses:

- Parses common command patterns (cut, fade, speed, text, audio)
- Generates realistic operation IDs and file paths
- Provides downloadable mock video files for testing

### Testing Commands

Try these commands to test the system:

```
"Cut the first 3 seconds of scene 1"
"Add fade transition between all scenes"
"Speed up scene 2 by 1.5x"
"Add text overlay 'THE END' to the last scene"
"Reduce audio volume to 50% for scene 3"
"Add fade out at the end of the video"
```

### Error Handling

- **Command Parsing Errors**: GPT-4 responds with clarification requests
- **File Not Found**: Graceful fallback with helpful error messages
- **API Failures**: Automatic fallback to mock responses
- **Invalid Operations**: Clear error messages with suggestions

## Future Enhancements

### Planned Features

1. **MCP FFmpeg Server Integration**: Enhanced FFmpeg command processing
2. **Advanced Audio Sync**: Beat detection and automatic synchronization
3. **Color Grading**: AI-powered color correction and grading
4. **Motion Graphics**: Automated text animations and effects
5. **Batch Operations**: Process multiple clips simultaneously
6. **Template System**: Save and reuse editing templates

### Integration Opportunities

1. **Voice Commands**: Speech-to-text for hands-free editing
2. **Auto-editing**: AI analyzes content and suggests edits
3. **Style Transfer**: Apply editing styles from reference videos
4. **Collaborative Editing**: Multi-user editing sessions
5. **Version Control**: Track and revert editing changes

## Troubleshooting

### Common Issues

1. **"MoviePy not available"**
   - Solution: `pip install moviepy==1.0.3`

2. **"FFmpeg not found"**
   - Solution: Install FFmpeg system-wide
   - Verify with: `ffmpeg -version`

3. **"OpenAI API Error"**
   - Check: `OPENAI_API_KEY` environment variable
   - Verify: API key has sufficient credits

4. **"Preview not loading"**
   - Check: File permissions in output directory
   - Verify: Python API is running on correct port

5. **"Command not understood"**
   - Try: More specific language ("scene 2" instead of "the second one")
   - Use: Suggested commands from the interface

### Performance Optimization

1. **Large Files**: 
   - Use proxy files for editing
   - Generate final output only when complete

2. **Memory Usage**:
   - MoviePy clips are properly closed after operations
   - Temporary files cleaned automatically

3. **Response Time**:
   - Preview generation runs in background
   - GPT-4 responses cached when possible

## Security Considerations

- **Input Validation**: All user commands validated before processing
- **File Access**: Restricted to designated output directories
- **API Keys**: Stored securely in environment variables
- **Command Injection**: Protected by structured operation parsing

## Architecture Benefits

### User Experience
- **Natural Language**: No need to learn complex editing interfaces
- **Visual Feedback**: Real-time preview of all operations
- **Contextual Awareness**: AI understands project structure
- **Iterative Editing**: Easy to undo and modify operations

### Technical Advantages
- **Modular Design**: Each component can be enhanced independently
- **Fallback Systems**: Graceful degradation when services unavailable
- **Extensible**: Easy to add new operation types
- **Scalable**: Can handle multiple projects and users

This AI Video Editor represents a significant advancement in making video editing accessible through natural language while maintaining professional-grade editing capabilities.