import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, jsonb, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

// Video processing schema
export const videos = pgTable("videos", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  filename: text("filename").notNull(),
  originalPath: text("original_path").notNull(),
  status: text("status").notNull().default("uploaded"), // uploaded, processing, completed, error
  duration: integer("duration"), // in seconds
  uploadedAt: timestamp("uploaded_at").defaultNow(),
  processedAt: timestamp("processed_at"),
});

export const annotations = pgTable("annotations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  videoId: varchar("video_id").notNull().references(() => videos.id),
  timestamp: integer("timestamp").notNull(), // milliseconds
  type: text("type").notNull(), // "object", "action", "hand_tracking"
  data: jsonb("data").notNull(), // flexible annotation data
  confidence: integer("confidence"), // 0-100
  createdAt: timestamp("created_at").defaultNow(),
});

export const robotStates = pgTable("robot_states", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  videoId: varchar("video_id").notNull().references(() => videos.id),
  jointAngles: jsonb("joint_angles").notNull(), // robot joint data
  timestamp: integer("timestamp").notNull(),
  status: text("status").notNull().default("pending"), // pending, transferred, executing, completed
  createdAt: timestamp("created_at").defaultNow(),
});

// Insert schemas
export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertVideoSchema = createInsertSchema(videos).pick({
  filename: true,
  originalPath: true,
  status: true,
  duration: true,
});

export const insertAnnotationSchema = createInsertSchema(annotations).pick({
  videoId: true,
  timestamp: true,
  type: true,
  data: true,
  confidence: true,
});

export const insertRobotStateSchema = createInsertSchema(robotStates).pick({
  videoId: true,
  jointAngles: true,
  timestamp: true,
  status: true,
});

// Types
export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type Video = typeof videos.$inferSelect;
export type InsertVideo = z.infer<typeof insertVideoSchema>;
export type Annotation = typeof annotations.$inferSelect;
export type InsertAnnotation = z.infer<typeof insertAnnotationSchema>;
export type RobotState = typeof robotStates.$inferSelect;
export type InsertRobotState = z.infer<typeof insertRobotStateSchema>;