import { useState, useEffect } from 'react';
import { Search, Filter, SlidersHorizontal, X, Globe } from 'lucide-react'; // Importa Globe
import api from '../services/api';
import VideoCard from '../components/VideoCard';

export default function Home() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  // Estado para opciones
  const [filterOptions, setFilterOptions] = useState({
    levels: [],
    types: [],
    topics: [],
    languages: {} // Objeto del accents.json
  });

  const [filters, setFilters] = useState({
    search: '',
    topic: '',
    level: '',
    source: '',
    accent: '',
    speed: '',
    type: '',
    language: '' // Nuevo estado
  });

  // 1. Cargar Opciones
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const res = await api.get('/videos/filters');
        setFilterOptions(res.data);
      } catch (error) {
        console.error("Error cargando filtros:", error);
      }
    };
    fetchOptions();
  }, []);

  // 2. Cargar Videos
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

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    
    // Si cambia el idioma, reseteamos el acento para evitar inconsistencias
    if (name === 'language') {
      setFilters({ ...filters, language: value, accent: '' });
    } else {
      setFilters({ ...filters, [name]: value });
    }
  };

  const clearFilters = () => setFilters({
    search: '', topic: '', level: '', source: '', accent: '', speed: '', type: '', language: ''
  });

  // Helper para obtener acentos según idioma seleccionado
  const availableAccents = filters.language && filterOptions.languages[filters.language]
    ? filterOptions.languages[filters.language].accents
    : [];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      
      {/* SIDEBAR */}
      <aside className={`fixed inset-y-0 left-0 z-40 w-72 bg-white border-r border-slate-200 transform transition-transform duration-300 md:translate-x-0 md:static overflow-y-auto ${showMobileFilters ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Filter size={20} className="text-indigo-600" /> Filtros
            </h2>
            <button onClick={clearFilters} className="text-xs text-slate-500 hover:text-indigo-600 underline">Limpiar</button>
            <button onClick={() => setShowMobileFilters(false)} className="md:hidden"><X size={24} /></button>
          </div>

          <div className="space-y-6">
            
            {/* BUSCADOR */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Búsqueda</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                <input type="text" name="search" value={filters.search} onChange={handleFilterChange} placeholder="Título..." className="w-full pl-9 pr-3 py-2 bg-slate-50 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
              </div>
            </div>

            {/* --- NUEVO: FILTRO DE IDIOMA --- */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Idioma</label>
              <div className="relative">
                <Globe className="absolute left-3 top-2.5 text-slate-400" size={16} />
                <select name="language" value={filters.language} onChange={handleFilterChange} className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none">
                  <option value="">Todos los idiomas</option>
                  {Object.entries(filterOptions.languages || {}).map(([code, data]) => (
                    <option key={code} value={code}>{data.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* --- FILTRO DE ACENTOS (DEPENDIENTE) --- */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Acento</label>
              <select 
                name="accent" 
                value={filters.accent} 
                onChange={handleFilterChange} 
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none disabled:bg-slate-100 disabled:text-slate-400"
                disabled={!filters.language} // Deshabilitado si no hay idioma
              >
                <option value="">
                  {!filters.language ? "Selecciona un idioma primero" : "Cualquier acento"}
                </option>
                {availableAccents.map((acc, index) => (
                  <option key={index} value={acc}>{acc}</option>
                ))}
              </select>
            </div>

            {/* RESTO DE FILTROS (Tags, Nivel, Tipo, Velocidad, Subtítulos) */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Tema / Tag</label>
              <select name="topic" value={filters.topic} onChange={handleFilterChange} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none">
                <option value="">Cualquier tema</option>
                {filterOptions.topics.map((t, i) => <option key={i} value={t}>{t}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Nivel</label>
              <select name="level" value={filters.level} onChange={handleFilterChange} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none">
                <option value="">Todos los niveles</option>
                {filterOptions.levels.map((l, i) => <option key={i} value={l}>{l}</option>)}
              </select>
            </div>

             <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Tipo de Vocabulario</label>
              <select name="type" value={filters.type} onChange={handleFilterChange} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none">
                <option value="">Cualquiera</option>
                {filterOptions.types.map((t, i) => <option key={i} value={t}>{t}</option>)}
              </select>
            </div>
            
            {/* Velocidad y Subtítulos (Igual que antes) */}
             <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Velocidad</label>
              <div className="grid grid-cols-3 gap-2">
                {['slow', 'normal', 'fast'].map((s) => (
                  <button key={s} onClick={() => setFilters({...filters, speed: filters.speed === s ? '' : s})} className={`text-xs py-2 rounded-lg border transition-colors ${filters.speed === s ? 'bg-indigo-100 border-indigo-200 text-indigo-700 font-bold' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
                    {s === 'slow' ? 'Lento' : s === 'normal' ? 'Normal' : 'Rápido'}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Subtítulos</label>
              <select name="source" value={filters.source} onChange={handleFilterChange} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none">
                <option value="">Cualquiera</option>
                <option value="manual">Manuales</option>
                <option value="generated">Generados</option>
                <option value="none">Sin subtítulos</option>
              </select>
            </div>

          </div>
        </div>
      </aside>

      {/* MAIN CONTENT (Igual) */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto h-screen">
          {/* ... (Todo igual que antes) ... */}
           <div className="md:hidden flex justify-between items-center mb-6">
            <h1 className="font-bold text-xl text-slate-800">Videos</h1>
            <button onClick={() => setShowMobileFilters(true)} className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm border text-sm font-medium">
              <SlidersHorizontal size={16} /> Filtros
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {loading 
              ? [1,2,3].map(i => <div key={i} className="bg-slate-200 h-60 rounded-2xl animate-pulse"/>)
              : videos.map(video => <VideoCard key={video.video_id} video={video} />)
            }
            {!loading && videos.length === 0 && <div className="col-span-full text-center text-slate-500 mt-10">No hay videos con estos filtros.</div>}
          </div>
      </main>
    </div>
  );
}