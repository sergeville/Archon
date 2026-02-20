import { formatDistanceToNow } from "date-fns";
import { Clock, History, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/features/ui/primitives/button";
import { useDeleteContext } from "../hooks/useContextQueries";
import type { ContextEntry } from "../types";

interface ContextEntryRowProps {
  entry: ContextEntry;
  onShowHistory: (key: string) => void;
  onEdit: (entry: ContextEntry) => void;
}

function truncateValue(value: unknown): string {
  const str = typeof value === "string" ? value : JSON.stringify(value);
  return str.length > 80 ? `${str.slice(0, 80)}…` : str;
}

export function ContextEntryRow({ entry, onShowHistory, onEdit }: ContextEntryRowProps) {
  const deleteMutation = useDeleteContext();

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteMutation.mutate(entry.context_key);
  };

  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/30 transition-colors group">
      <td className="px-4 py-3">
        <span className="font-mono text-xs text-cyan-400">{entry.context_key}</span>
      </td>
      <td className="px-4 py-3">
        <span className="text-xs text-gray-300 font-mono">{truncateValue(entry.value)}</span>
      </td>
      <td className="px-4 py-3">
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-700/50 text-gray-300 border border-gray-600/50">
          {entry.set_by}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="h-3 w-3" />
          {formatDistanceToNow(new Date(entry.updated_at), { addSuffix: true })}
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onShowHistory(entry.context_key)}
            className="h-7 px-2 text-gray-400 hover:text-cyan-400"
            title="View history"
          >
            <History className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(entry)}
            className="h-7 px-2 text-gray-400 hover:text-yellow-400"
            title="Edit value"
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="h-7 px-2 text-gray-400 hover:text-red-400"
            title="Delete entry"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </td>
    </tr>
  );
}
