import { Link } from 'react-router-dom';
import { Play, Clock, BarChart } from 'lucide-react';

export default function VideoCard({ video }) {
  // Color dinámico según nivel (opcional, visual sugar)
  const getLevelColor = (level) => {
    const colors = {
      'A1': 'bg-green-100 text-green-700',
      'A2': 'bg-emerald-100 text-emerald-700',
      'B1': 'bg-blue-100 text-blue-700',
      'B2': 'bg-indigo-100 text-indigo-700',
      'C1': 'bg-purple-100 text-purple-700',
      'C2': 'bg-rose-100 text-rose-700',
    };
    return colors[level] || 'bg-slate-100 text-slate-600';
  };

  return (
    <Link to={`/video/${video.video_id}`} className="group h-full">
      <div className="bg-white rounded-2xl overflow-hidden border border-slate-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 h-full flex flex-col">
        
        {/* Thumbnail con Overlay */}
        <div className="relative aspect-video overflow-hidden">
          <img 
            src={`https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`} 
            alt={video.title} 
            className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500" 
          />
          <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors" />
          
          {/* Botón Play Flotante */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 transform scale-90 group-hover:scale-100">
            <div className="bg-white/90 backdrop-blur-sm p-4 rounded-full shadow-lg">
              <Play className="text-indigo-600 fill-indigo-600 ml-1" size={24} />
            </div>
          </div>

          {/* Badge de Nivel */}
          {video.level && (
            <span className={`absolute top-3 right-3 text-xs font-bold px-3 py-1 rounded-full shadow-sm backdrop-blur-md ${getLevelColor(video.level)}`}>
              {video.level}
            </span>
          )}
        </div>

        {/* Contenido */}
        <div className="p-5 flex-1 flex flex-col">
          <div className="flex gap-2 mb-3">
            {video.topics?.slice(0, 2).map(topic => (
              <span key={topic} className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded-md">
                {topic}
              </span>
            ))}
          </div>

          <h3 className="font-bold text-slate-900 leading-snug mb-2 line-clamp-2 group-hover:text-indigo-600 transition-colors">
            {video.title}
          </h3>

          <div className="mt-auto pt-4 flex items-center justify-between text-xs text-slate-500 border-t border-slate-50">
            <div className="flex items-center gap-1">
              <span className="font-medium text-slate-700">{video.channel_name}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1" title="Velocidad">
                <Clock size={14} /> {video.wpm} wpm
              </span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}