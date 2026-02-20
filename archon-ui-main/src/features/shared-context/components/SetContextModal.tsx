import { Database, Loader2, X } from "lucide-react";
import { useId, useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { Input } from "@/features/ui/primitives/input";
import { useSetContext } from "../hooks/useContextQueries";
import type { ContextEntry } from "../types";

interface SetContextModalProps {
  editEntry?: ContextEntry;
  onClose: () => void;
}

export function SetContextModal({ editEntry, onClose }: SetContextModalProps) {
  const keyId = useId();
  const valueId = useId();
  const setById = useId();
  const expiresId = useId();

  const [key, setKey] = useState(editEntry?.context_key ?? "");
  const [valueInput, setValueInput] = useState(editEntry ? JSON.stringify(editEntry.value, null, 2) : "");
  const [setBy, setSetBy] = useState(editEntry?.set_by ?? "");
  const [expiresAt, setExpiresAt] = useState(editEntry?.expires_at ?? "");
  const [valueError, setValueError] = useState<string | null>(null);

  const setContextMutation = useSetContext();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let parsedValue: unknown;
    try {
      parsedValue = JSON.parse(valueInput);
      setValueError(null);
    } catch {
      setValueError("Invalid JSON value");
      return;
    }

    await setContextMutation.mutateAsync({
      key: key.trim(),
      data: {
        value: parsedValue,
        set_by: setBy.trim(),
        expires_at: expiresAt || undefined,
      },
    });
    onClose();
  };

  const isEditing = !!editEntry;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="w-full max-w-md">
        <Card className="bg-gray-900 border-gray-700">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold text-white">
                {isEditing ? "Edit Context Value" : "Set Context Value"}
              </h2>
            </div>
            <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-white">
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={keyId}>
                Key
              </label>
              <Input
                id={keyId}
                type="text"
                placeholder="e.g. agent.current_task"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                required
                disabled={isEditing}
                className="font-mono"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={valueId}>
                Value
                <span className="text-gray-500 font-normal ml-1">(JSON)</span>
              </label>
              <textarea
                id={valueId}
                className="w-full h-28 px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 resize-none font-mono"
                placeholder='e.g. "value" or {"key": "val"}'
                value={valueInput}
                onChange={(e) => setValueInput(e.target.value)}
                required
              />
              {valueError && <p className="text-xs text-red-400">{valueError}</p>}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={setById}>
                Set By
              </label>
              <Input
                id={setById}
                type="text"
                placeholder="e.g. claude"
                value={setBy}
                onChange={(e) => setSetBy(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={expiresId}>
                Expires At
                <span className="text-gray-500 font-normal ml-1">(optional)</span>
              </label>
              <Input
                id={expiresId}
                type="datetime-local"
                value={expiresAt ? expiresAt.slice(0, 16) : ""}
                onChange={(e) => setExpiresAt(e.target.value ? new Date(e.target.value).toISOString() : "")}
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={setContextMutation.isPending || !key.trim() || !setBy.trim()}>
                {setContextMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                    Saving...
                  </>
                ) : isEditing ? (
                  "Update Value"
                ) : (
                  "Set Value"
                )}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
