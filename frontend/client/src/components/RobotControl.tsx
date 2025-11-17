import { useState, useEffect } from 'react';
import { Activity, Zap, AlertCircle, CheckCircle, RotateCcw, Play, Square, Wifi, Battery, Thermometer, Clock, Target, Cpu } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient';
import { useToast } from '@/hooks/use-toast';
import { apiUrl } from '@/lib/config';

interface JointAngle {
  name: string;
  current: number;
  target: number;
  min: number;
  max: number;
}

interface RobotControlProps {
  annotations?: any[];
}

interface RobotStatus {
  connected: boolean;
  homed: boolean;
  playing: boolean;
  commands_loaded: number;
  current_position: Record<string, number>;
  battery_level?: number;
  temperature?: number;
  network_latency?: number;
  last_update?: string;
  error?: string;
}

interface RobotPosition {
  [key: string]: number;
}

export default function RobotControl({ annotations = [] }: RobotControlProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [executionProgress, setExecutionProgress] = useState(0);

  // Load robot commands from hand processing job
  const loadCommands = async (jobId: string) => {
    try {
      const response = await fetch(`/hand/commands/${jobId}`);
      if (response.ok) {
        // Commands file will be downloaded and can be loaded into robot
        toast({ title: "Robot commands loaded successfully" });
        queryClient.invalidateQueries({ queryKey: ['/robot/status'] });
      } else {
        throw new Error('Failed to load commands');
      }
    } catch (error) {
      toast({ 
        title: "Failed to load commands", 
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive" 
      });
    }
  };

  // Load commands when annotations are provided
  useEffect(() => {
    if (annotations.length > 0 && annotations[0]?.handJobId) {
      loadCommands(annotations[0].handJobId);
    }
  }, [annotations]);

  // Get robot status from backend
  const { data: robotStatus, isLoading: statusLoading, error: statusError } = useQuery<RobotStatus>({
    queryKey: ['/robot/status'],
    refetchInterval: 2000, // Refresh every 2 seconds
  });

  // Get robot position
  const { data: robotPosition } = useQuery<RobotPosition>({
    queryKey: ['/robot/position'],
    refetchInterval: 1000, // Refresh every second for real-time position
  });

  // Get robot capabilities
  const { data: robotCapabilities } = useQuery({
    queryKey: ['/robot/capabilities'],
  });

  // Robot command mutations
  const connectMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/robot/command', {
        action: 'connect'
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/robot/status'] });
      toast({ title: "Robot connected successfully" });
    },
    onError: (error: Error) => {
      toast({ title: "Failed to connect to robot", description: error.message, variant: "destructive" });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/robot/command', {
        action: 'disconnect'
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/robot/status'] });
      toast({ title: "Robot disconnected successfully" });
    },
    onError: (error: Error) => {
      toast({ title: "Failed to disconnect robot", description: error.message, variant: "destructive" });
    },
  });

  const homeMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/robot/command', {
        action: 'home'
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/robot/status'] });
      queryClient.invalidateQueries({ queryKey: ['/robot/position'] });
      toast({ title: "Robot homed successfully" });
    },
    onError: (error: Error) => {
      toast({ title: "Failed to home robot", description: error.message, variant: "destructive" });
    },
  });

  const playMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/robot/command', {
        action: 'play',
        speed: 1,
        loop: false
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/robot/status'] });
      toast({ title: "Robot playback started" });
    },
    onError: (error: Error) => {
      toast({ title: "Failed to start playback", description: error.message, variant: "destructive" });
    },
  });

  const stopMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/robot/command', {
        action: 'stop'
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/robot/status'] });
      toast({ title: "Robot stopped" });
    },
    onError: (error: Error) => {
      toast({ title: "Failed to stop robot", description: error.message, variant: "destructive" });
    },
  });

  const emergencyStopMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/robot/emergency_stop');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/robot/status'] });
      toast({ title: "Emergency stop activated", variant: "destructive" });
    },
    onError: (error: Error) => {
      toast({ title: "Failed to emergency stop", description: error.message, variant: "destructive" });
    },
  });

  // Derived state from robot status
  const isConnected = robotStatus?.connected || false;
  const isExecuting = robotStatus?.playing || false;
  const isHomed = robotStatus?.homed || false;
  const commandsLoaded = robotStatus?.commands_loaded || 0;
  const currentPosition = robotStatus?.current_position || {};
  const hasError = !!robotStatus?.error;

  // Convert position data to joint angles format for display
  const jointAngles: JointAngle[] = Object.entries(currentPosition).map(([name, value], index) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    current: value as number,
    target: value as number, // Use current as target for now
    min: -180,
    max: 180,
  }));

  // System metrics from robot status
  const systemMetrics = {
    batteryLevel: robotStatus?.battery_level || 0,
    temperature: robotStatus?.temperature || 0,
    networkLatency: robotStatus?.network_latency || 0,
    lastUpdate: robotStatus?.last_update || new Date().toLocaleTimeString(),
    connected: isConnected,
    homed: isHomed,
    commandsLoaded,
  };

  const executeMotion = () => {
    if (isExecuting) {
      stopMutation.mutate();
    } else {
      playMutation.mutate();
    }
  };

  const stopExecution = () => {
    stopMutation.mutate();
  };

  const resetToHome = () => {
    homeMutation.mutate();
  };

  const connectRobot = () => {
    if (isConnected) {
      disconnectMutation.mutate();
    } else {
      connectMutation.mutate();
    }
  };

  const emergencyStop = () => {
    emergencyStopMutation.mutate();
  };

  const getStatusColor = () => {
    if (hasError) return 'text-red-400';
    if (isExecuting) return 'text-blue-400';
    if (isConnected && isHomed) return 'text-green-400';
    if (isConnected) return 'text-yellow-400';
    return 'text-white/70';
  };

  const getStatusIcon = () => {
    if (hasError) return <AlertCircle className="h-5 w-5" />;
    if (isExecuting) return <Activity className="h-5 w-5 animate-pulse" />;
    if (isConnected && isHomed) return <CheckCircle className="h-5 w-5" />;
    if (isConnected) return <Wifi className="h-5 w-5" />;
    return <Zap className="h-5 w-5" />;
  };

  const getStatusText = () => {
    if (statusLoading) return 'Connecting...';
    if (hasError) return `Error: ${robotStatus?.error}`;
    if (isExecuting) return 'Executing';
    if (isConnected && isHomed) return 'Ready';
    if (isConnected) return 'Connected - Not Homed';
    return 'Disconnected';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-black to-slate-900 p-6 page-transition">
      {/* Atmospheric Background */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-cyan-500/8 rounded-full blur-3xl float-gentle"></div>
        <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-blue-500/6 rounded-full blur-3xl" style={{animationDelay: '3s'}}></div>
      </div>
      
      <div className="relative z-10 max-w-7xl mx-auto space-elegant">
        {/* Minimal Header */}
        <div className="text-center space-y-3">
          <h1 className="text-3xl font-ultra-light text-glass">Robot Command Center</h1>
          <p className="text-white/50 text-sm font-light tracking-wide">Real-time control and monitoring</p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main Visualization */}
          <div className="xl:col-span-3 space-y-6">
            {/* Robot 3D View */}
            <div className="glass-ultra rounded-3xl p-8 aspect-video relative overflow-hidden">
              {/* 3D Visualization Area */}
              <div className="absolute inset-6 rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/30 flex items-center justify-center">
                <div className="text-center space-y-6">
                  <div className="relative">
                    <div className="w-40 h-40 mx-auto glass-subtle rounded-2xl flex items-center justify-center float-gentle">
                      <Cpu className="h-20 w-20 text-white/40" />
                    </div>
                    <div className="absolute inset-0 bg-cyan-400/10 rounded-2xl blur-xl"></div>
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-xl font-ultra-light text-glass">Robot Visualization</h3>
                    <p className="text-white/40 text-sm font-light">Current pose and target trajectory</p>
                  </div>
                </div>
              </div>

              {/* Connection Status */}
              <div className="absolute top-6 right-6">
                <div className={cn(
                  "glass-subtle rounded-xl px-4 py-2 flex items-center space-x-3",
                  isConnected ? "" : "border-red-400/30"
                )}>
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    isConnected ? "bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50" : "bg-red-400"
                  )} />
                  <span className={cn(
                    "text-sm font-light",
                    isConnected ? "text-white/80" : "text-red-400"
                  )}>
                    {isConnected ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>

              {/* Status Display */}
              <div className="absolute bottom-6 left-6 right-6">
                <div className="glass-card rounded-2xl p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={cn(
                        "w-10 h-10 rounded-xl glass-subtle flex items-center justify-center",
                        getStatusColor()
                      )}>
                        {getStatusIcon()}
                      </div>
                      <div className="space-y-1">
                        <p className={cn("font-light text-sm", getStatusColor())}>
                          {getStatusText()}
                        </p>
                        <p className="text-white/50 text-xs">
                          {isExecuting ? `Executing: ${executionProgress}%` : 'Awaiting commands'}
                        </p>
                      </div>
                    </div>
                    {isExecuting && (
                      <div className="flex items-center space-x-3">
                        <div className="glass-subtle rounded-full h-2 w-32 overflow-hidden">
                          <div 
                            className="bg-gradient-to-r from-cyan-400 to-blue-400 h-full transition-all duration-500 ease-out"
                            style={{ width: `${executionProgress}%` }}
                          />
                        </div>
                        <span className="text-white/70 text-xs font-light min-w-[3rem]">{executionProgress}%</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Command Center */}
            <div className="glass-ultra rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-light text-glass">Motion Commands</h3>
                <Target className="h-5 w-5 text-white/40" />
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <button
                  onClick={executeMotion}
                  disabled={!isConnected || isExecuting}
                  className={cn(
                    "glass-card rounded-xl p-4 flex flex-col items-center space-y-3",
                    "liquid-hover fluid-transform disabled:opacity-40 disabled:cursor-not-allowed",
                    "hover:glass-hover focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
                  )}
                  data-testid="button-execute"
                >
                  <Play className="h-6 w-6 text-white/70" />
                  <span className="text-sm font-light text-white">Execute</span>
                </button>
                
                <button
                  onClick={stopExecution}
                  disabled={!isExecuting}
                  className={cn(
                    "glass-card rounded-xl p-4 flex flex-col items-center space-y-3",
                    "liquid-hover fluid-transform disabled:opacity-40 disabled:cursor-not-allowed",
                    "hover:glass-hover focus:outline-none focus:ring-2 focus:ring-red-400/30"
                  )}
                  data-testid="button-stop"
                >
                  <Square className="h-6 w-6 text-white/70" />
                  <span className="text-sm font-light text-white">Stop</span>
                </button>
                
                <button
                  onClick={resetToHome}
                  disabled={isExecuting}
                  className={cn(
                    "glass-card rounded-xl p-4 flex flex-col items-center space-y-3",
                    "liquid-hover fluid-transform disabled:opacity-40 disabled:cursor-not-allowed",
                    "hover:glass-hover focus:outline-none focus:ring-2 focus:ring-white/20"
                  )}
                  data-testid="button-reset"
                >
                  <RotateCcw className="h-6 w-6 text-white/70" />
                  <span className="text-sm font-light text-white">Reset</span>
                </button>
              </div>
            </div>
          </div>

          {/* Control Sidebar */}
          <div className="space-y-6">
            {/* Joint Control */}
            <div className="glass-ultra rounded-2xl p-5">
              <div className="flex items-center space-x-3 mb-5">
                <Target className="h-4 w-4 text-white/50" />
                <h3 className="text-sm font-light text-white/70 tracking-wide">Joint Control</h3>
              </div>
              
              <div className="space-y-4">
                {jointAngles.map((joint, index) => (
                  <div key={joint.name} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-white/80 text-xs font-light">{joint.name}</span>
                      <span className="text-white/50 text-[10px] font-light tracking-wider">
                        {joint.current.toFixed(1)}° → {joint.target.toFixed(1)}°
                      </span>
                    </div>
                    <div className="relative">
                      <div className="glass-subtle rounded-full h-1.5 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-400 to-blue-400 transition-all duration-500"
                          style={{
                            width: `${((joint.current - joint.min) / (joint.max - joint.min)) * 100}%`
                          }}
                        />
                      </div>
                      <div
                        className="absolute top-0 w-0.5 h-1.5 bg-yellow-400 rounded-full shadow-sm shadow-yellow-400/50"
                        style={{
                          left: `${((joint.target - joint.min) / (joint.max - joint.min)) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* System Telemetry */}
            <div className="glass-ultra rounded-2xl p-5">
              <div className="flex items-center space-x-3 mb-5">
                <Activity className="h-4 w-4 text-white/50" />
                <h3 className="text-sm font-light text-white/70 tracking-wide">System Health</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Battery className="h-3 w-3 text-white/40" />
                    <span className="text-white/60 text-xs font-light">Battery</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="glass-subtle rounded-full h-1 w-16 overflow-hidden">
                      <div 
                        className={cn(
                          "h-full transition-all duration-300",
                          systemMetrics.batteryLevel > 50 ? "bg-emerald-400" : 
                          systemMetrics.batteryLevel > 20 ? "bg-yellow-400" : "bg-red-400"
                        )}
                        style={{ width: `${systemMetrics.batteryLevel}%` }}
                      />
                    </div>
                    <span className="text-white/80 text-xs font-light min-w-[2rem]">{systemMetrics.batteryLevel}%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Thermometer className="h-3 w-3 text-white/40" />
                    <span className="text-white/60 text-xs font-light">Temperature</span>
                  </div>
                  <span className="text-white/80 text-xs font-light">{systemMetrics.temperature}°C</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Wifi className="h-3 w-3 text-white/40" />
                    <span className="text-white/60 text-xs font-light">Latency</span>
                  </div>
                  <span className="text-white/80 text-xs font-light">{systemMetrics.networkLatency}ms</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-3 w-3 text-white/40" />
                    <span className="text-white/60 text-xs font-light">Updated</span>
                  </div>
                  <span className="text-white/80 text-xs font-light">{systemMetrics.lastUpdate}</span>
                </div>
              </div>
            </div>

            {/* Transfer Status */}
            {annotations.length > 0 && (
              <div className="glass-ultra rounded-2xl p-5">
                <div className="flex items-center space-x-3 mb-4">
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                  <h3 className="text-sm font-light text-white/70 tracking-wide">Data Transfer</h3>
                </div>
                
                <div className="space-y-3 text-xs">
                  <div className="flex items-center space-x-2 text-emerald-400">
                    <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></div>
                    <span className="font-light">Motion data received</span>
                  </div>
                  <div className="text-white/60 font-light">
                    {annotations.length} tracking points
                  </div>
                  <div className="text-white/40 font-light">
                    Ready for execution
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}