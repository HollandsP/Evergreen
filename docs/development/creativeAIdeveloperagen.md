You are a creative AI developer agent. Your job is to design and implement a complete content-generation pipeline for an AI-apocalypse narrative YouTube series. The first video is based on the story "LOG_0002: THE DESCENT". This pipeline should allow modular production of future videos in the same style.

The goal is to automate and scaffold:

1. A complete narration script for the video (5–8 minutes max), based on the Winston Marek survivor log from “The Descent.”
2. Generation of AI voiceovers using ElevenLabs or a stubbed module.
3. Visual prompt templates for Runway Gen-2 or Pika Labs to produce cinematic scenes.
4. Terminal UI animation simulation (text typing, blinking cursors, static transitions).
5. Assembly of visual + audio using DaVinci Resolve project templates or simple FFmpeg automation.
6. Optional CivicGPT glitchy PSA scenes.
7. File organization, metadata management, and export structure for YouTube publishing.

### Deliverables

Please generate the following:

- A structured project folder scaffold with comments:


project/
scripts/log_0002_descent.txt # full episode narration
voice/ # ElevenLabs or TTS audio
video/ # generated video clips
terminal_ui/ # animated logs, prompts
psa/ # CivicGPT video overlays
sfx/ # ambient audio + tones
edit/ # project files for DaVinci or Premiere
export/ # final video output


- A complete script for "The Descent", broken into timestamped segments with speaker cues.
- Python or shell code module to:
  - Slice the script into voiceover chunks
  - Generate TTS from ElevenLabs or stub
  - Create placeholder terminal scenes (e.g. ASCII animation)
  - Overlay audio onto video using FFmpeg
- Prompt templates for Runway Gen-2 or Veo for key scenes:

{
"scene": "rooftop suicide shot, white uniforms, Berlin skyline",
"style": "cinematic, dystopian, glitchy realism",
"camera": "static drone or wide shot",
"audio": "low wind, distant city noise"
}


- Readme file explaining:
  - Required accounts & API keys
  - Installation dependencies (Python libs, SDKs, video editors)
  - How to run each module
  - How to manually add visual overlays or adjust timing
  - How to expand for future stories (e.g. LOG_0003)

### Rules

- Output should be technically sound, but not overly complex — built for a beginner/intermediate indie creator.
- Modular: Each story can reuse the same system.
- Tone: Dystopian, documentary, emotionless but haunting.
- Assume we are building a universe of “recovered video logs” from the AI apocalypse scenario in the “AI 2027: Race” timeline.
- Prioritize clean formatting, reusable code, and clear commentary.
- Begin with the script file and folder scaffold, then walk through tools and modules.

Let me know if any steps require special access, and clearly comment TODOs for API keys or integrations.

