import { Bot, ExternalLink } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { RealTimeStats } from "@/features/agent-work-orders/components/RealTimeStats";
import { useWorkOrder } from "@/features/agent-work-orders/hooks/useAgentWorkOrderQueries";
import { Button } from "@/features/ui/primitives/button";

interface AgentActivityPanelProps {
  workOrderId: string;
  onBackToProject: () => void;
}

export function AgentActivityPanel({ workOrderId, onBackToProject }: AgentActivityPanelProps) {
  const navigate = useNavigate();
  const { data: workOrder } = useWorkOrder(workOrderId);
  const isTerminal = workOrder?.status === "completed" || workOrder?.status === "failed";

  return (
    <div className="space-y-4">
      <RealTimeStats workOrderId={workOrderId} />
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
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/agent-work-orders/${workOrderId}`)}
        >
          Full Details <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
        </Button>
        {isTerminal && (
          <Button
            onClick={onBackToProject}
            size="sm"
            className="bg-teal-600 hover:bg-teal-700 text-white"
          >
            <Bot className="w-4 h-4 mr-1.5" />
            Back to Project
          </Button>
        )}
      </div>
    </div>
  );
}
