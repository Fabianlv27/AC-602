import { Link } from 'react-router-dom';
import { Sparkles, ShieldCheck } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo con gradiente */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="bg-gradient-to-tr from-indigo-600 to-violet-600 text-white p-2 rounded-lg shadow-md group-hover:shadow-indigo-200 transition-all">
              <Sparkles size={20} />
            </div>
            <span className="font-bold text-xl tracking-tight text-slate-800">
              AC602<span className="text-indigo-600">Learning</span>
            </span>
          </Link>
          
          <div className="flex gap-4">
            <Link 
              to="/admin" 
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all"
            >
              <ShieldCheck size={18} /> 
              Admin
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}