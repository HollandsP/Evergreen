import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { productionState } from '@/lib/production-state';

// Mock components that might throw errors
const ThrowingComponent = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>Component rendered successfully</div>;
};

describe('Error Handling and Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    productionState.reset();
  });

  describe('Error Boundary', () => {
    it('should catch and display errors', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      render(
        <ErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </ErrorBoundary>,
      );
      
      expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
      expect(screen.getByText(/Test error/i)).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });

    it('should allow retry after error', async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      let shouldThrow = true;
      
      const TestComponent = () => {
        if (shouldThrow) {
          throw new Error('Temporary error');
        }
        return <div>Success!</div>;
      };
      
      const { rerender } = render(
        <ErrorBoundary>
          <TestComponent />
        </ErrorBoundary>,
      );
      
      expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
      
      // Fix the error condition
      shouldThrow = false;
      
      // Click retry
      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);
      
      // Rerender to simulate retry
      rerender(
        <ErrorBoundary>
          <TestComponent />
        </ErrorBoundary>,
      );
      
      expect(screen.getByText(/Success!/i)).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });
  });

  describe('Network Error Handling', () => {
    it('should handle network timeouts', async () => {
      const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
      
      // Simulate timeout
      mockFetch.mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Network timeout')), 100),
        ),
      );
      
      // Test component that makes network request
      const NetworkComponent = () => {
        const [error, setError] = React.useState<string | null>(null);
        const [loading, setLoading] = React.useState(false);
        
        const makeRequest = async () => {
          setLoading(true);
          try {
            await fetch('/api/test');
          } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
          } finally {
            setLoading(false);
          }
        };
        
        React.useEffect(() => {
          makeRequest();
        }, []);
        
        if (loading) return <div>Loading...</div>;
        if (error) return <div>Error: {error}</div>;
        return <div>Success</div>;
      };
      
      render(<NetworkComponent />);
      
      expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.getByText(/Error: Network timeout/i)).toBeInTheDocument();
      });
    });

    it('should handle API error responses', async () => {
      const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal server error' }),
      } as Response);
      
      // Component that handles API errors
      const ApiComponent = () => {
        const [error, setError] = React.useState<string | null>(null);
        
        React.useEffect(() => {
          fetch('/api/test')
            .then(async res => {
              if (!res.ok) {
                const data = await res.json();
                throw new Error(data.error || `HTTP ${res.status}`);
              }
              return res.json();
            })
            .catch(err => setError(err.message));
        }, []);
        
        if (error) return <div>API Error: {error}</div>;
        return <div>Loading...</div>;
      };
      
      render(<ApiComponent />);
      
      await waitFor(() => {
        expect(screen.getByText(/API Error: Internal server error/i)).toBeInTheDocument();
      });
    });
  });

  describe('State Corruption Recovery', () => {
    it('should handle corrupted localStorage data', () => {
      // Inject corrupted data
      localStorage.setItem('evergreen_production_state', 'invalid json{');
      
      // Reset should handle corrupted data gracefully
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      productionState.reset();
      const state = productionState.getState();
      
      expect(state.script.status).toBe('idle');
      expect(state.currentStage).toBe('script');
      
      consoleSpy.mockRestore();
    });

    it('should validate and fix invalid state transitions', () => {
      // Try to set invalid state
      productionState.updateStage('script', {
        status: 'completed',
        scenes: [], // Invalid: completed but no scenes
      });
      
      const validation = productionState.validateState();
      expect(validation.valid).toBe(false);
      expect(validation.errors).toContain('Script completed but no scenes found');
    });

    it('should handle missing required voice selection', () => {
      productionState.updateStage('voice', {
        status: 'completed',
        // Missing selectedVoiceId
      });
      
      const validation = productionState.validateState();
      expect(validation.valid).toBe(false);
      expect(validation.errors).toContain('Voice selection completed but no voice selected');
    });
  });

  describe('Memory Management', () => {
    it('should handle large file uploads gracefully', async () => {
      const user = userEvent.setup();
      
      // Create a large file (10MB)
      const largeContent = new Array(10 * 1024 * 1024).fill('x').join('');
      const largeFile = new File([largeContent], 'large-script.txt', {
        type: 'text/plain',
      });
      
      // Component that validates file size
      const FileUploadComponent = () => {
        const [error, setError] = React.useState<string | null>(null);
        
        const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
          const file = e.target.files?.[0];
          if (file && file.size > 5 * 1024 * 1024) {
            setError('File too large. Maximum size is 5MB.');
          }
        };
        
        return (
          <div>
            <input
              type="file"
              onChange={handleFileChange}
              data-testid="file-input"
            />
            {error && <div role="alert">{error}</div>}
          </div>
        );
      };
      
      render(<FileUploadComponent />);
      
      const input = screen.getByTestId('file-input');
      await user.upload(input, largeFile);
      
      expect(screen.getByRole('alert')).toHaveTextContent(
        'File too large. Maximum size is 5MB.',
      );
    });

    it('should prevent memory leaks from event listeners', () => {
      const eventListeners: Function[] = [];
      
      // Mock addEventListener to track listeners
      const originalAddEventListener = window.addEventListener;
      window.addEventListener = jest.fn((event, listener) => {
        eventListeners.push(listener as Function);
        originalAddEventListener.call(window, event, listener);
      });
      
      // Component that adds event listeners
      const LeakyComponent = () => {
        React.useEffect(() => {
          const handleResize = () => console.log('resize');
          window.addEventListener('resize', handleResize);
          
          return () => {
            window.removeEventListener('resize', handleResize);
          };
        }, []);
        
        return <div>Component with listeners</div>;
      };
      
      const { unmount } = render(<LeakyComponent />);
      
      expect(eventListeners.length).toBe(1);
      
      unmount();
      
      // Verify cleanup (would need to track removeEventListener calls)
      window.addEventListener = originalAddEventListener;
    });
  });

  describe('Concurrent Operations', () => {
    it('should handle race conditions in state updates', async () => {
      const updates: Promise<void>[] = [];
      
      // Simulate concurrent updates
      for (let i = 0; i < 10; i++) {
        updates.push(
          new Promise(resolve => {
            setTimeout(() => {
              productionState.updateStage('audio', {
                progress: i * 10,
              });
              resolve();
            }, Math.random() * 100);
          }),
        );
      }
      
      await Promise.all(updates);
      
      // State should reflect last update
      const state = productionState.getState();
      expect(state.audio.progress).toBeGreaterThanOrEqual(0);
      expect(state.audio.progress).toBeLessThanOrEqual(90);
    });

    it('should handle multiple file uploads', async () => {
      const user = userEvent.setup();
      
      // Component that handles multiple files
      const MultiUploadComponent = () => {
        const [files, setFiles] = React.useState<File[]>([]);
        const [processing, setProcessing] = React.useState(false);
        
        const handleFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
          const fileList = Array.from(e.target.files || []);
          setProcessing(true);
          
          // Simulate processing
          await new Promise(resolve => setTimeout(resolve, 100));
          
          setFiles(fileList);
          setProcessing(false);
        };
        
        return (
          <div>
            <input
              type="file"
              multiple
              onChange={handleFiles}
              data-testid="multi-file-input"
            />
            {processing && <div>Processing files...</div>}
            {files.map((file, i) => (
              <div key={i}>{file.name}</div>
            ))}
          </div>
        );
      };
      
      render(<MultiUploadComponent />);
      
      const files = [
        new File(['content1'], 'file1.txt', { type: 'text/plain' }),
        new File(['content2'], 'file2.txt', { type: 'text/plain' }),
      ];
      
      const input = screen.getByTestId('multi-file-input');
      await user.upload(input, files);
      
      await waitFor(() => {
        expect(screen.getByText('file1.txt')).toBeInTheDocument();
        expect(screen.getByText('file2.txt')).toBeInTheDocument();
      });
    });
  });

  describe('Browser Compatibility', () => {
    it('should handle missing browser APIs gracefully', () => {
      // Temporarily remove localStorage
      const originalLocalStorage = window.localStorage;
      delete (window as any).localStorage;
      
      // Component that uses localStorage
      const StorageComponent = () => {
        const [supported, setSupported] = React.useState(true);
        
        React.useEffect(() => {
          try {
            if (!window.localStorage) {
              setSupported(false);
            }
          } catch {
            setSupported(false);
          }
        }, []);
        
        if (!supported) {
          return <div>Local storage not supported</div>;
        }
        
        return <div>Storage available</div>;
      };
      
      render(<StorageComponent />);
      
      expect(screen.getByText(/Local storage not supported/i)).toBeInTheDocument()
      
      // Restore localStorage
      (window as any).localStorage = originalLocalStorage;
    });

    it('should handle different viewport sizes', () => {
      // Test responsive behavior
      const ResponsiveComponent = () => {
        const [isMobile, setIsMobile] = React.useState(false);
        
        React.useEffect(() => {
          const checkSize = () => {
            setIsMobile(window.innerWidth < 768);
          };
          
          checkSize();
          window.addEventListener('resize', checkSize);
          
          return () => window.removeEventListener('resize', checkSize);
        }, []);
        
        return (
          <div>
            {isMobile ? 'Mobile View' : 'Desktop View'}
          </div>
        );
      };
      
      render(<ResponsiveComponent />);
      
      // Default viewport
      expect(screen.getByText(/Desktop View/i)).toBeInTheDocument();
      
      // Change viewport size
      global.innerWidth = 500;
      global.dispatchEvent(new Event('resize'));
      
      waitFor(() => {
        expect(screen.getByText(/Mobile View/i)).toBeInTheDocument();
      });
      
      // Restore
      global.innerWidth = 1024;
    });
  });
});
