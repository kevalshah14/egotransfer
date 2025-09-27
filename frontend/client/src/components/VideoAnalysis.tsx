import { useState, useRef, useEffect } from 'react';
import { Play, Pause, SkipBack, SkipForward, Send, Eye, Hand, Zap } from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import GlassCard from './GlassCard';
import { cn } from '@/lib/utils';

interface Annotation {
  id: string;
  timestamp: number;
  type: 'object' | 'action' | 'hand_tracking';
  data: any;
  confidence: number;
}

interface VideoAnalysisProps {
  videoFile?: File;
  onTransferToRobot?: (annotations: Annotation[]) => void;
}

export default function VideoAnalysis({ videoFile, onTransferToRobot }: VideoAnalysisProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // Fetch real annotations when component mounts
    if (videoFile) {
      setIsProcessing(true);
      // Note: This component is not used in the main app flow
      // Real data fetching would need to be implemented if used
      setIsProcessing(false);
      setAnnotations([]); // No mock data - empty array
    }
  }, [videoFile]);

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeek = (value: number[]) => {
    if (videoRef.current) {
      videoRef.current.currentTime = value[0];
      setCurrentTime(value[0]);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getAnnotationIcon = (type: string) => {
    switch (type) {
      case 'hand_tracking': return <Hand className="h-4 w-4" />;
      case 'object': return <Eye className="h-4 w-4" />;
      case 'action': return <Zap className="h-4 w-4" />;
      default: return <Eye className="h-4 w-4" />;
    }
  };

  const getAnnotationColor = (type: string) => {
    switch (type) {
      case 'hand_tracking': return 'text-blue-400 border-blue-400/50';
      case 'object': return 'text-green-400 border-green-400/50';
      case 'action': return 'text-yellow-400 border-yellow-400/50';
      default: return 'text-white border-white/50';
    }
  };

  const handleTransferToRobot = () => {
    const handTrackingAnnotations = annotations.filter(a => a.type === 'hand_tracking');
    onTransferToRobot?.(handTrackingAnnotations);
    console.log('Transferring to robot:', handTrackingAnnotations);
  };

  return (
    <div className="min-h-screen bg-black p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-white">Video Analysis</h1>
          <p className="text-white/70 text-lg">AI-powered hand tracking and object detection</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Video Player */}
          <div className="lg:col-span-2 space-y-6">
            <GlassCard className="relative overflow-hidden">
              <div className="aspect-video bg-black rounded-lg relative">
                {videoFile ? (
                  <>
                    <video
                      ref={videoRef}
                      className="w-full h-full object-cover rounded-lg"
                      src={URL.createObjectURL(videoFile)}
                      onTimeUpdate={handleTimeUpdate}
                      onLoadedMetadata={handleLoadedMetadata}
                      data-testid="video-player"
                    />
                    
                    {/* Annotation Overlays */}
                    {annotations
                      .filter(a => Math.abs(a.timestamp - currentTime) < 0.5)
                      .map(annotation => (
                        <div
                          key={annotation.id}
                          className={cn(
                            "absolute border-2 rounded-lg p-2 backdrop-blur-sm",
                            getAnnotationColor(annotation.type),
                            selectedAnnotation === annotation.id ? "bg-white/20" : "bg-black/20"
                          )}
                          style={{
                            left: annotation.data.handPosition?.x || annotation.data.position?.x || '50%',
                            top: annotation.data.handPosition?.y || annotation.data.position?.y || '50%',
                            transform: 'translate(-50%, -50%)'
                          }}
                          onClick={() => setSelectedAnnotation(annotation.id)}
                          data-testid={`annotation-${annotation.id}`}
                        >
                          <div className="flex items-center gap-1 text-xs">
                            {getAnnotationIcon(annotation.type)}
                            <span>{annotation.confidence}%</span>
                          </div>
                        </div>
                      ))
                    }
                  </>
                ) : (
                  <div className="flex items-center justify-center h-full text-white/50">
                    <div className="text-center">
                      <Eye className="h-16 w-16 mx-auto mb-4" />
                      <p>No video loaded</p>
                    </div>
                  </div>
                )}

                {isProcessing && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <div className="text-center text-white">
                      <div className="animate-spin rounded-full h-12 w-12 border-2 border-white border-t-transparent mx-auto mb-4"></div>
                      <p>Processing video with AI...</p>
                    </div>
                  </div>
                )}
              </div>
            </GlassCard>

            {/* Video Controls */}
            <GlassCard className="p-6">
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => handleSeek([Math.max(0, currentTime - 10)])}
                    className="apple-button-ghost apple-button-icon"
                    data-testid="button-skip-back"
                  >
                    <SkipBack className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={togglePlayPause}
                    className="apple-button-ghost apple-button-icon"
                    data-testid="button-play-pause"
                  >
                    {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </button>
                  
                  <button
                    onClick={() => handleSeek([Math.min(duration, currentTime + 10)])}
                    className="apple-button-ghost apple-button-icon"
                    data-testid="button-skip-forward"
                  >
                    <SkipForward className="h-4 w-4" />
                  </button>

                  <span className="text-white/70 text-sm">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>

                <div className="relative w-full">
                  <Slider
                    value={[currentTime]}
                    max={duration}
                    step={0.1}
                    onValueChange={handleSeek}
                    className="w-full"
                    data-testid="slider-timeline"
                  />
                  
                  {/* Keypoint markers */}
                  <div className="absolute top-0 left-0 right-0 h-full pointer-events-none">
                    {annotations.map(annotation => {
                      const position = duration > 0 ? (annotation.timestamp / duration) * 100 : 0;
                      const markerColor = annotation.type === 'hand_tracking' 
                        ? 'bg-blue-400' 
                        : annotation.type === 'object' 
                        ? 'bg-green-400' 
                        : 'bg-yellow-400';
                      
                      return (
                        <div
                          key={annotation.id}
                          className={cn(
                            "absolute top-1/2 transform -translate-y-1/2 w-2 h-2 rounded-full pointer-events-auto cursor-pointer transition-all hover:scale-125",
                            markerColor,
                            selectedAnnotation === annotation.id ? "scale-125 ring-2 ring-white" : ""
                          )}
                          style={{ left: `${position}%` }}
                          onClick={() => {
                            handleSeek([annotation.timestamp]);
                            setSelectedAnnotation(annotation.id);
                          }}
                          title={`${annotation.type.replace('_', ' ')} - ${annotation.timestamp.toFixed(1)}s`}
                          data-testid={`timeline-marker-${annotation.id}`}
                        />
                      );
                    })}
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Annotations Panel */}
          <div className="space-y-6">
            <GlassCard className="p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Annotations</h3>
              
              {isProcessing ? (
                <div className="text-center py-8">
                  <div className="animate-pulse text-white/70">
                    Analyzing video...
                  </div>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {annotations.map(annotation => (
                    <div
                      key={annotation.id}
                      className={cn(
                        "p-3 rounded-lg border cursor-pointer transition-all",
                        selectedAnnotation === annotation.id 
                          ? "bg-white/20 border-white/40" 
                          : "bg-white/5 border-white/20 hover:bg-white/10"
                      )}
                      onClick={() => setSelectedAnnotation(annotation.id)}
                      data-testid={`annotation-item-${annotation.id}`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={getAnnotationColor(annotation.type)}>
                          {getAnnotationIcon(annotation.type)}
                        </div>
                        <span className="text-white font-medium capitalize">
                          {annotation.type.replace('_', ' ')}
                        </span>
                        <span className="text-white/70 text-sm ml-auto">
                          {formatTime(annotation.timestamp)}
                        </span>
                      </div>
                      <div className="text-white/80 text-sm">
                        Confidence: {annotation.confidence}%
                      </div>
                      {annotation.data.object && (
                        <div className="text-white/70 text-sm">
                          Object: {annotation.data.object}
                        </div>
                      )}
                      {annotation.data.action && (
                        <div className="text-white/70 text-sm">
                          Action: {annotation.data.action}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>

            {/* Transfer to Robot */}
            {annotations.length > 0 && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-semibold text-white mb-4">Robot Control</h3>
                <p className="text-white/70 text-sm mb-4">
                  Transfer hand tracking data to robot for motion replication
                </p>
                <button
                  onClick={handleTransferToRobot}
                  className="w-full apple-button-primary apple-button-large"
                  data-testid="button-transfer-robot"
                >
                  <Send className="h-4 w-4 mr-2" />
                  Transfer to Robot
                </button>
              </GlassCard>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}