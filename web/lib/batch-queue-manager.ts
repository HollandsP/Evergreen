/**
 * Intelligent batch processing queue system
 * Optimizes API calls, manages resources, and handles failures gracefully
 */

import EventEmitter from 'events';

export interface BatchJob {
  id: string;
  type: 'image' | 'video' | 'audio' | 'script';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  data: any;
  retryCount: number;
  maxRetries: number;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  failedAt?: Date;
  error?: string;
  dependencies?: string[];
  estimatedDuration?: number;
  costEstimate?: number;
}

export interface BatchJobResult {
  success: boolean;
  data?: any;
  error?: string;
  duration: number;
  cost?: number;
}

interface QueueConfig {
  maxConcurrentJobs: number;
  maxBatchSize: number;
  batchTimeoutMs: number;
  retryDelayMs: number;
  priorityWeights: Record<string, number>;
  resourceLimits: {
    maxMemoryMB: number;
    maxCostPerHour: number;
  };
}

interface QueueStats {
  totalJobs: number;
  completedJobs: number;
  failedJobs: number;
  activeJobs: number;
  queuedJobs: number;
  averageProcessingTime: number;
  totalCost: number;
  costPerHour: number;
  successRate: number;
}

interface ProcessorFunction {
  (jobs: BatchJob[]): Promise<BatchJobResult[]>;
}

interface ResourceUsage {
  memoryMB: number;
  costPerHour: number;
  activeConnections: number;
}

export class IntelligentBatchQueueManager extends EventEmitter {
  private queues = new Map<string, BatchJob[]>();
  private processingJobs = new Map<string, BatchJob>();
  private completedJobs = new Map<string, BatchJob>();
  private processors = new Map<string, ProcessorFunction>();
  private config: QueueConfig;
  private stats: QueueStats;
  private resourceUsage: ResourceUsage;
  private batchTimer?: NodeJS.Timeout;
  private isProcessing = false;

  constructor(config: Partial<QueueConfig> = {}) {
    super();
    
    this.config = {
      maxConcurrentJobs: 5,
      maxBatchSize: 10,
      batchTimeoutMs: 5000,
      retryDelayMs: 1000,
      priorityWeights: {
        urgent: 4,
        high: 3,
        medium: 2,
        low: 1
      },
      resourceLimits: {
        maxMemoryMB: 2048,
        maxCostPerHour: 50
      },
      ...config
    };

    this.stats = {
      totalJobs: 0,
      completedJobs: 0,
      failedJobs: 0,
      activeJobs: 0,
      queuedJobs: 0,
      averageProcessingTime: 0,
      totalCost: 0,
      costPerHour: 0,
      successRate: 0
    };

    this.resourceUsage = {
      memoryMB: 0,
      costPerHour: 0,
      activeConnections: 0
    };

    this.startBatchProcessing();
    this.startResourceMonitoring();
  }

  /**
   * Register a processor function for a specific job type
   */
  registerProcessor(jobType: string, processor: ProcessorFunction): void {
    this.processors.set(jobType, processor);
  }

  /**
   * Add a job to the queue with intelligent prioritization
   */
  async addJob(job: Omit<BatchJob, 'id' | 'createdAt' | 'retryCount'>): Promise<string> {
    const jobId = this.generateJobId();
    const fullJob: BatchJob = {
      id: jobId,
      retryCount: 0,
      createdAt: new Date(),
      ...job
    };

    // Check dependencies
    if (fullJob.dependencies) {
      const pendingDeps = fullJob.dependencies.filter(depId => 
        !this.completedJobs.has(depId)
      );
      
      if (pendingDeps.length > 0) {
        fullJob.priority = 'low'; // Lower priority until dependencies complete
      }
    }

    // Add to appropriate queue
    if (!this.queues.has(fullJob.type)) {
      this.queues.set(fullJob.type, []);
    }

    const queue = this.queues.get(fullJob.type)!;
    queue.push(fullJob);

    // Sort queue by priority and creation time
    queue.sort((a, b) => {
      const priorityDiff = this.config.priorityWeights[b.priority] - this.config.priorityWeights[a.priority];
      if (priorityDiff !== 0) return priorityDiff;
      return a.createdAt.getTime() - b.createdAt.getTime();
    });

    this.updateStats();
    this.emit('jobQueued', fullJob);

    console.log(`Job ${jobId} added to ${fullJob.type} queue with priority ${fullJob.priority}`);
    return jobId;
  }

