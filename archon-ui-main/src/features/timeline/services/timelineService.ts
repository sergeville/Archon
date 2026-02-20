import { callAPIWithETag } from "../../shared/api/apiClient";
import type { AuditLogEntry, AuditLogFilters, AuditLogListResponse } from "../types";

export const timelineService = {
  async listAuditLog(filters?: AuditLogFilters): Promise<AuditLogEntry[]> {
    try {
      const params = new URLSearchParams();

      if (filters?.source) {
        params.append("source", filters.source);
      }
      if (filters?.risk_level) {
        params.append("risk_level", filters.risk_level);
      }
      if (filters?.limit) {
        params.append("limit", String(filters.limit));
      }

      const queryString = params.toString();
      const url = queryString ? `/api/audit?${queryString}` : "/api/audit";

      const response = await callAPIWithETag<AuditLogListResponse>(url);
      return response.events || [];
    } catch (error) {
      console.error("Failed to list audit log:", error);
      throw error;
    }
  },
};
