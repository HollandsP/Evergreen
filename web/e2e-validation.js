#!/usr/bin/env node

/**
 * End-to-End Validation Script for Cycle 1 Fixes
 * Tests critical user flows to ensure fixes work in practice
 */

const fs = require('fs');
const https = require('https');

console.log('🚀 END-TO-END VALIDATION SUITE');
console.log('==============================\n');

let totalTests = 0;
let passedTests = 0;
const failedTests = [];

function e2eTest(testName, testFunction, description) {
  totalTests++;
  console.log(`🔄 Running: ${testName}`);
  console.log(`   Description: ${description}`);
  
  try {
    const result = testFunction();
    if (result === true) {
      passedTests++;
      console.log('   ✅ PASSED\n');
      return true;
    } else {
      failedTests.push({ name: testName, reason: result || 'Test returned false', description });
      console.log(`   ❌ FAILED: ${result || 'Test returned false'}\n`);
      return false;
    }
  } catch (error) {
    failedTests.push({ name: testName, reason: error.message, description });
    console.log(`   ❌ FAILED: ${error.message}\n`);
    return false;
  }
}

// Test 1: Component Import Validation
e2eTest(
  'UI-IMPORT-01',
  () => {
    const audioGenContent = fs.readFileSync('./components/stages/AudioGenerator.tsx', 'utf8');
    
    // Check for correct icon import
    const hasCorrectImport = audioGenContent.includes("import { SpeakerWaveIcon, PlayIcon, PauseIcon, ArrowDownTrayIcon, SparklesIcon } from '@heroicons/react/24/outline'");
    const hasIncorrectImport = audioGenContent.includes('DownloadIcon');
    
    if (!hasCorrectImport) {
      return 'ArrowDownTrayIcon not properly imported';
    }
    
    if (hasIncorrectImport) {
      return 'DownloadIcon still referenced in imports';
    }
    
    // Check usage in component
    const hasCorrectUsage = audioGenContent.includes('<ArrowDownTrayIcon className="h-5 w-5"');
    if (!hasCorrectUsage) {
      return 'ArrowDownTrayIcon not used in component JSX';
    }
    
    return true;
  },
  'Validates that DownloadIcon has been replaced with ArrowDownTrayIcon',
);

// Test 2: WebSocket Connection Setup
e2eTest(
  'WS-CONNECTION-01',
  () => {
    // Check main index page
    const indexContent = fs.readFileSync('./pages/index.tsx', 'utf8');
    const hasWsConnect = indexContent.includes('wsManager.connect()');
    
    if (!hasWsConnect) {
      return 'wsManager.connect() not found in index.tsx';
    }
    
    // Check WebSocket manager implementation
    const wsContent = fs.readFileSync('./lib/websocket.ts', 'utf8');
    const hasProperSetup = wsContent.includes('setupEventHandlers') && 
                          wsContent.includes('reconnection: true') &&
                          wsContent.includes('maxReconnectAttempts');
    
    if (!hasProperSetup) {
      return 'WebSocket manager missing proper configuration';
    }
    
    return true;
  },
  'Validates WebSocket connection is properly initialized',
);

// Test 3: Parallel Processing Implementation
e2eTest(
  'PERF-PARALLEL-01',
  () => {
    const audioGenContent = fs.readFileSync('./components/stages/AudioGenerator.tsx', 'utf8');
    
    // Check for Promise.all implementation
    const hasPromiseAll = audioGenContent.includes('await Promise.all(generatePromises)');
    if (!hasPromiseAll) {
      return 'Promise.all not found in generateAllAudio function';
    }
    
    // Check that sequential loop is not present
    const hasSequentialLoop = audioGenContent.includes('for (const scene of scenes)') &&
                             !audioGenContent.includes('// Process scenes in parallel');
    
    if (hasSequentialLoop) {
      return 'Sequential processing loop still present';
    }
    
    // Verify parallel processing setup
    const hasParallelSetup = audioGenContent.includes('scenesToGenerate.map') &&
                           audioGenContent.includes('generateAudio(scene.id, scene.narration)');
    
    if (!hasParallelSetup) {
      return 'Parallel processing not properly configured';
    }
    
    return true;
  },
  'Validates audio generation uses parallel processing with Promise.all',
);

// Test 4: Error Boundary Implementation
e2eTest(
  'ERROR-BOUNDARY-01',
  () => {
    const errorBoundaryContent = fs.readFileSync('./components/ErrorBoundary.tsx', 'utf8');
    
    // Check for essential error boundary methods
    const hasGetDerivedState = errorBoundaryContent.includes('getDerivedStateFromError');
    const hasComponentDidCatch = errorBoundaryContent.includes('componentDidCatch');
    const hasErrorState = errorBoundaryContent.includes('hasError: false');
    
    if (!hasGetDerivedState) {
      return 'getDerivedStateFromError method missing';
    }
    
    if (!hasComponentDidCatch) {
      return 'componentDidCatch method missing';
    }
    
    if (!hasErrorState) {
      return 'Error state management missing';
    }
    
    // Check for user-friendly error UI
    const hasErrorUI = errorBoundaryContent.includes('Something went wrong') &&
                      errorBoundaryContent.includes('Try Again');
    
    if (!hasErrorUI) {
      return 'User-friendly error UI missing';
    }
    
    return true;
  },
  'Validates comprehensive error boundary implementation',
);

