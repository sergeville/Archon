import { callAPIWithETag } from "../../shared/api/apiClient";
import type { ContextEntry, ContextHistoryResponse, ContextListResponse, SetContextRequest } from "../types";

export const contextService = {
  async listContext(prefix?: string): Promise<ContextEntry[]> {
    try {
      const url = prefix ? `/api/context?prefix=${encodeURIComponent(prefix)}` : "/api/context";
      const response = await callAPIWithETag<ContextListResponse>(url);
      return response.context || [];
    } catch (error) {
      console.error("Failed to list context:", error);
      throw error;
    }
  },

  async getContext(key: string): Promise<ContextEntry> {
    try {
      const response = await callAPIWithETag<{ success: boolean; entry: ContextEntry }>(
        `/api/context/${encodeURIComponent(key)}`,
      );
      return response.entry;
    } catch (error) {
      console.error(`Failed to get context key ${key}:`, error);
      throw error;
    }
  },

  async setContext(key: string, data: SetContextRequest): Promise<ContextEntry> {
    try {
      const response = await callAPIWithETag<{ success: boolean; entry: ContextEntry }>(
        `/api/context/${encodeURIComponent(key)}`,
        {
          method: "PUT",
          body: JSON.stringify(data),
        },
      );
      return response.entry;
    } catch (error) {
      console.error(`Failed to set context key ${key}:`, error);
      throw error;
    }
  },

  async deleteContext(key: string): Promise<void> {
    try {
      await callAPIWithETag<void>(`/api/context/${encodeURIComponent(key)}`, {
        method: "DELETE",
      });
    } catch (error) {
      console.error(`Failed to delete context key ${key}:`, error);
      throw error;
    }
  },

  async getHistory(key: string, limit?: number): Promise<ContextHistoryResponse> {
    try {
      const url = limit
        ? `/api/context/${encodeURIComponent(key)}/history?limit=${limit}`
        : `/api/context/${encodeURIComponent(key)}/history`;
      const response = await callAPIWithETag<ContextHistoryResponse>(url);
      return response;
    } catch (error) {
      console.error(`Failed to get history for context key ${key}:`, error);
      throw error;
    }
  },
};
