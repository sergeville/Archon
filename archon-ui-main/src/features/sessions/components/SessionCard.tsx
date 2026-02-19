/**
 * SessionCard Component
 *
 * Displays a single session with its details and associated events/tasks
 */

import { formatDistanceToNow } from "date-fns";
import { Clock, User, Calendar, Activity, CheckCircle2, Circle } from "lucide-react";
import { Card } from "@/features/ui/primitives/card";
import { cn } from "@/features/ui/primitives/styles";
import type { Session } from "../types";

interface SessionCardProps {
  session: Session;
  onClick?: () => void;
}

export function SessionCard({ session, onClick }: SessionCardProps) {
  const isActive = !session.ended_at;
  const duration = session.ended_at
    ? new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()
    : Date.now() - new Date(session.started_at).getTime();

  const durationMinutes = Math.floor(duration / (1000 * 60));
  const durationHours = Math.floor(durationMinutes / 60);
  const remainingMinutes = durationMinutes % 60;

  const durationText =
    durationHours > 0
      ? `${durationHours}h ${remainingMinutes}m`
      : `${durationMinutes}m`;

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

  return (
    <Card
      className={`p-4 cursor-pointer transition-all hover:border-cyan-500/50 ${
        isActive ? "border-cyan-500/30 bg-cyan-500/5" : "border-gray-700/50"
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          {/* Header */}
          <div className="flex items-center gap-3">
            {isActive ? (
              <Activity className="h-5 w-5 text-cyan-400 animate-pulse" />
            ) : (
              <CheckCircle2 className="h-5 w-5 text-gray-500" />
            )}
            <div className="flex items-center gap-2 flex-1">
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
                  getAgentColor(session.agent)
                )}
              >
                <User className="h-3 w-3" />
                {session.agent}
              </span>
              {isActive && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  <Circle className="h-2 w-2 fill-current" />
                  Active
                </span>
              )}
            </div>
          </div>

          {/* Summary */}
          {session.summary && (
            <p className="text-sm text-gray-300 line-clamp-2">{session.summary}</p>
          )}

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDistanceToNow(new Date(session.started_at), { addSuffix: true })}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {durationText}
            </div>
          </div>

          {/* AI Summary Key Events */}
          {session.metadata?.ai_summary?.key_events && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-400">Key Events:</p>
              <ul className="text-xs text-gray-500 space-y-0.5">
                {session.metadata.ai_summary.key_events.slice(0, 3).map((event, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-cyan-400">•</span>
                    <span className="line-clamp-1">{event}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Session ID */}
        <div className="text-xs text-gray-500 font-mono">
          #{session.id.slice(0, 8)}
        </div>
      </div>
    </Card>
  );
}
