/**
 * Comprehensive prompt template library for Evergreen video generation
 * Based on the Python dalle3_runway_prompts.py library
 */

export interface PromptTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  imagePrompt: string;
  videoPrompt: string;
  tags: string[];
  genre?: string;
  style?: string;
  cameraMovement?: string;
  durationRange?: [number, number];
}

// DALL-E 3 template examples with best practices
export const DALLE_TEMPLATES = {
  // Visual descriptions with style modifiers
  dystopian_cityscape: "A {scene_description}, towering concrete buildings silhouetted against a polluted orange sky, scattered neon signs casting harsh shadows, atmospheric fog rolling between buildings, cinematic wide shot, photorealistic, dramatic lighting, shot on RED camera, high detail",
  
  underground_facility: "A {scene_description}, reinforced concrete walls, harsh fluorescent lighting casting stark shadows, industrial pipes running along the ceiling, heavy security doors, sterile environment, cinematic perspective, professional photography",
  
  corporate_interior: "A {scene_description}, modern corporate office with floor-to-ceiling windows, ergonomic furniture, digital displays, professional lighting, clean composition, minimalist design, high-end photography",
  
  residential_area: "A {scene_description}, suburban neighborhood with tree-lined streets, well-maintained landscaping, peaceful atmosphere, golden hour lighting, natural photography, residential setting",
  
  natural_environment: "A {scene_description}, pristine wilderness, dramatic natural lighting, untouched nature, cinematic nature photography, wide landscape shot, environmental beauty",
  
  industrial_complex: "A {scene_description}, massive industrial facility, complex machinery, warning signs, harsh industrial lighting, gritty photojournalism style, documentary photography"
};

// RunwayML template examples with camera movement
export const RUNWAY_TEMPLATES = {
  // Camera movement starting prompts for cinematic motion
  slow_dolly_forward: "{camera_movement}: Slow dolly forward through {scene_action}. {atmosphere_details}. Cinematic camera movement with professional smoothness",
  
  gentle_pan_reveal: "{camera_movement}: Gentle pan across {scene_action}, revealing {atmosphere_details}. Smooth horizontal movement",
  
  tracking_shot: "{camera_movement}: Steady tracking shot following {scene_action}. {atmosphere_details} with dynamic movement",
  
  slow_zoom_in: "{camera_movement}: Gradual zoom focusing on {scene_action}. {atmosphere_details} with increasing intimacy",
  
  orbital_movement: "{camera_movement}: Circular movement around {scene_action}. {atmosphere_details} revealing multiple perspectives",
  
  floating_drift: "{camera_movement}: Gentle floating camera drift through {scene_action}. {atmosphere_details} with dreamlike quality"
};

// ElevenLabs template examples with emotion tags
export const ELEVENLABS_TEMPLATES = {
  // Emotion tags for better voice synthesis
  excited: "[{emotion}] {dialogue_text} [{pause_or_effect}]",
  whispers: "[{emotion}] {dialogue_text} [{pause_or_effect}]", 
  nervously: "[{emotion}] {dialogue_text} [{pause_or_effect}]",
  calm: "[{emotion}] {dialogue_text} [{pause_or_effect}]",
  urgent: "[{emotion}] {dialogue_text} [{pause_or_effect}]",
  mysterious: "[{emotion}] {dialogue_text} [{pause_or_effect}]"
};

