import VideoAnalysis from '../VideoAnalysis';

export default function VideoAnalysisExample() {
  const handleTransferToRobot = (annotations: any[]) => {
    console.log('Transferring annotations to robot:', annotations);
  };

  // No mock data - real video file should be provided
  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white">
      <p>VideoAnalysis component requires a real video file</p>
    </div>
  );
}