import { callAPIWithETag } from "../../shared/api/apiClient";
import type { PlansResponse, PromoteRequest, PromoteResult } from "../types";

export const planPromoterService = {
  async listPlans(): Promise<PlansResponse> {
    return callAPIWithETag<PlansResponse>("/api/plan-promoter/plans");
  },

  async promotePlan(request: PromoteRequest): Promise<PromoteResult> {
    return callAPIWithETag<PromoteResult>("/api/plan-promoter/promote", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
};
