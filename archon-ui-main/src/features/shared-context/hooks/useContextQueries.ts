import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/features/shared/hooks/useToast";
import { DISABLED_QUERY_KEY, STALE_TIMES } from "../../shared/config/queryPatterns";
import { contextService } from "../services";
import type { SetContextRequest } from "../types";

export const contextKeys = {
  all: ["context"] as const,
  lists: () => [...contextKeys.all, "list"] as const,
  listWithPrefix: (prefix?: string) => [...contextKeys.all, "list", prefix] as const,
  detail: (key: string) => [...contextKeys.all, "detail", key] as const,
  history: (key: string) => [...contextKeys.all, key, "history"] as const,
};

export function useContextEntries(prefix?: string) {
  return useQuery({
    queryKey: contextKeys.listWithPrefix(prefix),
    queryFn: () => contextService.listContext(prefix),
    refetchOnWindowFocus: true,
    staleTime: STALE_TIMES.frequent,
  });
}

export function useContextEntry(key: string | undefined) {
  return useQuery({
    queryKey: key ? contextKeys.detail(key) : DISABLED_QUERY_KEY,
    queryFn: () => (key ? contextService.getContext(key) : Promise.reject("No context key")),
    enabled: !!key,
    staleTime: STALE_TIMES.frequent,
  });
}

export function useContextHistory(key: string | undefined, limit?: number) {
  return useQuery({
    queryKey: key ? contextKeys.history(key) : DISABLED_QUERY_KEY,
    queryFn: () => (key ? contextService.getHistory(key, limit) : Promise.reject("No context key")),
    enabled: !!key,
    staleTime: STALE_TIMES.frequent,
  });
}

export function useSetContext() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: ({ key, data }: { key: string; data: SetContextRequest }) => contextService.setContext(key, data),
    onSuccess: (_response, { key }) => {
      queryClient.invalidateQueries({ queryKey: contextKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contextKeys.detail(key) });
      queryClient.invalidateQueries({ queryKey: contextKeys.history(key) });
      showToast("Context value set successfully", "success");
    },
    onError: (error) => {
      console.error("Failed to set context:", error);
      showToast("Failed to set context value", "error");
    },
  });
}

export function useDeleteContext() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (key: string) => contextService.deleteContext(key),
    onSuccess: (_response, key) => {
      queryClient.invalidateQueries({ queryKey: contextKeys.lists() });
      queryClient.removeQueries({ queryKey: contextKeys.detail(key) });
      showToast("Context entry deleted", "success");
    },
    onError: (error) => {
      console.error("Failed to delete context:", error);
      showToast("Failed to delete context entry", "error");
    },
  });
}
