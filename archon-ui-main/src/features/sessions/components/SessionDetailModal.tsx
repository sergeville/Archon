/**
 * SessionDetailModal Component
 *
 * Full detail view of a session with event timeline, AI summary, and actions.
 * Displays complete session history with event cards.
 */

import { format, formatDistanceToNow } from "date-fns";
import { Activity, Calendar, CheckCircle2, Clock, Loader2, Sparkles, User, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { cn } from "@/features/ui/primitives/styles";
import { useEndSession, useSession, useSessionEvents, useSummarizeSession } from "../hooks/useSessionQueries";
import { SessionEventCard } from "./SessionEventCard";
import { SessionSummaryPanel } from "./SessionSummaryPanel";

interface SessionDetailModalProps {
  sessionId: string;
  onClose: () => void;
}

export function SessionDetailModal({ sessionId, onClose }: SessionDetailModalProps) {
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);

  const { data: session, isLoading, error } = useSession(sessionId);
  const { data: events = [], isLoading: eventsLoading } = useSessionEvents(sessionId);
  const endSessionMutation = useEndSession();
  const summarizeMutation = useSummarizeSession();

  const isActive = session && !session.ended_at;
  const duration = session
    ? session.ended_at
      ? new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()
      : Date.now() - new Date(session.started_at).getTime()
    : 0;

  const durationMinutes = Math.floor(duration / (1000 * 60));
  const durationHours = Math.floor(durationMinutes / 60);
  const remainingMinutes = durationMinutes % 60;
  const durationText = durationHours > 0 ? `${durationHours}h ${remainingMinutes}m` : `${durationMinutes}m`;

  const getAgentColor = (agent: string) => {
    switch (agent) {
      case "claude":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "gemini":
        return "bg-purple-500/20 text-purple-400 border-purple-500/30";
      case "gpt":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "user":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const handleEndSession = async () => {
    if (!session) return;
    try {
      await endSessionMutation.mutateAsync({
        sessionId: session.id,
        data: {},
      });
    } catch (error) {
      console.error("Failed to end session:", error);
    }
  };

  const handleGenerateSummary = async () => {
    if (!session) return;
    setIsGeneratingSummary(true);
    try {
      await summarizeMutation.mutateAsync(session.id);
    } catch (error) {
      console.error("Failed to generate summary:", error);
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="max-w-md w-full p-6 bg-gray-900 border-gray-700">
          <div className="text-center">
            <p className="text-red-400">Failed to load session</p>
            <p className="text-gray-500 text-sm mt-2">{(error as Error).message}</p>
            <Button onClick={onClose} className="mt-4" variant="outline">
              Close
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading || !session) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="max-w-md w-full p-6 bg-gray-900 border-gray-700">
          <div className="text-center">
            <Activity className="h-8 w-8 text-cyan-400 animate-pulse mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Loading session...</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="my-8 w-full max-w-4xl">
        <Card className="bg-gray-900 border-gray-700">
          {/* Header */}
          <div className="sticky top-0 z-10 bg-gray-900 border-b border-gray-700 px-6 py-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-3">
                {/* Status and Agent */}
                <div className="flex items-center gap-3 flex-wrap">
                  {isActive ? (
                    <Activity className="h-5 w-5 text-cyan-400 animate-pulse" />
                  ) : (
                    <CheckCircle2 className="h-5 w-5 text-gray-500" />
                  )}
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
                      getAgentColor(session.agent),
                    )}
                  >
                    <User className="h-3 w-3" />
                    {session.agent}
                  </span>
                  {isActive && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                      Active Session
                    </span>
                  )}
                  <span className="text-xs text-gray-500 font-mono">#{sessionId.slice(0, 8)}</span>
                </div>

                {/* Metadata */}
                <div className="flex items-center gap-4 text-xs text-gray-400 flex-wrap">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    Started {formatDistanceToNow(new Date(session.started_at), { addSuffix: true })}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Duration: {durationText}
                  </div>
                  {session.ended_at && (
                    <div className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Ended {format(new Date(session.ended_at), "MMM d, yyyy h:mm a")}
                    </div>
                  )}
                </div>
              </div>

              {/* Close Button */}
              <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-4">
              {isActive && (
                <Button onClick={handleEndSession} variant="outline" size="sm" disabled={endSessionMutation.isPending}>
                  {endSessionMutation.isPending ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
                      Ending...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="h-3 w-3 mr-1.5" />
                      End Session
                    </>
                  )}
                </Button>
              )}
              {!session.summary && (
                <Button
                  onClick={handleGenerateSummary}
                  variant="outline"
                  size="sm"
                  disabled={isGeneratingSummary || summarizeMutation.isPending}
                >
                  {isGeneratingSummary || summarizeMutation.isPending ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3 w-3 mr-1.5" />
                      Generate AI Summary
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* AI Summary Panel */}
            {session.summary && <SessionSummaryPanel summary={session.summary} metadata={session.metadata} />}

            {/* Event Timeline */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Event Timeline</h3>
                <span className="text-xs text-gray-400">
                  {events.length} {events.length === 1 ? "event" : "events"}
                </span>
              </div>

              {eventsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Activity className="h-6 w-6 text-cyan-400 animate-pulse" />
                </div>
              ) : events.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-400 text-sm">No events logged yet</p>
                  <p className="text-gray-500 text-xs mt-1">Events will appear here as the session progresses</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {events.map((event, index) => (
                    <SessionEventCard
                      key={event.id}
                      event={event}
                      isFirst={index === 0}
                      isLast={index === events.length - 1}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
