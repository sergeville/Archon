import { Bot, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RealTimeStats } from "@/features/agent-work-orders/components/RealTimeStats";
import { TerminalStream } from "@/features/agent-work-orders/components/TerminalStream";
import { useWorkOrder } from "@/features/agent-work-orders/hooks/useAgentWorkOrderQueries";
import { Button } from "@/features/ui/primitives/button";

interface AgentActivityPanelProps {
  workOrderId: string;
  onBackToProject: () => void;
}

export function AgentActivityPanel({ workOrderId, onBackToProject }: AgentActivityPanelProps) {
  const navigate = useNavigate();
  const { data: workOrder, isLoading, isError } = useWorkOrder(workOrderId);
  const isTerminal = workOrder?.status === "completed" || workOrder?.status === "failed";
  const [terminalOpen, setTerminalOpen] = useState(true);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 text-sm text-gray-500 dark:text-gray-400">
        <span className="w-4 h-4 border-2 border-gray-300 dark:border-gray-600 border-t-teal-500 rounded-full animate-spin mr-2" />
        Loading agent activity…
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 rounded-lg border border-red-400/30 bg-red-500/10 text-sm text-red-600 dark:text-red-400">
        Failed to load work order. Check that the Agent Work Orders service is running.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <RealTimeStats workOrderId={workOrderId} />

      {/* Terminal Output collapsible section */}
      <div className="border border-white/10 dark:border-gray-700/30 rounded-lg overflow-hidden">
        <button
          type="button"
          onClick={() => setTerminalOpen((prev) => !prev)}
          className="w-full flex items-center justify-between px-4 py-2 bg-gray-900/50 dark:bg-gray-800/30 text-sm font-semibold text-gray-300 hover:bg-gray-800/50 transition-colors"
        >
          <span>Terminal Output</span>
          {terminalOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {terminalOpen && (
          <div className="p-2">
            <TerminalStream workOrderId={workOrderId} isLive={!isTerminal} />
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200/30 dark:border-gray-700/30">
        {workOrder?.github_pull_request_url && (
          <a
            href={workOrder.github_pull_request_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-teal-500/10 border border-teal-400/30 text-teal-600 dark:text-teal-400 hover:bg-teal-500/20 transition-colors"
          >
            Open PR <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
        <Button variant="outline" size="sm" onClick={() => navigate(`/agent-work-orders/${workOrderId}`)}>
          Full Details <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
        </Button>
        {isTerminal && (
          <Button onClick={onBackToProject} size="sm" className="bg-teal-600 hover:bg-teal-700 text-white">
            <Bot className="w-4 h-4 mr-1.5" />
            Back to Project
          </Button>
        )}
      </div>
    </div>
  );
}