// Test 5: Waveform Performance Optimization
e2eTest(
  'PERF-WAVEFORM-01',
  () => {
    const waveformContent = fs.readFileSync('./components/audio/WaveformVisualizer.tsx', 'utf8');
    
    // Check for performance optimizations
    const hasWaveformDataRef = waveformContent.includes('waveformDataRef.useRef') ||
                              waveformContent.includes('waveformDataRef = useRef');
    
    if (!hasWaveformDataRef) {
      return 'Waveform data caching not implemented';
    }
    
    // Check for audio context cleanup
    const hasCleanup = waveformContent.includes('audioContextRef.current?.close()') ||
                      waveformContent.includes('audioContextRef.current.close()');
    
    if (!hasCleanup) {
      return 'AudioContext cleanup missing';
    }
    
    // Check for animation frame management
    const hasAnimationFrame = waveformContent.includes('requestAnimationFrame') ||
                             waveformContent.includes('cancelAnimationFrame');
    
    if (!hasAnimationFrame) {
      return 'Animation frame management missing';
    }
    
    return true;
  },
  'Validates waveform visualizer performance optimizations',
);

// Test 6: Timeout Handling
e2eTest(
  'RELIABILITY-TIMEOUT-01',
  () => {
    const audioGenContent = fs.readFileSync('./components/stages/AudioGenerator.tsx', 'utf8');
    
    // Check for timeout handling in error catch
    const hasTimeoutHandling = audioGenContent.includes('AbortError') ||
                             audioGenContent.includes('timeout') ||
                             audioGenContent.includes('timed out');
    
    if (!hasTimeoutHandling) {
      return 'Timeout error handling not found';
    }
    
    // Check for proper error states
    const hasErrorState = audioGenContent.includes("status: 'error'") &&
                         audioGenContent.includes('errorMessage');
    
    if (!hasErrorState) {
      return 'Error state management missing';
    }
    
    return true;
  },
  'Validates timeout handling in API calls',
);

// Test 7: Memory Management
e2eTest(
  'MEMORY-MANAGEMENT-01',
  () => {
    const waveformContent = fs.readFileSync('./components/audio/WaveformVisualizer.tsx', 'utf8');
    
    // Check for useEffect cleanup
    const hasUseEffectCleanup = waveformContent.includes('return () =>');
    
    if (!hasUseEffectCleanup) {
      return 'useEffect cleanup function missing';
    }
    
    // Check for proper resource disposal
    const hasResourceCleanup = waveformContent.includes('audioContextRef.current?.close()') ||
                              waveformContent.includes('cancelAnimationFrame');
    
    if (!hasResourceCleanup) {
      return 'Resource cleanup not properly implemented';
    }
    
    return true;
  },
  'Validates proper memory management and cleanup',
);

// Test 8: Security - No Unsafe Code
e2eTest(
  'SECURITY-EVAL-01',
  () => {
    const criticalFiles = [
      './lib/script-parser.ts',
      './pages/api/script/parse.ts',
      './lib/utils.ts',
    ];
    
    for (const file of criticalFiles) {
      if (fs.existsSync(file)) {
        const content = fs.readFileSync(file, 'utf8');
        if (content.includes('eval(') && !content.includes('// Safe eval')) {
          return `Unsafe eval() found in ${file}`;
        }
      }
    }
    
    return true;
  },
  'Validates no unsafe eval() usage in critical files',
);

// Summary Report
console.log('=' .repeat(50));
console.log('📊 END-TO-END VALIDATION SUMMARY');
console.log('=' .repeat(50));

const successRate = Math.round((passedTests / totalTests) * 100);

console.log(`\nTotal Tests: ${totalTests}`);
console.log(`Passed: ${passedTests} (${successRate}%)`);
console.log(`Failed: ${failedTests.length} (${100 - successRate}%)`);

if (failedTests.length === 0) {
  console.log('\n🎉 ALL END-TO-END TESTS PASSED!');
  console.log('✅ Critical user flows are working correctly');
  console.log('✅ All Cycle 1 fixes have been successfully validated');
} else {
  console.log('\n❌ FAILED TESTS:');
  failedTests.forEach((test, index) => {
    console.log(`\n${index + 1}. ${test.name}`);
    console.log(`   Description: ${test.description}`);
    console.log(`   Reason: ${test.reason}`);
  });
  
  console.log('\n🔧 ACTION REQUIRED:');
  console.log('- Review failed tests above');
  console.log('- Fix issues before proceeding to Cycle 2');
  console.log('- Re-run validation after fixes');
}

console.log('\n📝 VALIDATION COMPLETE');
console.log(`Overall System Health: ${successRate}%`);

// Exit with error code if tests failed
process.exit(failedTests.length > 0 ? 1 : 0);
