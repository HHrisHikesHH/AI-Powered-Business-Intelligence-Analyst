import axios from 'axios';
import type { QueryRequest, QueryResponse, AdminMetricsResponse } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const queryApi = {
  submitQuery: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await apiClient.post<QueryResponse>('/queries/', request);
    return response.data;
  },

  getQueryResult: async (queryId: string): Promise<QueryResponse> => {
    const response = await apiClient.get<QueryResponse>(`/queries/${queryId}`);
    return response.data;
  },
};

export const adminApi = {
  getMetrics: async (): Promise<AdminMetricsResponse> => {
    const response = await apiClient.get<AdminMetricsResponse>('/admin/metrics');
    return response.data;
  },
};

export default apiClient;

