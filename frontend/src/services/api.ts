import axios from 'axios';
import {
  Contract,
  Clause,
  DocumentSection,
  ContractStats,
  RiskDistribution,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Contract API
export const contractApi = {
  uploadContract: async (file: File): Promise<Contract> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/contracts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getContracts: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    risk_level?: string;
  }): Promise<Contract[]> => {
    const response = await api.get('/contracts/', { params });
    return response.data;
  },

  getContract: async (id: number): Promise<Contract> => {
    const response = await api.get(`/contracts/${id}`);
    return response.data;
  },

  updateContract: async (
    id: number,
    data: Partial<Contract>
  ): Promise<Contract> => {
    const response = await api.put(`/contracts/${id}`, data);
    return response.data;
  },

  deleteContract: async (id: number): Promise<void> => {
    await api.delete(`/contracts/${id}`);
  },

  processContract: async (id: number): Promise<Contract> => {
    const response = await api.post(`/contracts/${id}/process`);
    return response.data;
  },

  reprocessContract: async (id: number): Promise<Contract> => {
    const response = await api.post(`/contracts/${id}/reprocess`);
    return response.data;
  },

  getContractFile: async (id: number): Promise<Blob> => {
    const response = await api.get(`/contracts/${id}/file`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Clause API
export const clauseApi = {
  getAllClauses: async (params?: {
    skip?: number;
    limit?: number;
    clause_type?: string;
    risk_level?: string;
  }): Promise<Clause[]> => {
    const response = await api.get('/clauses/', { params });
    return response.data;
  },

  getClauses: async (
    contractId: number,
    params?: {
      skip?: number;
      limit?: number;
      clause_type?: string;
      risk_level?: string;
    }
  ): Promise<Clause[]> => {
    const response = await api.get(`/contracts/${contractId}/clauses`, {
      params,
    });
    return response.data;
  },

  getClause: async (id: number): Promise<Clause> => {
    const response = await api.get(`/clauses/${id}`);
    return response.data;
  },

  createClause: async (data: Partial<Clause>): Promise<Clause> => {
    const response = await api.post('/clauses/', data);
    return response.data;
  },

  updateClause: async (id: number, data: Partial<Clause>): Promise<Clause> => {
    const response = await api.put(`/clauses/${id}`, data);
    return response.data;
  },

  deleteClause: async (id: number): Promise<void> => {
    await api.delete(`/clauses/${id}`);
  },

  analyzeClause: async (id: number): Promise<Clause> => {
    const response = await api.post(`/clauses/${id}/analyze`);
    return response.data;
  },
};

// Section API
export const sectionApi = {
  getSections: async (
    contractId: number,
    params?: {
      skip?: number;
      limit?: number;
      section_type?: string;
    }
  ): Promise<DocumentSection[]> => {
    const response = await api.get(`/contracts/${contractId}/sections`, {
      params,
    });
    return response.data;
  },

  getSection: async (id: number): Promise<DocumentSection> => {
    const response = await api.get(`/sections/${id}`);
    return response.data;
  },

  createSection: async (
    data: Partial<DocumentSection>
  ): Promise<DocumentSection> => {
    const response = await api.post('/sections/', data);
    return response.data;
  },

  updateSection: async (
    id: number,
    data: Partial<DocumentSection>
  ): Promise<DocumentSection> => {
    const response = await api.put(`/sections/${id}`, data);
    return response.data;
  },

  deleteSection: async (id: number): Promise<void> => {
    await api.delete(`/sections/${id}`);
  },
};

// Stats API
export const statsApi = {
  getContractStats: async (): Promise<ContractStats> => {
    const response = await api.get('/stats/contracts');
    return response.data;
  },

  getRiskDistribution: async (): Promise<RiskDistribution[]> => {
    const response = await api.get('/stats/risk-distribution');
    return response.data;
  },
};

export default api;

// Made with Bob
