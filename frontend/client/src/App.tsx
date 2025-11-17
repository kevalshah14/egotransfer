import { useState } from "react";
import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/lib/auth";
import { AuthGuard } from "@/components/Auth";
import NotFound from "@/pages/not-found";
import VideoUpload from "@/components/VideoUpload";
import DetailedVideoAnalysis from "@/components/DetailedVideoAnalysis";
// import RobotControl from "@/components/RobotControl"; // Hidden for now
import Settings from "@/components/Settings";
import Navigation from "@/components/Navigation";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

function VideoProcessingApp() {
  const [currentPage, setCurrentPage] = useState<'upload' | 'analysis' | 'robot' | 'settings'>('upload'); // robot type kept for compatibility but page is hidden
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [annotations, setAnnotations] = useState<any[]>([]);

  const navigateWithTransition = (newPage: 'upload' | 'analysis' | 'robot' | 'settings') => {
    // Prevent navigation to robot page (hidden for now)
    if (newPage === 'robot') {
      return;
    }
    // Prevent navigation during processing except to settings
    if (isProcessing && newPage !== 'settings') {
      return;
    }
    
    setIsTransitioning(true);
    setCurrentPage(newPage);
    // Transition state will be managed by AnimatePresence
    setTimeout(() => setIsTransitioning(false), 400);
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
      // Get session for authenticated requests
      const session = localStorage.getItem("auth_session");
      const sessionParam = session ? `?session=${session}` : '';
      
      // Fetch job data
      const jobResponse = await fetch(`/jobs/${jobId}${sessionParam}`);
      if (!jobResponse.ok) {
        throw new Error('Failed to fetch job data');
      }
      const jobData = await jobResponse.json();
      
      // Fetch analysis data
      const analysisResponse = await fetch(`/ai/analysis/${jobId}${sessionParam}`);
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
    // Robot control page is hidden for now
    console.log('Robot control page is currently unavailable');
    // Extract robot commands from analysis data if available
    // if (analysisData?.handJobId) {
    //   // Pass the job ID so RobotControl can load the robot commands
    //   setAnnotations([{
    //     handJobId: analysisData.handJobId,
    //     robotCommandsUrl: analysisData.robotCommands
    //   }]);
    // }
    // navigateWithTransition('robot');
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
        // Robot control page hidden for now
        return <div className="min-h-screen flex items-center justify-center bg-black text-white">Robot Control page is currently unavailable</div>;
      case 'settings':
        return <Settings onViewJob={handleViewJob} />;
      default:
        return <VideoUpload onVideoUpload={handleVideoUpload} />;
    }
  };

  // Check for reduced motion preference
  const shouldReduceMotion = useReducedMotion();

  // Animation variants for smooth page transitions
  const pageVariants = {
    initial: {
      opacity: 0,
      y: shouldReduceMotion ? 0 : 20,
      scale: shouldReduceMotion ? 1 : 0.98,
    },
    animate: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: shouldReduceMotion ? 0.2 : 0.4,
        ease: [0.16, 1, 0.3, 1], // Custom easing for smooth feel
      },
    },
    exit: {
      opacity: 0,
      y: shouldReduceMotion ? 0 : -20,
      scale: shouldReduceMotion ? 1 : 0.98,
      transition: {
        duration: shouldReduceMotion ? 0.15 : 0.3,
        ease: [0.16, 1, 0.3, 1],
      },
    },
  };

  return (
    <div className="relative overflow-hidden min-h-screen bg-gradient-to-br from-slate-950 via-black to-slate-900">
      <Navigation 
        currentPage={currentPage} 
        onPageChange={navigateWithTransition} 
        isProcessing={isProcessing}
      />
      <div className="relative min-h-screen">
        <AnimatePresence mode="sync" initial={false}>
          <motion.div
            key={currentPage}
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
            className={`${isTransitioning ? 'pointer-events-none' : ''} page-content w-full`}
            style={{ 
              willChange: 'opacity, transform',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              minHeight: '100vh'
            }}
          >
            {renderCurrentPage()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function Router() {
  return (
    <AuthGuard>
      <Switch>
        <Route path="/" component={VideoProcessingApp} />
        <Route component={NotFound} />
      </Switch>
    </AuthGuard>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <div className="dark min-h-screen">
            <Router />
            <Toaster />
          </div>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;