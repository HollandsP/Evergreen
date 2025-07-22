# AI Content Pipeline - Progress Monitoring UI Guide

## 📺 Available UIs for Monitoring Video Generation Progress

### 1. 🌸 Flower (Celery Task Monitor)
**URL**: http://localhost:5556
**Credentials**: admin / admin

Flower provides real-time monitoring of your video generation tasks:
- **Task Progress**: See live progress bars for each step (voice generation, video creation, assembly)
- **Worker Status**: Monitor worker health and availability
- **Task History**: View completed, failed, and pending tasks
- **Task Details**: Click on any task to see:
  - Input parameters
  - Execution time
  - Result data
  - Error messages (if any)

### 2. 📚 FastAPI Interactive Documentation
**URL**: http://localhost:8000/docs

The API documentation provides:
- **Interactive Endpoints**: Test API calls directly from the browser
- **Task Status Endpoint**: Check specific task status by ID
- **Project Management**: Create and manage video projects
- **Real-time Testing**: Submit video generation requests and get task IDs

### 3. 🏥 Health Dashboard
**URL**: http://localhost:8000/health

Simple health check endpoint showing:
- API status
- Database connectivity
- Redis connectivity
- Worker availability

## 🎬 Workflow for Video Generation

1. **Submit Video Request**:
   - Use the API docs at http://localhost:8000/docs
   - Call `/api/v1/projects` to create a project
   - Call `/api/v1/scripts/process` to submit your script
   - Each call returns a task ID

2. **Monitor Progress**:
   - Open Flower at http://localhost:5556
   - Find your task ID in the task list
   - Watch the real-time progress bar
   - See status updates as it moves through stages:
     - 📝 Script parsing
     - 🎙️ Voice generation (ElevenLabs)
     - 🎨 Visual generation (Runway)
     - 🎞️ Video assembly (FFmpeg)
     - ☁️ Upload to S3

3. **Check Results**:
   - When task completes, view the result in Flower
   - Result will include:
     - S3 URL for the video
     - Processing time
     - Any warnings or notes

## 🚀 Quick Start

1. Ensure services are running:
   ```bash
   docker-compose -f docker-compose.simple.yml ps
   ```

2. Open Flower in your browser:
   ```
   http://localhost:5556
   ```
   Login with admin/admin

3. In another tab, open the API docs:
   ```
   http://localhost:8000/docs
   ```

4. Submit a video generation request through the API

5. Switch back to Flower to watch the progress!

## 📊 What You'll See in Flower

- **Active Tasks**: Currently running tasks with progress bars
- **Processed Tasks**: Completed tasks with results
- **Failed Tasks**: Any errors with full stack traces
- **Workers**: Number of workers and their current status
- **Queues**: Pending tasks waiting to be processed

The progress bar will update as your video moves through each stage, giving you real-time visibility into the generation process.