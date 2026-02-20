# Archon Performance Baseline Metrics

**Created**: 2026-02-18
**Project**: Shared Memory System Implementation - Phase 1
**Task**: Create Baseline Performance Metrics (Task 7)
**Test Run**: 2026-02-18T14:33:04

## Executive Summary

This document establishes performance baselines for the Archon system measured on 2026-02-18. These metrics provide a reference point for tracking performance improvements as the Shared Memory System (Phases 2-6) is implemented.

**Key Metrics**:
- **API Response Times**: P50: 4.6ms (health) to 6116ms (list projects)
- **Database Queries**: P50: 4.4ms (simple) to 411ms (paginated list)
- **Concurrent Load**: 3.3 requests/second with 100% success rate
- **Overall Success Rate**: 100% across all 260 test requests

## Test Configuration

**Environment**:
- API Base URL: `http://localhost:8181`
- Test Project: `7c3528df-b1a2-4fde-9fee-68727c15b6c6` (Shared Memory project)
- Test Date: 2026-02-18

**Test Parameters**:
- Single Request Iterations: 20 per endpoint
- Database Query Iterations: 30 per query (20 for large result sets)
- Concurrent Request Count: 10 simultaneous requests

**Testing Tool**: Python 3 with httpx.AsyncClient

## API Endpoint Performance

### Summary Table

| Endpoint | Iterations | P50 | P95 | P99 | Mean | Success Rate |
|----------|------------|-----|-----|-----|------|--------------|
| GET /api/health | 20 | 4.6ms | 15.7ms | 22.2ms | 5.4ms | 100.0% |
| GET /api/projects | 20 | 6115.9ms | 6940.6ms | 7025.0ms | 6213.0ms | 100.0% |
| GET /api/projects/{id} | 20 | 403.9ms | 476.2ms | 494.7ms | 405.7ms | 100.0% |
| GET /api/projects/{id}/tasks | 20 | 276.8ms | 843.6ms | 1192.4ms | 317.3ms | 100.0% |
| GET /api/tasks | 20 | 404.7ms | 620.1ms | 729.5ms | 422.4ms | 100.0% |
| GET /api/tasks (filtered) | 20 | 361.2ms | 719.7ms | 745.6ms | 412.1ms | 100.0% |
| GET /api/knowledge-items/summary | 20 | 928.3ms | 1102.7ms | 1122.4ms | 933.1ms | 100.0% |

### Detailed Results

#### 1. Health Check
**Endpoint**: `GET /api/health`
**Purpose**: Minimal DB access, system health validation

- **P50**: 4.6ms
- **P95**: 15.7ms
- **P99**: 22.2ms
- **Mean**: 5.4ms
- **Range**: 3.7ms - 16.1ms
- **Success Rate**: 100%

**Analysis**: Excellent performance for health checks. Sub-5ms median response.

#### 2. List Projects
**Endpoint**: `GET /api/projects`
**Purpose**: Retrieve all projects with full metadata

- **P50**: 6115.9ms
- **P95**: 6940.6ms
- **P99**: 7025.0ms
- **Mean**: 6213.0ms
- **Range**: 5809ms - 6946ms
- **Success Rate**: 100%

**Analysis**: ⚠️ **PERFORMANCE CONCERN** - Slowest endpoint by far. 6+ second median response time indicates optimization opportunity. Likely loading all project data including features arrays and metadata.

**Recommendation**: Implement pagination, reduce payload size, or add caching layer.

#### 3. Get Project by ID
**Endpoint**: `GET /api/projects/{id}`
**Purpose**: Retrieve single project details

- **P50**: 403.9ms
- **P95**: 476.2ms
- **P99**: 494.7ms
- **Mean**: 405.7ms
- **Range**: 368ms - 477ms
- **Success Rate**: 100%

**Analysis**: Acceptable performance for single project fetch. Consistent response times.

#### 4. Get Project Tasks
**Endpoint**: `GET /api/projects/{id}/tasks`
**Purpose**: Tasks scoped to specific project

- **P50**: 276.8ms
- **P95**: 843.6ms
- **P99**: 1192.4ms
- **Mean**: 317.3ms
- **Range**: 230ms - 864ms
- **Success Rate**: 100%

**Analysis**: Good median performance, but P95/P99 show occasional slowdowns. Variability suggests potential for query optimization.

#### 5. List All Tasks
**Endpoint**: `GET /api/tasks?include_closed=true`
**Purpose**: Global task list with closed tasks

- **P50**: 404.7ms
- **P95**: 620.1ms
- **P99**: 729.5ms
- **Mean**: 422.4ms
- **Range**: 379ms - 627ms
- **Success Rate**: 100%

