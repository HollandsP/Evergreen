export interface ScriptTimestamp {
  time: string;
  seconds: number;
}

export interface OnScreenText {
  lines: string[];
}

export interface ScriptScene {
  id: string;
  timestamp: ScriptTimestamp;
  sceneType: string;
  description: string;
  visual: string;
  narration?: string;
  onScreenText?: OnScreenText;
  imagePrompt?: string;
}

export interface ParsedScript {
  title: string;
  logNumber: string;
  scenes: ScriptScene[];
  totalDuration: number;
}

export class ScriptParser {
  /**
   * Parse a script from The Descent format
   * Format: [timestamp - Scene Type | Description]
   */
  parseScript(content: string): ParsedScript {
    const lines = content.split('\n').map(line => line.trim());
    const scenes: ScriptScene[] = [];
    
    // Extract title and log number
    const titleMatch = lines[0]?.match(/SCRIPT:\s*LOG_(\d+)\s*[–-]\s*(.+)/);
    const logNumber = titleMatch?.[1] || '0000';
    const title = titleMatch?.[2] || 'Untitled';
    
    let currentScene: Partial<ScriptScene> | null = null;
    let sceneIndex = 0;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Skip empty lines
      if (!line) continue;
      
      // Enhanced scene detection patterns
      // Match scene timestamp and header: [timestamp - Scene Type | Description]
      const sceneMatch = line.match(/^\[(\d+:\d+)\s*[–-]\s*([^|]+)\s*\|\s*(.+)\]$/) ||
                        // Match standard screenplay format: INT./EXT. LOCATION - TIME
                        line.match(/^(INT\.|EXT\.)\s+(.+?)\s*-\s*(.+)$/i) ||
                        // Match simple scene markers: Scene 1, SCENE 1, etc.
                        line.match(/^SCENE\s+(\d+)[:\.]?\s*(.*)$/i) ||
                        // Match chapter/part markers
                        line.match(/^(CHAPTER|PART)\s+(\d+)[:\.]?\s*(.*)$/i);
      
      if (sceneMatch) {
        // Save previous scene if exists
        if (currentScene && currentScene.timestamp) {
          scenes.push(this.finalizeScene(currentScene, sceneIndex++));
        }
        
        // Start new scene with enhanced format detection
        let timestamp, sceneType, description;
        
        if (sceneMatch[0].startsWith('[')) {
          // Original LOG format: [timestamp - Scene Type | Description]
          [, timestamp, sceneType, description] = sceneMatch;
        } else if (sceneMatch[1] && (sceneMatch[1].startsWith('INT.') || sceneMatch[1].startsWith('EXT.'))) {
          // Screenplay format: INT./EXT. LOCATION - TIME
          timestamp = this.estimateTimestamp(sceneIndex);
          sceneType = sceneMatch[1];
          description = `${sceneMatch[2]} - ${sceneMatch[3]}`;
        } else if (sceneMatch[0].toLowerCase().startsWith('scene')) {
          // Simple scene format: Scene 1
          timestamp = this.estimateTimestamp(sceneIndex);
          sceneType = 'Scene';
          description = sceneMatch[2] || `Scene ${sceneMatch[1]}`;
        } else {
          // Chapter/Part format
          timestamp = this.estimateTimestamp(sceneIndex);
          sceneType = sceneMatch[1];
          description = sceneMatch[3] || `${sceneMatch[1]} ${sceneMatch[2]}`;
        }
        
        currentScene = {
          timestamp: typeof timestamp === 'string' ? this.parseTimestamp(timestamp) : timestamp,
          sceneType: sceneType.trim(),
          description: description.trim(),
          visual: '',
          narration: '',
          onScreenText: { lines: [] },
        };
      } else if (currentScene) {
        // Process content within current scene
        if (line.startsWith('Visual:')) {
          currentScene.visual = line.substring(7).trim();
        } else if (line.startsWith('Narration (Winston):') || line.startsWith('Narration:')) {
          // Start collecting narration
          const narrationStart = line.indexOf(':') + 1;
          currentScene.narration = line.substring(narrationStart).trim();
        } else if (line.startsWith('ON-SCREEN TEXT:') || line.startsWith('ON SCREEN:')) {
          // Start collecting on-screen text
          currentScene.onScreenText = { lines: [] };
        } else if (line.startsWith('Audio (Winston')) {
          // Handle audio lines as narration
          const audioStart = line.indexOf(':') + 1;
          currentScene.narration = line.substring(audioStart).trim();
        } else if (line.startsWith('INVITE TEXT:')) {
          // Handle invite text as on-screen text
          currentScene.onScreenText = { lines: [] };
        } else if (currentScene.onScreenText && !line.startsWith('Visual:') && !line.startsWith('[')) {
          // Collect on-screen text lines
          if (line && !line.match(/^(Visual:|Narration|Audio|On-screen:)/i)) {
            currentScene.onScreenText.lines.push(line);
          }
        } else if (currentScene.narration !== undefined && line.startsWith('"') && !line.startsWith('Visual:')) {
          // Continue narration if it spans multiple lines
          currentScene.narration += ' ' + line;
        }
      }
    }
    
