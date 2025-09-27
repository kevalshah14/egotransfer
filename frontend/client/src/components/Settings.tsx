import { useState, useEffect, useMemo } from 'react';
import { Clock, FileVideo, Trash2, RefreshCw, Download, BarChart, CheckCircle, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

interface Job {
  job_id: string;
  video_name: string;
  created_at: string;
  status: 'completed' | 'failed' | 'pending' | 'processing';
  progress: number;
  message: string;
  processed_files?: Record<string, string>;
}

// Helper functions
const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'text-emerald-400';
    case 'failed':
      return 'text-red-400';
    case 'pending':
      return 'text-yellow-400';
    case 'processing':
      return 'text-blue-400';
    default:
      return 'text-white/60';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4" />;
    case 'failed':
      return <X className="h-4 w-4" />;
    case 'pending':
      return <Clock className="h-4 w-4" />;
    case 'processing':
      return <RefreshCw className="h-4 w-4 animate-spin" />;
    default:
      return <FileVideo className="h-4 w-4" />;
  }
};

const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleDateString();
  } catch {
    return 'Invalid date';
  }
};

interface SettingsProps {
  onViewJob?: (jobId: string) => void;
}

const viewJob = (jobId: string, onViewJob?: (jobId: string) => void) => {
  console.log('Viewing job:', jobId);
  if (onViewJob) {
    onViewJob(jobId);
  }
};

