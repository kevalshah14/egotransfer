-- Migration: Add is_admin column to users table
-- Run this SQL in your database to add the is_admin column

-- Add is_admin column (defaults to false for existing users)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT false;

-- Create index for faster admin queries
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);

-- Optional: Grant admin to specific users by email
-- UPDATE users SET is_admin = true WHERE email = 'admin@example.com';