  /**
   * Add multiple jobs as a batch
   */
  async addBatch(jobs: Array<Omit<BatchJob, 'id' | 'createdAt' | 'retryCount'>>): Promise<string[]> {
    const jobIds: string[] = [];
    
    for (const job of jobs) {
      const jobId = await this.addJob(job);
      jobIds.push(jobId);
    }

    return jobIds;
  }

  /**
   * Get job status
   */
  getJobStatus(jobId: string): { status: 'queued' | 'processing' | 'completed' | 'failed' | 'not_found'; job?: BatchJob } {
    // Check completed first
    if (this.completedJobs.has(jobId)) {
      const job = this.completedJobs.get(jobId)!;
      const status = job.failedAt ? 'failed' : 'completed';
      return { status, job };
    }

    // Check processing
    if (this.processingJobs.has(jobId)) {
      return { status: 'processing', job: this.processingJobs.get(jobId) };
    }

    // Check queues
    for (const queue of this.queues.values()) {
      const job = queue.find(j => j.id === jobId);
      if (job) {
        return { status: 'queued', job };
      }
    }

    return { status: 'not_found' };
  }

  /**
   * Cancel a job
   */
  async cancelJob(jobId: string): Promise<boolean> {
    // Remove from queues
    for (const [type, queue] of this.queues.entries()) {
      const index = queue.findIndex(job => job.id === jobId);
      if (index !== -1) {
        queue.splice(index, 1);
        this.updateStats();
        this.emit('jobCancelled', jobId);
        return true;
      }
    }

    // If it's processing, mark for cancellation
    if (this.processingJobs.has(jobId)) {
      const job = this.processingJobs.get(jobId)!;
      job.error = 'Cancelled by user';
      this.emit('jobCancelled', jobId);
      return true;
    }

    return false;
  }

  /**
   * Get queue statistics
   */
  getStats(): QueueStats & { 
    resourceUsage: ResourceUsage;
    queueSizes: Record<string, number>;
    estimatedWaitTime: number;
  } {
    const queueSizes: Record<string, number> = {};
    let totalQueued = 0;

    for (const [type, queue] of this.queues.entries()) {
      queueSizes[type] = queue.length;
      totalQueued += queue.length;
    }

    // Calculate estimated wait time based on average processing time and queue length
    const estimatedWaitTime = this.stats.averageProcessingTime * 
      (totalQueued / Math.max(1, this.config.maxConcurrentJobs));

    return {
      ...this.stats,
      resourceUsage: this.resourceUsage,
      queueSizes,
      estimatedWaitTime
    };
  }

