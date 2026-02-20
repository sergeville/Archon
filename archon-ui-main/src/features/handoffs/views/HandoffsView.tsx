import { ArrowRightLeft, Plus } from "lucide-react";
import { useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { Input } from "@/features/ui/primitives/input";
import { CreateHandoffModal, HandoffCard, HandoffDetailModal } from "../components";
import { useHandoffs } from "../hooks/useHandoffQueries";
import type { HandoffStatus } from "../types";

type FilterTab = "all" | HandoffStatus;

const TABS: { label: string; value: FilterTab }[] = [
  { label: "All", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Accepted", value: "accepted" },
  { label: "Completed", value: "completed" },
  { label: "Rejected", value: "rejected" },
];

export function HandoffsView() {
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const [agentFilter, setAgentFilter] = useState("");
  const [selectedHandoffId, setSelectedHandoffId] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const {
    data: handoffs = [],
    isLoading,
    error,
  } = useHandoffs(
    activeTab === "all" && !agentFilter
      ? undefined
      : {
          status: activeTab === "all" ? undefined : activeTab,
          agent: agentFilter || undefined,
        },
  );

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-400 text-sm">Failed to load handoffs</p>
          <p className="text-gray-500 text-xs mt-1">{(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ArrowRightLeft className="h-6 w-6 text-cyan-400" />
            Handoffs
          </h1>
          <p className="text-sm text-gray-400 mt-1">Track agent-to-agent task handoffs</p>
        </div>
        <div className="flex items-center gap-3">
          {handoffs.length > 0 && (
            <span className="text-sm text-gray-400">
              <span className="text-cyan-400 font-bold">{handoffs.length}</span> handoffs
            </span>
          )}
          <Button onClick={() => setShowCreateModal(true)} size="sm">
            <Plus className="h-4 w-4 mr-1.5" />
            Create Handoff
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Status tabs */}
        <div className="flex items-center gap-1">
          {TABS.map((tab) => (
            <button
              type="button"
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                activeTab === tab.value
                  ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                  : "text-gray-400 hover:text-gray-300 hover:bg-gray-800/50"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Agent filter */}
        <Input
          type="text"
          placeholder="Filter by agent..."
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
          className="w-[180px]"
        />

        {agentFilter && (
          <Button variant="outline" size="sm" onClick={() => setAgentFilter("")}>
            Clear
          </Button>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <ArrowRightLeft className="h-8 w-8 text-cyan-400 animate-pulse mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Loading handoffs...</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && handoffs.length === 0 && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <ArrowRightLeft className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No handoffs found</p>
            <p className="text-gray-500 text-sm mt-1">
              {activeTab !== "all" || agentFilter ? "Try adjusting your filters" : "Create a handoff to get started"}
            </p>
          </div>
        </div>
      )}

      {/* Handoff list */}
      {!isLoading && handoffs.length > 0 && (
        <div className="space-y-3">
          {handoffs.map((handoff) => (
            <HandoffCard key={handoff.id} handoff={handoff} onClick={() => setSelectedHandoffId(handoff.id)} />
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selectedHandoffId && (
        <HandoffDetailModal handoffId={selectedHandoffId} onClose={() => setSelectedHandoffId(null)} />
      )}

      {/* Create modal */}
      {showCreateModal && <CreateHandoffModal onClose={() => setShowCreateModal(false)} />}
    </div>
  );
}
