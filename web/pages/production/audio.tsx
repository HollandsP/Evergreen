import React from 'react';
import { useRouter } from 'next/router';
import ProductionLayout from '@/components/layout/ProductionLayout';
import AudioGenerator from '@/components/stages/AudioGenerator';

export default function AudioGenerationPage() {
  const router = useRouter();

  const handleComplete = () => {
    // Navigate to the images stage
    router.push('/production/images');
  };

  return (
    <ProductionLayout 
      title="Audio Generation" 
      currentStage="audio"
    >
      <div className="space-y-8">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audio Generation</h1>
          <p className="mt-2 text-lg text-gray-600">
            Generate narration audio using ElevenLabs voice synthesis for Winston Marek's character
          </p>
        </div>

        {/* Audio Generator Component */}
        <AudioGenerator onComplete={handleComplete} />
      </div>
    </ProductionLayout>
  );
}
