import { useState, useEffect } from 'react';
import { Search, Filter, SlidersHorizontal } from 'lucide-react';
import api from '../../services/api';
import VideoCard from '../components/VideoCard'; // <--- IMPORTANTE

export default function Home() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    level: '',
    topic: '',
    channel: ''
  });

  useEffect(() => {
    const timeoutId = setTimeout(() => fetchVideos(), 500);
    return () => clearTimeout(timeoutId);
  }, [filters]);

  const fetchVideos = async () => {
    setLoading(true);
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''));
      const res = await api.get('/videos/', { params });
      setVideos(res.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => setFilters({ ...filters, [e.target.name]: e.target.value });

  return (
    <div className="min-h-screen">
      {/* --- HERO SECTION --- */}
      <div className="bg-indigo-900 py-16 px-4 relative overflow-hidden">
        {/* Decoración de fondo */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden opacity-20">
             <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-purple-500 blur-3xl mix-blend-multiply"></div>
             <div className="absolute top-1/2 right-0 w-80 h-80 rounded-full bg-indigo-400 blur-3xl mix-blend-multiply"></div>
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-6 tracking-tight">
            Domina el inglés con <span className="text-indigo-200">contenido real</span>
          </h1>
          <p className="text-indigo-100 text-lg mb-8 max-w-2xl mx-auto">
            Aprende con videos de YouTube analizados por IA, clasificados por nivel CEFR y vocabulario específico.
          </p>

          {/* BARRA DE BÚSQUEDA FLOTANTE */}
          <div className="bg-white p-2 rounded-2xl shadow-xl flex flex-col md:flex-row gap-2 max-w-3xl mx-auto">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-3.5 text-slate-400" size={20} />
              <input
                type="text"
                name="search"
                placeholder="Busca temas, títulos..."
                className="w-full pl-12 pr-4 py-3 rounded-xl bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all placeholder:text-slate-400 text-slate-700"
                onChange={handleFilterChange}
              />
            </div>
            
            <div className="flex gap-2">
              <div className="relative">
                 <select 
                    name="level" 
                    onChange={handleFilterChange} 
                    className="appearance-none h-full pl-4 pr-10 py-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-indigo-500 text-slate-700 font-medium cursor-pointer hover:bg-slate-100 transition-colors"
                 >
                  <option value="">Nivel</option>
                  <option value="A1">A1</option>
                  <option value="A2">A2</option>
                  <option value="B1">B1</option>
                  <option value="B2">B2</option>
                  <option value="C1">C1</option>
                  <option value="C2">C2</option>
                </select>
                <Filter className="absolute right-3 top-3.5 text-slate-400 pointer-events-none" size={16} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* --- CONTENT GRID --- */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <SlidersHorizontal size={24} className="text-indigo-600" />
            Videos Recientes
          </h2>
          <span className="text-sm text-slate-500 bg-white px-3 py-1 rounded-full border shadow-sm">
            {videos.length} resultados
          </span>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
            {[1,2,3].map(i => (
              <div key={i} className="bg-white rounded-2xl h-80"></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            {videos.map((video) => (
              <VideoCard key={video.video_id} video={video} />
            ))}
          </div>
        )}

        {!loading && videos.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-bold text-slate-700">No encontramos videos</h3>
            <p className="text-slate-500">Intenta cambiar los filtros de búsqueda.</p>
          </div>
        )}
      </div>
    </div>
  );
}