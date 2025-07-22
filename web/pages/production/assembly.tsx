import React from 'react';
import ProductionLayout from '../../components/layout/ProductionLayout';
import FinalAssembly from '../../components/stages/FinalAssembly';
// import { useRouter } from 'next/router';

export default function AssemblyPage() {
  // const router = useRouter();

  const handleComplete = () => {
    // Production is complete - could redirect to a completion page or download page
    alert('Video production complete! Your video is ready for download.');
    // router.push('/completion'); // Future enhancement
  };

  return (
    <ProductionLayout currentStage="assembly" title="Final Assembly">
      <FinalAssembly onComplete={handleComplete} />
    </ProductionLayout>
  );
}
