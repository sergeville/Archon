/**
 * Session Query Hooks
 *
 * TanStack Query hooks for session management.
 * Provides queries and mutations for sessions, events, and memory search.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSmartPolling } from "@/features/shared/hooks";
import { useToast } from "@/features/shared/hooks/useToast";
import {
  createOptimisticEntity,
  replaceOptimisticEntity,
} from "@/features/shared/utils/optimistic";
import { DISABLED_QUERY_KEY, STALE_TIMES } from "../../shared/config/queryPatterns";
import { sessionService } from "../services";
import type {
  Session,
  SessionEvent,
  CreateSessionRequest,
  UpdateSessionRequest,
  EndSessionRequest,
  LogEventRequest,
  SearchSessionsRequest,
  SessionFilterOptions,
  MemorySearchResult,
} from "../types";

/**
 * Query keys factory for sessions
 */
export const sessionKeys = {
  all: ["sessions"] as const,
  lists: () => [...sessionKeys.all, "list"] as const,
  listWithFilters: (filters?: SessionFilterOptions) =>
    [...sessionKeys.all, "list", filters] as const,
  detail: (id: string) => [...sessionKeys.all, "detail", id] as const,
  events: (sessionId: string) => [...sessionKeys.all, sessionId, "events"] as const,
  recentByAgent: (agent: string, limit?: number) =>
    [...sessionKeys.all, "recent", agent, limit] as const,
  search: (query: string) => [...sessionKeys.all, "search", query] as const,
  memorySearch: (query: string) => ["memory", "search", query] as const,
};

/**
 * Fetch all sessions with optional filters
 */
export function useSessions(options?: SessionFilterOptions) {
  const { refetchInterval } = useSmartPolling(3000); // 3 second base interval

  return useQuery<Session[]>({
    queryKey: sessionKeys.listWithFilters(options),
    queryFn: () => sessionService.listSessions(options),
    refetchInterval,
    refetchOnWindowFocus: true,
    staleTime: STALE_TIMES.normal,
  });
}

/**
 * Fetch a specific session by ID
 */
export function useSession(sessionId: string | undefined) {
  return useQuery<Session>({
    queryKey: sessionId ? sessionKeys.detail(sessionId) : DISABLED_QUERY_KEY,
    queryFn: () =>
      sessionId
        ? sessionService.getSession(sessionId).then((response) => response)
        : Promise.reject("No session ID"),
    enabled: !!sessionId,
    staleTime: STALE_TIMES.normal,
  });
}

/**
 * Fetch recent sessions for a specific agent
 */
export function useRecentSessions(agent: string, limit: number = 10) {
  const { refetchInterval } = useSmartPolling(5000); // 5 second base interval

  return useQuery<Session[]>({
    queryKey: sessionKeys.recentByAgent(agent, limit),
    queryFn: () => sessionService.getRecentSessions(agent, limit),
    refetchInterval,
    staleTime: STALE_TIMES.frequent,
  });
}

/**
 * Fetch events for a specific session
 */
export function useSessionEvents(sessionId: string | undefined) {
  return useQuery<SessionEvent[]>({
    queryKey: sessionId ? sessionKeys.events(sessionId) : DISABLED_QUERY_KEY,
    queryFn: () =>
      sessionId
        ? sessionService.getSessionEvents(sessionId)
        : Promise.reject("No session ID"),
    enabled: !!sessionId,
    staleTime: STALE_TIMES.frequent,
  });
}

/**
 * Create a new session
 */
export function useCreateSession() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: CreateSessionRequest) => sessionService.createSession(data),
    onMutate: async (newData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: sessionKeys.lists() });

      // Snapshot previous value
      const previousSessions = queryClient.getQueryData<Session[]>(
        sessionKeys.lists()
      );

      // Create optimistic session
      const optimisticSession = createOptimisticEntity<Session>({
        agent: newData.agent,
        project_id: newData.project_id || null,
        started_at: new Date().toISOString(),
        ended_at: null,
        summary: null,
        context: newData.context || {},
        metadata: newData.metadata || {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        embedding: null,
      });

      // Optimistically add session
      queryClient.setQueryData(
        sessionKeys.lists(),
        (old: Session[] | undefined) => {
          if (!old) return [optimisticSession];
          return [optimisticSession, ...old];
        }
      );

      return { previousSessions, optimisticId: optimisticSession._localId };
    },
    onError: (error, _variables, context) => {
      console.error("Failed to create session:", error);

      // Rollback on error
      if (context?.previousSessions) {
        queryClient.setQueryData(sessionKeys.lists(), context.previousSessions);
      }

      showToast("Failed to create session", "error");
    },
    onSuccess: (response, _variables, context) => {
      const newSession = response.session;

      // Replace optimistic with server data
      queryClient.setQueryData(
        sessionKeys.lists(),
        (sessions: Session[] = []) => {
          return replaceOptimisticEntity(
            sessions,
            context?.optimisticId || "",
            newSession
          );
        }
      );

      showToast("Session created successfully", "success");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
    },
  });
}

