# Evergreen AI - Web Interface

A modern, responsive web interface for the AI video generation pipeline. Built with Next.js, TypeScript, and Tailwind CSS.

## Features

- **Real-time Progress Tracking**: WebSocket integration for live updates
- **Provider Selection**: Switch between DALL-E 3 and Flux.1 
- **Visual Workflow**: Interactive pipeline visualization
- **Media Preview**: Integrated image and video preview with controls
- **Cost Tracking**: Real-time cost estimates and breakdowns
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Settings Management**: Persistent user preferences
- **Download Management**: Direct media downloads with progress indication

## Quick Start

### Prerequisites

- Node.js 18.0 or higher
- npm or yarn package manager
- Running backend service (see main project README)

### Installation

1. **Clone and navigate to web directory**:
   ```bash
   cd web
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` with your configuration:
   ```env
   BACKEND_URL=http://localhost:8000
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Architecture

### Component Structure

```
components/
├── ImageGeneratorPanel.tsx    # Main generation interface
├── WorkflowVisualizer.tsx     # Pipeline progress display
├── MediaPreview.tsx           # Image/video preview component
└── PipelineControls.tsx       # Settings and system controls
```

### API Integration

The web interface communicates with the backend through:

- **REST API**: Job management and system status
- **WebSocket**: Real-time updates and progress tracking
- **File Downloads**: Direct media file downloads

### State Management

- **React State**: Local component state for UI interactions
- **WebSocket Manager**: Singleton for real-time communication
- **LocalStorage**: Persistent user settings and preferences

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_API_BASE_URL` | Public API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000/ws` |
| `API_TOKEN` | Backend authentication token | - |

### Backend Integration

The web interface expects the backend to provide:

1. **REST Endpoints**:
   - `POST /api/v1/generate` - Start generation
   - `GET /api/v1/jobs` - List jobs
   - `GET /api/v1/jobs/{id}` - Get job details
   - `DELETE /api/v1/jobs/{id}` - Cancel job
   - `GET /api/v1/status` - System status

2. **WebSocket Events**:
   - `job_update` - Job status changes
   - `step_update` - Pipeline step progress
   - `job_completed` - Generation completed
   - `job_failed` - Generation failed
   - `system_status` - System status updates

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Style

The project uses:
- TypeScript for type safety
- ESLint for code linting
- Tailwind CSS for styling
- Prettier for code formatting (configured in ESLint)

### Adding New Features

1. **Create components** in the `components/` directory
2. **Add types** to `types/index.ts`
3. **Update API client** in `lib/api.ts` if needed
4. **Add pages** in the `pages/` directory

## Production Deployment

### Build and Deploy

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Set production environment variables**:
   ```env
   NODE_ENV=production
   BACKEND_URL=https://your-backend-url.com
   NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.com
   NEXT_PUBLIC_WS_URL=wss://your-backend-url.com/ws
   ```

3. **Start the production server**:
   ```bash
   npm start
   ```

### Docker Deployment

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

### Vercel Deployment

The application is optimized for Vercel deployment:

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

## API Reference

### WebSocket Events

The web interface listens for these WebSocket events:

```typescript
// Job status update
interface JobUpdateEvent {
  type: 'job_update';
  jobId: string;
  data: GenerationJob;
}

// Pipeline step update
interface StepUpdateEvent {
  type: 'step_update';
  jobId: string;
  data: PipelineStep;
}

// Job completion
interface JobCompletedEvent {
  type: 'job_completed';
  jobId: string;
  data: GenerationJob;
}
```

### REST API Endpoints

All API endpoints are proxied through Next.js API routes for security and CORS handling.

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**:
   - Check backend WebSocket server is running
   - Verify WebSocket URL in environment variables
   - Check firewall and proxy settings

2. **API calls fail**:
   - Verify backend service is running
   - Check API URL and authentication token
   - Review browser console for CORS errors

3. **Build errors**:
   - Ensure all dependencies are installed
   - Check TypeScript errors
   - Verify environment variables are set

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=true
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Evergreen AI video generation pipeline. See the main project LICENSE for details.