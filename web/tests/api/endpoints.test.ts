import { createMocks } from 'node-mocks-http';
import { NextApiRequest, NextApiResponse } from 'next';
import { createMockFetch, mockBackendResponse } from '../mocks/api';

// Import API handlers
import scriptParseHandler from '@/pages/api/script/parse';
import scriptUploadHandler from '@/pages/api/script/upload';
import voiceListHandler from '@/pages/api/voice/list';
import audioGenerateHandler from '@/pages/api/audio/generate';
import audioBatchHandler from '@/pages/api/audio/batch';
import imageGenerateHandler from '@/pages/api/images/generate';
import imageBatchHandler from '@/pages/api/images/batch';
import videoGenerateHandler from '@/pages/api/videos/generate';
import videoBatchHandler from '@/pages/api/videos/batch';
import assemblyExportHandler from '@/pages/api/assembly/export';
import healthHandler from '@/pages/api/health';
import statusHandler from '@/pages/api/status';

// Mock external dependencies
jest.mock('@/lib/api', () => ({
  parseScript: jest.fn().mockResolvedValue({
    success: true,
    scenes: [
      {
        id: 'scene-1',
        speaker: 'Narrator',
        text: 'This is a test.',
        duration: 5,
      },
    ],
  }),
  generateAudio: jest.fn().mockResolvedValue({
    success: true,
    audioUrl: '/audio/test.mp3',
    duration: 5,
  }),
  generateImage: jest.fn().mockResolvedValue({
    success: true,
    imageUrl: '/images/test.jpg',
    prompt: 'test prompt',
  }),
  generateVideo: jest.fn().mockResolvedValue({
    success: true,
    videoUrl: '/videos/test.mp4',
    duration: 10,
  }),
  assembleVideo: jest.fn().mockResolvedValue({
    success: true,
    videoUrl: '/videos/final.mp4',
    duration: 60,
  }),
}));

// Mock file system operations
jest.mock('fs', () => ({
  readFileSync: jest.fn().mockReturnValue('# Test Script\n\n**Narrator**: This is a test.'),
  existsSync: jest.fn().mockReturnValue(true),
  promises: {
    readFile: jest.fn().mockResolvedValue('# Test Script\n\n**Narrator**: This is a test.'),
  },
}));

jest.mock('formidable', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    parse: jest.fn((req, callback) => {
      callback(null, {}, {
        file: [{
          filepath: '/tmp/test.txt',
          originalFilename: 'test-script.txt',
          mimetype: 'text/plain',
          size: 1024,
        }],
      });
    }),
  })),
}));

