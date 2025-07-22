import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { StageNavigation, DEFAULT_PRODUCTION_STAGES } from '@/components/layout/StageNavigation';
import ConnectionStatus from '@/components/shared/ConnectionStatus';
import { SparklesIcon } from '@heroicons/react/24/outline';
import { wsManager } from '@/lib/websocket';

export default function ProductionDashboard() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to first stage
    router.push('/production/script');
  }, [router]);

  return (
    <>
      <Head>
        <title>Production Pipeline - Evergreen AI</title>
        <meta name="description" content="Multi-stage AI video production pipeline" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg">
                  <SparklesIcon className="h-6 w-6 text-white" />
                </div>
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
          currentStage="script"
          stages={DEFAULT_PRODUCTION_STAGES}
        />

        {/* Loading State */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Redirecting to Script Processing...</p>
          </div>
        </div>
      </div>
    </>
  );
}