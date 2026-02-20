/**
 * Whiteboard Types
 *
 * Types for the real-time whiteboard that displays active sessions,
 * tasks, and events from AI agents.
 */

/**
 * Active session displayed on the whiteboard
 */
export interface WhiteboardSession {
  session_id: string;
  agent: string;
  project_id: string;
  started_at: string;
  current_activity?: string;
}

/**
 * Active task displayed on the whiteboard
 */
export interface WhiteboardTask {
  task_id: string;
  title: string;
  status: "todo" | "doing" | "review" | "done";
  assignee: string | null;
  project_id: string;
  updated_at: string;
}

/**
 * Event displayed in the timeline
 */
export interface WhiteboardEvent {
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

/**
 * Complete whiteboard content structure
 */
export interface WhiteboardContent {
  markdown: string;
  active_sessions?: WhiteboardSession[];
  active_tasks?: WhiteboardTask[];
  recent_events?: WhiteboardEvent[];
}

/**
 * Complete whiteboard data structure
 */
export interface Whiteboard {
  id: string;
  project_id: string;
  title: string;
  content: WhiteboardContent;
  updated_at: string;
}

/**
 * Response from whiteboard endpoints
 */
export interface WhiteboardResponse {
  whiteboard: Whiteboard;
}

export interface ActiveSessionsResponse {
  active_sessions: WhiteboardSession[];
  count: number;
}

export interface ActiveTasksResponse {
  active_tasks: WhiteboardTask[];
  count: number;
}

export interface RecentEventsResponse {
  recent_events: WhiteboardEvent[];
  count: number;
  total: number;
}
