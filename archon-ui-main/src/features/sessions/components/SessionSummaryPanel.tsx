/**
 * SessionSummaryPanel Component
 *
 * Displays AI-generated session summary with structured insights:
 * - Key events that occurred
 * - Decisions made
 * - Outcomes achieved
 * - Next steps recommended
 */

import { formatDistanceToNow } from "date-fns";
import { ArrowRight, CheckCircle2, Lightbulb, Sparkles, TrendingUp } from "lucide-react";
import { Card } from "@/features/ui/primitives/card";
import type { SessionMetadata } from "../types";

interface SessionSummaryPanelProps {
  summary: string;
  metadata: SessionMetadata;
}

export function SessionSummaryPanel({ summary, metadata }: SessionSummaryPanelProps) {
  const aiSummary = metadata?.ai_summary;

  return (
    <Card className="p-4 bg-gradient-to-br from-cyan-500/10 via-blue-500/10 to-purple-500/10 border-cyan-500/30">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-cyan-400" />
            <h3 className="text-lg font-semibold text-white">AI Summary</h3>
          </div>
          {aiSummary?.summarized_at && (
            <span className="text-xs text-gray-400">
              {formatDistanceToNow(new Date(aiSummary.summarized_at), { addSuffix: true })}
            </span>
          )}
        </div>

        {/* Main Summary Text */}
        <p className="text-sm text-gray-300 leading-relaxed">{summary}</p>

        {/* Structured Insights */}
        {aiSummary && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {/* Key Events */}
            {aiSummary.key_events && aiSummary.key_events.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-cyan-400">
                  <CheckCircle2 className="h-4 w-4" />
                  <span className="text-sm font-medium">Key Events</span>
                </div>
                <ul className="space-y-1">
                  {aiSummary.key_events.map((event) => (
                    <li key={event} className="flex items-start gap-2 text-xs text-gray-400">
                      <span className="text-cyan-400 mt-1">•</span>
                      <span className="flex-1">{event}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Decisions */}
            {aiSummary.decisions && aiSummary.decisions.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-blue-400">
                  <Lightbulb className="h-4 w-4" />
                  <span className="text-sm font-medium">Decisions Made</span>
                </div>
                <ul className="space-y-1">
                  {aiSummary.decisions.map((decision) => (
                    <li key={decision} className="flex items-start gap-2 text-xs text-gray-400">
                      <span className="text-blue-400 mt-1">•</span>
                      <span className="flex-1">{decision}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Outcomes */}
            {aiSummary.outcomes && aiSummary.outcomes.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-green-400">
                  <TrendingUp className="h-4 w-4" />
                  <span className="text-sm font-medium">Outcomes</span>
                </div>
                <ul className="space-y-1">
                  {aiSummary.outcomes.map((outcome) => (
                    <li key={outcome} className="flex items-start gap-2 text-xs text-gray-400">
                      <span className="text-green-400 mt-1">•</span>
                      <span className="flex-1">{outcome}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Next Steps */}
            {aiSummary.next_steps && aiSummary.next_steps.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-purple-400">
                  <ArrowRight className="h-4 w-4" />
                  <span className="text-sm font-medium">Next Steps</span>
                </div>
                <ul className="space-y-1">
                  {aiSummary.next_steps.map((step, index) => (
                    <li key={step} className="flex items-start gap-2 text-xs text-gray-400">
                      <span className="text-purple-400 mt-1">{index + 1}.</span>
                      <span className="flex-1">{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
