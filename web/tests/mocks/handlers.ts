import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Define API base URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

// Mock handlers for MSW
export const handlers = [
  // Script endpoints
  rest.post(`${API_URL}/script/parse`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        scenes: [
          {
            id: 'scene_1',
            timestamp: 0,
            narration: 'Mock narration',
            onScreenText: '',
            imagePrompt: 'Mock image prompt',
            metadata: {
              sceneType: 'establishing',
              description: 'Mock scene',
              visual: 'Mock visual',
            },
          },
        ],
        totalDuration: 5,
      }),
    );
  }),

  rest.post(`${API_URL}/script/upload`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        scenes: [],
        fileName: 'test-script.txt',
        fileSize: 1024,
      }),
    );
  }),

  // Voice endpoints
  rest.get(`${API_URL}/voice/list`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        voices: [
          {
            voice_id: 'winston_churchill',
            name: 'Winston Churchill',
            category: 'historical',
            is_winston: true,
          },
          {
            voice_id: 'test_voice',
            name: 'Test Voice',
            category: 'test',
          },
        ],
      }),
    );
  }),

  // Audio endpoints
  rest.post(`${API_URL}/audio/generate`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        sceneId: 'scene_1',
        url: '/audio/scene_1.mp3',
        duration: 5,
      }),
    );
  }),

  rest.post(`${API_URL}/audio/batch`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        results: [
          {
            sceneId: 'scene_1',
            url: '/audio/scene_1.mp3',
            duration: 5,
          },
        ],
      }),
    );
  }),

  // Mock audio files
  rest.get(`${API_URL}/audio/mock/:sceneId`, (req, res, ctx) => {
    const { sceneId } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        url: `/audio/${sceneId}.mp3`,
        duration: 5,
      }),
    );
  }),

  // Image endpoints
  rest.post(`${API_URL}/images/generate`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        sceneId: 'scene_1',
        url: '/images/scene_1.jpg',
        provider: 'dalle3',
        cost: 0.04,
      }),
    );
  }),

  rest.post(`${API_URL}/images/batch`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        results: [
          {
            sceneId: 'scene_1',
            url: '/images/scene_1.jpg',
            provider: 'dalle3',
            cost: 0.04,
          },
        ],
        totalCost: 0.04,
      }),
    );
  }),

  // Video endpoints
  rest.post(`${API_URL}/videos/generate`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        sceneId: 'scene_1',
        videoUrl: '/videos/scene_1.mp4',
        duration: 5,
      }),
    );
  }),

  rest.post(`${API_URL}/videos/batch`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        results: [
          {
            sceneId: 'scene_1',
            videoUrl: '/videos/scene_1.mp4',
            duration: 5,
          },
        ],
      }),
    );
  }),

  // Assembly endpoints
  rest.post(`${API_URL}/assembly/export`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        videoUrl: '/final/output.mp4',
        downloadUrl: '/download/output.mp4',
      }),
    );
  }),

  // Production state
  rest.get(`${API_URL}/production/state`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        script: { status: 'idle', scenes: [], parseProgress: 0 },
        voice: { status: 'idle', availableVoices: [] },
        audio: { status: 'idle', progress: 0, generatedAudio: [], totalDuration: 0 },
        images: { status: 'idle', progress: 0, generatedImages: [], provider: 'dalle3' },
        video: { status: 'idle', progress: 0, scenes: [], provider: 'runway' },
        assembly: { status: 'idle', progress: 0, exportFormat: 'mp4', exportQuality: 'high' },
        currentStage: 'script',
        isLocked: false,
        lastSaved: new Date().toISOString(),
        projectId: 'test_project',
      }),
    );
  }),

  rest.post(`${API_URL}/production/state`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ success: true }));
  }),

  // Health and status
  rest.get(`${API_URL}/health`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
      }),
    );
  }),

  rest.get(`${API_URL}/status`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        dalle3Available: true,
        runwayAvailable: true,
        activeJobs: 0,
        queueLength: 0,
        systemLoad: 0.5,
      }),
    );
  }),

  // Job endpoints
  rest.get(`${API_URL}/jobs/:id`, (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        id,
        status: 'completed',
        progress: 100,
        result: {
          url: `/results/${id}`,
        },
      }),
    );
  }),

  rest.get(`${API_URL}/jobs/:id/download/:type`, (req, res, ctx) => {
    const { id, type } = req.params;
    return res(
      ctx.status(200),
      ctx.set('Content-Type', 'application/octet-stream'),
      ctx.body('Mock file content'),
    );
  }),
];

// Create mock server
export const server = setupServer(...handlers);

// Helper to add custom handlers for specific tests
export const addCustomHandler = (handler: any) => {
  server.use(handler);
};

// Helper to simulate errors
export const simulateError = (endpoint: string, status = 500, message = 'Internal server error') => {
  server.use(
    rest.post(`${API_URL}${endpoint}`, (req, res, ctx) => {
      return res(ctx.status(status), ctx.json({ error: message }));
    }),
    rest.get(`${API_URL}${endpoint}`, (req, res, ctx) => {
      return res(ctx.status(status), ctx.json({ error: message }));
    }),
  );
};

// Helper to simulate delays
export const simulateDelay = (endpoint: string, delay: number) => {
  server.use(
    rest.post(`${API_URL}${endpoint}`, (req, res, ctx) => {
      return res(ctx.delay(delay));
    }),
    rest.get(`${API_URL}${endpoint}`, (req, res, ctx) => {
      return res(ctx.delay(delay));
    }),
  );
};

// Helper to simulate rate limiting
export const simulateRateLimit = (endpoint: string) => {
  server.use(
    rest.post(`${API_URL}${endpoint}`, (req, res, ctx) => {
      return res(
        ctx.status(429),
        ctx.json({ error: 'Rate limit exceeded', retryAfter: 60 }),
        ctx.set('X-RateLimit-Limit', '100'),
        ctx.set('X-RateLimit-Remaining', '0'),
        ctx.set('X-RateLimit-Reset', String(Date.now() + 3600000)),
      );
    }),
  );
};
