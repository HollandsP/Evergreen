import type { NextApiRequest, NextApiResponse } from 'next';
import { 
  getProductionState, 
  updateProductionStage, 
  setCurrentStage,
  canProceedToStage,
  resetProductionState,
  getProductionProgress,
  validateProductionState,
  ProductionStage,
  ProductionState,
} from '@/lib/production-state';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version',
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    switch (req.method) {
      case 'GET':
        // Get current production state
        const state = getProductionState();
        const progress = getProductionProgress();
        const validation = validateProductionState();
        
        res.status(200).json({
          state,
          progress,
          validation,
          timestamp: new Date().toISOString(),
        });
        break;

      case 'POST':
        // Update production state
        const { stage, updates, action } = req.body;
        
        if (action === 'reset') {
          resetProductionState();
          res.status(200).json({ 
            message: 'Production state reset successfully',
            state: getProductionState(),
          });
          break;
        }
        
        if (action === 'setStage') {
          const { targetStage } = req.body;
          if (!targetStage || !['script', 'voice', 'audio', 'images', 'video', 'assembly'].includes(targetStage)) {
            res.status(400).json({ error: 'Invalid stage' });
            return;
          }
          
          if (!canProceedToStage(targetStage as ProductionStage)) {
            res.status(400).json({ 
              error: 'Cannot proceed to this stage',
              message: 'Previous stages must be completed first',
            });
            return;
          }
          
          setCurrentStage(targetStage as ProductionStage);
          res.status(200).json({ 
            message: 'Stage updated successfully',
            currentStage: targetStage,
          });
          break;
        }
        
        if (!stage || !updates) {
          res.status(400).json({ error: 'Missing stage or updates' });
          return;
        }
        
        // Validate stage
        const validStages = ['script', 'voice', 'audio', 'images', 'video', 'assembly'];
        if (!validStages.includes(stage)) {
          res.status(400).json({ error: 'Invalid stage' });
          return;
        }
        
        // Update the specific stage
        updateProductionStage(stage as keyof ProductionState, updates);
        
        // Send WebSocket notification
        if (global.io) {
          global.io.emit('production:stateUpdate', {
            stage,
            updates,
            timestamp: new Date().toISOString(),
          });
        }
        
        res.status(200).json({ 
          message: 'State updated successfully',
          stage,
          updates,
        });
        break;

      case 'PUT':
        // Import complete state
        const { state: importedState } = req.body;
        
        if (!importedState) {
          res.status(400).json({ error: 'Missing state data' });
          return;
        }
        
        try {
          // This would need to be implemented in production-state.ts
          // For now, we'll update each stage individually
          Object.keys(importedState).forEach((key) => {
            if (key !== 'currentStage' && key !== 'isLocked' && key !== 'lastSaved' && key !== 'projectId') {
              updateProductionStage(key as keyof ProductionState, importedState[key]);
            }
          });
          
          res.status(200).json({ 
            message: 'State imported successfully',
            state: getProductionState(),
          });
        } catch (error) {
          res.status(400).json({ error: 'Invalid state format' });
        }
        break;

      default:
        res.setHeader('Allow', ['GET', 'POST', 'PUT']);
        res.status(405).end(`Method ${req.method} Not Allowed`);
    }
  } catch (error) {
    console.error('Production state API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
