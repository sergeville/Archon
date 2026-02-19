/**
 * SessionsView Component
 *
 * Main view for displaying and managing agent sessions
 * Shows active and recent sessions with filtering options
 */

import { useState } from "react";
import { Activity, Filter, Search, TrendingUp } from "lucide-react";
import { useSessions } from "../hooks/useSessionQueries";
import { SessionRow, SessionDetailModal } from "../components";
import { Button } from "@/features/ui/primitives/button";
import { Input } from "@/features/ui/primitives/input";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/features/ui/primitives/select";
import type { SessionFilterOptions } from "../types";

export function SessionsView() {
  const [filters, setFilters] = useState<SessionFilterOptions>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  const { data: sessions = [], isLoading, error } = useSessions(filters);

  // Filter sessions by search query
  const filteredSessions = sessions.filter((session) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      session.agent.toLowerCase().includes(query) ||
      session.id.toLowerCase().includes(query) ||
      session.summary?.toLowerCase().includes(query)
    );
  });

  // Separate active and completed sessions
  const activeSessions = filteredSessions.filter((s) => !s.ended_at);
  const completedSessions = filteredSessions.filter((s) => s.ended_at);

  const handleFilterChange = (key: keyof SessionFilterOptions, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === "all" ? undefined : value,
    }));
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-400 text-sm">Failed to load sessions</p>
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
            <Activity className="h-6 w-6 text-cyan-400" />
            Sessions
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Track agent work sessions and task progress
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-sm text-gray-400">
            <span className="text-cyan-400 font-bold">{activeSessions.length}</span>{" "}
            active
          </div>
          <div className="text-sm text-gray-400">
            <span className="text-gray-300 font-bold">{completedSessions.length}</span>{" "}
            completed
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search sessions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Agent Filter */}
        <Select
          value={filters.agent || "all"}
          onValueChange={(value) => handleFilterChange("agent", value)}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Agents</SelectItem>
            <SelectItem value="claude">Claude</SelectItem>
            <SelectItem value="gemini">Gemini</SelectItem>
            <SelectItem value="gpt">GPT</SelectItem>
            <SelectItem value="user">User</SelectItem>
          </SelectContent>
        </Select>

        {/* Timeframe Filter */}
        <Select
          value={filters.timeframe || "all"}
          onValueChange={(value) => handleFilterChange("timeframe", value)}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Time</SelectItem>
            <SelectItem value="24h">Last 24 Hours</SelectItem>
            <SelectItem value="7days">Last 7 Days</SelectItem>
            <SelectItem value="30days">Last 30 Days</SelectItem>
          </SelectContent>
        </Select>

        {/* Clear Filters */}
        {(filters.agent || filters.timeframe || searchQuery) && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setFilters({});
              setSearchQuery("");
            }}
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-8 w-8 text-cyan-400 animate-pulse mx-auto mb-2" />
            <p className="text-gray-400 text-sm">Loading sessions...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredSessions.length === 0 && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No sessions found</p>
            <p className="text-gray-500 text-sm mt-1">
              {searchQuery || filters.agent || filters.timeframe
                ? "Try adjusting your filters"
                : "Sessions will appear here as agents work"}
            </p>
          </div>
        </div>
      )}

      {/* Active Sessions */}
      {!isLoading && activeSessions.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-cyan-400" />
            <h2 className="text-lg font-semibold text-white">Active Sessions</h2>
            <span className="text-xs text-gray-400">({activeSessions.length})</span>
          </div>
          <div className="space-y-1">
            {activeSessions.map((session) => (
              <SessionRow
                key={session.id}
                session={session}
                onClick={() => setSelectedSessionId(session.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Completed Sessions */}
      {!isLoading && completedSessions.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <h2 className="text-lg font-semibold text-white">Completed Sessions</h2>
            <span className="text-xs text-gray-400">({completedSessions.length})</span>
          </div>
          <div className="space-y-1">
            {completedSessions.map((session) => (
              <SessionRow
                key={session.id}
                session={session}
                onClick={() => setSelectedSessionId(session.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Session Detail Modal */}
      {selectedSessionId && (
        <SessionDetailModal
          sessionId={selectedSessionId}
          onClose={() => setSelectedSessionId(null)}
        />
      )}
    </div>
  );
}
