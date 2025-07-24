import React, { useCallback } from 'react';
import { useRouter } from 'next/router';
import ProductionLayout from '@/components/layout/ProductionLayout';
import ScriptProcessor from '@/components/stages/ScriptProcessor';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

export default function ScriptProcessingPage() {
  const router = useRouter();

  const handleScriptComplete = useCallback((scriptData: any) => {
    // Script data is already saved to localStorage by ScriptProcessor
    // Navigate to the audio generation stage with projectId
    const projectId = scriptData.projectId;
    if (projectId) {
      // Store projectId in URL query for next stages
      setTimeout(() => {
        router.push(`/production/audio?projectId=${projectId}`);
      }, 1000);
    } else {
      // Fallback to regular navigation
      setTimeout(() => {
        router.push('/production/audio');
      }, 1000);
    }
  }, [router]);

  return (
    <ProductionLayout 
      title="Script Processing" 
      currentStage="script"
    >
      <div className="space-y-8">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Script Processing</h1>
          <p className="mt-2 text-lg text-gray-600">
            Upload and parse "The Descent" script to begin the production pipeline
          </p>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <InformationCircleIcon className="h-5 w-5 text-blue-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Script Requirements</h3>
              <div className="mt-2 text-sm text-blue-700">
                <ul className="list-disc list-inside space-y-1">
                  <li>Upload the LOG format script file (.txt)</li>
                  <li>Script will be parsed to extract scenes, timestamps, and narration</li>
                  <li>You can edit narration text before proceeding</li>
                  <li>Image prompts will be auto-generated for each scene</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Script Processor Component */}
        <ScriptProcessor onComplete={handleScriptComplete} />

        {/* Help Section */}
        <div className="mt-12 border-t border-gray-200 pt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">About The Descent Script Format</h3>
          <div className="prose prose-sm text-gray-600">
            <p>
              "The Descent" uses a specialized LOG format designed for audio-visual production:
            </p>
            <ul>
              <li><strong>Timestamps:</strong> Each scene begins with [MM:SS - Scene Type | Description]</li>
              <li><strong>Visual:</strong> Describes what should appear on screen</li>
              <li><strong>Narration:</strong> Winston's voiceover text (can be edited)</li>
              <li><strong>On-Screen Text:</strong> Terminal or UI text displayed in the scene</li>
            </ul>
            <p>
              The parser automatically extracts these elements and generates appropriate image prompts
              for each scene based on the visual descriptions and scene type.
            </p>
          </div>
        </div>
      </div>
    </ProductionLayout>
  );
}
