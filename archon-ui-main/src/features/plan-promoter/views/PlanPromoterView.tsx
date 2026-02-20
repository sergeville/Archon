import { AlertTriangle, Map } from "lucide-react";
import { useState } from "react";
import { PlanCard } from "../components/PlanCard";
import { PromoteModal } from "../components/PromoteModal";
import { usePlans } from "../hooks/usePlanPromoterQueries";
import type { Plan } from "../types";

export function PlanPromoterView() {
  const { data, isLoading, error } = usePlans();
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  function handlePromote(plan: Plan) {
    setSelectedPlan(plan);
    setModalOpen(true);
  }

  const plans = data?.plans ?? [];
  const configError = data?.error;

  // Group plans by section
  const sections = plans.reduce<Record<string, Plan[]>>((acc, plan) => {
    const section = plan.section || "Uncategorized";
    acc[section] = acc[section] ?? [];
    acc[section].push(plan);
    return acc;
  }, {});

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Map className="h-6 w-6 text-cyan-400" />
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Plan Promoter</h1>
          <p className="text-sm text-gray-500 dark:text-zinc-500">
            Promote plan files from PLANS_INDEX.md into Archon projects with AI-generated tasks.
          </p>
        </div>
      </div>

      {/* Config error banner */}
      {configError && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
          <AlertTriangle className="h-5 w-5 text-yellow-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-yellow-300">Documents not accessible</p>
            <p className="text-xs text-gray-400 mt-1">{configError}</p>
            <p className="text-xs text-gray-500 mt-2">
              Add <code className="bg-black/30 px-1 rounded text-cyan-400">{"- ${HOME}/Documents:/documents:ro"}</code>{" "}
              to the <code className="bg-black/30 px-1 rounded text-cyan-400">archon-server</code> volumes in{" "}
              <code className="bg-black/30 px-1 rounded text-cyan-400">docker-compose.yml</code>.
            </p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-20 text-gray-500 dark:text-zinc-500">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 rounded-full border-2 border-cyan-400/30 border-t-cyan-400 animate-spin" />
            <p className="text-sm">Loading plans…</p>
          </div>
        </div>
      )}

      {/* API error (network/server error) */}
      {error && !isLoading && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertTriangle className="h-5 w-5 text-red-400 shrink-0" />
          <p className="text-sm text-red-300">{error instanceof Error ? error.message : "Failed to load plans."}</p>
        </div>
      )}

      {/* Plans grouped by section */}
      {!isLoading && !error && Object.keys(sections).length === 0 && !configError && (
        <div className="flex items-center justify-center py-20 text-gray-500 dark:text-zinc-500">
          <p className="text-sm">No plans found in PLANS_INDEX.md.</p>
        </div>
      )}

      {Object.entries(sections).map(([section, sectionPlans]) => (
        <section key={section}>
          <h2 className="text-sm font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-3">
            {section}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sectionPlans.map((plan) => (
              <PlanCard key={plan.path} plan={plan} onPromote={handlePromote} />
            ))}
          </div>
        </section>
      ))}

      {/* Promote modal */}
      <PromoteModal
        plan={selectedPlan}
        open={modalOpen}
        onOpenChange={(open) => {
          setModalOpen(open);
          if (!open) setSelectedPlan(null);
        }}
      />
    </div>
  );
}