export default function Settings({ onViewJob }: SettingsProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch system stats
  const { data: systemStats } = useQuery({
    queryKey: ['/stats'],
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch job history
  const { data: jobsData, isLoading, error } = useQuery<any>({
    queryKey: ['/jobs'],
    refetchInterval: 5000,
  });

  // Ensure jobs is always an array with proper error handling
  const jobs = useMemo(() => {
    if (error) {
      console.error('Error fetching jobs:', error);
      return [];
    }
    if (!jobsData) {
      return [];
    }
    // Handle both array format and response object format
    if (Array.isArray(jobsData)) {
      return jobsData;
    }
    if (jobsData.jobs && Array.isArray(jobsData.jobs)) {
      return jobsData.jobs;
    }
    console.warn('Jobs data is not in expected format:', jobsData);
    return [];
  }, [jobsData, error]);

  // Delete job mutation
  const deleteJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      const response = await fetch(`/jobs/${jobId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete job');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/jobs'] });
      toast({ title: "Job deleted", description: "Job has been removed from history." });
    },
    onError: () => {
      toast({ 
        title: "Delete failed", 
        description: "Could not delete job.",
        variant: "destructive"
      });
    }
  });

  // Clear all jobs mutation
  const clearAllMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/jobs', {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to clear jobs');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/jobs'] });
      toast({ title: "History cleared", description: "All jobs have been removed from history." });
    },
    onError: () => {
      toast({ 
        title: "Clear failed", 
        description: "Could not clear job history.",
        variant: "destructive"
      });
    }
  });

  // Download functions
  const downloadProcessedVideo = async (jobId: string) => {
    try {
      const response = await fetch(`/hand/video/${jobId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processed_video_${jobId}.mp4`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast({ title: "Video downloaded successfully" });
      } else {
        throw new Error('Failed to download video');
      }
    } catch (error) {
      toast({ 
        title: "Download failed", 
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive" 
      });
    }
  };

  const downloadRobotCommands = async (jobId: string) => {
    try {
      const response = await fetch(`/hand/commands/${jobId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `robot_commands_${jobId}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast({ title: "Robot commands downloaded successfully" });
      } else {
        throw new Error('Failed to download commands');
      }
    } catch (error) {
      toast({ 
        title: "Download failed", 
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive" 
      });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-emerald-400';
      case 'failed':
        return 'text-red-400';
      case 'pending':
        return 'text-yellow-400';
      default:
        return 'text-white/50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-black to-slate-900 flex items-center justify-center p-4 relative overflow-hidden page-transition">
      {/* Atmospheric Background */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl float-gentle"></div>
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-purple-500/8 rounded-full blur-3xl" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-emerald-500/6 rounded-full blur-3xl" style={{animationDelay: '4s'}}></div>
      </div>

      <div className="max-w-4xl w-full space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center space-y-3">
          <h1 className="text-3xl font-ultra-light text-glass">Settings</h1>
          <p className="text-white/50 text-sm font-light tracking-wide">View and manage your analysis jobs</p>
        </div>

        {/* Job History */}
        <div className="glass-ultra rounded-3xl p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-light text-glass">Job History</h2>
            <div className="flex items-center space-x-3">
              {jobs.length > 0 && (
                <button
                  onClick={() => clearAllMutation.mutate()}
                  disabled={clearAllMutation.isPending}
                  className={cn(
                    "glass-card rounded-xl px-4 py-2 text-red-400 text-sm font-light",
                    "hover:glass-hover focus:outline-none focus:ring-2 focus:ring-red-400/30",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                  data-testid="button-clear-all"
                >
                  Clear All
                </button>
              )}
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ['/jobs'] })}
                className={cn(
                  "glass-card rounded-xl px-4 py-2 text-white/70 text-sm font-light",
                  "hover:glass-hover focus:outline-none focus:ring-2 focus:ring-white/20"
                )}
                data-testid="button-refresh"
              >
                <RefreshCw className="h-4 w-4 inline mr-2" />
                Refresh
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="text-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-white/50 mx-auto mb-4" />
              <p className="text-white/50">Loading job history...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <FileVideo className="h-16 w-16 text-red-400/50 mx-auto mb-4" />
              <p className="text-red-400 text-lg mb-2">Error loading jobs</p>
              <p className="text-white/30 text-sm">Please try refreshing or check your connection</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12">
              <FileVideo className="h-16 w-16 text-white/30 mx-auto mb-4" />
              <p className="text-white/50 text-lg mb-2">No jobs yet</p>
              <p className="text-white/30 text-sm">Upload and analyze videos to see them here</p>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job: Job) => (
                <div
                  key={job.job_id}
                  className={cn(
                    "glass-card rounded-2xl p-6",
                    "hover:glass-hover transition-all duration-300",
                    job.status === 'completed' && "border border-emerald-500/20",
                    job.status === 'failed' && "border border-red-500/20",
                    job.status === 'processing' && "border border-blue-500/20",
                    job.status === 'pending' && "border border-yellow-500/20"
                  )}
                  data-testid={`job-${job.job_id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="w-12 h-12 glass-subtle rounded-xl flex items-center justify-center">
                        {getStatusIcon(job.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-white font-light truncate">{job.video_name}</h3>
                          <div className={cn("flex items-center space-x-1", getStatusColor(job.status))}>
                            <span className="text-sm font-light capitalize">{job.status}</span>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-center space-x-4 text-sm text-white/50">
                            <span>Progress: {job.progress}%</span>
                            <span>Created: {formatDate(job.created_at)}</span>
                          </div>
                          <p className="text-white/70 text-sm truncate">{job.message}</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => viewJob(job.job_id, onViewJob)}
                        className={cn(
                          "px-4 py-2 rounded-xl glass-subtle text-white/70",
                          "hover:glass-hover hover:text-white/90",
                          "focus:outline-none focus:ring-2 focus:ring-white/20"
                        )}
                        title="View job details"
                      >
                        <FileVideo className="h-4 w-4 inline mr-2" />
                        View
                      </button>
                      <button
                        onClick={() => deleteJobMutation.mutate(job.job_id)}
                        disabled={deleteJobMutation.isPending}
                        className={cn(
                          "px-4 py-2 rounded-xl glass-subtle text-red-400/70",
                          "hover:glass-hover hover:text-red-400/90",
                          "focus:outline-none focus:ring-2 focus:ring-red-400/30",
                          "disabled:opacity-50 disabled:cursor-not-allowed"
                        )}
                        title="Delete job"
                      >
                        <Trash2 className="h-4 w-4 inline mr-2" />
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}