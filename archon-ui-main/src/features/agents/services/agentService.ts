import { callAPIWithETag } from "../../shared/api/apiClient";
import type { Agent, AgentResponse, AgentStatus, AgentsListResponse, RegisterAgentRequest } from "../types";

export const agentService = {
  async listAgents(status?: AgentStatus): Promise<Agent[]> {
    try {
      const url = status ? `/api/agents?status=${status}` : "/api/agents";
      const response = await callAPIWithETag<AgentsListResponse>(url);
      return response.agents || [];
    } catch (error) {
      console.error("Failed to list agents:", error);
      throw error;
    }
  },

  async getAgent(name: string): Promise<Agent> {
    try {
      const response = await callAPIWithETag<AgentResponse>(`/api/agents/${name}`);
      return response.agent;
    } catch (error) {
      console.error(`Failed to get agent ${name}:`, error);
      throw error;
    }
  },

  async registerAgent(data: RegisterAgentRequest): Promise<AgentResponse> {
    try {
      const response = await callAPIWithETag<AgentResponse>("/api/agents/register", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return response;
    } catch (error) {
      console.error("Failed to register agent:", error);
      throw error;
    }
  },

  async heartbeat(name: string): Promise<AgentResponse> {
    try {
      const response = await callAPIWithETag<AgentResponse>(`/api/agents/${name}/heartbeat`, {
        method: "POST",
      });
      return response;
    } catch (error) {
      console.error(`Failed to send heartbeat for agent ${name}:`, error);
      throw error;
    }
  },

  async deactivateAgent(name: string): Promise<AgentResponse> {
    try {
      const response = await callAPIWithETag<AgentResponse>(`/api/agents/${name}/deactivate`, {
        method: "POST",
      });
      return response;
    } catch (error) {
      console.error(`Failed to deactivate agent ${name}:`, error);
      throw error;
    }
  },
};
