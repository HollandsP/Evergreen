#!/usr/bin/env node

/**
 * Security Vulnerability Test Suite
 * Tests for common security issues after Cycle 1 fixes
 */

const fs = require('fs');
const path = require('path');

console.log('🛡️  SECURITY VULNERABILITY TEST SUITE');
console.log('=====================================\n');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function securityTest(testName, condition, description, severity = 'MEDIUM') {
  totalTests++;
  const status = condition ? '✅ PASS' : '❌ FAIL';
  const severityColor = severity === 'CRITICAL' ? '🚨' : severity === 'HIGH' ? '⚠️' : '📋';
  
  console.log(`${status} ${severityColor} ${testName}`);
  console.log(`    ${description}`);
  
  if (condition) {
    passedTests++;
  } else {
    failedTests++;
    console.log(`    SEVERITY: ${severity}`);
  }
  console.log('');
  
  return condition;
}

function scanFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return null;
    }
    return fs.readFileSync(filePath, 'utf8');
  } catch (error) {
    return null;
  }
}

// Test 1: Check for eval() usage
console.log('1. EVAL INJECTION VULNERABILITY');
const criticalFiles = [
  './lib/script-parser.ts',
  './pages/api/script/parse.ts',
  './lib/utils.ts',
];

let evalFound = false;
let unsafeEvalFound = false;

criticalFiles.forEach(file => {
  const content = scanFile(file);
  if (content) {
    if (content.includes('eval(')) {
      evalFound = true;
      // Check if it's the unsafe kind
      if (!content.includes('// Safe eval') && !content.includes('safeEval')) {
        unsafeEvalFound = true;
        console.log(`    ⚠️  eval() found in ${file}`);
      }
    }
  }
});

securityTest(
  'EVAL-01', 
  !unsafeEvalFound, 
  unsafeEvalFound ? 
    'Unsafe eval() usage detected - can lead to code injection' :
    'No unsafe eval() usage found',
  'CRITICAL',
);

// Test 2: XSS Prevention
console.log('2. XSS PREVENTION');
const frontendFiles = [
  './components/stages/ScriptProcessor.tsx',
  './components/stages/AudioGenerator.tsx',
  './components/stages/ImageGenerator.tsx',
];

const xssVulnerabilities = [];
frontendFiles.forEach(file => {
  const content = scanFile(file);
  if (content) {
    // Check for dangerous patterns
    if (content.includes('dangerouslySetInnerHTML')) {
      if (!content.includes('DOMPurify') && !content.includes('sanitize')) {
        xssVulnerabilities.push(`${file}: dangerouslySetInnerHTML without sanitization`);
      }
    }
    
    if (content.includes('innerHTML') && !content.includes('textContent')) {
      xssVulnerabilities.push(`${file}: Direct innerHTML usage`);
    }
  }
});

securityTest(
  'XSS-01',
  xssVulnerabilities.length === 0,
  xssVulnerabilities.length === 0 ? 
    'No XSS vulnerabilities detected in frontend components' :
    `XSS vulnerabilities found: ${xssVulnerabilities.join(', ')}`,
  'HIGH',
);

// Test 3: Input Validation
console.log('3. INPUT VALIDATION');
const apiFiles = [
  './pages/api/script/parse.ts',
  './pages/api/audio/generate.ts',
  './pages/api/images/generate.ts',
  './pages/api/videos/generate.ts',
];

let validationCount = 0;
let totalApiFiles = 0;

apiFiles.forEach(file => {
  const content = scanFile(file);
  if (content) {
    totalApiFiles++;
    
    const hasValidation = 
      content.includes('z.') || // Zod validation
      content.includes('joi.') || // Joi validation
      content.includes('validate(') ||
      content.includes('sanitize(') ||
      content.includes('body.trim()') ||
      content.includes('validator.');
    
    if (hasValidation) {
      validationCount++;
    } else {
      console.log(`    ⚠️  No validation found in ${file}`);
    }
  }
});

securityTest(
  'INPUT-01',
  validationCount >= totalApiFiles * 0.8,
  `Input validation implemented in ${validationCount}/${totalApiFiles} API endpoints (${Math.round((validationCount/totalApiFiles)*100)}%)`,
  'HIGH',
);

// Test 4: SQL Injection Prevention
console.log('4. SQL INJECTION PREVENTION');
const dbFiles = [
  './lib/database.ts',
  './pages/api/jobs/index.ts',
  './pages/api/jobs/[id].ts',
];

const sqlInjectionRisks = [];
dbFiles.forEach(file => {
  const content = scanFile(file);
  if (content) {
    // Look for raw SQL without parameterization
    if (content.includes('SELECT ') || content.includes('INSERT ') || content.includes('UPDATE ')) {
      if (!content.includes('?') && !content.includes('$1') && !content.includes('prepare')) {
        sqlInjectionRisks.push(`${file}: Raw SQL queries detected`);
      }
    }
  }
});

securityTest(
  'SQL-01',
  sqlInjectionRisks.length === 0,
  sqlInjectionRisks.length === 0 ?
    'No SQL injection risks detected' :
    `SQL injection risks: ${sqlInjectionRisks.join(', ')}`,
  'CRITICAL',
);

