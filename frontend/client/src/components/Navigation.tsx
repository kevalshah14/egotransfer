import { useState } from 'react';
import { Upload, Eye, Settings, Menu, X } from 'lucide-react'; // Cpu icon removed (robot control hidden)
import { cn } from '@/lib/utils';
import { UserMenu } from './Auth';

interface NavigationProps {
  currentPage: 'upload' | 'analysis' | 'robot' | 'settings';
  onPageChange: (page: 'upload' | 'analysis' | 'robot' | 'settings') => void;
  isProcessing?: boolean;
}

export default function Navigation({ currentPage, onPageChange, isProcessing = false }: NavigationProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'upload' as const, label: 'Upload Video', icon: Upload },
    { id: 'analysis' as const, label: 'Analysis', icon: Eye },
    // { id: 'robot' as const, label: 'Robot Control', icon: Cpu }, // Hidden for now
    { id: 'settings' as const, label: 'Settings', icon: Settings },
  ];

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <>
      {/* Floating Navigation */}
      <div className="hidden md:block fixed top-6 left-1/2 transform -translate-x-1/2 z-50">
        <div className="glass-ultra rounded-2xl p-3">
          <nav className="flex items-center space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              const isDisabled = isProcessing && item.id !== 'settings';
              return (
                <button
                  key={item.id}
                  onClick={() => !isDisabled && onPageChange(item.id)}
                  disabled={isDisabled}
                  className={cn(
                    "flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-300",
                    "liquid-hover fluid-transform-fast hover:glass-hover",
                    isActive 
                      ? "glass-card text-white shadow-lg" 
                      : isDisabled
                      ? "text-white/30 cursor-not-allowed"
                      : "text-white/70 hover:text-white"
                  )}
                  data-testid={`nav-${item.id}`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden lg:inline text-sm font-light tracking-wide">{item.label}</span>
                </button>
              );
            })}
            <div className="ml-2">
              <UserMenu />
            </div>
          </nav>
        </div>
      </div>

      {/* Mobile Menu Trigger */}
      <div className="md:hidden fixed top-6 right-6 z-50">
        <button
          onClick={toggleMobileMenu}
          className={cn(
            "w-12 h-12 rounded-xl glass-ultra flex items-center justify-center",
            "liquid-hover fluid-transform-fast hover:glass-hover"
          )}
          data-testid="button-mobile-menu"
        >
          {isMobileMenuOpen ? 
            <X className="h-5 w-5 text-white" /> : 
            <Menu className="h-5 w-5 text-white/70" />
          }
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsMobileMenuOpen(false)}
          ></div>
          
          {/* Menu */}
          <div className="absolute top-20 right-6 left-6">
            <div className="glass-ultra rounded-2xl p-4 space-y-3">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                const isDisabled = isProcessing && item.id !== 'settings';
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      if (!isDisabled) {
                        onPageChange(item.id);
                        setIsMobileMenuOpen(false);
                      }
                    }}
                    disabled={isDisabled}
                    className={cn(
                      "w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300",
                      "liquid-hover fluid-transform-fast hover:glass-hover",
                      isActive 
                        ? "glass-card text-white" 
                        : isDisabled
                        ? "text-white/30 cursor-not-allowed"
                        : "text-white/70 hover:text-white"
                    )}
                    data-testid={`mobile-nav-${item.id}`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-light tracking-wide">{item.label}</span>
                  </button>
                );
              })}
              <div className="pt-2 border-t border-white/10">
                <UserMenu />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}