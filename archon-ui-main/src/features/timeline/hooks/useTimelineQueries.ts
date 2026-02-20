import { useQuery } from "@tanstack/react-query";
import { useSmartPolling } from "@/features/shared/hooks";
import { STALE_TIMES } from "../../shared/config/queryPatterns";
import { timelineService } from "../services";
import type { AuditLogFilters } from "../types";

export const timelineKeys = {
  all: ["timeline"] as const,
  lists: () => [...timelineKeys.all, "list"] as const,
  listWithFilters: (filters?: AuditLogFilters) => [...timelineKeys.all, "list", filters] as const,
};

export function useAuditLog(filters?: AuditLogFilters) {
  const { refetchInterval } = useSmartPolling(5000);

  return useQuery({
    queryKey: timelineKeys.listWithFilters(filters),
    queryFn: () => timelineService.listAuditLog(filters),
    refetchInterval,
    refetchOnWindowFocus: true,
    staleTime: STALE_TIMES.frequent,
  });
}