/**
 * Update a session
 */
export function useUpdateSession() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: ({
      sessionId,
      updates,
    }: {
      sessionId: string;
      updates: UpdateSessionRequest;
    }) => sessionService.updateSession(sessionId, updates),
    onSuccess: (response) => {
      const updatedSession = response.session;

      // Update in list
      queryClient.setQueryData(
        sessionKeys.lists(),
        (old: Session[] | undefined) => {
          if (!old) return old;
          return old.map((s) =>
            s.id === updatedSession.id ? updatedSession : s
          );
        }
      );

      // Update detail query
      queryClient.setQueryData(
        sessionKeys.detail(updatedSession.id),
        updatedSession
      );

      showToast("Session updated successfully", "success");
    },
    onError: (error) => {
      console.error("Failed to update session:", error);
      showToast("Failed to update session", "error");
    },
  });
}

/**
 * End a session
 */
export function useEndSession() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: ({
      sessionId,
      data,
    }: {
      sessionId: string;
      data?: EndSessionRequest;
    }) => sessionService.endSession(sessionId, data),
    onSuccess: (response) => {
      const endedSession = response.session;

      // Update in list
      queryClient.setQueryData(
        sessionKeys.lists(),
        (old: Session[] | undefined) => {
          if (!old) return old;
          return old.map((s) => (s.id === endedSession.id ? endedSession : s));
        }
      );

      // Update detail query
      queryClient.setQueryData(
        sessionKeys.detail(endedSession.id),
        endedSession
      );

      showToast("Session ended successfully", "success");
    },
    onError: (error) => {
      console.error("Failed to end session:", error);
      showToast("Failed to end session", "error");
    },
  });
}

/**
 * Log an event to a session
 */
export function useLogEvent() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: LogEventRequest) => sessionService.logEvent(data),
    onSuccess: (response, variables) => {
      // Invalidate events query for this session
      queryClient.invalidateQueries({
        queryKey: sessionKeys.events(variables.session_id),
      });

      showToast("Event logged successfully", "success");
    },
    onError: (error) => {
      console.error("Failed to log event:", error);
      showToast("Failed to log event", "error");
    },
  });
}

/**
 * Search sessions semantically
 */
export function useSearchSessions() {
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (data: SearchSessionsRequest) =>
      sessionService.searchSessions(data),
    onError: (error) => {
      console.error("Failed to search sessions:", error);
      showToast("Failed to search sessions", "error");
    },
  });
}

/**
 * Search across all memory layers (sessions, tasks, projects)
 */
export function useMemorySearch() {
  const { showToast } = useToast();

  return useMutation<
    { results: MemorySearchResult[]; count: number; query: string },
    Error,
    { query: string; limit?: number; threshold?: number }
  >({
    mutationFn: ({ query, limit = 20, threshold = 0.7 }) =>
      sessionService.searchAllMemory(query, limit, threshold),
    onError: (error) => {
      console.error("Failed to search memory:", error);
      showToast("Failed to search memory", "error");
    },
  });
}

/**
 * Generate AI summary for a session
 */
export function useSummarizeSession() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (sessionId: string) =>
      sessionService.summarizeSession(sessionId),
    onSuccess: (response) => {
      // Invalidate session detail to refetch with summary
      queryClient.invalidateQueries({
        queryKey: sessionKeys.detail(response.session_id),
      });

      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });

      showToast("Session summarized successfully", "success");
    },
    onError: (error) => {
      console.error("Failed to summarize session:", error);
      showToast("Failed to summarize session", "error");
    },
  });
}
