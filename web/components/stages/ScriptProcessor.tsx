import React, { useState, useCallback, useRef } from 'react';
import { CloudArrowUpIcon, PencilIcon, CheckIcon, XMarkIcon, FolderIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { scriptParser, ParsedScript, ScriptScene } from '@/lib/script-parser';
import { cn } from '@/lib/utils';
import { SceneTree } from '@/components/script/SceneTree';
import { SceneDivider } from '@/components/script/SceneDivider';

interface ScriptProcessorProps {
  onComplete: (scriptData: any) => void;
}

// Helper functions for folder structure
const createProjectFolders = async (projectId: string, scenes: ScriptScene[]) => {
  // In a real implementation, this would make API calls to create server-side folders
  // For now, we'll simulate folder creation
  const folders = scenes.map((scene, index) => ({
    name: `scene_${String(index + 1).padStart(2, '0')}`,
    path: `/output/projects/${projectId}/scene_${String(index + 1).padStart(2, '0')}/`,
    sceneId: scene.id
  }));
  
  // Store folder structure in localStorage for now
  localStorage.setItem(`projectFolders_${projectId}`, JSON.stringify(folders));
  return folders;
};

const generateFolderStructure = (projectId: string, scenes: ScriptScene[]) => {
  return scenes.map((scene, index) => ({
    sceneNumber: index + 1,
    sceneId: scene.id,
    folderName: `scene_${String(index + 1).padStart(2, '0')}`,
    folderPath: `/output/projects/${projectId}/scene_${String(index + 1).padStart(2, '0')}/`,
    assets: {
      images: [],
      audio: [],
      video: [],
      metadata: {
        title: scene.sceneType || `Scene ${index + 1}`,
        description: scene.description || '',
        duration: 0,
        wordCount: scene.narration?.split(' ').length || 0
      }
    }
  }));
};

export const ScriptProcessor: React.FC<ScriptProcessorProps> = ({ onComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsedScript, setParsedScript] = useState<ParsedScript | null>(null);
  const [editingScene, setEditingScene] = useState<string | null>(null);
  const [editedNarration, setEditedNarration] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = useCallback(async (file: File) => {
    const supportedFormats = ['.txt', '.md', '.pdf'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!supportedFormats.includes(fileExtension)) {
      setError('Please upload a .txt, .md, or .pdf file');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let content: string;
      
      if (fileExtension === '.pdf') {
        // For PDF files, we'll need to extract text (simplified approach)
        setError('PDF support coming soon. Please convert to .txt or .md format.');
        return;
      } else {
        content = await file.text();
      }
      
      // Call the API to parse the script
      const response = await fetch('/api/script/parse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          fileName: file.name,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to parse script');
      }

      const result = await response.json();
      
      if (!result.success || !result.scenes || result.scenes.length === 0) {
        throw new Error('No scenes found in the script');
      }

      // Create a parsed script object from the API response
      const parsed = {
        title: result.metadata?.title || 'The Descent',
        logNumber: '001',
        scenes: result.scenes,
        totalDuration: result.totalDuration,
        characterCount: result.characterCount
      };

      setParsedScript(parsed);
      
      // Save to localStorage with enhanced metadata
      const productionData = {
        ...parsed,
        projectId: result.projectId,
        uploadedFile: file.name,
        uploadedAt: new Date().toISOString(),
        scenes: result.scenes,
      };
      localStorage.setItem('scriptData', JSON.stringify(productionData));
      
      // Update production state
      const currentState = JSON.parse(localStorage.getItem('productionState') || '{}');
      const newState = { 
        ...currentState, 
        scriptUploaded: true,
        projectId: result.projectId,
        projectName: parsed.title || 'Untitled Project',
        currentStage: 'script'
      };
      localStorage.setItem('productionState', JSON.stringify(newState));
      
      // Notify parent with the project ID
      onComplete({ ...productionData, projectId: result.projectId });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse script');
    } finally {
      setIsLoading(false);
    }
  }, [onComplete]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  }, [handleFileUpload]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  }, [handleFileUpload]);

  const startEditingNarration = (scene: ScriptScene) => {
    setEditingScene(scene.id);
    setEditedNarration(scene.narration || '');
  };

  const saveNarrationEdit = () => {
    if (!parsedScript || !editingScene) return;

    const updatedScenes = parsedScript.scenes.map(scene => 
      scene.id === editingScene 
        ? { ...scene, narration: editedNarration }
        : scene,
    );

    const updatedScript = { ...parsedScript, scenes: updatedScenes };
    setParsedScript(updatedScript);

    // Update localStorage
    const productionData = scriptParser.exportForProduction(updatedScript);
    localStorage.setItem('scriptData', JSON.stringify(productionData));

    setEditingScene(null);
    setEditedNarration('');
  };

  const cancelEdit = () => {
    setEditingScene(null);
    setEditedNarration('');
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-4xl mx-auto">
      {!parsedScript ? (
        <div className="space-y-6">
          {/* Upload Area */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={cn(
              'relative border-2 border-dashed rounded-lg p-12 text-center transition-all duration-200',
              isDragging 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-300 hover:border-gray-400 bg-white',
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            <CloudArrowUpIcon className={cn(
              'mx-auto h-16 w-16 transition-colors',
              isDragging ? 'text-primary-500' : 'text-gray-400',
            )} />
            
            <h3 className="mt-4 text-lg font-semibold text-gray-900">
              Upload "The Descent" Script
            </h3>
            <p className="mt-2 text-sm text-gray-600">
              Drag and drop your script file here, or click to browse
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Supports .txt, .md, and .pdf files in LOG format
            </p>
            
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : 'Select File'}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <XMarkIcon className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
                  <p className="mt-1 text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Example Format */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Expected Format:</h4>
            <pre className="text-xs text-gray-600 font-mono bg-white p-3 rounded border border-gray-200 overflow-x-auto">
              {`[0:00 - Cold Open | Terminal Boot-Up]
Visual: Terminal-style screen blinking to life.
ON-SCREEN TEXT:
ACCESSING: INCIDENT LOG
Narration (Winston):
"We didn't build gods..."

[0:20 - Introduction | Office Montage]
Visual: Futuristic office, name badges...`}
            </pre>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Script Info */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">{parsedScript.title}</h2>
                <p className="text-sm text-gray-500">
                  LOG_{parsedScript.logNumber} • {parsedScript.scenes.length} scenes • {formatDuration(parsedScript.totalDuration)} total
                </p>
              </div>
              <button
                onClick={() => {
                  setParsedScript(null);
                  setError(null);
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Upload Different Script
              </button>
            </div>
          </div>

          {/* Script Tree Visualization */}
          <div className="space-y-6">
            <SceneTree parsedScript={parsedScript} />
            
            {/* Scene Division Editor */}
            <SceneDivider 
              parsedScript={parsedScript} 
              onScenesUpdated={(updatedScript) => {
                setParsedScript(updatedScript);
                // Update localStorage
                const productionData = scriptParser.exportForProduction(updatedScript);
                localStorage.setItem('scriptData', JSON.stringify(productionData));
              }}
            />
            
            <h3 className="text-lg font-semibold text-gray-900">Scene Breakdown</h3>
            
            {parsedScript.scenes.map((scene, index) => (
              <div key={scene.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-gray-900">
                        Scene {index + 1}: {scene.sceneType}
                      </span>
                      <span className="ml-3 text-sm text-gray-500">
                        [{scene.timestamp.time}]
                      </span>
                    </div>
                  </div>
                  <p className="mt-1 text-sm text-gray-600">{scene.description}</p>
                </div>
                
                <div className="p-6 space-y-4">
                  {/* Visual Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Visual</label>
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{scene.visual}</p>
                  </div>

                  {/* Narration */}
                  {scene.narration && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="block text-sm font-medium text-gray-700">Narration</label>
                        {editingScene !== scene.id && (
                          <button
                            onClick={() => startEditingNarration(scene)}
                            className="text-xs text-primary-600 hover:text-primary-700 flex items-center"
                          >
                            <PencilIcon className="h-3 w-3 mr-1" />
                            Edit
                          </button>
                        )}
                      </div>
                      
                      {editingScene === scene.id ? (
                        <div className="space-y-2">
                          <textarea
                            value={editedNarration}
                            onChange={(e) => setEditedNarration(e.target.value)}
                            className="w-full text-sm text-gray-600 bg-white p-3 rounded border border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                            rows={3}
                          />
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={cancelEdit}
                              className="text-sm text-gray-500 hover:text-gray-700"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={saveNarrationEdit}
                              className="text-sm text-white bg-primary-600 hover:bg-primary-700 px-3 py-1 rounded"
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded italic">
                          "{scene.narration}"
                        </p>
                      )}
                    </div>
                  )}

                  {/* On-Screen Text */}
                  {scene.onScreenText && scene.onScreenText.lines.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">On-Screen Text</label>
                      <div className="text-sm text-gray-600 bg-gray-900 text-green-400 p-3 rounded font-mono">
                        {scene.onScreenText.lines.map((line, i) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Generated Image Prompt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Generated Image Prompt</label>
                    <p className="text-sm text-gray-600 bg-blue-50 p-3 rounded">{scene.imagePrompt}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Continue Button */}
          <div className="flex justify-end pt-6">
            <button
              onClick={() => {
                const productionData = scriptParser.exportForProduction(parsedScript);
                onComplete(productionData);
              }}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Continue to Audio Generation
              <CheckIcon className="ml-2 h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScriptProcessor;