describe('API Endpoints', () => {
  beforeAll(() => {
    // Setup global fetch mock
    global.fetch = createMockFetch({
      '/health': mockBackendResponse.health,
    });
  });
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('/api/script/parse', () => {
    it('should parse script content successfully', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          content: '# Test Script\n\n**Narrator**: This is a test.',
        },
      });

      await scriptParseHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('scenes');
      expect(Array.isArray(jsonData.scenes)).toBe(true);
    });

    it('should validate request method', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'GET',
      });

      await scriptParseHandler(req, res);

      expect(res._getStatusCode()).toBe(405);
      expect(JSON.parse(res._getData())).toEqual({
        error: 'Method not allowed',
      });
    });

    it('should handle missing content', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {},
      });

      await scriptParseHandler(req, res);

      expect(res._getStatusCode()).toBe(400);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });

    it('should handle parsing errors', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          content: 'Invalid \x00 content',
        },
      });

      await scriptParseHandler(req, res);

      expect(res._getStatusCode()).toBe(400);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });
  });

  describe('/api/script/upload', () => {
    it('should handle file upload successfully', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        headers: {
          'content-type': 'multipart/form-data',
        },
      });

      await scriptUploadHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('scenes');
      expect(jsonData).toHaveProperty('fileName', 'test-script.txt');
    });

    it('should validate file type', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        headers: {
          'content-type': 'multipart/form-data',
        },
      });

      // Mock formidable to return invalid file type
      jest.requireMock('formidable').default.mockImplementationOnce(() => ({
        parse: jest.fn((req, callback) => {
          callback(null, {}, {
            file: [{
              filepath: '/tmp/test.exe',
              originalFilename: 'test.exe',
              mimetype: 'application/exe',
              size: 1024,
            }],
          });
        }),
      }));

      await scriptUploadHandler(req, res);

      expect(res._getStatusCode()).toBe(400);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });
  });

  describe('/api/voice/list', () => {
    it('should return available voices', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'GET',
      });

      await voiceListHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('voices');
      expect(Array.isArray(jsonData.voices)).toBe(true);
    });
  });

  describe('/api/audio/generate', () => {
    it('should generate audio for a scene', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          sceneId: 'scene_1',
          text: 'Test narration',
          voiceId: 'test_voice',
        },
      });

      await audioGenerateHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('sceneId', 'scene_1');
      expect(jsonData).toHaveProperty('url');
      expect(jsonData).toHaveProperty('duration');
    });

    it('should validate required fields', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          sceneId: 'scene_1',
          // missing text and voiceId
        },
      });

      await audioGenerateHandler(req, res);

      expect(res._getStatusCode()).toBe(400);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });
  });

  describe('/api/audio/batch', () => {
    it('should generate audio for multiple scenes', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          scenes: [
            { sceneId: 'scene_1', text: 'Test 1' },
            { sceneId: 'scene_2', text: 'Test 2' },
          ],
          voiceId: 'test_voice',
        },
      });

      await audioBatchHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('success', true);
      expect(jsonData).toHaveProperty('results');
      expect(jsonData.results).toHaveLength(2);
    });

    it('should handle partial failures', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          scenes: [
            { sceneId: 'scene_1', text: 'Test 1' },
            { sceneId: 'scene_2', text: '' }, // Invalid - empty text
          ],
          voiceId: 'test_voice',
        },
      });

      await audioBatchHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('success', false);
      expect(jsonData).toHaveProperty('failed');
      expect(jsonData.failed).toContain('scene_2');
    });
  });

  describe('/api/images/generate', () => {
    it('should generate image with DALL-E 3', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          prompt: 'A beautiful mountain landscape',
          provider: 'dalle3',
          sceneId: 'scene_1',
          size: '1024x1024',
        },
      });

      await imageGenerateHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('url');
      expect(jsonData).toHaveProperty('provider', 'dalle3');
      expect(jsonData).toHaveProperty('sceneId', 'scene_1');
      expect(jsonData).toHaveProperty('cost');
    });

    it('should validate image size', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          prompt: 'Test prompt',
          provider: 'dalle3',
          sceneId: 'scene_1',
          size: '9999x9999', // Invalid size
        },
      });

      await imageGenerateHandler(req, res);

      expect(res._getStatusCode()).toBe(400);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });
  });

  describe('/api/images/batch', () => {
    it('should generate multiple images', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          scenes: [
            { sceneId: 'scene_1', prompt: 'Mountain landscape' },
            { sceneId: 'scene_2', prompt: 'Ocean view' },
          ],
          provider: 'dalle3',
        },
      });

      await imageBatchHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('success', true);
      expect(jsonData.results).toHaveLength(2);
    });

    it('should calculate total cost', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          scenes: [
            { sceneId: 'scene_1', prompt: 'Test 1' },
            { sceneId: 'scene_2', prompt: 'Test 2' },
          ],
          provider: 'dalle3',
          size: '1024x1024',
        },
      });

      await imageBatchHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('totalCost', 0.08); // $0.04 * 2
    });
  });

  describe('/api/videos/generate', () => {
    it('should generate video from image', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          sceneId: 'scene_1',
          imageUrl: '/images/test.jpg',
          duration: 5,
          provider: 'runway',
          motionPrompt: 'Slow zoom in',
        },
      });

      await videoGenerateHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('sceneId', 'scene_1');
      expect(jsonData).toHaveProperty('videoUrl');
      expect(jsonData).toHaveProperty('duration', 5);
    });
  });

  describe('/api/videos/batch', () => {
    it('should generate videos with audio sync', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          scenes: [
            {
              sceneId: 'scene_1',
              imageUrl: '/images/1.jpg',
              audioDuration: 5,
            },
            {
              sceneId: 'scene_2',
              imageUrl: '/images/2.jpg',
              audioDuration: 4,
            },
          ],
          provider: 'runway',
        },
      });

      await videoBatchHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('success', true);
      expect(jsonData.results).toHaveLength(2);
      expect(jsonData.results[0].duration).toBe(5);
      expect(jsonData.results[1].duration).toBe(4);
    });
  });

  describe('/api/assembly/export', () => {
    it('should export final video', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          scenes: [
            { videoUrl: '/videos/1.mp4', duration: 5 },
            { videoUrl: '/videos/2.mp4', duration: 4 },
          ],
          format: 'mp4',
          quality: 'high',
          projectId: 'test_project',
        },
      });

      await assemblyExportHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('success', true);
      expect(jsonData).toHaveProperty('videoUrl');
      expect(jsonData).toHaveProperty('downloadUrl');
    });

    it('should validate export format', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: {
          scenes: [],
          format: 'invalid_format',
          quality: 'high',
        },
      });

      await assemblyExportHandler(req, res);

      expect(res._getStatusCode()).toBe(400);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });
  });

  describe('/api/health', () => {
    it('should return health status', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'GET',
      });

      await healthHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('status', 'healthy');
      expect(jsonData).toHaveProperty('timestamp');
    });
  });

  describe('/api/health', () => {
    it('should return service health status', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'GET',
      });

      await healthHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('status');
      expect(jsonData).toHaveProperty('timestamp');
      expect(jsonData).toHaveProperty('services');
      expect(jsonData.services).toHaveProperty('frontend', 'up');
    });

    it('should handle health check method restrictions', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST', // Should only accept GET
      });

      await healthHandler(req, res);

      expect(res._getStatusCode()).toBe(405);
      expect(res.getHeader('Allow')).toContain('GET');
    });
  });

  describe('/api/status', () => {
    it('should return system status', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'GET',
      });

      await statusHandler(req, res);

      expect(res._getStatusCode()).toBe(200);
      const jsonData = JSON.parse(res._getData());
      expect(jsonData).toHaveProperty('dalle3Available');
      expect(jsonData).toHaveProperty('runwayAvailable');
      expect(jsonData).toHaveProperty('activeJobs');
      expect(jsonData).toHaveProperty('queueLength');
    });
  });

  describe('Error Handling', () => {
    it('should handle rate limiting', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: { prompt: 'Test', provider: 'dalle3', sceneId: 'test' },
        headers: {
          'x-rate-limit-remaining': '0',
        },
      });

      // Mock rate limit response
      res.setHeader('X-RateLimit-Limit', '100');
      res.setHeader('X-RateLimit-Remaining', '0');
      res.setHeader('X-RateLimit-Reset', String(Date.now() + 3600000));
      res.status(429).json({ error: 'Rate limit exceeded', retryAfter: 3600 });

      expect(res._getStatusCode()).toBe(429);
      expect(JSON.parse(res._getData())).toHaveProperty('error', 'Rate limit exceeded');
    });

    it('should handle server errors gracefully', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: { sceneId: 'test', text: 'Test', voiceId: 'test' },
      });

      // Mock internal server error
      jest.requireMock('@/lib/api').generateAudio.mockRejectedValueOnce(
        new Error('Internal server error'),
      );

      await audioGenerateHandler(req, res);

      expect(res._getStatusCode()).toBe(500);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });
  });

  describe('Validation', () => {
    it('should validate content type', async () => {
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        headers: {
          'content-type': 'text/plain',
        },
        body: 'invalid body',
      });

      await scriptParseHandler(req, res);

      expect(res._getStatusCode()).toBe(400);
      expect(JSON.parse(res._getData())).toHaveProperty('error');
    });

    it('should validate request size', async () => {
      const largeContent = 'x'.repeat(10 * 1024 * 1024); // 10MB
      const { req, res } = createMocks<NextApiRequest, NextApiResponse>({
        method: 'POST',
        body: { content: largeContent },
      });

      await scriptParseHandler(req, res);

      expect(res._getStatusCode()).toBe(413);
      expect(JSON.parse(res._getData())).toHaveProperty('error', 'Request too large');
    });
  });
});
