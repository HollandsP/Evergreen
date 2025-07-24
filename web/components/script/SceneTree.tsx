import React, { useState } from 'react';
import { 
  ChevronDownIcon, 
  ChevronRightIcon, 
  DocumentTextIcon,
  FolderIcon,
  FolderOpenIcon,
  ClockIcon,
  ChatBubbleLeftIcon,
  PhotoIcon
} from '@heroicons/react/24/outline';
import { ParsedScript, ScriptScene } from '@/lib/script-parser';
import { cn } from '@/lib/utils';

interface SceneTreeProps {
  parsedScript: ParsedScript;
}

interface TreeNodeProps {
  scene: ScriptScene;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

const SceneTreeNode: React.FC<TreeNodeProps> = ({ scene, index, isExpanded, onToggle }) => {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const wordCount = scene.narration?.split(' ').length || 0;

  return (
    <div className="border-l-2 border-gray-200 ml-4">
      {/* Scene Header */}
      <div 
        className="flex items-center space-x-2 p-3 hover:bg-gray-50 cursor-pointer group"
        onClick={onToggle}
      >
        <button className="text-gray-400 group-hover:text-gray-600">
          {isExpanded ? (
            <ChevronDownIcon className="h-4 w-4" />
          ) : (
            <ChevronRightIcon className="h-4 w-4" />
          )}
        </button>
        
        <div className="flex items-center space-x-2 flex-1">
          {isExpanded ? (
            <FolderOpenIcon className="h-5 w-5 text-blue-500" />
          ) : (
            <FolderIcon className="h-5 w-5 text-gray-500" />
          )}
          
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900">
                Scene {index + 1}: {scene.sceneType}
              </h4>
              <span className="text-xs text-gray-500 flex items-center">
                <ClockIcon className="h-3 w-3 mr-1" />
                {scene.timestamp.time}
              </span>
            </div>
            <p className="text-xs text-gray-600 truncate">
              {scene.description}
            </p>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="ml-8 space-y-2 pb-3">
          {/* Folder Structure */}
          <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded font-mono">
            📁 scene_{String(index + 1).padStart(2, '0')}/
            <div className="ml-4">
              📄 metadata.json<br/>
              🖼️ images/<br/>
              🔊 audio/<br/>
              🎬 video/
            </div>
          </div>

          {/* Scene Metadata */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="bg-white p-2 rounded border">
              <div className="flex items-center space-x-1 mb-1">
                <ChatBubbleLeftIcon className="h-3 w-3 text-blue-500" />
                <span className="font-medium">Narration</span>
              </div>
              <div className="text-gray-600">
                {wordCount} words
                {scene.narration && (
                  <div className="mt-1 text-xs italic truncate">
                    "{scene.narration.substring(0, 50)}..."
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white p-2 rounded border">
              <div className="flex items-center space-x-1 mb-1">
                <PhotoIcon className="h-3 w-3 text-green-500" />
                <span className="font-medium">Visual Style</span>
              </div>
              <div className="text-gray-600 text-xs">
                {scene.visual || 'No visual description'}
              </div>
            </div>
          </div>

          {/* Generated Prompt Preview */}
          {scene.imagePrompt && (
            <div className="bg-blue-50 p-2 rounded">
              <div className="text-xs font-medium text-blue-800 mb-1">
                Generated Image Prompt:
              </div>
              <div className="text-xs text-blue-700">
                {scene.imagePrompt}
              </div>
            </div>
          )}

          {/* On-Screen Text */}
          {scene.onScreenText && scene.onScreenText.lines.length > 0 && (
            <div className="bg-gray-900 text-green-400 p-2 rounded font-mono text-xs">
              <div className="text-green-300 mb-1">TERMINAL OUTPUT:</div>
              {scene.onScreenText.lines.map((line, i) => (
                <div key={i}>&gt; {line}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const SceneTree: React.FC<SceneTreeProps> = ({ parsedScript }) => {
  const [expandedScenes, setExpandedScenes] = useState<Set<string>>(new Set());

  const toggleScene = (sceneId: string) => {
    const newExpanded = new Set(expandedScenes);
    if (newExpanded.has(sceneId)) {
      newExpanded.delete(sceneId);
    } else {
      newExpanded.add(sceneId);
    }
    setExpandedScenes(newExpanded);
  };

  const toggleAll = () => {
    if (expandedScenes.size === parsedScript.scenes.length) {
      setExpandedScenes(new Set());
    } else {
      setExpandedScenes(new Set(parsedScript.scenes.map(scene => scene.id)));
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <DocumentTextIcon className="h-6 w-6 text-blue-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {parsedScript.title}
              </h3>
              <p className="text-sm text-gray-500">
                LOG_{parsedScript.logNumber} • {parsedScript.scenes.length} scenes • {formatDuration(parsedScript.totalDuration)} total
              </p>
            </div>
          </div>
          
          <button
            onClick={toggleAll}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {expandedScenes.size === parsedScript.scenes.length ? 'Collapse All' : 'Expand All'}
          </button>
        </div>
      </div>

      {/* Project Structure Root */}
      <div className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <FolderOpenIcon className="h-5 w-5 text-yellow-500" />
          <span className="font-medium text-gray-900">Project Structure</span>
        </div>

        {/* Scene Tree */}
        <div className="space-y-1">
          {parsedScript.scenes.map((scene, index) => (
            <SceneTreeNode
              key={scene.id}
              scene={scene}
              index={index}
              isExpanded={expandedScenes.has(scene.id)}
              onToggle={() => toggleScene(scene.id)}
            />
          ))}
        </div>

        {/* Summary Statistics */}
        <div className="mt-6 grid grid-cols-3 gap-4 text-center">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-lg font-semibold text-blue-700">
              {parsedScript.scenes.length}
            </div>
            <div className="text-sm text-blue-600">Total Scenes</div>
          </div>
          
          <div className="bg-green-50 p-3 rounded">
            <div className="text-lg font-semibold text-green-700">
              {parsedScript.scenes.reduce((total, scene) => 
                total + (scene.narration?.split(' ').length || 0), 0
              )}
            </div>
            <div className="text-sm text-green-600">Total Words</div>
          </div>
          
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-lg font-semibold text-purple-700">
              {formatDuration(parsedScript.totalDuration)}
            </div>
            <div className="text-sm text-purple-600">Estimated Duration</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SceneTree;