import { format } from "date-fns";
import { Clock, Database, X } from "lucide-react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { useContextHistory } from "../hooks/useContextQueries";

interface ContextHistoryModalProps {
  contextKey: string;
  onClose: () => void;
}

function valuePreview(value: unknown): string {
  const str = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return str.length > 200 ? `${str.slice(0, 200)}…` : str;
}

export function ContextHistoryModal({ contextKey, onClose }: ContextHistoryModalProps) {
  const { data: historyResponse, isLoading, error } = useContextHistory(contextKey, 50);

  const history = historyResponse?.history ?? [];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="my-8 w-full max-w-2xl">
        <Card className="bg-gray-900 border-gray-700">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-cyan-400" />
              <div>
                <h2 className="text-lg font-semibold text-white">Context History</h2>
                <p className="text-xs font-mono text-cyan-400 mt-0.5">{contextKey}</p>
              </div>
            </div>
            <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-white">
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-6">
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <Clock className="h-6 w-6 text-cyan-400 animate-pulse" />
              </div>
            )}

            {error && (
              <div className="text-center py-8">
                <p className="text-red-400 text-sm">Failed to load history</p>
                <p className="text-gray-500 text-xs mt-1">{(error as Error).message}</p>
              </div>
            )}

            {!isLoading && !error && history.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-400 text-sm">No history available</p>
              </div>
            )}

            {!isLoading && !error && history.length > 0 && (
              <div className="space-y-4">
                {history.map((entry) => (
                  <div key={entry.id} className="border border-gray-700 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span className="text-gray-300 font-medium">
                        Changed by <span className="text-cyan-400">{entry.changed_by}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {format(new Date(entry.changed_at), "MMM d, yyyy h:mm:ss a")}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      {entry.old_value !== undefined && (
                        <div className="space-y-1">
                          <p className="text-xs font-medium text-red-400">Old Value</p>
                          <pre className="text-xs text-gray-400 bg-gray-800/50 border border-gray-700 rounded p-2 overflow-x-auto">
                            {valuePreview(entry.old_value)}
                          </pre>
                        </div>
                      )}
                      <div className={entry.old_value !== undefined ? "" : "col-span-2"}>
                        <div className="space-y-1">
                          <p className="text-xs font-medium text-green-400">New Value</p>
                          <pre className="text-xs text-gray-300 bg-gray-800/50 border border-gray-700 rounded p-2 overflow-x-auto">
                            {valuePreview(entry.new_value)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