  /**
   * Intelligent batch processing with resource management
   */
  private async processBatches(): Promise<void> {
    if (this.isProcessing) return;
    this.isProcessing = true;

    try {
      // Check resource constraints
      if (!this.canProcessMoreJobs()) {
        console.log('Resource limits reached, skipping batch processing');
        return;
      }

      // Process each job type
      for (const [jobType, queue] of this.queues.entries()) {
        if (queue.length === 0) continue;

        const processor = this.processors.get(jobType);
        if (!processor) {
          console.warn(`No processor registered for job type: ${jobType}`);
          continue;
        }

        await this.processJobType(jobType, queue, processor);
      }
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Process jobs of a specific type
   */
  private async processJobType(
    jobType: string,
    queue: BatchJob[],
    processor: ProcessorFunction
  ): Promise<void> {
    const availableSlots = this.config.maxConcurrentJobs - this.processingJobs.size;
    if (availableSlots <= 0) return;

    // Select jobs for processing based on various factors
    const jobsToProcess = this.selectJobsForBatch(queue, availableSlots);
    if (jobsToProcess.length === 0) return;

    // Move jobs to processing
    jobsToProcess.forEach(job => {
      const index = queue.indexOf(job);
      if (index !== -1) {
        queue.splice(index, 1);
        job.startedAt = new Date();
        this.processingJobs.set(job.id, job);
      }
    });

    this.updateStats();

    try {
      console.log(`Processing batch of ${jobsToProcess.length} ${jobType} jobs`);
      
      // Update resource usage
      this.resourceUsage.activeConnections += jobsToProcess.length;
      this.resourceUsage.memoryMB += jobsToProcess.reduce((sum, job) => 
        sum + this.estimateJobMemoryUsage(job), 0);

      const results = await processor(jobsToProcess);

      // Process results
      for (let i = 0; i < jobsToProcess.length; i++) {
        const job = jobsToProcess[i];
        const result = results[i];

        await this.handleJobResult(job, result);
      }

    } catch (error) {
      console.error(`Batch processing failed for ${jobType}:`, error);
      
      // Handle batch failure
      for (const job of jobsToProcess) {
        await this.handleJobResult(job, {
          success: false,
          error: error instanceof Error ? error.message : 'Batch processing failed',
          duration: Date.now() - (job.startedAt?.getTime() || 0)
        });
      }
    } finally {
      // Update resource usage
      this.resourceUsage.activeConnections -= jobsToProcess.length;
      this.resourceUsage.memoryMB -= jobsToProcess.reduce((sum, job) => 
        sum + this.estimateJobMemoryUsage(job), 0);
      
      this.updateStats();
    }
  }

  /**
   * Select jobs for batch processing using intelligent algorithms
   */
  private selectJobsForBatch(queue: BatchJob[], maxJobs: number): BatchJob[] {
    const selected: BatchJob[] = [];
    const consideredJobs = queue.slice(0, Math.min(maxJobs * 2, queue.length));

    // First pass: select jobs without dependencies or with satisfied dependencies
    for (const job of consideredJobs) {
      if (selected.length >= maxJobs) break;

      // Check dependencies
      if (job.dependencies) {
        const hasUnsatisfiedDeps = job.dependencies.some(depId => 
          !this.completedJobs.has(depId)
        );
        if (hasUnsatisfiedDeps) continue;
      }

      // Check resource constraints for this job
      const estimatedMemory = this.estimateJobMemoryUsage(job);
      if (this.resourceUsage.memoryMB + estimatedMemory > this.config.resourceLimits.maxMemoryMB) {
        continue;
      }

      const estimatedCost = job.costEstimate || 1;
      if (this.resourceUsage.costPerHour + estimatedCost > this.config.resourceLimits.maxCostPerHour) {
        continue;
      }

      selected.push(job);
    }

    // Second pass: fill remaining slots with compatible jobs
    if (selected.length < maxJobs) {
      const remaining = consideredJobs.filter(job => !selected.includes(job));
      
      for (const job of remaining) {
        if (selected.length >= maxJobs) break;
        
        // More lenient selection for remaining slots
        if (this.canJobFitInBatch(job, selected)) {
          selected.push(job);
        }
      }
    }

    return selected;
  }

  /**
   * Handle job processing result
   */
  private async handleJobResult(job: BatchJob, result: BatchJobResult): Promise<void> {
    // Remove from processing
    this.processingJobs.delete(job.id);

    if (result.success) {
      job.completedAt = new Date();
      job.error = undefined;
      this.completedJobs.set(job.id, job);
      
      this.stats.completedJobs++;
      this.stats.totalCost += result.cost || 0;
      
      this.emit('jobCompleted', { job, result });
      
      // Trigger processing of dependent jobs
      this.triggerDependentJobs(job.id);
      
    } else {
      job.retryCount++;
      
      if (job.retryCount < job.maxRetries) {
        // Retry with exponential backoff
        const delay = this.config.retryDelayMs * Math.pow(2, job.retryCount - 1);
        
        setTimeout(() => {
          // Add back to queue with lower priority
          const originalPriority = job.priority;
          if (job.priority !== 'low') {
            const priorities = ['urgent', 'high', 'medium', 'low'];
            const currentIndex = priorities.indexOf(job.priority);
            job.priority = priorities[Math.min(currentIndex + 1, 3)] as any;
          }
          
          const queue = this.queues.get(job.type);
          if (queue) {
            queue.push(job);
            queue.sort((a, b) => {
              const priorityDiff = this.config.priorityWeights[b.priority] - this.config.priorityWeights[a.priority];
              if (priorityDiff !== 0) return priorityDiff;
              return a.createdAt.getTime() - b.createdAt.getTime();
            });
          }
          
          this.emit('jobRetry', job);
        }, delay);
        
      } else {
        // Max retries reached
        job.failedAt = new Date();
        job.error = result.error || 'Max retries exceeded';
        this.completedJobs.set(job.id, job);
        
        this.stats.failedJobs++;
        this.emit('jobFailed', { job, error: job.error });
      }
    }

    this.updateStats();
  }

  /**
   * Trigger processing of jobs that depend on the completed job
   */
  private triggerDependentJobs(completedJobId: string): void {
    for (const queue of this.queues.values()) {
      for (const job of queue) {
        if (job.dependencies?.includes(completedJobId)) {
          // Check if all dependencies are now satisfied
          const hasUnsatisfiedDeps = job.dependencies.some(depId => 
            !this.completedJobs.has(depId)
          );
          
          if (!hasUnsatisfiedDeps && job.priority === 'low') {
            // Restore original priority
            job.priority = 'medium'; // Default restored priority
          }
        }
      }
    }
  }

  /**
   * Check if system can process more jobs
   */
  private canProcessMoreJobs(): boolean {
    return (
      this.processingJobs.size < this.config.maxConcurrentJobs &&
      this.resourceUsage.memoryMB < this.config.resourceLimits.maxMemoryMB &&
      this.resourceUsage.costPerHour < this.config.resourceLimits.maxCostPerHour
    );
  }

  /**
   * Check if a job can fit in the current batch
   */
  private canJobFitInBatch(job: BatchJob, selectedJobs: BatchJob[]): boolean {
    const totalMemory = selectedJobs.reduce((sum, j) => sum + this.estimateJobMemoryUsage(j), 0);
    const jobMemory = this.estimateJobMemoryUsage(job);
    
    const totalCost = selectedJobs.reduce((sum, j) => sum + (j.costEstimate || 1), 0);
    const jobCost = job.costEstimate || 1;
    
    return (
      totalMemory + jobMemory <= this.config.resourceLimits.maxMemoryMB &&
      totalCost + jobCost <= this.config.resourceLimits.maxCostPerHour
    );
  }

  /**
   * Estimate memory usage for a job based on its type and data
   */
  private estimateJobMemoryUsage(job: BatchJob): number {
    const baseMemory = {
      image: 50,    // 50MB base for image processing
      video: 200,   // 200MB base for video processing  
      audio: 30,    // 30MB base for audio processing
      script: 10    // 10MB base for script processing
    };

    let memory = baseMemory[job.type] || 20;

    // Adjust based on data size
    if (job.data) {
      const dataSize = JSON.stringify(job.data).length;
      memory += Math.ceil(dataSize / (1024 * 1024)) * 5; // 5MB per MB of data
    }

    return memory;
  }

  private generateJobId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private updateStats(): void {
    let totalQueued = 0;
    for (const queue of this.queues.values()) {
      totalQueued += queue.length;
    }

    this.stats.activeJobs = this.processingJobs.size;
    this.stats.queuedJobs = totalQueued;
    this.stats.totalJobs = this.stats.completedJobs + this.stats.failedJobs + this.stats.activeJobs + this.stats.queuedJobs;

    if (this.stats.totalJobs > 0) {
      this.stats.successRate = this.stats.completedJobs / (this.stats.completedJobs + this.stats.failedJobs);
    }

    // Calculate cost per hour
    const startTime = Date.now() - (60 * 60 * 1000); // 1 hour ago
    this.resourceUsage.costPerHour = this.stats.totalCost; // Simplified calculation
  }

  private startBatchProcessing(): void {
    this.batchTimer = setInterval(() => {
      this.processBatches().catch(error => {
        console.error('Batch processing error:', error);
        this.emit('error', error);
      });
    }, this.config.batchTimeoutMs);
  }

  private startResourceMonitoring(): void {
    setInterval(() => {
      this.monitorResources();
    }, 10000); // Monitor every 10 seconds
  }

  private monitorResources(): void {
    // Update memory usage (simplified)
    if (typeof window !== 'undefined' && 'performance' in window) {
      // @ts-ignore
      const memory = (performance as any).memory;
      if (memory) {
        this.resourceUsage.memoryMB = memory.usedJSHeapSize / (1024 * 1024);
      }
    }

    // Emit resource alerts if limits are approached
    const memoryUsage = this.resourceUsage.memoryMB / this.config.resourceLimits.maxMemoryMB;
    const costUsage = this.resourceUsage.costPerHour / this.config.resourceLimits.maxCostPerHour;

    if (memoryUsage > 0.8) {
      this.emit('resourceAlert', { type: 'memory', usage: memoryUsage, threshold: 0.8 });
    }

    if (costUsage > 0.8) {
      this.emit('resourceAlert', { type: 'cost', usage: costUsage, threshold: 0.8 });
    }
  }

  /**
   * Graceful shutdown
   */
  async shutdown(): Promise<void> {
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
    }

    // Wait for current jobs to complete or timeout after 30 seconds
    const timeout = 30000;
    const startTime = Date.now();

    while (this.processingJobs.size > 0 && (Date.now() - startTime) < timeout) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Cancel remaining jobs
    for (const jobId of this.processingJobs.keys()) {
      await this.cancelJob(jobId);
    }

    this.emit('shutdown');
  }
}

export default IntelligentBatchQueueManager;