import { Loader2, Users, X } from "lucide-react";
import { useId, useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { Card } from "@/features/ui/primitives/card";
import { Input } from "@/features/ui/primitives/input";
import { useRegisterAgent } from "../hooks/useAgentQueries";

interface RegisterAgentModalProps {
  onClose: () => void;
}

export function RegisterAgentModal({ onClose }: RegisterAgentModalProps) {
  const nameId = useId();
  const capabilitiesId = useId();
  const metadataId = useId();

  const [name, setName] = useState("");
  const [capabilitiesInput, setCapabilitiesInput] = useState("");
  const [metadataInput, setMetadataInput] = useState("{}");
  const [metadataError, setMetadataError] = useState<string | null>(null);

  const registerMutation = useRegisterAgent();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let metadata: Record<string, unknown> = {};
    try {
      metadata = JSON.parse(metadataInput);
      setMetadataError(null);
    } catch {
      setMetadataError("Invalid JSON in metadata field");
      return;
    }

    const capabilities = capabilitiesInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    await registerMutation.mutateAsync({ name: name.trim(), capabilities, metadata });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="w-full max-w-md">
        <Card className="bg-gray-900 border-gray-700">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-semibold text-white">Register Agent</h2>
            </div>
            <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-white">
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={nameId}>
                Name
              </label>
              <Input
                id={nameId}
                type="text"
                placeholder="e.g. claude-primary"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={capabilitiesId}>
                Capabilities
                <span className="text-gray-500 font-normal ml-1">(comma-separated)</span>
              </label>
              <Input
                id={capabilitiesId}
                type="text"
                placeholder="e.g. coding, analysis, search"
                value={capabilitiesInput}
                onChange={(e) => setCapabilitiesInput(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300" htmlFor={metadataId}>
                Metadata
                <span className="text-gray-500 font-normal ml-1">(JSON)</span>
              </label>
              <textarea
                id={metadataId}
                className="w-full h-24 px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 resize-none font-mono"
                value={metadataInput}
                onChange={(e) => setMetadataInput(e.target.value)}
              />
              {metadataError && <p className="text-xs text-red-400">{metadataError}</p>}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={registerMutation.isPending || !name.trim()}>
                {registerMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                    Registering...
                  </>
                ) : (
                  "Register Agent"
                )}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
