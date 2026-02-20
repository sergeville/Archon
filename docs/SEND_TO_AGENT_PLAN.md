# Plan: Send to Agent — Project & Task Level

**Created:** 2026-02-20
**Status:** ACTIVE

---

## Overview

Add a "Send to Agent" capability to the Project page with two entry points, and a dedicated **Execution View** that appears once the agent starts — showing the project tasks alongside a live panel of what the agent is doing.

### Entry Points

1. **Project-level button** — in the project header. Sends all `todo`/`doing` tasks as a batch prompt.
2. **Task-level button** — on each `TaskCard`. Sends that single task as a targeted prompt.

### Execution View

After confirming in `SendToAgentModal`, instead of navigating away to `/agent-work-orders/{id}`, the project page **transitions into Execution View** at route `/projects/{projectId}/agent-run/{workOrderId}`:

- **Left panel** — project task list (simplified, read-only, no drag-drop)
- **Right panel** — live agent activity: streaming logs, current step, status indicator, link to full work order

**No backend changes required.** Pure frontend integration between Project Management and Agent Work Orders features.

---

## User Flow

### Project-level

1. User opens a project → clicks **"Run with Agent"** in the project header
2. `SendToAgentModal` opens, pre-filled with all `todo`/`doing` tasks
3. User picks a repository, reviews/edits the prompt, confirms
4. Work order created → page **transitions to Execution View** at `/projects/{projectId}/agent-run/{workOrderId}`
5. User sees tasks on the left, live agent activity on the right
6. When done, a "Back to Project" button returns to the normal project view

### Task-level

1. User hovers a `TaskCard` → clicks the **bot icon** button
2. Same `SendToAgentModal` opens, pre-filled for that single task
3. Same confirm flow → same Execution View (right panel shows the single task)

---

## Architecture

### New Files

| File | Purpose |
|------|---------|
| `src/features/projects/components/SendToAgentModal.tsx` | Modal: repo picker, prompt preview, workflow steps, submit |
| `src/features/projects/views/AgentExecutionView.tsx` | Split-panel execution view (tasks + live agent panel) |
| `src/features/projects/components/AgentActivityPanel.tsx` | Right panel: status, live logs, step progress, PR link |

### Modified Files

| File | Change |
|------|--------|
| `src/features/projects/views/ProjectsView.tsx` | Add "Run with Agent" button; swap to `AgentExecutionView` when `agentRunId` param is set |
| `src/features/projects/tasks/components/TaskCardActions.tsx` | Add bot-icon button + `onSendToAgent` prop |
| `src/features/projects/tasks/components/TaskCard.tsx` | Wire `onSendToAgent` prop through to actions |
| `src/App.tsx` | Add route `/projects/:projectId/agent-run/:workOrderId` |

---

## SendToAgentModal

### Props

```typescript
interface SendToAgentModalProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  tasks: Task[];   // 1 = task-level, many = project-level
}
```

### Sections

1. **Context** — read-only header: project name + task count (or single task title)
2. **Repository** — dropdown from `useRepositories()`. If none: "Configure a repository first →" link
3. **Workflow steps** — checkboxes: `create-branch` ✓, `planning` ✓, `execute` ✓, `commit` ✓, `create-pr` ✓, `prp-review` ☐
4. **Prompt** — textarea, pre-filled (see prompt templates below), fully editable
5. **Actions** — Cancel | **Start Agent** (primary, spinner while creating)

### Prompt Templates

**Project-level:**
```
Implement the following tasks for project "{projectName}":

1. {task.title} [{task.priority}]
   {task.description}

2. {task.title} [{task.priority}]
   {task.description}

Work through tasks in priority order (critical → high → medium → low).
Create a branch, implement each task, commit, and open a pull request.
```

**Task-level:**
```
Implement the following task from project "{projectName}":

Title: {task.title}
Priority: {task.priority}
Feature: {task.feature || "—"}

{task.description}

Create a branch, implement the task, commit, and open a pull request.
```

### On Submit

```typescript
const { agent_work_order_id } = await createWorkOrder({
  repository_id: selectedRepoId,
  repository_url: selectedRepo.url,
  sandbox_type: "git_worktree",
  user_request: promptText,
  selected_commands: selectedSteps,
});
navigate(`/projects/${projectId}/agent-run/${agent_work_order_id}`);
```

---

## Execution View (`AgentExecutionView`)

### Route

```
/projects/:projectId/agent-run/:workOrderId
```

