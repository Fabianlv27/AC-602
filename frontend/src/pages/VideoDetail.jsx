import { useEffect, useState, useRef } from "react";
import ReactPlayer from "react-player/youtube";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Brain,
  FileText,
  Activity,
  Captions,
  Clock,
  BarChart,
  Globe,
  BookOpen,
  Book,
  GraduationCap,
  Zap,
} from "lucide-react";
import api from "../services/api";

export default function VideoDetail() {
  const { id } = useParams();
  const [video, setVideo] = useState(null);
  const playerRef = useRef(null);

  // Función para saltar al segundo exacto
  const handleSeek = (seconds) => {
    playerRef.current?.seekTo(seconds, "seconds");
  };

  const langNames = {
    en: "Inglés",
    es: "Español",
    fr: "Francés",
    de: "Alemán",
    it: "Italiano",
    pt: "Portugués",
  };

  // Helper para el badge de subtítulos
  const getSubtitleBadge = (source) => {
    switch (source) {
      case "manual":
        return {
          text: "Manuales (Preciso)",
          color: "bg-emerald-100 text-emerald-800 border-emerald-200",
        };
      case "generated":
        return {
          text: "Auto-generados",
          color: "bg-amber-100 text-amber-800 border-amber-200",
        };
      default:
        return {
          text: "Sin subtítulos",
          color: "bg-slate-100 text-slate-600 border-slate-200",
        };
    }
  };

  useEffect(() => {
    api
      .get(`/videos/${id}`)
      .then((res) => setVideo(res.data))
      .catch(console.error);
  }, [id]);

  if (!video)
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-500 font-medium">Cargando lección...</p>
        </div>
      </div>
    );

  const subInfo = getSubtitleBadge(video.subtitle_source);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 min-h-screen">
      {/* Breadcrumb */}
      <Link
        to="/"
        className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-indigo-600 mb-6 transition-colors"
      >
        <ArrowLeft size={16} className="mr-1" /> Volver al buscador
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* --- COLUMNA IZQUIERDA (VIDEO & TRANSCRIPT) --- */}
        <div className="lg:col-span-2 space-y-6">
          {/* REPRODUCTOR INTERACTIVO (ReactPlayer) */}
          <div className="bg-black rounded-3xl overflow-hidden shadow-2xl aspect-video relative ring-4 ring-white z-10">
            <ReactPlayer
              ref={playerRef}
              url={`https://www.youtube.com/watch?v=${video.video_id}`}
              width="100%"
              height="100%"
              controls
              config={{
                youtube: {
                  playerVars: { showinfo: 1, modestbranding: 1, rel: 0 },
                },
              }}
            />
          </div>

          {/* SECCIÓN DE TRANSCRIPCIÓN */}
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 h-[600px] flex flex-col">
            <div className="flex items-center gap-3 mb-4 border-b border-slate-100 pb-4 shrink-0">
              <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                <FileText size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-800">
                Resumen y Transcripción
              </h2>
            </div>

            <div className="overflow-y-auto pr-2 custom-scrollbar flex-1">
              {/* Resumen IA */}
              {video.ai_analysis?.summary && (
                <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 mb-6 italic text-slate-600 relative mx-1">
                  <span className="absolute top-2 left-3 text-4xl text-slate-200 font-serif">
                    "
                  </span>
                  <p className="relative z-10 m-0 pl-4 text-sm leading-relaxed">
                    {video.ai_analysis.summary}
                  </p>
                </div>
              )}

              {/* TRANSCRIPCIÓN INTERACTIVA */}
              {video.transcript_json && video.transcript_json.length > 0 ? (
                <div className="space-y-1">
                  {video.transcript_json.map((line, index) => (
                    <div
                      key={index}
                      onClick={() => handleSeek(line.start)}
                      className="group flex gap-4 p-3 hover:bg-indigo-50 rounded-xl cursor-pointer transition-all duration-200 border border-transparent hover:border-indigo-100"
                    >
                      <span className="text-xs font-mono font-bold text-indigo-400 mt-1 bg-indigo-50/50 px-2 py-0.5 rounded group-hover:bg-white group-hover:text-indigo-600 transition-colors h-fit whitespace-nowrap">
                        {new Date(line.start * 1000)
                          .toISOString()
                          .substr(14, 5)}
                      </span>
                      <p className="text-slate-700 text-sm leading-relaxed group-hover:text-slate-900">
                        {line.text}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                /* Fallback Texto Plano */
                <div className="whitespace-pre-wrap font-sans text-base text-slate-700 p-2 leading-loose">
                  {video.transcript ||
                    video.ai_analysis?.transcript_summary ||
                    "Transcripción no disponible."}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* --- COLUMNA DERECHA (METADATA & AI) --- */}
        <div className="space-y-6">
          {/* TARJETA PRINCIPAL DE INFO */}
          <div className="bg-white rounded-3xl p-6 shadow-lg border border-indigo-50 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-40 h-40 bg-indigo-50 rounded-full -mr-20 -mt-20 opacity-60 pointer-events-none"></div>

            <h1 className="text-xl font-bold text-slate-900 mb-2 relative z-10 leading-snug pr-10">
              {video.title}
            </h1>

            <p className="text-indigo-600 font-medium mb-6 relative z-10 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-600"></span>
              {video.channel_name}
            </p>

            {/* BADGE IDIOMA */}
            <div className="absolute top-6 right-6 flex items-center gap-1 bg-white/80 backdrop-blur text-slate-600 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm border border-slate-200">
              <Globe size={14} />
              {langNames[video.language] || video.language || "N/A"}
            </div>

            {/* Métricas Clave */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex flex-col items-center justify-center text-center group hover:border-indigo-200 transition-colors">
                <BarChart
                  size={20}
                  className="text-slate-400 mb-2 group-hover:text-indigo-500 transition-colors"
                />
                <div className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">
                  Nivel
                </div>
                <div className="text-2xl font-black text-slate-800">
                  {video.level || "-"}
                </div>
              </div>

              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex flex-col items-center justify-center text-center group hover:border-indigo-200 transition-colors">
                <Clock
                  size={20}
                  className="text-slate-400 mb-2 group-hover:text-indigo-500 transition-colors"
                />
                <div className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">
                  Velocidad
                </div>
                <div className="text-2xl font-black text-slate-800">
                  {video.wpm}{" "}
                  <span className="text-xs font-normal text-slate-500">
                    wpm
                  </span>
                </div>
              </div>
            </div>

            {/* Badge de Subtítulos */}
            <div
              className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl border ${subInfo.color} font-medium text-sm`}
            >
              <Captions size={18} />
              {subInfo.text}
            </div>
          </div>

          {/* TARJETA DE ANÁLISIS LINGÜÍSTICO (AI) */}
          <div className="bg-gradient-to-br from-indigo-600 to-violet-700 rounded-3xl p-6 text-white shadow-xl">
            <div className="flex items-center gap-2 mb-6 border-b border-indigo-400/30 pb-4">
              <Brain className="text-indigo-200" />
              <h3 className="font-bold text-lg">Análisis de IA</h3>
            </div>

            <div className="space-y-6">
              {/* Tópicos */}
              <div>
                <span className="text-indigo-200 text-xs font-bold uppercase block mb-3 flex items-center gap-1">
                  Temas Detectados
                </span>
                <div className="flex flex-wrap gap-2">
                  {video.topics?.length > 0 ? (
                    video.topics.map((t) => (
                      <span
                        key={t}
                        className="bg-white/10 hover:bg-white/20 backdrop-blur-md px-3 py-1.5 rounded-lg text-sm border border-white/10 transition cursor-default"
                      >
                        {t}
                      </span>
                    ))
                  ) : (
                    <span className="text-indigo-300 text-sm italic">
                      Sin temas etiquetados
                    </span>
                  )}
                </div>
              </div>

              {/* TIPO DE VOCABULARIO (Nuevo) */}
              <div>
                <span className="text-indigo-200 text-xs font-bold uppercase block mb-3 flex items-center gap-1">
                  <BookOpen size={14} /> Estilo / Vocabulario
                </span>
                <div className="flex flex-wrap gap-2">
                  {video.content_types?.length > 0 ? (
                    video.content_types.map((type) => (
                      <div
                        key={type}
                        className="flex items-center gap-2 bg-white text-indigo-900 px-3 py-1.5 rounded-lg text-xs font-bold shadow-sm"
                      >
                        {type.toLowerCase().includes("formal")
                          ? "👔"
                          : type.toLowerCase().includes("slang")
                          ? "😎"
                          : "💬"}
                        {type}
                      </div>
                    ))
                  ) : (
                    <span className="text-indigo-300 text-sm italic">
                      No especificado
                    </span>
                  )}
                </div>
              </div>

              {/* Acentos */}
              <div>
                <span className="text-indigo-200 text-xs font-bold uppercase block mb-3 flex items-center gap-1">
                  <Activity size={14} /> Acentos
                </span>
                <div className="flex flex-wrap gap-2">
                  {video.accents?.length > 0 ? (
                    video.accents.map((a) => (
                      <span
                        key={a}
                        className="flex items-center gap-1.5 text-sm text-white bg-white/10 px-3 py-1 rounded-full border border-white/5"
                      >
                        {a.includes("British")
                          ? "🇬🇧"
                          : a.includes("American")
                          ? "🇺🇸"
                          : "🌍"}{" "}
                        {a}
                      </span>
                    ))
                  ) : (
                    <span className="text-indigo-300 text-sm italic">
                      Neutro / No detectado
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* --- NUEVA SECCIÓN: VOCABULARIO Y GRAMÁTICA --- */}
        <div className="space-y-6 mt-6">
          {/* TARJETA DE VOCABULARIO */}
          <div className="bg-white rounded-3xl p-6 shadow-lg border border-indigo-50">
            <div className="flex items-center gap-2 mb-4 border-b pb-2">
              <Book className="text-indigo-600" size={20} />
              <h3 className="font-bold text-lg text-slate-800">
                Vocabulario Clave
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {video.ai_analysis?.vocabulary?.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-slate-50 p-3 rounded-xl border border-slate-100 hover:border-indigo-200 transition-colors"
                >
                  <p className="font-bold text-indigo-700 text-sm mb-1">
                    {item.term}
                  </p>
                  <p className="text-slate-600 text-xs leading-relaxed">
                    {item.definition}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* TARJETA DE GRAMÁTICA Y USO */}
          <div className="bg-white rounded-3xl p-6 shadow-lg border border-indigo-50">
            <div className="flex items-center gap-2 mb-4 border-b pb-2">
              <GraduationCap className="text-indigo-600" size={20} />
              <h3 className="font-bold text-lg text-slate-800">
                Foco Gramatical
              </h3>
            </div>

            <div className="space-y-4">
              {/* Estadística Visual Simple */}
              {video.ai_analysis?.grammar_stats &&
                Object.entries(video.ai_analysis.grammar_stats).map(
                  ([key, val]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between"
                    >
                      <span className="text-sm text-slate-600 capitalize">
                        {key.replace("_", " ")}
                      </span>
                      <span
                        className={`text-xs font-bold px-2 py-1 rounded-md ${
                          val === "Alto"
                            ? "bg-indigo-100 text-indigo-700"
                            : val === "Medio"
                            ? "bg-slate-100 text-slate-600"
                            : "bg-slate-50 text-slate-400"
                        }`}
                      >
                        {val}
                      </span>
                    </div>
                  )
                )}

              {/* Uso Funcional (Bonus) */}
              {video.ai_analysis?.functional_use && (
                <div className="mt-4 p-3 bg-amber-50 rounded-xl border border-amber-100 flex gap-3">
                  <Zap className="text-amber-500 shrink-0" size={18} />
                  <div>
                    <p className="text-xs font-bold text-amber-800 uppercase mb-0.5">
                      Mejor para aprender:
                    </p>
                    <p className="text-sm text-amber-900">
                      {video.ai_analysis.functional_use}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
