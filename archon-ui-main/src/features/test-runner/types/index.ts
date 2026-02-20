export type TestStatus = "pending" | "running" | "passed" | "failed" | "skipped" | "error";

export interface TestItem {
  id: string;
  name: string;
  path: string;
  status: TestStatus;
}

export interface TestSummary {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration?: number;
}

export type SuiteName = "mcp_server" | "embedding" | "rag" | "all";

export interface CollectResponse {
  suite: string;
  tests: Array<{ id: string; name: string; path: string }>;
  count: number;
}

export interface RunResponse {
  run_id: string;
}
