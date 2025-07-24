import React from 'react';
import ProductionLayout from '../../components/layout/ProductionLayout';
import VideoGenerator from '../../components/stages/VideoGenerator';
import { useRouter } from 'next/router';

export default function VideosPage() {
  const router = useRouter();
  const { projectId } = router.query;

  const handleComplete = () => {
    if (projectId) {
      router.push(`/production/assembly?projectId=${projectId}`);
    } else {
      router.push('/production/assembly');
    }
  };

  return (
    <ProductionLayout currentStage="videos" title="Video Generation">
      <VideoGenerator 
        onComplete={handleComplete} 
        projectId={projectId as string}
      />
    </ProductionLayout>
  );
}
