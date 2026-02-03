import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryApi } from '@/lib/api';
import type { QueryRequest, QueryResponse } from '@/types/api';
import { useQueryHistory } from './useQueryHistory';

export const useSubmitQuery = () => {
  const queryClient = useQueryClient();
  const { addToHistory } = useQueryHistory();

  return useMutation({
    mutationFn: (request: QueryRequest) => queryApi.submitQuery(request),
    onSuccess: (data: QueryResponse) => {
      // Add to query history
      addToHistory({
        id: data.query_id,
        query: data.natural_language_query,
        timestamp: new Date(),
        response: data,
      });

      // Cache the query result
      queryClient.setQueryData(['query', data.query_id], data);
    },
  });
};

