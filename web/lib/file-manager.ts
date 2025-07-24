/**
 * Centralized File Manager for Evergreen AI Video Pipeline
 * 
 * Manages project folder structure, scene organization, and file paths
 * Ensures consistent file organization across all pipeline stages
 */

import path from 'path';
import fs from 'fs/promises';

export interface ProjectMetadata {
  id: string;
  title: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status: 'draft' | 'processing' | 'completed' | 'failed';
  scenes: SceneMetadata[];
  settings?: {
    targetPlatform?: 'youtube' | 'tiktok' | 'instagram';
    videoFormat?: string;
    audioFormat?: string;
  };
}

export interface SceneMetadata {
  id: string;
  sceneNumber: number;
  title: string;
  description?: string;
  text: string;
  speaker?: string;
  duration?: number;
  assets: {
    images: string[];
    audio: string[];
    videos: string[];
  };
  prompts?: {
    image?: string;
    audio?: string;
    video?: string;
  };
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

export class ProjectFileManager {
  private basePath: string;

  constructor(basePath?: string) {
    // Use environment variable or default path
    this.basePath = basePath || process.env.PROJECT_BASE_PATH || path.join(process.cwd(), 'projects');
  }

  /**
   * Get the base projects directory
   */
  getBasePath(): string {
    return this.basePath;
  }

  /**
   * Get project directory path
   */
  getProjectPath(projectId: string): string {
    return path.join(this.basePath, projectId);
  }

  /**
   * Get scene directory path
   */
  getScenePath(projectId: string, sceneId: string): string {
    return path.join(this.getProjectPath(projectId), 'scenes', sceneId);
  }

  /**
   * Get asset directory path for a specific type
   */
  getAssetPath(projectId: string, sceneId: string, assetType: 'images' | 'audio' | 'videos'): string {
    return path.join(this.getScenePath(projectId, sceneId), assetType);
  }

  /**
   * Get full file path for a specific asset
   */
  getAssetFilePath(projectId: string, sceneId: string, assetType: 'images' | 'audio' | 'videos', filename: string): string {
    return path.join(this.getAssetPath(projectId, sceneId, assetType), filename);
  }

  /**
   * Get project metadata file path
   */
  getMetadataPath(projectId: string): string {
    return path.join(this.getProjectPath(projectId), 'metadata.json');
  }

  /**
   * Get export directory path
   */
  getExportPath(projectId: string): string {
    return path.join(this.getProjectPath(projectId), 'exports');
  }

  /**
   * Create project folder structure
   */
  async createProjectStructure(projectId: string, sceneCount: number): Promise<void> {
    const projectPath = this.getProjectPath(projectId);
    
    // Create main project directory
    await fs.mkdir(projectPath, { recursive: true });
    
    // Create scenes directory
    const scenesPath = path.join(projectPath, 'scenes');
    await fs.mkdir(scenesPath, { recursive: true });
    
    // Create export directory
    await fs.mkdir(this.getExportPath(projectId), { recursive: true });
    
    // Create scene directories
    for (let i = 1; i <= sceneCount; i++) {
      const sceneId = `scene_${i.toString().padStart(3, '0')}`;
      const scenePath = path.join(scenesPath, sceneId);
      
      // Create scene directory with asset subdirectories
      await fs.mkdir(path.join(scenePath, 'images'), { recursive: true });
      await fs.mkdir(path.join(scenePath, 'audio'), { recursive: true });
      await fs.mkdir(path.join(scenePath, 'videos'), { recursive: true });
    }
  }

