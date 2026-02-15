/**
 * SessionsPage
 *
 * Page container for agent sessions tracking.
 * Displays active and completed work sessions from all agents.
 */

import { SessionsView } from "@/features/sessions/views/SessionsView";

export function SessionsPage() {
  return (
    <div className="container mx-auto p-6">
      <SessionsView />
    </div>
  );
}
