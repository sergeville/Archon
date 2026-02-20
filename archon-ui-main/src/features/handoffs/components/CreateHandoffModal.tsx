import { ArrowRightLeft, Loader2, X } from "lucide-react";
import { useId, useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { Input } from "@/features/ui/primitives/input";
import { useCreateHandoff } from "../hooks/useHandoffQueries";

interface CreateHandoffModalProps {
  onClose: () => void;
}

export function CreateHandoffModal({ onClose }: CreateHandoffModalProps) {
  const sessionId_fieldId = useId();
  const fromAgentId = useId();
  const toAgentId = useId();
  const notesId = useId();
  const contextId = useId();

  const [sessionId, setSessionId] = useState("");
  const [fromAgent, setFromAgent] = useState("");
  const [toAgent, setToAgent] = useState("");
  const [notes, setNotes] = useState("");
  const [contextInput, setContextInput] = useState("{}");
  const [contextError, setContextError] = useState<string | null>(null);

  const createMutation = useCreateHandoff();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let context: Record<string, unknown> = {};
    try {
      context = JSON.parse(contextInput);
      setContextError(null);
    } catch {
      setContextError("Invalid JSON in context field");
      return;
    }

    await createMutation.mutateAsync({
      session_id: sessionId.trim(),
      from_agent: fromAgent.trim(),
      to_agent: toAgent.trim(),
      notes: notes.trim() || undefined,
      context,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="w-full max-w-md">
        <Card className="bg-gray-900 border-gray-700">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
            <div className="flex items-center gap-2">
              <ArrowRightLeft className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold text-white">Create Handoff</h2>
            </div>
            <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-white">
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={sessionId_fieldId}>
                Session ID
              </label>
              <Input
                id={sessionId_fieldId}
                type="text"
                placeholder="UUID of the session"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                required
                className="font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-gray-300" htmlFor={fromAgentId}>
                  From Agent
                </label>
                <Input
                  id={fromAgentId}
                  type="text"
                  placeholder="e.g. claude"
                  value={fromAgent}
                  onChange={(e) => setFromAgent(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-gray-300" htmlFor={toAgentId}>
                  To Agent
                </label>
                <Input
                  id={toAgentId}
                  type="text"
                  placeholder="e.g. gemini"
                  value={toAgent}
                  onChange={(e) => setToAgent(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={notesId}>
                Notes
                <span className="text-gray-500 font-normal ml-1">(optional)</span>
              </label>
              <textarea
                id={notesId}
                className="w-full h-20 px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 resize-none"
                placeholder="Instructions or context for the receiving agent..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={contextId}>
                Context
                <span className="text-gray-500 font-normal ml-1">(JSON)</span>
              </label>
              <textarea
                id={contextId}
                className="w-full h-24 px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 resize-none font-mono"
                value={contextInput}
                onChange={(e) => setContextInput(e.target.value)}
              />
              {contextError && <p className="text-xs text-red-400">{contextError}</p>}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending || !sessionId.trim() || !fromAgent.trim() || !toAgent.trim()}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Handoff"
                )}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
