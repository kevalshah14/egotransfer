import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Hand, Box, Cpu, Zap, X, ChevronRight, ChevronLeft, Volume2, VolumeX, Settings, RotateCcw } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface HandSkeleton {
  points: { x: number; y: number; confidence: number }[];
  connections: [number, number][];
}

interface CombinedProcessingData {
  handJobId: string;
  aiJobId: string;
  handProcessing: any;
  aiAnalysis: any;
  processedVideoUrl: string;
  trackingData: string;
  robotCommands: string;
}

interface DetailedVideoAnalysisProps {
  videoFile: File | null;
  videoUrl?: string; // Add optional video URL for old jobs
  analysisData: CombinedProcessingData | null;
  onBack: () => void;
  onTransferToRobot?: () => void;
}

export default function DetailedVideoAnalysis({ 
  videoFile, 
  videoUrl,
  analysisData, 
  onBack, 
  onTransferToRobot 
}: DetailedVideoAnalysisProps) {
  
  console.log('DetailedVideoAnalysis: Received analysisData:', analysisData);
  
  // State definitions
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentHandSkeleton, setCurrentHandSkeleton] = useState<HandSkeleton | null>(null);
  const [currentAction, setCurrentAction] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [realTrackingData, setRealTrackingData] = useState<any[]>([]);
  const [processedVideoUrl, setProcessedVideoUrl] = useState<string | null>(null);
  const [processingStats, setProcessingStats] = useState<any>(null);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showControls, setShowControls] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const stepsScrollRef = useRef<HTMLDivElement>(null);

  // Create stable object URL and manage lifecycle
  const objectUrl = useMemo(() => {
    if (processedVideoUrl) {
      return processedVideoUrl;
    } else if (videoUrl) {
      return videoUrl;
    } else if (videoFile) {
      const url = URL.createObjectURL(videoFile);
      return url;
    }
    return null;
  }, [videoFile, videoUrl, processedVideoUrl]);

  // Cleanup object URL on unmount or video change
  useEffect(() => {
    return () => {
      if (objectUrl && objectUrl.startsWith('blob:')) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [objectUrl]);

  // Function to invert hand labels in timeline data and convert time strings to seconds
  const invertHandLabels = (timeline: any[]) => {
    return timeline.map(action => {
      const invertedAction = {
        ...action,
        actors: action.actors?.map((actor: string) => {
          if (actor.toLowerCase().includes('right hand')) {
            return actor.replace(/right hand/gi, 'left hand');
          } else if (actor.toLowerCase().includes('left hand')) {
            return actor.replace(/left hand/gi, 'right hand');
          }
          return actor;
        }) || []
      };

      // Convert time strings to seconds for easier processing
      if (action.start_time) {
        invertedAction.timestamp = parseTimeToSeconds(action.start_time);
      }
      if (action.end_time) {
        invertedAction.end_timestamp = parseTimeToSeconds(action.end_time);
      }

      return invertedAction;
    });
  };

  // Helper function to convert MM:SS format to seconds
  const parseTimeToSeconds = (timeStr: string): number => {
    const parts = timeStr.split(':');
    if (parts.length === 2) {
      const minutes = parseInt(parts[0], 10);
      const seconds = parseInt(parts[1], 10);
      return minutes * 60 + seconds;
    }
    return 0;
  };

  // Memoize taskProgress to prevent unnecessary re-renders
  const taskProgress = useMemo(() => {
    if (analysisData?.aiAnalysis) {
      const originalTimeline = analysisData.aiAnalysis.timeline || [];
      const invertedTimeline = invertHandLabels(originalTimeline);
      
      return {
        title: analysisData.aiAnalysis.task_description || "Video Analysis",
        completed: originalTimeline.length,
        total: originalTimeline.length,
        currentAction: analysisData.aiAnalysis.robot_notes || "Analysis completed",
        objects: analysisData.aiAnalysis.detected_objects || [],
        actors: analysisData.aiAnalysis.movement_patterns ? ["Left Hand", "Right Hand"] : [],
        confidence: analysisData.aiAnalysis.confidence || 0,
        timeline: invertedTimeline
      };
    }
    
    return {
      title: "Waiting for analysis...",
      completed: 0,
      total: 12,
      currentAction: "No analysis data available",
      objects: [],
      actors: [],
      confidence: 0,
      timeline: []
    };
  }, [analysisData]);

  // Memoize annotation timeline
  const annotationTimeline = useMemo(() => {
    if (realTrackingData.length === 0) return [];
    
    return realTrackingData.map((frame, index) => ({
      time: frame.timestamp || (index * 0.5),
      type: 'hand_tracking',
      data: {
        points: frame.landmarks || [],
        connections: frame.connections || [],
        action: frame.gesture_type || frame.action_type || 'Hand detected'
      }
    }));
  }, [realTrackingData]);

  // Stable updateCurrentStep function
  const updateCurrentStep = useCallback((time: number) => {
    if (taskProgress.timeline && taskProgress.timeline.length > 0) {
      let stepIndex = -1;
      
      for (let i = 0; i < taskProgress.timeline.length; i++) {
        const stepStartTime = taskProgress.timeline[i].timestamp || 0;
        const stepEndTime = taskProgress.timeline[i].end_timestamp || (stepStartTime + 2);
        
        // Check if current time is within this step's duration
        if (time >= stepStartTime && time < stepEndTime) {
          stepIndex = i;
          break;
        }
        
        // For the last step, also check if we're past its start time (in case there's no end time)
        if (i === taskProgress.timeline.length - 1 && time >= stepStartTime) {
          stepIndex = i;
          break;
        }
      }
      
      if (stepIndex !== -1 && stepIndex !== currentStep) {
        setCurrentStep(stepIndex);
      }
    } else if (duration > 0) {
      const progress = Math.min(time / duration, 1);
      const stepIndex = Math.min(Math.floor(progress * taskProgress.total), taskProgress.total - 1);
      if (stepIndex !== currentStep) {
        setCurrentStep(stepIndex);
      }
    }
  }, [taskProgress.timeline, taskProgress.total, duration, currentStep]);

  // Fetch real tracking data on component mount with proper cleanup
  useEffect(() => {
    if (!analysisData?.handJobId) return;

    // Cancel any existing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const fetchTrackingData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch hand tracking data
        const trackingResponse = await fetch(`/hand/tracking/${analysisData.handJobId}`, {
          signal: abortController.signal
        });
        
        if (trackingResponse.ok) {
          const trackingData = await trackingResponse.json();
          if (!abortController.signal.aborted) {
            setRealTrackingData(trackingData);
          }
        }
        
        // Fetch processing statistics
        const statsResponse = await fetch(`/hand/stats/${analysisData.handJobId}`, {
          signal: abortController.signal
        });
        
        if (statsResponse.ok) {
          const stats = await statsResponse.json();
          if (!abortController.signal.aborted) {
            setProcessingStats(stats);
          }
        }
        
        // Set processed video URL
        if (!abortController.signal.aborted) {
          setProcessedVideoUrl(analysisData.processedVideoUrl);
        }
        
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.error('Error fetching tracking data:', error);
        }
      } finally {
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };
    
    fetchTrackingData();

    return () => {
      abortController.abort();
    };
  }, [analysisData?.handJobId, analysisData?.processedVideoUrl]);

  // Handle seeking to specific timestamp
  const seekToTimestamp = useCallback((timestamp: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp;
      setCurrentTime(timestamp);
    }
  }, []);

  // Synchronize annotations with video timeline
  useEffect(() => {
    if (annotationTimeline.length === 0) return;

    const activeAnnotation = annotationTimeline
      .filter(annotation => currentTime >= annotation.time)
      .pop();

    if (activeAnnotation) {
      setCurrentHandSkeleton({
        points: activeAnnotation.data.points,
        connections: activeAnnotation.data.connections as [number, number][]
      });
      setCurrentAction(activeAnnotation.data.action);
    } else if (!isPlaying) {
      // Keep skeleton visible when paused
      const lastAnnotation = annotationTimeline
        .filter(annotation => currentTime >= annotation.time)
        .pop();
      
      if (lastAnnotation) {
        setCurrentHandSkeleton({
          points: lastAnnotation.data.points,
          connections: lastAnnotation.data.connections as [number, number][]
        });
        setCurrentAction(lastAnnotation.data.action);
      } else {
        setCurrentHandSkeleton(null);
        setCurrentAction('');
      }
    }
  }, [currentTime, isPlaying, annotationTimeline]);

  // Update current step based on video time
  useEffect(() => {
    if (currentTime >= 0 && (taskProgress.timeline.length > 0 || duration > 0)) {
      updateCurrentStep(currentTime);
    }
  }, [currentTime, updateCurrentStep]);

  const togglePlayPause = async () => {
    if (!videoRef.current || videoRef.current.readyState < 2) return;
    
    try {
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        await videoRef.current.play();
        setIsPlaying(true);
      }
      setVideoError(null);
    } catch (error) {
      console.error('Playback failed:', error);
      setVideoError('Playback failed. Please try again.');
    }
  };

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      setVideoError(null);
    }
  }, []);

  const handleVideoError = useCallback((e: React.SyntheticEvent<HTMLVideoElement>) => {
    console.error('Video playback error:', e);
    const video = e.target as HTMLVideoElement;
    let errorMessage = 'Video playback error';
    
    if (video.error) {
      switch (video.error.code) {
        case video.error.MEDIA_ERR_ABORTED:
          errorMessage = 'Video loading was aborted';
          break;
        case video.error.MEDIA_ERR_NETWORK:
          errorMessage = 'Network error while loading video';
          break;
        case video.error.MEDIA_ERR_DECODE:
          errorMessage = 'Video format not supported';
          break;
        case video.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
          errorMessage = 'Video source not supported';
          break;
      }
    }
    
    setVideoError(errorMessage);
    setIsPlaying(false);
  }, []);

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Enhanced control functions
  const handleVolumeChange = useCallback((newVolume: number) => {
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setVolume(newVolume);
      setIsMuted(newVolume === 0);
    }
  }, []);

  const toggleMute = useCallback(() => {
    if (videoRef.current) {
      if (isMuted) {
        videoRef.current.volume = volume;
        setIsMuted(false);
      } else {
        videoRef.current.volume = 0;
        setIsMuted(true);
      }
    }
  }, [isMuted, volume]);

  const handlePlaybackSpeedChange = useCallback((speed: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
      setPlaybackSpeed(speed);
    }
  }, []);

  const handleProgressBarClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!videoRef.current || !duration) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  }, [duration]);

  const handleProgressBarDrag = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!videoRef.current || !duration) return;
    
    setIsDragging(true);
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, clickX / rect.width));
    const newTime = percentage * duration;
    
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  }, [duration]);

  const handleProgressBarDragEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!videoRef.current) return;
      
      switch (e.code) {
        case 'Space':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          // Previous step
          if (taskProgress.timeline && taskProgress.timeline.length > 0 && currentStep > 0) {
            const prevStep = taskProgress.timeline[currentStep - 1];
            const timestamp = prevStep.timestamp || ((currentStep - 1) * 2);
            seekToTimestamp(timestamp);
          }
          break;
        case 'ArrowRight':
          e.preventDefault();
          // Next step
          if (taskProgress.timeline && taskProgress.timeline.length > 0 && currentStep < taskProgress.timeline.length - 1) {
            const nextStep = taskProgress.timeline[currentStep + 1];
            const timestamp = nextStep.timestamp || ((currentStep + 1) * 2);
            seekToTimestamp(timestamp);
          }
          break;
        case 'KeyM':
          e.preventDefault();
          toggleMute();
          break;
        case 'KeyF':
          e.preventDefault();
          // Toggle fullscreen
          if (videoRef.current.requestFullscreen) {
            videoRef.current.requestFullscreen();
          }
          break;
        case 'Digit0':
          e.preventDefault();
          handlePlaybackSpeedChange(1);
          break;
        case 'Digit1':
          e.preventDefault();
          handlePlaybackSpeedChange(0.5);
          break;
        case 'Digit2':
          e.preventDefault();
          handlePlaybackSpeedChange(1.25);
          break;
        case 'Digit3':
          e.preventDefault();
          handlePlaybackSpeedChange(1.5);
          break;
        case 'Digit4':
          e.preventDefault();
          handlePlaybackSpeedChange(2);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [currentTime, duration, toggleMute, handlePlaybackSpeedChange, taskProgress.timeline, currentStep]);

  // Auto-hide controls
  useEffect(() => {
    if (!isPlaying) return;
    
    const timer = setTimeout(() => {
      setShowControls(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, [isPlaying, currentTime]);

  const handleMouseMove = useCallback(() => {
    setShowControls(true);
  }, []);

  // Auto-scroll to active step
  const scrollToActiveStep = useCallback(() => {
    if (!stepsScrollRef.current || !taskProgress.timeline || taskProgress.timeline.length === 0) return;
    
    const scrollContainer = stepsScrollRef.current;
    const activeStepElement = scrollContainer.querySelector(`[data-step-index="${currentStep}"]`) as HTMLElement;
    
    if (activeStepElement) {
      // Use scrollIntoView for more reliable scrolling
      activeStepElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });
    }
  }, [currentStep, taskProgress.timeline]);

  // Scroll to active step when currentStep changes
  useEffect(() => {
    scrollToActiveStep();
  }, [scrollToActiveStep]);

  const progressPercentage = (currentStep / Math.max(taskProgress.total - 1, 1)) * 100;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  if (!videoFile && !videoUrl) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-950 via-black to-slate-900 page-transition">
        <div className="flex items-center justify-center h-full text-white/50">
          <div className="text-center">
            <Play className="h-16 w-16 mx-auto mb-4" />
            <p>No video file provided</p>
            <button 
              onClick={onBack}
              className="mt-4 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-950 via-black to-slate-900 page-transition">
      <div className="relative w-full h-full">
        {videoError ? (
          <div className="flex items-center justify-center h-full text-white/50">
            <div className="text-center">
              <X className="h-16 w-16 mx-auto mb-4 text-red-400" />
              <p className="mb-2">{videoError}</p>
              <button 
                onClick={() => {
                  setVideoError(null);
                  if (videoRef.current) {
                    videoRef.current.load();
                  }
                }}
                className="px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              src={objectUrl || ''}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onSeeked={handleTimeUpdate}
              onError={handleVideoError}
              onMouseMove={handleMouseMove}
              preload="auto"
              playsInline
              data-testid="detailed-video-player"
            />
            
            {/* Rest of the component remains the same... */}
            {/* Hand Skeleton Overlay */}
            {currentHandSkeleton && isPlaying && (
              <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 800 600">
                {currentHandSkeleton.connections.map((connection, index) => {
                  const startPoint = currentHandSkeleton.points[connection[0]];
                  const endPoint = currentHandSkeleton.points[connection[1]];
                  if (!startPoint || !endPoint) return null;
                  
                  return (
                    <line
                      key={`connection-${index}`}
                      x1={startPoint.x}
                      y1={startPoint.y}
                      x2={endPoint.x}
                      y2={endPoint.y}
                      stroke="#ef4444"
                      strokeWidth="3"
                      opacity={Math.min(startPoint.confidence, endPoint.confidence)}
                    />
                  );
                })}
                
                {currentHandSkeleton.points.map((point, index) => (
                  <circle
                    key={`point-${index}`}
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill="#ef4444"
                    opacity={point.confidence}
                  />
                ))}
              </svg>
            )}

            {/* Live Action Indicator */}
            {currentAction && isPlaying && (
              <div className="absolute bottom-32 left-1/2 transform -translate-x-1/2">
                <div className="glass-card rounded-xl px-6 py-3 flex items-center space-x-3">
                  <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
                  <span className="text-white text-sm font-light tracking-wide">
                    {currentAction}
                  </span>
                </div>
              </div>
            )}

            {/* Analysis Toggle Arrow */}
            {!isAnalysisOpen && (
              <button
                onClick={() => setIsAnalysisOpen(true)}
                className={cn(
                  "fixed left-3 top-1/2 -translate-y-1/2 z-50",
                  "glass-ultra rounded-full w-9 h-9 flex items-center justify-center",
                  "hover:glass-hover focus:outline-none focus:ring-2 focus:ring-white/20"
                )}
                data-testid="button-analysis-toggle"
              >
                <ChevronRight className="h-4 w-4 text-white/70" />
              </button>
            )}

            {/* Compact Analysis Card */}
            <div className={cn(
              "fixed left-6 top-1/2 -translate-y-1/2 w-72 z-40",
              "glass-ultra rounded-3xl shadow-2xl",
              "transition-all duration-300 ease-out",
              isAnalysisOpen ? "translate-x-0 opacity-100" : "-translate-x-[120%] opacity-0 pointer-events-none"
            )}>
              <div className="relative p-6 space-y-5">
                {/* Close Button */}
                <button
                  onClick={() => setIsAnalysisOpen(false)}
                  className={cn(
                    "absolute top-4 right-4 w-6 h-6 rounded-lg",
                    "flex items-center justify-center",
                    "hover:bg-white/10 transition-colors duration-200"
                  )}
                  data-testid="button-close-analysis"
                >
                  <X className="h-4 w-4 text-white/50" />
                </button>

                {/* Task Analysis */}
                <div className="space-y-2">
                  <h3 className="text-white/60 text-xs font-medium tracking-wider uppercase">Task Analysis</h3>
                  <p className="text-white text-base font-normal leading-relaxed">{taskProgress.title}</p>
                  {analysisData?.aiAnalysis && (
                    <div className="text-xs text-white/50">
                      Confidence: {taskProgress.confidence}%
                    </div>
                  )}
                </div>

                {/* Progress Bar */}
                <div className="space-y-3">
                  <h3 className="text-white/60 text-xs font-medium tracking-wider uppercase">Analysis Progress</h3>
                  <div className="space-y-2">
                    <div className="w-full bg-white/20 rounded-full h-2 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-emerald-500 h-full transition-all duration-1000 ease-out"
                        style={{ width: `${progressPercentage}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-white/60">
                      <span>Step {currentStep + 1} of {taskProgress.total}</span>
                      <span>{Math.round(progressPercentage)}% Complete</span>
                    </div>
                  </div>
                </div>

                {/* Task Steps */}
                <div className="space-y-4">
                  <h3 className="text-white/60 text-xs font-medium tracking-wider uppercase">Task Steps</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto" ref={stepsScrollRef}>
                    {taskProgress.timeline && taskProgress.timeline.length > 0 ? (
                      taskProgress.timeline
                        .map((step: any, index: number) => {
                          const isCompleted = index < currentStep;
                          const isCurrent = index === currentStep;
                          const isCurrentlyPlaying = index === currentStep && isPlaying;
                          const timestamp = step.timestamp || 0;
                          
                          return (
                            <button
                              key={index}
                              data-step-index={index}
                              onClick={() => seekToTimestamp(timestamp)}
                              className={cn(
                                "w-full text-left rounded-lg transition-all duration-200",
                                "hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/20",
                                isCompleted 
                                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 p-3" 
                                  : isCurrent
                                  ? "bg-blue-500/30 text-blue-200 border border-blue-400 shadow-lg shadow-blue-500/20 p-4 scale-105"
                                  : "bg-white/5 text-white/60 border border-white/10 p-3"
                              )}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <div className={cn(
                                    "w-2 h-2 rounded-full",
                                    isCompleted 
                                      ? "bg-emerald-400" 
                                      : isCurrent
                                      ? "bg-blue-400 animate-pulse"
                                      : "bg-white/30"
                                  )} />
                                  <span className="text-xs font-medium">Step {index + 1}</span>
                                </div>
                                <span className="text-xs text-white/50">{formatTime(timestamp)}</span>
                              </div>
                              <div className="mt-2 text-xs flex items-center space-x-2">
                                <span>{step.description || step.action || step.title || `Task step ${index + 1}`}</span>
                                {isCurrentlyPlaying && (
                                  <div className="flex items-center space-x-1 text-blue-300">
                                    <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" />
                                    <span className="text-xs">Playing</span>
                                  </div>
                                )}
                              </div>
                            </button>
                          );
                        })
                    ) : (
                      Array.from({ length: Math.min(currentStep + 1, taskProgress.total) }, (_, index) => {
                        const isCompleted = index < currentStep;
                        const isCurrent = index === currentStep;
                        const isCurrentlyPlaying = index === currentStep && isPlaying;
                        const timestamp = (index * duration) / taskProgress.total;
                        
                        return (
                          <button
                            key={index}
                            data-step-index={index}
                            onClick={() => seekToTimestamp(timestamp)}
                            className={cn(
                              "w-full text-left rounded-lg transition-all duration-200",
                              "hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/20",
                              isCompleted 
                                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 p-3" 
                                : isCurrent
                                ? "bg-blue-500/30 text-blue-200 border border-blue-400 shadow-lg shadow-blue-500/20 p-4 scale-105"
                                : "bg-white/5 text-white/60 border border-white/10 p-3"
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <div className={cn(
                                  "w-2 h-2 rounded-full",
                                  isCompleted 
                                    ? "bg-emerald-400" 
                                    : isCurrent
                                    ? "bg-blue-400 animate-pulse"
                                    : "bg-white/30"
                                )} />
                                <span className="text-xs font-medium">Step {index + 1}</span>
                              </div>
                              <span className="text-xs text-white/50">{formatTime(timestamp)}</span>
                            </div>
                            <div className="mt-2 text-xs flex items-center space-x-2">
                              <span>{isCompleted ? "Completed" : isCurrent ? "In Progress" : "Pending"}</span>
                              {isCurrentlyPlaying && (
                                <div className="flex items-center space-x-1 text-blue-300">
                                  <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" />
                                  <span className="text-xs">Playing</span>
                                </div>
                              )}
                            </div>
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Current Step Details */}
                {taskProgress.timeline && taskProgress.timeline.length > 0 && currentStep < taskProgress.timeline.length && (
                  <div className="space-y-3">
                    <h3 className="text-white/60 text-xs font-medium tracking-wider uppercase">Current Step Details</h3>
                    <div className="space-y-2">
                      {/* Actors */}
                      {taskProgress.timeline[currentStep]?.actors && taskProgress.timeline[currentStep].actors.length > 0 && (
                        <div className="space-y-1">
                          <h4 className="text-white/50 text-xs font-medium">Actors</h4>
                          <div className="flex flex-wrap gap-1">
                            {taskProgress.timeline[currentStep].actors.map((actor: string, index: number) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-full border border-blue-500/30"
                              >
                                {actor}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Objects */}
                      {taskProgress.timeline[currentStep]?.objects && taskProgress.timeline[currentStep].objects.length > 0 && (
                        <div className="space-y-1">
                          <h4 className="text-white/50 text-xs font-medium">Objects</h4>
                          <div className="flex flex-wrap gap-1">
                            {taskProgress.timeline[currentStep].objects.map((object: string, index: number) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-emerald-500/20 text-emerald-300 text-xs rounded-full border border-emerald-500/30"
                              >
                                {object}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                    </div>
                  </div>
                )}

                {/* Hand Tracking Stats */}
                {realTrackingData.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-white/60 text-xs font-medium tracking-wider uppercase">Tracking Data</h3>
                    <div className="space-y-1">
                      <p className="text-white text-sm">{realTrackingData.length} frames tracked</p>
                      <p className="text-white text-sm">{taskProgress.actors.length} hands detected</p>
                      {processingStats && (
                        <>
                          <p className="text-white text-sm">Processing time: {processingStats.processing_time_seconds}s</p>
                          <p className="text-white text-sm">Avg confidence: {processingStats.average_confidence}%</p>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

        {/* Floating Action */}
        {taskProgress.completed > 0 && (
          <div className="absolute top-6 right-6">
            <button
              onClick={() => onTransferToRobot?.()}
              className={cn(
                "glass-ultra rounded-2xl px-4 md:px-6 py-3 text-white font-light tracking-wide",
                "liquid-hover fluid-transform flex items-center space-x-2 md:space-x-3",
                "hover:glass-hover focus:outline-none focus:ring-2 focus:ring-white/20"
              )}
              data-testid="button-transfer-robot"
            >
              <Cpu className="h-4 w-4" />
              <span className="hidden sm:inline">Deploy to Robot</span>
              <span className="sm:hidden">Deploy</span>
            </button>
          </div>
        )}

        {/* Floating Circular Controls */}
        <div 
          className={cn(
            "absolute bottom-8 left-1/2 transform -translate-x-1/2 transition-all duration-500",
            showControls ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          )}
          onMouseMove={handleMouseMove}
        >
          <div className="flex items-center space-x-4">
            {/* Time Display - Left */}
            <div className="glass-subtle rounded-full px-3 py-1">
              <span className="text-white/70 text-xs font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>

            {/* Previous Step Circle */}
            <button
              onClick={() => {
                if (taskProgress.timeline && taskProgress.timeline.length > 0 && currentStep > 0) {
                  const prevStep = taskProgress.timeline[currentStep - 1];
                  const timestamp = prevStep.timestamp || 0;
                  seekToTimestamp(timestamp);
                }
              }}
              disabled={!taskProgress.timeline || taskProgress.timeline.length === 0 || currentStep <= 0}
              className={cn(
                "w-10 h-10 rounded-full glass-ultra flex items-center justify-center",
                "hover:glass-hover transition-all duration-300",
                "focus:outline-none focus:ring-2 focus:ring-white/20",
                "disabled:opacity-30 disabled:cursor-not-allowed",
                "hover:scale-110 active:scale-95"
              )}
              data-testid="button-prev-step"
              title="Previous step"
            >
              <ChevronLeft className="h-4 w-4 text-white/80" />
            </button>

            {/* Center Play/Pause Circle */}
            <button
              onClick={togglePlayPause}
              className={cn(
                "w-14 h-14 rounded-full glass-ultra flex items-center justify-center",
                "hover:glass-hover transition-all duration-300",
                "focus:outline-none focus:ring-2 focus:ring-white/20",
                "hover:scale-110 active:scale-95",
                "shadow-xl shadow-black/20"
              )}
              data-testid="button-play-pause"
              title={isPlaying ? "Pause (Space)" : "Play (Space)"}
            >
              {isPlaying ? 
                <Pause className="h-6 w-6 text-white" /> : 
                <Play className="h-6 w-6 text-white ml-0.5" />
              }
            </button>

            {/* Next Step Circle */}
            <button
              onClick={() => {
                if (taskProgress.timeline && taskProgress.timeline.length > 0 && currentStep < taskProgress.timeline.length - 1) {
                  const nextStep = taskProgress.timeline[currentStep + 1];
                  const timestamp = nextStep.timestamp || 0;
                  seekToTimestamp(timestamp);
                }
              }}
              disabled={!taskProgress.timeline || taskProgress.timeline.length === 0 || currentStep >= taskProgress.timeline.length - 1}
              className={cn(
                "w-10 h-10 rounded-full glass-ultra flex items-center justify-center",
                "hover:glass-hover transition-all duration-300",
                "focus:outline-none focus:ring-2 focus:ring-white/20",
                "disabled:opacity-30 disabled:cursor-not-allowed",
                "hover:scale-110 active:scale-95"
              )}
              data-testid="button-next-step"
              title="Next step"
            >
              <ChevronRight className="h-4 w-4 text-white/80" />
            </button>

            {/* Step Counter - Right */}
            <div className="glass-subtle rounded-full px-3 py-1">
              <span className="text-white/50 text-xs">
                Step {currentStep + 1} of {taskProgress.total}
              </span>
            </div>
          </div>
        </div>
          </>
        )}
      </div>
    </div>
  );
}