  /**
   * Save project metadata
   */
  async saveProjectMetadata(projectId: string, metadata: ProjectMetadata): Promise<void> {
    const metadataPath = this.getMetadataPath(projectId);
    
    // Update timestamp
    metadata.updatedAt = new Date().toISOString();
    
    // Save metadata
    await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2), 'utf-8');
  }

  /**
   * Load project metadata
   */
  async loadProjectMetadata(projectId: string): Promise<ProjectMetadata | null> {
    try {
      const metadataPath = this.getMetadataPath(projectId);
      const data = await fs.readFile(metadataPath, 'utf-8');
      return JSON.parse(data) as ProjectMetadata;
    } catch (error) {
      console.error(`Failed to load metadata for project ${projectId}:`, error);
      return null;
    }
  }

  /**
   * Update scene metadata
   */
  async updateSceneMetadata(projectId: string, sceneId: string, updates: Partial<SceneMetadata>): Promise<void> {
    const metadata = await this.loadProjectMetadata(projectId);
    if (!metadata) {
      throw new Error(`Project metadata not found for ${projectId}`);
    }

    // Find and update scene
    const sceneIndex = metadata.scenes.findIndex(s => s.id === sceneId);
    if (sceneIndex === -1) {
      throw new Error(`Scene ${sceneId} not found in project ${projectId}`);
    }

    metadata.scenes[sceneIndex] = {
      ...metadata.scenes[sceneIndex],
      ...updates
    };

    await this.saveProjectMetadata(projectId, metadata);
  }

  /**
   * Add asset to scene
   */
  async addAssetToScene(
    projectId: string, 
    sceneId: string, 
    assetType: 'images' | 'audio' | 'videos', 
    filename: string
  ): Promise<void> {
    const metadata = await this.loadProjectMetadata(projectId);
    if (!metadata) {
      throw new Error(`Project metadata not found for ${projectId}`);
    }

    const scene = metadata.scenes.find(s => s.id === sceneId);
    if (!scene) {
      throw new Error(`Scene ${sceneId} not found in project ${projectId}`);
    }

    // Add asset to scene metadata
    if (!scene.assets[assetType].includes(filename)) {
      scene.assets[assetType].push(filename);
      await this.saveProjectMetadata(projectId, metadata);
    }
  }

  /**
   * Get all projects
   */
  async getAllProjects(): Promise<string[]> {
    try {
      const entries = await fs.readdir(this.basePath, { withFileTypes: true });
      return entries
        .filter(entry => entry.isDirectory())
        .map(entry => entry.name);
    } catch (error) {
      console.error('Failed to get projects:', error);
      return [];
    }
  }

  /**
   * Delete project and all its files
   */
  async deleteProject(projectId: string): Promise<void> {
    const projectPath = this.getProjectPath(projectId);
    await fs.rm(projectPath, { recursive: true, force: true });
  }

  /**
   * Check if project exists
   */
  async projectExists(projectId: string): Promise<boolean> {
    try {
      const projectPath = this.getProjectPath(projectId);
      await fs.access(projectPath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get scene files
   */
  async getSceneFiles(projectId: string, sceneId: string, assetType?: 'images' | 'audio' | 'videos'): Promise<string[]> {
    try {
      if (assetType) {
        const assetPath = this.getAssetPath(projectId, sceneId, assetType);
        const files = await fs.readdir(assetPath);
        return files.filter(f => !f.startsWith('.'));
      }

      // Get all files from all asset types
      const allFiles: string[] = [];
      const assetTypes: Array<'images' | 'audio' | 'videos'> = ['images', 'audio', 'videos'];
      
      for (const type of assetTypes) {
        const assetPath = this.getAssetPath(projectId, sceneId, type);
        try {
          const files = await fs.readdir(assetPath);
          allFiles.push(...files.filter(f => !f.startsWith('.')));
        } catch (error) {
          // Directory might not exist yet
          console.warn(`Asset directory ${assetPath} not found`);
        }
      }

      return allFiles;
    } catch (error) {
      console.error(`Failed to get scene files for ${projectId}/${sceneId}:`, error);
      return [];
    }
  }

  /**
   * Clean up empty directories
   */
  async cleanupEmptyDirectories(projectId: string): Promise<void> {
    const projectPath = this.getProjectPath(projectId);
    
    async function removeEmptyDirs(dir: string): Promise<boolean> {
      try {
        const files = await fs.readdir(dir);
        
        if (files.length === 0) {
          await fs.rmdir(dir);
          return true;
        }

        let hasFiles = false;
        for (const file of files) {
          const fullPath = path.join(dir, file);
          const stat = await fs.stat(fullPath);
          
          if (stat.isDirectory()) {
            const isEmpty = await removeEmptyDirs(fullPath);
            if (!isEmpty) hasFiles = true;
          } else {
            hasFiles = true;
          }
        }

        if (!hasFiles && dir !== projectPath) {
          await fs.rmdir(dir);
          return true;
        }

        return false;
      } catch (error) {
        console.error(`Error cleaning directory ${dir}:`, error);
        return false;
      }
    }

    await removeEmptyDirs(projectPath);
  }
}

// Export singleton instance
export const fileManager = new ProjectFileManager();

// Export default
export default fileManager;