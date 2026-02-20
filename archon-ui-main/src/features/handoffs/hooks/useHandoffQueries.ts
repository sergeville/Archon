import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSmartPolling } from "@/features/shared/hooks";
import { useToast } from "@/features/shared/hooks/useToast";
import { DISABLED_QUERY_KEY, STALE_TIMES } from "../../shared/config/queryPatterns";
import { handoffService } from "../services";
import type { CreateHandoffRequest, HandoffFilterParams } from "../types";

export const handoffKeys = {
  all: ["handoffs"] as const,
  lists: () => [...handoffKeys.all, "list"] as const,
  listWithFilters: (filters?: HandoffFilterParams) => [...handoffKeys.all, "list", filters] as const,
  detail: (id: string) => [...handoffKeys.all, "detail", id] as const,
  pending: (agent: string) => [...handoffKeys.all, "pending", agent] as const,
};

export function useHandoffs(filters?: HandoffFilterParams) {
  const { refetchInterval } = useSmartPolling(5000);

  return useQuery({
    queryKey: handoffKeys.listWithFilters(filters),
    queryFn: () => handoffService.listHandoffs(filters),
    refetchInterval,
    refetchOnWindowFocus: true,
    staleTime: STALE_TIMES.frequent,
  });
}

export function usePendingHandoffs(agent: string) {
  const { refetchInterval } = useSmartPolling(5000);

  return useQuery({
    queryKey: agent ? handoffKeys.pending(agent) : DISABLED_QUERY_KEY,
    queryFn: () => (agent ? handoffService.getPendingHandoffs(agent) : Promise.reject("No agent")),
    enabled: !!agent,
    refetchInterval,
    staleTime: STALE_TIMES.frequent,
  });
}

export function useHandoff(id: string | undefined) {
  return useQuery({
    queryKey: id ? handoffKeys.detail(id) : DISABLED_QUERY_KEY,
    queryFn: () => (id ? handoffService.getHandoff(id) : Promise.reject("No handoff ID")),
    enabled: !!id,
    staleTime: STALE_TIMES.normal,
  });
}

export function useCreateHandoff() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: CreateHandoffRequest) => handoffService.createHandoff(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: handoffKeys.lists() });
      showToast("Handoff created successfully", "success");
    },
    onError: (error) => {
      console.error("Failed to create handoff:", error);
      showToast("Failed to create handoff", "error");
    },
  });
}

export function useAcceptHandoff() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => handoffService.acceptHandoff(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: handoffKeys.lists() });
      queryClient.invalidateQueries({ queryKey: handoffKeys.detail(id) });
      showToast("Handoff accepted", "success");
    },
    onError: (error) => {
      console.error("Failed to accept handoff:", error);
      showToast("Failed to accept handoff", "error");
    },
  });
}

export function useCompleteHandoff() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => handoffService.completeHandoff(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: handoffKeys.lists() });
      queryClient.invalidateQueries({ queryKey: handoffKeys.detail(id) });
      showToast("Handoff completed", "success");
    },
    onError: (error) => {
      console.error("Failed to complete handoff:", error);
      showToast("Failed to complete handoff", "error");
    },
  });
}

export function useRejectHandoff() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => handoffService.rejectHandoff(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: handoffKeys.lists() });
      queryClient.invalidateQueries({ queryKey: handoffKeys.detail(id) });
      showToast("Handoff rejected", "success");
    },
    onError: (error) => {
      console.error("Failed to reject handoff:", error);
      showToast("Failed to reject handoff", "error");
    },
  });
}
