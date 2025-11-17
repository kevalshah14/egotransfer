import { useState, useRef } from 'react';
import { Video, CheckCircle, Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMutation } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

interface VideoUploadProps {
  onVideoUpload?: (file: File, analysisData?: any) => void;
  onProcessingStart?: () => void;
  onProcessingComplete?: () => void;
}

interface ProcessingResponse {
  job_id: string;
  message: string;
  status: 'pending' | 'completed' | 'error';
}

interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  current_step: string;
  video_name: string;
  processed_files: Record<string, string>;
  error?: string;
}

interface AnalysisResult {
  task_description: string;
  timeline: any[];
  robot_notes: string;
  confidence: number;
  movement_patterns?: any[];
  detected_objects?: string[];
}

export default function VideoUpload({ onVideoUpload, onProcessingStart, onProcessingComplete }: VideoUploadProps) {
  const { toast } = useToast();
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState('');
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [eta, setEta] = useState('');
  const [isReadyToAnalyze, setIsReadyToAnalyze] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const videoFile = files.find(file => file.type.startsWith('video/'));
    
    if (videoFile) {
      handleFileUpload(videoFile);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('video/')) {
      handleFileUpload(file);
    }
  };

  // Hand processing and AI analysis mutation
  const processVideoMutation = useMutation({
    mutationFn: async (file: File): Promise<ProcessingResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('target_hand', 'right');
      formData.append('confidence_threshold', '0.7');
      formData.append('tracking_confidence', '0.5');
      formData.append('max_hands', '2');
      formData.append('generate_video', 'true');
      formData.append('generate_robot_commands', 'true');

      // Get session from localStorage if available
      const session = localStorage.getItem("auth_session");
      const url = session ? `/hand/process?session=${session}` : '/hand/process';

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to process video: ${response.statusText}`);
      }

      return response.json();
    },
    onSuccess: async (data) => {
      const handJobId = data.job_id;
      setIsProcessing(true);
      onProcessingStart?.();
      setAnalysisProgress('Processing hand tracking...');
      setCurrentStep('Hand Tracking');
      setProgressPercentage(0);
      setEta('');
      
      // Poll for hand processing completion (with small delay to avoid race condition)
      const pollForHandResults = async (): Promise<void> => {
        try {
          // Include session in status check
          const session = localStorage.getItem("auth_session");
          const statusUrl = session ? `/jobs/${handJobId}?session=${session}` : `/jobs/${handJobId}`;
          const response = await fetch(statusUrl);
          
          if (response.ok) {
            const jobStatus: JobStatus = await response.json();
            
            if (jobStatus.status === 'completed') {
              setCurrentStep('Complete');
              setProgressPercentage(100);
              setEta('');
              
              // Try to get AI analysis results (may not exist if AI analysis failed)
              const analysisUrl = session ? `/ai/analysis/${handJobId}?session=${session}` : `/ai/analysis/${handJobId}`;
              const analysisResponse = await fetch(analysisUrl);
              
              let analysisData: AnalysisResult | null = null;
              if (analysisResponse.ok) {
                try {
                  analysisData = await analysisResponse.json();
                  console.log('AI analysis results retrieved successfully');
                } catch (e) {
                  console.warn('Failed to parse AI analysis results:', e);
                }
              } else {
                console.warn('AI analysis not available (this is ok if AI failed):', analysisResponse.status);
              }
              
              // Combine job data with analysis (analysis may be null if AI failed)
              const combinedData = {
                handJobId,
                aiJobId: handJobId,
                handProcessing: jobStatus,
                aiAnalysis: analysisData || {
                  task_description: 'AI analysis unavailable',
                  timeline: [],
                  robot_notes: 'Hand tracking completed successfully, but AI analysis failed or is unavailable.',
                  confidence: 0
                },
                processedVideoUrl: `/hand/video/${handJobId}`,
                trackingData: `/hand/tracking/${handJobId}`,
                robotCommands: `/hand/commands/${handJobId}`,
              };
              
              console.log('Combined data for analysis:', combinedData);
              
              setTimeout(() => {
                setIsUploading(false);
                setIsProcessing(false);
                setAnalysisProgress('');
                setProgressPercentage(0);
                setCurrentStep('');
                setEta('');
                onProcessingComplete?.();
              }, 1000);
              onVideoUpload?.(uploadedFile!, combinedData);
              console.log('Video uploaded and processed:', uploadedFile!.name);
            } else if (jobStatus.status === 'error') {
              throw new Error(jobStatus.error || 'Hand processing failed');
            } else {
              // Still processing, poll again
              setTimeout(pollForHandResults, 1000); // Poll every 1 second for more responsive updates
              setAnalysisProgress(`Hand Processing: ${jobStatus.current_step || 'Processing'}...`);
              // Update progress based on job progress if available
              if (jobStatus.progress !== undefined) {
                console.log(`Progress update: ${jobStatus.progress}% - Step: ${jobStatus.current_step} - Message: ${jobStatus.message}`);
                setProgressPercentage(jobStatus.progress);
                setCurrentStep(jobStatus.current_step || 'Processing');
                // Extract ETA from progress message if available
                if (jobStatus.message && jobStatus.message.includes('ETA:')) {
                  const etaMatch = jobStatus.message.match(/ETA:\s*([0-9.]+)s/);
                  if (etaMatch) {
                    const etaSeconds = parseFloat(etaMatch[1]);
                    setEta(`${Math.round(etaSeconds)}s`);
                  }
                } else {
                  setEta(''); // Clear ETA if not in message
                }
              }
            }
          } else {
            throw new Error('Failed to get job status');
          }
        } catch (error) {
          console.error('Error polling for hand results:', error);
          setTimeout(pollForHandResults, 5000);
        }
      };

      setTimeout(pollForHandResults, 1000); // Reduced delay since backend now updates immediately
    },
    onError: (error: Error) => {
      setIsUploading(false);
      setIsProcessing(false);
      setAnalysisProgress('');
      setEta('');
      onProcessingComplete?.();
      toast({ 
        title: "Processing failed", 
        description: error.message, 
        variant: "destructive" 
      });
    },
  });

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file);
    setIsReadyToAnalyze(true);
  };

  const handleBeginAnalysis = () => {
    if (!uploadedFile) return;
    
    setIsUploading(true);
    setIsReadyToAnalyze(false);
    setAnalysisProgress('Uploading video...');
    setProgressPercentage(10);
    setCurrentStep('Upload');
    
    // Start hand processing and AI analysis
    processVideoMutation.mutate(uploadedFile);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-black to-slate-900 flex items-center justify-center p-4 relative overflow-hidden page-transition">
      {/* Atmospheric Background */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl float-gentle"></div>
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-purple-500/8 rounded-full blur-3xl" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-emerald-500/6 rounded-full blur-3xl" style={{animationDelay: '4s'}}></div>
      </div>
      
      <div className="max-w-xl w-full space-elegant relative z-10">

        {/* Main Upload Glass */}
        <div className="text-center space-elegant">
          {!isProcessing ? (
            <div>
              <div
                className={cn(
                  "relative cursor-pointer rounded-3xl overflow-hidden group",
                  "glass-ultra liquid-hover fluid-transform",
                  isDragging && "scale-105",
                  uploadedFile ? "glass-strong" : "",
                  isReadyToAnalyze && "pointer-events-none"
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={!isReadyToAnalyze ? openFileDialog : undefined}
                data-testid="upload-area"
              >
              <div className="p-20 text-center">
                {uploadedFile ? (
                  <div className="space-y-6">
                    <div className="relative">
                      <CheckCircle className="h-20 w-20 text-emerald-400 mx-auto drop-shadow-lg" />
                      <div className="absolute inset-0 bg-emerald-400/20 rounded-full blur-xl"></div>
                    </div>
                    <div className="space-y-3">
                      <h3 className="text-2xl font-light text-glass">Video Selected</h3>
                      <p className="text-white/60 text-sm font-light tracking-wide">{uploadedFile.name}</p>
                    </div>
                  </div>
                ) : (
                <div className="space-y-6">
                  <div className="relative">
                    {isUploading ? (
                      <div className="relative">
                        <Video className="h-20 w-20 text-white/40 mx-auto" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="animate-spin rounded-full h-12 w-12 border-2 border-white/30 border-t-white"></div>
                        </div>
                      </div>
                    ) : (
                      <div className="relative group">
                        <Video className="h-20 w-20 text-white/50 mx-auto transition-all duration-500 group-hover:text-white/70 group-hover:scale-110" />
                        <div className="absolute inset-0 bg-white/5 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-2xl font-ultra-light text-glass">
                      {isUploading ? 'Processing...' : 'Drop Video'}
                    </h3>
                    {isUploading && analysisProgress ? (
                      <div className="space-y-4 w-full max-w-md mx-auto">
                        <p className="text-white/70 text-sm font-light text-center">{analysisProgress}</p>
                        
                        {/* Enhanced Progress Bar */}
                        <div className="space-y-3">
                          <div className="relative w-full bg-white/10 rounded-full h-3 overflow-hidden shadow-inner">
                            <div 
                              className="bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500 h-full transition-all duration-1000 ease-out relative"
                              style={{ width: `${progressPercentage}%` }}
                            >
                              <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                              <div className="absolute right-0 top-0 w-1 h-full bg-white/40 shadow-lg"></div>
                            </div>
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-white/60 font-medium">{currentStep}</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                              <span className="text-white/70 font-semibold">{progressPercentage}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : !isUploading && (
                      <p className="text-white/40 text-xs font-light tracking-widest uppercase">MP4 · MOV · AVI</p>
                    )}
                  </div>
                </div>
              )}
            </div>
              </div>

              {/* Begin Analysis Button */}
              {isReadyToAnalyze && uploadedFile && (
                <div className="mt-6 space-y-4">
                  <button
                    onClick={handleBeginAnalysis}
                    className={cn(
                      "w-full px-8 py-4 rounded-2xl",
                      "glass-card liquid-hover fluid-transform",
                      "text-white font-light text-lg tracking-wide",
                      "transition-all duration-300",
                      "hover:glass-hover hover:scale-105",
                      "active:scale-95",
                      "relative overflow-hidden group",
                      "focus:outline-none focus:ring-2 focus:ring-white/20"
                    )}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-emerald-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    <span className="relative z-10 flex items-center justify-center gap-2">
                      <Play className="h-5 w-5" />
                      Begin Analysis
                    </span>
                  </button>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setUploadedFile(null);
                      setIsReadyToAnalyze(false);
                      if (fileInputRef.current) {
                        fileInputRef.current.value = '';
                      }
                    }}
                    className={cn(
                      "w-full px-6 py-3 rounded-xl",
                      "glass-subtle text-white/70",
                      "text-sm font-light tracking-wide",
                      "transition-all duration-300",
                      "hover:text-white hover:glass-strong hover:scale-[1.02]",
                      "active:scale-95",
                      "focus:outline-none focus:ring-2 focus:ring-white/10"
                    )}
                  >
                    Choose Different Video
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Processing View */
            <div className="glass-ultra rounded-3xl p-20 text-center">
              <div className="space-y-8">
                <div className="relative">
                  <Video className="h-20 w-20 text-white/40 mx-auto" />
                </div>
                
                <div className="space-y-6">
                  <h3 className="text-2xl font-ultra-light text-glass">Processing Video</h3>
                  
                  {analysisProgress && (
                    <div className="space-y-4 w-full max-w-md mx-auto">
                      <p className="text-white/70 text-sm font-light text-center">{analysisProgress}</p>
                      
                      {/* Enhanced Progress Bar */}
                      <div className="space-y-3">
                        <div className="relative w-full bg-white/10 rounded-full h-3 overflow-hidden shadow-inner">
                          <div 
                            className="bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500 h-full transition-all duration-1000 ease-out relative"
                            style={{ width: `${progressPercentage}%` }}
                          >
                            <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                            <div className="absolute right-0 top-0 w-1 h-full bg-white/40 shadow-lg"></div>
                          </div>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-white/60 font-medium">{currentStep}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                            <span className="text-white/70 font-semibold">{Math.round(progressPercentage)}%</span>
                            {eta && (
                              <span className="text-white/50 text-xs">ETA: {eta}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>


        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          onChange={handleFileSelect}
          className="hidden"
          data-testid="input-file"
        />
      </div>
    </div>
  );
}