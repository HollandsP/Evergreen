# Evergreen AI Content Generation Pipeline

Transform written stories into cinematic YouTube videos using AI-powered automation with a modern web interface and production pipeline.

## 🎬 Overview

The AI Content Generation Pipeline automates the creation of professional-quality YouTube videos for AI-apocalypse narratives. Starting with "LOG_0002: THE DESCENT" from the "AI 2027: Race" universe, this system enables rapid, modular production of dystopian video content.

### Key Features
- 🎬 **Web Production Interface**: Complete 5-stage audio-first production pipeline
- 📝 **Script Processing**: Upload and parse "The Descent" with auto-prompt generation
- 🎙️ **AI Voice Synthesis**: ElevenLabs integration with Winston character voices
- 🖼️ **Image Generation**: DALL-E 3 integration for scene visualization
- 🎥 **Video Generation**: RunwayML Gen-4 Turbo with lip-sync and audio synchronization
- 💻 **Terminal UI Effects**: Cinematic terminal animations with multiple themes
- 🎬 **Smart Assembly**: Timeline editing, transitions, and professional video export

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+ (for web interface)
- FFmpeg 4.0+
- Docker & Docker Compose
- 16GB RAM (minimum)
- API Keys: ElevenLabs, OpenAI (DALL-E 3), RunwayML

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/HollandsP/ai-content-pipeline.git
cd Evergreen
```

2. **Set up environment variables**
```bash
# API keys are already configured in project environment
# Includes: ELEVENLABS_API_KEY, OPENAI_API_KEY, RUNWAY_API_KEY
```

3. **Quick Start with Web Interface**
```bash
# Start the web interface
cd web
npm install
npm run dev

# Open browser to: http://localhost:3000/production
```

4. **Alternative: Docker Setup**
```bash
# Start all services with Docker
docker-compose up -d

# Access web interface at: http://localhost:3000
# API documentation at: http://localhost:8000/docs
```

## 📁 Project Structure

```
Evergreen/
├── web/                   # Next.js production interface
│   ├── components/        # React components for 5-stage workflow
│   ├── pages/production/  # Stage-specific pages
│   └── lib/              # WebSocket, API, and state management
├── api/                   # FastAPI backend
│   └── routes/           # Script, audio, image, video, assembly endpoints
├── src/                   # Core Python services
│   ├── script_engine/    # Script parsing and processing
│   ├── services/         # ElevenLabs, DALL-E 3, RunwayML clients
│   ├── terminal_sim/     # Terminal UI animation system
│   └── prompts/          # 600+ optimized generation prompts
├── workers/              # Celery background processing
├── scripts/              # Generation and utility scripts
│   ├── generation/       # Video generation scripts
│   ├── startup/          # Service startup scripts
│   └── utilities/        # Maintenance and testing tools
├── tests/                # Organized test suites
│   ├── unit/             # Unit tests
│   ├── integration/      # Service integration tests
│   ├── e2e/             # End-to-end pipeline tests
│   └── experimental/     # Feature testing
├── docs/                 # Comprehensive documentation
│   ├── setup/           # Installation and setup guides
│   ├── development/     # Development workflows
│   ├── design/          # Architecture and design docs
│   └── runway/          # RunwayML integration guides
├── output/              # Generated media and final videos
└── assets/              # Templates, styles, and static assets
```

## 🎯 Production Workflows

### Web Interface Production Pipeline

**Audio-First 5-Stage Workflow:**

1. **Script Processing** (`/production/script`)
   - Upload "The Descent" script file
   - Automatic parsing into 8 scenes with timestamps
   - Auto-generated prompts for each scene
   - Narration extraction for Winston character

2. **Audio Generation** (`/production/audio`)
   - ElevenLabs voice synthesis
   - Winston character voice selection
   - Batch audio generation for all scenes
   - Audio timing for lip-sync preparation

3. **Image Generation** (`/production/images`)
   - DALL-E 3 integration (cost: ~$0.32 for 8 images)
   - Pre-filled, editable prompts from script analysis
   - High-resolution scene visualization
   - Custom image upload option

4. **Video Generation** (`/production/videos`)
   - RunwayML Gen-4 Turbo video creation
   - Audio-synchronized video generation
   - Lip-sync enabled for dialogue scenes
   - Camera movement and motion controls

5. **Final Assembly** (`/production/assembly`)
   - Timeline editor with all media assets
   - Transition effects and scene ordering
   - Background music integration
   - Professional video export

### Direct Script Usage
```bash
# Generate complete video using scripts
python scripts/generation/generate_log_0002_video.py

