import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Play, Filter, X } from 'lucide-react'; // Eliminado Clock
import api from '../../services/api'; // Ruta corregida

export default function Home() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [filters, setFilters] = useState({
    search: '',
    language: '',
    accent: '',
    level: '',
    topic: '',
    type: ''
  });

  const [options, setOptions] = useState({
    levels: [],
    topics: [],
    content_types: [],
    accents_data: {}
  });

  useEffect(() => {
    api.get('/videos/filters')
      .then(res => {
        if (res.data) setOptions(res.data);
      })
      .catch(err => console.error("Error cargando filtros:", err));
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [filters]);

  const fetchVideos = async () => {
    setLoading(true);
    const params = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== '')
    );
    
    if (params.type) {
        params.content_types = params.type;
        delete params.type;
    }
    if (params.search) {
        params.title = params.search;
        delete params.search;
    }

    try {
      const res = await api.get('/videos/', { params });
      setVideos(res.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => {
      const newFilters = { ...prev, [name]: value };
      if (name === 'language') {
        newFilters.accent = '';
      }
      return newFilters;
    });
  };

  const selectedLangData = filters.language ? options.accents_data[filters.language] : null;
  const availableAccents = selectedLangData ? selectedLangData.accents : [];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 min-h-screen">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Library</h1>
          <p className="text-slate-500 mt-1">Explora lecciones mejoradas con IA</p>
        </div>

        {/* BUSCADOR */}
        <div className="relative w-full md:w-96">
          <input 
            type="text"
            name="search"
            value={filters.search}
            onChange={handleFilterChange}
            placeholder="Buscar por título..."
            className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm"
          />
          <Search className="absolute left-3 top-3.5 text-slate-400" size={20} />
          {filters.search && (
            <button onClick={() => setFilters({...filters, search: ''})} className="absolute right-3 top-3.5 text-slate-300 hover:text-slate-500">
              <X size={18}/>
            </button>
          )}
        </div>
      </div>

      {/* BARRA DE FILTROS */}
      <div className="bg-white p-4 rounded-3xl shadow-sm border border-slate-200 mb-10 flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 text-slate-400 mr-2">
            <Filter size={18} /> <span className="text-xs font-bold uppercase">Filtros</span>
        </div>

        <select 
            name="language" 
            value={filters.language} 
            onChange={handleFilterChange}
            className="bg-slate-50 border-transparent rounded-xl text-sm font-medium text-slate-700 py-2 px-3 focus:ring-indigo-500 cursor-pointer"
        >
            <option value="">Todos los idiomas</option>
            {Object.entries(options.accents_data).map(([code, data]) => (
                <option key={code} value={code}>{data.label}</option>
            ))}
        </select>

        <select 
            name="accent" 
            value={filters.accent} 
            onChange={handleFilterChange}
            disabled={!filters.language}
            className="bg-slate-50 border-transparent rounded-xl text-sm font-medium text-slate-700 py-2 px-3 focus:ring-indigo-500 cursor-pointer disabled:opacity-50"
        >
            <option value="">Cualquier acento</option>
            {availableAccents.map(acc => (
                <option key={acc} value={acc}>{acc}</option>
            ))}
        </select>

        <select name="level" value={filters.level} onChange={handleFilterChange} className="bg-slate-50 border-transparent rounded-xl text-sm font-medium text-slate-700 py-2 px-3 cursor-pointer">
            <option value="">Nivel</option>
            {options.levels.map(l => <option key={l} value={l}>{l}</option>)}
        </select>

        <select name="topic" value={filters.topic} onChange={handleFilterChange} className="bg-slate-50 border-transparent rounded-xl text-sm font-medium text-slate-700 py-2 px-3 cursor-pointer max-w-[150px]">
            <option value="">Tema</option>
            {options.topics.map(t => <option key={t} value={t}>{t}</option>)}
        </select>

         <select name="type" value={filters.type} onChange={handleFilterChange} className="bg-slate-50 border-transparent rounded-xl text-sm font-medium text-slate-700 py-2 px-3 cursor-pointer">
            <option value="">Tipo</option>
            {options.content_types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>

        {(filters.language || filters.level || filters.topic || filters.type || filters.search) && (
             <button 
                onClick={() => setFilters({ search: '', language: '', accent: '', level: '', topic: '', type: '' })}
                className="ml-auto text-xs font-bold text-rose-500 hover:bg-rose-50 px-3 py-2 rounded-xl"
             >
                Limpiar
             </button>
        )}
      </div>

      {/* GRID VIDEOS */}
      {loading ? (
         <div className="text-center py-20 text-slate-400">Cargando...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.map((video) => (
            <Link key={video.video_id} to={`/video/${video.video_id}`} className="group bg-white rounded-3xl border border-slate-100 overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="aspect-video relative overflow-hidden bg-slate-100">
                    <img 
                        src={`https://img.youtube.com/vi/${video.video_id}/maxresdefault.jpg`} 
                        alt={video.title} 
                        className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
                        onError={(e) => { e.target.src = `https://img.youtube.com/vi/${video.video_id}/hqdefault.jpg`; }} 
                    />
                    <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <div className="bg-white/90 p-3 rounded-full shadow-lg backdrop-blur-sm">
                        <Play className="text-indigo-600 fill-current ml-1" size={24} />
                        </div>
                    </div>

                    {/* OVERLAYS: Nivel y Etiquetas en la miniatura */}
                    
                    {/* Nivel (Arriba Izquierda) */}
                    <div className="absolute top-3 left-3">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border shadow-sm ${
                            video.level?.startsWith('A') ? 'bg-green-100 text-green-700 border-green-200' :
                            video.level?.startsWith('B') ? 'bg-amber-100 text-amber-700 border-amber-200' :
                            video.level?.startsWith('C') ? 'bg-rose-100 text-rose-700 border-rose-200' :
                            'bg-slate-100 text-slate-600 border-slate-200'
                        }`}>
                            {video.level || '?'}
                        </span>
                    </div>

                    {/* Etiquetas/Temas (Abajo Izquierda) */}
                    <div className="absolute bottom-3 left-3 flex flex-wrap gap-1">
                        {video.topics?.slice(0, 2).map(t => (
                            <span key={t} className="text-[10px] bg-black/60 backdrop-blur-md text-white px-2 py-1 rounded-md border border-white/10 font-medium">
                                {t}
                            </span>
                        ))}
                    </div>
                </div>

                <div className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs text-slate-400 font-medium truncate flex-1 text-left">{video.channel_name}</span>
                    </div>
                    <h3 className="font-bold text-slate-800 leading-snug mb-3 line-clamp-2 h-[2.8em]">{video.title}</h3>
                    
                    {/* Acentos (Se mantienen aquí si existen, para no perder información) */}
                    <div className="flex flex-wrap gap-1.5 mt-4 h-6 overflow-hidden">
                         {video.accents?.slice(0, 1).map(a => (
                            <span key={a} className="text-[10px] bg-indigo-50 text-indigo-600 px-2 py-1 rounded-md border border-indigo-100 font-medium">
                              {a}
                            </span>
                         ))}
                    </div>
                </div>
            </Link>
            ))}
        </div>
      )}
    </div>
  );
}