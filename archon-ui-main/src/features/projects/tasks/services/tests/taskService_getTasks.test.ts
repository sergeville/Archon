import { describe, expect, it, vi } from "vitest";
import { callAPIWithETag } from "../../../../shared/api/apiClient";
import type { Task } from "../../types";
import { taskService } from "../taskService";

// Mock the API call
vi.mock("../../../../shared/api/apiClient", () => ({
  callAPIWithETag: vi.fn(),
}));

describe("taskService.getTasks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockTasks: Task[] = [
    {
      id: "task-1",
      project_id: "project-123",
      title: "Task 1",
      description: "Description 1",
      status: "todo",
      assignee: "User",
      task_order: 50,
      priority: "low",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
  ];

  const mockResponse = {
    tasks: mockTasks,
    pagination: {
      total: 1,
      page: 1,
      per_page: 10,
      pages: 1,
    },
  };

  it("should fetch tasks with no params", async () => {
    (callAPIWithETag as any).mockResolvedValueOnce(mockResponse);

    const result = await taskService.getTasks();

    expect(callAPIWithETag).toHaveBeenCalledWith("/api/tasks?");
    expect(result).toEqual(mockResponse);
  });

  it("should fetch tasks with params", async () => {
    (callAPIWithETag as any).mockResolvedValueOnce(mockResponse);

    await taskService.getTasks({ status: "todo", per_page: 100 });

    // Check specific params presence
    const lastCall = (callAPIWithETag as any).mock.calls[0];
    const url = lastCall[0];

    expect(url).toContain("/api/tasks?");
    expect(url).toContain("status=todo");
    expect(url).toContain("per_page=100");
  });
});
