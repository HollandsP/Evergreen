import React, { useState, useRef, useCallback } from 'react';
import { 
  ScissorsIcon,
  PlusIcon,
  TrashIcon,
  ArrowsUpDownIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { ParsedScript, ScriptScene, scriptParser } from '@/lib/script-parser';
import { cn } from '@/lib/utils';

interface SceneDividerProps {
  parsedScript: ParsedScript;
  onScenesUpdated: (updatedScript: ParsedScript) => void;
}

interface DivisionPoint {
  id: string;
  position: number; // Character position in the full script
  sceneIndex: number;
  isNew?: boolean;
}

export const SceneDivider: React.FC<SceneDividerProps> = ({ parsedScript, onScenesUpdated }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [divisionPoints, setDivisionPoints] = useState<DivisionPoint[]>([]);
  const [selectedScript, setSelectedScript] = useState<string>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize editing mode
  const startEditing = useCallback(() => {
    // Reconstruct the original script content for editing
    const reconstructedScript = reconstructScriptContent(parsedScript);
    setSelectedScript(reconstructedScript);
    
    // Initialize division points from current scenes
    let position = 0;
    const points: DivisionPoint[] = [];
    
    parsedScript.scenes.forEach((scene, index) => {
      if (index > 0) { // Skip first scene
        points.push({
          id: `existing-${index}`,
          position,
          sceneIndex: index,
          isNew: false
        });
      }
      
      // Estimate position based on scene content length
      const sceneContent = `[${scene.timestamp.time} - ${scene.sceneType} | ${scene.description}]\n${scene.visual}\n${scene.narration || ''}\n${scene.onScreenText?.lines.join('\n') || ''}\n\n`;
      position += sceneContent.length;
    });
    
    setDivisionPoints(points);
    setIsEditing(true);
  }, [parsedScript]);

  // Add new division point
  const addDivisionPoint = useCallback((position: number) => {
    const newPoint: DivisionPoint = {
      id: `new-${Date.now()}`,
      position,
      sceneIndex: findSceneIndexAtPosition(position),
      isNew: true
    };
    
    setDivisionPoints(prev => [...prev, newPoint].sort((a, b) => a.position - b.position));
  }, []);

  // Remove division point
  const removeDivisionPoint = useCallback((pointId: string) => {
    setDivisionPoints(prev => prev.filter(point => point.id !== pointId));
  }, []);

  // Apply changes and re-parse script
  const applyChanges = useCallback(() => {
    try {
      // Apply division points to create new scene boundaries
      const newScriptContent = applyDivisionsToScript(selectedScript, divisionPoints);
      
      // Re-parse the modified script
      const newParsedScript = scriptParser.parseScript(newScriptContent);
      
      // Update the parent component
      onScenesUpdated(newParsedScript);
      
      setIsEditing(false);
      setDivisionPoints([]);
    } catch (error) {
      console.error('Error applying scene divisions:', error);
    }
  }, [selectedScript, divisionPoints, onScenesUpdated]);

  // Cancel editing
  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setDivisionPoints([]);
    setSelectedScript('');
  }, []);

  // Handle text selection for adding division points
  const handleTextSelection = useCallback(() => {
    if (!textareaRef.current) return;
    
    const start = textareaRef.current.selectionStart;
    const end = textareaRef.current.selectionEnd;
    
    if (start === end) {
      // Single cursor position - add division point
      addDivisionPoint(start);
    }
  }, [addDivisionPoint]);

  if (!isEditing) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Scene Division Editor</h3>
            <p className="text-sm text-gray-600">
              Customize scene boundaries by editing division points
            </p>
          </div>
          
          <button
            onClick={startEditing}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <ScissorsIcon className="h-4 w-4 mr-2" />
            Edit Scene Divisions
          </button>
        </div>

        {/* Current Scene Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-lg font-semibold text-blue-700">
              {parsedScript.scenes.length}
            </div>
            <div className="text-sm text-blue-600">Current Scenes</div>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-lg font-semibold text-green-700">
              Auto-Detected
            </div>
            <div className="text-sm text-green-600">Division Method</div>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-lg font-semibold text-purple-700">
              {Math.round(parsedScript.totalDuration / parsedScript.scenes.length)}s
            </div>
            <div className="text-sm text-purple-600">Avg Scene Length</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Editing Scene Divisions</h3>
          <p className="text-sm text-gray-600">
            Click in the text to add division points. Drag handles to move them.
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={cancelEditing}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <XMarkIcon className="h-4 w-4 mr-2" />
            Cancel
          </button>
          
          <button
            onClick={applyChanges}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
          >
            <CheckIcon className="h-4 w-4 mr-2" />
            Apply Changes
          </button>
        </div>
      </div>

      {/* Division Points Summary */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">
            Division Points: {divisionPoints.length}
          </span>
          <span className="text-sm text-gray-600">
            Will create {divisionPoints.length + 1} scenes
          </span>
        </div>
        
        {divisionPoints.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {divisionPoints.map((point) => (
              <div 
                key={point.id}
                className={cn(
                  "inline-flex items-center px-2 py-1 rounded text-xs",
                  point.isNew 
                    ? "bg-green-100 text-green-700" 
                    : "bg-blue-100 text-blue-700"
                )}
              >
                <span>Position {point.position}</span>
                <button
                  onClick={() => removeDivisionPoint(point.id)}
                  className="ml-1 text-red-500 hover:text-red-700"
                >
                  <TrashIcon className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Script Editor */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={selectedScript}
          onChange={(e) => setSelectedScript(e.target.value)}
          onSelect={handleTextSelection}
          className="w-full h-96 p-4 border border-gray-300 rounded-lg font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Paste your script content here..."
        />
        
        {/* Division Point Indicators */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
          {divisionPoints.map((point) => (
            <div
              key={point.id}
              className={cn(
                "absolute w-0.5 h-full",
                point.isNew ? "bg-green-500" : "bg-blue-500"
              )}
              style={{
                left: `${(point.position / selectedScript.length) * 100}%`
              }}
            />
          ))}
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-800 mb-2">Instructions:</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Click anywhere in the text to add a new scene division point</li>
          <li>• Green indicators show new division points you've added</li>
          <li>• Blue indicators show existing scene boundaries</li>
          <li>• Use the trash icon to remove division points</li>
          <li>• Scene divisions should be at natural breaking points (new paragraphs, scene changes)</li>
        </ul>
      </div>
    </div>
  );
};

// Helper functions
function reconstructScriptContent(parsedScript: ParsedScript): string {
  const scriptLines: string[] = [];
  
  // Add title header
  scriptLines.push(`SCRIPT: LOG_${parsedScript.logNumber} - ${parsedScript.title}`);
  scriptLines.push('');
  
  // Add each scene
  parsedScript.scenes.forEach((scene) => {
    scriptLines.push(`[${scene.timestamp.time} - ${scene.sceneType} | ${scene.description}]`);
    
    if (scene.visual) {
      scriptLines.push(`Visual: ${scene.visual}`);
    }
    
    if (scene.narration) {
      scriptLines.push(`Narration: "${scene.narration}"`);
    }
    
    if (scene.onScreenText && scene.onScreenText.lines.length > 0) {
      scriptLines.push('ON-SCREEN TEXT:');
      scene.onScreenText.lines.forEach(line => {
        scriptLines.push(line);
      });
    }
    
    scriptLines.push(''); // Empty line between scenes
  });
  
  return scriptLines.join('\n');
}

function findSceneIndexAtPosition(position: number): number {
  // This is a simplified implementation
  // In a real scenario, you'd need to map positions back to scenes more accurately
  return Math.floor(position / 500); // Rough estimate
}

function applyDivisionsToScript(scriptContent: string, divisionPoints: DivisionPoint[]): string {
  if (divisionPoints.length === 0) {
    return scriptContent;
  }
  
  // Sort division points by position
  const sortedPoints = [...divisionPoints].sort((a, b) => a.position - b.position);
  
  // Split script at division points and add scene markers
  let result = scriptContent;
  let offset = 0;
  
  sortedPoints.forEach((point, index) => {
    const insertPosition = point.position + offset;
    const sceneMarker = `\n\n[NEW SCENE ${index + 1}]\n`;
    
    result = result.slice(0, insertPosition) + sceneMarker + result.slice(insertPosition);
    offset += sceneMarker.length;
  });
  
  return result;
}

export default SceneDivider;