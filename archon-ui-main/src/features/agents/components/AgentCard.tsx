import { formatDistanceToNow } from "date-fns";
import { Activity, Heart, PowerOff, Tag, Users } from "lucide-react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { cn } from "@/features/ui/primitives/styles";
import { useDeactivateAgent, useHeartbeat } from "../hooks/useAgentQueries";
import type { Agent } from "../types";

interface AgentCardProps {
  agent: Agent;
  onClick?: () => void;
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

export function AgentCard({ agent, onClick }: AgentCardProps) {
  const heartbeatMutation = useHeartbeat();
  const deactivateMutation = useDeactivateAgent();

  const handleHeartbeat = (e: React.MouseEvent) => {
    e.stopPropagation();
    heartbeatMutation.mutate(agent.name);
  };

  const handleDeactivate = (e: React.MouseEvent) => {
    e.stopPropagation();
    deactivateMutation.mutate(agent.name);
  };

  return (
    <Card
      className={cn(
        "p-4 cursor-pointer transition-all hover:border-cyan-500/50",
        agent.status === "active" && "border-green-500/30 bg-green-500/5",
        agent.status === "busy" && "border-yellow-500/30 bg-yellow-500/5",
        agent.status === "inactive" && "border-gray-700/50",
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          {/* Header */}
          <div className="flex items-center gap-3 flex-wrap">
            <Users className="h-4 w-4 text-cyan-400 shrink-0" />
            <span className="text-sm font-semibold text-white">{agent.name}</span>
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border",
                getStatusStyle(agent.status),
              )}
            >
              {agent.status === "active" && <Activity className="h-2.5 w-2.5" />}
              {agent.status}
            </span>
          </div>

          {/* Capabilities */}
          {agent.capabilities.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <Tag className="h-3 w-3 text-gray-500 shrink-0" />
              {agent.capabilities.map((cap) => (
                <span
                  key={cap}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                >
                  {cap}
                </span>
              ))}
            </div>
          )}

          {/* Last seen */}
          <p className="text-xs text-gray-500">
            Last seen {formatDistanceToNow(new Date(agent.last_seen), { addSuffix: true })}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleHeartbeat}
            disabled={heartbeatMutation.isPending}
            className="text-green-400 hover:text-green-300 hover:bg-green-500/10 h-7 px-2"
          >
            <Heart className="h-3.5 w-3.5" />
          </Button>
          {agent.status !== "inactive" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDeactivate}
              disabled={deactivateMutation.isPending}
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-7 px-2"
            >
              <PowerOff className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
