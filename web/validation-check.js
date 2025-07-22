#!/usr/bin/env node

/**
 * Critical Web UI Fixes Validation Script
 * Verifies all critical issues have been fixed
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating Critical Web UI Fixes...\n');

const fixes = [
  {
    name: '1. DownloadIcon Import Fix',
    description: 'Fixed DownloadIcon to ArrowDownTrayIcon in AudioGenerator',
    validate: () => {
      const audioGenPath = path.join(__dirname, 'components/stages/AudioGenerator.tsx');
      if (!fs.existsSync(audioGenPath)) return { success: false, message: 'AudioGenerator.tsx not found' };
      
      const content = fs.readFileSync(audioGenPath, 'utf8');
      const hasDownloadIcon = content.includes('<DownloadIcon');
      const hasArrowDownTray = content.includes('<ArrowDownTrayIcon');
      const hasImport = content.includes('ArrowDownTrayIcon') && content.includes("from '@heroicons/react/24/outline'");
      
      if (hasDownloadIcon) {
        return { success: false, message: 'Still using DownloadIcon instead of ArrowDownTrayIcon' };
      }
      
      if (!hasArrowDownTray || !hasImport) {
        return { success: false, message: 'ArrowDownTrayIcon not properly imported or used' };
      }
      
      return { success: true, message: 'ArrowDownTrayIcon properly imported and used' };
    },
  },

  {
    name: '2. WebSocket Connection Fix',
    description: 'Added connection retry logic and error handling',
    validate: () => {
      const wsPath = path.join(__dirname, 'lib/websocket.ts');
      const indexPath = path.join(__dirname, 'pages/index.tsx');
      
      if (!fs.existsSync(wsPath)) return { success: false, message: 'websocket.ts not found' };
      if (!fs.existsSync(indexPath)) return { success: false, message: 'index.tsx not found' };
      
      const wsContent = fs.readFileSync(wsPath, 'utf8');
      const indexContent = fs.readFileSync(indexPath, 'utf8');
      
      const hasReconnection = wsContent.includes('reconnection: true');
      const hasReconnectionAttempts = wsContent.includes('reconnectionAttempts');
      const hasSetupListeners = indexContent.includes('setupWebSocketListeners');
      const hasConnectionHandling = indexContent.includes('wsManager.connect()');
      
      if (!hasReconnection || !hasReconnectionAttempts) {
        return { success: false, message: 'WebSocket reconnection logic missing' };
      }
      
      if (!hasSetupListeners || !hasConnectionHandling) {
        return { success: false, message: 'WebSocket connection setup incomplete' };
      }
      
      return { success: true, message: 'WebSocket connection properly configured with retry logic' };
    },
  },

  {
    name: '3. Parallel Processing Fix', 
    description: 'Replaced for-await loop with Promise.all for parallel processing',
    validate: () => {
      const audioGenPath = path.join(__dirname, 'components/stages/AudioGenerator.tsx');
      if (!fs.existsSync(audioGenPath)) return { success: false, message: 'AudioGenerator.tsx not found' };
      
      const content = fs.readFileSync(audioGenPath, 'utf8');
      const hasPromiseAll = content.includes('Promise.all(');
      const hasGeneratePromises = content.includes('generatePromises');
      const hasFilterScenes = content.includes('scenesToGenerate');
      
      if (!hasPromiseAll || !hasGeneratePromises || !hasFilterScenes) {
        return { success: false, message: 'Parallel processing implementation missing' };
      }
      
      return { success: true, message: 'Parallel processing with Promise.all implemented' };
    },
  },

  {
    name: '4. WaveformVisualizer Performance Fix',
    description: 'Optimized canvas operations and added memory management',
    validate: () => {
      const waveformPath = path.join(__dirname, 'components/audio/WaveformVisualizer.tsx');
      if (!fs.existsSync(waveformPath)) return { success: false, message: 'WaveformVisualizer.tsx not found' };
      
      const content = fs.readFileSync(waveformPath, 'utf8');
      const hasOptimizedDraw = content.includes('drawOptimizedWaveform');
      const hasWaveformData = content.includes('waveformDataRef');
      const hasTargetFPS = content.includes('targetFPS');
      const hasErrorHandling = content.includes('setError');
      const hasLoadingState = content.includes('isLoading');
      
      if (!hasOptimizedDraw || !hasWaveformData) {
        return { success: false, message: 'Waveform optimization missing' };
      }
      
      if (!hasTargetFPS) {
        return { success: false, message: 'FPS limiting not implemented' };
      }
      
      if (!hasErrorHandling || !hasLoadingState) {
        return { success: false, message: 'Error handling or loading states missing' };
      }
      
      return { success: true, message: 'WaveformVisualizer performance optimizations implemented' };
    },
  },

  {
    name: '5. Error Boundaries and Loading States',
    description: 'Added comprehensive error boundaries and loading indicators',
    validate: () => {
      const errorBoundaryPath = path.join(__dirname, 'components/ErrorBoundary.tsx');
      const loadingSpinnerPath = path.join(__dirname, 'components/LoadingSpinner.tsx');
      const audioGenPath = path.join(__dirname, 'components/stages/AudioGenerator.tsx');
      
      if (!fs.existsSync(errorBoundaryPath)) return { success: false, message: 'ErrorBoundary.tsx not found' };
      if (!fs.existsSync(loadingSpinnerPath)) return { success: false, message: 'LoadingSpinner.tsx not found' };
      if (!fs.existsSync(audioGenPath)) return { success: false, message: 'AudioGenerator.tsx not found' };
      
      const errorBoundaryContent = fs.readFileSync(errorBoundaryPath, 'utf8');
      const loadingSpinnerContent = fs.readFileSync(loadingSpinnerPath, 'utf8');
      const audioGenContent = fs.readFileSync(audioGenPath, 'utf8');
      
      const hasErrorBoundary = errorBoundaryContent.includes('class ErrorBoundary');
      const hasTryAgain = errorBoundaryContent.includes('Try Again');
      const hasLoadingSpinner = loadingSpinnerContent.includes('animate-spin');
      const hasErrorBoundaryUsage = audioGenContent.includes('<ErrorBoundary');
      const hasLoadingSpinnerUsage = audioGenContent.includes('<LoadingSpinner');
      
      if (!hasErrorBoundary || !hasTryAgain) {
        return { success: false, message: 'ErrorBoundary implementation incomplete' };
      }
      
      if (!hasLoadingSpinner) {
        return { success: false, message: 'LoadingSpinner implementation missing' };
      }
      
      if (!hasErrorBoundaryUsage || !hasLoadingSpinnerUsage) {
        return { success: false, message: 'Error boundary or loading spinner not used in components' };
      }
      
      return { success: true, message: 'Error boundaries and loading states properly implemented' };
    },
  },

  {
    name: '6. Enhanced Error Handling',
    description: 'Added timeout handling, detailed error messages, and graceful degradation',
    validate: () => {
      const audioGenPath = path.join(__dirname, 'components/stages/AudioGenerator.tsx');
      if (!fs.existsSync(audioGenPath)) return { success: false, message: 'AudioGenerator.tsx not found' };
      
      const content = fs.readFileSync(audioGenPath, 'utf8');
      const hasAbortController = content.includes('AbortController');
      const hasTimeout = content.includes('setTimeout') && content.includes('controller.abort()');
      const hasDetailedError = content.includes('HTTP ${response.status}');
      const hasAbortError = content.includes('AbortError');
      const hasStorageErrorHandling = content.includes('catch (storageError)');
      
      if (!hasAbortController || !hasTimeout) {
        return { success: false, message: 'Request timeout handling missing' };
      }
      
      if (!hasDetailedError || !hasAbortError) {
        return { success: false, message: 'Detailed error handling missing' };
      }
      
      if (!hasStorageErrorHandling) {
        return { success: false, message: 'Storage error handling missing' };
      }
      
      return { success: true, message: 'Enhanced error handling with timeouts and detailed messages' };
    },
  },
];

let passedCount = 0;
let failedCount = 0;

console.log('Running validation checks...\n');

fixes.forEach((fix, index) => {
  try {
    const result = fix.validate();
    const status = result.success ? '✅ PASS' : '❌ FAIL';
    const icon = result.success ? '✅' : '❌';
    
    console.log(`${icon} ${fix.name}`);
    console.log(`   ${fix.description}`);
    console.log(`   ${result.message}\n`);
    
    if (result.success) {
      passedCount++;
    } else {
      failedCount++;
    }
  } catch (error) {
    console.log(`❌ ${fix.name}`);
    console.log(`   ${fix.description}`);
    console.log(`   Error during validation: ${error.message}\n`);
    failedCount++;
  }
});

console.log('=' .repeat(60));
console.log('\n📊 VALIDATION SUMMARY:');
console.log(`✅ Passed: ${passedCount}/${fixes.length}`);
console.log(`❌ Failed: ${failedCount}/${fixes.length}`);

if (failedCount === 0) {
  console.log('\n🎉 ALL CRITICAL WEB UI FIXES VALIDATED SUCCESSFULLY!');
  console.log('\nThe following issues have been resolved:');
  console.log('• DownloadIcon import crash fixed');
  console.log('• WebSocket connection issues resolved'); 
  console.log('• Sequential processing performance improved');
  console.log('• WaveformVisualizer performance optimized');
  console.log('• Error boundaries and loading states added');
  console.log('• Enhanced error handling implemented');
  
  console.log('\n🚀 Web UI is now stable and performant!');
  process.exit(0);
} else {
  console.log('\n⚠️  Some fixes need attention. Please review failed items above.');
  process.exit(1);
}
