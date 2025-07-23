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
    // Initialize WebSocket connection for production updates
    wsManager.connect();
    
    return () => {
      // Cleanup WebSocket on unmount
      wsManager.disconnect();
    };
  }, []);

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
          currentStage=""
          stages={DEFAULT_PRODUCTION_STAGES}
        />

        {/* Production Pipeline Overview */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">AI Video Production Pipeline</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Transform your script into professional YouTube videos using our 5-stage AI-powered pipeline.
              Select any stage below to begin or continue your video production.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {DEFAULT_PRODUCTION_STAGES.map((stage, index) => {
              const Icon = stage.icon;
              return (
                <div
                  key={stage.id}
                  onClick={() => router.push(stage.path)}
                  className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer group"
                >
                  <div className="flex items-center mb-4">
                    <div className="flex-shrink-0">
                      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-50 group-hover:bg-primary-100 transition-colors">
                        <Icon className="h-6 w-6 text-primary-600" />
                      </div>
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-medium text-gray-900">
                        Stage {index + 1}: {stage.name}
                      </h3>
                    </div>
                  </div>
                  <p className="text-gray-600 mb-4">{stage.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Click to start</span>
                    <svg
                      className="h-5 w-5 text-gray-400 group-hover:text-primary-600 transition-colors"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
}
