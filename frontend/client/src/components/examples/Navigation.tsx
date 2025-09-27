import { useState } from 'react';
import Navigation from '../Navigation';

export default function NavigationExample() {
  const [currentPage, setCurrentPage] = useState<'upload' | 'analysis' | 'robot'>('upload');

  return (
    <div className="min-h-screen bg-black p-8">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <div className="pt-24 text-center">
        <h2 className="text-2xl font-bold text-white mb-4">Navigation Example</h2>
        <p className="text-white/70">Current page: {currentPage}</p>
      </div>
    </div>
  );
}