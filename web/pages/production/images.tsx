import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import ProductionLayout from '@/components/layout/ProductionLayout';
import ImageGenerator from '@/components/stages/ImageGenerator';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export default function ImageGenerationPage() {
  const router = useRouter();
  const { projectId } = router.query;
  const [hasRequiredData, setHasRequiredData] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if we have the required data from previous stages
    const scriptData = localStorage.getItem('scriptData');
    const audioData = localStorage.getItem('audioData');
    const productionState = JSON.parse(localStorage.getItem('productionState') || '{}');

    if (scriptData && audioData && productionState.audioGenerated) {
      setHasRequiredData(true);
    }
    setIsLoading(false);
  }, []);

  const handleComplete = () => {
    if (projectId) {
      router.push(`/production/videos?projectId=${projectId}`);
    } else {
      router.push('/production/videos');
    }
  };

  if (isLoading) {
    return (
      <ProductionLayout 
        title="Image Generation" 
        currentStage="images"
      >
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </ProductionLayout>
    );
  }

  return (
    <ProductionLayout 
      title="Image Generation" 
      currentStage="images"
    >
      <div className="space-y-8">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Image Generation</h1>
          <p className="mt-2 text-lg text-gray-600">
            Generate visual scenes for your video using AI image generation
          </p>
        </div>

        {hasRequiredData ? (
          <ImageGenerator 
            onComplete={handleComplete} 
            projectId={projectId as string}
          />
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex">
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600 flex-shrink-0" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Missing Required Data
                </h3>
                <p className="mt-2 text-sm text-yellow-700">
                  Please complete the script processing and audio generation stages first.
                </p>
                <button
                  onClick={() => router.push('/production/script')}
                  className="mt-3 text-sm font-medium text-yellow-800 hover:text-yellow-900"
                >
                  Go to Script Processing →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProductionLayout>
  );
}
