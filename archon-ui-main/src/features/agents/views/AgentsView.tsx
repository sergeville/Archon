import { Plus, Users } from "lucide-react";
import { useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { AgentCard, AgentDetailModal, RegisterAgentModal } from "../components";
import { useAgents } from "../hooks/useAgentQueries";
import type { AgentStatus } from "../types";

type FilterTab = "all" | AgentStatus;

const TABS: { label: string; value: FilterTab }[] = [
  { label: "All", value: "all" },
  { label: "Active", value: "active" },
  { label: "Inactive", value: "inactive" },
  { label: "Busy", value: "busy" },
];

export function AgentsView() {
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);

  const { data: agents = [], isLoading, error } = useAgents(activeTab === "all" ? undefined : activeTab);

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-400 text-sm">Failed to load agents</p>
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
            <Users className="h-6 w-6 text-cyan-400" />
            Agent Registry
          </h1>
          <p className="text-sm text-gray-400 mt-1">Manage and monitor registered agents in the swarm</p>
        </div>
        <div className="flex items-center gap-3">
          {agents.length > 0 && (
            <span className="text-sm text-gray-400">
              <span className="text-cyan-400 font-bold">{agents.length}</span>{" "}
              {activeTab === "all" ? "agents" : `${activeTab}`}
            </span>
          )}
          <Button onClick={() => setShowRegisterModal(true)} size="sm">
            <Plus className="h-4 w-4 mr-1.5" />
            Register Agent
          </Button>
        </div>
      </div>

      {/* Status filter tabs */}
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

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Users className="h-8 w-8 text-cyan-400 animate-pulse mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Loading agents...</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && agents.length === 0 && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Users className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No agents found</p>
            <p className="text-gray-500 text-sm mt-1">
              {activeTab !== "all" ? "Try a different filter" : "Register an agent to get started"}
            </p>
          </div>
        </div>
      )}

      {/* Agent grid */}
      {!isLoading && agents.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onClick={() => setSelectedAgentName(agent.name)} />
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selectedAgentName && (
        <AgentDetailModal agentName={selectedAgentName} onClose={() => setSelectedAgentName(null)} />
      )}

      {/* Register modal */}
      {showRegisterModal && <RegisterAgentModal onClose={() => setShowRegisterModal(false)} />}
    </div>
  );
}
