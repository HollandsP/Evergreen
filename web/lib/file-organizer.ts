/**
 * File Organization System for Scene-Based Media Management
 * Creates and manages folder structures for storing images, audio, video, and metadata by scene
 */

import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';

export interface SceneAsset {
  id: string;
  type: 'image' | 'audio' | 'video' | 'metadata';
  url: string;
  filename: string;
  size: number;
  mimeType: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface SceneFolder {
  sceneId: string;
  projectId: string;
  basePath: string;
  folders: {
    images: string;
    audio: string;
    videos: string;
    metadata: string;
    exports: string;
  };
  assets: SceneAsset[];
  manifest: {
    createdAt: string;
    updatedAt: string;
    totalAssets: number;
    totalSize: number;
    completionStatus: {
      hasImages: boolean;
      hasAudio: boolean;
      hasVideos: boolean;
    };
  };
}

export interface ProjectStructure {
  projectId: string;
  title: string;
  basePath: string;
  scenes: SceneFolder[];
  globalAssets: {
    scripts: string;
    exports: string;
    backups: string;
  };
  projectManifest: {
    createdAt: string;
    updatedAt: string;
    totalScenes: number;
    totalAssets: number;
    totalSize: number;
  };
}

export class FileOrganizer {
  private basePath: string;
  private projectStructures = new Map<string, ProjectStructure>();

  constructor(basePath: string = path.join(process.cwd(), 'public', 'projects')) {
    this.basePath = basePath;
  }

  /**
   * Initialize project folder structure
   */
  async initializeProject(
    projectId: string,
    title: string,
    sceneIds: string[]
  ): Promise<ProjectStructure> {
    const projectPath = path.join(this.basePath, projectId);
    
    // Create main project folders
    const globalAssets = {
      scripts: path.join(projectPath, 'scripts'),
      exports: path.join(projectPath, 'exports'),
      backups: path.join(projectPath, 'backups')
    };

    await this.ensureDirectoryExists(projectPath);
    await Promise.all(
      Object.values(globalAssets).map(dir => this.ensureDirectoryExists(dir))
    );

    // Initialize scene folders
    const scenes: SceneFolder[] = [];
    for (const sceneId of sceneIds) {
      const sceneFolder = await this.initializeSceneFolder(projectId, sceneId);
      scenes.push(sceneFolder);
    }

    const structure: ProjectStructure = {
      projectId,
      title,
      basePath: projectPath,
      scenes,
      globalAssets,
      projectManifest: {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        totalScenes: scenes.length,
        totalAssets: 0,
        totalSize: 0
      }
    };

    // Save project manifest
    await this.saveProjectManifest(structure);
    this.projectStructures.set(projectId, structure);

    console.log(`Initialized project structure for ${title} with ${sceneIds.length} scenes`);
    return structure;
  }

  /**
   * Initialize individual scene folder structure
   */
  async initializeSceneFolder(projectId: string, sceneId: string): Promise<SceneFolder> {
    const scenePath = path.join(this.basePath, projectId, 'scenes', sceneId);
    
    const folders = {
      images: path.join(scenePath, 'images'),
      audio: path.join(scenePath, 'audio'),
      videos: path.join(scenePath, 'videos'),
      metadata: path.join(scenePath, 'metadata'),
      exports: path.join(scenePath, 'exports')
    };

    // Create all scene folders
    await Promise.all(
      Object.values(folders).map(dir => this.ensureDirectoryExists(dir))
    );

    const sceneFolder: SceneFolder = {
      sceneId,
      projectId,
      basePath: scenePath,
      folders,
      assets: [],
      manifest: {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        totalAssets: 0,
        totalSize: 0,
        completionStatus: {
          hasImages: false,
          hasAudio: false,
          hasVideos: false
        }
      }
    };

    // Save scene manifest
    await this.saveSceneManifest(sceneFolder);
    return sceneFolder;
  }

