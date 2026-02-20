import { format, formatDistanceToNow } from "date-fns";
import { ArrowRight, ArrowRightLeft, Calendar, CheckCircle2, Loader2, X, XCircle } from "lucide-react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { cn } from "@/features/ui/primitives/styles";
import { useAcceptHandoff, useCompleteHandoff, useHandoff, useRejectHandoff } from "../hooks/useHandoffQueries";
import type { HandoffStatus } from "../types";

interface HandoffDetailModalProps {
  handoffId: string;
  onClose: () => void;
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

export function HandoffDetailModal({ handoffId, onClose }: HandoffDetailModalProps) {
  const { data: handoff, isLoading, error } = useHandoff(handoffId);
  const acceptMutation = useAcceptHandoff();
  const completeMutation = useCompleteHandoff();
  const rejectMutation = useRejectHandoff();

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="max-w-md w-full p-6 bg-gray-900 border-gray-700">
          <div className="text-center">
            <p className="text-red-400">Failed to load handoff</p>
            <p className="text-gray-500 text-sm mt-2">{(error as Error).message}</p>
            <Button onClick={onClose} className="mt-4" variant="outline">
              Close
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading || !handoff) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="max-w-md w-full p-6 bg-gray-900 border-gray-700">
          <div className="text-center">
            <ArrowRightLeft className="h-8 w-8 text-cyan-400 animate-pulse mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Loading handoff...</p>
          </div>
        </Card>
      </div>
    );
  }

  const isMutating = acceptMutation.isPending || completeMutation.isPending || rejectMutation.isPending;
  const hasContext = Object.keys(handoff.context).length > 0;
  const hasMetadata = Object.keys(handoff.metadata).length > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="my-8 w-full max-w-2xl">
        <Card className="bg-gray-900 border-gray-700">
          {/* Header */}
          <div className="sticky top-0 z-10 bg-gray-900 border-b border-gray-700 px-6 py-4">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-3 flex-wrap">
                  <ArrowRightLeft className="h-5 w-5 text-cyan-400" />
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-white font-medium">{handoff.from_agent}</span>
                    <ArrowRight className="h-4 w-4 text-gray-400" />
                    <span className="text-white font-medium">{handoff.to_agent}</span>
                  </div>
                  <span
                    className={cn(
                      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
                      getStatusStyle(handoff.status),
                    )}
                  >
                    {handoff.status}
                  </span>
                </div>
                <p className="text-xs text-gray-500 font-mono">Session: {handoff.session_id}</p>
              </div>
              <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-4">
              {handoff.status === "pending" && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => acceptMutation.mutate(handoff.id)}
                    disabled={isMutating}
                    className="text-blue-400 border-blue-500/30"
                  >
                    {acceptMutation.isPending ? <Loader2 className="h-3 w-3 mr-1.5 animate-spin" /> : null}
                    Accept
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => rejectMutation.mutate(handoff.id)}
                    disabled={isMutating}
                    className="text-red-400 border-red-500/30"
                  >
                    {rejectMutation.isPending ? <Loader2 className="h-3 w-3 mr-1.5 animate-spin" /> : null}
                    Reject
                  </Button>
                </>
              )}
              {handoff.status === "accepted" && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => completeMutation.mutate(handoff.id)}
                  disabled={isMutating}
                  className="text-green-400 border-green-500/30"
                >
                  {completeMutation.isPending ? (
                    <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-3 w-3 mr-1.5" />
                  )}
                  Complete
                </Button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Timeline */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-white">Timeline</h3>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <Calendar className="h-3 w-3" />
                  Created {format(new Date(handoff.created_at), "MMM d, yyyy h:mm a")}
                  <span className="text-gray-600">
                    ({formatDistanceToNow(new Date(handoff.created_at), { addSuffix: true })})
                  </span>
                </div>
                {handoff.accepted_at && (
                  <div className="flex items-center gap-2 text-xs text-blue-400">
                    <ArrowRight className="h-3 w-3" />
                    Accepted {format(new Date(handoff.accepted_at), "MMM d, yyyy h:mm a")}
                  </div>
                )}
                {handoff.completed_at && (
                  <div className="flex items-center gap-2 text-xs text-green-400">
                    <CheckCircle2 className="h-3 w-3" />
                    Completed {format(new Date(handoff.completed_at), "MMM d, yyyy h:mm a")}
                  </div>
                )}
                {handoff.status === "rejected" && (
                  <div className="flex items-center gap-2 text-xs text-red-400">
                    <XCircle className="h-3 w-3" />
                    Rejected
                  </div>
                )}
              </div>
            </div>

            {/* Notes */}
            {handoff.notes && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-white">Notes</h3>
                <p className="text-sm text-gray-300 bg-gray-800/50 border border-gray-700 rounded p-3">
                  {handoff.notes}
                </p>
              </div>
            )}

            {/* Context */}
            {hasContext && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-white">Context</h3>
                <pre className="text-xs text-gray-300 bg-gray-800/50 border border-gray-700 rounded p-3 overflow-x-auto">
                  {JSON.stringify(handoff.context, null, 2)}
                </pre>
              </div>
            )}

            {/* Metadata */}
            {hasMetadata && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-white">Metadata</h3>
                <pre className="text-xs text-gray-300 bg-gray-800/50 border border-gray-700 rounded p-3 overflow-x-auto">
                  {JSON.stringify(handoff.metadata, null, 2)}
                </pre>
              </div>
            )}

            <p className="text-xs text-gray-600 font-mono">ID: {handoff.id}</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
