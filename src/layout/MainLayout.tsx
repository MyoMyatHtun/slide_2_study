import { BookOpen, Github } from 'lucide-react';
import { Outlet, Link } from 'react-router-dom';

export function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo Section */}
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="p-2 bg-brand-blue-900 rounded-lg shadow-sm">
              <BookOpen className="h-6 w-6 text-brand-yellow-400" />
            </div>
            <span className="text-xl font-bold text-brand-blue-900 tracking-tight">Slide2Study</span>
          </Link>

          {/* Navigation */}
          <nav className="flex gap-6 text-sm font-medium text-gray-600 items-center">
            <Link to="/" className="hover:text-brand-blue-600 transition-colors">Home</Link>
            <a href="#" className="hover:text-brand-blue-600 transition-colors">About</a>
            <div className="w-px h-4 bg-gray-300 mx-2"></div>
            <a href="#" className="text-gray-400 hover:text-gray-600">
              <Github className="w-5 h-5" />
            </a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow">
        <Outlet /> 
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-8 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-500 text-sm">
          <p>© 2026 Slide2Study. MIIT Special Project P-11.</p>
          <p className="mt-2 text-xs text-gray-400">Kaung Khant Lynn • Myo Myat Htun • Wai Yan Win Kyaw</p>
        </div>
      </footer>
    </div>
  );
}