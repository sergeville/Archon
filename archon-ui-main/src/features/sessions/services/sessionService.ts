/**
 * Session Management Service
 *
 * Service for session CRUD operations, event logging, and semantic search.
 * Sessions represent continuous work periods by agents.
 */

import { callAPIWithETag } from "../../shared/api/apiClient";
import type {
  CreateSessionRequest,
  CreateSessionResponse,
  EndSessionRequest,
  EndSessionResponse,
  LogEventRequest,
  LogEventResponse,
  SearchSessionsRequest,
  SearchSessionsResponse,
  Session,
  SessionEvent,
  SessionFilterOptions,
  SummarizeSessionResponse,
  UnifiedMemorySearchResponse,
  UpdateSessionRequest,
  UpdateSessionResponse,
} from "../types";

export const sessionService = {
  /**
   * List all sessions with optional filters
   */
  async listSessions(options?: SessionFilterOptions): Promise<Session[]> {
    try {
      const params = new URLSearchParams();

      if (options?.agent) {
        params.append("agent", options.agent);
      }
      if (options?.project_id) {
        params.append("project_id", options.project_id);
      }
      if (options?.timeframe) {
        params.append("timeframe", options.timeframe);
      }

      const queryString = params.toString();
      const url = queryString ? `/api/sessions?${queryString}` : "/api/sessions";

      const response = await callAPIWithETag<{ sessions: Session[] }>(url);
      return response.sessions || [];
    } catch (error) {
      console.error("Failed to list sessions:", error);
      throw error;
    }
  },

  /**
   * Get a specific session by ID
   */
  async getSession(sessionId: string): Promise<Session> {
    try {
      const response = await callAPIWithETag<{ session: Session }>(`/api/sessions/${sessionId}`);
      return response.session;
    } catch (error) {
      console.error(`Failed to get session ${sessionId}:`, error);
      throw error;
    }
  },

  /**
   * Get recent sessions for a specific agent
   */
  async getRecentSessions(agent: string, limit: number = 10): Promise<Session[]> {
    try {
      const response = await callAPIWithETag<{ sessions: Session[] }>(`/api/sessions/recent/${agent}?limit=${limit}`);
      return response.sessions || [];
    } catch (error) {
      console.error(`Failed to get recent sessions for ${agent}:`, error);
      throw error;
    }
  },

  /**
   * Get events for a specific session
   */
  async getSessionEvents(sessionId: string): Promise<SessionEvent[]> {
    try {
      const response = await callAPIWithETag<{ events: SessionEvent[] }>(`/api/sessions/${sessionId}/events`);
      return response.events || [];
    } catch (error) {
      console.error(`Failed to get events for session ${sessionId}:`, error);
      throw error;
    }
  },

  /**
   * Create a new session
   */
  async createSession(data: CreateSessionRequest): Promise<CreateSessionResponse> {
    try {
      const response = await callAPIWithETag<CreateSessionResponse>("/api/sessions", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return response;
    } catch (error) {
      console.error("Failed to create session:", error);
      throw error;
    }
  },

  /**
   * Update a session
   */
  async updateSession(sessionId: string, data: UpdateSessionRequest): Promise<UpdateSessionResponse> {
    try {
      const response = await callAPIWithETag<UpdateSessionResponse>(`/api/sessions/${sessionId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return response;
    } catch (error) {
      console.error(`Failed to update session ${sessionId}:`, error);
      throw error;
    }
  },

  /**
   * End a session
   */
  async endSession(sessionId: string, data?: EndSessionRequest): Promise<EndSessionResponse> {
    try {
      const response = await callAPIWithETag<EndSessionResponse>(`/api/sessions/${sessionId}/end`, {
        method: "POST",
        body: JSON.stringify(data || {}),
      });
      return response;
    } catch (error) {
      console.error(`Failed to end session ${sessionId}:`, error);
      throw error;
    }
  },

  /**
   * Log an event to a session
   */
  async logEvent(data: LogEventRequest): Promise<LogEventResponse> {
    try {
      const response = await callAPIWithETag<LogEventResponse>("/api/sessions/events", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return response;
    } catch (error) {
      console.error("Failed to log event:", error);
      throw error;
    }
  },

  /**
   * Search sessions semantically
   */
  async searchSessions(data: SearchSessionsRequest): Promise<SearchSessionsResponse> {
    try {
      const response = await callAPIWithETag<SearchSessionsResponse>("/api/sessions/search", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return response;
    } catch (error) {
      console.error("Failed to search sessions:", error);
      throw error;
    }
  },

  /**
   * Search across all memory layers (sessions, tasks, projects)
   */
  async searchAllMemory(
    query: string,
    limit: number = 20,
    threshold: number = 0.7,
  ): Promise<UnifiedMemorySearchResponse> {
    try {
      const response = await callAPIWithETag<UnifiedMemorySearchResponse>("/api/sessions/search/all", {
        method: "POST",
        body: JSON.stringify({ query, limit, threshold }),
      });
      return response;
    } catch (error) {
      console.error("Failed to search all memory:", error);
      throw error;
    }
  },

  /**
   * Generate AI summary for a session
   */
  async summarizeSession(sessionId: string): Promise<SummarizeSessionResponse> {
    try {
      const response = await callAPIWithETag<SummarizeSessionResponse>(`/api/sessions/${sessionId}/summarize`, {
        method: "POST",
      });
      return response;
    } catch (error) {
      console.error(`Failed to summarize session ${sessionId}:`, error);
      throw error;
    }
  },
};
