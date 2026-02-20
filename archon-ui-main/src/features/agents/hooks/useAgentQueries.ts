import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSmartPolling } from "@/features/shared/hooks";
import { useToast } from "@/features/shared/hooks/useToast";
import { DISABLED_QUERY_KEY, STALE_TIMES } from "../../shared/config/queryPatterns";
import { agentService } from "../services";
import type { AgentStatus, RegisterAgentRequest } from "../types";

export const agentKeys = {
  all: ["agents"] as const,
  lists: () => [...agentKeys.all, "list"] as const,
  listWithFilter: (status?: AgentStatus) => [...agentKeys.all, "list", status] as const,
  detail: (name: string) => [...agentKeys.all, "detail", name] as const,
};

export function useAgents(status?: AgentStatus) {
  const { refetchInterval } = useSmartPolling(5000);

  return useQuery({
    queryKey: agentKeys.listWithFilter(status),
    queryFn: () => agentService.listAgents(status),
    refetchInterval,
    refetchOnWindowFocus: true,
    staleTime: STALE_TIMES.frequent,
  });
}

export function useAgent(name: string | undefined) {
  return useQuery({
    queryKey: name ? agentKeys.detail(name) : DISABLED_QUERY_KEY,
    queryFn: () => (name ? agentService.getAgent(name) : Promise.reject("No agent name")),
    enabled: !!name,
    staleTime: STALE_TIMES.normal,
  });
}

export function useRegisterAgent() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: RegisterAgentRequest) => agentService.registerAgent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      showToast("Agent registered successfully", "success");
    },
    onError: (error) => {
      console.error("Failed to register agent:", error);
      showToast("Failed to register agent", "error");
    },
  });
}

export function useHeartbeat() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (name: string) => agentService.heartbeat(name),
    onSuccess: (_response, name) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.detail(name) });
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      showToast("Heartbeat sent", "success");
    },
    onError: (error) => {
      console.error("Failed to send heartbeat:", error);
      showToast("Failed to send heartbeat", "error");
    },
  });
}

export function useDeactivateAgent() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (name: string) => agentService.deactivateAgent(name),
    onSuccess: (_response, name) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.detail(name) });
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      showToast("Agent deactivated", "success");
    },
    onError: (error) => {
      console.error("Failed to deactivate agent:", error);
      showToast("Failed to deactivate agent", "error");
    },
  });
}
