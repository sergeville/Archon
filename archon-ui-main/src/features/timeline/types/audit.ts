export type RiskLevel = "LOW" | "MED" | "HIGH" | "DESTRUCTIVE";

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  source: string;
  agent: string | null;
  action: string;
  target: string | null;
  risk_level: RiskLevel;
  outcome: string | null;
  metadata: Record<string, unknown>;
  session_id: string | null;
}

export interface AuditLogFilters {
  source?: string;
  risk_level?: string;
  limit?: number;
}

export interface AuditLogListResponse {
  events: AuditLogEntry[];
  count: number;
}
