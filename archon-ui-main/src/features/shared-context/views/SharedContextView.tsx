import { Database, Plus, Search } from "lucide-react";
import { useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { Input } from "@/features/ui/primitives/input";
import { ContextEntryRow, ContextHistoryModal, SetContextModal } from "../components";
import { useContextEntries } from "../hooks/useContextQueries";
import type { ContextEntry } from "../types";

export function SharedContextView() {
  const [prefixFilter, setPrefixFilter] = useState("");
  const [historyKey, setHistoryKey] = useState<string | null>(null);
  const [editEntry, setEditEntry] = useState<ContextEntry | null>(null);
  const [showSetModal, setShowSetModal] = useState(false);

  const { data: entries = [], isLoading, error } = useContextEntries();

  // Client-side prefix filtering
  const filteredEntries = prefixFilter
    ? entries.filter((e) => e.context_key.toLowerCase().startsWith(prefixFilter.toLowerCase()))
    : entries;

  const handleEdit = (entry: ContextEntry) => {
    setEditEntry(entry);
    setShowSetModal(true);
  };

  const handleCloseModal = () => {
    setShowSetModal(false);
    setEditEntry(null);
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-400 text-sm">Failed to load context</p>
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
            <Database className="h-6 w-6 text-cyan-400" />
            Shared Context Board
          </h1>
          <p className="text-sm text-gray-400 mt-1">Key-value store shared across all agents</p>
        </div>
        <div className="flex items-center gap-3">
          {entries.length > 0 && (
            <span className="text-sm text-gray-400">
              <span className="text-cyan-400 font-bold">{filteredEntries.length}</span> entries
            </span>
          )}
          <Button onClick={() => setShowSetModal(true)} size="sm">
            <Plus className="h-4 w-4 mr-1.5" />
            Set Value
          </Button>
        </div>
      </div>

      {/* Prefix filter */}
      <div className="flex items-center gap-3">
        <div className="flex-1 max-w-xs">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Filter by key prefix..."
              value={prefixFilter}
              onChange={(e) => setPrefixFilter(e.target.value)}
              className="pl-10 font-mono"
            />
          </div>
        </div>
        {prefixFilter && (
          <Button variant="outline" size="sm" onClick={() => setPrefixFilter("")}>
            Clear
          </Button>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Database className="h-8 w-8 text-cyan-400 animate-pulse mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Loading context...</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && filteredEntries.length === 0 && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Database className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No context entries found</p>
            <p className="text-gray-500 text-sm mt-1">
              {prefixFilter ? "Try a different prefix filter" : "Use 'Set Value' to add entries"}
            </p>
          </div>
        </div>
      )}

      {/* Table */}
      {!isLoading && filteredEntries.length > 0 && (
        <div className="border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-800/50 text-xs text-gray-400 uppercase tracking-wider">
                <th className="px-4 py-3 text-left">Key</th>
                <th className="px-4 py-3 text-left">Value</th>
                <th className="px-4 py-3 text-left">Set By</th>
                <th className="px-4 py-3 text-left">Updated</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map((entry) => (
                <ContextEntryRow
                  key={entry.id}
                  entry={entry}
                  onShowHistory={(key) => setHistoryKey(key)}
                  onEdit={handleEdit}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      {historyKey && <ContextHistoryModal contextKey={historyKey} onClose={() => setHistoryKey(null)} />}

      {showSetModal && <SetContextModal editEntry={editEntry ?? undefined} onClose={handleCloseModal} />}
    </div>
  );
}
