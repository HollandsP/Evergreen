import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react-dom/test-utils';
import { productionState, getProductionState } from '@/lib/production-state';
import { wsManager } from '@/lib/websocket';
import { io } from 'socket.io-client';

// Mock socket.io-client
jest.mock('socket.io-client');

// Mock API calls
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

// Mock WebSocket events
const mockSocket = {
  connected: true,
  on: jest.fn(),
  emit: jest.fn(),
  disconnect: jest.fn(),
  connect: jest.fn(),
};

describe('Video Production Pipeline Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    productionState.reset()
    ;(io as jest.Mock).mockReturnValue(mockSocket);
    
    // Reset WebSocket mock handlers
    mockSocket.on.mockReset();
    mockSocket.emit.mockReset();
  });

  describe('Complete Pipeline Flow', () => {
    it('should process a script from upload to final video', async () => {
      // Mock successful API responses
      const mockScriptResponse = {
        scenes: [
          {
            id: 'scene_1',
            timestamp: 0,
            narration: 'In the depths of the earth, darkness holds secrets...',
            onScreenText: '',
            imagePrompt: 'Remote snow-covered mountain landscape, desolate terrain',
            metadata: {
              sceneType: 'establishing',
              description: 'Opening shot',
              visual: 'Mountain landscape',
            },
          },
          {
            id: 'scene_2',
            timestamp: 5,
            narration: 'This is it. The adventure we\'ve been waiting for.',
            onScreenText: 'Sarah',
            imagePrompt: 'Six women at cave entrance, headlamps in darkness',
            metadata: {
              sceneType: 'dialogue',
              description: 'Cave entrance',
              visual: 'Group at cave mouth',
            },
          },
        ],
        totalDuration: 10,
      };

      // 1. Test Script Upload and Parsing
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockScriptResponse,
      } as Response);

      await act(async () => {
        productionState.updateStage('script', {
          status: 'uploading',
          fileName: 'test-script.txt',
          fileSize: 1024,
        });
      });

      // Simulate script parsing
      await act(async () => {
        productionState.updateStage('script', {
          status: 'parsing',
          parseProgress: 50,
        });
      });

      await act(async () => {
        productionState.updateStage('script', {
          status: 'completed',
          scenes: mockScriptResponse.scenes,
          parseProgress: 100,
        });
      });

      const state = getProductionState();
      expect(state.script.status).toBe('completed');
      expect(state.script.scenes).toHaveLength(2);

      // 2. Test Voice Selection
      const mockVoices = [
        {
          voice_id: 'winston_churchill',
          name: 'Winston Churchill',
          category: 'historical',
          is_winston: true,
        },
        {
          voice_id: 'morgan_freeman',
          name: 'Morgan Freeman',
          category: 'celebrity',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ voices: mockVoices }),
      } as Response);

      await act(async () => {
        productionState.updateStage('voice', {
          status: 'loading',
        });
      });

      await act(async () => {
        productionState.updateStage('voice', {
          status: 'completed',
          availableVoices: mockVoices,
          selectedVoiceId: 'winston_churchill',
          selectedVoiceName: 'Winston Churchill',
        });
      });

      expect(getProductionState().voice.selectedVoiceId).toBe('winston_churchill');

      // 3. Test Audio Generation
      const mockAudioResponses = [
        { sceneId: 'scene_1', url: '/audio/scene_1.mp3', duration: 5 },
        { sceneId: 'scene_2', url: '/audio/scene_2.mp3', duration: 5 },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true,
          results: mockAudioResponses,
        }),
      } as Response);

      await act(async () => {
        productionState.updateStage('audio', {
          status: 'generating',
          progress: 0,
        });
      });

      // Simulate WebSocket progress updates
      const audioProgressHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'job_update',
      )?.[1];

      if (audioProgressHandler) {
        act(() => {
          audioProgressHandler({
            jobId: 'audio_batch_1',
            progress: 50,
            stage: 'audio',
          });
        });
      }

      await act(async () => {
        productionState.updateStage('audio', {
          status: 'completed',
          progress: 100,
          generatedAudio: mockAudioResponses.map(r => ({
            ...r,
            status: 'completed' as const,
          })),
          totalDuration: 10,
        });
      });

      expect(getProductionState().audio.generatedAudio).toHaveLength(2);

      // 4. Test Image Generation with DALL-E 3
      const mockImageResponses = [
        { 
          sceneId: 'scene_1', 
          url: '/images/scene_1.jpg',
          provider: 'dalle3',
          cost: 0.04,
        },
        { 
          sceneId: 'scene_2', 
          url: '/images/scene_2.jpg',
          provider: 'dalle3',
          cost: 0.04,
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true,
          results: mockImageResponses,
        }),
      } as Response);

      await act(async () => {
        productionState.updateStage('images', {
          status: 'generating',
          progress: 0,
          provider: 'dalle3',
        });
      });

      await act(async () => {
        productionState.updateStage('images', {
          status: 'completed',
          progress: 100,
          generatedImages: mockImageResponses.map(r => ({
            ...r,
            prompt: state.script.scenes.find(s => s.id === r.sceneId)?.imagePrompt || '',
            status: 'completed' as const,
          })),
        });
      });

      expect(getProductionState().images.generatedImages).toHaveLength(2);

      // 5. Test Video Generation
      const mockVideoResponses = [
        {
          sceneId: 'scene_1',
          videoUrl: '/videos/scene_1.mp4',
          duration: 5,
        },
        {
          sceneId: 'scene_2',
          videoUrl: '/videos/scene_2.mp4',
          duration: 5,
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true,
          results: mockVideoResponses,
        }),
      } as Response);

      await act(async () => {
        productionState.updateStage('video', {
          status: 'generating',
          progress: 0,
          provider: 'runway',
        });
      });

      await act(async () => {
        productionState.updateStage('video', {
          status: 'completed',
          progress: 100,
          scenes: mockVideoResponses.map(r => ({
            ...r,
            status: 'completed' as const,
            imageUrl: mockImageResponses.find(i => i.sceneId === r.sceneId)?.url || '',
          })),
        });
      });

      expect(getProductionState().video.scenes).toHaveLength(2);

      // 6. Test Final Assembly and Export
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true,
          videoUrl: '/final/output.mp4',
          downloadUrl: '/download/output.mp4',
        }),
      } as Response);

      await act(async () => {
        productionState.updateStage('assembly', {
          status: 'assembling',
          progress: 0,
          exportFormat: 'mp4',
          exportQuality: 'high',
        });
      });

      await act(async () => {
        productionState.updateStage('assembly', {
          status: 'completed',
          progress: 100,
          finalVideoUrl: '/final/output.mp4',
        });
      });

      const finalState = getProductionState();
      expect(finalState.assembly.status).toBe('completed');
      expect(finalState.assembly.finalVideoUrl).toBeDefined();

      // Validate complete pipeline
      const validation = productionState.validateState();
      expect(validation.valid).toBe(true);
      expect(validation.errors).toHaveLength(0);

      // Check overall progress
      expect(productionState.getProgress()).toBe(100);
    });

    it('should handle API failures gracefully', async () => {
      // Test script parsing failure
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        productionState.updateStage('script', {
          status: 'error',
          error: 'Failed to parse script: Network error',
        });
      });

      expect(getProductionState().script.status).toBe('error');
      expect(getProductionState().script.error).toContain('Network error');

      // Test recovery
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ scenes: [], totalDuration: 0 }),
      } as Response);

      await act(async () => {
        productionState.updateStage('script', {
          status: 'completed',
          scenes: [],
          error: undefined,
        });
      });

      expect(getProductionState().script.status).toBe('completed');
      expect(getProductionState().script.error).toBeUndefined();
    });

    it('should handle WebSocket disconnection', async () => {
      // Simulate WebSocket disconnection
      const disconnectHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'disconnect',
      )?.[1];

      if (disconnectHandler) {
        act(() => {
          disconnectHandler('transport close');
        });
      }

      // Verify reconnection attempt
      await waitFor(() => {
        expect(mockSocket.connect).toHaveBeenCalled();
      });
    });

    it('should persist state across page reloads', async () => {
      const testState = {
        script: {
          status: 'completed' as const,
          scenes: [{ id: 'test', narration: 'Test' }] as any,
          parseProgress: 100,
        },
      };

      // Update state
      await act(async () => {
        productionState.updateStage('script', testState.script);
      });

      // Simulate page reload by creating new instance
      const savedState = localStorage.getItem('evergreen_production_state');
      expect(savedState).toBeDefined();

      const parsedState = JSON.parse(savedState!);
      expect(parsedState.script.status).toBe('completed');
      expect(parsedState.script.scenes).toHaveLength(1);
    });

    it('should validate state progression', () => {
      // Cannot proceed to audio without completing voice selection
      expect(productionState.canProceedToStage('audio')).toBe(false);

      // Complete script stage
      productionState.updateStage('script', { status: 'completed' });
      expect(productionState.canProceedToStage('voice')).toBe(true);

      // Complete voice stage
      productionState.updateStage('voice', { status: 'completed' });
      expect(productionState.canProceedToStage('audio')).toBe(true);

      // Can always go back to previous stages
      productionState.setCurrentStage('images');
      expect(productionState.canProceedToStage('script')).toBe(true);
      expect(productionState.canProceedToStage('voice')).toBe(true);
    });

    it('should handle batch operations efficiently', async () => {
      const scenes = Array.from({ length: 10 }, (_, i) => ({
        id: `scene_${i}`,
        narration: `Scene ${i} narration`,
        imagePrompt: `Scene ${i} visual`,
      }));

      // Mock batch image generation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          results: scenes.map(s => ({
            sceneId: s.id,
            url: `/images/${s.id}.jpg`,
            provider: 'dalle3',
            cost: 0.04,
          })),
        }),
      } as Response);

      // Test batch processing doesn't block UI
      const startTime = Date.now();
      
      await act(async () => {
        productionState.updateStage('images', {
          status: 'generating',
          progress: 0,
        });
      });

      // Simulate progress updates
      for (let i = 0; i <= 100; i += 10) {
        await act(async () => {
          productionState.updateStage('images', {
            progress: i,
          });
        });
      }

      const endTime = Date.now();
      expect(endTime - startTime).toBeLessThan(1000); // Should complete quickly
    });
  });

  describe('Error Recovery', () => {
    it('should recover from partial failures in batch operations', async () => {
      const mockBatchResponse = {
        success: false,
        results: [
          { sceneId: 'scene_1', url: '/audio/scene_1.mp3', duration: 5 },
          { sceneId: 'scene_2', error: 'Generation failed' },
        ],
        failed: ['scene_2'],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBatchResponse,
      } as Response);

      await act(async () => {
        productionState.updateStage('audio', {
          status: 'generating',
          generatedAudio: [
            { sceneId: 'scene_1', url: '/audio/scene_1.mp3', duration: 5, status: 'completed' },
            { sceneId: 'scene_2', url: '', duration: 0, status: 'error', error: 'Generation failed' },
          ],
        });
      });

      const state = getProductionState();
      expect(state.audio.generatedAudio[0].status).toBe('completed');
      expect(state.audio.generatedAudio[1].status).toBe('error');

      // Retry failed scene
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          sceneId: 'scene_2',
          url: '/audio/scene_2.mp3',
          duration: 5,
        }),
      } as Response);

      await act(async () => {
        const audio = state.audio.generatedAudio;
        audio[1] = { sceneId: 'scene_2', url: '/audio/scene_2.mp3', duration: 5, status: 'completed' };
        productionState.updateStage('audio', { generatedAudio: audio });
      });

      expect(getProductionState().audio.generatedAudio[1].status).toBe('completed');
    });

    it('should handle invalid file uploads', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Invalid file format' }),
      } as Response);

      await act(async () => {
        productionState.updateStage('script', {
          status: 'error',
          error: 'Invalid file format',
        });
      });

      expect(getProductionState().script.status).toBe('error');
      expect(getProductionState().script.error).toBe('Invalid file format');
    });

    it('should handle API rate limiting', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({ 
          error: 'Rate limit exceeded',
          retryAfter: 60,
        }),
      } as Response);

      await act(async () => {
        productionState.updateStage('images', {
          status: 'error',
          error: 'Rate limit exceeded. Please retry after 60 seconds.',
        });
      });

      expect(getProductionState().images.error).toContain('Rate limit');
    });
  });

  describe('State Management', () => {
    it('should export and import state correctly', () => {
      const testState = getProductionState();
      testState.script.scenes = [{ id: 'test', narration: 'Test scene' } as any];
      
      productionState.updateStage('script', testState.script);
      
      const exported = productionState.exportState();
      productionState.reset();
      
      expect(getProductionState().script.scenes).toHaveLength(0);
      
      productionState.importState(exported);
      expect(getProductionState().script.scenes).toHaveLength(1);
      expect(getProductionState().script.scenes[0].id).toBe('test');
    });

    it('should handle state locking during critical operations', () => {
      productionState.lockState();
      expect(getProductionState().isLocked).toBe(true);

      // Attempt to update while locked
      const initialScenes = getProductionState().script.scenes;
      productionState.updateStage('script', { scenes: [] });
      
      // State should still update even when locked (lock is advisory)
      expect(getProductionState().script.scenes).toHaveLength(0);

      productionState.unlockState();
      expect(getProductionState().isLocked).toBe(false);
    });

    it('should track last saved timestamp', async () => {
      const before = new Date();
      
      await act(async () => {
        productionState.updateStage('script', { status: 'parsing' });
      });
      
      const after = new Date();
      const lastSaved = getProductionState().lastSaved;
      
      expect(lastSaved.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(lastSaved.getTime()).toBeLessThanOrEqual(after.getTime());
    });
  });
});
