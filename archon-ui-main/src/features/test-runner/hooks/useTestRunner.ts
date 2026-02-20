import { useCallback, useRef, useState } from "react";
import { API_BASE_URL } from "../../../config/api";
import { testRunnerService } from "../services/testRunnerService";
import type { SuiteName, TestItem, TestStatus, TestSummary } from "../types";

interface UseTestRunnerReturn {
  tests: TestItem[];
  summary: TestSummary | null;
  isRunning: boolean;
  selectedSuite: SuiteName;
  setSelectedSuite: (suite: SuiteName) => void;
  collect: () => Promise<void>;
  run: () => Promise<void>;
  reset: () => void;
}

export function useTestRunner(): UseTestRunnerReturn {
  const [tests, setTests] = useState<TestItem[]>([]);
  const [summary, setSummary] = useState<TestSummary | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedSuite, setSelectedSuite] = useState<SuiteName>("mcp_server");
  const esRef = useRef<EventSource | null>(null);

  const collect = useCallback(async () => {
    const data = await testRunnerService.collect(selectedSuite);
    setTests(
      data.tests.map((t) => ({ id: t.id, name: t.name, path: t.path, status: "pending" as TestStatus }))
    );
    setSummary(null);
  }, [selectedSuite]);

  const run = useCallback(async () => {
    if (isRunning) return;

    // Collect first if no tests loaded yet
    let currentTests = tests;
    if (currentTests.length === 0) {
      const data = await testRunnerService.collect(selectedSuite);
      currentTests = data.tests.map((t) => ({
        id: t.id,
        name: t.name,
        path: t.path,
        status: "pending" as TestStatus,
      }));
    }

    // Set all to "running"
    setTests(currentTests.map((t) => ({ ...t, status: "running" })));
    setSummary(null);
    setIsRunning(true);

    const { run_id } = await testRunnerService.startRun(selectedSuite);

    // Close any prior stream
    esRef.current?.close();

    const es = new EventSource(`${API_BASE_URL}/test-runner/stream/${run_id}`);
    esRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "test_result") {
        setTests((prev) =>
          prev.map((t) => (t.id === data.id ? { ...t, status: data.status as TestStatus } : t))
        );
      } else if (data.type === "summary") {
        setSummary({
          total: data.total,
          passed: data.passed,
          failed: data.failed,
          skipped: data.skipped,
          duration: data.duration,
        });
        setIsRunning(false);
        es.close();
      } else if (data.type === "error") {
        setIsRunning(false);
        es.close();
      }
    };

    es.onerror = () => {
      setIsRunning(false);
      es.close();
    };
  }, [isRunning, tests, selectedSuite]);

  const reset = useCallback(() => {
    esRef.current?.close();
    setTests([]);
    setSummary(null);
    setIsRunning(false);
  }, []);

  return { tests, summary, isRunning, selectedSuite, setSelectedSuite, collect, run, reset };
}
