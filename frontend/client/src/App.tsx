import { useState } from "react";
import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import VideoUpload from "@/components/VideoUpload";
import DetailedVideoAnalysis from "@/components/DetailedVideoAnalysis";
import RobotControl from "@/components/RobotControl";
import Settings from "@/components/Settings";
import Navigation from "@/components/Navigation";

function VideoProcessingApp() {
  const [currentPage, setCurrentPage] = useState<'upload' | 'analysis' | 'robot' | 'settings'>('upload');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [annotations, setAnnotations] = useState<any[]>([]);

  const navigateWithTransition = (newPage: 'upload' | 'analysis' | 'robot' | 'settings') => {
    // Prevent navigation during processing except to settings
    if (isProcessing && newPage !== 'settings') {
      return;
    }
    
    if ('startViewTransition' in document) {
      setIsTransitioning(true);
      // @ts-ignore - View Transitions API
      document.startViewTransition(() => {
        setCurrentPage(newPage);
      }).finished.finally(() => {
        setIsTransitioning(false);
      });
    } else {
      // Fallback transition for browsers without View Transitions API
      setIsTransitioning(true);
      const pageContent = (document as any).querySelector('.page-content');
      
      if (pageContent) {
        pageContent.classList.add('page-transition-exit');
        
        setTimeout(() => {
          setCurrentPage(newPage);
          pageContent.classList.remove('page-transition-exit');
          pageContent.classList.add('page-transition-enter');
          
          setTimeout(() => {
            pageContent.classList.remove('page-transition-enter');
            setIsTransitioning(false);
          }, 300);
        }, 200);
      } else {
        setCurrentPage(newPage);
        setIsTransitioning(false);
      }
    }
  };

  const handleVideoUpload = (file: File, analysisData?: any) => {
    console.log('App: handleVideoUpload called with:', { file: file.name, analysisData });
    setUploadedVideo(file);
    setVideoUrl(null); // Clear video URL for new uploads
    setAnalysisData(analysisData);
    navigateWithTransition('analysis');
    console.log('Video uploaded and processed, navigating to analysis');
    console.log('Analysis data received:', analysisData);
  };

  const handleViewJob = async (jobId: string) => {
    console.log('App: handleViewJob called with jobId:', jobId);
    
    try {
      // Fetch job data
      const jobResponse = await fetch(`/jobs/${jobId}`);
      if (!jobResponse.ok) {
        throw new Error('Failed to fetch job data');
      }
      const jobData = await jobResponse.json();
      
      // Fetch analysis data
      const analysisResponse = await fetch(`/ai/analysis/${jobId}`);
      if (!analysisResponse.ok) {
        throw new Error('Failed to fetch analysis data');
      }
      const analysisData = await analysisResponse.json();
      
      // Create combined data similar to upload flow
      const combinedData = {
        handJobId: jobId,
        aiJobId: jobId,
        handProcessing: jobData,
        aiAnalysis: analysisData,
        processedVideoUrl: `/hand/video/${jobId}`,
        trackingData: `/hand/tracking/${jobId}`,
        robotCommands: `/hand/commands/${jobId}`,
      };
      
      console.log('App: Combined data for job view:', combinedData);
      
      // Set the data and navigate to analysis
      setAnalysisData(combinedData);
      setUploadedVideo(null); // No file for old jobs
      setVideoUrl(`/hand/video/${jobId}`); // Use video URL for old jobs
      navigateWithTransition('analysis');
      
    } catch (error) {
      console.error('Error loading job for analysis:', error);
      // You could show a toast error here
    }
  };

  const handleTransferToRobot = () => {
    // Extract robot commands from analysis data if available
    if (analysisData?.handJobId) {
      // Pass the job ID so RobotControl can load the robot commands
      setAnnotations([{
        handJobId: analysisData.handJobId,
        robotCommandsUrl: analysisData.robotCommands
      }]);
    }
    navigateWithTransition('robot');
    console.log('Transferring to robot, navigating to robot control');
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'upload':
        return (
          <VideoUpload 
            onVideoUpload={handleVideoUpload} 
            onProcessingStart={() => setIsProcessing(true)}
            onProcessingComplete={() => setIsProcessing(false)}
          />
        );
      case 'analysis':
        return uploadedVideo || videoUrl ? (
          <DetailedVideoAnalysis 
            videoFile={uploadedVideo} 
            videoUrl={videoUrl || undefined}
            analysisData={analysisData} 
            onBack={() => navigateWithTransition('upload')} 
            onTransferToRobot={handleTransferToRobot} 
          />
        ) : (
          <div className="min-h-screen flex items-center justify-center bg-black text-white">
            No video loaded
          </div>
        );
      case 'robot':
        return <RobotControl annotations={annotations} />;
      case 'settings':
        return <Settings onViewJob={handleViewJob} />;
      default:
        return <VideoUpload onVideoUpload={handleVideoUpload} />;
    }
  };

  return (
    <div className="relative overflow-hidden">
      <Navigation 
        currentPage={currentPage} 
        onPageChange={navigateWithTransition} 
        isProcessing={isProcessing}
      />
      <div className={`${isTransitioning ? 'pointer-events-none' : ''} page-content`}>
        {renderCurrentPage()}
      </div>
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={VideoProcessingApp} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <div className="dark min-h-screen">
          <Router />
          <Toaster />
        </div>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;