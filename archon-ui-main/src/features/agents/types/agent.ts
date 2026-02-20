export type AgentStatus = "active" | "inactive" | "busy";

export interface Agent {
  id: string;
  name: string;
  capabilities: string[];
  status: AgentStatus;
  last_seen: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface RegisterAgentRequest {
  name: string;
  capabilities?: string[];
  metadata?: Record<string, unknown>;
}

export interface AgentResponse {
  success: boolean;
  agent: Agent;
}

export interface AgentsListResponse {
  success: boolean;
  agents: Agent[];
  count: number;
}
