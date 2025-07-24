import React, { useState } from 'react';
import { useRouter } from 'next/router';
import ProductionLayout from '../../components/layout/ProductionLayout';
import FinalAssembly from '../../components/stages/FinalAssembly';
import ChatInterface from '../../components/editor/ChatInterface';
import EditingTimeline from '../../components/editor/EditingTimeline';
export default function AssemblyPage() {
  const router = useRouter();
  const { projectId } = router.query;
  const [storyboardData] = useState(null);

  const handleComplete = () => {
    // Production is complete - could redirect to a completion page or download page
    alert('Video production complete! Your video is ready for download.');
    // router.push('/completion'); // Future enhancement
  };

  const handleCommandExecuted = (result: any) => {
    // Handle successful command execution
    console.log('Command executed:', result);
    // Optionally refresh timeline or show notifications
  };

  const handleClipSelected = (_clip: any) => {
    // Handle clip selection - to be implemented
  };

  const handleTimelineChange = (tracks: any) => {
    // Handle timeline changes
    console.log('Timeline updated:', tracks);
  };

  return (
    <ProductionLayout currentStage="assembly" title="AI Video Editor">
      <div className="h-full flex flex-col gap-4 p-4">
        {/* Top section: Final Assembly component */}
        <div className="flex-shrink-0">
          <FinalAssembly onComplete={handleComplete} projectId={projectId as string} />
        </div>

        {/* Main editing interface */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0">
          {/* Timeline - spans 2 columns on large screens */}
          <div className="lg:col-span-2">
            <EditingTimeline
              projectId={projectId as string || "current_project"}
              storyboardData={storyboardData}
              onClipSelected={handleClipSelected}
              onTimelineChange={handleTimelineChange}
              className="h-full"
            />
          </div>

          {/* Chat Interface - 1 column */}
          <div className="lg:col-span-1">
            <ChatInterface
              projectId={projectId as string || "current_project"}
              storyboardData={storyboardData}
              onCommandExecuted={handleCommandExecuted}
              className="h-full"
            />
          </div>
        </div>
      </div>
    </ProductionLayout>
  );
}
