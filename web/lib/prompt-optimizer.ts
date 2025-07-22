/**
 * Prompt optimization for DALL-E 3 based on dalle3_runway_prompts.py
 * Flux.1 support removed due to high subscription costs
 */

// Removed unused interfaces

// Base style for all images
const BASE_STYLE = 'cinematic, high contrast, moody lighting, 16:9 aspect ratio, photorealistic';

// Scene-specific styles based on the Python prompt library
const SCENE_STYLES: Record<string, string> = {
  'cold_open': 'dark, mysterious, terminal green glow, dystopian atmosphere',
  'terminal': 'retro computer terminal, green phosphor text, dark background, CRT monitor effects',
  'office': 'modern office, futuristic tech, clean minimal design, corporate aesthetic',
  'rooftop': 'dramatic sky, urban cityscape, ethereal lighting, golden hour',
  'outro': 'distorted, glitchy, unsettling, digital corruption effects',
  'underground': 'industrial, harsh fluorescent lighting, concrete walls, sterile environment',
  'corporate': 'professional lighting, minimalist design, glass and steel, high-end photography',
  'residential': 'natural lighting, lived-in atmosphere, warm tones, suburban setting',
  'industrial': 'gritty, harsh lighting, machinery, warning signs, documentary style',
  'dystopian': 'polluted sky, neon signs, abandoned vehicles, atmospheric fog',
};

// Lighting modifiers from the Python library
const LIGHTING_MODIFIERS = [
  'golden hour natural lighting',
  'dramatic chiaroscuro lighting',
  'soft diffused window light',
  'harsh industrial fluorescent lighting',
  'moody tungsten color temperature',
  'neon lights in urban darkness',
  'high dynamic range color grading',
];

// Composition techniques
const COMPOSITION_MODIFIERS = [
  'rule of thirds composition',
  'leading lines drawing the eye',
  'symmetrical architectural framing',
  'asymmetrical dynamic balance',
  'foreground, midground, background layers',
  'wide establishing shot',
  'cinematic perspective',
];

// Camera movements (for video prompt hints)
const CAMERA_MOVEMENTS = {
  static: 'locked off shot, minimal camera movement',
  pan: 'slow horizontal pan revealing environment',
  tilt: 'gradual vertical tilt showing scale',
  track: 'smooth tracking shot following action',
  zoom: 'subtle zoom focusing attention',
  drift: 'gentle floating camera movement',
};

// Color grading options (unused)
// const COLOR_GRADING = [
//   'desaturated color palette with teal and orange accents',
//   'high contrast with crushed blacks',
//   'cool color temperature suggesting technology',
//   'warm practical lights in cold environments',
//   'monochromatic blue-green color scheme'
// ];

export function optimizePrompt(
  basePrompt: string,
  sceneType: string,
  audioDuration?: number,
): string {
  let optimizedPrompt = basePrompt;
  
  // Find matching scene style
  const sceneKey = Object.keys(SCENE_STYLES).find(key => 
    sceneType.toLowerCase().includes(key),
  );
  
  const sceneStyle = sceneKey ? SCENE_STYLES[sceneKey] : '';
  
  // Add base style
  optimizedPrompt = `${optimizedPrompt}, ${BASE_STYLE}`;
  
  // Add scene-specific style
  if (sceneStyle) {
    optimizedPrompt = `${optimizedPrompt}, ${sceneStyle}`;
  }
  
  // Add duration-based enhancements
  if (audioDuration) {
    if (audioDuration < 3) {
      optimizedPrompt += ', dramatic composition, high impact visual, immediate focal point';
    } else if (audioDuration > 8) {
      optimizedPrompt += ', highly detailed environment, rich textures, complex layered scene';
    } else {
      optimizedPrompt += ', balanced composition, clear subject focus';
    }
  }
  
  // Add random lighting modifier for variety
  const lighting = LIGHTING_MODIFIERS[Math.floor(Math.random() * LIGHTING_MODIFIERS.length)];
  optimizedPrompt += `, ${lighting}`;
  
  // Add composition technique
  const composition = COMPOSITION_MODIFIERS[Math.floor(Math.random() * COMPOSITION_MODIFIERS.length)];
  optimizedPrompt += `, ${composition}`;
  
  // DALL-E 3 optimizations - responds well to detailed descriptions
  optimizedPrompt += ', professional photography, high detail, sharp focus, shot on RED camera';
  
  return optimizedPrompt;
}

