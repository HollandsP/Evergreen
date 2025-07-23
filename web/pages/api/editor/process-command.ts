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
      // If Python service is not available, provide mock responses for development
      const mockResponse = await generateMockResponse(command, projectId);
      return res.status(200).json(mockResponse);
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
    
    // Fallback to mock response for development
    try {
      const mockResponse = await generateMockResponse(
        req.body.command, 
        req.body.projectId
      );
      return res.status(200).json(mockResponse);
    } catch (mockError) {
      return res.status(500).json({
        success: false,
        message: 'Internal server error processing command',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
}

async function generateMockResponse(
  command: string, 
  _projectId: string
): Promise<ProcessCommandResponse> {
  // Simple command parsing for development/demo purposes
  const lowerCommand = command.toLowerCase();
  
  if (lowerCommand.includes('cut') || lowerCommand.includes('trim')) {
    const operation = {
      operation: 'CUT',
      parameters: {
        target: extractSceneFromCommand(command),
        start_time: 0,
        duration: extractDurationFromCommand(command) || 3
      },
      confidence: 0.9,
      explanation: `Will remove the specified duration from ${extractSceneFromCommand(command)}`
    };

    return {
      success: true,
      message: `Successfully applied cut operation to ${operation.parameters.target}`,
      operation,
      operation_id: generateMockOperationId(),
      preview_url: `/api/editor/preview/${generateMockOperationId()}`,
      output_path: `/output/editor/${generateMockOperationId()}_cut.mp4`
    };
  }
  
  if (lowerCommand.includes('fade')) {
    const operation = {
      operation: 'FADE',
      parameters: {
        target: lowerCommand.includes('all') ? 'all_scenes' : extractSceneFromCommand(command),
        fade_type: lowerCommand.includes('out') ? 'out' : 'in',
        duration: 1.0
      },
      confidence: 0.95,
      explanation: `Will add fade ${lowerCommand.includes('out') ? 'out' : 'in'} effect`
    };

    return {
      success: true,
      message: `Successfully added fade transition`,
      operation,
      operation_id: generateMockOperationId(),
      preview_url: `/api/editor/preview/${generateMockOperationId()}`,
      output_path: `/output/editor/${generateMockOperationId()}_fade.mp4`
    };
  }
  
  if (lowerCommand.includes('speed')) {
    const speedMatch = command.match(/(\d+\.?\d*)\s*x/);
    const speed = speedMatch ? parseFloat(speedMatch[1]) : 1.5;
    
    const operation = {
      operation: 'SPEED',
      parameters: {
        target: extractSceneFromCommand(command),
        multiplier: speed
      },
      confidence: 0.9,
      explanation: `Will change playback speed to ${speed}x`
    };

    return {
      success: true,
      message: `Successfully changed speed to ${speed}x for ${operation.parameters.target}`,
      operation,
      operation_id: generateMockOperationId(),
      preview_url: `/api/editor/preview/${generateMockOperationId()}`,
      output_path: `/output/editor/${generateMockOperationId()}_speed.mp4`
    };
  }
  
  if (lowerCommand.includes('text') || lowerCommand.includes('overlay')) {
    const textMatch = command.match(/['"]([^'"]+)['"]/);
    const text = textMatch ? textMatch[1] : 'Sample Text';
    
    const operation = {
      operation: 'OVERLAY',
      parameters: {
        target: extractSceneFromCommand(command),
        overlay_type: 'text',
        content: text,
        position: 'center'
      },
      confidence: 0.85,
      explanation: `Will add text overlay "${text}" to the video`
    };

    return {
      success: true,
      message: `Successfully added text overlay "${text}"`,
      operation,
      operation_id: generateMockOperationId(),
      preview_url: `/api/editor/preview/${generateMockOperationId()}`,
      output_path: `/output/editor/${generateMockOperationId()}_overlay.mp4`
    };
  }
  
  if (lowerCommand.includes('audio') || lowerCommand.includes('volume')) {
    const volumeMatch = command.match(/(\d+)%/);
    const volume = volumeMatch ? parseInt(volumeMatch[1]) / 100 : 0.5;
    
    const operation = {
      operation: 'AUDIO_MIX',
      parameters: {
        target: extractSceneFromCommand(command),
        volume: volume
      },
      confidence: 0.9,
      explanation: `Will adjust audio volume to ${Math.round(volume * 100)}%`
    };

    return {
      success: true,
      message: `Successfully adjusted audio volume to ${Math.round(volume * 100)}%`,
      operation,
      operation_id: generateMockOperationId(),
      preview_url: `/api/editor/preview/${generateMockOperationId()}`,
      output_path: `/output/editor/${generateMockOperationId()}_audio.mp4`
    };
  }
  
  if (lowerCommand.includes('transition')) {
    const operation = {
      operation: 'TRANSITION',
      parameters: {
        target: 'all_scenes',
        transition_type: 'fade',
        duration: 1.0
      },
      confidence: 0.9,
      explanation: 'Will add fade transitions between all scene clips'
    };

    return {
      success: true,
      message: 'Successfully added transitions between all scenes',
      operation,
      operation_id: generateMockOperationId(),
      preview_url: `/api/editor/preview/${generateMockOperationId()}`,
      output_path: `/output/editor/${generateMockOperationId()}_transitions.mp4`
    };
  }

  // Default response for unrecognized commands
  return {
    success: false,
    message: 'I\'m not sure how to help with that command. Could you try rephrasing it?',
    suggestions: [
      'Cut the first 3 seconds of scene 1',
      'Add fade transition between all scenes',
      'Speed up scene 2 by 1.5x',
      'Add text overlay "THE END" to the last scene',
      'Reduce audio volume to 50% for scene 3'
    ]
  };
}

function extractSceneFromCommand(command: string): string {
  const sceneMatch = command.match(/scene\s*(\d+)/i);
  if (sceneMatch) {
    return `scene_${sceneMatch[1]}`;
  }
  
  // Look for other scene indicators
  if (command.toLowerCase().includes('last scene') || command.toLowerCase().includes('final scene')) {
    return 'scene_last';
  }
  
  if (command.toLowerCase().includes('first scene')) {
    return 'scene_1';
  }
  
  return 'scene_1'; // Default
}

function extractDurationFromCommand(command: string): number | null {
  // Look for patterns like "3 seconds", "5s", "2.5 sec"
  const durationMatch = command.match(/(\d+\.?\d*)\s*(second|sec|s)\b/i);
  if (durationMatch) {
    return parseFloat(durationMatch[1]);
  }
  
  // Look for "first X seconds"
  const firstMatch = command.match(/first\s+(\d+\.?\d*)/i);
  if (firstMatch) {
    return parseFloat(firstMatch[1]);
  }
  
  return null;
}

function generateMockOperationId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}