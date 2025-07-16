import axios from 'axios';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for API responses
export interface JobConfig {
  ai_provider: 'openai' | 'anthropic' | 'google';
  ai_model: string;
  pdf_style: string;
  combine_by_group: boolean;
  temperature: number;
}

export interface JobSubmissionRequest {
  urls: string[];
  config?: JobConfig;
}

export interface JobResponse {
  job_id: string;
  status: string;
  message: string;
  status_url: string;
}

export interface JobInfo {
  id: string;
  status: 'pending' | 'downloading' | 'processing' | 'generating_pdf' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message: string;
  config: JobConfig;
  urls: string[];
  created_at: string;
  started_at?: string;
  completed_at?: string;
  download_url?: string;
  error_message?: string;
}

export interface JobListResponse {
  jobs: JobInfo[];
  total: number;
  page: number;
  size: number;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  models: string[];
  available: boolean;
  description: string;
}

// API functions
export const whimpizerAPI = {
  // Health check
  health: () => api.get('/health'),

  // Job management
  submitJob: (data: JobSubmissionRequest): Promise<{ data: JobResponse }> =>
    api.post('/api/jobs', data),

  getJobStatus: (jobId: string): Promise<{ data: JobInfo }> =>
    api.get(`/api/jobs/${jobId}/status`),

  listJobs: (page = 1, size = 10, status?: string): Promise<{ data: JobListResponse }> => {
    const params = new URLSearchParams({ page: page.toString(), size: size.toString() });
    if (status) params.append('status', status);
    return api.get(`/api/jobs?${params}`);
  },

  downloadPDF: (jobId: string) =>
    api.get(`/api/jobs/${jobId}/download`, { responseType: 'blob' }),

  cancelJob: (jobId: string) =>
    api.delete(`/api/jobs/${jobId}`),

  // Provider management
  listProviders: (): Promise<{ data: ProviderInfo[] }> =>
    api.get('/api/providers'),

  getProviderInfo: (providerName: string): Promise<{ data: ProviderInfo }> =>
    api.get(`/api/providers/${providerName}`),

  testProviderConnection: (providerName: string) =>
    api.post(`/api/providers/${providerName}/test`),
};

// Utility function to download blob as file
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};