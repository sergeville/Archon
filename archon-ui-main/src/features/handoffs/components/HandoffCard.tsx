import { formatDistanceToNow } from "date-fns";
import { ArrowRight, CheckCircle2, Loader2, XCircle } from "lucide-react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { cn } from "@/features/ui/primitives/styles";
import { useAcceptHandoff, useCompleteHandoff, useRejectHandoff } from "../hooks/useHandoffQueries";
import type { Handoff, HandoffStatus } from "../types";

interface HandoffCardProps {
  handoff: Handoff;
  onClick?: () => void;
}

function getStatusStyle(status: HandoffStatus): string {
  switch (status) {
    case "pending":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "accepted":
      return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    case "completed":
      return "bg-green-500/20 text-green-400 border-green-500/30";
    case "rejected":
      return "bg-red-500/20 text-red-400 border-red-500/30";
    default:
      return "bg-gray-500/20 text-gray-400 border-gray-500/30";
  }
}

export function HandoffCard({ handoff, onClick }: HandoffCardProps) {
  const acceptMutation = useAcceptHandoff();
  const completeMutation = useCompleteHandoff();
  const rejectMutation = useRejectHandoff();

  const handleAccept = (e: React.MouseEvent) => {
    e.stopPropagation();
    acceptMutation.mutate(handoff.id);
  };

  const handleComplete = (e: React.MouseEvent) => {
    e.stopPropagation();
    completeMutation.mutate(handoff.id);
  };

  const handleReject = (e: React.MouseEvent) => {
    e.stopPropagation();
    rejectMutation.mutate(handoff.id);
  };

  const isMutating = acceptMutation.isPending || completeMutation.isPending || rejectMutation.isPending;

  return (
    <Card
      className={cn(
        "p-4 cursor-pointer transition-all hover:border-cyan-500/50",
        handoff.status === "pending" && "border-yellow-500/30 bg-yellow-500/5",
        handoff.status === "accepted" && "border-blue-500/30 bg-blue-500/5",
        handoff.status === "completed" && "border-green-500/30 bg-green-500/5",
        handoff.status === "rejected" && "border-red-500/20",
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          {/* Status badge + agents */}
          <div className="flex items-center gap-3 flex-wrap">
            <span
              className={cn(
                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
                getStatusStyle(handoff.status),
              )}
            >
              {handoff.status}
            </span>
            <div className="flex items-center gap-1.5 text-sm">
              <span className="text-gray-300 font-medium">{handoff.from_agent}</span>
              <ArrowRight className="h-3.5 w-3.5 text-gray-500" />
              <span className="text-gray-300 font-medium">{handoff.to_agent}</span>
            </div>
          </div>

          {/* Session link */}
          <p className="text-xs text-gray-500 font-mono">Session: {handoff.session_id.slice(0, 8)}…</p>

          {/* Notes */}
          {handoff.notes && <p className="text-sm text-gray-400 line-clamp-2">{handoff.notes}</p>}

          {/* Created at */}
          <p className="text-xs text-gray-600">
            {formatDistanceToNow(new Date(handoff.created_at), { addSuffix: true })}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-1.5 shrink-0">
          {handoff.status === "pending" && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleAccept}
                disabled={isMutating}
                className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 h-7 px-2 text-xs"
              >
                {acceptMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "Accept"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReject}
                disabled={isMutating}
                className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-7 px-2 text-xs"
              >
                {rejectMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "Reject"}
              </Button>
            </>
          )}
          {handoff.status === "accepted" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleComplete}
              disabled={isMutating}
              className="text-green-400 hover:text-green-300 hover:bg-green-500/10 h-7 px-2 text-xs"
            >
              {completeMutation.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <>
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Complete
                </>
              )}
            </Button>
          )}
          {(handoff.status === "completed" || handoff.status === "rejected") && (
            <div className="flex items-center justify-center h-7 w-7">
              {handoff.status === "completed" ? (
                <CheckCircle2 className="h-4 w-4 text-green-400" />
              ) : (
                <XCircle className="h-4 w-4 text-red-400" />
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
