import { NextApiRequest, NextApiResponse } from 'next';
import { promises as fs } from 'fs';
import path from 'path';

interface FolderStructure {
  name: string;
  path: string;
  type: 'folder' | 'file';
  children?: FolderStructure[];
  metadata?: {
    createdAt: string;
    updatedAt: string;
    size?: number;
  };
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { projectId } = req.query;

  if (!projectId || typeof projectId !== 'string') {
    return res.status(400).json({ error: 'Invalid project ID' });
  }

  const projectPath = path.join(process.cwd(), 'public', 'exports', projectId);

  switch (req.method) {
    case 'GET':
      return getFolderStructure(req, res, projectPath);
    case 'POST':
      return createSceneFolder(req, res, projectPath);
    case 'DELETE':
      return deleteFolder(req, res, projectPath);
    default:
      return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function getFolderStructure(
  _req: NextApiRequest,
  res: NextApiResponse,
  projectPath: string
): Promise<void> {
  try {
    const structure = await buildFolderStructure(projectPath);
    res.status(200).json(structure);
  } catch (error) {
    console.error('Error reading folder structure:', error);
    res.status(500).json({ error: 'Failed to read folder structure' });
  }
}

async function buildFolderStructure(folderPath: string): Promise<FolderStructure> {
  const stats = await fs.stat(folderPath).catch(() => null);
  
  if (!stats) {
    // Create project folder if it doesn't exist
    await fs.mkdir(folderPath, { recursive: true });
    return {
      name: path.basename(folderPath),
      path: folderPath,
      type: 'folder',
      children: [],
      metadata: {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    };
  }

  const folderName = path.basename(folderPath);
  const structure: FolderStructure = {
    name: folderName,
    path: folderPath,
    type: 'folder',
    children: [],
    metadata: {
      createdAt: stats.birthtime.toISOString(),
      updatedAt: stats.mtime.toISOString()
    }
  };

  if (stats.isDirectory()) {
    const items = await fs.readdir(folderPath);
    const children = await Promise.all(
      items.map(async (item) => {
        const itemPath = path.join(folderPath, item);
        const itemStats = await fs.stat(itemPath);

        if (itemStats.isDirectory()) {
          return buildFolderStructure(itemPath);
        } else {
          return {
            name: item,
            path: itemPath,
            type: 'file' as const,
            metadata: {
              createdAt: itemStats.birthtime.toISOString(),
              updatedAt: itemStats.mtime.toISOString(),
              size: itemStats.size
            }
          };
        }
      })
    );

    structure.children = children.sort((a, b) => {
      // Sort folders first, then files
      if (a.type !== b.type) {
        return a.type === 'folder' ? -1 : 1;
      }
      // Sort by name
      return a.name.localeCompare(b.name);
    });
  }

  return structure;
}

async function createSceneFolder(
  req: NextApiRequest,
  res: NextApiResponse,
  projectPath: string
): Promise<void> {
  try {
    const { sceneId, sceneName } = req.body;

    if (!sceneId) {
      return res.status(400).json({ error: 'Scene ID is required' });
    }

    const sceneFolderName = sceneName || sceneId;
    const scenePath = path.join(projectPath, sceneFolderName);

    // Create scene folder structure
    const folders = ['images', 'audio', 'videos', 'metadata'];
    
    for (const folder of folders) {
      const folderPath = path.join(scenePath, folder);
      await fs.mkdir(folderPath, { recursive: true });
    }

    // Create scene metadata file
    const metadataPath = path.join(scenePath, 'metadata', 'scene.json');
    const metadata = {
      id: sceneId,
      name: sceneName,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'created',
      assets: {
        images: [],
        audio: [],
        videos: []
      }
    };

    await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));

    res.status(201).json({
      message: 'Scene folder created successfully',
      path: scenePath,
      metadata
    });
  } catch (error) {
    console.error('Error creating scene folder:', error);
    res.status(500).json({ error: 'Failed to create scene folder' });
  }
}

async function deleteFolder(
  req: NextApiRequest,
  res: NextApiResponse,
  projectPath: string
): Promise<void> {
  try {
    const { scenePath } = req.body;

    if (!scenePath) {
      return res.status(400).json({ error: 'Scene path is required' });
    }

    // Security check: ensure the path is within the project directory
    const fullPath = path.join(projectPath, scenePath);
    const normalizedPath = path.normalize(fullPath);
    const normalizedProjectPath = path.normalize(projectPath);

    if (!normalizedPath.startsWith(normalizedProjectPath)) {
      return res.status(403).json({ error: 'Invalid path' });
    }

    // Delete the folder recursively
    await fs.rm(normalizedPath, { recursive: true, force: true });

    res.status(200).json({ message: 'Folder deleted successfully' });
  } catch (error) {
    console.error('Error deleting folder:', error);
    res.status(500).json({ error: 'Failed to delete folder' });
  }
}

// Configuration for larger payload sizes
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
  },
};