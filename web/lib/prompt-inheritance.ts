/**
 * Prompt inheritance system for Evergreen
 * Manages the flow: Script description → DALL-E prompt → RunwayML motion prompt
 */

export interface PromptInheritanceChain {
  storyboard?: {
    description: string;
    sceneType: string;
    metadata?: {
      genre?: string;
      mood?: string;
      timeOfDay?: string;
      location?: string;
    };
  };
  image?: {
    prompt: string;
    inheritedFrom: string;
    isCustom: boolean;
    generated?: {
      imageUrl?: string;
      style?: string;
      dimensions?: string;
    };
  };
  video?: {
    motionPrompt: string;
    inheritedFrom: string;
    isCustom: boolean;
    cameraMovement?: string;
    duration?: number;
    generated?: {
      videoUrl?: string;
      thumbnailUrl?: string;
    };
  };
  audio?: {
    transcript: string;
    voiceSettings?: {
      emotion?: string;
      pace?: string;
      voice?: string;
    };
    generated?: {
      audioUrl?: string;
      duration?: number;
    };
  };
}

export interface InheritanceOptions {
  preserveCustomEdits?: boolean;
  enhanceWithAI?: boolean;
  sceneMetadata?: {
    sceneIndex?: number;
    totalScenes?: number;
    audioDuration?: number;
    previousScene?: string;
    nextScene?: string;
  };
}

/**
 * Create initial inheritance chain from storyboard description
 */
export function createInheritanceChain(
  storyboardDescription: string,
  sceneType: string,
  metadata?: PromptInheritanceChain['storyboard']['metadata']
): PromptInheritanceChain {
  return {
    storyboard: {
      description: storyboardDescription,
      sceneType,
      metadata
    }
  };
}

/**
 * Inherit image prompt from storyboard description
 */
export function inheritImagePrompt(
  chain: PromptInheritanceChain,
  options: InheritanceOptions = {}
): string {
  if (!chain.storyboard) {
    throw new Error('No storyboard description found in inheritance chain');
  }

  const { description, sceneType, metadata } = chain.storyboard;
  
  // Base image prompt from storyboard
  let imagePrompt = description;
  
  // Add scene-specific enhancements
  imagePrompt += ', cinematic composition, high detail, photorealistic';
  
  // Add genre-specific styling
  if (metadata?.genre) {
    const genreStyles = {
      horror: ', dark atmosphere, dramatic shadows, eerie lighting, moody composition',
      'sci-fi': ', futuristic aesthetic, technological elements, clean lines, high contrast',
      documentary: ', natural lighting, realistic setting, authentic details, environmental context',
      cinematic: ', professional cinematography, dramatic lighting, rule of thirds, depth of field'
    };
    
    imagePrompt += genreStyles[metadata.genre as keyof typeof genreStyles] || '';
  }
  
  // Add time of day lighting
  if (metadata?.timeOfDay) {
    const timeStyles = {
      dawn: ', golden hour lighting, soft warm colors, gentle shadows',
      day: ', natural daylight, bright even lighting, clear visibility',
      dusk: ', golden hour lighting, dramatic sky, warm color temperature', 
      night: ', artificial lighting, dramatic shadows, moody atmosphere',
      twilight: ', blue hour lighting, mixed artificial and natural light'
    };
    
    imagePrompt += timeStyles[metadata.timeOfDay as keyof typeof timeStyles] || '';
  }
  
  // Add location-specific details
  if (metadata?.location) {
    const locationStyles = {
      indoor: ', interior lighting, architectural details, spatial depth',
      outdoor: ', environmental context, natural elements, atmospheric perspective',
      urban: ', city environment, architectural elements, human activity',
      rural: ', natural landscape, organic textures, peaceful atmosphere',
      industrial: ', functional design, utilitarian aesthetic, harsh lighting'
    };
    
    imagePrompt += locationStyles[metadata.location as keyof typeof locationStyles] || '';
  }
  
  // Add DALL-E 3 optimization
  imagePrompt += ', shot on RED camera, professional photography, 16:9 aspect ratio';
  
  // Ensure length doesn't exceed DALL-E 3 limits (4000 characters)
  if (imagePrompt.length > 4000) {
    imagePrompt = imagePrompt.substring(0, 3997) + '...';
  }
  
  return imagePrompt;
}

/**
 * Inherit video motion prompt from image prompt and storyboard
 */
export function inheritVideoPrompt(
  chain: PromptInheritanceChain,
  options: InheritanceOptions = {}
): string {
  if (!chain.storyboard) {
    throw new Error('No storyboard description found in inheritance chain');
  }
  
  const { sceneType, metadata } = chain.storyboard;
  const audioDuration = options.sceneMetadata?.audioDuration || 5;
  
  // Generate camera movement based on scene type and duration
  let cameraMovement = getCameraMovementForScene(sceneType, audioDuration);
  
  // Create action description from storyboard
  let sceneAction = extractActionFromStoryboard(chain.storyboard.description);
  
  // Create atmosphere details
  let atmosphereDetails = createAtmosphereDescription(metadata);
  
  // Build RunwayML prompt starting with camera movement
  let videoPrompt = `${cameraMovement}: ${sceneAction}. ${atmosphereDetails}`;
  
  // Add duration-specific enhancements
  if (audioDuration < 3) {
    videoPrompt += '. Quick dynamic movement, high impact visual, immediate focus';
  } else if (audioDuration > 8) {
    videoPrompt += '. Slow deliberate movement, complex environmental details, extended atmosphere';
  } else {
    videoPrompt += '. Smooth professional movement, balanced pacing, cinematic flow';
  }
  
  // Add genre-specific camera work
  if (metadata?.genre) {
    const genreCameraWork = {
      horror: '. Unsettling camera movement, building tension, ominous atmosphere',
      'sci-fi': '. Precise technical movement, futuristic smoothness, clean camera work',
      documentary: '. Natural handheld feel, observational movement, realistic pacing',
      cinematic: '. Professional camera operation, dramatic reveals, artistic composition'
    };
    
    videoPrompt += genreCameraWork[metadata.genre as keyof typeof genreCameraWork] || '';
  }
  
  // Ensure length is appropriate for RunwayML (800 character limit)
  if (videoPrompt.length > 800) {
    videoPrompt = videoPrompt.substring(0, 797) + '...';
  }
  
  return videoPrompt;
}

