import { CheckCircle2, ExternalLink, Loader2, Rocket } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../ui/primitives/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../ui/primitives/dialog";
import { usePromotePlan } from "../hooks/usePlanPromoterQueries";
import type { Plan, PromoteResult } from "../types";

interface PromoteModalProps {
  plan: Plan | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function PromoteModal({ plan, open, onOpenChange }: PromoteModalProps) {
  const [result, setResult] = useState<PromoteResult | null>(null);
  const promoteMutation = usePromotePlan();

  function handleClose() {
    onOpenChange(false);
    // Reset result after dialog closes
    setTimeout(() => {
      setResult(null);
      promoteMutation.reset();
    }, 200);
  }

  async function handleConfirm() {
    if (!plan) return;
    try {
      const res = await promoteMutation.mutateAsync({
        plan_path: plan.path,
        plan_name: plan.name,
      });
      setResult(res);
    } catch {
      // Error is in promoteMutation.error
    }
  }

  if (!plan) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Rocket className="h-5 w-5 text-cyan-400" />
            Promote Plan to Project
          </DialogTitle>
        </DialogHeader>

        <div className="mt-2 space-y-4">
          {/* Plan info */}
          <div className="rounded-lg bg-white/5 dark:bg-black/20 border border-zinc-700/50 p-3 space-y-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{plan.name}</p>
            <p className="text-[11px] font-mono text-gray-500 dark:text-zinc-500">{plan.path}</p>
          </div>

          {/* States */}
          {!result && !promoteMutation.isPending && !promoteMutation.isError && (
            <div className="space-y-3">
              <p className="text-sm text-gray-600 dark:text-zinc-400">
                This will create an Archon project and use AI to generate implementation tasks from
                the plan document.
              </p>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={handleClose}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="bg-cyan-600 hover:bg-cyan-700 text-white"
                  onClick={handleConfirm}
                >
                  <Rocket className="h-3.5 w-3.5 mr-1.5" />
                  Promote
                </Button>
              </div>
            </div>
          )}

          {promoteMutation.isPending && (
            <div className="flex items-center gap-3 py-4">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-400 shrink-0" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Generating tasks with AI…
                </p>
                <p className="text-xs text-gray-500 dark:text-zinc-500 mt-0.5">
                  Reading plan and extracting implementation tasks
                </p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-green-500/10 border border-green-500/30">
                <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-green-300">Promotion complete!</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Created project with{" "}
                    <span className="text-cyan-400 font-semibold">{result.tasks_created}</span> of{" "}
                    <span className="text-cyan-400 font-semibold">{result.task_count}</span> AI-generated tasks.
                  </p>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={handleClose}>
                  Close
                </Button>
                <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 text-white" asChild>
                  <Link to={`/projects/${result.project_id}`} onClick={handleClose}>
                    <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                    Go to Project
                  </Link>
                </Button>
              </div>
            </div>
          )}

          {promoteMutation.isError && !result && (
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                <p className="text-sm font-semibold text-red-400">Promotion failed</p>
                <p className="text-xs text-gray-400 mt-1">
                  {promoteMutation.error instanceof Error
                    ? promoteMutation.error.message
                    : "An unexpected error occurred. Check the server logs."}
                </p>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={handleClose}>
                  Close
                </Button>
                <Button
                  size="sm"
                  className="bg-cyan-600 hover:bg-cyan-700 text-white"
                  onClick={handleConfirm}
                >
                  Retry
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
