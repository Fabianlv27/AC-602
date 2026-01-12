import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Brain, FileText, Activity } from 'lucide-react';
import api from '../../services/api';

export default function VideoDetail() {
  const { id } = useParams();
  const [video, setVideo] = useState(null);

  useEffect(() => {
    api.get(`/videos/${id}`).then(res => setVideo(res.data)).catch(console.error);
  }, [id]);

  if (!video) return <div className="min-h-screen flex items-center justify-center"><div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <Link to="/" className="inline-flex items-center text-sm text-slate-500 hover:text-indigo-600 mb-6 transition-colors">
        <ArrowLeft size={16} className="mr-1" /> Volver al buscador
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* --- COLUMNA IZQUIERDA (VIDEO & TRANSCRIPT) --- */}
        <div className="lg:col-span-2 space-y-8">
          {/* Player Wrapper */}
          <div className="bg-black rounded-3xl overflow-hidden shadow-2xl aspect-video relative ring-4 ring-indigo-50">
            <iframe
              className="w-full h-full"
              src={`https://www.youtube.com/embed/${video.video_id}?rel=0&modestbranding=1`}
              title={video.title}
              allowFullScreen
            ></iframe>
          </div>

          {/* Sección de Transcripción / Resumen */}
          <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
            <div className="flex items-center gap-2 mb-6 border-b pb-4">
              <FileText className="text-indigo-600" />
              <h2 className="text-xl font-bold text-slate-800">Resumen y Transcripción</h2>
            </div>
            <div className="prose prose-indigo max-w-none text-slate-600 leading-relaxed">
              <p className="bg-slate-50 p-4 rounded-xl border border-slate-100 italic text-slate-500 mb-6">
                {video.ai_analysis?.summary || "El resumen no está disponible para este video."}
              </p>
              <div className="whitespace-pre-wrap font-sans text-base">
                {/* Aquí podrías poner el texto completo si lo tuvieras */}
                {video.ai_analysis?.transcript_summary || "Transcripción detallada no disponible."}
              </div>
            </div>
          </div>
        </div>

        {/* --- COLUMNA DERECHA (METADATA & AI) --- */}
        <div className="space-y-6">
          
          {/* Tarjeta Principal de Info */}
          <div className="bg-white rounded-3xl p-6 shadow-lg border border-indigo-50 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full -mr-16 -mt-16 opacity-50"></div>
            
            <h1 className="text-xl font-bold text-slate-900 mb-2 relative z-10">{video.title}</h1>
            <p className="text-indigo-600 font-medium mb-6 relative z-10">{video.channel_name}</p>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 text-center">
                <div className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">Nivel</div>
                <div className="text-2xl font-black text-slate-800">{video.level || "-"}</div>
              </div>
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 text-center">
                <div className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">WPM</div>
                <div className="text-2xl font-black text-slate-800">{video.wpm}</div>
              </div>
            </div>
          </div>

          {/* Tarjeta de IA Analysis */}
          <div className="bg-gradient-to-br from-indigo-600 to-violet-700 rounded-3xl p-6 text-white shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="text-indigo-200" />
              <h3 className="font-bold text-lg">Análisis de IA</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <span className="text-indigo-200 text-xs font-bold uppercase block mb-2">Tópicos Detectados</span>
                <div className="flex flex-wrap gap-2">
                  {video.topics?.map(t => (
                    <span key={t} className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-sm hover:bg-white/30 transition cursor-default">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-indigo-200 text-xs font-bold uppercase block mb-2">Acentos</span>
                <div className="flex flex-wrap gap-2">
                  {video.accents?.map(a => (
                    <span key={a} className="flex items-center gap-1 text-sm text-indigo-100">
                      <Activity size={14} /> {a}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}