/**
 * Update inheritance chain with custom edits
 */
export function updateInheritanceChain(
  chain: PromptInheritanceChain,
  stage: 'image' | 'video',
  customPrompt: string,
  isCustom: boolean = true
): PromptInheritanceChain {
  const updatedChain = { ...chain };
  
  if (stage === 'image') {
    updatedChain.image = {
      prompt: customPrompt,
      inheritedFrom: isCustom ? 'custom edit' : 'storyboard description',
      isCustom
    };
  } else if (stage === 'video') {
    updatedChain.video = {
      motionPrompt: customPrompt,
      inheritedFrom: isCustom ? 'custom edit' : chain.image ? 'image prompt' : 'storyboard description',
      isCustom
    };
  }
  
  return updatedChain;
}

/**
 * Get inheritance indicators for UI display
 */
export function getInheritanceIndicators(chain: PromptInheritanceChain) {
  return {
    image: {
      hasInheritance: !!chain.storyboard,
      source: chain.image?.inheritedFrom || 'storyboard description',
      isCustom: chain.image?.isCustom || false
    },
    video: {
      hasInheritance: !!(chain.storyboard || chain.image),
      source: chain.video?.inheritedFrom || (chain.image ? 'image prompt' : 'storyboard description'),
      isCustom: chain.video?.isCustom || false
    }
  };
}

/**
 * Helper: Get appropriate camera movement for scene type and duration
 */
function getCameraMovementForScene(sceneType: string, duration: number): string {
  const sceneMovements = {
    // Static/calm scenes
    'office': duration < 5 ? 'Slow dolly forward' : 'Gentle tracking shot',
    'residential': 'Slow pan across',
    'interior': 'Subtle dolly in',
    
    // Dynamic scenes  
    'cityscape': 'Sweeping pan revealing',
    'rooftop': 'Rising crane shot',
    'underground': 'Forward tracking through',
    
    // Atmospheric scenes
    'forest': 'Floating drift through',
    'facility': 'Steady glide between',
    'industrial': 'Orbiting movement around'
  };
  
  // Find matching scene type
  const movement = Object.entries(sceneMovements).find(([key]) => 
    sceneType.toLowerCase().includes(key.toLowerCase())
  )?.[1];
  
  return movement || 'Smooth camera movement through';
}

/**
 * Helper: Extract action elements from storyboard description
 */
function extractActionFromStoryboard(description: string): string {
  // Remove technical camera terms and focus on subject/action
  let action = description
    .replace(/cinematic|photorealistic|shot on|professional|high detail/gi, '')
    .replace(/\s+/g, ' ')
    .trim();
  
  // If too long, take first part
  if (action.length > 100) {
    action = action.substring(0, 97) + '...';
  }
  
  return action || 'the scene environment';
}

/**
 * Helper: Create atmosphere description from metadata
 */
function createAtmosphereDescription(metadata?: PromptInheritanceChain['storyboard']['metadata']): string {
  const elements = [];
  
  if (metadata?.mood) {
    const moodDescriptions = {
      tense: 'tension building in the air',
      calm: 'peaceful atmosphere',
      mysterious: 'enigmatic shadows and lighting',
      dramatic: 'intense atmospheric drama',
      eerie: 'unsettling environmental details'
    };
    elements.push(moodDescriptions[metadata.mood as keyof typeof moodDescriptions] || metadata.mood);
  }
  
  if (metadata?.timeOfDay) {
    const timeAtmospheres = {
      dawn: 'golden morning light warming the scene',
      day: 'clear natural lighting throughout',
      dusk: 'warm evening light creating depth',
      night: 'dramatic artificial lighting',
      twilight: 'transitional lighting between day and night'
    };
    elements.push(timeAtmospheres[metadata.timeOfDay as keyof typeof timeAtmospheres] || '');
  }
  
  return elements.length > 0 ? elements.join(', ') : 'atmospheric environmental details';
}

/**
 * Validate inheritance chain completeness
 */
export function validateInheritanceChain(chain: PromptInheritanceChain): {
  isValid: boolean;
  missingStages: string[];
  warnings: string[];
} {
  const missingStages: string[] = [];
  const warnings: string[] = [];
  
  if (!chain.storyboard) {
    missingStages.push('storyboard');
  }
  
  if (!chain.image && chain.storyboard) {
    warnings.push('Image prompt not yet generated from storyboard');
  }
  
  if (!chain.video && (chain.image || chain.storyboard)) {
    warnings.push('Video motion prompt not yet generated');
  }
  
  return {
    isValid: missingStages.length === 0,
    missingStages,
    warnings
  };
}

/**
 * Export inheritance chain for API use
 */
export function exportInheritanceChain(chain: PromptInheritanceChain) {
  return {
    storyboard: chain.storyboard?.description || '',
    imagePrompt: chain.image?.prompt || '',
    videoPrompt: chain.video?.motionPrompt || '',
    metadata: {
      sceneType: chain.storyboard?.sceneType || '',
      inheritanceMap: getInheritanceIndicators(chain),
      customizations: {
        imageCustom: chain.image?.isCustom || false,
        videoCustom: chain.video?.isCustom || false
      }
    }
  };
}