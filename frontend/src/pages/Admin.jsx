import { useState, useEffect } from 'react';
import { Trash2, Upload, Key } from 'lucide-react';
import api from '../../services/api';


export default function Admin() {
  const [key, setKey] = useState('');
  const [isAuth, setIsAuth] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [status, setStatus] = useState(null);

  // Al cargar, revisar si ya hay clave
  useEffect(() => {
    const stored = localStorage.getItem('adminKey');
    if (stored) {
      setKey(stored);
      setIsAuth(true);
    }
  }, []);

  const handleLogin = (e) => {
    e.preventDefault();
    localStorage.setItem('adminKey', key);
    setIsAuth(true);
  };

  const handleBatchUpload = async () => {
    try {
      setStatus({ type: 'info', msg: 'Subiendo...' });
      const data = JSON.parse(jsonInput); // Validar que sea JSON
      
      const res = await api.post('/videos/batch/', data);
      setStatus({ 
        type: 'success', 
        msg: `Éxito: ${res.data.created} creados, ${res.data.ignored_duplicates} ignorados.` 
      });
      setJsonInput('');
    } catch (error) {
      console.error(error);
      setStatus({ type: 'error', msg: 'Error: JSON inválido o clave incorrecta.' });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('adminKey');
    setIsAuth(false);
    setKey('');
  };

  if (!isAuth) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 bg-white rounded-xl shadow border text-center">
        <div className="flex justify-center mb-4 text-indigo-600"><Key size={40} /></div>
        <h2 className="text-2xl font-bold mb-4">Zona Administrativa</h2>
        <form onSubmit={handleLogin}>
          <input
            type="password"
            placeholder="Introduce tu Admin Secret"
            className="w-full border p-3 rounded mb-4"
            value={key}
            onChange={e => setKey(e.target.value)}
          />
          <button className="w-full bg-indigo-600 text-white p-3 rounded font-bold hover:bg-indigo-700">
            Acceder
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Panel de Control</h1>
        <button onClick={handleLogout} className="text-red-500 underline">Cerrar Sesión</button>
      </div>

      {/* Carga Masiva */}
      <div className="bg-white p-6 rounded-xl shadow-sm border mb-8">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Upload size={20} /> Carga Masiva (JSON)
        </h2>
        <p className="text-sm text-slate-500 mb-2">Pega aquí un array de objetos JSON para insertar múltiples videos.</p>
        
        <textarea
          rows={10}
          className="w-full border p-4 rounded bg-slate-50 font-mono text-sm"
          placeholder='[{"video_id": "...", "title": "...", "url": "..."}]'
          value={jsonInput}
          onChange={e => setJsonInput(e.target.value)}
        />
        
        <div className="mt-4 flex justify-between items-center">
          <button 
            onClick={handleBatchUpload}
            className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 font-bold"
          >
            Subir Videos
          </button>
          
          {status && (
            <div className={`text-sm font-bold ${status.type === 'error' ? 'text-red-600' : 'text-green-600'}`}>
              {status.msg}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}