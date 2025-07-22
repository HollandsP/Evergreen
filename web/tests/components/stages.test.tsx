import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ScriptProcessor } from '@/components/stages/ScriptProcessor'
import { AudioGenerator } from '@/components/stages/AudioGenerator'
import { ImageGenerator } from '@/components/stages/ImageGenerator'
import { VideoGenerator } from '@/components/stages/VideoGenerator'
import { FinalAssembly } from '@/components/stages/FinalAssembly'
import { productionState } from '@/lib/production-state'

// Mock fetch
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

// Mock router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/production/script',
  }),
}))

describe('Stage Components', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    productionState.reset()
  })

  describe('ScriptProcessor', () => {
    it('should handle file upload and parsing', async () => {
      const user = userEvent.setup()
      
      render(<ScriptProcessor />)
      
      // Check initial state
      expect(screen.getByText(/Upload Script/i)).toBeInTheDocument()
      expect(screen.getByText(/Drop your script file here or click to browse/i)).toBeInTheDocument()
      
      // Create a test file
      const file = new File(['Test script content'], 'test-script.txt', {
        type: 'text/plain',
      })
      
      // Mock successful API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          scenes: [
            {
              id: 'scene_1',
              timestamp: 0,
              narration: 'Test narration',
              onScreenText: '',
              imagePrompt: 'Test visual',
              metadata: {
                sceneType: 'establishing',
                description: 'Test scene',
                visual: 'Test visual description',
              },
            },
          ],
          totalDuration: 10,
        }),
      } as Response)
      
      // Upload file
      const input = screen.getByLabelText(/upload script/i)
      await user.upload(input, file)
      
      // Wait for upload and parsing
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/script/upload'),
          expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData),
          })
        )
      })
      
      // Check if scenes are displayed
      await waitFor(() => {
        expect(screen.getByText(/Scene 1/i)).toBeInTheDocument()
        expect(screen.getByText(/Test narration/i)).toBeInTheDocument()
      })
    })

    it('should display parsing progress', async () => {
      render(<ScriptProcessor />)
      
      // Update state to show parsing progress
      productionState.updateStage('script', {
        status: 'parsing',
        parseProgress: 50,
        fileName: 'test-script.txt',
      })
      
      await waitFor(() => {
        expect(screen.getByText(/Parsing script/i)).toBeInTheDocument()
        expect(screen.getByText(/50%/)).toBeInTheDocument()
      })
    })

    it('should handle parsing errors', async () => {
      render(<ScriptProcessor />)
      
      productionState.updateStage('script', {
        status: 'error',
        error: 'Invalid script format',
      })
      
      await waitFor(() => {
        expect(screen.getByText(/Invalid script format/i)).toBeInTheDocument()
      })
    })

    it('should allow scene editing', async () => {
      const user = userEvent.setup()
      
      productionState.updateStage('script', {
        status: 'completed',
        scenes: [
          {
            id: 'scene_1',
            timestamp: 0,
            narration: 'Original narration',
            onScreenText: '',
            imagePrompt: 'Original prompt',
            metadata: {
              sceneType: 'establishing',
              description: 'Test scene',
              visual: 'Test visual',
            },
          },
        ],
      })
      
      render(<ScriptProcessor />)
      
      // Find and click edit button
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)
      
      // Edit narration
      const narrationInput = screen.getByLabelText(/narration/i)
      await user.clear(narrationInput)
      await user.type(narrationInput, 'Updated narration')
      
      // Save changes
      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)
      
      // Verify changes
      expect(screen.getByText(/Updated narration/i)).toBeInTheDocument()
    })
  })

  describe('AudioGenerator', () => {
    beforeEach(() => {
      // Set up required state
      productionState.updateStage('script', {
        status: 'completed',
        scenes: [
          {
            id: 'scene_1',
            narration: 'Test narration 1',
            timestamp: 0,
            onScreenText: '',
            imagePrompt: '',
            metadata: {} as any,
          },
          {
            id: 'scene_2',
            narration: 'Test narration 2',
            timestamp: 5,
            onScreenText: '',
            imagePrompt: '',
            metadata: {} as any,
          },
        ],
      })
      
      productionState.updateStage('voice', {
        status: 'completed',
        selectedVoiceId: 'test_voice',
        selectedVoiceName: 'Test Voice',
      })
    })

    it('should display scenes for audio generation', () => {
      render(<AudioGenerator />)
      
      expect(screen.getByText(/Test narration 1/i)).toBeInTheDocument()
      expect(screen.getByText(/Test narration 2/i)).toBeInTheDocument()
    })

    it('should handle batch audio generation', async () => {
      const user = userEvent.setup()
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          results: [
            { sceneId: 'scene_1', url: '/audio/1.mp3', duration: 3 },
            { sceneId: 'scene_2', url: '/audio/2.mp3', duration: 4 },
          ],
        }),
      } as Response)
      
      render(<AudioGenerator />)
      
      const generateButton = screen.getByRole('button', { name: /generate all audio/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/audio/batch'),
          expect.objectContaining({
            method: 'POST',
          })
        )
      })
    })

    it('should show progress during generation', async () => {
      render(<AudioGenerator />)
      
      productionState.updateStage('audio', {
        status: 'generating',
        progress: 75,
      })
      
      await waitFor(() => {
        expect(screen.getByText(/75%/)).toBeInTheDocument()
        expect(screen.getByText(/Generating audio/i)).toBeInTheDocument()
      })
    })

    it('should allow individual scene regeneration', async () => {
      const user = userEvent.setup()
      
      productionState.updateStage('audio', {
        status: 'completed',
        generatedAudio: [
          { sceneId: 'scene_1', url: '/audio/1.mp3', duration: 3, status: 'completed' },
          { sceneId: 'scene_2', url: '', duration: 0, status: 'error', error: 'Failed' },
        ],
      })
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          sceneId: 'scene_2',
          url: '/audio/2.mp3',
          duration: 4,
        }),
      } as Response)
      
      render(<AudioGenerator />)
      
      // Find and click regenerate button for failed scene
      const regenerateButtons = screen.getAllByRole('button', { name: /regenerate/i })
      await user.click(regenerateButtons[0])
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/audio/generate'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('scene_2'),
          })
        )
      })
    })
  })

  describe('ImageGenerator', () => {
    beforeEach(() => {
      productionState.updateStage('script', {
        status: 'completed',
        scenes: [
          {
            id: 'scene_1',
            imagePrompt: 'Mountain landscape',
            narration: '',
            timestamp: 0,
            onScreenText: '',
            metadata: {} as any,
          },
        ],
      })
    })

    it('should display image generation options', () => {
      render(<ImageGenerator />)
      
      expect(screen.getByText(/DALL-E 3/i)).toBeInTheDocument()
      expect(screen.getByText(/Upload Images/i)).toBeInTheDocument()
    })

    it('should handle DALL-E 3 generation', async () => {
      const user = userEvent.setup()
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          results: [
            {
              sceneId: 'scene_1',
              url: '/images/1.jpg',
              provider: 'dalle3',
              cost: 0.04,
            },
          ],
        }),
      } as Response)
      
      render(<ImageGenerator />)
      
      // Select DALL-E 3
      const dalle3Tab = screen.getByRole('tab', { name: /DALL-E 3/i })
      await user.click(dalle3Tab)
      
      // Generate images
      const generateButton = screen.getByRole('button', { name: /generate all images/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/images/batch'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('dalle3'),
          })
        )
      })
    })

    it('should handle image upload', async () => {
      const user = userEvent.setup()
      
      render(<ImageGenerator />)
      
      // Switch to upload tab
      const uploadTab = screen.getByRole('tab', { name: /upload images/i })
      await user.click(uploadTab)
      
      // Create test image file
      const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
      
      const input = screen.getByLabelText(/upload image/i)
      await user.upload(input, file)
      
      // Verify file is processed
      await waitFor(() => {
        expect(screen.getByText(/test.jpg/i)).toBeInTheDocument()
      })
    })

    it('should preview generated images', async () => {
      productionState.updateStage('images', {
        status: 'completed',
        generatedImages: [
          {
            sceneId: 'scene_1',
            url: '/images/1.jpg',
            prompt: 'Mountain landscape',
            provider: 'dalle3',
            status: 'completed',
          },
        ],
      })
      
      render(<ImageGenerator />)
      
      // Check if image is displayed
      const image = screen.getByAltText(/Scene 1/i)
      expect(image).toHaveAttribute('src', '/images/1.jpg')
    })
  })

  describe('VideoGenerator', () => {
    beforeEach(() => {
      productionState.updateStage('images', {
        status: 'completed',
        generatedImages: [
          {
            sceneId: 'scene_1',
            url: '/images/1.jpg',
            prompt: 'Test prompt',
            provider: 'dalle3',
            status: 'completed',
          },
        ],
      })
      
      productionState.updateStage('audio', {
        status: 'completed',
        generatedAudio: [
          {
            sceneId: 'scene_1',
            url: '/audio/1.mp3',
            duration: 5,
            status: 'completed',
          },
        ],
      })
    })

    it('should display video generation providers', () => {
      render(<VideoGenerator />)
      
      expect(screen.getByText(/Runway Gen-2/i)).toBeInTheDocument()
      expect(screen.getByText(/Stable Video Diffusion/i)).toBeInTheDocument()
      expect(screen.getByText(/ModelScope/i)).toBeInTheDocument()
    })

    it('should handle video generation with audio sync', async () => {
      const user = userEvent.setup()
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          results: [
            {
              sceneId: 'scene_1',
              videoUrl: '/videos/1.mp4',
              duration: 5,
            },
          ],
        }),
      } as Response)
      
      render(<VideoGenerator />)
      
      const generateButton = screen.getByRole('button', { name: /generate all videos/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/videos/batch'),
          expect.objectContaining({
            method: 'POST',
          })
        )
      })
    })

    it('should show audio sync timeline', () => {
      productionState.updateStage('video', {
        status: 'completed',
        scenes: [
          {
            sceneId: 'scene_1',
            status: 'completed',
            videoUrl: '/videos/1.mp4',
            imageUrl: '/images/1.jpg',
            duration: 5,
          },
        ],
      })
      
      render(<VideoGenerator />)
      
      expect(screen.getByText(/Audio Sync Timeline/i)).toBeInTheDocument()
      expect(screen.getByText(/5s/i)).toBeInTheDocument()
    })
  })

  describe('FinalAssembly', () => {
    beforeEach(() => {
      productionState.updateStage('video', {
        status: 'completed',
        scenes: [
          {
            sceneId: 'scene_1',
            status: 'completed',
            videoUrl: '/videos/1.mp4',
            imageUrl: '/images/1.jpg',
            duration: 5,
          },
          {
            sceneId: 'scene_2',
            status: 'completed',
            videoUrl: '/videos/2.mp4',
            imageUrl: '/images/2.jpg',
            duration: 4,
          },
        ],
      })
    })

    it('should display timeline editor', () => {
      render(<FinalAssembly />)
      
      expect(screen.getByText(/Timeline Editor/i)).toBeInTheDocument()
      expect(screen.getByText(/Total Duration: 9s/i)).toBeInTheDocument()
    })

    it('should allow export format selection', async () => {
      const user = userEvent.setup()
      
      render(<FinalAssembly />)
      
      // Find format selector
      const formatSelect = screen.getByLabelText(/export format/i)
      await user.selectOptions(formatSelect, 'webm')
      
      expect(formatSelect).toHaveValue('webm')
    })

    it('should handle final export', async () => {
      const user = userEvent.setup()
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          videoUrl: '/final/output.mp4',
          downloadUrl: '/download/output.mp4',
        }),
      } as Response)
      
      render(<FinalAssembly />)
      
      const exportButton = screen.getByRole('button', { name: /export final video/i })
      await user.click(exportButton)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/assembly/export'),
          expect.objectContaining({
            method: 'POST',
          })
        )
      })
      
      // Check for download link
      await waitFor(() => {
        expect(screen.getByRole('link', { name: /download/i })).toHaveAttribute(
          'href',
          '/download/output.mp4'
        )
      })
    })

    it('should show export progress', async () => {
      render(<FinalAssembly />)
      
      productionState.updateStage('assembly', {
        status: 'exporting',
        progress: 60,
      })
      
      await waitFor(() => {
        expect(screen.getByText(/60%/)).toBeInTheDocument()
        expect(screen.getByText(/Exporting video/i)).toBeInTheDocument()
      })
    })
  })

  describe('Stage Navigation', () => {
    it('should prevent navigation to locked stages', () => {
      productionState.updateStage('script', { status: 'idle' })
      
      render(<AudioGenerator />)
      
      expect(screen.getByText(/Complete script processing first/i)).toBeInTheDocument()
    })

    it('should show completion status for each stage', () => {
      productionState.updateStage('script', { status: 'completed' })
      productionState.updateStage('voice', { status: 'completed' })
      productionState.updateStage('audio', { status: 'generating', progress: 50 })
      
      // Would need to render a navigation component here
      // This is a placeholder for the navigation test
    })
  })
})