  /**
   * Store asset file and update scene structure
   */
  async storeAsset(
    projectId: string,
    sceneId: string,
    assetType: 'image' | 'audio' | 'video' | 'metadata',
    fileData: Buffer | string,
    originalFilename: string,
    metadata?: Record<string, any>
  ): Promise<SceneAsset> {
    const project = await this.getOrLoadProject(projectId);
    const scene = project.scenes.find(s => s.sceneId === sceneId);
    
    if (!scene) {
      throw new Error(`Scene ${sceneId} not found in project ${projectId}`);
    }

    // Generate unique filename
    const extension = path.extname(originalFilename);
    const basename = path.basename(originalFilename, extension);
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const uniqueId = crypto.randomBytes(4).toString('hex');
    const filename = `${basename}_${timestamp}_${uniqueId}${extension}`;

    // Determine target folder and MIME type
    const targetFolder = scene.folders[`${assetType}s` as keyof typeof scene.folders];
    const filepath = path.join(targetFolder, filename);
    const mimeType = this.getMimeType(extension, assetType);

    // Write file
    if (Buffer.isBuffer(fileData)) {
      await fs.writeFile(filepath, fileData);
    } else {
      await fs.writeFile(filepath, fileData, 'utf8');
    }

    // Get file stats
    const stats = await fs.stat(filepath);
    
    // Create asset record
    const asset: SceneAsset = {
      id: crypto.randomUUID(),
      type: assetType,
      url: this.getPublicUrl(filepath),
      filename,
      size: stats.size,
      mimeType,
      timestamp: new Date().toISOString(),
      metadata
    };

    // Update scene
    scene.assets.push(asset);
    scene.manifest.totalAssets++;
    scene.manifest.totalSize += stats.size;
    scene.manifest.updatedAt = new Date().toISOString();
    
    // Update completion status
    this.updateCompletionStatus(scene);

    // Save updated manifests
    await this.saveSceneManifest(scene);
    await this.updateProjectManifest(project);

    console.log(`Stored ${assetType} asset: ${filename} (${stats.size} bytes)`);
    return asset;
  }