export function enhanceWithGenre(prompt: string, genre: string): string {
  const genreEnhancements: Record<string, string> = {
    'dystopian_cityscape': 'towering concrete buildings, polluted orange sky, neon signs, abandoned vehicles',
    'underground_facility': 'reinforced concrete walls, industrial pipes, security doors, sterile environment',
    'corporate_interior': 'modern office space, ergonomic furniture, floor-to-ceiling windows, minimalist design',
    'residential_area': 'suburban houses, tree-lined streets, well-maintained lawns, peaceful atmosphere',
    'natural_environment': 'pristine wilderness, untouched nature, dramatic natural lighting',
    'industrial_complex': 'massive machinery, cooling towers, warning signs, harsh industrial setting',
  };
  
  const enhancement = genreEnhancements[genre];
  return enhancement ? `${prompt}, ${enhancement}` : prompt;
}

export function addTransitionEffects(prompt: string, transitionType: string): string {
  const transitions: Record<string, string> = {
    'time_passage': 'showing passage of time, lighting changes, temporal progression',
    'location_change': 'establishing shot, spatial orientation, new environment reveal',
    'scale_change': 'dramatic scale shift, perspective change, zoom transition',
    'emotional_shift': 'mood transformation, color temperature change, atmosphere evolution',
  };
  
  const effect = transitions[transitionType];
  return effect ? `${prompt}, ${effect}` : prompt;
}

export function sanitizePrompt(prompt: string): string {
  // Content moderation based on the Python library guidelines
  const avoidTerms = [
    'blood', 'gore', 'weapon', 'gun', 'knife', 'violence', 'death',
    'nude', 'naked', 'sexual', 'erotic',
    'drug', 'illegal',
  ];
  
  let sanitized = prompt.toLowerCase();
  
  // Check for problematic terms
  for (const term of avoidTerms) {
    if (sanitized.includes(term)) {
      console.warn(`Prompt contains potentially problematic term: ${term}`);
      // Replace with safer alternatives
      sanitized = sanitized.replace(term, getSafeAlternative(term));
    }
  }
  
  return sanitized;
}

function getSafeAlternative(term: string): string {
  const alternatives: Record<string, string> = {
    'destruction': 'decay',
    'conflict': 'tension',
    'danger': 'warning',
    'weapon': 'tool',
    'death': 'ending',
    'violence': 'action',
  };
  
  return alternatives[term] || 'scene';
}

// Export camera movement suggestions for video generation hints
export function getCameraMovementHint(sceneType: string, duration: number): string {
  if (duration < 3) {
    return CAMERA_MOVEMENTS.static;
  } else if (sceneType.includes('office') || sceneType.includes('interior')) {
    return CAMERA_MOVEMENTS.track;
  } else if (sceneType.includes('cityscape') || sceneType.includes('rooftop')) {
    return CAMERA_MOVEMENTS.pan;
  } else if (sceneType.includes('terminal')) {
    return CAMERA_MOVEMENTS.zoom;
  } else {
    return CAMERA_MOVEMENTS.drift;
  }
}

// Main export function that combines all optimizations
export function generateOptimizedPrompt(
  basePrompt: string,
  options: {
    sceneType?: string;
    genre?: string;
    audioDuration?: number;
    provider?: 'dalle3'; // Only DALL-E 3 supported (Flux.1 removed due to cost)
    transitionType?: string;
  } = {},
): string {
  let prompt = basePrompt;
  
  // Apply optimizations in order
  if (options.sceneType) {
    prompt = optimizePrompt(prompt, options.sceneType, options.audioDuration);
  }
  
  if (options.genre) {
    prompt = enhanceWithGenre(prompt, options.genre);
  }
  
  if (options.transitionType) {
    prompt = addTransitionEffects(prompt, options.transitionType);
  }
  
  // Always sanitize
  prompt = sanitizePrompt(prompt);
  
  // Ensure prompt doesn't exceed length limits
  const maxLength = options.provider === 'dalle3' ? 4000 : 2000;
  if (prompt.length > maxLength) {
    prompt = prompt.substring(0, maxLength - 3) + '...';
  }
  
  return prompt;
}