    // Add the last scene
    if (currentScene && currentScene.timestamp) {
      scenes.push(this.finalizeScene(currentScene, sceneIndex));
    }
    
    // Calculate total duration
    const totalDuration = scenes.length > 0 
      ? scenes[scenes.length - 1].timestamp.seconds 
      : 0;
    
    return {
      title,
      logNumber,
      scenes,
      totalDuration,
    };
  }
  
  private parseTimestamp(timestamp: string): ScriptTimestamp {
    const [minutes, seconds] = timestamp.split(':').map(Number);
    return {
      time: timestamp,
      seconds: minutes * 60 + seconds,
    };
  }
  
  private estimateTimestamp(sceneIndex: number): ScriptTimestamp {
    // Estimate timestamp based on scene index (assume ~30 seconds per scene)
    const estimatedSeconds = sceneIndex * 30;
    const minutes = Math.floor(estimatedSeconds / 60);
    const seconds = estimatedSeconds % 60;
    const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    return {
      time: timeString,
      seconds: estimatedSeconds,
    };
  }
  
  private finalizeScene(scene: Partial<ScriptScene>, index: number): ScriptScene {
    // Clean up narration and on-screen text
    if (scene.narration) {
      scene.narration = this.cleanQuotes(scene.narration);
    }
    
    // Generate image prompt based on visual description
    scene.imagePrompt = this.generateImagePrompt(scene);
    
    return {
      id: `scene-${index}`,
      timestamp: scene.timestamp!,
      sceneType: scene.sceneType || '',
      description: scene.description || '',
      visual: scene.visual || '',
      narration: scene.narration,
      onScreenText: scene.onScreenText?.lines.length ? scene.onScreenText : undefined,
      imagePrompt: scene.imagePrompt,
    };
  }
  
  private cleanQuotes(text: string): string {
    // Remove surrounding quotes and normalize quotation marks
    return text
      .replace(/^[""]/, '')
      .replace(/[""]$/, '')
      .replace(/[""]/g, '"')
      .trim();
  }
  
  private generateImagePrompt(scene: Partial<ScriptScene>): string {
    const { visual, sceneType, description } = scene;
    
    // Base style for all images
    const baseStyle = 'cinematic, high contrast, moody lighting, 16:9 aspect ratio';
    
    // Scene-specific styles
    const sceneStyles: Record<string, string> = {
      'Cold Open': 'dark, mysterious, terminal green glow',
      'Terminal Boot-Up': 'retro computer terminal, green phosphor text, dark background',
      'Office Montage': 'modern office, futuristic tech, clean minimal design',
      'Rooftop Scene': 'dramatic sky, urban cityscape, ethereal lighting',
      'Outro': 'distorted, glitchy, unsettling',
    };
    
    // Find matching style
    let style = baseStyle;
    for (const [key, value] of Object.entries(sceneStyles)) {
      if (sceneType?.includes(key) || description?.includes(key)) {
        style = `${baseStyle}, ${value}`;
        break;
      }
    }
    
    // Construct prompt
    let prompt = visual || description || '';
    
    // Add specific details for terminal/screen scenes
    if (sceneType?.toLowerCase().includes('terminal') || visual?.toLowerCase().includes('terminal')) {
      prompt = `Computer terminal screen showing: ${prompt}, ${style}`;
    } else {
      prompt = `${prompt}, ${style}`;
    }
    
    return prompt;
  }
  
  /**
   * Export scenes to a format suitable for the production pipeline
   */
  exportForProduction(parsedScript: ParsedScript) {
    return {
      title: parsedScript.title,
      logNumber: parsedScript.logNumber,
      totalDuration: parsedScript.totalDuration,
      scenes: parsedScript.scenes.map(scene => ({
        id: scene.id,
        timestamp: scene.timestamp.seconds,
        narration: scene.narration || '',
        onScreenText: scene.onScreenText?.lines.join('\n') || '',
        imagePrompt: scene.imagePrompt || '',
        metadata: {
          sceneType: scene.sceneType,
          description: scene.description,
          visual: scene.visual,
        },
      })),
    };
  }
}

export const scriptParser = new ScriptParser();
