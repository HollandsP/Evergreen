import { NextApiRequest, NextApiResponse } from 'next';

interface ProcessCommandRequest {
  command: string;
  projectId: string;
  storyboardData?: any;
}

interface ProcessCommandResponse {
  success: boolean;
  message: string;
  operation?: {
    operation: string;
    parameters: any;
    confidence: number;
    explanation: string;
  };
  operation_id?: string;
  preview_url?: string;
  output_path?: string;
  error?: string;
  suggestions?: string[];
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ProcessCommandResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      message: 'Method not allowed'
    });
  }

  try {
    const { command, projectId, storyboardData }: ProcessCommandRequest = req.body;

    if (!command || !projectId) {
      return res.status(400).json({
        success: false,
        message: 'Command and project ID are required'
      });
    }

    // Forward request to Python AI Video Editor service
    const response = await fetch(`${process.env.PYTHON_API_URL || 'http://localhost:8000'}/api/v1/editor/process-command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command,
        project_id: projectId,
        storyboard_data: storyboardData
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Python service error:', response.status, errorText);
      
      return res.status(response.status).json({
        success: false,
        message: `AI Video Editor service error: ${response.statusText}`,
        error: `Backend service returned ${response.status}: ${errorText}`,
        suggestions: [
          'Check if the Python backend is running on port 8000',
          'Verify that MoviePy and OpenAI API key are properly configured',
          'Try a simpler command like "Cut the first 2 seconds"'
        ]
      });
    }

    const result = await response.json();
    
    return res.status(200).json({
      success: result.success || false,
      message: result.message || 'Command processed',
      operation: result.operation,
      operation_id: result.operation_id,
      preview_url: result.preview_url,
      output_path: result.output_path,
      error: result.error,
      suggestions: result.suggestions
    });

  } catch (error) {
    console.error('Error processing editor command:', error);
    
    return res.status(500).json({
      success: false,
      message: 'Failed to connect to AI Video Editor service',
      error: error instanceof Error ? error.message : 'Unknown error',
      suggestions: [
        'Ensure the Python backend is running: python -m uvicorn api.main:app --reload',
        'Check that OPENAI_API_KEY is configured in .env',
        'Verify MoviePy is installed: pip install moviepy',
        'Try restarting the backend service'
      ]
    });
  }
}

// Mock functions removed - now connecting directly to FastAPI backend
// The AI Video Editor service handles all command parsing with GPT-4
// and video operations with MoviePy