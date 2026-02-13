import { ListTodo, ArrowRight, Search, X } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useBackendHealth } from "../components/layout/hooks/useBackendHealth";
import { callAPIWithETag } from "../features/shared/api/apiClient";
import { taskService } from "../features/projects/tasks/services/taskService";
import { Card } from "../features/ui/primitives/card";
import { Badge } from "../components/ui/Badge";
import { Input } from "../features/ui/primitives/input";

export default function GlobalTodoPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const { data: healthData } = useBackendHealth();

  useEffect(() => {
    async function fetchData() {
      if (healthData?.status !== "healthy") {
        console.log("[DEBUG] Backend not healthy yet", healthData);
        return;
      }
      
      try {
        console.log("[DEBUG] Fetching data...");
        
        // Fetch projects to map project_id to project_title
        const projectsRes = await callAPIWithETag<any>("/api/projects");
        const projects = projectsRes.projects || [];
        const projectsMap = projects.reduce((acc: any, p: any) => {
          acc[p.id] = p.title;
          return acc;
        }, {});
        
        console.log("[DEBUG] Projects loaded:", projects.length);

        // Fetch tasks using taskService
        const { tasks: rawTasks } = await taskService.getTasks({ status: "todo", per_page: 100 });
        
        console.log("[DEBUG] Raw tasks loaded:", rawTasks.length);

        const mapped = rawTasks.map((t: any) => ({
          ...t,
          project_title: projectsMap[t.project_id] || "Unknown Project"
        }));

        setTasks(mapped);
        setError(null);
      } catch (err: any) {
        console.error("[DEBUG] Fetch error:", err);
        setError(err.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [healthData]);

  const filteredTasks = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return tasks;

    // Handle negation operator (!)
    if (query.startsWith('!')) {
      const term = query.substring(1);
      if (!term) return tasks; // Just '!' shows everything
      return tasks.filter(task => 
        !task.title.toLowerCase().includes(term) && 
        !task.project_title.toLowerCase().includes(term)
      );
    }

    return tasks.filter(task => 
      task.title.toLowerCase().includes(query) || 
      task.project_title.toLowerCase().includes(query)
    );
  }, [tasks, searchQuery]);

  if (error) {
    return <div className="p-8 text-red-500 font-mono">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto py-8 space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-500">
            <ListTodo className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Global Todo List</h1>
            <p className="text-zinc-500 dark:text-zinc-400">All pending tasks across all active projects.</p>
          </div>
        </div>

        {/* Search input */}
        <div className="relative w-full md:w-64">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-400" />
          <Input
            type="text"
            placeholder="Search tasks or projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-8"
            aria-label="Search tasks"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <Card size="none" className="overflow-hidden">
        <div className="p-6 border-b border-zinc-200 dark:border-zinc-800/50 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Open Tasks ({filteredTasks.length})</h3>
            <p className="text-sm text-zinc-500">
              {loading ? "Loading tasks..." : "Showing all tasks with 'todo' status."}
            </p>
          </div>
          {searchQuery && (
            <Badge color="blue" variant="outline">
              Filtered by: {searchQuery}
            </Badge>
          )}
        </div>
        <div className="p-0">
          <div className="relative overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-zinc-500 uppercase bg-zinc-50/50 dark:bg-zinc-900/50 border-b border-zinc-200 dark:border-zinc-800/50">
                <tr>
                  <th className="px-6 py-4 font-medium">Project</th>
                  <th className="px-6 py-4 font-medium">Task</th>
                  <th className="px-6 py-4 font-medium">Priority</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800/50">
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      <td className="px-6 py-4"><div className="h-4 w-24 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-48 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-12 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-8 ml-auto bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                    </tr>
                  ))
                ) : filteredTasks.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-zinc-500">
                      {searchQuery ? "No tasks match your search." : "No pending tasks found. All clear!"}
                    </td>
                  </tr>
                ) : (
                  filteredTasks.map((task) => (
                    <tr key={task.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-800/20 transition-colors">
                      <td className="px-6 py-4">
                        <Link to={"/projects/" + task.project_id} className="font-semibold text-blue-600 dark:text-blue-400 hover:underline">
                          {task.project_title}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-zinc-700 dark:text-zinc-300">
                        {task.title}
                      </td>
                      <td className="px-6 py-4">
                        <Badge color={task.priority === "high" ? "pink" : "gray"}>
                          {task.priority}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link to={"/projects/" + task.project_id} className="inline-flex items-center gap-1 text-zinc-400 hover:text-blue-500 transition-colors">
                          View <ArrowRight className="h-4 w-4" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  );
}
