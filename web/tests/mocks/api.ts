// Mock external API services for testing

export const mockBackendResponse = {
  health: {
    status: 'ok',
    timestamp: new Date().toISOString(),
    services: {
      database: 'up',
      redis: 'up',
      storage: 'up',
    },
  },
  parseScript: {
    success: true,
    scenes: [
      {
        id: 'scene-1',
        speaker: 'Narrator', 
        text: 'This is a test scene.',
        duration: 5.2,
        timestamp: 0,
      },
      {
        id: 'scene-2',
        speaker: 'Character',
        text: 'This is another test scene.',
        duration: 3.8,
        timestamp: 5.2,
      },
    ],
    totalDuration: 9.0,
  },
  generateAudio: {
    success: true,
    audioUrl: '/api/audio/mock/test-scene.mp3',
    duration: 5.2,
    jobId: 'audio-job-123',
  },
  generateImage: {
    success: true,
    imageUrl: '/api/images/mock/test-image.jpg',
    prompt: 'A cinematic scene',
    jobId: 'image-job-123',
  },
  generateVideo: {
    success: true,
    videoUrl: '/api/videos/mock/test-video.mp4',
    duration: 10.5,
    jobId: 'video-job-123',
  },
  assembleVideo: {
    success: true,
    videoUrl: '/api/assembly/mock/final-video.mp4',
    duration: 125.3,
    jobId: 'assembly-job-123',
  },
};

export const mockErrorResponse = {
  success: false,
  error: 'Test error message',
  code: 'TEST_ERROR',
};

// Mock fetch implementation for API tests
export const createMockFetch = (mockResponses: Record<string, any> = {}) => {
  return jest.fn().mockImplementation((url: string, options?: RequestInit) => {
    const method = options?.method || 'GET';
    const urlPath = new URL(url, 'http://localhost').pathname;
    
    // Default successful response
    let responseData = mockResponses[`${method} ${urlPath}`] || mockResponses[urlPath] || {};
    
    // Handle health check endpoint specifically
    if (urlPath.includes('/health')) {
      responseData = mockBackendResponse.health;
    }
    
    return Promise.resolve({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: () => Promise.resolve(responseData),
      text: () => Promise.resolve(JSON.stringify(responseData)),
      headers: new Headers({
        'content-type': 'application/json',
      }),
    });
  });
};

// Mock WebSocket for API tests
export const createMockWebSocket = () => {
  const mockWs = {
    connected: false,
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
    connect: jest.fn(),
    off: jest.fn(),
    removeAllListeners: jest.fn(),
  };
  
  return mockWs;
};
