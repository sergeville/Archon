import { Bot, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateWorkOrder } from "@/features/agent-work-orders/hooks/useAgentWorkOrderQueries";
import { useRepositories } from "@/features/agent-work-orders/hooks/useRepositoryQueries";
import type { WorkflowStep } from "@/features/agent-work-orders/types";
import { useToast } from "@/features/shared/hooks/useToast";
import { Button } from "@/features/ui/primitives/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/features/ui/primitives/dialog";
import type { Task } from "../tasks/types";

interface SendToAgentModalProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  tasks: Task[];
}

const ALL_STEPS: WorkflowStep[] = ["create-branch", "planning", "execute", "commit", "create-pr"];
const DEFAULT_STEPS = new Set<WorkflowStep>(ALL_STEPS);

function buildPrompt(projectName: string, tasks: Task[]): string {
  if (tasks.length === 1) {
    const t = tasks[0];
    return [
      `Implement the following task from project "${projectName}":`,
      "",
      `Title: ${t.title}`,
      `Priority: ${t.priority}`,
      t.feature ? `Feature: ${t.feature}` : null,
      "",
      t.description || "(no description provided)",
      "",
      "Create a branch, implement the task, commit the changes, and open a pull request.",
    ]
      .filter((l) => l !== null)
      .join("\n");
  }

  const taskLines = tasks
    .map((t, i) => [`${i + 1}. ${t.title} [${t.priority}]`, t.description ? `   ${t.description}` : null])
    .flat()
    .filter(Boolean)
    .join("\n");

  return [
    `Implement the following tasks for project "${projectName}":`,
    "",
    taskLines,
    "",
    "Work through tasks in priority order (critical → high → medium → low).",
    "Create a branch, implement each task, commit, and open a pull request.",
  ].join("\n");
}

export function SendToAgentModal({ open, onClose, projectId, projectName, tasks }: SendToAgentModalProps) {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { data: repositories = [], isLoading: isLoadingRepos } = useRepositories();
  const createWorkOrder = useCreateWorkOrder();

  const [selectedRepoId, setSelectedRepoId] = useState<string>("");
  const [selectedSteps, setSelectedSteps] = useState<Set<WorkflowStep>>(DEFAULT_STEPS);
  const [prompt, setPrompt] = useState("");

  // Reset state when modal opens with new tasks
  useEffect(() => {
    if (open) {
      setPrompt(buildPrompt(projectName, tasks));
      setSelectedSteps(new Set(DEFAULT_STEPS));
      if (repositories.length > 0 && !selectedRepoId) {
        setSelectedRepoId(repositories[0].id);
      }
    }
  }, [open, projectName, tasks]);

  // Auto-select first repo when repos load
  useEffect(() => {
    if (repositories.length > 0 && !selectedRepoId) {
      setSelectedRepoId(repositories[0].id);
    }
  }, [repositories, selectedRepoId]);

  const toggleStep = (step: WorkflowStep) => {
    setSelectedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(step)) {
        next.delete(step);
      } else {
        next.add(step);
      }
      return next;
    });
  };

  const selectedRepo = repositories.find((r) => r.id === selectedRepoId);

  const handleSubmit = async () => {
    if (!selectedRepo) return;

    try {
      const result = await createWorkOrder.mutateAsync({
        repository_id: selectedRepo.id,
        repository_url: selectedRepo.repository_url,
        sandbox_type: selectedRepo.default_sandbox_type || "git_worktree",
        user_request: prompt,
        selected_commands: ALL_STEPS.filter((s) => selectedSteps.has(s)),
      });

      onClose();
      navigate(`/projects/${projectId}/agent-run/${result.agent_work_order_id}`);
    } catch (err) {
      showToast(`Failed to create work order: ${err instanceof Error ? err.message : "Unknown error"}`, "error");
    }
  };

  const hasNoRepos = !isLoadingRepos && repositories.length === 0;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-teal-500" />
            {tasks.length === 1 ? `Run task with Agent` : `Run project with Agent`}
          </DialogTitle>
          <DialogDescription>
            {tasks.length === 1
              ? `Send "${tasks[0].title}" to an agent for implementation.`
              : `Send ${tasks.length} tasks from "${projectName}" to an agent for implementation.`}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* Repository */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Repository</label>
            {hasNoRepos ? (
              <div className="flex items-center gap-2 p-3 rounded-lg border border-amber-400/30 bg-amber-500/10 text-sm text-amber-600 dark:text-amber-400">
                <span>No repositories configured.</span>
                <button
                  type="button"
                  onClick={() => { onClose(); navigate("/agent-work-orders"); }}
                  className="inline-flex items-center gap-1 underline hover:no-underline"
                >
                  Configure one <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <select
                value={selectedRepoId}
                onChange={(e) => setSelectedRepoId(e.target.value)}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                {isLoadingRepos && <option>Loading...</option>}
                {repositories.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.display_name || repo.repository_url}
                    {!repo.is_verified && " (unverified)"}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Workflow Steps */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Workflow Steps</label>
            <div className="flex flex-wrap gap-2">
              {ALL_STEPS.map((step) => (
                <button
                  key={step}
                  type="button"
                  onClick={() => toggleStep(step)}
                  className={[
                    "px-3 py-1.5 rounded-full text-xs font-medium border transition-all",
                    selectedSteps.has(step)
                      ? "bg-teal-500/20 border-teal-400/50 text-teal-600 dark:text-teal-400"
                      : "bg-gray-100/50 dark:bg-gray-800/50 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400",
                  ].join(" ")}
                >
                  {step}
                </button>
              ))}
            </div>
          </div>

          {/* Prompt */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={10}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-mono focus:outline-none focus:ring-2 focus:ring-teal-500 resize-y"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={createWorkOrder.isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={hasNoRepos || !prompt.trim() || createWorkOrder.isPending}
            className="bg-teal-600 hover:bg-teal-700 text-white"
          >
            {createWorkOrder.isPending ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Starting…
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Bot className="w-4 h-4" />
                Start Agent
              </span>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