Added in `App.tsx` alongside existing `/projects/:projectId/*` routes.

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Back to Project   [Project Name] — Running with Agent   [●Live]│
├──────────────────────────────┬──────────────────────────────────┤
│                              │                                  │
│   Project Tasks              │   Agent Activity                 │
│   (read-only, grouped by     │   (live panel)                   │
│    status / priority)        │                                  │
│                              │   ● Status: executing            │
│   ○ Task A [high]            │   ─────────────────              │
│   ○ Task B [medium]          │   ▶ create-branch  ✓             │
│   ○ Task C [low]             │   ▶ planning       ✓             │
│                              │   ▶ execute        ⟳ running     │
│                              │   ─────────────────              │
│                              │   [INFO] Creating branch...      │
│                              │   [INFO] Reading plan document   │
│                              │   [INFO] Implementing task A...  │
│                              │                                  │
│                              │   ─────────────────              │
│                              │   Open PR ↗  |  Full Details ↗   │
└──────────────────────────────┴──────────────────────────────────┘
```

### Left Panel — Task List

- Renders existing `TaskCard` components in **read-only mode** (no drag-drop, no action buttons)
- Grouped by status column (todo / doing / review / done) or flat list — flat list preferred for simplicity
- Polls task statuses via existing `useProjectTasks(projectId)` so cards update if the agent changes them
- Highlighted tasks (the ones sent to the agent) shown with a subtle cyan border

### Right Panel — `AgentActivityPanel`

```typescript
interface AgentActivityPanelProps {
  workOrderId: string;
  onViewFullDetails: () => void;  // navigate to /agent-work-orders/{id}
}
```

Sections (top to bottom):

1. **Status badge** — `pending` / `running` / `completed` / `failed` with color + spinner when running
2. **Workflow step progress** — ordered list of steps with ✓ done / ⟳ active / ○ pending icons. Reuse `StepHistoryCard` or build inline from `useWorkOrder(workOrderId)`
3. **Live log feed** — reuse `ExecutionLogs` component from `src/features/agent-work-orders/components/ExecutionLogs.tsx`. Connect via existing Zustand `sseSlice` (same as `AgentWorkOrderDetailView`). Pass `isLive={true}` while running
4. **Footer actions**:
   - "Open PR ↗" — shown when `github_pull_request_url` is available (opens in new tab)
   - "Full Details ↗" — navigates to `/agent-work-orders/{workOrderId}`
   - When completed/failed: "Back to Project" primary button

### SSE Connection

Reuse the existing Zustand SSE slice exactly as `AgentWorkOrderDetailView` does — subscribe to `workOrderId` on mount, unsubscribe on unmount. No new SSE infrastructure needed.

---

## UI Details

### "Run with Agent" Header Button

- Icon: `<Bot />` from lucide-react
- Label: "Run with Agent"
- Variant: `outline`
- Placement: right side of project header, before existing action menu
- Gated on: `agentWorkOrdersEnabled` from `useSettings()`

### Task Card Bot Button

- Icon: `<Bot />` same size as other action icons
- Tooltip: "Send to Agent"
- Color: teal/cyan (distinct from edit=cyan-lighter and delete=red)
- Placement: `TaskCardActions` between Edit and Delete
- Gated on: `agentWorkOrdersEnabled`

### "Back to Project" Navigation

- In the execution view header: `← Back to Project` link → `navigate(/projects/${projectId})`
- Also shown as a prominent button when the work order reaches `completed` or `failed`

---

## Reused Components & Hooks

| Component / Hook | From | Used For |
|---|---|---|
| `ExecutionLogs` | `agent-work-orders/components/` | Live log feed in right panel |
| `RealTimeStats` | `agent-work-orders/components/` | Step progress display |
| `StepHistoryCard` | `agent-work-orders/components/` | Step list with status icons |
| `sseSlice` (Zustand) | `agent-work-orders/state/slices/` | SSE EventSource management |
| `useWorkOrder(id)` | `agent-work-orders/hooks/` | Poll work order status |
| `useRepositories()` | `agent-work-orders/hooks/` | Populate repo dropdown |
| `useCreateWorkOrder()` | `agent-work-orders/hooks/` | Submit work order |
| `useProjectTasks(id)` | `projects/tasks/hooks/` | Task list in left panel |
| `useSettings()` | `contexts/SettingsContext` | Gate on `agentWorkOrdersEnabled` |
| `useNavigate()` | react-router-dom | Navigate to execution view |

---

## Implementation Sequence

1. **`SendToAgentModal.tsx`** — standalone modal, no navigation side effects
2. **`TaskCardActions.tsx` + `TaskCard.tsx`** — add bot button, wire prop
3. **`AgentActivityPanel.tsx`** — right panel (SSE + logs + step progress)
4. **`AgentExecutionView.tsx`** — split layout: task list left + `AgentActivityPanel` right
5. **`App.tsx`** — add route `/projects/:projectId/agent-run/:workOrderId`
6. **`ProjectsView.tsx`** — add header button + delegate to execution view when route matches

---

## Out of Scope

- Task checkbox selection (send a subset of project tasks) — follow-up
- Auto-marking tasks as `doing` / `done` as agent completes them — follow-up
- Multiple concurrent agent runs per project

---

## Verification

1. "Run with Agent" button appears in project header when `agentWorkOrdersEnabled=true`
2. Task cards show bot icon; clicking opens modal pre-filled for that task
3. Submitting modal navigates to `/projects/{projectId}/agent-run/{workOrderId}`
4. Execution view shows task list on left, live agent logs on right
5. Step progress updates as agent advances through workflow
6. "Open PR ↗" appears when agent creates a pull request
7. "Back to Project" restores normal project view
8. With `agentWorkOrdersEnabled=false`, no buttons appear
