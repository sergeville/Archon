/**
 * Whiteboard Query Hooks
 *
 * TanStack Query hooks for whiteboard data (active sessions, tasks, events).
 */

import { useQuery } from "@tanstack/react-query";
import { whiteboardService } from "../services/whiteboardService";
import { STALE_TIMES } from "@/features/shared/config/queryPatterns";

/**
 * Query key factory for whiteboard data
 */
export const whiteboardKeys = {
  all: ["whiteboard"] as const,
  whiteboard: () => [...whiteboardKeys.all, "full"] as const,
  sessions: () => [...whiteboardKeys.all, "sessions"] as const,
  tasks: () => [...whiteboardKeys.all, "tasks"] as const,
  events: (limit?: number) =>
    [...whiteboardKeys.all, "events", limit] as const,
};

/**
 * Get complete whiteboard data
 */
export function useWhiteboard() {
  return useQuery({
    queryKey: whiteboardKeys.whiteboard(),
    queryFn: () => whiteboardService.getWhiteboard(),
    staleTime: STALE_TIMES.frequent,
    refetchInterval: 5000, // Refresh every 5 seconds for real-time updates
  });
}

/**
 * Get active sessions
 */
export function useActiveSessions() {
  return useQuery({
    queryKey: whiteboardKeys.sessions(),
    queryFn: () => whiteboardService.getActiveSessions(),
    staleTime: STALE_TIMES.frequent,
    refetchInterval: 5000,
  });
}

/**
 * Get active tasks
 */
export function useActiveTasks() {
  return useQuery({
    queryKey: whiteboardKeys.tasks(),
    queryFn: () => whiteboardService.getActiveTasks(),
    staleTime: STALE_TIMES.frequent,
    refetchInterval: 5000,
  });
}

/**
 * Get recent events
 * @param limit - Maximum number of events to return
 */
export function useRecentEvents(limit = 20) {
  return useQuery({
    queryKey: whiteboardKeys.events(limit),
    queryFn: () => whiteboardService.getRecentEvents(limit),
    staleTime: STALE_TIMES.frequent,
    refetchInterval: 5000,
  });
}

/**
 * Get all tasks for todo-list display
 * @param projectId - Optional project ID filter
 */
export function useAllTasks(projectId?: string) {
  return useQuery({
    queryKey: [...whiteboardKeys.all, "all-tasks", projectId] as const,
    queryFn: () => whiteboardService.getAllTasks(projectId),
    staleTime: STALE_TIMES.frequent,
    refetchInterval: 5000,
  });
}
