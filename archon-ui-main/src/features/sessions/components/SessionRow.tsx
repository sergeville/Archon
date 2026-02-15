/**
 * SessionRow Component
 *
 * Compact one-line view of a session/task
 */

import { formatDistanceToNow } from "date-fns";
import { Clock, User, Circle } from "lucide-react";
import { cn } from "@/features/ui/primitives/styles";
import type { Session } from "../types";

interface SessionRowProps {
  session: Session;
  onClick?: () => void;
}

export function SessionRow({ session, onClick }: SessionRowProps) {
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
        return "text-blue-400";
      case "gemini":
        return "text-purple-400";
      case "gpt":
        return "text-green-400";
      case "user":
        return "text-yellow-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <div
      className={cn(
        "group flex items-center gap-3 px-4 py-2 rounded-lg border transition-all cursor-pointer",
        "hover:border-cyan-500/50 hover:bg-cyan-500/5",
        isActive
          ? "border-cyan-500/30 bg-cyan-500/5"
          : "border-gray-700/50 hover:border-gray-600"
      )}
      onClick={onClick}
    >
      {/* Status Indicator */}
      <div className="flex items-center justify-center w-5">
        {isActive ? (
          <Circle className="h-2.5 w-2.5 fill-cyan-400 text-cyan-400 animate-pulse" />
        ) : (
          <Circle className="h-2.5 w-2.5 fill-gray-600 text-gray-600" />
        )}
      </div>

      {/* Agent */}
      <div className={cn("flex items-center gap-1.5 min-w-[80px]", getAgentColor(session.agent))}>
        <User className="h-3.5 w-3.5" />
        <span className="text-xs font-medium">{session.agent}</span>
      </div>

      {/* Status Badge */}
      {!isActive && (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-gray-700/50 text-gray-400 border border-gray-600">
          CLOSED
        </span>
      )}

      {/* Task/Summary */}
      <div className="flex-1 min-w-0">
        <p className={cn(
          "text-sm truncate",
          isActive ? "text-gray-300" : "text-gray-500"
        )}>
          {session.summary || session.context?.working_on || (isActive ? "Active session" : "Session ended")}
        </p>
      </div>

      {/* Duration */}
      <div className="flex items-center gap-1.5 text-xs text-gray-500 min-w-[60px]">
        <Clock className="h-3.5 w-3.5" />
        <span className="tabular-nums">{durationText}</span>
      </div>

      {/* Timestamp */}
      <div className="text-xs text-gray-500 min-w-[80px] text-right">
        {isActive
          ? formatDistanceToNow(new Date(session.started_at), { addSuffix: true })
          : `Ended ${formatDistanceToNow(new Date(session.ended_at!), { addSuffix: true })}`}
      </div>

      {/* Session ID */}
      <div className="text-xs text-gray-600 font-mono">
        #{session.id.slice(0, 8)}
      </div>
    </div>
  );
}
