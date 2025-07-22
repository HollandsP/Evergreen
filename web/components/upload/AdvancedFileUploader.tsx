/**
 * Advanced drag-and-drop file uploader with comprehensive features
 * Supports multiple files, validation, progress tracking, and previews
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { 
  Upload, 
  X, 
  File, 
  Image, 
  Video, 
  Music, 
  FileText,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Download,
  Eye,
  Trash2,
  FolderOpen,
  CloudUpload,
  Pause,
  Play
} from 'lucide-react';
import { performanceMonitor } from '../../lib/performance-monitor';
import { cacheManager } from '../../lib/cache-manager';

interface UploadFile {
  id: string;
  file: File;
  preview?: string;
  status: 'pending' | 'uploading' | 'completed' | 'failed' | 'paused';
  progress: number;
  error?: string;
  uploadedUrl?: string;
  metadata?: {
    type: string;
    size: number;
    dimensions?: { width: number; height: number };
    duration?: number;
    quality?: number;
  };
}

interface ValidationRule {
  type: 'fileType' | 'fileSize' | 'dimensions' | 'duration' | 'count';
  value: any;
  message: string;
}

interface UploadConfig {
  maxFiles: number;
  maxFileSize: number;
  acceptedTypes: string[];
  enablePreview: boolean;
  enableCompression: boolean;
  enableChunkedUpload: boolean;
  chunkSize: number;
  autoUpload: boolean;
  uploadEndpoint: string;
  validationRules: ValidationRule[];
}

interface AdvancedFileUploaderProps {
  config?: Partial<UploadConfig>;
  onFilesAdded?: (files: UploadFile[]) => void;
  onFileRemoved?: (file: UploadFile) => void;
  onUploadStart?: (file: UploadFile) => void;
  onUploadProgress?: (file: UploadFile, progress: number) => void;
  onUploadComplete?: (file: UploadFile, result: any) => void;
  onUploadError?: (file: UploadFile, error: string) => void;
  onAllComplete?: (results: Array<{ file: UploadFile; result?: any; error?: string }>) => void;
  className?: string;
}

const defaultConfig: UploadConfig = {
  maxFiles: 10,
  maxFileSize: 100 * 1024 * 1024, // 100MB
  acceptedTypes: ['image/*', 'video/*', 'audio/*', 'text/*', '.json', '.csv', '.pdf'],
  enablePreview: true,
  enableCompression: true,
  enableChunkedUpload: true,
  chunkSize: 1024 * 1024, // 1MB chunks
  autoUpload: false,
  uploadEndpoint: '/api/upload',
  validationRules: []
};

export const AdvancedFileUploader: React.FC<AdvancedFileUploaderProps> = ({
  config: configOverride = {},
  onFilesAdded,
  onFileRemoved,
  onUploadStart,
  onUploadProgress,
  onUploadComplete,
  onUploadError,
  onAllComplete,
  className = ''
}) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [globalProgress, setGlobalProgress] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const [showPreviews, setShowPreviews] = useState(true);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);
  const uploadControllersRef = useRef<Map<string, AbortController>>(new Map());

  const config: UploadConfig = { ...defaultConfig, ...configOverride };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cancel all active uploads
      uploadControllersRef.current.forEach(controller => controller.abort());
      uploadControllersRef.current.clear();
      
      // Cleanup object URLs
      files.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview);
        }
      });
    };
  }, []);

  // Update global progress
  useEffect(() => {
    if (files.length === 0) {
      setGlobalProgress(0);
      return;
    }

    const totalProgress = files.reduce((sum, file) => sum + file.progress, 0);
    setGlobalProgress(totalProgress / files.length);
  }, [files]);

  const generateFileId = (): string => {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const getFileIcon = (file: File) => {
    const type = file.type;
    if (type.startsWith('image/')) return <Image className="w-6 h-6" />;
    if (type.startsWith('video/')) return <Video className="w-6 h-6" />;
    if (type.startsWith('audio/')) return <Music className="w-6 h-6" />;
    if (type.startsWith('text/') || type.includes('json') || type.includes('csv')) {
      return <FileText className="w-6 h-6" />;
    }
    return <File className="w-6 h-6" />;
  };

  const validateFile = (file: File): string[] => {
    const errors: string[] = [];

    // Check file type
    if (config.acceptedTypes.length > 0) {
      const isAccepted = config.acceptedTypes.some(type => {
        if (type.startsWith('.')) {
          return file.name.toLowerCase().endsWith(type.toLowerCase());
        }
        if (type.includes('*')) {
          const pattern = type.replace('*', '');
          return file.type.startsWith(pattern);
        }
        return file.type === type;
      });

      if (!isAccepted) {
        errors.push(`File type ${file.type} is not allowed`);
      }
    }

    // Check file size
    if (file.size > config.maxFileSize) {
      errors.push(`File size ${formatBytes(file.size)} exceeds limit of ${formatBytes(config.maxFileSize)}`);
    }

    // Apply custom validation rules
    config.validationRules.forEach(rule => {
      switch (rule.type) {
        case 'fileSize':
          if (file.size > rule.value) {
            errors.push(rule.message);
          }
          break;
        case 'fileType':
          if (!rule.value.includes(file.type)) {
            errors.push(rule.message);
          }
          break;
        // Add more validation types as needed
      }
    });

    return errors;
  };

  const createFilePreview = async (file: File): Promise<string | undefined> => {
    if (!config.enablePreview) return undefined;

    if (file.type.startsWith('image/')) {
      return URL.createObjectURL(file);
    }

    if (file.type.startsWith('video/')) {
      return new Promise((resolve) => {
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.onloadedmetadata = () => {
          video.currentTime = 1;
        };
        video.onseeked = () => {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          ctx?.drawImage(video, 0, 0);
          resolve(canvas.toDataURL());
          URL.revokeObjectURL(video.src);
        };
        video.src = URL.createObjectURL(file);
      });
    }

    return undefined;
  };

  const extractMetadata = async (file: File): Promise<any> => {
    const metadata: any = {
      type: file.type,
      size: file.size,
    };

    if (file.type.startsWith('image/')) {
      return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          metadata.dimensions = { width: img.width, height: img.height };
          resolve(metadata);
          URL.revokeObjectURL(img.src);
        };
        img.onerror = () => resolve(metadata);
        img.src = URL.createObjectURL(file);
      });
    }

    if (file.type.startsWith('video/')) {
      return new Promise((resolve) => {
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.onloadedmetadata = () => {
          metadata.dimensions = { width: video.videoWidth, height: video.videoHeight };
          metadata.duration = video.duration;
          resolve(metadata);
          URL.revokeObjectURL(video.src);
        };
        video.onerror = () => resolve(metadata);
        video.src = URL.createObjectURL(file);
      });
    }

    if (file.type.startsWith('audio/')) {
      return new Promise((resolve) => {
        const audio = document.createElement('audio');
        audio.preload = 'metadata';
        audio.onloadedmetadata = () => {
          metadata.duration = audio.duration;
          resolve(metadata);
          URL.revokeObjectURL(audio.src);
        };
        audio.onerror = () => resolve(metadata);
        audio.src = URL.createObjectURL(file);
      });
    }

    return metadata;
  };

  const processFiles = async (fileList: FileList | File[]) => {
    const newFiles: UploadFile[] = [];
    const fileErrors: string[] = [];

    // Check total file count
    if (files.length + fileList.length > config.maxFiles) {
      fileErrors.push(`Cannot add ${fileList.length} files. Maximum ${config.maxFiles} files allowed.`);
      setErrors(prev => [...prev, ...fileErrors]);
      return;
    }

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList instanceof FileList ? fileList[i] : fileList[i];
      const validationErrors = validateFile(file);

      if (validationErrors.length > 0) {
        fileErrors.push(`${file.name}: ${validationErrors.join(', ')}`);
        continue;
      }

      // Check for duplicates
      const isDuplicate = files.some(existingFile => 
        existingFile.file.name === file.name && 
        existingFile.file.size === file.size
      );

      if (isDuplicate) {
        fileErrors.push(`${file.name}: File already added`);
        continue;
      }

      try {
        const preview = await createFilePreview(file);
        const metadata = await extractMetadata(file);

        const uploadFile: UploadFile = {
          id: generateFileId(),
          file,
          preview,
          status: 'pending',
          progress: 0,
          metadata
        };

        newFiles.push(uploadFile);
      } catch (error) {
        fileErrors.push(`${file.name}: Failed to process file`);
      }
    }

    if (fileErrors.length > 0) {
      setErrors(prev => [...prev, ...fileErrors]);
    }

    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles]);
      onFilesAdded?.(newFiles);

      // Record performance metrics
      performanceMonitor.recordMetric('files_added', newFiles.length, {
        totalFiles: (files.length + newFiles.length).toString(),
        operation: 'file_selection'
      });

      // Auto-upload if enabled
      if (config.autoUpload) {
        setTimeout(() => {
          newFiles.forEach(file => uploadFile(file));
        }, 100);
      }
    }
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only set dragging to false if we're leaving the dropzone
    if (!dropzoneRef.current?.contains(e.relatedTarget as Node)) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      processFiles(droppedFiles);
      performanceMonitor.recordInteraction('files_dropped', 'AdvancedFileUploader', 0, true);
    }
  }, [files, config]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
      performanceMonitor.recordInteraction('files_selected', 'AdvancedFileUploader', 0, true);
    }
    
    // Reset input value to allow selecting same files again
    e.target.value = '';
  }, [files, config]);

  const removeFile = useCallback((fileId: string) => {
    const fileToRemove = files.find(f => f.id === fileId);
    if (!fileToRemove) return;

    // Cancel upload if in progress
    const controller = uploadControllersRef.current.get(fileId);
    if (controller) {
      controller.abort();
      uploadControllersRef.current.delete(fileId);
    }

    // Cleanup preview URL
    if (fileToRemove.preview) {
      URL.revokeObjectURL(fileToRemove.preview);
    }

    setFiles(prev => prev.filter(f => f.id !== fileId));
    onFileRemoved?.(fileToRemove);

    performanceMonitor.recordInteraction('file_removed', 'AdvancedFileUploader', 0, true);
  }, [files, onFileRemoved]);

  const uploadFile = async (uploadFile: UploadFile) => {
    if (uploadFile.status === 'uploading' || uploadFile.status === 'completed') return;

    const controller = new AbortController();
    uploadControllersRef.current.set(uploadFile.id, controller);

    // Update file status
    setFiles(prev => prev.map(f => 
      f.id === uploadFile.id 
        ? { ...f, status: 'uploading', progress: 0, error: undefined }
        : f
    ));

    onUploadStart?.(uploadFile);

    try {
      let result;
      
      if (config.enableChunkedUpload && uploadFile.file.size > config.chunkSize) {
        result = await uploadFileChunked(uploadFile, controller);
      } else {
        result = await uploadFileSimple(uploadFile, controller);
      }

      // Mark as completed
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'completed', progress: 100, uploadedUrl: result.url }
          : f
      ));

      onUploadComplete?.(uploadFile, result);

      // Cache the uploaded file info
      await cacheManager.cacheMediaFile(
        result.url,
        uploadFile.file.type.startsWith('image/') ? 'image' : 
        uploadFile.file.type.startsWith('video/') ? 'video' : 'audio',
        uploadFile.file.type.split('/')[1] || 'unknown',
        await uploadFile.file.arrayBuffer(),
        uploadFile.metadata?.dimensions ? 
          `${uploadFile.metadata.dimensions.width}x${uploadFile.metadata.dimensions.height}` : 
          undefined,
        ['upload', 'user_content']
      );

      performanceMonitor.recordInteraction('file_uploaded', 'AdvancedFileUploader', 
        Date.now() - (uploadFile.metadata?.uploadStartTime || Date.now()), true);

    } catch (error: any) {
      if (error.name === 'AbortError') {
        // Upload was cancelled
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'pending', progress: 0 }
            : f
        ));
      } else {
        const errorMessage = error.message || 'Upload failed';
        
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'failed', error: errorMessage }
            : f
        ));

        onUploadError?.(uploadFile, errorMessage);

        performanceMonitor.recordInteraction('file_upload_failed', 'AdvancedFileUploader', 
          Date.now() - (uploadFile.metadata?.uploadStartTime || Date.now()), false, errorMessage);
      }
    } finally {
      uploadControllersRef.current.delete(uploadFile.id);
    }
  };

  const uploadFileSimple = async (uploadFile: UploadFile, controller: AbortController): Promise<any> => {
    const formData = new FormData();
    formData.append('file', uploadFile.file);
    formData.append('metadata', JSON.stringify(uploadFile.metadata));

    const response = await fetch(config.uploadEndpoint, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  };

  const uploadFileChunked = async (uploadFile: UploadFile, controller: AbortController): Promise<any> => {
    const file = uploadFile.file;
    const totalChunks = Math.ceil(file.size / config.chunkSize);
    const uploadId = generateFileId();

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      if (controller.signal.aborted) {
        throw new Error('Upload cancelled');
      }

      const start = chunkIndex * config.chunkSize;
      const end = Math.min(start + config.chunkSize, file.size);
      const chunk = file.slice(start, end);

      const formData = new FormData();
      formData.append('chunk', chunk);
      formData.append('chunkIndex', chunkIndex.toString());
      formData.append('totalChunks', totalChunks.toString());
      formData.append('uploadId', uploadId);
      formData.append('fileName', file.name);
      formData.append('fileSize', file.size.toString());
      
      if (chunkIndex === 0) {
        formData.append('metadata', JSON.stringify(uploadFile.metadata));
      }

      const response = await fetch(`${config.uploadEndpoint}/chunk`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Chunk upload failed: ${response.statusText}`);
      }

      // Update progress
      const progress = ((chunkIndex + 1) / totalChunks) * 100;
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id ? { ...f, progress } : f
      ));
      
      onUploadProgress?.(uploadFile, progress);
    }

    // Finalize chunked upload
    const finalResponse = await fetch(`${config.uploadEndpoint}/finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uploadId, fileName: file.name }),
      signal: controller.signal,
    });

    if (!finalResponse.ok) {
      throw new Error(`Upload finalization failed: ${finalResponse.statusText}`);
    }

    return finalResponse.json();
  };

  const pauseUpload = (fileId: string) => {
    const controller = uploadControllersRef.current.get(fileId);
    if (controller) {
      controller.abort();
      uploadControllersRef.current.delete(fileId);
      
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: 'paused' } : f
      ));
    }
  };

  const resumeUpload = (fileId: string) => {
    const file = files.find(f => f.id === fileId);
    if (file && file.status === 'paused') {
      uploadFile(file);
    }
  };

  const uploadAll = () => {
    setIsUploading(true);
    const pendingFiles = files.filter(f => f.status === 'pending' || f.status === 'failed');
    
    pendingFiles.forEach(file => uploadFile(file));
    
    // Check completion
    const checkCompletion = () => {
      const activeUploads = files.filter(f => f.status === 'uploading').length;
      if (activeUploads === 0) {
        setIsUploading(false);
        const results = files.map(f => ({ 
          file: f, 
          result: f.uploadedUrl, 
          error: f.error 
        }));
        onAllComplete?.(results);
      } else {
        setTimeout(checkCompletion, 1000);
      }
    };

    setTimeout(checkCompletion, 1000);
  };

  const clearAll = () => {
    // Cancel all uploads
    uploadControllersRef.current.forEach(controller => controller.abort());
    uploadControllersRef.current.clear();

    // Cleanup previews
    files.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });

    setFiles([]);
    setErrors([]);
    setIsUploading(false);
    setGlobalProgress(0);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'uploading': return 'text-blue-600 bg-blue-50';
      case 'failed': return 'text-red-600 bg-red-50';
      case 'paused': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CloudUpload className="w-5 h-5" />
            <span>File Upload</span>
            <Badge variant="secondary">
              {files.length}/{config.maxFiles}
            </Badge>
          </div>
          
          {files.length > 0 && (
            <div className="flex space-x-2">
              {!isUploading && files.some(f => f.status === 'pending' || f.status === 'failed') && (
                <Button size="sm" onClick={uploadAll}>
                  Upload All
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={clearAll}>
                Clear All
              </Button>
            </div>
          )}
        </CardTitle>

        {files.length > 0 && (
          <div className="space-y-2">
            <Progress value={globalProgress} className="h-2" />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>
                {files.filter(f => f.status === 'completed').length} of {files.length} completed
              </span>
              <span>{Math.round(globalProgress)}%</span>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Drop Zone */}
        <div
          ref={dropzoneRef}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-all
            ${isDragging 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
            }
          `}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-semibold mb-2">
            {isDragging ? 'Drop files here' : 'Upload Files'}
          </h3>
          <p className="text-muted-foreground mb-4">
            Drag and drop files here, or click to browse
          </p>
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
          >
            <FolderOpen className="w-4 h-4 mr-2" />
            Browse Files
          </Button>
          
          <div className="mt-4 text-xs text-muted-foreground">
            <p>Max {config.maxFiles} files, up to {formatBytes(config.maxFileSize)} each</p>
            <p>Accepted types: {config.acceptedTypes.join(', ')}</p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={config.acceptedTypes.join(',')}
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* Errors */}
        {errors.length > 0 && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <h4 className="font-semibold text-red-900">Upload Errors</h4>
            </div>
            <div className="space-y-1">
              {errors.slice(-5).map((error, index) => (
                <p key={index} className="text-sm text-red-700">{error}</p>
              ))}
            </div>
            {errors.length > 5 && (
              <p className="text-sm text-red-600 mt-2">
                ... and {errors.length - 5} more errors
              </p>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="mt-2"
              onClick={() => setErrors([])}
            >
              Clear Errors
            </Button>
          </div>
        )}

        {/* File List */}
        {files.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold">Files ({files.length})</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPreviews(!showPreviews)}
              >
                <Eye className="w-4 h-4 mr-2" />
                {showPreviews ? 'Hide' : 'Show'} Previews
              </Button>
            </div>

            <div className="grid gap-3">
              {files.map(file => (
                <div key={file.id} className="border rounded-lg p-3">
                  <div className="flex items-start space-x-3">
                    {/* File Icon/Preview */}
                    <div className="flex-shrink-0">
                      {showPreviews && file.preview ? (
                        <img
                          src={file.preview}
                          alt={file.file.name}
                          className="w-12 h-12 object-cover rounded"
                        />
                      ) : (
                        <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                          {getFileIcon(file.file)}
                        </div>
                      )}
                    </div>

                    {/* File Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h5 className="font-medium truncate">{file.file.name}</h5>
                        <Badge className={getStatusColor(file.status)}>
                          {file.status}
                        </Badge>
                      </div>

                      <div className="text-sm text-muted-foreground mb-2">
                        <span>{formatBytes(file.file.size)}</span>
                        {file.metadata?.dimensions && (
                          <span> • {file.metadata.dimensions.width}×{file.metadata.dimensions.height}</span>
                        )}
                        {file.metadata?.duration && (
                          <span> • {formatDuration(file.metadata.duration)}</span>
                        )}
                      </div>

                      {/* Progress Bar */}
                      {(file.status === 'uploading' || file.progress > 0) && (
                        <div className="mb-2">
                          <Progress value={file.progress} className="h-1" />
                          <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                            <span>{Math.round(file.progress)}%</span>
                            {file.status === 'uploading' && (
                              <span>Uploading...</span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Error Message */}
                      {file.error && (
                        <p className="text-sm text-red-600 mb-2">{file.error}</p>
                      )}

                      {/* Actions */}
                      <div className="flex space-x-2">
                        {file.status === 'pending' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => uploadFile(file)}
                          >
                            <Upload className="w-3 h-3 mr-1" />
                            Upload
                          </Button>
                        )}

                        {file.status === 'uploading' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => pauseUpload(file.id)}
                          >
                            <Pause className="w-3 h-3 mr-1" />
                            Pause
                          </Button>
                        )}

                        {file.status === 'paused' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => resumeUpload(file.id)}
                          >
                            <Play className="w-3 h-3 mr-1" />
                            Resume
                          </Button>
                        )}

                        {file.status === 'failed' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => uploadFile(file)}
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Retry
                          </Button>
                        )}

                        {file.status === 'completed' && file.uploadedUrl && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => window.open(file.uploadedUrl, '_blank')}
                          >
                            <Download className="w-3 h-3 mr-1" />
                            Download
                          </Button>
                        )}

                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeFile(file.id)}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AdvancedFileUploader;