# Test individual components
python tests/integration/test_complete_pipeline.py

# Quick API test
python scripts/experimental/quick_api_test.py
```

### API Integration
```python
import requests

# Upload and parse script
response = requests.post('http://localhost:8000/api/v1/script/parse', 
    files={'file': open('scripts/ScriptLog0002TheDescent.txt', 'rb')})
scenes = response.json()['scenes']

# Generate audio for all scenes
response = requests.post('http://localhost:8000/api/v1/audio/batch',
    json={'scenes': scenes, 'voice': 'winston_calm'})

# Track progress via WebSocket
# ws://localhost:8000/ws for real-time updates
```

## 🛠️ Configuration

### Voice Configuration
ElevenLabs voices are pre-configured for "The Descent" characters:
```python
# Available voices in web interface
VOICES = {
    'winston_calm': 'Calm, authoritative narrator',
    'winston_urgent': 'Urgent, concerned tone',
    'system_voice': 'Synthetic, robotic announcements'
}
```

### Production Settings
Customize production pipeline in web interface:
```typescript
// Audio settings
const audioSettings = {
  voice: 'winston_calm',
  stability: 0.7,
  similarityBoost: 0.8,
  style: 'narrative'
};

// Video settings  
const videoSettings = {
  provider: 'runway',
  model: 'gen4-turbo',
  duration: 'auto', // Based on audio length
  lipSync: true,    // Auto-enabled for dialogue
  cameraMovement: 'subtle',
  motionIntensity: 0.7
};
```

### Prompt Templates
Extensive prompt library in `src/prompts/dalle3_runway_prompts.py`:
```python
# 600+ optimized prompts for different scene types
SCENE_TEMPLATES = {
    'rooftop_dystopian': {
        'dalle_prompt': 'Dystopian Berlin rooftop at sunset, white-clad figures...',
        'runway_prompt': 'Slow camera movement across rooftop scene...',
        'style_modifiers': ['cinematic', 'high contrast', 'moody lighting']
    }
}
```

## 🔧 Advanced Features

### Terminal UI Animations
```python
from src.terminal_sim.advanced_effects import TerminalRenderer

# Create cinematic terminal animations
renderer = TerminalRenderer(theme='matrix')
renderer.add_typing_effect(
    text="SYSTEM FAILURE IMMINENT",
    speed=50,  # ms per character
    cursor_blink=True
)
video = renderer.export_video(duration=5, fps=30)
```

### Custom Video Assembly
```python
from workers.tasks.video_generation import VideoComposer

# Advanced video composition
composer = VideoComposer()
timeline = composer.build_timeline([
    {'type': 'audio', 'file': 'scene_1.mp3', 'start': 0},
    {'type': 'visual', 'file': 'scene_1.mp4', 'start': 0},
    {'type': 'terminal', 'file': 'ui_1.mp4', 'start': 0, 'overlay': True}
])
final_video = composer.assemble(timeline, transitions=['crossfade'])
```

### Production State Management
```typescript
// Web interface state persistence
import { productionState } from '@/lib/production-state';

// Save progress across sessions
productionState.updateStage('audio', {
  status: 'completed',
  generatedAudio: audioFiles,
  totalDuration: 85.2
});

// Resume from any stage
const currentStage = productionState.getCurrentStage();
```

## 📊 Performance & Analytics

### Production Pipeline Metrics
- **Complete video generation**: ~5-10 minutes ("The Descent" - 8 scenes)
- **API costs per video**: ~$4.62 total
  - Audio (ElevenLabs): ~$0.30
  - Images (DALL-E 3): ~$0.32 (8 images @ $0.04 each)
  - Videos (RunwayML): ~$4.00 (8 clips @ ~$0.50 each)
- **Success rate**: 98%+ with automatic retry logic
- **WebSocket real-time updates**: <100ms latency

### Web Interface Analytics
```bash
# View production statistics
open http://localhost:3000/production
# Real-time progress tracking
# Cost estimation per stage
# Performance metrics dashboard
```

### API Performance
```bash
# Health check and metrics
curl http://localhost:8000/api/v1/health
# Detailed API docs
open http://localhost:8000/docs
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: WebSocket shows "Connecting" but never connects
```javascript
// Solution: Check WebSocket connection in browser DevTools
// Fixed in latest version with proper wsManager.connect() call
```

