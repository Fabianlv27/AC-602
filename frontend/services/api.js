import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Tu Backend

const api = axios.create({
  baseURL: API_URL,
});

// Interceptor: Antes de cada petición, revisa si tenemos la llave guardada
api.interceptors.request.use((config) => {
  const adminKey = localStorage.getItem('adminKey');
  if (adminKey) {
    config.headers['x-admin-key'] = adminKey;
  }
  return config;
});

export default api; 