  /**
   * Store asset from URL (download and store locally)
   */
  async storeAssetFromUrl(
    projectId: string,
    sceneId: string,
    assetType: 'image' | 'audio' | 'video',
    url: string,
    metadata?: Record<string, any>
  ): Promise<SceneAsset> {
    try {
      // Download the file
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download asset: ${response.statusText}`);
      }

      const buffer = Buffer.from(await response.arrayBuffer());
      const filename = this.extractFilenameFromUrl(url, assetType);

      return await this.storeAsset(
        projectId,
        sceneId,
        assetType,
        buffer,
        filename,
        { ...metadata, originalUrl: url }
      );
    } catch (error) {
      console.error(`Failed to store asset from URL ${url}:`, error);
      throw error;
    }
  }

  /**
   * Get scene assets with filtering options
   */
  async getSceneAssets(
    projectId: string,
    sceneId: string,
    filters?: {
      type?: 'image' | 'audio' | 'video' | 'metadata';
      after?: string; // timestamp
      before?: string; // timestamp
    }
  ): Promise<SceneAsset[]> {
    const project = await this.getOrLoadProject(projectId);
    const scene = project.scenes.find(s => s.sceneId === sceneId);
    
    if (!scene) {
      throw new Error(`Scene ${sceneId} not found`);
    }

    let assets = [...scene.assets];

    if (filters) {
      if (filters.type) {
        assets = assets.filter(asset => asset.type === filters.type);
      }
      if (filters.after) {
        assets = assets.filter(asset => asset.timestamp > filters.after!);
      }
      if (filters.before) {
        assets = assets.filter(asset => asset.timestamp < filters.before!);
      }
    }

    return assets.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  }

  /**
   * Get project structure and stats
   */
  async getProjectStructure(projectId: string): Promise<ProjectStructure> {
    return await this.getOrLoadProject(projectId);
  }

  /**
   * Get scene completion status
   */
  async getSceneCompletionStatus(projectId: string, sceneId: string): Promise<{
    hasImages: boolean;
    hasAudio: boolean;
    hasVideos: boolean;
    completionPercentage: number;
    totalAssets: number;
  }> {
    const project = await this.getOrLoadProject(projectId);
    const scene = project.scenes.find(s => s.sceneId === sceneId);
    
    if (!scene) {
      throw new Error(`Scene ${sceneId} not found`);
    }

    const status = scene.manifest.completionStatus;
    const completionPercentage = [
      status.hasImages,
      status.hasAudio,
      status.hasVideos
    ].filter(Boolean).length / 3 * 100;

    return {
      ...status,
      completionPercentage,
      totalAssets: scene.manifest.totalAssets
    };
  }

  /**
   * Clean up old or unused assets
   */
  async cleanupProject(
    projectId: string,
    options: {
      removeOlderThan?: number; // days
      removeUnusedAssets?: boolean;
      dryRun?: boolean;
    } = {}
  ): Promise<{
    removedFiles: string[];
    reclaimedSpace: number;
    errors: string[];
  }> {
    const project = await this.getOrLoadProject(projectId);
    const removedFiles: string[] = [];
    const errors: string[] = [];
    let reclaimedSpace = 0;

    const cutoffDate = options.removeOlderThan 
      ? new Date(Date.now() - options.removeOlderThan * 24 * 60 * 60 * 1000).toISOString()
      : null;

    for (const scene of project.scenes) {
      for (let i = scene.assets.length - 1; i >= 0; i--) {
        const asset = scene.assets[i];
        let shouldRemove = false;

        // Check age criterion
        if (cutoffDate && asset.timestamp < cutoffDate) {
          shouldRemove = true;
        }

        // Check if file actually exists
        const filepath = this.getLocalPath(asset.url);
        try {
          await fs.access(filepath);
        } catch {
          // File doesn't exist, remove from records
          shouldRemove = true;
        }

        if (shouldRemove && !options.dryRun) {
          try {
            await fs.unlink(filepath);
            reclaimedSpace += asset.size;
            removedFiles.push(asset.filename);
            scene.assets.splice(i, 1);
          } catch (error) {
            errors.push(`Failed to remove ${asset.filename}: ${error}`);
          }
        }
      }

      if (!options.dryRun && removedFiles.length > 0) {
        this.updateCompletionStatus(scene);
        await this.saveSceneManifest(scene);
      }
    }

    if (!options.dryRun && removedFiles.length > 0) {
      await this.updateProjectManifest(project);
    }

    return { removedFiles, reclaimedSpace, errors };
  }

  /**
   * Export scene assets as a package
   */
  async exportScene(
    projectId: string,
    sceneId: string,
    exportFormat: 'zip' | 'tar' = 'zip'
  ): Promise<string> {
    const scene = await this.getSceneFolder(projectId, sceneId);
    const exportPath = path.join(scene.folders.exports, `scene_${sceneId}_${Date.now()}.${exportFormat}`);
    
    // This would implement actual zip/tar creation
    // For now, return the export path where the package would be created
    console.log(`Would export scene ${sceneId} to ${exportPath}`);
    return exportPath;
  }

  // Private helper methods

  private async getOrLoadProject(projectId: string): Promise<ProjectStructure> {
    if (this.projectStructures.has(projectId)) {
      return this.projectStructures.get(projectId)!;
    }

    return await this.loadProjectFromDisk(projectId);
  }

  private async loadProjectFromDisk(projectId: string): Promise<ProjectStructure> {
    const projectPath = path.join(this.basePath, projectId);
    const manifestPath = path.join(projectPath, 'project-manifest.json');

    try {
      const manifestData = await fs.readFile(manifestPath, 'utf8');
      const structure = JSON.parse(manifestData) as ProjectStructure;
      
      // Load scene data
      for (const scene of structure.scenes) {
        const sceneManifestPath = path.join(scene.folders.metadata, 'scene-manifest.json');
        try {
          const sceneData = await fs.readFile(sceneManifestPath, 'utf8');
          const sceneManifest = JSON.parse(sceneData);
          Object.assign(scene, sceneManifest);
        } catch (error) {
          console.warn(`Failed to load scene manifest for ${scene.sceneId}:`, error);
        }
      }

      this.projectStructures.set(projectId, structure);
      return structure;
    } catch (error) {
      throw new Error(`Failed to load project ${projectId}: ${error}`);
    }
  }

  private async getSceneFolder(projectId: string, sceneId: string): Promise<SceneFolder> {
    const project = await this.getOrLoadProject(projectId);
    const scene = project.scenes.find(s => s.sceneId === sceneId);
    
    if (!scene) {
      throw new Error(`Scene ${sceneId} not found in project ${projectId}`);
    }

    return scene;
  }

  private async ensureDirectoryExists(dirPath: string): Promise<void> {
    try {
      await fs.mkdir(dirPath, { recursive: true });
    } catch (error) {
      if ((error as any).code !== 'EEXIST') {
        throw error;
      }
    }
  }

  private async saveProjectManifest(structure: ProjectStructure): Promise<void> {
    const manifestPath = path.join(structure.basePath, 'project-manifest.json');
    await fs.writeFile(manifestPath, JSON.stringify(structure, null, 2));
  }

  private async saveSceneManifest(scene: SceneFolder): Promise<void> {
    const manifestPath = path.join(scene.folders.metadata, 'scene-manifest.json');
    await fs.writeFile(manifestPath, JSON.stringify(scene, null, 2));
  }

  private async updateProjectManifest(project: ProjectStructure): Promise<void> {
    project.projectManifest.updatedAt = new Date().toISOString();
    project.projectManifest.totalAssets = project.scenes.reduce(
      (sum, scene) => sum + scene.manifest.totalAssets, 0
    );
    project.projectManifest.totalSize = project.scenes.reduce(
      (sum, scene) => sum + scene.manifest.totalSize, 0
    );
    
    await this.saveProjectManifest(project);
  }

  private updateCompletionStatus(scene: SceneFolder): void {
    scene.manifest.completionStatus = {
      hasImages: scene.assets.some(a => a.type === 'image'),
      hasAudio: scene.assets.some(a => a.type === 'audio'),
      hasVideos: scene.assets.some(a => a.type === 'video')
    };
    scene.manifest.totalAssets = scene.assets.length;
    scene.manifest.totalSize = scene.assets.reduce((sum, asset) => sum + asset.size, 0);
  }

  private getMimeType(extension: string, assetType: string): string {
    const mimeMap: Record<string, string> = {
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif',
      '.webp': 'image/webp',
      '.mp3': 'audio/mpeg',
      '.wav': 'audio/wav',
      '.ogg': 'audio/ogg',
      '.mp4': 'video/mp4',
      '.webm': 'video/webm',
      '.mov': 'video/quicktime',
      '.json': 'application/json',
      '.txt': 'text/plain'
    };

    return mimeMap[extension.toLowerCase()] || `${assetType}/*`;
  }

  private getPublicUrl(filepath: string): string {
    // Convert absolute file path to public URL
    const relativePath = path.relative(path.join(process.cwd(), 'public'), filepath);
    return '/' + relativePath.replace(/\\/g, '/'); // Normalize path separators
  }

  private getLocalPath(url: string): string {
    // Convert public URL back to local file path
    const relativePath = url.startsWith('/') ? url.slice(1) : url;
    return path.join(process.cwd(), 'public', relativePath);
  }

  private extractFilenameFromUrl(url: string, assetType: string): string {
    try {
      const urlObj = new URL(url);
      const pathname = urlObj.pathname;
      const filename = path.basename(pathname);
      
      if (filename && filename.includes('.')) {
        return filename;
      }
      
      // Generate filename based on asset type and timestamp
      const extension = this.getDefaultExtension(assetType);
      return `${assetType}_${Date.now()}${extension}`;
    } catch {
      const extension = this.getDefaultExtension(assetType);
      return `${assetType}_${Date.now()}${extension}`;
    }
  }

  private getDefaultExtension(assetType: string): string {
    const extensions = {
      image: '.jpg',
      audio: '.mp3',
      video: '.mp4',
      metadata: '.json'
    };
    return extensions[assetType as keyof typeof extensions] || '.bin';
  }
}

// Export singleton instance
export const fileOrganizer = new FileOrganizer();
export default fileOrganizer;