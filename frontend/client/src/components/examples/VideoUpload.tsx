import VideoUpload from '../VideoUpload';

export default function VideoUploadExample() {
  const handleVideoUpload = (file: File) => {
    console.log('Video uploaded in example:', file.name);
  };

  return <VideoUpload onVideoUpload={handleVideoUpload} />;
}