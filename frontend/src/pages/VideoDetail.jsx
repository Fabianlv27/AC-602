import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, FileText, Globe, BookOpen, GraduationCap, AlertCircle, Sparkles, Bot, Clock, Tag 
} from 'lucide-react';
import api from '../../services/api';

export default function VideoDetail() {
  const { id } = useParams();
  const [video, setVideo] = useState(null);
  const [embedUrl, setEmbedUrl] = useState("");

  const langLabels = { 
      'en': 'Inglés', 'es': 'Español', 'fr': 'Francés', 
      'de': 'Alemán', 'it': 'Italiano', 'pt': 'Portugués' 
  };

  const extractVideoID = (input) => {
    if (!input) return null;
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = input.match(regExp);
    return (match && match[2].length === 11) ? match[2] : input;
  };

  // Helper para formato de tiempo (Duración)
  const formatDuration = (seconds) => {
    if (!seconds) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    api.get(`/videos/${id}`).then(res => {
        const vidData = res.data;
        setVideo(vidData);
        const cleanID = extractVideoID(vidData.video_id);
        if (cleanID) {
            setEmbedUrl(`https://www.youtube.com/embed/${cleanID}?autoplay=0&rel=0`);
        }
    }).catch(console.error);
  }, [id]);

  const handleSeek = (seconds) => {
    if (!video) return;
    const cleanID = extractVideoID(video.video_id);
    const time = Math.floor(seconds);
    setEmbedUrl(`https://www.youtube.com/embed/${cleanID}?start=${time}&autoplay=1&rel=0`);
  };

  if (!video) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
    </div>
  );

  const { vocabulary, grammar_stats, transcript_summary } = video.ai_analysis || {};

  return (
    <div className="max-w-[1400px] mx-auto px-4 py-6 min-h-screen font-sans">
      <Link to="/" className="inline-flex items-center text-slate-500 hover:text-indigo-600 mb-6 font-medium text-sm">
        <ArrowLeft size={16} className="mr-1" /> Volver a la librería
      </Link>

      <div className="space-y-8">
        
        {/* --- GRID SUPERIOR --- */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          <div className="lg:col-span-2 space-y-4">
            {/* PLAYER */}
            <div className="bg-black rounded-3xl overflow-hidden shadow-2xl relative w-full aspect-video">
                {embedUrl ? (
                    <iframe 
                        width="100%" height="100%" src={embedUrl} title={video.title} frameBorder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowFullScreen className="absolute top-0 left-0 w-full h-full"
                    ></iframe>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-white">
                        <AlertCircle size={40} className="text-red-500 mb-2" />
                        <p>ID inválido</p>
                    </div>
                )}
            </div>

            {/* INFO VIDEO */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 leading-tight mb-2">{video.title}</h1>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">
                            {video.channel_name ? video.channel_name[0].toUpperCase() : "C"}
                        </div>
                        <div>
                            <p className="font-bold text-slate-800 text-sm">{video.channel_name}</p>
                            <p className="text-slate-500 text-xs">YouTube Channel</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-bold uppercase flex gap-1 items-center">
                            <Globe size={12}/> {langLabels[video.language] || video.language}
                        </span>
                        <span className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-bold uppercase border border-indigo-100">
                             {video.level || "N/A"}
                        </span>
                    </div>
                </div>
            </div>
          </div>

          {/* TRANSCRIPT */}
          <div className="lg:col-span-1 bg-white rounded-3xl p-6 shadow-sm border border-slate-200 flex flex-col h-[600px]">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3 shrink-0">
              <FileText size={20} className="text-indigo-600"/>
              <h2 className="font-bold text-slate-800">Transcript</h2>
            </div>
            <div className="overflow-y-auto pr-2 custom-scrollbar flex-1 space-y-4">
              {transcript_summary && (
                <div className="bg-indigo-50/50 p-3 rounded-xl border border-indigo-100 text-slate-700 text-sm italic">
                   {transcript_summary}
                </div>
              )}
              {video.transcript_json && video.transcript_json.length > 0 ? (
                <div className="space-y-1">
                  {video.transcript_json.map((line, i) => (
                    <div key={i} onClick={() => handleSeek(line.start)}
                      className="group flex gap-3 p-2 hover:bg-slate-50 rounded-lg cursor-pointer transition border border-transparent hover:border-slate-100">
                      <span className="text-[10px] font-mono font-bold text-slate-400 mt-1 min-w-[35px]">
                        {!isNaN(line.start) ? new Date(line.start * 1000).toISOString().substr(14, 5) : "00:00"}
                      </span>
                      <p className="text-slate-600 text-sm leading-relaxed group-hover:text-slate-900">
                        {line.text}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-10 text-slate-400 italic text-sm">Transcripción no disponible.</div>
              )}
            </div>
          </div>
        </div>

        {/* DISCLAIMER IA */}
        <div className="flex items-center gap-2 text-indigo-600/80 justify-center py-2 opacity-70">
            <Sparkles size={16} />
            <span className="text-xs font-bold uppercase tracking-widest">Educational Data Generated by AI</span>
            <Sparkles size={16} />
        </div>

        {/* --- GRID INFERIOR --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* CONTEXT CARD */}
            <div className="bg-white rounded-3xl p-6 shadow-lg border border-indigo-50 h-full relative overflow-hidden">
                <div className="absolute top-0 right-0 p-3 opacity-10">
                    <Bot size={64} className="text-indigo-600"/>
                </div>
                
                <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-2">
                    <Globe className="text-indigo-600" size={20} />
                    <h3 className="font-bold text-lg text-slate-800">Context</h3>
                </div>

                <div className="space-y-4">
                     {/* Stats Row */}
                     <div className="grid grid-cols-2 gap-2">
                        <div className="bg-slate-50 p-3 rounded-xl flex flex-col justify-center">
                            <span className="text-xs text-slate-500 font-medium mb-1">Speed</span>
                            <span className="text-sm font-bold text-emerald-600">{video.wpm} WPM</span>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl flex flex-col justify-center">
                            <span className="text-xs text-slate-500 font-medium mb-1">Duration</span>
                            <span className="text-sm font-bold text-slate-700 flex items-center gap-1">
                                <Clock size={14}/> {formatDuration(video.duration_seconds)}
                            </span>
                        </div>
                     </div>
                     
                     {/* Accents */}
                     <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Detected Accents</span>
                        <div className="flex flex-wrap gap-2">
                            {video.accents?.length > 0 ? video.accents.map(a => 
                                <span key={a} className="px-2 py-1 bg-indigo-50 border border-indigo-100 text-indigo-700 rounded-md text-xs font-bold">{a}</span>
                            ) : <span className="text-xs text-slate-400">Neutral</span>}
                        </div>
                    </div>

                    {/* NUEVO: ETIQUETAS / TOPICS */}
                    {video.topics && video.topics.length > 0 && (
                        <div>
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2 flex items-center gap-1">
                                <Tag size={10}/> Tags
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                                {video.topics.slice(0, 8).map(t => (
                                    <span key={t} className="px-2 py-1 bg-slate-100 text-slate-500 border border-slate-200 rounded-md text-[10px] font-medium">
                                        {t}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* VOCABULARY */}
            <div className="bg-white rounded-3xl p-6 shadow-lg border border-indigo-50 h-full">
                <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-2">
                    <BookOpen className="text-indigo-600" size={20} />
                    <h3 className="font-bold text-lg text-slate-800">Vocabulary</h3>
                </div>
                <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                    {vocabulary?.map((item, idx) => (
                    <div key={idx} className="bg-slate-50 p-3 rounded-xl border border-slate-100 hover:border-indigo-200 transition-colors">
                        <p className="font-bold text-indigo-700 text-sm">{item.term}</p>
                        <p className="text-slate-600 text-xs mt-1 leading-relaxed">{item.definition}</p>
                    </div>
                    ))}
                </div>
            </div>

            {/* GRAMMAR */}
            <div className="bg-gradient-to-br from-indigo-600 to-violet-700 rounded-3xl p-6 text-white shadow-xl flex flex-col justify-center h-full relative overflow-hidden">
                <div className="absolute top-0 right-0 p-3 opacity-10">
                    <GraduationCap size={80} className="text-white"/>
                </div>
                <div className="flex items-center gap-2 mb-6 border-b border-white/20 pb-2 relative z-10">
                    <Sparkles className="text-indigo-200" size={20} />
                    <h3 className="font-bold text-lg">Grammar Insights</h3>
                </div>
                <div className="space-y-4 relative z-10">
                    {grammar_stats && Object.entries(grammar_stats).map(([key, val]) => (
                    <div key={key} className="flex justify-between items-center text-sm">
                        <span className="capitalize opacity-90">{key.replace('_', ' ')}</span>
                        <span className="font-bold bg-white/20 px-2 py-0.5 rounded text-xs uppercase shadow-sm">{val}</span>
                    </div>
                    ))}
                </div>
            </div>

        </div>
      </div>
    </div>
  );
}