import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";

const upload = multer({ storage: multer.memoryStorage() });
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function registerRoutes(app: Express): Promise<Server> {
  // Authentication API Routes - Proxy to Backend
  
  // Google OAuth sign-in
  app.get("/api/auth/sign-in/google", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/sign-in/google`);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Auth sign-in error:", error);
      res.status(500).json({ error: "Failed to initiate sign-in" });
    }
  });

  // Google OAuth callback
  app.get("/api/auth/callback/google", async (req, res) => {
    try {
      const queryParams = new URLSearchParams(req.query as any).toString();
      const response = await fetch(`${BACKEND_URL}/api/auth/callback/google?${queryParams}`);
      
      // If backend redirects, follow it
      if (response.redirected) {
        return res.redirect(response.url);
      }
      
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Auth callback error:", error);
      res.status(500).json({ error: "Authentication failed" });
    }
  });

  // Get current user
  app.get("/api/auth/user", async (req, res) => {
    try {
      const session = req.query.session || req.cookies.auth_session;
      const url = session 
        ? `${BACKEND_URL}/api/auth/user?session=${session}`
        : `${BACKEND_URL}/api/auth/user`;
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        res.json(data);
      } else {
        res.status(response.status).json({ error: "Not authenticated" });
      }
    } catch (error) {
      console.error("Get user error:", error);
      res.status(500).json({ error: "Failed to get user" });
    }
  });

  // Sign out
  app.post("/api/auth/sign-out", async (req, res) => {
    try {
      const session = req.query.session || req.cookies.auth_session;
      const url = session 
        ? `${BACKEND_URL}/api/auth/sign-out?session=${session}`
        : `${BACKEND_URL}/api/auth/sign-out`;
      
      const response = await fetch(url, { method: "POST" });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Sign out error:", error);
      res.status(500).json({ error: "Failed to sign out" });
    }
  });

  // Hand Processing Routes - Proxy to Backend
  app.post("/hand/process", upload.single('file'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file provided" });
      }

      const formData = new FormData();
      formData.append('file', new Blob([new Uint8Array(req.file.buffer)]), req.file.originalname);
      
      // Forward all form fields
      Object.keys(req.body).forEach(key => {
        formData.append(key, req.body[key]);
      });

      const response = await fetch(`${BACKEND_URL}/hand/process`, {
        method: 'POST',
        body: formData as any,
      });

      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Hand process error:", error);
      res.status(500).json({ error: "Failed to process video" });
    }
  });

  app.get("/hand/tracking/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const session = req.query.session;
      const url = session 
        ? `${BACKEND_URL}/hand/tracking/${job_id}?session=${session}`
        : `${BACKEND_URL}/hand/tracking/${job_id}`;
      
      const response = await fetch(url);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Hand tracking error:", error);
      res.status(500).json({ error: "Failed to get tracking data" });
    }
  });

  app.get("/hand/stats/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const session = req.query.session;
      const url = session 
        ? `${BACKEND_URL}/hand/stats/${job_id}?session=${session}`
        : `${BACKEND_URL}/hand/stats/${job_id}`;
      
      const response = await fetch(url);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Hand stats error:", error);
      res.status(500).json({ error: "Failed to get stats" });
    }
  });

  app.get("/hand/video/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const response = await fetch(`${BACKEND_URL}/hand/video/${job_id}`);
      
      // Set content type and forward the video
      res.setHeader('Content-Type', response.headers.get('Content-Type') || 'video/mp4');
      const buffer = await response.arrayBuffer();
      res.send(Buffer.from(buffer));
    } catch (error) {
      console.error("Hand video error:", error);
      res.status(500).json({ error: "Failed to get video" });
    }
  });

  // Get job status - proxy to backend
  app.get("/jobs/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const session = req.query.session;
      const url = session 
        ? `${BACKEND_URL}/hand/jobs/${job_id}?session=${session}`
        : `${BACKEND_URL}/hand/jobs/${job_id}`;
      
      const response = await fetch(url);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Job status error:", error);
      res.status(500).json({ error: "Failed to get job status" });
    }
  });

  app.get("/hand/commands/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const session = req.query.session;
      const url = session 
        ? `${BACKEND_URL}/hand/commands/${job_id}?session=${session}`
        : `${BACKEND_URL}/hand/commands/${job_id}`;
      
      const response = await fetch(url);
      
      // Set content type and forward the file
      res.setHeader('Content-Type', response.headers.get('Content-Type') || 'application/json');
      const buffer = await response.arrayBuffer();
      res.send(Buffer.from(buffer));
    } catch (error) {
      console.error("Hand commands error:", error);
      res.status(500).json({ error: "Failed to get commands" });
    }
  });

  // Robot Control API Routes
  
  // Get robot status
  app.get("/api/robot/status", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/status`);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot status error:", error);
      res.status(500).json({ error: "Failed to get robot status" });
    }
  });

  // Execute robot command
  app.post("/api/robot/command", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot command error:", error);
      res.status(500).json({ error: "Failed to execute robot command" });
    }
  });

  // Connect to robot
  app.post("/api/robot/connect", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/connect`, {
        method: "POST"
      });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot connect error:", error);
      res.status(500).json({ error: "Failed to connect to robot" });
    }
  });

  // Disconnect from robot
  app.post("/api/robot/disconnect", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/disconnect`, {
        method: "POST"
      });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot disconnect error:", error);
      res.status(500).json({ error: "Failed to disconnect from robot" });
    }
  });

  // Home robot
  app.post("/api/robot/home", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/home`, {
        method: "POST"
      });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot home error:", error);
      res.status(500).json({ error: "Failed to home robot" });
    }
  });

  // Emergency stop
  app.post("/api/robot/emergency_stop", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/emergency_stop`, {
        method: "POST"
      });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot emergency stop error:", error);
      res.status(500).json({ error: "Failed to emergency stop robot" });
    }
  });

  // Get robot capabilities
  app.get("/api/robot/capabilities", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/capabilities`);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot capabilities error:", error);
      res.status(500).json({ error: "Failed to get robot capabilities" });
    }
  });

  // Get robot position
  app.get("/api/robot/position", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/robot/position`);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Robot position error:", error);
      res.status(500).json({ error: "Failed to get robot position" });
    }
  });

  // AI Analysis API Routes

  // Analyze video with AI
  app.post("/api/ai/analyze", upload.single('file'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file provided" });
      }

      // Create job in storage
      const job = await storage.createJob(req.file.originalname || 'unknown.mp4');
      
      // Simulate analysis processing
      setTimeout(async () => {
        try {
          // Update job with completion data
          await storage.updateJob(job.id, {
            status: 'completed',
            taskDescription: 'Hand Gesture Recognition and Object Manipulation',
            confidence: 89
          });
          console.log(`Mock analysis job ${job.id} completed`);
        } catch (error) {
          console.error('Failed to update job:', error);
          await storage.updateJob(job.id, { status: 'failed' });
        }
      }, 2000);

      res.json({
        job_id: job.id,
        message: "Analysis started successfully",
        status: "pending"
      });
    } catch (error) {
      console.error("AI analyze error:", error);
      res.status(500).json({ error: "Failed to analyze video" });
    }
  });

  // Get analysis result - proxy to backend
  app.get("/ai/analysis/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const session = req.query.session;
      const url = session 
        ? `${BACKEND_URL}/ai/analysis/${job_id}?session=${session}`
        : `${BACKEND_URL}/ai/analysis/${job_id}`;
      
      const response = await fetch(url);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("AI analysis result error:", error);
      res.status(500).json({ error: "Failed to get analysis result" });
    }
  });

  // Get analysis result (legacy /api prefix)
  app.get("/api/ai/analysis/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const session = req.query.session;
      const url = session 
        ? `${BACKEND_URL}/ai/analysis/${job_id}?session=${session}`
        : `${BACKEND_URL}/ai/analysis/${job_id}`;
      
      const response = await fetch(url);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("AI analysis result error:", error);
      res.status(500).json({ error: "Failed to get analysis result" });
    }
  });

  // Get available AI models
  app.get("/api/ai/models", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/ai/models`);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("AI models error:", error);
      res.status(500).json({ error: "Failed to get AI models" });
    }
  });

  // Analyze existing video
  app.post("/api/ai/analyze_existing/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const formData = new URLSearchParams();
      
      if (req.body.include_task_analysis !== undefined) {
        formData.append('include_task_analysis', req.body.include_task_analysis);
      }
      if (req.body.include_movement_analysis !== undefined) {
        formData.append('include_movement_analysis', req.body.include_movement_analysis);
      }
      if (req.body.analysis_detail_level !== undefined) {
        formData.append('analysis_detail_level', req.body.analysis_detail_level);
      }

      const response = await fetch(`${BACKEND_URL}/ai/analyze_existing/${job_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("AI analyze existing error:", error);
      res.status(500).json({ error: "Failed to analyze existing video" });
    }
  });

  // Reanalyze video
  app.post("/api/ai/reanalyze/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      const response = await fetch(`${BACKEND_URL}/ai/reanalyze/${job_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("AI reanalyze error:", error);
      res.status(500).json({ error: "Failed to reanalyze video" });
    }
  });

  // Job History API Routes
  
  // Get all jobs - proxy to backend Python server
  app.get("/jobs", async (req, res) => {
    try {
      const response = await fetch(`${BACKEND_URL}/jobs`);
      if (!response.ok) {
        throw new Error(`Backend responded with status ${response.status}`);
      }
      const data = await response.json();
      // Return just the jobs array, not the full response object
      res.json(data.jobs || []);
    } catch (error) {
      console.error("Get jobs error:", error);
      res.status(500).json({ error: "Failed to get jobs" });
    }
  });

  // Get all jobs - legacy endpoint
  app.get("/api/jobs/history", async (req, res) => {
    try {
      const jobs = await storage.getAllJobs();
      res.json(jobs);
    } catch (error) {
      console.error("Get jobs error:", error);
      res.status(500).json({ error: "Failed to get jobs" });
    }
  });

  // Delete specific job - proxy to backend Python server
  app.delete("/jobs/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const response = await fetch(`${BACKEND_URL}/jobs/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        res.json({ success: true });
      } else if (response.status === 404) {
        res.status(404).json({ error: "Job not found" });
      } else {
        throw new Error(`Backend responded with status ${response.status}`);
      }
    } catch (error) {
      console.error("Delete job error:", error);
      res.status(500).json({ error: "Failed to delete job" });
    }
  });

  // Clear all jobs - proxy to backend Python server
  app.delete("/jobs", async (req, res) => {
    try {
      // For now, we'll implement this by deleting jobs individually
      // since the backend doesn't have a clear all endpoint
      const jobsResponse = await fetch(`${BACKEND_URL}/jobs`);
      if (!jobsResponse.ok) {
        throw new Error(`Backend responded with status ${jobsResponse.status}`);
      }
      const jobsData = await jobsResponse.json();
      const jobs = jobsData.jobs || [];
      
      // Delete each job individually
      for (const job of jobs) {
        try {
          await fetch(`${BACKEND_URL}/jobs/${job.job_id}`, {
            method: 'DELETE'
          });
        } catch (error) {
          console.warn(`Failed to delete job ${job.job_id}:`, error);
        }
      }
      
      res.json({ success: true });
    } catch (error) {
      console.error("Clear jobs error:", error);
      res.status(500).json({ error: "Failed to clear jobs" });
    }
  });

  // Delete specific job - legacy endpoint
  app.delete("/api/jobs/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const deleted = await storage.deleteJob(id);
      if (deleted) {
        res.json({ success: true });
      } else {
        res.status(404).json({ error: "Job not found" });
      }
    } catch (error) {
      console.error("Delete job error:", error);
      res.status(500).json({ error: "Failed to delete job" });
    }
  });

  // Clear all jobs - legacy endpoint
  app.delete("/api/jobs/clear", async (req, res) => {
    try {
      await storage.clearAllJobs();
      res.json({ success: true });
    } catch (error) {
      console.error("Clear jobs error:", error);
      res.status(500).json({ error: "Failed to clear jobs" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
