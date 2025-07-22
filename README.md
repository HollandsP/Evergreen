# 🎬 Evergreen - AI-Powered YouTube Video Studio

> Transform scripts into professional YouTube videos with AI-powered storyboarding, generation, and editing.

![Evergreen Studio](./docs/images/evergreen-banner.png)

## 🌟 Overview

Evergreen is a revolutionary video production platform that combines AI with intuitive visual tools to create YouTube content. From scripts to final videos, Evergreen handles the entire production pipeline with a unique **storyboard-first approach**.

### ✨ Key Features

- **📋 Visual Storyboarding** - Plan your entire video with sketches, AI suggestions, or uploaded references
- **🤖 AI Scene Division** - Automatically break scripts into optimized scenes
- **🎨 Flexible Image Creation** - Upload your own or generate with DALL-E 3
- **🎙️ Voice Synthesis** - Natural voices with ElevenLabs integration
- **🎬 Video Generation** - RunwayML Gen-4 Turbo for image-to-video magic
- **✂️ AI Video Editor** - Chat-based editing with natural language commands
- **📤 Direct Publishing** - Export locally or upload directly to YouTube
- **🌙 Dark Mode UI** - Professional interface designed for creators

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.9+ (for AI services)
- PostgreSQL 14+
- Redis 6+
- FFmpeg installed
- API Keys (see Environment Setup)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/evergreen.git
cd evergreen

# Install dependencies
npm install
cd web && npm install
cd ../api && pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize database
npm run db:init

# Start development servers
npm run dev
```

### Environment Variables

```env
# Required API Keys
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
RUNWAY_API_KEY=your_runway_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/evergreen
REDIS_URL=redis://localhost:6379

# Optional
YOUTUBE_API_KEY=your_youtube_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Storyboard (Always Visible)             │
├─────────────────────────────────────────────────────────┤
│ Script → Images → Audio → Video → Edit → Export         │
├─────────────────────────────────────────────────────────┤
│                   Production Workspace                   │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), Node.js APIs
- **AI/ML**: OpenAI GPT-4, DALL-E 3, RunwayML, ElevenLabs
- **Database**: PostgreSQL, Redis
- **Media**: FFmpeg, MoviePy, Sharp
- **Real-time**: WebSockets, Server-Sent Events

## 📁 Project Structure

```
evergreen/
├── web/                 # Next.js frontend
│   ├── components/      # React components
│   │   ├── storyboard/  # Storyboard UI components
│   │   ├── stages/      # Production stage components
│   │   └── editor/      # AI video editor interface
│   ├── pages/          # Page routes
│   └── styles/         # Tailwind styles
├── api/                # Backend services
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   └── models/         # Data models
├── src/                # Python services
│   ├── ai_editor/      # Video editing AI
│   ├── scene_parser/   # Script analysis
│   └── media_pipeline/ # Asset processing
└── docs/              # Documentation
```

## 🎯 Workflow

### 1. Script Upload & Storyboarding
Upload your script and watch as AI divides it into scenes. Create a visual storyboard using our sketch tool, AI generation, or uploaded references.

### 2. Asset Generation
- **Images**: Upload your own or generate with DALL-E 3
- **Audio**: Create voiceovers with ElevenLabs
- **Music**: Upload background tracks

### 3. Video Creation
Convert static images to dynamic videos using RunwayML's Gen-4 Turbo with customizable motion prompts.

### 4. AI Editing
Use natural language to edit your video:
- "Cut the first 3 seconds"
- "Add fade transitions between scenes"
- "Sync to the beat of the music"

### 5. Export & Publish
Export in multiple formats or publish directly to YouTube with AI-generated metadata.

## 💡 Usage Examples

### Creating a YouTube Short

```typescript
// 1. Upload script
const script = `
Scene 1: Opening hook - "Did you know..."
Scene 2: Main point with visual
Scene 3: Call to action
`;

// 2. AI divides into scenes and suggests storyboard
// 3. Generate or upload images
// 4. Create voiceover
// 5. Generate 5-second video clips
// 6. AI edits for optimal pacing
// 7. Export as YouTube Short
```

### Long-Form Content

Perfect for:
- Educational videos
- Story narrations  
- Product demonstrations
- Tutorial content

## 🛠️ Development

### Project Structure

```
evergreen/
├── web/                 # Next.js frontend
│   ├── components/      # React components
│   ├── pages/          # Page routes
│   └── styles/         # Tailwind styles
├── api/                # Backend services
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   └── models/         # Data models
├── src/                # Python services
│   ├── ai_editor/      # Video editing AI
│   ├── scene_parser/   # Script analysis
│   └── media_pipeline/ # Asset processing
└── docs/              # Documentation
```

### Running Tests

```bash
# Frontend tests
cd web && npm test

# Backend tests
cd api && pytest

# E2E tests
npm run test:e2e
```

### Building for Production

```bash
# Build all services
npm run build

# Docker deployment
docker-compose up -d

# Deploy to cloud
npm run deploy
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Roadmap

- [x] Storyboard-first UI design
- [x] Script parsing and scene division
- [x] Image generation/upload
- [x] Voice synthesis integration
- [x] RunwayML video generation
- [ ] AI video editor (in progress)
- [ ] YouTube direct upload
- [ ] Collaborative features
- [ ] Mobile app
- [ ] Plugin system

## 💰 Pricing Estimates

Per video costs (approximate):
- **Script Analysis**: ~$0.10
- **Image Generation**: ~$0.50/scene
- **Voice Synthesis**: ~$0.10/scene  
- **Video Generation**: ~$0.50/scene
- **Total**: ~$5-10 per complete video

## 🔒 Security

- All API keys stored securely
- User content encrypted at rest
- Secure media upload/download
- Rate limiting on all endpoints

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


## 📄 API Documentation

Full API documentation available at:
- [API Reference](docs/api/README.md)
- [Integration Guide](docs/api/integration.md)


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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 and DALL-E 3
- RunwayML for Gen-4 Turbo
- ElevenLabs for voice synthesis
- The open-source community

## 📞 Support

- **Documentation**: [docs.evergreen.ai](https://docs.evergreen.ai)
- **Discord**: [Join our community](https://discord.gg/evergreen)
- **Email**: support@evergreen.ai
- **Issues**: [GitHub Issues](https://github.com/yourusername/evergreen/issues)

---

Built with ❤️ by creators, for creators.