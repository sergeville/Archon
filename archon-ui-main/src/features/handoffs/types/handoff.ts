export type HandoffStatus = "pending" | "accepted" | "completed" | "rejected";

export interface Handoff {
  id: string;
  session_id: string;
  from_agent: string;
  to_agent: string;
  context: Record<string, unknown>;
  notes?: string | null;
  status: HandoffStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  accepted_at?: string | null;
  completed_at?: string | null;
}

export interface CreateHandoffRequest {
  session_id: string;
  from_agent: string;
  to_agent: string;
  context?: Record<string, unknown>;
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface HandoffsListResponse {
  success: boolean;
  handoffs: Handoff[];
  count: number;
}

export interface HandoffFilterParams {
  session_id?: string;
  agent?: string;
  status?: HandoffStatus;
}
