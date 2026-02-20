import { ArrowLeft, Bot } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { cn } from "@/features/ui/primitives/styles";
import type { Task } from "../tasks/types";
import { useProjectTasks } from "../tasks/hooks/useTaskQueries";
import { AgentActivityPanel } from "../components/AgentActivityPanel";

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  high: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

const STATUS_BORDER: Record<string, string> = {
  todo: "border-gray-400/30",
  doing: "border-blue-400/40",
  review: "border-yellow-400/40",
  done: "border-green-400/30",
};

function ReadOnlyTaskCard({ task }: { task: Task }) {
  return (
    <div
      className={cn(
        "p-3 rounded-lg border bg-white/5 dark:bg-black/20",
        STATUS_BORDER[task.status] || "border-gray-400/30",
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2">{task.title}</p>
        <span
          className={cn(
            "px-1.5 py-0.5 rounded text-[10px] font-medium flex-shrink-0",
            PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.medium,
          )}
        >
          {task.priority}
        </span>
      </div>
      {task.description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1">{task.description}</p>
      )}
      <div className="flex items-center gap-1.5 mt-2">
        <span className="text-[10px] text-gray-500 dark:text-gray-500 capitalize">{task.status}</span>
        {task.feature && (
          <span className="text-[10px] text-gray-400 dark:text-gray-500">· {task.feature}</span>
        )}
      </div>
    </div>
  );
}

export function AgentExecutionView() {
  const { projectId, workOrderId } = useParams<{ projectId: string; workOrderId: string }>();
  const navigate = useNavigate();
  const { data: tasks = [] } = useProjectTasks(projectId);

  const handleBackToProject = () => navigate(`/projects/${projectId}`);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={handleBackToProject}
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Project
        </button>
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-teal-500" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Running with Agent</span>
        </div>
      </div>

      {/* Split layout */}
      <div className="flex gap-6">
        {/* Left panel: task list */}
        <div className="w-72 flex-shrink-0 space-y-2">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Project Tasks</h3>
          {tasks.length === 0 ? (
            <p className="text-sm text-gray-400 dark:text-gray-500">No tasks</p>
          ) : (
            tasks.map((task) => <ReadOnlyTaskCard key={task.id} task={task} />)
          )}
        </div>

        {/* Right panel: agent activity */}
        <div className="flex-1 min-w-0">
          {workOrderId && (
            <AgentActivityPanel workOrderId={workOrderId} onBackToProject={handleBackToProject} />
          )}
        </div>
      </div>
    </div>
  );
}
