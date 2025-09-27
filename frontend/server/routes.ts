import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";

const upload = multer({ storage: multer.memoryStorage() });
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function registerRoutes(app: Express): Promise<Server> {
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

  // Get analysis result
  app.get("/api/ai/analysis/:job_id", async (req, res) => {
    try {
      const { job_id } = req.params;
      
      // Return mock analysis result
      res.json({
        task_description: "Hand Gesture Recognition and Object Manipulation",
        timeline: [
          { timestamp: 0.5, action: "Hand enters frame", confidence: 0.95 },
          { timestamp: 2.1, action: "Grip pattern detected", confidence: 0.89 },
          { timestamp: 3.7, action: "Object interaction", confidence: 0.92 },
          { timestamp: 5.2, action: "Task completion", confidence: 0.87 }
        ],
        robot_notes: "Complex manipulation task with high dexterity requirements. Recommend slower execution speed for accuracy.",
        confidence: 89,
        objects: ["Coffee Cup", "Smartphone", "Keyboard"],
        actors: ["Left Hand", "Right Hand"]
      });
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