**Analysis**: Consistent performance for global task list. Similar to filtered queries.

#### 6. List Tasks (Filtered)
**Endpoint**: `GET /api/tasks?status=todo&per_page=10`
**Purpose**: Filtered task list with pagination

- **P50**: 361.2ms
- **P95**: 719.7ms
- **P99**: 745.6ms
- **Mean**: 412.1ms
- **Range**: 331ms - 721ms
- **Success Rate**: 100%

**Analysis**: Slightly faster than unfiltered list. Filtering and pagination working effectively.

#### 7. Knowledge Items Summary
**Endpoint**: `GET /api/knowledge-items/summary?per_page=10`
**Purpose**: Knowledge base sources summary

- **P50**: 928.3ms
- **P95**: 1102.7ms
- **P99**: 1122.4ms
- **Mean**: 933.1ms
- **Range**: 808ms - 1104ms
- **Success Rate**: 100%

**Analysis**: Nearly 1-second response time. May involve aggregations or vector similarity calculations.

## Database Query Performance

### Summary Table

| Query Type | Iterations | P50 | P95 | P99 | Mean | Success Rate |
|------------|------------|-----|-----|-----|------|--------------|
| Simple query (health) | 30 | 4.4ms | 7.7ms | 11.5ms | 4.5ms | 100.0% |
| Single record fetch | 30 | 294.9ms | 6460.8ms | 6521.6ms | 765.7ms | 100.0% |
| Paginated list (20 items) | 30 | 410.8ms | 548.5ms | 612.5ms | 418.2ms | 100.0% |
| Filtered query | 30 | 370.0ms | 907.4ms | 1563.7ms | 434.6ms | 100.0% |
| Large result set (50 items) | 20 | 395.6ms | 738.2ms | 848.2ms | 449.7ms | 100.0% |

### Detailed Analysis

#### Simple Query (Health Check)
- **P50**: 4.4ms
- **P95**: 7.7ms
- **Mean**: 4.5ms
- **Analysis**: Baseline database access time. Excellent performance.

#### Single Record Fetch
- **P50**: 294.9ms
- **P95**: 6460.8ms ⚠️
- **P99**: 6521.6ms ⚠️
- **Mean**: 765.7ms
- **Analysis**: **MAJOR OUTLIERS** in P95/P99. Some single record fetches take 6+ seconds. Investigate query execution plans and indexing.

#### Paginated List Query
- **P50**: 410.8ms
- **P95**: 548.5ms
- **Mean**: 418.2ms
- **Analysis**: Consistent performance. Pagination working effectively.

#### Filtered Query
- **P50**: 370.0ms
- **P95**: 907.4ms
- **P99**: 1563.7ms
- **Mean**: 434.6ms
- **Analysis**: Some outliers in tail latencies. Filter optimization opportunity.

#### Large Result Set (50 items)
- **P50**: 395.6ms
- **P95**: 738.2ms
- **Mean**: 449.7ms
- **Analysis**: Performance scales reasonably with result set size.

## Concurrent Request Performance

**Test Setup**: 10 simultaneous requests to `GET /api/projects/{id}/tasks`

### Metrics

- **Total Time**: 3024.5ms
- **Requests Per Second**: 3.3 req/sec
- **Success Rate**: 100% (10/10 succeeded)
- **Latency P50**: 3023.2ms
- **Latency P95**: 3024.2ms
- **Latency P99**: 3024.4ms
- **Latency Mean**: 3022.8ms
- **Latency Range**: 3021ms - 3024ms

### Analysis

**Observations**:
- All requests completed in ~3 seconds with tight clustering (3ms variance)
- High consistency across all concurrent requests
- No failures or timeouts under concurrent load
- System handles concurrent requests with minimal latency variance

**Interpretation**: The system appears to process concurrent requests sequentially or with limited parallelism, resulting in uniform completion times. This is acceptable for current load but may become bottleneck under higher concurrency.

## Performance Patterns & Insights

### Outlier Analysis

**Critical Findings**:

1. **List Projects Endpoint** - Consistently slow (6+ seconds)
   - Affects user experience significantly
   - Should be prioritized for optimization
   - Consider: pagination, payload reduction, caching

2. **Single Record Fetch P95/P99** - Occasional 6+ second outliers
   - 95th percentile 20x slower than median
   - Suggests intermittent database performance issues
   - Investigate: query plans, indexes, connection pooling

3. **Knowledge Items Summary** - Nearly 1 second response
   - May involve complex aggregations or embeddings
   - Consider: materialized views, caching strategies

### Performance Tiers

Based on median (P50) response times:

- **Tier 1 (Excellent)**: < 10ms
  - Health check (4.6ms)

