import GlassCard from '../GlassCard';

export default function GlassCardExample() {
  return (
    <div className="p-8 bg-black min-h-screen">
      <div className="space-y-6">
        <GlassCard className="p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Glass Card Example</h3>
          <p className="text-white/80">This is a glassmorphism card with blur and transparency effects.</p>
        </GlassCard>
        
        <GlassCard blur="xl" opacity="high" className="p-6">
          <h3 className="text-xl font-semibold text-white mb-2">High Opacity Card</h3>
          <p className="text-white/80">This card has higher opacity and stronger blur effects.</p>
        </GlassCard>
      </div>
    </div>
  );
}