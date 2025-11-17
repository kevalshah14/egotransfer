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
import { LogOut, User, Shield, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export function SignInButton() {
  const { signInWithGoogle, loading } = useAuth();

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
    >
      <Button
        onClick={signInWithGoogle}
        disabled={loading}
        className={cn(
          "w-full px-6 py-6 text-base font-medium",
          "glass-card text-white hover:glass-hover",
          "liquid-hover fluid-transform-fast",
          "border border-white/20",
          "shadow-lg shadow-blue-500/10",
          "hover:shadow-xl hover:shadow-blue-500/20",
          "transition-all duration-300",
          loading && "opacity-70 cursor-not-allowed"
        )}
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white/30 border-t-white mr-3"></div>
            <span>Signing in...</span>
          </div>
        ) : (
          <div className="flex items-center justify-center">
            <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
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
            <span>Sign in with Google</span>
          </div>
        )}
      </Button>
    </motion.div>
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
        {/* Background effects to match main app */}
        <div className="absolute inset-0 opacity-30">
          <motion.div 
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"
            animate={{
              scale: [1, 1.1, 1],
              x: [0, 30, 0],
              y: [0, -30, 0],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </div>
        <div className="glass-card rounded-2xl p-8 relative z-10">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white/30 border-t-white mx-auto mb-4"></div>
            <p className="text-sm font-light text-white/70">Signing you in...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-black to-slate-900 relative overflow-hidden">
        {/* Enhanced Atmospheric Background */}
        <div className="absolute inset-0 opacity-30">
          <motion.div 
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"
            animate={{
              scale: [1, 1.1, 1],
              x: [0, 30, 0],
              y: [0, -30, 0],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          <motion.div 
            className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-purple-500/8 rounded-full blur-3xl"
            animate={{
              scale: [1, 1.15, 1],
              x: [0, -20, 0],
              y: [0, 20, 0],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 2
            }}
          />
          <motion.div 
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-emerald-500/6 rounded-full blur-3xl"
            animate={{
              scale: [1, 1.2, 1],
              rotate: [0, 180, 360],
            }}
            transition={{
              duration: 12,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 4
            }}
          />
        </div>
        
        <div className="relative z-10 w-full max-w-7xl mx-auto px-4 py-12">
          <div className="grid lg:grid-cols-2 gap-16 items-center min-h-[600px]">
            {/* Left side - Logo with animation */}
            <motion.div 
              className="flex items-center justify-center"
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="relative w-full max-w-lg aspect-square">
                {/* Enhanced ambient glow */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div 
                    className="absolute w-full h-full bg-blue-500/6 rounded-full blur-3xl"
                    animate={{ opacity: [0.4, 0.6, 0.4] }}
                    transition={{ duration: 4, repeat: Infinity }}
                  />
                  <motion.div 
                    className="absolute w-4/5 h-4/5 bg-purple-500/5 rounded-full blur-2xl"
                    animate={{ opacity: [0.3, 0.5, 0.3] }}
                    transition={{ duration: 5, repeat: Infinity, delay: 1 }}
                  />
                </div>
                
                {/* Logo centered */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div 
                    className="relative z-10 flex flex-col items-center space-y-6"
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                  >
                    <motion.div 
                      className="relative logo-shine-container"
                      whileHover={{ scale: 1.05 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="absolute inset-0 bg-blue-500/8 rounded-full blur-2xl"></div>
                      {/* Moving shine effect following logo outline */}
                      <div className="logo-shine-wrapper">
                        <div className="logo-outline-border">
                          <div className="logo-shine-border"></div>
                        </div>
                      </div>
                      <img 
                        src="/cosmicbrain.png" 
                        alt="Cosmic Brain Logo" 
                        className="relative w-80 h-auto object-contain drop-shadow-2xl z-10 logo-image"
                      />
                    </motion.div>
                    <motion.h1 
                      className="text-5xl font-bold text-white tracking-wider"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.6, delay: 0.4 }}
                    >
                      CosmicBrain
                    </motion.h1>
                    <motion.p 
                      className="text-white/50 text-sm font-light tracking-wide"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.6, delay: 0.6 }}
                    >
                      AI-Powered Video Analysis
                    </motion.p>
                  </motion.div>
                </div>
              </div>
            </motion.div>
            
            {/* Right side - Enhanced Sign in card */}
            <motion.div 
              className="flex items-center justify-center"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
            >
              <div className="w-full max-w-md">
                <motion.div 
                  className="glass-ultra rounded-3xl p-10 space-y-8 backdrop-blur-2xl border border-white/10 shadow-2xl"
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.5, delay: 0.3 }}
                  whileHover={{ scale: 1.01 }}
                >
                  <motion.div 
                    className="text-center space-y-4"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                  >
                    <motion.div 
                      className="inline-flex items-center justify-center w-20 h-20 mx-auto mb-2 glass-card rounded-2xl border border-white/10"
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ duration: 0.6, delay: 0.5, type: "spring" }}
                      whileHover={{ rotate: 360, scale: 1.1 }}
                    >
                      <Shield className="w-10 h-10 text-white/90" />
                    </motion.div>
                    
                    <h3 className="text-3xl font-light text-white tracking-tight">
                      Welcome Back
                    </h3>
                    <p className="text-white/60 text-sm font-light leading-relaxed max-w-sm mx-auto">
                      Sign in with your Google account to access your video analysis dashboard
                    </p>
                  </motion.div>
                  
                  <motion.div 
                    className="space-y-5"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.6 }}
                  >
                    <SignInButton />
                    
                    <div className="relative py-2">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-white/10"></div>
                      </div>
                      <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-transparent px-3 text-white/40 font-light tracking-wider">Secure Authentication</span>
                      </div>
                    </div>
                  </motion.div>
                  
                  <motion.div 
                    className="pt-2 space-y-3"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: 0.7 }}
                  >
                    <div className="flex items-start space-x-3 text-xs text-white/50 group">
                      <motion.div
                        whileHover={{ scale: 1.2, rotate: 360 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Lock className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-400/80 group-hover:text-green-400 transition-colors" />
                      </motion.div>
                      <span className="font-light leading-relaxed">Your data is encrypted and secure with industry-standard protocols</span>
                    </div>
                    
                    <div className="flex items-start space-x-3 text-xs text-white/50 group">
                      <motion.div
                        whileHover={{ scale: 1.2, rotate: 360 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Shield className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-400/80 group-hover:text-green-400 transition-colors" />
                      </motion.div>
                      <span className="font-light leading-relaxed">We'll never share your information with third parties</span>
                    </div>
                  </motion.div>
                  
                  <motion.p 
                    className="text-xs text-white/30 text-center font-light pt-2 leading-relaxed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: 0.8 }}
                  >
                    By signing in, you agree to our{" "}
                    <a href="#" className="text-white/50 hover:text-white underline underline-offset-2 transition-colors">terms of service</a>
                    {" "}and{" "}
                    <a href="#" className="text-white/50 hover:text-white underline underline-offset-2 transition-colors">privacy policy</a>
                  </motion.p>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

