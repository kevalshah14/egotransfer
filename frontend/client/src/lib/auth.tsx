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
    // Safety timeout to ensure loading never hangs
    const safetyTimeout = setTimeout(() => {
      console.warn("Auth loading timeout - forcing completion");
      setLoading(false);
    }, 5000);

    // Check for session in URL params (from OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");
    const sessionId = urlParams.get("session");

    if (token && sessionId) {
      console.log("OAuth callback detected, storing session...");
      // Store session
      localStorage.setItem("auth_session", sessionId);
      localStorage.setItem("auth_token", token);
      setSession(sessionId);
      
      // Clean up URL parameters - use full URL
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
      
      // Fetch user info - no reload needed, React will re-render
      fetchUser(sessionId)
        .then(() => {
          clearTimeout(safetyTimeout);
        })
        .catch((error) => {
          console.error("Failed to fetch user after OAuth:", error);
          clearTimeout(safetyTimeout);
          setLoading(false);
        });
    } else {
      // Check for existing session
      const storedSession = localStorage.getItem("auth_session");
      if (storedSession) {
        setSession(storedSession);
        fetchUser(storedSession).finally(() => {
          clearTimeout(safetyTimeout);
        });
      } else {
        setLoading(false);
        clearTimeout(safetyTimeout);
      }
    }

    return () => {
      clearTimeout(safetyTimeout);
    };
  }, []);

  const fetchUser = async (sessionId: string): Promise<void> => {
    try {
      console.log("Fetching user data with session:", sessionId.substring(0, 10) + "...");
      const response = await fetch(`/api/auth/user?session=${sessionId}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        console.log("User data fetched successfully:", userData.email);
        setUser(userData);
        setLoading(false);
        return Promise.resolve();
      } else if (response.status === 401) {
        console.warn("Session invalid (401)");
        // Session invalid, clear it
        localStorage.removeItem("auth_session");
        localStorage.removeItem("auth_token");
        setSession(null);
        setUser(null);
        setLoading(false);
        return Promise.reject(new Error("Session invalid"));
      } else {
        console.error("Unexpected response status:", response.status);
        setLoading(false);
        return Promise.reject(new Error(`HTTP ${response.status}`));
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

