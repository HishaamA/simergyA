import axios from 'axios';
import type { PredictionResult, BatchPredictionResponse, ModelInfo, PredictionSettings } from '../types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export async function getModelInfo(): Promise<ModelInfo> {
  const response = await api.get<ModelInfo>('/model/info');
  return response.data;
}

export async function predictSingle(
  file: File,
  settings: PredictionSettings
): Promise<PredictionResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('relax_structure', String(settings.relax_structure));
  formData.append('relax_steps', String(settings.relax_steps));
  formData.append('force_threshold', String(settings.force_threshold));

  const response = await api.post<PredictionResult>('/predict', formData);
  return response.data;
}

export async function predictBatch(
  files: File[],
  settings: PredictionSettings
): Promise<BatchPredictionResponse> {
  const formData = new FormData();
  
  files.forEach((file) => {
    formData.append('files', file);
  });
  
  formData.append('relax_structure', String(settings.relax_structure));
  formData.append('relax_steps', String(settings.relax_steps));
  formData.append('force_threshold', String(settings.force_threshold));

  const response = await api.post<BatchPredictionResponse>('/predict/batch', formData);
  return response.data;
}

export default api;
