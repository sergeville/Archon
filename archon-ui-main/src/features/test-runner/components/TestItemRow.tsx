import { AlertCircle, AlertTriangle, CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { cn } from "../../../lib/utils";
import type { TestItem } from "../types";

interface TestItemRowProps {
  test: TestItem;
}

const STATUS_CONFIG = {
  pending: {
    icon: Circle,
    color: "text-zinc-500",
    border: "border-zinc-700/30",
    spin: false,
  },
  running: {
    icon: Loader2,
    color: "text-blue-400",
    border: "border-blue-400/50",
    spin: true,
  },
  passed: {
    icon: CheckCircle2,
    color: "text-green-400",
    border: "border-green-400/50",
    spin: false,
  },
  failed: {
    icon: XCircle,
    color: "text-red-400",
    border: "border-red-400/50",
    spin: false,
  },
  skipped: {
    icon: AlertTriangle,
    color: "text-yellow-400",
    border: "border-yellow-400/50",
    spin: false,
  },
  error: {
    icon: AlertCircle,
    color: "text-orange-400",
    border: "border-orange-400/50",
    spin: false,
  },
} as const;

export function TestItemRow({ test }: TestItemRowProps) {
  const cfg = STATUS_CONFIG[test.status];
  const Icon = cfg.icon;

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-3 py-2 rounded-lg",
        "border-l-2",
        cfg.border,
        "bg-zinc-900/40 border border-zinc-800/30 border-l-2",
      )}
    >
      <Icon className={cn("h-4 w-4 shrink-0", cfg.color, cfg.spin && "animate-spin")} />
      <div className="flex flex-col min-w-0">
        <span className="text-sm text-zinc-200 truncate font-mono">{test.name}</span>
        <span className="text-xs text-zinc-500 truncate">{test.path}</span>
      </div>
    </div>
  );
}
