/**
 * Whiteboard Service
 *
 * Handles API calls for whiteboard data (active sessions, tasks, events).
 */

import { callAPIWithETag } from "@/features/shared/api/apiClient";
import type {
  WhiteboardResponse,
  ActiveSessionsResponse,
  ActiveTasksResponse,
  RecentEventsResponse,
} from "../types/whiteboard";

/**
 * Whiteboard API service for real-time agent activity display
 */
export const whiteboardService = {
  /**
   * Get complete whiteboard data
   */
  async getWhiteboard(): Promise<WhiteboardResponse> {
    const response = await callAPIWithETag<WhiteboardResponse>("/api/whiteboard");
    return response;
  },

  /**
   * Get active sessions
   */
  async getActiveSessions(): Promise<ActiveSessionsResponse> {
    const response = await callAPIWithETag<ActiveSessionsResponse>(
      "/api/whiteboard/active-sessions",
    );
    return response;
  },

  /**
   * Get active tasks
   */
  async getActiveTasks(): Promise<ActiveTasksResponse> {
    const response = await callAPIWithETag<ActiveTasksResponse>(
      "/api/whiteboard/active-tasks",
    );
    return response;
  },

  /**
   * Get recent events
   * @param limit - Maximum number of events to return (default: 20)
   */
  async getRecentEvents(limit = 20): Promise<RecentEventsResponse> {
    const response = await callAPIWithETag<RecentEventsResponse>(
      `/api/whiteboard/recent-events?limit=${limit}`,
    );
    return response;
  },

  /**
   * Get all tasks grouped by status for todo-list display
   * @param projectId - Optional project ID filter
   */
  async getAllTasks(projectId?: string): Promise<ActiveTasksResponse> {
    const url = projectId
      ? `/api/whiteboard/all-tasks?project_id=${projectId}`
      : `/api/whiteboard/all-tasks`;
    const response = await callAPIWithETag<ActiveTasksResponse>(url);
    return response;
  },
};
