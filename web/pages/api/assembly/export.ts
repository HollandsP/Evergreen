import { NextApiRequest, NextApiResponse } from 'next';
import formidable from 'formidable';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

const execAsync = promisify(exec);

export const config = {
  api: {
    bodyParser: false, // Disable body parser for file uploads
  },
};

interface TimelineItem {
  sceneId: string;
  startTime: number;
  duration: number;
  transition: 'cut' | 'fade' | 'dissolve' | 'wipe';
  transitionDuration: number;
  audioUrl?: string;
  imageUrl?: string;
  videoUrl?: string;
  narration?: string;
  onScreenText?: string;
}

interface ExportData {
  timeline: TimelineItem[];
  settings: {
    format: 'mp4' | 'mov' | 'webm';
    resolution: '4K' | '1080p' | '720p';
    frameRate: 24 | 30 | 60;
    quality: 'high' | 'medium' | 'low';
    includeBackgroundMusic: boolean;
    musicVolume: number;
    narrationVolume: number;
  };
  totalDuration: number;
  projectId?: string;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const jobId = uuidv4();
  const outputDir = path.join(process.cwd(), 'public', 'exports', jobId);
  
  try {
    // Create output directory
    await fs.mkdir(outputDir, { recursive: true });

    // Parse multipart form data
    const form = formidable({
      uploadDir: outputDir,
      keepExtensions: true,
    });

    const [fields, files] = await form.parse(req);
    const exportDataString = Array.isArray(fields.exportData) ? fields.exportData[0] : fields.exportData;
    if (!exportDataString) {
      throw new Error('Export data is required');
    }
    const exportData: ExportData = JSON.parse(exportDataString as string);
    const backgroundMusic = files.backgroundMusic?.[0];

    // Prepare FFmpeg command based on export settings
    const outputFile = path.join(outputDir, `video.${exportData.settings.format}`);
    const tempDir = path.join(outputDir, 'temp');
    await fs.mkdir(tempDir, { recursive: true });

    // Resolution mapping
    const resolutionMap = {
      '4K': '3840x2160',
      '1080p': '1920x1080',
      '720p': '1280x720',
    };

    // Quality preset mapping
    const qualityMap = {
      high: { preset: 'slow', crf: 18 },
      medium: { preset: 'medium', crf: 23 },
      low: { preset: 'fast', crf: 28 },
    };

    // Step 1: Create video segments for each timeline item
    const videoSegments: string[] = [];
    
    for (let i = 0; i < exportData.timeline.length; i++) {
      const item = exportData.timeline[i];
      const segmentFile = path.join(tempDir, `segment_${i}.mp4`);
      
      if (item.videoUrl) {
        // Use existing video
        const videoPath = item.videoUrl.startsWith('http') 
          ? await downloadFile(item.videoUrl, tempDir)
          : item.videoUrl;
          
        // Trim and scale video to match duration and resolution
        await execAsync(`ffmpeg -i "${videoPath}" -t ${item.duration} -vf "scale=${resolutionMap[exportData.settings.resolution]}" -c:v libx264 -preset fast -c:a copy "${segmentFile}"`);
      } else if (item.imageUrl) {
        // Create video from image
        const imagePath = item.imageUrl.startsWith('http')
          ? await downloadFile(item.imageUrl, tempDir)
          : item.imageUrl;
          
        // Generate video from still image
        await execAsync(`ffmpeg -loop 1 -i "${imagePath}" -t ${item.duration} -vf "scale=${resolutionMap[exportData.settings.resolution]}" -c:v libx264 -preset fast -pix_fmt yuv420p "${segmentFile}"`);
      } else {
        // Create black video placeholder
        await execAsync(`ffmpeg -f lavfi -i "color=c=black:s=${resolutionMap[exportData.settings.resolution]}:d=${item.duration}" -c:v libx264 -preset fast "${segmentFile}"`);
      }
      
      // Add transition if not the first segment
      if (i > 0 && item.transition !== 'cut') {
        const transitionFile = path.join(tempDir, `transition_${i}.mp4`);
        await applyTransition(
          videoSegments[videoSegments.length - 1],
          segmentFile,
          transitionFile,
          item.transition,
          item.transitionDuration,
        );
        videoSegments[videoSegments.length - 1] = transitionFile;
      }
      
      videoSegments.push(segmentFile);
    }

    // Step 2: Create concat list
    const concatList = path.join(tempDir, 'concat.txt');
    const concatContent = videoSegments.map(segment => `file '${segment}'`).join('\n');
    await fs.writeFile(concatList, concatContent);

    // Step 3: Concatenate all video segments
    const concatenatedVideo = path.join(tempDir, 'concatenated.mp4');
    await execAsync(`ffmpeg -f concat -safe 0 -i "${concatList}" -c copy "${concatenatedVideo}"`);

    // Step 4: Process audio
    let finalCommand = `ffmpeg -i "${concatenatedVideo}"`;
    
    // Add narration audio if available
    const audioFiles: string[] = [];
    for (const item of exportData.timeline) {
      if (item.audioUrl) {
        const audioPath = item.audioUrl.startsWith('http')
          ? await downloadFile(item.audioUrl, tempDir)
          : item.audioUrl;
        audioFiles.push(audioPath);
      }
    }
    
    if (audioFiles.length > 0) {
      // Concatenate audio files
      const audioConcat = path.join(tempDir, 'narration.mp3');
      const audioConcatList = path.join(tempDir, 'audio_concat.txt');
      const audioConcatContent = audioFiles.map(audio => `file '${audio}'`).join('\n');
      await fs.writeFile(audioConcatList, audioConcatContent);
      await execAsync(`ffmpeg -f concat -safe 0 -i "${audioConcatList}" -c copy "${audioConcat}"`);
      
      finalCommand += ` -i "${audioConcat}"`;
    }
    
    // Add background music if provided
    if (backgroundMusic && exportData.settings.includeBackgroundMusic) {
      finalCommand += ` -i "${backgroundMusic.filepath}"`;
    }
    
    // Build filter complex for audio mixing
    let filterComplex = '';
    // let audioInputs = 1; // Start at 1 because video is input 0
    
    if (audioFiles.length > 0 && backgroundMusic && exportData.settings.includeBackgroundMusic) {
      // Mix narration and background music
      const narrationVolume = exportData.settings.narrationVolume / 100;
      const musicVolume = exportData.settings.musicVolume / 100;
      filterComplex = `-filter_complex "[1]volume=${narrationVolume}[narration];[2]volume=${musicVolume}[music];[narration][music]amix=inputs=2:duration=shortest[aout]" -map 0:v -map "[aout]"`;
    } else if (audioFiles.length > 0) {
      // Just narration
      const narrationVolume = exportData.settings.narrationVolume / 100;
      filterComplex = `-filter_complex "[1]volume=${narrationVolume}[aout]" -map 0:v -map "[aout]"`;
    } else if (backgroundMusic && exportData.settings.includeBackgroundMusic) {
      // Just background music
      const musicVolume = exportData.settings.musicVolume / 100;
      filterComplex = `-filter_complex "[1]volume=${musicVolume}[aout]" -map 0:v -map "[aout]"`;
    } else {
      // No audio
      filterComplex = '-map 0:v';
    }
    
    // Add output parameters
    const { preset, crf } = qualityMap[exportData.settings.quality];
    finalCommand += ` ${filterComplex} -c:v libx264 -preset ${preset} -crf ${crf} -r ${exportData.settings.frameRate} -pix_fmt yuv420p`;
    
    if (filterComplex.includes('[aout]')) {
      finalCommand += ' -c:a aac -b:a 192k';
    }
    
    finalCommand += ` -movflags +faststart "${outputFile}"`;
    
    // Execute final encoding
    console.log('Executing FFmpeg command:', finalCommand);
    await execAsync(finalCommand);
    
    // Clean up temp files
    await fs.rm(tempDir, { recursive: true, force: true });
    
    // Return download URL
    const downloadUrl = `/exports/${jobId}/video.${exportData.settings.format}`;
    
    res.status(200).json({
      jobId,
      downloadUrl,
      fileSize: (await fs.stat(outputFile)).size,
      duration: exportData.totalDuration,
    });
    
  } catch (error) {
    console.error('Export error:', error);
    
    // Clean up on error
    try {
      await fs.rm(outputDir, { recursive: true, force: true });
    } catch (cleanupError) {
      console.error('Cleanup error:', cleanupError);
    }
    
    res.status(500).json({
      error: 'Export failed',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

// Helper function to download files
async function downloadFile(url: string, outputDir: string): Promise<string> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to download ${url}`);
  
  const buffer = await response.arrayBuffer();
  const filename = path.join(outputDir, `download_${Date.now()}_${path.basename(url)}`);
  await fs.writeFile(filename, Buffer.from(buffer));
  
  return filename;
}

// Helper function to apply transitions
async function applyTransition(
  prevVideo: string,
  nextVideo: string,
  outputFile: string,
  transition: string,
  duration: number,
): Promise<void> {
  let filter = '';
  
  switch (transition) {
    case 'fade':
      filter = `[0:v]fade=t=out:st=${duration}:d=${duration}:alpha=1[v0];[1:v]fade=t=in:st=0:d=${duration}:alpha=1[v1];[v0][v1]overlay[outv]`;
      break;
    case 'dissolve':
      filter = `[0:v][1:v]xfade=transition=dissolve:duration=${duration}:offset=0[outv]`;
      break;
    case 'wipe':
      filter = `[0:v][1:v]xfade=transition=wipeleft:duration=${duration}:offset=0[outv]`;
      break;
    default:
      // Cut - just copy
      await fs.copyFile(nextVideo, outputFile);
      return;
  }
  
  await execAsync(`ffmpeg -i "${prevVideo}" -i "${nextVideo}" -filter_complex "${filter}" -map "[outv]" -c:v libx264 -preset fast "${outputFile}"`);
}