// Comprehensive template categories
export const PROMPT_TEMPLATES: Record<string, PromptTemplate[]> = {
  Horror: [
    {
      id: "horror-abandoned",
      name: "Abandoned Building",
      category: "Horror",
      description: "Creepy abandoned building with atmospheric lighting",
      imagePrompt: "Abandoned industrial building with broken windows, overgrown vegetation creeping through cracks, dim emergency lighting casting eerie shadows, mist rolling across the floor, cinematic wide shot, photorealistic, dramatic chiaroscuro lighting, shot on RED camera",
      videoPrompt: "Slow dolly forward: through the abandoned corridors. Mist swirls mysteriously around broken fixtures, emergency lights flickering intermittently",
      tags: ["horror", "abandoned", "atmospheric", "industrial"],
      genre: "horror",
      style: "cinematic",
      cameraMovement: "dolly",
      durationRange: [5, 10]
    },
    {
      id: "horror-forest",
      name: "Dark Forest",
      category: "Horror", 
      description: "Dense forest with mysterious shadows",
      imagePrompt: "Dense forest with ancient trees towering overhead, mysterious shadows between tree trunks, dappled moonlight filtering through thick canopy, fog creeping along the ground, cinematic nature photography, moody lighting, atmospheric depth",
      videoPrompt: "Slow walk: through the forest path. Moonlight patterns shifting on the ground, gentle breeze moving branches overhead, shadows dancing",
      tags: ["horror", "forest", "shadows", "nature"],
      genre: "horror",
      style: "atmospheric",
      cameraMovement: "walk",
      durationRange: [7, 12]
    }
  ],

  "Sci-Fi": [
    {
      id: "scifi-facility",
      name: "Underground Data Center",
      category: "Sci-Fi",
      description: "Futuristic underground data center with servers",
      imagePrompt: "Vast underground data center, rows of server racks stretching into darkness, blinking status lights creating patterns of red and green, thick cables snaking across the floor, emergency lighting casting an eerie glow, wide establishing shot, cyberpunk aesthetic",
      videoPrompt: "Slow glide: between server racks. Status lights pulsing in sequence, gentle camera movement revealing the scale of the facility, electronic humming atmosphere",
      tags: ["sci-fi", "technology", "underground", "servers"],
      genre: "sci-fi",
      style: "cyberpunk",
      cameraMovement: "glide",
      durationRange: [6, 10]
    },
    {
      id: "scifi-corporate",
      name: "Corporate Control Room",
      category: "Sci-Fi",
      description: "High-tech corporate control room with monitors",
      imagePrompt: "Control room with multiple monitor walls displaying data streams, ergonomic workstations, emergency alert indicators blinking red, backup power providing dim illumination, professional photography, minimalist tech design, high contrast lighting",
      videoPrompt: "Pan across: monitor walls showing scrolling data. Alert lights blinking in rhythm, slight camera shake suggesting system instability, technological tension",
      tags: ["sci-fi", "corporate", "technology", "control"],
      genre: "sci-fi", 
      style: "minimal",
      cameraMovement: "pan",
      durationRange: [5, 8]
    }
  ],

  Documentary: [
    {
      id: "doc-urban",
      name: "Urban Landscape",
      category: "Documentary",
      description: "Realistic urban environment documentation",
      imagePrompt: "Urban cityscape during golden hour, everyday life visible in apartment windows, people going about daily routines, natural lighting, documentary photography style, candid environmental portrait, photojournalistic truthfulness",
      videoPrompt: "Observational pan: across the urban landscape. Natural light shifting as clouds pass, subtle movement of people in windows, real-time documentation",
      tags: ["documentary", "urban", "realistic", "daily-life"],
      genre: "documentary",
      style: "realistic",
      cameraMovement: "pan",
      durationRange: [8, 15]
    },
    {
      id: "doc-industrial", 
      name: "Industrial Documentation",
      category: "Documentary",
      description: "Factory or industrial facility documentation",
      imagePrompt: "Industrial facility with workers in safety gear, complex machinery operations, warning signs and safety protocols clearly visible, available light photography, environmental documentation, authentic workplace conditions",
      videoPrompt: "Steady observation: of industrial operations. Workers moving through safety procedures, machinery operating with rhythmic precision, documentary realism",
      tags: ["documentary", "industrial", "workers", "authentic"],
      genre: "documentary",
      style: "observational", 
      cameraMovement: "static",
      durationRange: [10, 20]
    }
  ],

  Cinematic: [
    {
      id: "cine-rooftop",
      name: "Rooftop Drama",
      category: "Cinematic",
      description: "Dramatic rooftop scene with city backdrop",
      imagePrompt: "Rooftop scene with dramatic city skyline backdrop, golden hour lighting creating warm atmosphere, architectural elements framing the composition, cinematic wide shot, professional cinematography, shallow depth of field, shot on 85mm lens",
      videoPrompt: "Slow crane rise: revealing the city beyond. Golden light shifting across urban landscape, gentle wind movement, cinematic scope and drama",
      tags: ["cinematic", "rooftop", "dramatic", "urban"],
      genre: "drama",
      style: "cinematic",
      cameraMovement: "crane",
      durationRange: [6, 12]
    },
    {
      id: "cine-interior",
      name: "Intimate Interior",
      category: "Cinematic", 
      description: "Intimate interior scene with character focus",
      imagePrompt: "Intimate interior space with soft window lighting, carefully arranged personal objects telling a story, warm color temperature, cinematic composition with rule of thirds, shallow depth of field, emotional atmosphere",
      videoPrompt: "Gentle dolly in: toward the intimate space. Soft lighting creating emotional warmth, subtle character movements, intimate cinematic storytelling",
      tags: ["cinematic", "interior", "intimate", "character"],
      genre: "drama",
      style: "intimate",
      cameraMovement: "dolly",
      durationRange: [4, 8]
    }
  ]
};

// Style modifiers for consistent aesthetics
export const STYLE_MODIFIERS = {
  photorealistic: {
    technical: [
      "shot on RED camera with 85mm lens",
      "professional cinematography with shallow depth of field", 
      "natural lighting with practical light sources",
      "high dynamic range color grading",
      "film grain texture for organic feel"
    ],
    lighting: [
      "golden hour natural lighting",
      "dramatic chiaroscuro lighting", 
      "soft diffused window light",
      "harsh industrial fluorescent lighting",
      "moody tungsten color temperature"
    ],
    composition: [
      "rule of thirds composition",
      "leading lines drawing the eye",
      "symmetrical architectural framing", 
      "asymmetrical dynamic balance",
      "foreground, midground, background layers"
    ]
  },
  
  cinematic: {
    mood: [
      "dystopian science fiction atmosphere",
      "psychological thriller tension",
      "corporate espionage aesthetic", 
      "technological anxiety mood",
      "existential dread undertones"
    ],
    colorGrading: [
      "desaturated color palette with teal and orange accents",
      "high contrast with crushed blacks",
      "cool color temperature suggesting technology",
      "warm practical lights in cold environments", 
      "monochromatic blue-green color scheme"
    ],
    visualStyle: [
      "blade runner inspired visuals",
      "minority report clean futurism",
      "ex machina minimalist tech aesthetic",
      "black mirror contemporary dystopia", 
      "westworld corporate luxury design"
    ]
  }
};

