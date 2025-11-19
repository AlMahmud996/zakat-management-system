import axios from 'axios';

// Base URL for API
const API_URL = 'http://127.0.0.1:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth APIs
export const register = async (userData) => {
  const response = await api.post('/auth/register', userData);
  return response.data;
};

export const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email); // FastAPI OAuth2 uses 'username' field
  formData.append('password', password);
  
  const response = await axios.post(`${API_URL}/auth/login`, formData);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// Zakat APIs
export const createZakat = async (zakatData) => {
  const response = await api.post('/zakat', zakatData);
  return response.data;
};

export const getZakatEntries = async () => {
  const response = await api.get('/zakat');
  return response.data;
};

export const getZakatEntry = async (id) => {
  const response = await api.get(`/zakat/${id}`);
  return response.data;
};

export const updateZakat = async (id, zakatData) => {
  const response = await api.put(`/zakat/${id}`, zakatData);
  return response.data;
};

export const deleteZakat = async (id) => {
  await api.delete(`/zakat/${id}`);
};

export const getZakatStatistics = async () => {
  const response = await api.get('/zakat/statistics/summary');
  return response.data;
};

export default api;