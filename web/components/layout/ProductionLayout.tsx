import React, { ReactNode, useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { StageNavigation, Stage, DEFAULT_PRODUCTION_STAGES } from './StageNavigation';
import ConnectionStatus from '@/components/shared/ConnectionStatus';
import { SparklesIcon } from '@heroicons/react/24/outline';
import { wsManager } from '@/lib/websocket';

interface ProductionLayoutProps {
  children: ReactNode;
  title: string;
  currentStage: string;
}

export const ProductionLayout: React.FC<ProductionLayoutProps> = ({ 
  children, 
  title,
  currentStage, 
}) => {
  const router = useRouter();
  const [stages, setStages] = useState<Stage[]>(DEFAULT_PRODUCTION_STAGES);
  const [productionState, setProductionState] = useState({
    scriptUploaded: false,
    audioGenerated: false,
    imagesGenerated: false,
    videosGenerated: false,
    readyForAssembly: false,
  });

  useEffect(() => {
    // Initialize WebSocket connection
    wsManager.connect();

    // Subscribe to production state updates
    const handleProductionUpdate = (data: any) => {
      setProductionState(data);
      updateStageAvailability(data);
    };

    wsManager.subscribe('production_state', handleProductionUpdate);

    // Load production state from localStorage
    const savedState = localStorage.getItem('productionState');
    if (savedState) {
      const state = JSON.parse(savedState);
      setProductionState(state);
      updateStageAvailability(state);
    }

    return () => {
      wsManager.unsubscribe('production_state', handleProductionUpdate);
    };
  }, []);

  const updateStageAvailability = (state: typeof productionState) => {
    const updatedStages = [...DEFAULT_PRODUCTION_STAGES];
    
    // Script stage is always available
    updatedStages[0].isAvailable = true;
    
    // Audio stage available after script uploaded
    updatedStages[1].isAvailable = state.scriptUploaded;
    updatedStages[1].status = state.scriptUploaded 
      ? (state.audioGenerated ? 'completed' : 'pending')
      : 'disabled';
    
    // Images stage available after audio generated
    updatedStages[2].isAvailable = state.audioGenerated;
    updatedStages[2].status = state.audioGenerated
      ? (state.imagesGenerated ? 'completed' : 'pending')
      : 'disabled';
    
    // Videos stage available after images generated
    updatedStages[3].isAvailable = state.imagesGenerated;
    updatedStages[3].status = state.imagesGenerated
      ? (state.videosGenerated ? 'completed' : 'pending')
      : 'disabled';
    
    // Assembly stage available after videos generated
    updatedStages[4].isAvailable = state.videosGenerated;
    updatedStages[4].status = state.videosGenerated
      ? (state.readyForAssembly ? 'completed' : 'pending')
      : 'disabled';

    // Update current stage status
    const currentStageIndex = updatedStages.findIndex(s => s.id === currentStage);
    if (currentStageIndex !== -1) {
      updatedStages[currentStageIndex].status = 'in_progress';
    }

    setStages(updatedStages);
  };

  const handleStageChange = (stageId: string) => {
    router.push(`/production/${stageId}`);
  };

  return (
    <>
      <Head>
        <title>{title} - Evergreen AI Production</title>
        <meta name="description" content="Multi-stage AI video production pipeline" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <button 
                  onClick={() => router.push('/')}
                  className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg hover:from-primary-600 hover:to-purple-700 transition-colors"
                >
                  <SparklesIcon className="h-6 w-6 text-white" />
                </button>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Evergreen AI Production</h1>
                  <p className="text-sm text-gray-500">Audio-First Video Pipeline</p>
                </div>
              </div>
              
              <ConnectionStatus className="hidden sm:flex" />
            </div>
          </div>
        </header>

        {/* Stage Navigation */}
        <StageNavigation 
          currentStage={currentStage}
          stages={stages}
          onStageChange={handleStageChange}
        />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>
    </>
  );
};

export default ProductionLayout;
