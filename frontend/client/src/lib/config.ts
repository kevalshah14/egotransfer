/**
 * Frontend Configuration
 * 
 * Handles environment-specific API configuration
 */

/**
 * Get the API base URL based on environment
 * - Development: uses Vite proxy (empty string) -> proxies to localhost:8000
 * - Production: uses VITE_API_BASE_URL env var or defaults to same origin
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Helper to build full API URL
 */
export function apiUrl(path: string): string {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  
  if (!API_BASE_URL) {
    // In development or same-origin deployment, use relative paths
    return `/${cleanPath}`;
  }
  
  // In production with separate backend, use full URL
  return `${API_BASE_URL}/${cleanPath}`;
}

console.log('API Configuration:', {
  base_url: API_BASE_URL || '(same origin)',
  mode: import.meta.env.MODE,
});

