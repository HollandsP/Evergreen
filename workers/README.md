# Celery Task Queue Setup

This directory contains the Celery task queue implementation for the AI Content Generation Pipeline.

## Architecture

The system uses Celery with RabbitMQ as the message broker and Redis as the result backend. Tasks are distributed across multiple queues for optimal performance:

### Task Queues

1. **script** - Script parsing and analysis (high priority)
   - Parse screenplay scripts
   - Analyze scene requirements
   - Prepare voice scripts

2. **voice** - Voice synthesis using ElevenLabs (medium priority)
   - Text-to-speech conversion
   - Voice cloning
   - Voice optimization

3. **video** - Video generation using Runway ML (low priority, resource intensive)
   - Generate video segments
   - Create transitions
   - Apply effects

4. **assembly** - Media assembly using FFmpeg (medium priority)
   - Concatenate videos
   - Sync audio/video
   - Add subtitles
   - Platform optimization

## Setup

### Prerequisites

- Python 3.8+
- Redis
- RabbitMQ (or use Redis as broker)
- FFmpeg
- Docker (optional)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDIS_URL=redis://localhost:6379/0
export RABBITMQ_URL=amqp://guest:guest@localhost:5672//
export ELEVENLABS_API_KEY=your_api_key
export RUNWAY_API_KEY=your_api_key
```

### Running Workers

#### Using Scripts

```bash
# Start all workers
./scripts/start_workers.sh

# Stop all workers
./scripts/stop_workers.sh
```

#### Using Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.celery.yml up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.celery.yml logs -f

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.celery.yml down
```

#### Manual Start

```bash
# Start individual workers
celery -A workers.celery_app worker --queues=script --concurrency=4
celery -A workers.celery_app worker --queues=voice --concurrency=2
celery -A workers.celery_app worker --queues=video --concurrency=1
celery -A workers.celery_app worker --queues=assembly --concurrency=2

# Start beat scheduler
celery -A workers.celery_app beat

# Start Flower monitoring
celery -A workers.celery_app flower
```

## Monitoring

### Flower UI

Access the Flower monitoring interface at http://localhost:5555

Default credentials: `admin:password`

### Redis Progress Tracking

Progress for each job is stored in Redis with keys like:
- `job:progress:{job_id}` - Current progress
- `job:status:{job_id}` - Job status
- `metrics:{task_name}:{date}` - Task metrics

### Health Checks

The system includes automatic health monitoring:
- Worker health checks every 5 minutes
- Expired job cleanup every hour
- Redis optimization daily

## Task Examples

### Script Processing

```python
from workers.tasks.script_tasks import parse_script

result = parse_script.delay(
    job_id="job_123",
    script_content="INT. OFFICE - DAY\n\nJOHN enters...",
    metadata={"project": "demo"}
)
```

### Voice Synthesis

```python
from workers.tasks.voice_tasks import synthesize_voice

result = synthesize_voice.delay(
    job_id="job_123",
    voice_script={
        "voice_script": [
            {
                "id": "line_1",
                "character": "JOHN",
                "text": "Hello, world!",
                "emotion": "happy",
                "voice_settings": {"voice_id": "default"}
            }
        ]
    }
)
```

### Video Generation

```python
from workers.tasks.video_tasks import generate_video

result = generate_video.delay(
    job_id="job_123",
    scene_data={
        "scene_id": "scene_1",
        "description": "A beautiful sunset over the ocean",
        "duration_estimate": 5.0
    }
)
```

### Media Assembly

```python
from workers.tasks.assembly_tasks import assemble_final_video

result = assemble_final_video.delay(
    job_id="job_123",
    assembly_data={
        "video_segments": [...],
        "audio_files": [...],
        "transitions": [...]
    }
)
```

## Configuration

### Celery Settings

Configuration is in `workers/config.py`:

- **Task routing** - Automatic routing based on task name
- **Retry settings** - Exponential backoff with jitter
- **Priority queues** - Different priorities for different task types
- **Resource limits** - Memory and time limits for resource-intensive tasks

### Performance Tuning

Adjust concurrency based on your hardware:

- **Script tasks**: 4-8 workers (CPU bound)
- **Voice tasks**: 2-4 workers (API rate limited)
- **Video tasks**: 1-2 workers (Memory intensive)
- **Assembly tasks**: 2-4 workers (I/O bound)

## Error Handling

All tasks include:

- Automatic retry with exponential backoff
- Progress reporting to Redis
- Database status updates
- Comprehensive error logging
- Graceful degradation

## Extending

To add new task types:

1. Create a new task file in `workers/tasks/`
2. Add task routing in `workers/config.py`
3. Update queue configuration if needed
4. Add worker startup in scripts

## Troubleshooting

### Common Issues

1. **Workers not starting**
   - Check Redis/RabbitMQ connectivity
   - Verify environment variables
   - Check logs in `logs/` directory

2. **Tasks stuck in pending**
   - Ensure workers are running for the queue
   - Check Flower UI for worker status
   - Verify task routing configuration

3. **Memory issues**
   - Reduce video worker concurrency
   - Adjust `worker_max_tasks_per_child`
   - Monitor with Flower

### Debug Mode

Enable debug logging:

```bash
celery -A workers.celery_app worker --loglevel=debug
```

### Health Check

```bash
# Check worker status
celery -A workers.celery_app inspect active

# Check registered tasks
celery -A workers.celery_app inspect registered

# Ping workers
celery -A workers.celery_app inspect ping
```