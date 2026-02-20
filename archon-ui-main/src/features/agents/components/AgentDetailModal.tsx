import { format, formatDistanceToNow } from "date-fns";
import { Activity, Calendar, Heart, Loader2, PowerOff, Tag, Users, X } from "lucide-react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { cn } from "@/features/ui/primitives/styles";
import { useAgent, useDeactivateAgent, useHeartbeat } from "../hooks/useAgentQueries";

interface AgentDetailModalProps {
  agentName: string;
  onClose: () => void;
}

function getStatusStyle(status: string): string {
  switch (status) {
    case "active":
      return "bg-green-500/20 text-green-400 border-green-500/30";
    case "busy":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "inactive":
      return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    default:
      return "bg-gray-500/20 text-gray-400 border-gray-500/30";
  }
}

export function AgentDetailModal({ agentName, onClose }: AgentDetailModalProps) {
  const { data: agent, isLoading, error } = useAgent(agentName);
  const heartbeatMutation = useHeartbeat();
  const deactivateMutation = useDeactivateAgent();

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="max-w-md w-full p-6 bg-gray-900 border-gray-700">
          <div className="text-center">
            <p className="text-red-400">Failed to load agent</p>
            <p className="text-gray-500 text-sm mt-2">{(error as Error).message}</p>
            <Button onClick={onClose} className="mt-4" variant="outline">
              Close
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading || !agent) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="max-w-md w-full p-6 bg-gray-900 border-gray-700">
          <div className="text-center">
            <Activity className="h-8 w-8 text-cyan-400 animate-pulse mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Loading agent...</p>
          </div>
        </Card>
      </div>
    );
  }

  const hasMetadata = Object.keys(agent.metadata).length > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="my-8 w-full max-w-2xl">
        <Card className="bg-gray-900 border-gray-700">
          {/* Header */}
          <div className="sticky top-0 z-10 bg-gray-900 border-b border-gray-700 px-6 py-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3 flex-wrap">
                <Users className="h-5 w-5 text-cyan-400" />
                <span className="text-lg font-semibold text-white">{agent.name}</span>
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
                    getStatusStyle(agent.status),
                  )}
                >
                  {agent.status}
                </span>
              </div>
              <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => heartbeatMutation.mutate(agent.name)}
                disabled={heartbeatMutation.isPending}
              >
                {heartbeatMutation.isPending ? (
                  <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
                ) : (
                  <Heart className="h-3 w-3 mr-1.5 text-green-400" />
                )}
                Heartbeat
              </Button>
              {agent.status !== "inactive" && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => deactivateMutation.mutate(agent.name)}
                  disabled={deactivateMutation.isPending}
                  className="text-red-400 hover:text-red-300 border-red-500/30"
                >
                  {deactivateMutation.isPending ? (
                    <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
                  ) : (
                    <PowerOff className="h-3 w-3 mr-1.5" />
                  )}
                  Deactivate
                </Button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Timestamps */}
            <div className="flex items-center gap-6 text-xs text-gray-400">
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                Created {format(new Date(agent.created_at), "MMM d, yyyy h:mm a")}
              </div>
              <div className="flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5" />
                Last seen {formatDistanceToNow(new Date(agent.last_seen), { addSuffix: true })}
              </div>
            </div>

            {/* Capabilities */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Tag className="h-4 w-4 text-cyan-400" />
                Capabilities
              </h3>
              {agent.capabilities.length === 0 ? (
                <p className="text-sm text-gray-500">No capabilities registered</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="inline-flex items-center px-2.5 py-1 rounded text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Metadata */}
            {hasMetadata && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-white">Metadata</h3>
                <pre className="text-xs text-gray-300 bg-gray-800/50 border border-gray-700 rounded p-3 overflow-x-auto">
                  {JSON.stringify(agent.metadata, null, 2)}
                </pre>
              </div>
            )}

            {/* Agent ID */}
            <p className="text-xs text-gray-600 font-mono">ID: {agent.id}</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
