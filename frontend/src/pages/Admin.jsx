import { useState } from 'react';
import api from '../../services/api';
import { Plus, Save, X } from 'lucide-react';

export default function Admin() {
  const [formData, setFormData] = useState({
    video_id: '',
    title: '',
    channel_name: '',
    url: '',
    level: 'B1',
    language: 'en',
    // Campos nuevos: Strings separados por comas para simular Arrays
    topics_str: '',
    accents_str: '',
    content_types_str: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Transformar strings a arrays para el backend
    const payload = {
      ...formData,
      topics: formData.topics_str.split(',').map(s => s.trim()).filter(Boolean),
      accents: formData.accents_str.split(',').map(s => s.trim()).filter(Boolean),
      content_types: formData.content_types_str.split(',').map(s => s.trim()).filter(Boolean),
      // Campos por defecto para evitar errores
      wpm: 150,
      transcript_json: [], 
      ai_analysis: {} 
    };

    // Limpiamos los temporales
    delete payload.topics_str;
    delete payload.accents_str;
    delete payload.content_types_str;

    try {
      await api.post('/videos/', payload);
      alert('Video creado con éxito');
      setFormData({ ...formData, video_id: '', title: '' }); // Reset parcial
    } catch (err) {
      console.error(err);
      alert('Error creando video');
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <div className="bg-white rounded-3xl p-8 shadow-xl border border-indigo-50">
        <div className="flex items-center gap-3 mb-8 border-b pb-4">
          <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl"><Plus size={24}/></div>
          <h1 className="text-2xl font-bold text-slate-800">Añadir Video Manual</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Video ID</label>
              <input name="video_id" value={formData.video_id} onChange={handleChange} className="w-full p-3 bg-slate-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-indigo-200 transition" required />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Nivel</label>
              <select name="level" value={formData.level} onChange={handleChange} className="w-full p-3 bg-slate-50 rounded-xl border-transparent">
                 {['A1','A2','B1','B2','C1','C2'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
          </div>

          <div>
             <label className="block text-sm font-bold text-slate-700 mb-1">Título</label>
             <input name="title" value={formData.title} onChange={handleChange} className="w-full p-3 bg-slate-50 rounded-xl border-transparent" required />
          </div>

          <div>
             <label className="block text-sm font-bold text-slate-700 mb-1">URL Completa</label>
             <input name="url" value={formData.url} onChange={handleChange} className="w-full p-3 bg-slate-50 rounded-xl border-transparent" required />
          </div>

          {/* INPUTS PARA ARRAYS */}
          <div>
             <label className="block text-sm font-bold text-slate-700 mb-1">Acentos (separar por comas)</label>
             <input name="accents_str" placeholder="US, British, Southern" value={formData.accents_str} onChange={handleChange} className="w-full p-3 bg-slate-50 rounded-xl border-transparent" />
          </div>

          <div>
             <label className="block text-sm font-bold text-slate-700 mb-1">Topics (separar por comas)</label>
             <input name="topics_str" placeholder="Tech, Travel, Vlog" value={formData.topics_str} onChange={handleChange} className="w-full p-3 bg-slate-50 rounded-xl border-transparent" />
          </div>

          <button type="submit" className="w-full bg-indigo-600 text-white font-bold py-4 rounded-xl hover:bg-indigo-700 transition shadow-lg hover:shadow-indigo-200 flex justify-center items-center gap-2">
            <Save size={20} /> Guardar Video
          </button>
        </form>
      </div>
    </div>
  );
}