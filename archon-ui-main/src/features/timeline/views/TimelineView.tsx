import { ChevronDown, ChevronRight, Clock } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuditLog } from "../hooks/useTimelineQueries";
import type { AuditLogEntry, AuditLogFilters, RiskLevel } from "../types";

const SOURCE_OPTIONS = [
  { label: "All Sources", value: "" },
  { label: "Archon", value: "archon" },
  { label: "Alfred", value: "alfred" },
  { label: "Work Orders", value: "work-orders" },
  { label: "Situation Agent", value: "situation_agent" },
  { label: "Council", value: "council" },
];

const RISK_OPTIONS = [
  { label: "All Risks", value: "" },
  { label: "Low", value: "LOW" },
  { label: "Medium", value: "MED" },
  { label: "High", value: "HIGH" },
  { label: "Destructive", value: "DESTRUCTIVE" },
];

const LIMIT_OPTIONS = [50, 100, 500];

const SOURCE_COLORS: Record<string, string> = {
  alfred: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  archon: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  "work-orders": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  council: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  situation_agent: "bg-green-500/20 text-green-400 border-green-500/30",
};

const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  MED: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  HIGH: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  DESTRUCTIVE: "bg-red-500/20 text-red-400 border-red-500/30",
};

const OUTCOME_COLORS: Record<string, string> = {
  success: "text-green-400",
  failed: "text-red-400",
  blocked: "text-orange-400",
  approved: "text-green-400",
};

function formatRelativeTime(timestamp: string): string {
  const now = Date.now();
  const then = new Date(timestamp).getTime();
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return new Date(timestamp).toLocaleDateString();
}

function formatAbsoluteTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString();
}

function TimelineEntry({ entry }: { entry: AuditLogEntry }) {
  const [expanded, setExpanded] = useState(false);
  const hasMetadata = entry.metadata && Object.keys(entry.metadata).length > 0;
  const sourceColor = SOURCE_COLORS[entry.source] || "bg-gray-500/20 text-gray-400 border-gray-500/30";
  const riskColor = RISK_COLORS[entry.risk_level];
  const outcomeColor = entry.outcome ? OUTCOME_COLORS[entry.outcome.toLowerCase()] || "text-gray-400" : "";

  return (
    <div className="flex gap-3 p-3 rounded-lg bg-white/5 dark:bg-white/[0.03] border border-white/10 dark:border-white/[0.06] hover:bg-white/10 dark:hover:bg-white/[0.06] transition-colors">
      {/* Timeline dot */}
      <div className="flex flex-col items-center pt-1.5">
        <div className="w-2 h-2 rounded-full bg-cyan-400/60" />
        <div className="w-px flex-1 bg-white/10 mt-1" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1.5">
        {/* Top row: timestamp + badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-500" title={formatAbsoluteTime(entry.timestamp)}>
            {formatRelativeTime(entry.timestamp)}
          </span>
          <span className={cn("text-xs px-1.5 py-0.5 rounded border", sourceColor)}>{entry.source}</span>
          <span className={cn("text-xs px-1.5 py-0.5 rounded border", riskColor)}>{entry.risk_level}</span>
          {entry.outcome && <span className={cn("text-xs font-medium", outcomeColor)}>{entry.outcome}</span>}
        </div>

        {/* Action + target */}
        <div className="flex items-baseline gap-1.5">
          <span className="text-sm font-semibold text-white">{entry.action}</span>
          {entry.target && <span className="text-sm text-gray-500 truncate">{entry.target}</span>}
        </div>

        {/* Agent info */}
        {entry.agent && <div className="text-xs text-gray-500">agent: {entry.agent}</div>}

        {/* Expandable metadata */}
        {hasMetadata && (
          <div>
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              metadata
            </button>
            {expanded && (
              <pre className="mt-1 p-2 rounded bg-black/30 text-xs text-gray-400 overflow-x-auto max-h-48">
                {JSON.stringify(entry.metadata, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {(["s0", "s1", "s2", "s3", "s4"] as const).map((key) => (
        <div
          key={key}
          className="flex gap-3 p-3 rounded-lg bg-white/5 dark:bg-white/[0.03] border border-white/10 dark:border-white/[0.06] animate-pulse"
        >
          <div className="w-2 h-2 rounded-full bg-gray-700 mt-1.5" />
          <div className="flex-1 space-y-2">
            <div className="flex gap-2">
              <div className="h-4 w-16 rounded bg-gray-700" />
              <div className="h-4 w-12 rounded bg-gray-700" />
              <div className="h-4 w-10 rounded bg-gray-700" />
            </div>
            <div className="h-4 w-48 rounded bg-gray-700" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function TimelineView() {
  const [filters, setFilters] = useState<AuditLogFilters>({ limit: 50 });

  const { data: entries = [], isLoading, error } = useAuditLog(filters);

  const updateFilter = (key: keyof AuditLogFilters, value: string | number) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === "" || value === 0) {
        delete next[key];
      } else {
        (next as Record<string, string | number>)[key] = value;
      }
      return next;
    });
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-400 text-sm">Failed to load audit log</p>
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
            <Clock className="h-6 w-6 text-cyan-400" />
            Timeline
          </h1>
          <p className="text-sm text-gray-400 mt-1">Chronological log of all AI system actions</p>
        </div>
        {entries.length > 0 && (
          <span className="text-sm text-gray-400">
            <span className="text-cyan-400 font-bold">{entries.length}</span> events
          </span>
        )}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={filters.source || ""}
          onChange={(e) => updateFilter("source", e.target.value)}
          className="px-3 py-1.5 text-sm rounded-md bg-white/5 dark:bg-white/[0.03] border border-white/10 dark:border-white/[0.06] text-gray-300 focus:outline-none focus:border-cyan-500/50"
        >
          {SOURCE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-gray-900">
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={filters.risk_level || ""}
          onChange={(e) => updateFilter("risk_level", e.target.value)}
          className="px-3 py-1.5 text-sm rounded-md bg-white/5 dark:bg-white/[0.03] border border-white/10 dark:border-white/[0.06] text-gray-300 focus:outline-none focus:border-cyan-500/50"
        >
          {RISK_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-gray-900">
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={filters.limit || 50}
          onChange={(e) => updateFilter("limit", Number(e.target.value))}
          className="px-3 py-1.5 text-sm rounded-md bg-white/5 dark:bg-white/[0.03] border border-white/10 dark:border-white/[0.06] text-gray-300 focus:outline-none focus:border-cyan-500/50"
        >
          {LIMIT_OPTIONS.map((n) => (
            <option key={n} value={n} className="bg-gray-900">
              {n} events
            </option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {isLoading && <LoadingSkeleton />}

      {/* Empty state */}
      {!isLoading && entries.length === 0 && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Clock className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No audit events yet</p>
            <p className="text-gray-500 text-sm mt-1">Events will appear here as your AI systems take actions.</p>
          </div>
        </div>
      )}

      {/* Timeline entries */}
      {!isLoading && entries.length > 0 && (
        <div className="space-y-2">
          {entries.map((entry) => (
            <TimelineEntry key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
