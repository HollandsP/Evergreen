import React from 'react';
import ProductionLayout from '../../components/layout/ProductionLayout';
import VideoGenerator from '../../components/stages/VideoGenerator';
import { useRouter } from 'next/router';

export default function VideosPage() {
  const router = useRouter();

  const handleComplete = () => {
    router.push('/production/assembly');
  };

  return (
    <ProductionLayout currentStage="videos">
      <VideoGenerator onComplete={handleComplete} />
    </ProductionLayout>
  );
}