// Test 5: Secrets Exposure
console.log('5. SECRETS EXPOSURE');
const configFiles = [
  './next.config.js',
  './.env',
  './.env.local',
  './.env.example',
];

const secretsExposed = [];
configFiles.forEach(file => {
  const content = scanFile(file);
  if (content && file !== './.env.example') {
    // Look for exposed API keys
    const apiKeyPatterns = [
      /[A-Za-z0-9]{32,}/g, // 32+ char strings (potential API keys)
      /sk-[A-Za-z0-9]{32,}/g, // OpenAI style keys
      /xapi-key-[A-Za-z0-9]+/g, // Custom API key formats
    ];
    
    apiKeyPatterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches && !content.includes('YOUR_API_KEY_HERE') && !content.includes('example')) {
        secretsExposed.push(`${file}: Potential API key exposed`);
      }
    });
  }
});

securityTest(
  'SECRETS-01',
  secretsExposed.length === 0,
  secretsExposed.length === 0 ?
    'No exposed secrets detected in config files' :
    `Potential secrets exposed: ${secretsExposed.join(', ')}`,
  'CRITICAL',
);

// Test 6: File Upload Security
console.log('6. FILE UPLOAD SECURITY');
const uploadFiles = [
  './pages/api/script/upload.ts',
  './components/shared/ImageUploader.tsx',
];

const uploadVulnerabilities = [];
uploadFiles.forEach(file => {
  const content = scanFile(file);
  if (content) {
    // Check for file type validation
    const hasFileTypeCheck = content.includes('mime') || 
                            content.includes('extension') ||
                            content.includes('allowedTypes') ||
                            content.includes('accept=');
    
    const hasSizeLimit = content.includes('maxSize') ||
                        content.includes('fileSize') ||
                        content.includes('MAX_FILE_SIZE');
    
    if (!hasFileTypeCheck) {
      uploadVulnerabilities.push(`${file}: No file type validation`);
    }
    
    if (!hasSizeLimit) {
      uploadVulnerabilities.push(`${file}: No file size limits`);
    }
  }
});

securityTest(
  'UPLOAD-01',
  uploadVulnerabilities.length === 0,
  uploadVulnerabilities.length === 0 ?
    'File upload security measures in place' :
    `Upload vulnerabilities: ${uploadVulnerabilities.join(', ')}`,
  'MEDIUM',
);

// Test 7: CORS Configuration
console.log('7. CORS CONFIGURATION');
const corsFiles = [
  './next.config.js',
  './pages/api/generate.ts',
];

const corsIssues = [];
corsFiles.forEach(file => {
  const content = scanFile(file);
  if (content) {
    // Check for overly permissive CORS
    if (content.includes('Access-Control-Allow-Origin: *') && 
        !content.includes('credentials')) {
      corsIssues.push(`${file}: Overly permissive CORS policy`);
    }
  }
});

securityTest(
  'CORS-01',
  corsIssues.length === 0,
  corsIssues.length === 0 ?
    'CORS configuration appears secure' :
    `CORS issues: ${corsIssues.join(', ')}`,
  'MEDIUM',
);

// Test 8: Rate Limiting
console.log('8. RATE LIMITING');
const highLoadEndpoints = [
  './pages/api/audio/generate.ts',
  './pages/api/images/generate.ts',
  './pages/api/videos/generate.ts',
];

let rateLimitingCount = 0;
highLoadEndpoints.forEach(file => {
  const content = scanFile(file);
  if (content) {
    const hasRateLimit = content.includes('rateLimit') ||
                        content.includes('throttle') ||
                        content.includes('redis') ||
                        content.includes('rateLimiter');
    
    if (hasRateLimit) {
      rateLimitingCount++;
    }
  }
});

securityTest(
  'RATE-01',
  rateLimitingCount > 0,
  rateLimitingCount > 0 ?
    `Rate limiting implemented on ${rateLimitingCount}/${highLoadEndpoints.length} high-load endpoints` :
    'No rate limiting detected on high-load endpoints',
  'MEDIUM',
);

// Summary
console.log('=' .repeat(50));
console.log('📊 SECURITY TEST SUMMARY');
console.log('=' .repeat(50));
console.log(`Total Tests: ${totalTests}`);
console.log(`Passed: ${passedTests} (${Math.round((passedTests/totalTests)*100)}%)`);
console.log(`Failed: ${failedTests} (${Math.round((failedTests/totalTests)*100)}%)`);

if (failedTests === 0) {
  console.log('\n🎉 All security tests passed!');
} else if (failedTests <= 2) {
  console.log('\n✅ Security posture is good with minor issues to address.');
} else if (failedTests <= 4) {
  console.log('\n⚠️  Security posture needs improvement.');
} else {
  console.log('\n🚨 CRITICAL: Multiple security vulnerabilities detected!');
}

console.log('\n🔧 Next Steps for Cycle 2:');
if (failedTests > 0) {
  console.log('1. Address failed security tests immediately');
  console.log('2. Implement missing input validation');
  console.log('3. Add rate limiting to prevent abuse');
  console.log('4. Review and harden file upload mechanisms');
} else {
  console.log('1. Consider adding penetration testing');
  console.log('2. Implement security headers (CSP, HSTS)');
  console.log('3. Add automated security scanning to CI/CD');
}
