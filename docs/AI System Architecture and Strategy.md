# AI System Architecture & Strategy Review
**Date:** 2026-02-20
**Purpose:** Critical assessment of the Unified System Vision + concrete strategic suggestions
**Reviewing:** `Documentation/System/UNIFIED_SYSTEM_VISION.md`

---

## Assessment: The Good, The Bad, and The Brutal

### The Good — The "Skeleton" Realization

The document correctly identifies that Serge is not building apps — he is building an **Agentic Operating System (AOS)**.

- The **Situation Agent** is the most valuable insight. Without it, the human is the bottleneck. With it, the system becomes a partner.
- The **Validation Council** addresses the hallucination/destruction risk that plagues autonomous agents. It moves the system from *scripting* to *governance*.

### The Bad — The Archon Disconnect

The document admits Archon (the supposed "Brain") is 85% built but is currently tracking old data from January.

- **The Risk:** If the brain's memory is stale, the Validation Council will make decisions based on false premises.
- **The Verdict:** A high-tech system built on placeholder data is not a system — it's a demo.

### The Brutal — The Manual Work Order Bottleneck

A complex execution engine exists (Agent Work Orders), but every order is created manually.

- **The Reality:** Manual work order creation is a glorified, slower version of running terminal commands yourself.
- **Until** the Situation Agent → Work Order pipeline is automated, this system is a tax on productivity, not a boost.

---

## Strategic Suggestions

### A. Context Injection Protocol (Immediate)

Before building the Situation Agent, build a grounding script.

**`sync_context.py`** — a utility that:
1. Scrapes all active `.md` plans from `Documentation/System/` and `Projects/*/docs/`
2. Injects their contents into Archon's `shared_context` key-value store
3. Runs before every Situation Agent session

**Why this matters:** The Situation Agent is only as good as its RAG source. If the plans live in `.md` files that agents can't easily query, the agent is reasoning blind. `sync_context.py` is the bridge.

```python
# Pseudocode — sync_context.py
plan_dirs = [
    "~/Documents/Documentation/System/",
    "~/Documents/Projects/*/docs/",
]
for plan_file in find_markdown_files(plan_dirs):
    content = read(plan_file)
    archon_client.set_shared_context(
        key=f"plan:{plan_file.stem}",
        value=content,
        source="sync_context"
    )
```

### B. Risk-Based Validation Gating

Don't run the full Validation Council for every action. Tier by consequence.

| Risk Level | Trigger | Council Behavior |
|------------|---------|-----------------|
| `LOW` | Read-only, documentation, notes | Auto-approve, log only |
| `MED` | Code changes, config edits | Logic Validator + Impact Analyzer |
| `HIGH` | Deletions, cloud config, migrations | Full council (all 3 agents) |
| `DESTRUCTIVE` | DB drops, force-push, rm -rf | Full council + human MFA gate |

Add `risk_level: LOW | MED | HIGH | DESTRUCTIVE` as a required field on every Work Order. The system auto-escalates based on the field value. The human can never be bypassed for `DESTRUCTIVE`.

### C. Hardware-Awareness for Alfred

Alfred currently treats all output the same regardless of context. Since the environment includes an iPhone and MacBook Air, Alfred should route output intelligently.

**Rule:** If MacBook Air is open and active → send silent notification to screen, not TTS in the room.

Implementation: Alfred checks MacBook Air presence (via mDNS or Home Assistant network scanner) before deciding output channel. This is one config check, not a new system.

**Broader principle:** The Validation Council's **Context Agent** should include device context. "Is the user's primary device nearby and active?" is a valid validation input.

---

## Revised Implementation Order

The original Phase A has A1 (real work in Archon) before A2 (Unified Audit Log). This order is wrong. You cannot log what you aren't tracking. Revised:

**Step 0 — The Cleanup (do this first, 30 minutes)**
Purge the stale January Alfred/HA setup tasks from Archon. That data is toxic noise — it gives the Situation Agent false signals about system state.

**Step 1 — The Pulse (Unified Audit Log)**
Initialize `unified_audit_log` in the Archon database. Without the heartbeat visible, you are flying blind.

**Step 2 — The Grounding (sync_context.py)**
Load all active `.md` plans into Archon's `shared_context`. This is the prerequisite for the Situation Agent having complete information.

**Step 3 — The Awakening (Situation Agent, read-only)**
Deploy `/situation` as a read-only advisor. It reads, synthesizes, and recommends — but does not yet auto-execute. Human reviews and approves.

**Step 4 — The Governance (Validation Council)**
Wire all work orders through the council. Build port 8054. Add `risk_level` to all work orders.

---

## The Governance Mandate (Condensed)

- **No ghost actions.** Every agent action exists in the Unified Audit Log.
- **Validation before execution.** High-risk work orders require council consensus.
- **Context before synthesis.** `sync_context.py` runs before every Situation Agent session.
- **Hardware aware.** Alfred routes output based on which device is active.
- **Stale data is a bug.** Archon memory must be current or decisions are invalid.

---

*The architecture is correct. The gaps are named. The only remaining question is sequence.*
