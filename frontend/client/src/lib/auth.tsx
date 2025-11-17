import { useState, useEffect, createContext, useContext, ReactNode } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

interface AuthContextType {
  user: User | null;
  session: string | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for session in URL params (from OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");
    const sessionId = urlParams.get("session");

    if (token && sessionId) {
      // Store session
      localStorage.setItem("auth_session", sessionId);
      localStorage.setItem("auth_token", token);
      setSession(sessionId);
      
      // Clean up URL and reload to clear OAuth params
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Fetch user info and set loading to false
      fetchUser(sessionId).then(() => {
        // Force a re-render after successful auth
        window.location.href = window.location.pathname;
      });
    } else {
      // Check for existing session
      const storedSession = localStorage.getItem("auth_session");
      if (storedSession) {
        setSession(storedSession);
        fetchUser(storedSession);
      } else {
        setLoading(false);
      }
    }
  }, []);

  const fetchUser = async (sessionId: string): Promise<void> => {
    try {
      const response = await fetch(`/api/auth/user?session=${sessionId}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setLoading(false);
        return Promise.resolve();
      } else if (response.status === 401) {
        // Session invalid, clear it
        localStorage.removeItem("auth_session");
        localStorage.removeItem("auth_token");
        setSession(null);
        setUser(null);
        setLoading(false);
        return Promise.reject(new Error("Session invalid"));
      }
    } catch (error) {
      console.error("Failed to fetch user:", error);
      localStorage.removeItem("auth_session");
      localStorage.removeItem("auth_token");
      setSession(null);
      setUser(null);
      setLoading(false);
      return Promise.reject(error);
    }
  };

  const signInWithGoogle = async () => {
    try {
      const response = await fetch(`/api/auth/sign-in/google`, {
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get OAuth URL: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.url) {
        // Redirect to Google OAuth
        window.location.href = data.url;
      } else {
        console.error("No OAuth URL returned from server");
      }
    } catch (error) {
      console.error("Failed to initiate Google sign-in:", error);
    }
  };

  const signOut = async () => {
    try {
      if (session) {
        await fetch(`/api/auth/sign-out?session=${session}`, {
          method: "POST",
          credentials: "include",
        });
      }
    } catch (error) {
      console.error("Failed to sign out:", error);
    } finally {
      localStorage.removeItem("auth_session");
      localStorage.removeItem("auth_token");
      setUser(null);
      setSession(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signInWithGoogle, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

