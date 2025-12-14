import { useState } from 'react';
import { RfpPipelineResult } from '../types/rfp';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface UseRfpPipelineReturn {
  data: RfpPipelineResult | null;
  loading: boolean;
  error: string | null;
  runPipeline: () => Promise<void>;
}

export function useRfpPipeline(): UseRfpPipelineReturn {
  const [data, setData] = useState<RfpPipelineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runPipeline = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/run-rfp-pipeline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result: RfpPipelineResult = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Pipeline execution failed');
      }

      setData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to run pipeline';
      setError(errorMessage);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, runPipeline };
}