- **Tier 2 (Good)**: 10ms - 500ms
  - Get project by ID (403.9ms)
  - Get project tasks (276.8ms)
  - List tasks filtered (361.2ms)
  - List all tasks (404.7ms)

- **Tier 3 (Acceptable)**: 500ms - 1000ms
  - Knowledge items summary (928.3ms)

- **Tier 4 (Needs Improvement)**: > 1000ms
  - List projects (6115.9ms) ⚠️

### Consistency Analysis

**Most Consistent** (low P95/P50 ratio):
- Health check: 3.4x (15.7ms / 4.6ms)
- Get project by ID: 1.2x (476.2ms / 403.9ms)

**Most Variable** (high P95/P50 ratio):
- Single record fetch: 21.9x (6460.8ms / 294.9ms) ⚠️
- Get project tasks: 3.0x (843.6ms / 276.8ms)

## Baseline for Future Comparison

### Pre-Phase 2 State

This baseline represents the system **before** implementing:
- Session memory with vector embeddings (Phase 2)
- Pattern learning and retrieval (Phase 3)
- Multi-agent coordination (Phase 4)
- Real-time sync and collaboration (Phase 5)
- Cross-session memory search (Phase 6)

### Expected Changes

**After Phase 2 Implementation**:
- New session endpoints will be added
- Vector embedding operations will be measured
- Session event logging performance tracked
- Semantic search latencies established

**Performance Targets** (Proposed):
- Health check: < 10ms (already achieved)
- Single item queries: < 500ms (mostly achieved, outliers need fixing)
- List queries: < 1000ms (projects endpoint needs work)
- Concurrent throughput: > 10 req/sec (current: 3.3 req/sec)

## Recommendations

### Immediate Actions (Phase 1)

1. **Fix List Projects Performance**
   - Priority: **CRITICAL**
   - Current: 6+ seconds
   - Target: < 1 second
   - Actions: Add pagination, reduce payload, implement caching

2. **Investigate Single Record Fetch Outliers**
   - Priority: **HIGH**
   - Issue: P95 20x slower than P50
   - Actions: Review query execution plans, check indexing, analyze connection pool

3. **Optimize Knowledge Items Summary**
   - Priority: **MEDIUM**
   - Current: ~1 second
   - Target: < 500ms
   - Actions: Review aggregation logic, consider caching

### Future Monitoring (Phases 2-6)

1. **Session Memory Performance** (Phase 2)
   - Track session creation/retrieval times
   - Monitor embedding generation latency
   - Measure semantic search performance

2. **Pattern Learning Performance** (Phase 3)
   - Pattern harvest operation timing
   - Pattern search latency with vector similarity

3. **Multi-Agent Coordination** (Phase 4)
   - Context retrieval performance
   - Cross-agent data access patterns

4. **Real-Time Sync** (Phase 5)
   - Event propagation latency
   - WebSocket connection overhead

## Testing Methodology

### Approach

1. **Sequential Testing**: Each endpoint tested with 20-30 iterations
2. **Concurrent Testing**: 10 simultaneous requests to measure parallelism
3. **Percentile Calculation**: Using Python statistics.quantiles() for P50/P95/P99
4. **Success Tracking**: Every request logged with status code and timing
5. **Error Handling**: 50ms delay between requests to avoid overwhelming system

### Tools Used

- **HTTP Client**: Python httpx.AsyncClient
- **Timing**: time.perf_counter() for microsecond precision
- **Statistics**: Python statistics module for percentile calculations
- **Script**: `scripts/performance_baseline.py`

### Reproducibility

To rerun this baseline:

```bash
cd /Users/sergevilleneuve/Documents/Projects/Archon
python3 scripts/performance_baseline.py
```

Results saved to: `performance_baseline_results.json`

## Appendix: Raw Data

Full JSON results available in: `performance_baseline_results.json`

### Test Environment Details

- **Operating System**: macOS (Darwin 25.3.0)
- **Python Version**: 3.12+
- **Database**: Supabase PostgreSQL with pgvector
- **Backend**: FastAPI on port 8181
- **Test Location**: Local development environment

### Data Completeness

- **Total Endpoints Tested**: 7 API endpoints
- **Total Database Queries Tested**: 5 query patterns
- **Total Requests**: 260 (230 sequential + 30 DB queries)
- **Concurrent Requests**: 10
- **Success Rate**: 100% (no failures)
- **Data Quality**: All tests completed successfully

---

**Document Created By**: Claude (Archon Agent)
**Last Updated**: 2026-02-18
**Task**: Create Baseline Performance Metrics (Phase 1, Task 7)
**Project**: Shared Memory System Implementation
**Next Steps**: Begin Phase 2 - Session Memory System implementation with performance tracking