**Issue**: API key authentication failures
```bash
# Solution: API keys are pre-configured in environment
# Check .env.local in web/ directory
# All keys: ELEVENLABS_API_KEY, OPENAI_API_KEY, RUNWAY_API_KEY
```

**Issue**: DALL-E 3 content policy violations
```bash
# Solution: Modify prompts to be less specific about people/violence
# The system auto-generates safe prompts for cinematic content
```

**Issue**: RunwayML generation timeouts
```bash
# Solution: Videos are processed asynchronously
# Check progress via WebSocket or refresh the page
# Typical generation time: 30-60 seconds per video
```

**Issue**: Memory errors during video assembly
```bash
# Solution: Restart Docker services
docker-compose down && docker-compose up -d
```

### Debug Commands
```bash
# Test individual components
python tests/unit/test_script_parser.py
python tests/integration/test_elevenlabs_integration.py
python tests/e2e/test_complete_pipeline.py

# Check service status
docker-compose ps
docker-compose logs api
docker-compose logs worker
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Python backend development
pip install -r requirements-dev.txt
pytest tests/unit/ tests/integration/
flake8 src/ api/ workers/

# Web frontend development
cd web
npm install
npm run dev        # Start development server
npm run type-check # TypeScript validation
npm run lint       # ESLint validation
npm test           # Jest test suite
```

## 📄 API Documentation

Full API documentation available at:
- [API Reference](docs/api/README.md)
- [Integration Guide](docs/api/integration.md)

### Production API Examples
```bash
# Start API server (included in docker-compose)
uvicorn api.main:app --reload

# Upload and parse "The Descent" script
curl -X POST http://localhost:8000/api/v1/script/parse \
  -F "file=@scripts/ScriptLog0002TheDescent.txt"

# Generate audio for all scenes
curl -X POST http://localhost:8000/api/v1/audio/batch \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [...],
    "voice": "winston_calm",
    "settings": {"stability": 0.7}
  }'

# Generate images with DALL-E 3
curl -X POST http://localhost:8000/api/v1/images/batch \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [...],
    "provider": "dalle3"
  }'

# WebSocket connection for real-time updates
# ws://localhost:8000/ws
```

## 🚀 Deployment

### Docker Deployment
```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker/production/docker-compose.prod.yml up -d

# Development with hot reloading
docker-compose up -d

# Scale workers for high throughput
docker-compose up -d --scale worker=3

# Alternative RabbitMQ-based setup
docker-compose -f docker/alternative/docker-compose.celery.yml up -d
```

### Service Architecture
```bash
# Core services
# - Web Interface: http://localhost:3000
# - API Backend: http://localhost:8000  
# - PostgreSQL: localhost:5433
# - Redis: localhost:6379
# - Celery Worker: background processing
# - Flower Monitoring: http://localhost:5555
```

## 📚 Resources

### Documentation
- [Web UI Testing Checklist](web/TESTING_CHECKLIST.md)
- [Production Pipeline Guide](web/RUN_PRODUCTION_PIPELINE.md)
- [Agent Work Log](AGENT_WORK_LOG.md) - Development history
- [Implementation Workflow](docs/development/IMPLEMENTATION_WORKFLOW.md)
- [Architecture Documentation](docs/design/OPENAI_PIPELINE_DESIGN.md)
- [RunwayML Integration Guide](docs/runway/RUNWAY_IMPROVEMENTS.md)
- [Setup Guides](docs/setup/)

### API Documentation
- Interactive API Docs: http://localhost:8000/docs
- WebSocket Events: Real-time progress updates
- Batch Processing: Multi-scene generation endpoints
- State Management: Production workflow persistence

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ElevenLabs** for realistic voice synthesis
- **OpenAI** for DALL-E 3 image generation
- **RunwayML** for Gen-4 Turbo video generation
- **Next.js & React** for the modern web interface
- **FastAPI & Celery** for robust backend processing
- The **"AI 2027: Race"** creative universe

---

## 🎬 Ready to Create?

**Quick Start:**
1. `cd web && npm install && npm run dev`
2. Open http://localhost:3000/production
3. Upload "The Descent" script and start creating!

**Expected Output:** Complete 85-second dystopian thriller video with professional voice narration, cinematic visuals, and terminal UI effects.

**Cost per video:** ~$4.62 | **Generation time:** ~5-10 minutes

For questions or support, please check the [Agent Work Log](AGENT_WORK_LOG.md) or open an issue.