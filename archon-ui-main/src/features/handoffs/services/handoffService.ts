import { callAPIWithETag } from "../../shared/api/apiClient";
import type { CreateHandoffRequest, Handoff, HandoffFilterParams, HandoffsListResponse } from "../types";

export const handoffService = {
  async listHandoffs(params?: HandoffFilterParams): Promise<Handoff[]> {
    try {
      const searchParams = new URLSearchParams();
      if (params?.session_id) searchParams.append("session_id", params.session_id);
      if (params?.agent) searchParams.append("agent", params.agent);
      if (params?.status) searchParams.append("status", params.status);
      const queryString = searchParams.toString();
      const url = queryString ? `/api/handoffs?${queryString}` : "/api/handoffs";
      const response = await callAPIWithETag<HandoffsListResponse>(url);
      return response.handoffs || [];
    } catch (error) {
      console.error("Failed to list handoffs:", error);
      throw error;
    }
  },

  async getPendingHandoffs(agent: string): Promise<Handoff[]> {
    try {
      const response = await callAPIWithETag<HandoffsListResponse>(`/api/handoffs/pending/${agent}`);
      return response.handoffs || [];
    } catch (error) {
      console.error(`Failed to get pending handoffs for agent ${agent}:`, error);
      throw error;
    }
  },

  async getHandoff(id: string): Promise<Handoff> {
    try {
      const response = await callAPIWithETag<{ success: boolean; handoff: Handoff }>(`/api/handoffs/${id}`);
      return response.handoff;
    } catch (error) {
      console.error(`Failed to get handoff ${id}:`, error);
      throw error;
    }
  },

  async createHandoff(data: CreateHandoffRequest): Promise<Handoff> {
    try {
      const response = await callAPIWithETag<{ success: boolean; handoff: Handoff }>("/api/handoffs", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return response.handoff;
    } catch (error) {
      console.error("Failed to create handoff:", error);
      throw error;
    }
  },

  async acceptHandoff(id: string): Promise<Handoff> {
    try {
      const response = await callAPIWithETag<{ success: boolean; handoff: Handoff }>(`/api/handoffs/${id}/accept`, {
        method: "POST",
      });
      return response.handoff;
    } catch (error) {
      console.error(`Failed to accept handoff ${id}:`, error);
      throw error;
    }
  },

  async completeHandoff(id: string): Promise<Handoff> {
    try {
      const response = await callAPIWithETag<{ success: boolean; handoff: Handoff }>(`/api/handoffs/${id}/complete`, {
        method: "POST",
      });
      return response.handoff;
    } catch (error) {
      console.error(`Failed to complete handoff ${id}:`, error);
      throw error;
    }
  },

  async rejectHandoff(id: string): Promise<Handoff> {
    try {
      const response = await callAPIWithETag<{ success: boolean; handoff: Handoff }>(`/api/handoffs/${id}/reject`, {
        method: "POST",
      });
      return response.handoff;
    } catch (error) {
      console.error(`Failed to reject handoff ${id}:`, error);
      throw error;
    }
  },
};