// Camera movement descriptions for RunwayML
export const CAMERA_MOVEMENTS = {
  staticShots: {
    "locked_off": "Camera remains completely stationary, subjects move within frame",
    "subtle_breathing": "Almost imperceptible camera movement, like handheld breathing", 
    "micro_adjustments": "Tiny reframing movements, professional tripod work"
  },
  
  panningMovements: {
    "slow_pan_left": "Gentle horizontal movement from right to left, revealing new elements",
    "slow_pan_right": "Smooth horizontal movement from left to right, following action",
    "reveal_pan": "Pan that uncovers hidden elements or expands the visible area",
    "follow_pan": "Camera pans to track a moving subject across the frame",
    "environmental_pan": "Wide pan showing the full scope of a location"
  },
  
  trackingMovements: {
    "forward_track": "Camera moves steadily forward, creating depth and immersion", 
    "backward_track": "Smooth retreat revealing more of the environment",
    "lateral_track": "Side-to-side movement maintaining distance from subject",
    "arc_track": "Curved movement around a central point or subject",
    "following_track": "Camera tracks behind or alongside moving subjects"
  },
  
  complexMovements: {
    "orbital_movement": "Circular movement around a central subject or object",
    "rising_crane": "Upward movement combined with forward motion",
    "descending_approach": "Downward movement while moving toward subject", 
    "spiral_ascent": "Combination of circular and upward movement",
    "floating_drift": "Gentle, dreamlike movement with multiple axis changes"
  }
};

// Content moderation guidelines
export const MODERATION_GUIDELINES = {
  avoidTerms: [
    "blood", "gore", "weapon", "gun", "knife", "violence", "death",
    "nude", "naked", "sexual", "erotic",
    "drug", "illegal"
  ],
  
  safeAlternatives: {
    "destruction": "decay",
    "conflict": "tension", 
    "danger": "warning",
    "weapon": "tool",
    "death": "ending",
    "violence": "action"
  }
};

/**
 * Get template by category and ID
 */
export function getTemplate(category: string, id: string): PromptTemplate | undefined {
  return PROMPT_TEMPLATES[category]?.find(template => template.id === id);
}

/**
 * Get all templates for a category
 */
export function getTemplatesByCategory(category: string): PromptTemplate[] {
  return PROMPT_TEMPLATES[category] || [];
}

/**
 * Get all available categories
 */
export function getCategories(): string[] {
  return Object.keys(PROMPT_TEMPLATES);
}

/**
 * Search templates by tags or description
 */
export function searchTemplates(query: string): PromptTemplate[] {
  const results: PromptTemplate[] = [];
  const lowerQuery = query.toLowerCase();
  
  Object.values(PROMPT_TEMPLATES).forEach(categoryTemplates => {
    categoryTemplates.forEach(template => {
      if (
        template.name.toLowerCase().includes(lowerQuery) ||
        template.description.toLowerCase().includes(lowerQuery) ||
        template.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
      ) {
        results.push(template);
      }
    });
  });
  
  return results;
}

/**
 * Apply template to base prompt with variable substitution
 */
export function applyTemplate(
  template: PromptTemplate,
  variables: Record<string, string> = {}
): { imagePrompt: string; videoPrompt: string } {
  let imagePrompt = template.imagePrompt;
  let videoPrompt = template.videoPrompt;
  
  // Replace variables in templates
  Object.entries(variables).forEach(([key, value]) => {
    const placeholder = `{${key}}`;
    imagePrompt = imagePrompt.replace(new RegExp(placeholder, 'g'), value);
    videoPrompt = videoPrompt.replace(new RegExp(placeholder, 'g'), value);
  });
  
  return { imagePrompt, videoPrompt };
}

/**
 * Sanitize prompt for content moderation
 */
export function sanitizePrompt(prompt: string): string {
  let sanitized = prompt;
  
  MODERATION_GUIDELINES.avoidTerms.forEach(term => {
    const regex = new RegExp(term, 'gi');
    if (regex.test(sanitized)) {
      const alternative = MODERATION_GUIDELINES.safeAlternatives[term] || 'scene';
      sanitized = sanitized.replace(regex, alternative);
    }
  });
  
  return sanitized;
}

/**
 * Check if prompt is moderation safe
 */
export function isModerationSafe(prompt: string): boolean {
  const lowerPrompt = prompt.toLowerCase();
  return !MODERATION_GUIDELINES.avoidTerms.some(term => 
    lowerPrompt.includes(term.toLowerCase())
  );
}