import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut, User } from "lucide-react";
import { cn } from "@/lib/utils";

export function SignInButton() {
  const { signInWithGoogle, loading } = useAuth();

  return (
    <Button
      onClick={signInWithGoogle}
      disabled={loading}
      className={cn(
        "glass-card text-white hover:glass-hover",
        "liquid-hover fluid-transform-fast"
      )}
    >
      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
        <path
          fill="currentColor"
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
          fill="currentColor"
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
          fill="currentColor"
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
          fill="currentColor"
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
      </svg>
      Sign in with Google
    </Button>
  );
}

export function UserMenu() {
  const { user, signOut } = useAuth();

  if (!user) return null;

  const initials = user.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || user.email[0].toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={cn(
            "relative h-10 w-10 rounded-full glass-card",
            "liquid-hover fluid-transform-fast hover:glass-hover"
          )}
        >
          <Avatar className="h-10 w-10">
            <AvatarImage src={user.picture} alt={user.name || user.email} />
            <AvatarFallback className="bg-white/10 text-white">
              {initials}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-56 glass-card border-white/10"
        align="end"
        forceMount
      >
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none text-white">
              {user.name || "User"}
            </p>
            <p className="text-xs leading-none text-white/60">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-white/10" />
        <DropdownMenuItem
          className="text-white/80 hover:text-white hover:bg-white/10 cursor-pointer"
          onClick={signOut}
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-black to-slate-900">
        <div className="glass-card rounded-2xl p-8">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/30 border-t-white mx-auto mb-4"></div>
            <p className="text-sm font-light text-white/70">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-black to-slate-900 relative overflow-hidden">
        {/* Atmospheric Background - matching VideoUpload style */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl float-gentle"></div>
          <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-purple-500/8 rounded-full blur-3xl" style={{animationDelay: '2s'}}></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-emerald-500/6 rounded-full blur-3xl" style={{animationDelay: '4s'}}></div>
        </div>
        
        <div className="relative z-10 w-full max-w-7xl mx-auto px-4 py-12">
          <div className="grid lg:grid-cols-2 gap-16 items-center min-h-[600px]">
            {/* Left side - Logo */}
            <div className="flex items-center justify-center">
              <div className="relative w-full max-w-lg aspect-square">
                {/* Subtle ambient glow */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="absolute w-full h-full bg-blue-500/6 rounded-full blur-3xl animate-pulse"></div>
                  <div className="absolute w-4/5 h-4/5 bg-purple-500/5 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '1s', animationDuration: '3s' }}></div>
                </div>
                
                {/* Logo centered */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative z-10 flex flex-col items-center space-y-4">
                    <div className="relative">
                      <div className="absolute inset-0 bg-blue-500/8 rounded-full blur-2xl"></div>
                      <img 
                        src="/cosmicbrain.png" 
                        alt="Cosmic Brain Logo" 
                        className="relative w-80 h-auto object-contain drop-shadow-2xl"
                      />
                    </div>
                    <h1 className="text-4xl font-bold text-white tracking-wider rounded-lg px-4 py-2">CosmicBrain</h1>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Right side - Sign in card */}
            <div className="flex items-center justify-center">
              <div className="w-full max-w-md">
                <div className="glass-ultra rounded-3xl p-10 space-y-8 backdrop-blur-2xl border border-white/10 shadow-2xl">
                  <div className="text-center space-y-3">
                    <div className="inline-flex items-center justify-center w-16 h-16 mx-auto mb-4 glass-card rounded-2xl">
                      <svg className="w-8 h-8 text-white/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    
                    <h3 className="text-3xl font-light text-white">
                      Welcome Back
                    </h3>
                    <p className="text-white/60 text-sm font-light leading-relaxed">
                  Sign in with your Google account to continue
                </p>
              </div>
              
                  <div className="space-y-4">
                <div className="flex justify-center">
                <SignInButton />
              </div>
              
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-white/10"></div>
                      </div>
                      <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-transparent px-2 text-white/40 font-light">Secure Authentication</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="pt-4 space-y-4">
                    <div className="flex items-start space-x-3 text-xs text-white/50">
                      <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="font-light">Your data is encrypted and secure</span>
                    </div>
                    
                    <div className="flex items-start space-x-3 text-xs text-white/50">
                      <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="font-light">We'll never share your information</span>
                    </div>
                  </div>
                  
                  <p className="text-xs text-white/30 text-center font-light pt-2">
                    By signing in, you agree to our terms of service and privacy policy
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

