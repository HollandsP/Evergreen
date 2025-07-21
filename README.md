# AI Content Generation Pipeline

Transform written stories into cinematic YouTube videos using AI-powered automation.

## 🎬 Overview

The AI Content Generation Pipeline automates the creation of professional-quality YouTube videos for AI-apocalypse narratives. Starting with "LOG_0002: THE DESCENT" from the "AI 2027: Race" universe, this system enables rapid, modular production of dystopian video content.

### Key Features
- 📝 **Automated Script Processing**: Convert markdown stories to timestamped video scripts
- 🎙️ **AI Voice Synthesis**: Generate character voices with ElevenLabs or Google TTS
- 🎥 **Visual Generation**: Create cinematic scenes with Runway Gen-2 or Pika Labs
- 💻 **Terminal UI Effects**: Simulate retro terminal interfaces with glitch effects
- 🎬 **Smart Assembly**: Automatically sync audio/video into final exports

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- FFmpeg 4.0+
- Docker & Docker Compose
- 16GB RAM (minimum)
- API Keys: ElevenLabs, Runway Gen-2 (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-content-pipeline.git
cd ai-content-pipeline
```

2. **Set up Python environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys:
# ELEVENLABS_API_KEY=your_key_here
# RUNWAY_API_KEY=your_key_here (optional)
```

4. **Initialize the database**
```bash
python scripts/init_db.py
```

5. **Run the pipeline**
```bash
python -m pipeline.cli generate --story stories/LOG_0002_DESCENT.md
```

## 📁 Project Structure

```
ai-content-pipeline/
├── src/
│   ├── core/              # Core utilities and models
│   ├── script_engine/     # Script parsing and processing
│   ├── voice_synthesis/   # Voice generation modules
│   ├── visual_engine/     # Video generation components
│   ├── terminal_sim/      # Terminal UI effects
│   └── assembly/          # Media assembly pipeline
├── api/                   # REST API endpoints
├── templates/             # Prompt and style templates
├── stories/               # Input story files
├── output/                # Generated videos
├── docs/                  # Documentation
└── tests/                 # Test suites
```

## 🎯 Usage Examples

### Basic Video Generation
```bash
# Generate video from a story file
python -m pipeline.cli generate --story stories/LOG_0002_DESCENT.md

# Customize voice and style
python -m pipeline.cli generate \
  --story stories/LOG_0002_DESCENT.md \
  --voice winston_marek \
  --style dystopian_noir
```

### Batch Processing
```bash
# Process multiple stories
python -m pipeline.cli batch --folder stories/ --output output/batch/

# With custom settings
python -m pipeline.cli batch \
  --folder stories/ \
  --config configs/production.yaml
```

### API Usage
```python
from pipeline import ContentPipeline

# Initialize pipeline
pipeline = ContentPipeline()

# Generate video
result = pipeline.generate(
    story_file="stories/LOG_0002_DESCENT.md",
    voice_profile="winston_marek",
    visual_style="dystopian_cinematic"
)

print(f"Video generated: {result.output_path}")
```

## 🛠️ Configuration

### Voice Profiles
Create custom voice profiles in `config/voices.yaml`:
```yaml
winston_marek:
  provider: elevenlabs
  voice_id: "your_voice_id"
  settings:
    stability: 0.7
    similarity_boost: 0.8
    style: "serious"
```

### Visual Templates
Define scene templates in `templates/visual_prompts.json`:
```json
{
  "rooftop_scene": {
    "prompt": "Rooftop view of dystopian Berlin, white uniforms, sunset",
    "style": "cinematic, high contrast, moody lighting",
    "duration": 5,
    "camera": "wide establishing shot"
  }
}
```

## 🔧 Advanced Features

### Terminal UI Customization
```python
from pipeline.terminal_sim import TerminalUI

terminal = TerminalUI(theme="matrix")
terminal.add_typing_effect("SYSTEM FAILURE IMMINENT", speed=0.05)
terminal.add_glitch_transition(intensity=0.8)
```

### Custom Processing Pipeline
```python
from pipeline import CustomPipeline

class MyPipeline(CustomPipeline):
    def post_process_audio(self, audio):
        # Add custom audio effects
        return self.add_reverb(audio, room_size=0.7)
```

## 📊 Monitoring & Analytics

### Pipeline Metrics
- Average processing time: ~90 minutes per video
- API costs: ~$3-5 per video
- Success rate: 95%+

### View metrics dashboard
```bash
python -m pipeline.cli metrics --dashboard
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: ElevenLabs rate limit exceeded
```bash
# Solution: Enable queuing
export ENABLE_RATE_LIMIT_QUEUE=true
```

**Issue**: Video generation timeout
```bash
# Solution: Increase timeout
export VIDEO_GENERATION_TIMEOUT=600
```

**Issue**: Memory errors during assembly
```bash
# Solution: Adjust chunk size
export ASSEMBLY_CHUNK_SIZE=50
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
flake8 src/
black src/ --check
```

## 📄 API Documentation

Full API documentation available at:
- [API Reference](docs/api/README.md)
- [Integration Guide](docs/api/integration.md)

### Quick API Example
```bash
# Start API server
uvicorn api.main:app --reload

# Generate video via API
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "story_file": "stories/LOG_0002_DESCENT.md",
    "settings": {
      "voice": "winston_marek",
      "quality": "high"
    }
  }'
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale workers
docker-compose up -d --scale worker=3
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n content-pipeline
```

## 📚 Resources

- [PRD - Product Requirements](PRD.md)
- [Architecture Documentation](architecture.md)
- [API Specification](docs/api/openapi.yaml)
- [Deployment Guide](docs/deployment.md)

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- ElevenLabs for voice synthesis
- Runway ML for video generation
- The "AI 2027: Race" creative team

---

**Note**: This is a beginner-friendly project designed for indie creators. For questions or support, please open an issue or join our Discord community.