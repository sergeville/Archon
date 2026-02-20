import { API_BASE_URL } from "../../../config/api";
import type { CollectResponse, RunResponse, SuiteName } from "../types";

export const testRunnerService = {
  async collect(suite: SuiteName): Promise<CollectResponse> {
    const res = await fetch(`${API_BASE_URL}/test-runner/collect?suite=${suite}`);
    if (!res.ok) throw new Error(`Collect failed: ${res.statusText}`);
    return res.json();
  },

  async startRun(suite: SuiteName): Promise<RunResponse> {
    const res = await fetch(`${API_BASE_URL}/test-runner/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ suite }),
    });
    if (!res.ok) throw new Error(`Start run failed: ${res.statusText}`);
    return res.json();
  },
};
