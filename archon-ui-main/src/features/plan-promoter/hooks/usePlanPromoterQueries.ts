import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { STALE_TIMES } from "../../shared/config/queryPatterns";
import { planPromoterService } from "../services/planPromoterService";
import type { PromoteRequest } from "../types";

export const planPromoterKeys = {
  all: ["plan-promoter"] as const,
  plans: () => [...planPromoterKeys.all, "plans"] as const,
};

export function usePlans() {
  return useQuery({
    queryKey: planPromoterKeys.plans(),
    queryFn: () => planPromoterService.listPlans(),
    staleTime: STALE_TIMES.rare,
  });
}

export function usePromotePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: PromoteRequest) => planPromoterService.promotePlan(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: planPromoterKeys.plans() });
    },
  });
}
