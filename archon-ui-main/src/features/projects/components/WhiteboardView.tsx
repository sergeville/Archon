/**
 * WhiteboardView Component
 *
 * Real-time display of active AI agent sessions, tasks, and events.
 * This is the main view when users navigate to the whiteboard document.
 */

import { Activity, Bot, CheckCircle2, ListTodo, RefreshCw, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/features/ui/primitives";
import { useActiveSessions, useAllTasks, useRecentEvents } from "../hooks/useWhiteboardQueries";
import type { WhiteboardEvent, WhiteboardSession, WhiteboardTask } from "../types/whiteboard";

/**
 * Formats a timestamp to a relative time string
 */
function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

/**
 * Formats duration for active tasks (e.g., "4m 3s")
 */
function formatDuration(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);

  const secs = diffSecs % 60;
  const mins = diffMins % 60;

  if (diffHours > 0) {
    return `${diffHours}h ${mins}m`;
  }
  if (diffMins > 0) {
    return `${diffMins}m ${secs}s`;
  }
  return `${diffSecs}s`;
}

/**
 * Hook to trigger re-render every second for live timer updates
 */
function useLiveTimer(enabled: boolean) {
  const [, setTick] = useState(0);

  useEffect(() => {
    if (!enabled) return;

    const interval = setInterval(() => {
      setTick((tick) => tick + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [enabled]);
}

/**
 * SessionCard - Displays an active AI agent session
 */
function SessionCard({ session }: { session: WhiteboardSession }) {
  return (
    <div className="group relative overflow-hidden rounded-lg border border-cyan-500/30 bg-gradient-to-br from-cyan-500/5 via-transparent to-purple-500/5 p-4 backdrop-blur-sm transition-all hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/10">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500/20 flex-shrink-0">
          <Bot className="h-5 w-5 text-cyan-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-gray-900 dark:text-white truncate">{session.agent}</h4>
          {session.current_activity && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 truncate">{session.current_activity}</p>
          )}
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">{formatRelativeTime(session.started_at)}</p>
        </div>
        <div className="flex h-2 w-2 flex-shrink-0">
          <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-cyan-400 opacity-75"></span>
          <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-500"></span>
        </div>
      </div>
    </div>
  );
}

/**
 * TaskCard - Displays a task in todo-list format
 */
function TaskCard({ task }: { task: WhiteboardTask }) {
  // Enable live timer for active tasks
  useLiveTimer(task.status === "doing");

  const statusIcons = {
    todo: "☐",
    doing: "🟢",
    review: "🔍",
    done: "✅",
  };

  const statusColors = {
    todo: "text-gray-500 dark:text-gray-400",
    doing: "text-cyan-400 font-semibold",
    review: "text-purple-400 font-semibold",
    done: "text-green-400 line-through opacity-70",
  };

  const icon = statusIcons[task.status];
  const colorClass = statusColors[task.status];

  return (
    <div
      className={`flex items-start gap-3 py-2 px-3 rounded-lg transition-all ${
        task.status === "doing" ? "bg-cyan-500/10 border border-cyan-500/30" : "hover:bg-gray-500/5"
      }`}
    >
      <span className="text-lg flex-shrink-0 mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <p className={`text-sm ${colorClass} flex-1`}>{task.title}</p>
          {task.status === "doing" && task.updated_at && (
            <span className="text-xs text-cyan-400/80 flex-shrink-0">{formatDuration(task.updated_at)}</span>
          )}
        </div>
        {task.assignee && task.status === "doing" && <p className="text-xs text-cyan-400/60 mt-1">{task.assignee}</p>}
      </div>
    </div>
  );
}

/**
 * EventCard - Displays a recent event in the timeline
 */
function EventCard({ event }: { event: WhiteboardEvent }) {
  const eventTypeIcon = {
    task: ListTodo,
    session: Bot,
    system: Zap,
    default: Activity,
  };

  // Determine icon based on event_type prefix
  const getIcon = () => {
    if (event.event_type.startsWith("task.")) return eventTypeIcon.task;
    if (event.event_type.startsWith("session.")) return eventTypeIcon.session;
    return eventTypeIcon.default;
  };

  const Icon = getIcon();
  const entityId = event.data?.entity_id as string | undefined;
  const agent = event.data?.agent as string | undefined;

  return (
    <div className="group relative overflow-hidden rounded-lg border border-orange-500/30 bg-gradient-to-br from-orange-500/5 via-transparent to-yellow-500/5 p-4 backdrop-blur-sm transition-all hover:border-orange-500/50 hover:shadow-lg hover:shadow-orange-500/10">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-500/20 flex-shrink-0">
          <Icon className="h-4 w-4 text-orange-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {event.event_type.replace(/\./g, " ")}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">{formatRelativeTime(event.timestamp)}</span>
          </div>
          {(agent || entityId) && (
            <p className="mt-1 text-xs text-gray-600 dark:text-gray-400 truncate">
              {agent && <span>{agent}</span>}
              {agent && entityId && <span> · </span>}
              {entityId && <span>{entityId}</span>}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * WhiteboardView - Main component for real-time agent activity display
 */
export function WhiteboardView() {
  const { data: sessionsData, isLoading: loadingSessions, refetch: refetchSessions } = useActiveSessions();
  const { data: tasksData, isLoading: loadingTasks, refetch: refetchTasks } = useAllTasks();
  const { data: eventsData, isLoading: loadingEvents, refetch: refetchEvents } = useRecentEvents(20);

  const sessions = sessionsData?.active_sessions || [];
  const tasks = tasksData?.tasks || [];
  const events = eventsData?.recent_events || [];

  const isLoading = loadingSessions || loadingTasks || loadingEvents;

  const handleRefresh = () => {
    refetchSessions();
    refetchTasks();
    refetchEvents();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading whiteboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20">
            <Activity className="h-6 w-6 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Live Agent Activity</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Real-time updates from AI agents</p>
          </div>
        </div>
        <Button onClick={handleRefresh} variant="outline" size="sm" className="gap-2" disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Main Content - Task List */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center gap-2">
            <ListTodo className="h-5 w-5 text-cyan-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Task Progress</h3>
            <span className="ml-auto rounded-full bg-cyan-500/20 px-2 py-1 text-xs font-medium text-cyan-400">
              {tasks.length}
            </span>
          </div>

          {/* Todo List Display */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm p-4">
            {tasks.length === 0 ? (
              <div className="py-12 text-center">
                <ListTodo className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600 mb-3" />
                <p className="text-sm text-gray-600 dark:text-gray-400">No tasks found</p>
              </div>
            ) : (
              <div className="space-y-1">
                {tasks.map((task) => (
                  <TaskCard key={task.task_id} task={task} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Side Panel - Sessions & Events */}
        <div className="lg:col-span-1 space-y-6">
          {/* Active Sessions */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-purple-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Active Sessions</h3>
              <span className="ml-auto rounded-full bg-purple-500/20 px-2 py-1 text-xs font-medium text-purple-400">
                {sessions.length}
              </span>
            </div>
            <div className="space-y-2">
              {sessions.length === 0 ? (
                <div className="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 p-6 text-center">
                  <Bot className="mx-auto h-8 w-8 text-gray-400 dark:text-gray-600 mb-2" />
                  <p className="text-xs text-gray-600 dark:text-gray-400">No active sessions</p>
                </div>
              ) : (
                sessions.map((session) => <SessionCard key={session.session_id} session={session} />)
              )}
            </div>
          </div>

          {/* Recent Events */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-orange-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Events</h3>
              <span className="ml-auto rounded-full bg-orange-500/20 px-2 py-1 text-xs font-medium text-orange-400">
                {events.length}
              </span>
            </div>
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
              {events.length === 0 ? (
                <div className="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 p-6 text-center">
                  <Activity className="mx-auto h-8 w-8 text-gray-400 dark:text-gray-600 mb-2" />
                  <p className="text-xs text-gray-600 dark:text-gray-400">No recent events</p>
                </div>
              ) : (
                events.map((event, idx) => <EventCard key={`${event.timestamp}-${idx}`} event={event} />)
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
