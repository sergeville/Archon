/**
 * Session Feature Types
 *
 * Type definitions for agent sessions and session events.
 * Sessions represent continuous work periods by agents.
 */

/**
 * Agent identifiers in the system
 */
export type AgentType = "claude" | "gemini" | "gpt" | "user";

/**
 * Core Session type representing an agent work session
 */
export interface Session {
  id: string;
  agent: AgentType;
  project_id: string | null;
  started_at: string;
  ended_at: string | null;
  summary: string | null;
  context: Record<string, unknown>;
  metadata: SessionMetadata;
  created_at: string;
  updated_at: string;
  embedding: number[] | null;
}

/**
 * Extended metadata for sessions, including AI-generated summary data
 */
export interface SessionMetadata {
  ai_summary?: {
    key_events: string[];
    decisions: string[];
    outcomes: string[];
    next_steps: string[];
    summarized_at: string;
  };
  [key: string]: unknown;
}

/**
 * Session event representing an action within a session
 */
export interface SessionEvent {
  id: string;
  session_id: string;
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
}

/**
 * Request payload for creating a new session
 */
export interface CreateSessionRequest {
  agent: AgentType;
  project_id?: string | null;
  context?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

/**
 * Request payload for updating a session
 */
export interface UpdateSessionRequest {
  summary?: string | null;
  context?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

/**
 * Request payload for ending a session
 */
export interface EndSessionRequest {
  summary?: string | null;
  metadata?: Record<string, unknown>;
}

/**
 * Request payload for logging an event to a session
 */
export interface LogEventRequest {
  session_id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

/**
 * Request payload for semantic search across sessions
 */
export interface SearchSessionsRequest {
  query: string;
  limit?: number;
  threshold?: number;
}

/**
 * Response from session creation
 */
export interface CreateSessionResponse {
  message: string;
  session: Session;
}

/**
 * Response from session update
 */
export interface UpdateSessionResponse {
  message: string;
  session: Session;
}

/**
 * Response from session end
 */
export interface EndSessionResponse {
  message: string;
  session: Session;
}

/**
 * Response from event logging
 */
export interface LogEventResponse {
  message: string;
  event: SessionEvent;
}

/**
 * Response from session search
 */
export interface SearchSessionsResponse {
  query: string;
  results: Session[];
  count: number;
}

/**
 * Response from unified memory search (across sessions, tasks, projects)
 */
export interface MemorySearchResult {
  type: "session" | "task" | "project";
  id: string;
  title: string;
  description: string | null;
  similarity: number;
  created_at: string;
  metadata: Record<string, unknown>;
}

/**
 * Response from unified memory search
 */
export interface UnifiedMemorySearchResponse {
  query: string;
  results: MemorySearchResult[];
  count: number;
}

/**
 * Response from session summarization
 */
export interface SummarizeSessionResponse {
  session_id: string;
  summary: string;
  message: string;
}

/**
 * Options for filtering sessions
 */
export interface SessionFilterOptions {
  agent?: AgentType;
  project_id?: string;
  timeframe?: "24h" | "7days" | "30days" | "all";
  has_summary?: boolean;
}

/**
 * Session with computed properties for UI display
 */
export interface SessionWithComputedProps extends Session {
  duration_minutes: number | null;
  event_count: number;
  is_active: boolean;
}
