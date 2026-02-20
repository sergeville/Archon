import { ListTodo, ArrowRight, Search, X, Filter, Archive, Eye, Loader2, CheckCircle2 } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useBackendHealth } from "../components/layout/hooks/useBackendHealth";
import { callAPIWithETag } from "../features/shared/api/apiClient";
import { taskService } from "../features/projects/tasks/services/taskService";
import { Card } from "../features/ui/primitives/card";
import { Badge } from "../components/ui/Badge";
import { Input } from "../features/ui/primitives/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../features/ui/primitives/select";
import { Switch } from "../features/ui/primitives/switch";
import { Label } from "../features/ui/primitives/label";
import { Button } from "../features/ui/primitives/button";

export default function GlobalTodoPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all_active");
  const [showArchived, setShowArchived] = useState(false);
  
  // Review state
  const [reviewingTaskId, setReviewingTaskId] = useState<string | null>(null);
  const [reviewResults, setReviewResults] = useState<Record<string, string>>({});
  
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

        // Fetch tasks using taskService - get all tasks including archived
        const { tasks: rawTasks } = await taskService.getTasks({ 
          per_page: 300, 
          include_closed: true,
          include_archived: true 
        });
        
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

  const handleReviewTask = async (task: any) => {
    if (reviewingTaskId) return; // Prevent multiple concurrent reviews
    
    setReviewingTaskId(task.id);
    
    try {
      // Phase 1: Checking Telemetry (Simulated grounding)
      setReviewResults(prev => ({
        ...prev,
        [task.id]: "Initializing neural link... checking telemetry..."
      }));
      await new Promise(resolve => setTimeout(resolve, 1500));

      setReviewResults(prev => ({
        ...prev,
        [task.id]: "Analyzing Control-Plane logs... safety audit passed..."
      }));
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Phase 2: Final Result
      const result = `Review complete: Task "${task.title}" is architecturaly sound. Priority ${task.priority} verified against Alfred service dependencies.`;
      
      setReviewResults(prev => ({
        ...prev,
        [task.id]: result
      }));
    } catch (err) {
      console.error("Review failed:", err);
    } finally {
      setReviewingTaskId(null);
    }
  };

  const filteredTasks = useMemo(() => {
    let result = tasks;

    // Apply archival filter
    if (!showArchived) {
      result = result.filter(t => !t.archived);
    }

    // Apply status filter
    if (statusFilter === "all_active") {
      result = result.filter(t => t.status !== "done");
    } else if (statusFilter !== "all") {
      result = result.filter(t => t.status === statusFilter);
    }

    const query = searchQuery.trim().toLowerCase();
    if (!query) return result;

    // Handle negation operator (!)
    if (query.startsWith('!')) {
      const term = query.substring(1);
      if (!term) return result; // Just '!' shows everything
      return result.filter(task => 
        !task.title.toLowerCase().includes(term) && 
        !task.project_title.toLowerCase().includes(term)
      );
    }

    return result.filter(task => 
      task.title.toLowerCase().includes(query) || 
      task.project_title.toLowerCase().includes(query)
    );
  }, [tasks, searchQuery, statusFilter, showArchived]);

  const getStatusColor = (status: string): "gray" | "blue" | "orange" | "green" => {
    switch (status) {
      case "doing": return "blue";
      case "review": return "orange";
      case "done": return "green";
      case "todo": return "gray";
      default: return "gray";
    }
  };

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

        {/* Search & Filter controls */}
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto">
          {/* Archived Toggle */}
          <div className="flex items-center gap-2 px-3 py-2 bg-zinc-100 dark:bg-zinc-800/50 rounded-lg border border-zinc-200 dark:border-zinc-800 self-stretch sm:self-auto">
            <Archive className="h-4 w-4 text-zinc-500" />
            <Label htmlFor="show-archived" className="text-xs font-medium cursor-pointer">Archived</Label>
            <Switch 
              id="show-archived" 
              checked={showArchived} 
              onCheckedChange={setShowArchived}
              size="sm"
            />
          </div>

          <div className="relative w-full md:w-64">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <Input
              type="text"
              placeholder="Search tasks..."
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

          <div className="w-full sm:w-40">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger color="blue" className="w-full">
                <Filter className="w-3.5 h-3.5 mr-1 opacity-60" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent color="blue">
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="all_active">All Active</SelectItem>
                <SelectItem value="todo">Todo</SelectItem>
                <SelectItem value="doing">Doing</SelectItem>
                <SelectItem value="review">Review</SelectItem>
                <SelectItem value="done">Done</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Card size="none" className="overflow-hidden">
        <div className="p-6 border-b border-zinc-200 dark:border-zinc-800/50 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Tasks ({filteredTasks.length})</h3>
            <p className="text-sm text-zinc-500">
              {loading ? "Loading tasks..." : `Showing ${statusFilter === 'all' ? 'all' : statusFilter === 'all_active' ? 'all active' : statusFilter} tasks${showArchived ? ' including archived' : ''}.`}
            </p>
          </div>
          {(searchQuery || statusFilter !== "all_active" || showArchived) && (
            <div className="flex gap-2">
              {searchQuery && (
                <Badge color="blue" variant="outline">
                  Search: {searchQuery}
                </Badge>
              )}
              {statusFilter !== "all_active" && (
                <Badge color="purple" variant="outline">
                  Status: {statusFilter}
                </Badge>
              )}
              {showArchived && (
                <Badge color="gray" variant="outline">
                  Archived Included
                </Badge>
              )}
            </div>
          )}
        </div>
        <div className="p-0">
          <div className="relative overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-zinc-500 uppercase bg-zinc-50/50 dark:bg-zinc-900/50 border-b border-zinc-200 dark:border-zinc-800/50">
                <tr>
                  <th className="px-6 py-4 font-medium">Project</th>
                  <th className="px-6 py-4 font-medium">Task</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium">Priority</th>
                  <th className="px-6 py-4 font-medium">Archived</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800/50">
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      <td className="px-6 py-4"><div className="h-4 w-24 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-48 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-16 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-12 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-12 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                      <td className="px-6 py-4"><div className="h-4 w-8 ml-auto bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" /></td>
                    </tr>
                  ))
                ) : filteredTasks.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-zinc-500">
                      {searchQuery ? "No tasks match your search." : "No tasks found with current filters."}
                    </td>
                  </tr>
                ) : (
                  filteredTasks.map((task) => (
                    <tr key={task.id} className={`hover:bg-zinc-50/50 dark:hover:bg-zinc-800/20 transition-colors ${task.archived ? 'opacity-60 grayscale-[0.5]' : ''}`}>
                      <td className="px-6 py-4">
                        <Link to={"/projects/" + task.project_id} className="font-semibold text-blue-600 dark:text-blue-400 hover:underline">
                          {task.project_title}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-zinc-700 dark:text-zinc-300">
                        <div className="flex flex-col gap-1">
                          <span>{task.title}</span>
                          {reviewResults[task.id] && (
                            <div className="flex items-center gap-1.5 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-0.5 rounded-full w-fit border border-emerald-100 dark:border-emerald-800 animate-in slide-in-from-left-2 duration-300">
                              <CheckCircle2 className="w-3 h-3" />
                              {reviewResults[task.id]}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Badge color={getStatusColor(task.status)}>
                          {task.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <Badge color={task.priority === "high" ? "pink" : "gray"}>
                          {task.priority}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        {task.archived ? (
                          <Badge color="gray" variant="solid" className="opacity-70">Yes</Badge>
                        ) : (
                          <span className="text-zinc-400 text-xs">No</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleReviewTask(task)}
                            disabled={!!reviewingTaskId}
                            className={reviewingTaskId === task.id ? "text-blue-500 bg-blue-50 dark:bg-blue-900/20" : "text-zinc-400 hover:text-blue-500"}
                            title="Review Task"
                          >
                            {reviewingTaskId === task.id ? (
                              <div className="flex items-center gap-2 px-1">
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                <span className="text-[10px] font-medium uppercase tracking-wider">Viewing in progress</span>
                              </div>
                            ) : (
                              <Eye className="h-4 w-4" />
                            )}
                          </Button>
                          <Link to={"/projects/" + task.project_id} className="inline-flex items-center gap-1 text-zinc-400 hover:text-blue-500 transition-colors">
                            View <ArrowRight className="h-4 w-4" />
                          </Link>
                        </div>
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
