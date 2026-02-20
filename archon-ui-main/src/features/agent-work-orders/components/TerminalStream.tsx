import { useEffect, useRef } from "react";
import { useAgentWorkOrdersStore } from "../state/agentWorkOrdersStore";
import type { LogEntry } from "../types";

const EMPTY_LOGS: LogEntry[] = [];

interface TerminalStreamProps {
  workOrderId: string;
  isLive: boolean;
}

// Static color lookup — no dynamic Tailwind class construction
const cliTypeColors: Record<string, string> = {
  assistant: "text-cyan-400",
  tool_use: "text-yellow-400",
  tool_result: "text-green-400",
  result: "text-white font-semibold",
};

function formatTime(timestamp: string): string {
  const d = new Date(timestamp);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

export function TerminalStream({ workOrderId, isLive }: TerminalStreamProps) {
  const liveLogs = useAgentWorkOrdersStore((s) => s.liveLogs[workOrderId] ?? EMPTY_LOGS);
  const scrollRef = useRef<HTMLDivElement>(null);

  const cliLogs = liveLogs.filter((log: LogEntry) => log.event === "cli_output");

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [cliLogs.length]);

  if (cliLogs.length === 0) {
    return (
      <div className="bg-black rounded-lg font-mono text-sm p-3 text-gray-600 dark:text-gray-500 italic min-h-[3rem] flex items-center">
        {isLive ? "Waiting for agent output…" : "No terminal output recorded."}
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="bg-black rounded-lg font-mono text-sm p-3 overflow-y-auto max-h-96">
      {cliLogs.map((log: LogEntry, index: number) => {
        const cliType = (log.cli_type as string) ?? "assistant";
        const colorClass = cliTypeColors[cliType] ?? "text-gray-300";
        const output = (log.output as string) ?? "";
        return (
          <div key={`${log.timestamp}-${index}`} className={`leading-relaxed ${colorClass}`}>
            <span className="text-gray-600 mr-2">[{formatTime(log.timestamp)}]</span>
            {output}
          </div>
        );
      })}
    </div>
  );
}
