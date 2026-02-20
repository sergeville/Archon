import { FlaskConical, Play, RotateCcw } from "lucide-react";
import { cn } from "../../../lib/utils";
import { useTestRunner } from "../hooks/useTestRunner";
import type { SuiteName } from "../types";
import { TestItemRow } from "./TestItemRow";

const SUITES: { value: SuiteName; label: string }[] = [
  { value: "mcp_server", label: "MCP Server (201 tests)" },
  { value: "embedding", label: "Embedding" },
  { value: "rag", label: "RAG" },
  { value: "all", label: "All Tests" },
];

export function TestRunnerView() {
  const { tests, summary, isRunning, selectedSuite, setSelectedSuite, run, reset } = useTestRunner();

  const passed = summary?.passed ?? tests.filter((t) => t.status === "passed").length;
  const failed = summary?.failed ?? tests.filter((t) => t.status === "failed").length;
  const skipped = summary?.skipped ?? tests.filter((t) => t.status === "skipped").length;
  const running = tests.filter((t) => t.status === "running").length;
  const total = tests.length;

  return (
    <div className="flex flex-col h-full gap-4 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FlaskConical className="h-6 w-6 text-blue-400" />
        <h1 className="text-xl font-semibold text-zinc-100">Test Runner</h1>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={selectedSuite}
          onChange={(e) => {
            setSelectedSuite(e.target.value as SuiteName);
            reset();
          }}
          disabled={isRunning}
          className={cn(
            "bg-zinc-900 border border-zinc-700 text-zinc-200 text-sm rounded-lg px-3 py-2",
            "focus:outline-none focus:ring-1 focus:ring-blue-500",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          {SUITES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>

        <button
          onClick={run}
          disabled={isRunning}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
            "bg-blue-600 hover:bg-blue-500 text-white",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "shadow-[0_0_15px_-3px_rgba(59,130,246,0.5)]",
          )}
        >
          <Play className="h-4 w-4" />
          {isRunning ? "Running…" : "Run Tests"}
        </button>

        {tests.length > 0 && !isRunning && (
          <button
            onClick={reset}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-all"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
        )}
      </div>

      {/* Stats bar */}
      {total > 0 && (
        <div className="flex items-center gap-4 text-sm">
          <span className="text-zinc-500">
            Total: <span className="text-zinc-300 font-mono">{total}</span>
          </span>
          {running > 0 && (
            <span className="text-blue-400 font-mono animate-pulse">{running} running</span>
          )}
          {passed > 0 && (
            <span className="text-green-400">
              ✓ <span className="font-mono">{passed}</span> passed
            </span>
          )}
          {failed > 0 && (
            <span className="text-red-400">
              ✗ <span className="font-mono">{failed}</span> failed
            </span>
          )}
          {skipped > 0 && (
            <span className="text-yellow-400">
              △ <span className="font-mono">{skipped}</span> skipped
            </span>
          )}
          {summary?.duration !== undefined && (
            <span className="text-zinc-500 ml-auto">{summary.duration}s</span>
          )}
        </div>
      )}

      {/* Test list */}
      {tests.length > 0 ? (
        <div className="flex-1 overflow-y-auto space-y-1 pr-1">
          {tests.map((test) => (
            <TestItemRow key={test.id} test={test} />
          ))}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-zinc-500 space-y-2">
            <FlaskConical className="h-12 w-12 mx-auto opacity-30" />
            <p className="text-sm">Select a suite and click Run Tests</p>
          </div>
        </div>
      )}
    </div>
  );
}
