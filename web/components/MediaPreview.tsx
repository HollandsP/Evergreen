import React, { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import {
  PlayIcon,
  PauseIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  ShareIcon,
} from '@heroicons/react/24/outline';
import { GenerationJob } from '@/types';
import { downloadBlob, cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';

interface MediaPreviewProps {
  job: GenerationJob;
  className?: string;
  onDownload?: (type: 'image' | 'video') => void;
}

const MediaPreview: React.FC<MediaPreviewProps> = ({
  job,
  className,
  onDownload,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [isDownloading, setIsDownloading] = useState<'image' | 'video' | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      const handlePlay = () => setIsPlaying(true);
      const handlePause = () => setIsPlaying(false);
      const handleEnded = () => setIsPlaying(false);

      video.addEventListener('play', handlePlay);
      video.addEventListener('pause', handlePause);
      video.addEventListener('ended', handleEnded);

      return () => {
        video.removeEventListener('play', handlePlay);
        video.removeEventListener('pause', handlePause);
        video.removeEventListener('ended', handleEnded);
      };
    }
    return () => {}; // Empty cleanup function when video is not available
  }, [job.videoUrl]);

  const handlePlayPause = () => {
    const video = videoRef.current;
    if (video) {
      if (isPlaying) {
        video.pause();
      } else {
        video.play();
      }
    }
  };

  const handleMuteToggle = () => {
    const video = videoRef.current;
    if (video) {
      video.muted = !video.muted;
      setIsMuted(video.muted);
    }
  };

  const handleDownload = async (type: 'image' | 'video') => {
    setIsDownloading(type);
    try {
      const blob = await apiClient.downloadMedia(job.id, type);
      const filename = `${job.id}_${type}.${type === 'image' ? 'png' : 'mp4'}`;
      downloadBlob(blob, filename);
      onDownload?.(type);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setIsDownloading(null);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'AI Generated Video',
          text: job.prompt,
          url: window.location.href,
        });
      } catch (error) {
        console.error('Share failed:', error);
      }
    } else {
      // Fallback: copy URL to clipboard
      navigator.clipboard.writeText(window.location.href);
    }
  };

  if (job.status === 'pending' || job.status === 'generating_image') {
    return (
      <div className={cn('card', className)}>
        <div className="card-body">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Generating your content...</p>
            <p className="text-sm text-gray-500 mt-1">This may take a few minutes</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('card overflow-hidden', className)}>
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Generated Content</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowFullscreen(!showFullscreen)}
              className="btn-outline p-2"
              title="Toggle fullscreen"
            >
              <EyeIcon className="h-4 w-4" />
            </button>
            <button
              onClick={handleShare}
              className="btn-outline p-2"
              title="Share"
            >
              <ShareIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="relative">
        {/* Image Preview */}
        {job.imageUrl && (
          <div className="relative">
            <div className="aspect-w-16 aspect-h-9 bg-gray-100">
              <Image
                src={job.imageUrl}
                alt={job.prompt}
                fill
                className={cn(
                  'object-cover transition-opacity duration-300',
                  isImageLoaded ? 'opacity-100' : 'opacity-0',
                )}
                onLoad={() => setIsImageLoaded(true)}
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
              />
            </div>

            {/* Image Controls Overlay */}
            <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-20 transition-all duration-300 group">
              <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <button
                  onClick={() => handleDownload('image')}
                  disabled={isDownloading === 'image'}
                  className="btn-primary p-2"
                  title="Download image"
                >
                  {isDownloading === 'image' ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <ArrowDownTrayIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Video Preview */}
        {job.videoUrl && (
          <div className="relative">
            <video
              ref={videoRef}
              src={job.videoUrl}
              className="w-full aspect-video bg-gray-900"
              muted={isMuted}
              loop
              playsInline
              preload="metadata"
            />

            {/* Video Controls Overlay */}
            <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-all duration-300 group">
              {/* Play/Pause Button */}
              <div className="absolute inset-0 flex items-center justify-center">
                <button
                  onClick={handlePlayPause}
                  className={cn(
                    'flex items-center justify-center w-16 h-16 bg-black bg-opacity-50 rounded-full text-white transition-all duration-300',
                    'opacity-0 group-hover:opacity-100',
                    isPlaying && 'opacity-0',
                  )}
                >
                  {isPlaying ? (
                    <PauseIcon className="h-8 w-8" />
                  ) : (
                    <PlayIcon className="h-8 w-8 ml-1" />
                  )}
                </button>
              </div>

              {/* Bottom Controls */}
              <div className="absolute bottom-0 left-0 right-0 p-4">
                <div className="flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handlePlayPause}
                      className="text-white hover:text-gray-300 transition-colors"
                    >
                      {isPlaying ? (
                        <PauseIcon className="h-6 w-6" />
                      ) : (
                        <PlayIcon className="h-6 w-6" />
                      )}
                    </button>
                    
                    <button
                      onClick={handleMuteToggle}
                      className="text-white hover:text-gray-300 transition-colors"
                    >
                      {isMuted ? (
                        <SpeakerXMarkIcon className="h-6 w-6" />
                      ) : (
                        <SpeakerWaveIcon className="h-6 w-6" />
                      )}
                    </button>
                  </div>

                  <button
                    onClick={() => handleDownload('video')}
                    disabled={isDownloading === 'video'}
                    className="text-white hover:text-gray-300 transition-colors"
                    title="Download video"
                  >
                    {isDownloading === 'video' ? (
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                    ) : (
                      <ArrowDownTrayIcon className="h-6 w-6" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading States */}
        {!isImageLoaded && job.imageUrl && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        )}
      </div>

      {/* Content Info */}
      <div className="card-body pt-4">
        <div className="space-y-3">
          {/* Prompt */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-1">Prompt</h4>
            <p className="text-sm text-gray-600 leading-relaxed">{job.prompt}</p>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Provider:</span>
              <span className="ml-2 font-medium text-gray-900">
                DALL-E 3
              </span>
            </div>
            <div>
              <span className="text-gray-500">Duration:</span>
              <span className="ml-2 font-medium text-gray-900">
                {job.metadata?.videoDuration || 10}s
              </span>
            </div>
            <div>
              <span className="text-gray-500">Quality:</span>
              <span className="ml-2 font-medium text-gray-900">
                {job.metadata?.quality || 'High'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Size:</span>
              <span className="ml-2 font-medium text-gray-900">
                {job.metadata?.imageSize || '1024x1024'}
              </span>
            </div>
          </div>

          {/* Cost Breakdown */}
          {job.cost && (
            <div className="pt-2 border-t border-gray-100">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Cost Breakdown</h4>
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <span className="text-gray-500">Image:</span>
                  <span className="ml-1 font-medium">${job.cost.imageGeneration.toFixed(4)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Video:</span>
                  <span className="ml-1 font-medium">${job.cost.videoGeneration.toFixed(4)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Total:</span>
                  <span className="ml-1 font-medium text-primary-600">${job.cost.total.toFixed(4)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Download Actions */}
          <div className="flex space-x-2 pt-2">
            {job.imageUrl && (
              <button
                onClick={() => handleDownload('image')}
                disabled={isDownloading === 'image'}
                className="btn-outline flex-1"
              >
                {isDownloading === 'image' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                ) : (
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                )}
                Download Image
              </button>
            )}
            
            {job.videoUrl && (
              <button
                onClick={() => handleDownload('video')}
                disabled={isDownloading === 'video'}
                className="btn-primary flex-1"
              >
                {isDownloading === 'video' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                )}
                Download Video
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Fullscreen Modal */}
      {showFullscreen && (job.imageUrl || job.videoUrl) && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center p-4">
          <div className="relative max-w-6xl max-h-full">
            <button
              onClick={() => setShowFullscreen(false)}
              className="absolute -top-12 right-0 text-white hover:text-gray-300 transition-colors"
            >
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {job.videoUrl ? (
              <video
                src={job.videoUrl}
                controls
                autoPlay
                className="max-w-full max-h-full"
              />
            ) : job.imageUrl ? (
              <img
                src={job.imageUrl}
                alt={job.prompt}
                className="max-w-full max-h-full object-contain"
              />
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaPreview;
