import { type User, type InsertUser } from "@shared/schema";
import { randomUUID } from "crypto";

// modify the interface with any CRUD methods
// you might need

export interface Job {
  id: string;
  filename: string;
  createdAt: string;
  status: 'completed' | 'failed' | 'pending';
  taskDescription?: string;
  confidence?: number;
}

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Job management methods
  createJob(filename: string): Promise<Job>;
  getJob(id: string): Promise<Job | undefined>;
  getAllJobs(): Promise<Job[]>;
  updateJob(id: string, updates: Partial<Job>): Promise<Job | undefined>;
  deleteJob(id: string): Promise<boolean>;
  clearAllJobs(): Promise<void>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private jobs: Map<string, Job>;

  constructor() {
    this.users = new Map();
    this.jobs = new Map();
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  // Job management methods
  async createJob(filename: string): Promise<Job> {
    const id = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const job: Job = {
      id,
      filename,
      createdAt: new Date().toISOString(),
      status: 'pending',
    };
    this.jobs.set(id, job);
    return job;
  }

  async getJob(id: string): Promise<Job | undefined> {
    return this.jobs.get(id);
  }

  async getAllJobs(): Promise<Job[]> {
    return Array.from(this.jobs.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  async updateJob(id: string, updates: Partial<Job>): Promise<Job | undefined> {
    const job = this.jobs.get(id);
    if (job) {
      const updatedJob = { ...job, ...updates };
      this.jobs.set(id, updatedJob);
      return updatedJob;
    }
    return undefined;
  }

  async deleteJob(id: string): Promise<boolean> {
    return this.jobs.delete(id);
  }

  async clearAllJobs(): Promise<void> {
    this.jobs.clear();
  }
}

export const storage = new MemStorage();
