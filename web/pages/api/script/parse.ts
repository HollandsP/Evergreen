import type { NextApiRequest, NextApiResponse } from 'next';
import { ScriptScene } from '@/types';
import { updateProductionStage } from '@/lib/production-state';
import { v4 as uuidv4 } from 'uuid';

interface ParsedScript {
  scenes: ScriptScene[];
  totalDuration: number;
  characterCount: number;
  metadata: {
    title?: string;
    author?: string;
    date?: string;
  };
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version',
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
    return;
  }

  try {
    const { content, fileName } = req.body;

    if (!content) {
      res.status(400).json({ error: 'No content provided' });
      return;
    }

    // Update state to parsing
    updateProductionStage('script', {
      status: 'parsing',
      parseProgress: 0,
      fileName,
    });

    // Send WebSocket notification
    if (global.io) {
      global.io.emit('script:parseStart', {
        fileName,
        timestamp: new Date().toISOString(),
      });
    }

    // Parse the script content
    const parsedScript = await parseScriptContent(content);

    // Update progress periodically during parsing
    updateProductionStage('script', {
      parseProgress: 50,
    });

    // Generate image prompts for each scene
    const scenesWithPrompts = await generateImagePrompts(parsedScript.scenes);

    updateProductionStage('script', {
      parseProgress: 90,
    });

    // Update state with parsed scenes
    updateProductionStage('script', {
      status: 'completed',
      scenes: scenesWithPrompts,
      parseProgress: 100,
    });

    // Send WebSocket notification
    if (global.io) {
      global.io.emit('script:parseComplete', {
        sceneCount: scenesWithPrompts.length,
        totalDuration: parsedScript.totalDuration,
        timestamp: new Date().toISOString(),
      });
    }

    res.status(200).json({
      success: true,
      scenes: scenesWithPrompts,
      totalDuration: parsedScript.totalDuration,
      characterCount: parsedScript.characterCount,
      metadata: parsedScript.metadata,
    });
  } catch (error) {
    console.error('Script parsing error:', error);
    
    updateProductionStage('script', {
      status: 'error',
      error: error instanceof Error ? error.message : 'Failed to parse script',
    });

    if (global.io) {
      global.io.emit('script:parseError', {
        error: error instanceof Error ? error.message : 'Failed to parse script',
        timestamp: new Date().toISOString(),
      });
    }

    res.status(500).json({
      error: 'Failed to parse script',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

async function parseScriptContent(content: string): Promise<ParsedScript> {
  const lines = content.split('\n');
  const scenes: ScriptScene[] = [];
  let currentTimestamp = 0;
  let totalCharacterCount = 0;
  const metadata: ParsedScript['metadata'] = {};

  // Extract metadata from the beginning of the script
  for (let i = 0; i < Math.min(10, lines.length); i++) {
    const line = lines[i].trim();
    if (line.startsWith('# ')) {
      metadata.title = line.substring(2);
    } else if (line.startsWith('Author:')) {
      metadata.author = line.substring(7).trim();
    } else if (line.startsWith('Date:')) {
      metadata.date = line.substring(5).trim();
    }
  }

  // Parse scenes
  let currentScene: Partial<ScriptScene> | null = null;
  let sceneLines: string[] = [];

  for (const line of lines) {
    const trimmedLine = line.trim();

    // Scene marker (e.g., "## Scene 1" or "[Scene 1]")
    if (trimmedLine.match(/^(##|\[)\s*Scene\s+\d+/i)) {
      if (currentScene && sceneLines.length > 0) {
        // Process previous scene
        const processedScene = processScene(currentScene, sceneLines, currentTimestamp);
        scenes.push(processedScene);
        currentTimestamp += estimateDuration(processedScene.narration);
        totalCharacterCount += processedScene.narration.length;
      }

      // Start new scene
      currentScene = {
        id: uuidv4(),
        timestamp: currentTimestamp,
        narration: '',
        onScreenText: '',
        imagePrompt: '',
        metadata: {
          sceneType: 'standard',
          description: '',
          visual: '',
        },
      };
      sceneLines = [];
    } else if (currentScene) {
      sceneLines.push(line);
    }
  }

  // Process last scene
  if (currentScene && sceneLines.length > 0) {
    const processedScene = processScene(currentScene, sceneLines, currentTimestamp);
    scenes.push(processedScene);
    currentTimestamp += estimateDuration(processedScene.narration);
    totalCharacterCount += processedScene.narration.length;
  }

  // If no scenes were found, treat the entire content as one scene
  if (scenes.length === 0) {
    const narration = lines.filter(line => line.trim()).join(' ');
    scenes.push({
      id: uuidv4(),
      timestamp: 0,
      narration,
      onScreenText: extractOnScreenText(narration),
      imagePrompt: '',
      metadata: {
        sceneType: 'standard',
        description: narration.substring(0, 100) + '...',
        visual: '',
      },
    });
    totalCharacterCount = narration.length;
    currentTimestamp = estimateDuration(narration);
  }

  return {
    scenes,
    totalDuration: currentTimestamp,
    characterCount: totalCharacterCount,
    metadata,
  };
}

function processScene(
  scene: Partial<ScriptScene>,
  lines: string[],
  timestamp: number,
): ScriptScene {
  const content = lines.join('\n');
  
  // Extract narration (main text)
  const narrationMatch = content.match(/(?:Narration:|Winston:)?\s*(.+?)(?:\n\n|\[|$)/s);
  const narration = narrationMatch ? narrationMatch[1].trim() : content.trim();

  // Extract on-screen text (text in brackets or after "Text:")
  const onScreenText = extractOnScreenText(content);

  // Extract visual description
  const visualMatch = content.match(/(?:Visual:|Description:)\s*(.+?)(?:\n|$)/i);
  const visual = visualMatch ? visualMatch[1].trim() : '';

  // Determine scene type
  const sceneType = determineSceneType(content);

  return {
    id: scene.id || uuidv4(),
    timestamp,
    narration,
    onScreenText,
    imagePrompt: '', // Will be generated later
    metadata: {
      sceneType,
      description: narration.substring(0, 100) + (narration.length > 100 ? '...' : ''),
      visual,
    },
  };
}

function extractOnScreenText(content: string): string {
  const textMatches = content.match(/\[([^\]]+)\]/g);
  if (textMatches) {
    return textMatches.map(match => match.slice(1, -1)).join(' ');
  }

  const textMatch = content.match(/(?:Text:|On-screen:)\s*(.+?)(?:\n|$)/i);
  return textMatch ? textMatch[1].trim() : '';
}

function determineSceneType(content: string): string {
  const lowerContent = content.toLowerCase();
  
  if (lowerContent.includes('title') || lowerContent.includes('opening')) {
    return 'title';
  } else if (lowerContent.includes('ending') || lowerContent.includes('credits')) {
    return 'ending';
  } else if (lowerContent.includes('transition')) {
    return 'transition';
  } else if (lowerContent.includes('montage')) {
    return 'montage';
  } else if (lowerContent.includes('flashback')) {
    return 'flashback';
  }
  
  return 'standard';
}

function estimateDuration(text: string): number {
  // Estimate ~150 words per minute for narration
  const words = text.split(/\s+/).length;
  const minutes = words / 150;
  return Math.max(2, Math.round(minutes * 60)); // Minimum 2 seconds per scene
}

async function generateImagePrompts(scenes: ScriptScene[]): Promise<ScriptScene[]> {
  // In production, this could call an AI service to generate better prompts
  // For now, we'll create prompts based on the content
  
  return scenes.map(scene => {
    let prompt = '';
    
    // Base the prompt on scene type
    switch (scene.metadata.sceneType) {
      case 'title':
        prompt = 'Cinematic title card with dramatic lighting, text overlay space, professional movie poster style';
        break;
      case 'ending':
        prompt = 'Elegant ending scene with soft lighting, peaceful atmosphere, cinematic closure';
        break;
      case 'transition':
        prompt = 'Abstract transitional visual, flowing shapes, cinematic transition effect';
        break;
      default:
        // Use visual description if available
        if (scene.metadata.visual) {
          prompt = `Cinematic scene: ${scene.metadata.visual}, dramatic lighting, high quality, detailed`;
        } else {
          // Generate from narration
          const keywords = extractKeywords(scene.narration);
          prompt = `Cinematic scene depicting ${keywords.join(', ')}, dramatic lighting, professional film quality`;
        }
    }
    
    // Add on-screen text indication if present
    if (scene.onScreenText) {
      prompt += `, space for text overlay "${scene.onScreenText.substring(0, 50)}"`;
    }
    
    return {
      ...scene,
      imagePrompt: prompt,
    };
  });
}

function extractKeywords(text: string): string[] {
  // Simple keyword extraction - in production, use NLP
  const commonWords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did']);
  
  const words = text.toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter(word => word.length > 3 && !commonWords.has(word));
  
  // Get unique words and take top 5
  const uniqueWords = [...new Set(words)];
  return uniqueWords.slice(0, 5);
}
