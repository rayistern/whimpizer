import React from 'react';
import { BookOpen, Home, List, Info } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  currentPage?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, currentPage = 'home' }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-yellow-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-4 border-wimpy-blue">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="relative">
                <BookOpen className="h-10 w-10 text-wimpy-blue" />
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-wimpy-yellow rounded-full animate-bounce"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 comic-style">
                  Whimpizer
                </h1>
                <p className="text-sm text-gray-600 -mt-1">
                  Transform stories into Wimpy Kid magic! ✨
                </p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex space-x-8">
              <NavLink 
                href="/" 
                icon={<Home className="h-5 w-5" />} 
                text="Create" 
                active={currentPage === 'home'} 
              />
              <NavLink 
                href="/jobs" 
                icon={<List className="h-5 w-5" />} 
                text="My Jobs" 
                active={currentPage === 'jobs'} 
              />
              <NavLink 
                href="/about" 
                icon={<Info className="h-5 w-5" />} 
                text="About" 
                active={currentPage === 'about'} 
              />
            </nav>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button className="btn-secondary text-sm px-4 py-2">
                Menu
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center">
            <p className="text-gray-600 text-sm">
              🎨 Transform your web content into amazing Wimpy Kid stories
            </p>
            <p className="text-gray-500 text-xs mt-2">
              Made with ❤️ for young storytellers everywhere
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

interface NavLinkProps {
  href: string;
  icon: React.ReactNode;
  text: string;
  active?: boolean;
}

const NavLink: React.FC<NavLinkProps> = ({ href, icon, text, active }) => {
  return (
    <a
      href={href}
      className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors duration-200 ${
        active
          ? 'bg-wimpy-blue text-white shadow-md'
          : 'text-gray-700 hover:bg-gray-100 hover:text-wimpy-blue'
      }`}
    >
      {icon}
      <span className="font-medium">{text}</span>
    </a>
  );
};

export default Layout;