# Pattern Harvesting Best Practices

This guide explains when, what, and how agents should harvest patterns in Archon's shared memory system.

## What is Pattern Harvesting?

Pattern harvesting is the act of capturing a reusable lesson from a specific work experience and storing it in Archon's knowledge base. Patterns persist across sessions and are shared between agents — a pattern learned by Claude is immediately available to Gemini and GPT.

**A pattern answers:** *"Given a situation like this, do this thing, because it produces this outcome."*

## MCP Tools for Pattern Harvesting

### `manage_pattern` (action: "harvest")
Create a new pattern from an experience:
```
manage_pattern(
    action="harvest",
    pattern_type="technical",          # success | failure | technical | process
    domain="database",                 # application domain
    description="Index FK columns before running JOIN-heavy migrations",
    action="Create B-tree index on foreign key columns before migration",
    outcome="Migration time dropped from 45min to 3min",
    context={"technology": "PostgreSQL", "table_size": "10M rows"}
)
```

### `find_patterns` (with query)
Search for relevant patterns semantically:
```
find_patterns(query="database migration slow", domain="database", limit=5)
```

### `manage_pattern` (action: "observe")
Record the outcome of applying a pattern:
```
manage_pattern(
    action="observe",
    pattern_id="uuid-here",
    success_rating=4,     # 1=failed, 5=worked perfectly
    feedback="Worked but needed to also ANALYZE TABLE afterward"
)
```

## When to Harvest a Pattern

### Harvest when:
- **Something unexpectedly worked well** — capture the exact approach while fresh
- **Something failed** — document what to avoid and why
- **A non-obvious technique produced good results** — if you needed to figure it out, others will too
- **A repeated workflow proved effective** — multi-step processes that consistently work
- **An error had a specific, reusable fix** — "When X error appears, do Y"

### Don't harvest when:
- The situation is too specific to this exact task ("fix bug in file foo.py line 42")
- It's an obvious best practice that any competent developer already knows
- You don't have enough signal to know if it actually worked
- The pattern only makes sense with context that won't be available to other agents

## Pattern Quality Checklist

A good pattern is:

**Reusable** — Another agent, tomorrow, on a different project, could apply it.
> ✅ "When PostgreSQL query plans choose SeqScan over IndexScan on large tables, run ANALYZE TABLE to update statistics"
> ❌ "Run ANALYZE on archon_tasks table"

**Actionable** — The `action` field tells you exactly what to do.
> ✅ "Create B-tree index on foreign key columns before running JOIN-heavy migrations"
> ❌ "Use indexes"

**Specific enough** — General platitudes don't help.
> ✅ "Set `maintenance_work_mem = '256MB'` before CREATE INDEX on tables >1M rows"
> ❌ "Optimize database performance"

**Honest about confidence** — Don't harvest speculative patterns.
> Only harvest after you've seen the outcome, not just hypothesized it.

## Pattern Types

| Type | Use for | Example |
|------|---------|---------|
| `success` | Approaches that worked well | "Chunked API requests in batches of 50 prevented rate limiting" |
| `failure` | Antipatterns to avoid | "Never use TRUNCATE during live traffic — use soft delete instead" |
| `technical` | Specific technical implementations | "Use LATERAL JOIN instead of correlated subquery for 10x speedup" |
| `process` | Workflow and methodology | "Run migration on staging 24h before production to catch data issues" |

## Harvesting from Session End

The most reliable time to harvest patterns is when ending a session. After completing a significant piece of work:

1. Reflect on what worked and what didn't
2. Call `manage_session(action="end", session_id="...", summary="...")`
   - The summary triggers AI-powered pattern extraction automatically
3. Review the extracted candidates via `find_patterns(domain="...")`
4. Record observations on patterns you've used: `manage_pattern(action="observe", ...)`

## Domain Vocabulary

Use consistent domain names to make patterns findable across agents:

| Domain | Covers |
|--------|--------|
| `database` | PostgreSQL, migrations, queries, indexing |
| `api` | REST design, rate limiting, authentication |
| `development` | Code structure, refactoring, debugging |
| `testing` | Test strategies, fixtures, coverage |
| `deployment` | Docker, CI/CD, environments |
| `management` | Task planning, agent coordination |
| `security` | Auth, secrets, CVEs, permissions |

## Context Field Usage

The `context` field captures environmental conditions that affect applicability:

```json
{
    "technology": "PostgreSQL 15",
    "scale": "large (>1M rows)",
    "environment": "production",
    "constraint": "zero-downtime deployment required"
}
```

This allows future semantic search to surface patterns relevant to the current context.

## Pattern Lifecycle

1. **Harvest** → Pattern created with `confidence: null` in metadata
2. **Observe** → Each use adds an observation with success_rating (1-5)
3. **Confidence grows** → Service calculates confidence from observation history
4. **Retire** → Outdated patterns can be removed via `manage_pattern(action="delete")`

## Anti-patterns (What NOT to Do)

- **Over-harvesting**: Don't capture every small decision. Aim for 1-3 high-value patterns per session.
- **Vague descriptions**: "Be careful with databases" is useless. Be specific.
- **Stale patterns**: If you find a pattern that no longer applies, record a failure observation to lower its confidence.
- **Duplicate harvesting**: Search first with `find_patterns(query="...")` before creating a new one.

## Example: Complete Harvest Workflow

```
# 1. Check for existing patterns before starting work
find_patterns(query="docker networking containers", domain="deployment")

# 2. Do the work...

# 3. After solving a tricky issue, harvest the pattern
manage_pattern(
    action="harvest",
    pattern_type="technical",
    domain="deployment",
    description="Connect Docker containers on different networks by adding both network names",
    action="Run docker network connect <network2> <container> and declare both networks in compose",
    outcome="Archon server could reach Ollama container across network boundary",
    context={"technology": "Docker Compose", "scenario": "cross-network service discovery"}
)

# 4. End session with summary to trigger auto-extraction
manage_session(action="end", session_id="...", summary="Connected Archon to Ollama across Docker networks")

# 5. Record observation after verifying the pattern persisted correctly
manage_pattern(action="observe", pattern_id="...", success_rating=5)
```
