import { cn } from "@/lib/utils";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  blur?: "sm" | "md" | "lg" | "xl";
  opacity?: "low" | "medium" | "high";
}

export default function GlassCard({ 
  children, 
  className, 
  blur = "lg", 
  opacity = "medium" 
}: GlassCardProps) {
  const blurClasses = {
    sm: "backdrop-blur-sm",
    md: "backdrop-blur-md", 
    lg: "backdrop-blur-lg",
    xl: "backdrop-blur-xl"
  };

  const opacityClasses = {
    low: "bg-white/5 border-white/10",
    medium: "bg-white/10 border-white/20", 
    high: "bg-white/20 border-white/30"
  };

  return (
    <div 
      className={cn(
        "rounded-lg border",
        blurClasses[blur],
        opacityClasses[opacity],
        "shadow-xl shadow-black/20",
        className
      )}
      data-testid="glass-card"
    >
      {children}
    </div>
  );
}