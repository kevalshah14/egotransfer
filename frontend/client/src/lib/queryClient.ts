import { QueryClient, QueryFunction } from "@tanstack/react-query";
import { apiUrl } from './config';

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

export async function apiRequest(
  method: string,
  url: string,
  data?: unknown | undefined,
): Promise<Response> {
  // Get session from localStorage if available
  const session = localStorage.getItem("auth_session");
  const headers: Record<string, string> = data ? { "Content-Type": "application/json" } : {};
  
  // Build full URL with API base
  const fullUrl = apiUrl(url);
  
  // Add session as query parameter for backend compatibility
  const urlWithSession = session ? 
    (fullUrl.includes('?') ? `${fullUrl}&session=${session}` : `${fullUrl}?session=${session}`) : 
    fullUrl;
  
  const res = await fetch(urlWithSession, {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
    credentials: "include",
  });

  await throwIfResNotOk(res);
  return res;
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    // Get session from localStorage if available
    const session = localStorage.getItem("auth_session");
    let url = queryKey.join("/") as string;
    
    // Build full URL with API base
    url = apiUrl(url);
    
    // Add session as query parameter for backend compatibility
    if (session) {
      url = url.includes('?') ? `${url}&session=${session}` : `${url}?session=${session}`;
    }
    
    const res = await fetch(url, {
      credentials: "include",
    });

    if (unauthorizedBehavior === "returnNull" && res.status === 401) {
      return null;
    }

    await throwIfResNotOk(res);
    return await res.json();
  };

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});
