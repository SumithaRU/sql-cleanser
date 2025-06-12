// @ts-nocheck
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
});

export const uploadFiles = async (files: File[]) => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const res = await api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  return res.data;
};

export const getStatus = async (jobId: string) => {
  const res = await api.get(`/status/${jobId}`);
  return res.data;
};

export const downloadZip = (jobId: string) => {
  return `${api.defaults.baseURL}/download/${jobId}`;
}; 