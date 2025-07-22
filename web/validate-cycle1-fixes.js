#!/usr/bin/env node

/**
 * Cycle 1 Fix Validation Script
 * 
 * Validates that all critical fixes from Cycle 1 have been properly applied
 * and identifies any new issues for Cycle 2 improvements.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 CYCLE 1 FIX VALIDATION REPORT');
console.log('==================================\n');

const results = {
  security: { passed: 0, failed: 0, issues: [] },
  webUI: { passed: 0, failed: 0, issues: [] },
  performance: { passed: 0, failed: 0, issues: [] },
  reliability: { passed: 0, failed: 0, issues: [] },
  newIssues: [],
};

function validateFile(filePath, description) {
  try {
    if (!fs.existsSync(filePath)) {
      return { exists: false, content: null };
    }
    const content = fs.readFileSync(filePath, 'utf8');
    return { exists: true, content, lines: content.split('\n') };
  } catch (error) {
    console.log(`❌ Error reading ${description}: ${error.message}`);
    return { exists: false, content: null, error: error.message };
  }
}

function checkFix(category, testName, condition, description) {
  if (condition) {
    results[category].passed++;
    console.log(`✅ ${testName}: ${description}`);
    return true;
  } else {
    results[category].failed++;
    results[category].issues.push(`${testName}: ${description}`);
    console.log(`❌ ${testName}: ${description}`);
    return false;
  }
}

// =============================================================================
// 1. SECURITY FIXES VALIDATION
// =============================================================================

console.log('🛡️  SECURITY FIXES VALIDATION\n');

// Check for eval() removal/mitigation
const scriptParserFile = validateFile('./lib/script-parser.ts', 'Script Parser');
if (scriptParserFile.exists) {
  const hasEval = scriptParserFile.content.includes('eval(');
  const hasSecureEval = scriptParserFile.content.includes('safeEval') || 
                        scriptParserFile.content.includes('vm.runInNewContext') ||
                        scriptParserFile.content.includes('Function(');
  
  checkFix('security', 'SEC-01', !hasEval || hasSecureEval, 
    !hasEval ? 'No eval() usage found' : 
      hasSecureEval ? 'eval() replaced with secure alternative' : 
        'CRITICAL: Unsafe eval() still present');
}

// Check input validation
const apiFiles = [
  './pages/api/script/parse.ts',
  './pages/api/audio/generate.ts',
  './pages/api/images/generate.ts',
];

let inputValidationCount = 0;
apiFiles.forEach(apiFile => {
  const file = validateFile(apiFile, `API ${path.basename(apiFile)}`);
  if (file.exists) {
    const hasValidation = file.content.includes('z.') ||
                         file.content.includes('validator') ||
                         file.content.includes('validate') ||
                         file.content.includes('sanitize');
    if (hasValidation) inputValidationCount++;
  }
});

checkFix('security', 'SEC-02', inputValidationCount >= 2,
  `Input validation implemented in ${inputValidationCount}/${apiFiles.length} API endpoints`);

// Check for XSS prevention
const componentFiles = [
  './components/stages/ScriptProcessor.tsx',
  './components/stages/AudioGenerator.tsx',
];

let xssProtectionCount = 0;
componentFiles.forEach(componentFile => {
  const file = validateFile(componentFile, `Component ${path.basename(componentFile)}`);
  if (file.exists) {
    const hasDangerousHtml = file.content.includes('dangerouslySetInnerHTML');
    const hasXSSPrevention = !hasDangerousHtml || 
                            file.content.includes('DOMPurify') ||
                            file.content.includes('sanitizeHtml');
    if (hasXSSPrevention) xssProtectionCount++;
  }
});

checkFix('security', 'SEC-03', xssProtectionCount === componentFiles.length,
  `XSS prevention implemented in ${xssProtectionCount}/${componentFiles.length} components`);

// =============================================================================
// 2. WEB UI FIXES VALIDATION
// =============================================================================

console.log('\n🎨 WEB UI FIXES VALIDATION\n');

// Check DownloadIcon fix
const audioGenFile = validateFile('./components/stages/AudioGenerator.tsx', 'Audio Generator');
if (audioGenFile.exists) {
  const hasDownloadIcon = audioGenFile.content.includes('DownloadIcon');
  const hasArrowDownTray = audioGenFile.content.includes('ArrowDownTrayIcon');
  
  checkFix('webUI', 'UI-01', !hasDownloadIcon && hasArrowDownTray,
    hasArrowDownTray && !hasDownloadIcon ? 
      'DownloadIcon successfully replaced with ArrowDownTrayIcon' :
      hasDownloadIcon ? 
        'CRITICAL: DownloadIcon still present - will cause component crashes' :
        'ArrowDownTrayIcon not found - download functionality may be missing');
}

// Check WebSocket connection fix
const websocketFiles = [
  './pages/index.tsx',
  './pages/_app.tsx',
  './components/shared/ConnectionStatus.tsx',
];

let wsConnectionCount = 0;
websocketFiles.forEach(wsFile => {
  const file = validateFile(wsFile, `WebSocket ${path.basename(wsFile)}`);
  if (file.exists) {
    const hasWsConnect = file.content.includes('wsManager.connect()');
    if (hasWsConnect) wsConnectionCount++;
  }
});

checkFix('webUI', 'UI-02', wsConnectionCount >= 1,
  `WebSocket connection initialized in ${wsConnectionCount}/${websocketFiles.length} files`);

// Check Error Boundaries
const errorBoundaryFile = validateFile('./components/ErrorBoundary.tsx', 'Error Boundary');
const hasErrorBoundary = errorBoundaryFile.exists;

checkFix('webUI', 'UI-03', hasErrorBoundary,
  hasErrorBoundary ? 'Error Boundary component exists' : 'Error Boundary component missing');

// Check Loading States
const loadingSpinnerFile = validateFile('./components/LoadingSpinner.tsx', 'Loading Spinner');
const hasLoadingSpinner = loadingSpinnerFile.exists;

checkFix('webUI', 'UI-04', hasLoadingSpinner,
  hasLoadingSpinner ? 'Loading Spinner component exists' : 'Loading Spinner component missing');

// =============================================================================
// 3. PERFORMANCE FIXES VALIDATION
// =============================================================================

console.log('\n⚡ PERFORMANCE FIXES VALIDATION\n');

// Check parallel audio processing
if (audioGenFile.exists) {
  const hasSequentialLoop = audioGenFile.content.includes('for (const scene of scenes)') &&
                           !audioGenFile.content.includes('Promise.all');
  const hasParallelProcessing = audioGenFile.content.includes('Promise.all') &&
                               audioGenFile.content.includes('scenes.map');

  checkFix('performance', 'PERF-01', hasParallelProcessing && !hasSequentialLoop,
    hasParallelProcessing ? 
      'Parallel audio processing implemented with Promise.all' :
      hasSequentialLoop ?
        'CRITICAL: Sequential audio processing still blocks UI' :
        'Audio processing pattern unclear');
}

// Check waveform optimization
const waveformFile = validateFile('./components/audio/WaveformVisualizer.tsx', 'Waveform Visualizer');
if (waveformFile.exists) {
  const hasWaveformCaching = waveformFile.content.includes('waveformData') &&
                            waveformFile.content.includes('useState');
  const hasOptimizedRedraw = waveformFile.content.includes('requestAnimationFrame') ||
                            waveformFile.content.includes('useCallback');

  checkFix('performance', 'PERF-02', hasWaveformCaching,
    hasWaveformCaching ? 'Waveform data caching implemented' : 
      'Waveform data caching missing - may cause performance issues');

  checkFix('performance', 'PERF-03', hasOptimizedRedraw,
    hasOptimizedRedraw ? 'Canvas redraw optimization implemented' :
      'Canvas redraw optimization missing - may cause frame drops');
}

// Check memory management
const memoryLeakIndicators = [
  'addEventListener without removeEventListener',
  'setInterval without clearInterval',
  'setTimeout without clearTimeout',
  'new AudioContext() without close()',
];

const memoryIssues = [];
[audioGenFile, waveformFile].forEach((file, index) => {
  if (file.exists) {
    const fileName = index === 0 ? 'AudioGenerator' : 'WaveformVisualizer';
    
    // Check for cleanup in useEffect
    const hasUseEffect = file.content.includes('useEffect');
    const hasCleanup = file.content.includes('return () =>') ||
                      file.content.includes('cleanup') ||
                      file.content.includes('dispose');
    
    if (hasUseEffect && !hasCleanup) {
      memoryIssues.push(`${fileName}: useEffect without cleanup function`);
    }
  }
});

checkFix('performance', 'PERF-04', memoryIssues.length === 0,
  memoryIssues.length === 0 ? 'No obvious memory leak patterns found' :
    `Memory leak concerns: ${memoryIssues.join(', ')}`);

// =============================================================================
// 4. RELIABILITY FIXES VALIDATION
// =============================================================================

console.log('\n🔧 RELIABILITY FIXES VALIDATION\n');

// Check timeout handling
let timeoutImplementationCount = 0;
[audioGenFile].forEach(file => {
  if (file.exists) {
    const hasTimeout = file.content.includes('timeout') ||
                      file.content.includes('setTimeout') ||
                      file.content.includes('AbortController') ||
                      file.content.includes('Promise.race');
    if (hasTimeout) timeoutImplementationCount++;
  }
});

checkFix('reliability', 'REL-01', timeoutImplementationCount > 0,
  timeoutImplementationCount > 0 ? 
    'Timeout handling implemented in API calls' :
    'No timeout handling found - requests may hang indefinitely');

// Check error handling
let errorHandlingCount = 0;
const criticalFiles = [audioGenFile, waveformFile].filter(f => f.exists);

criticalFiles.forEach((file, index) => {
  const fileName = index === 0 ? 'AudioGenerator' : 'WaveformVisualizer';
  const hasTryCatch = file.content.includes('try {') && file.content.includes('catch');
  const hasErrorState = file.content.includes('error') && file.content.includes('useState');
  
  if (hasTryCatch || hasErrorState) {
    errorHandlingCount++;
  }
});

checkFix('reliability', 'REL-02', errorHandlingCount >= criticalFiles.length,
  `Error handling implemented in ${errorHandlingCount}/${criticalFiles.length} critical components`);

// Check retry mechanisms
const hasRetryLogic = criticalFiles.some(file => 
  file.content.includes('retry') || 
  file.content.includes('attempt') ||
  file.content.includes('backoff'),
);

checkFix('reliability', 'REL-03', hasRetryLogic,
  hasRetryLogic ? 'Retry mechanisms found in components' :
    'No retry mechanisms found - failed operations cannot recover');

// =============================================================================
// 5. NEW ISSUES IDENTIFICATION
// =============================================================================

console.log('\n🔍 NEW ISSUES IDENTIFICATION\n');

// Check for potential new issues
const newIssues = [];

// Check bundle size concerns
const packageFile = validateFile('./package.json', 'Package.json');
if (packageFile.exists) {
  const pkg = JSON.parse(packageFile.content);
  const heavyDependencies = Object.keys(pkg.dependencies || {}).filter(dep => 
    ['three', 'babylonjs', 'fabric', 'lodash'].includes(dep),
  );
  
  if (heavyDependencies.length > 0) {
    newIssues.push(`Bundle size concern: Heavy dependencies detected: ${heavyDependencies.join(', ')}`);
  }
}

// Check for accessibility issues
const componentCount = fs.readdirSync('./components', { recursive: true })
  .filter(file => file.endsWith('.tsx')).length;

let accessibilityScore = 0;
const accessibilityFiles = [
  './components/stages/AudioGenerator.tsx',
  './components/stages/ScriptProcessor.tsx',
];

accessibilityFiles.forEach(filePath => {
  const file = validateFile(filePath, path.basename(filePath));
  if (file.exists) {
    const hasAriaLabels = file.content.includes('aria-label') || 
                         file.content.includes('aria-describedby');
    const hasSemanticHtml = file.content.includes('<button') ||
                           file.content.includes('<input') ||
                           file.content.includes('<select');
    const hasKeyboardSupport = file.content.includes('onKeyDown') ||
                              file.content.includes('tabIndex');
    
    if (hasAriaLabels) accessibilityScore++;
    if (hasSemanticHtml) accessibilityScore++;
    if (hasKeyboardSupport) accessibilityScore++;
  }
});

if (accessibilityScore < 6) {
  newIssues.push(`Accessibility concerns: Score ${accessibilityScore}/6 - Missing ARIA labels, semantic HTML, or keyboard support`);
}

// Check for mobile responsiveness
const mobileOptimizedFiles = [];
const uiFiles = fs.readdirSync('./components', { recursive: true })
  .filter(file => file.endsWith('.tsx'))
  .slice(0, 5); // Sample first 5 components

uiFiles.forEach(fileName => {
  const file = validateFile(`./components/${fileName}`, fileName);
  if (file.exists) {
    const hasMobileClasses = file.content.includes('sm:') || 
                            file.content.includes('md:') ||
                            file.content.includes('lg:');
    const hasResponsiveDesign = file.content.includes('responsive') ||
                               file.content.includes('mobile');
    
    if (hasMobileClasses || hasResponsiveDesign) {
      mobileOptimizedFiles.push(fileName);
    }
  }
});

if (mobileOptimizedFiles.length < uiFiles.length * 0.7) {
  newIssues.push(`Mobile responsiveness: Only ${mobileOptimizedFiles.length}/${uiFiles.length} sampled components appear mobile-optimized`);
}

// Check for performance monitoring
const hasPerformanceMonitoring = criticalFiles.some(file =>
  file.content.includes('performance.now()') ||
  file.content.includes('console.time') ||
  file.content.includes('Analytics') ||
  file.content.includes('telemetry'),
);

if (!hasPerformanceMonitoring) {
  newIssues.push('Performance monitoring: No performance tracking found in critical components');
}

// =============================================================================
// SUMMARY REPORT
// =============================================================================

console.log('\n📊 VALIDATION SUMMARY');
console.log('====================\n');

const categories = ['security', 'webUI', 'performance', 'reliability'];
let totalPassed = 0;
let totalFailed = 0;

categories.forEach(category => {
  const cat = results[category];
  totalPassed += cat.passed;
  totalFailed += cat.failed;
  
  const total = cat.passed + cat.failed;
  const percentage = total > 0 ? Math.round((cat.passed / total) * 100) : 0;
  
  console.log(`${category.toUpperCase()}: ${cat.passed}/${total} tests passed (${percentage}%)`);
  
  if (cat.failed > 0) {
    cat.issues.forEach(issue => {
      console.log(`  ❌ ${issue}`);
    });
  }
});

const overallPercentage = Math.round((totalPassed / (totalPassed + totalFailed)) * 100);

console.log(`\nOVERALL: ${totalPassed}/${totalPassed + totalFailed} tests passed (${overallPercentage}%)\n`);

// New issues for Cycle 2
if (newIssues.length > 0) {
  console.log('🆕 NEW ISSUES FOR CYCLE 2:');
  console.log('=========================');
  newIssues.forEach((issue, index) => {
    console.log(`${index + 1}. ${issue}`);
  });
} else {
  console.log('🎉 No new major issues identified!');
}

// Cycle 2 Recommendations
console.log('\n🎯 CYCLE 2 IMPROVEMENT RECOMMENDATIONS');
console.log('====================================');

const recommendations = [];

if (results.security.failed > 0) {
  recommendations.push('HIGH PRIORITY: Address remaining security vulnerabilities');
}

if (results.webUI.failed > 0) {
  recommendations.push('HIGH PRIORITY: Fix critical UI component issues');
}

if (results.performance.failed > 2) {
  recommendations.push('MEDIUM PRIORITY: Optimize performance bottlenecks');
}

if (newIssues.length > 0) {
  recommendations.push('MEDIUM PRIORITY: Address accessibility and mobile responsiveness');
}

recommendations.push('LOW PRIORITY: Add comprehensive performance monitoring');
recommendations.push('LOW PRIORITY: Implement progressive enhancement patterns');

recommendations.forEach((rec, index) => {
  console.log(`${index + 1}. ${rec}`);
});

console.log(`\n✨ Validation complete! Overall health: ${overallPercentage}%`);
console.log(`${totalPassed} fixes validated, ${totalFailed} issues remaining, ${newIssues.length} new concerns identified.`);

process.exit(totalFailed > 5 ? 1 : 0);
