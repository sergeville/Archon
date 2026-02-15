#!/bin/bash
# ============================================================================
# Load Shared Memory System Project into Archon
# ============================================================================
# This script loads the complete 6-week implementation plan as an Archon
# project with all tasks, features, and metadata.
# ============================================================================

set -e  # Exit on error

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🎯 Loading Shared Memory System Project into Archon..."
echo ""

# Check if Archon is running
echo "1. Checking if Archon services are running..."
if ! docker compose ps | grep -q "archon-server"; then
    echo "❌ Archon services not running. Starting them now..."
    docker compose up -d
    echo "⏳ Waiting 10 seconds for services to initialize..."
    sleep 10
else
    echo "✅ Archon services are running"
fi

# Check MCP server is running
echo ""
echo "2. Checking MCP server status..."
if docker compose ps | grep -q "archon-mcp.*Up"; then
    echo "✅ MCP server is running"
    echo "   Note: /health endpoint has a known issue but server is functional"
else
    echo "❌ MCP server not running. Starting it now..."
    docker compose up -d archon-mcp
    sleep 5
fi

# Check Supabase connection
echo ""
echo "3. Checking Supabase connection..."
if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL not set. Please set it in your .env file"
    exit 1
fi
echo "✅ SUPABASE_URL is set: $SUPABASE_URL"

# Load the project SQL
echo ""
echo "4. Loading project into database..."
echo "   This will create:"
echo "   - 1 project: 'Shared Memory System Implementation'"
echo "   - 60+ tasks organized by phase (Week 1-6)"
echo "   - Task dependencies and metadata"
echo ""

if psql "$SUPABASE_URL" -f migration/shared_memory_project.sql; then
    echo "✅ Project loaded successfully!"
else
    echo "❌ Failed to load project. Check your database connection."
    exit 1
fi

# Verify project was created
echo ""
echo "5. Verifying project creation..."
PROJECT_COUNT=$(psql "$SUPABASE_URL" -t -c "SELECT COUNT(*) FROM archon_projects WHERE title = 'Shared Memory System Implementation';" | tr -d ' ')
TASK_COUNT=$(psql "$SUPABASE_URL" -t -c "SELECT COUNT(*) FROM archon_tasks WHERE project_id IN (SELECT id FROM archon_projects WHERE title = 'Shared Memory System Implementation');" | tr -d ' ')

if [ "$PROJECT_COUNT" -eq "1" ]; then
    echo "✅ Project created: 'Shared Memory System Implementation'"
    echo "✅ Tasks created: $TASK_COUNT"
else
    echo "❌ Project not found. Something went wrong."
    exit 1
fi

# Get project ID
PROJECT_ID=$(psql "$SUPABASE_URL" -t -c "SELECT id FROM archon_projects WHERE title = 'Shared Memory System Implementation' LIMIT 1;" | tr -d ' ')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SUCCESS! Project loaded into Archon"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Project Details:"
echo "   - Project ID: $PROJECT_ID"
echo "   - Total Tasks: $TASK_COUNT"
echo "   - Phases: 6 (Week 1-6)"
echo "   - Timeline: 6 weeks"
echo "   - Estimated Effort: 120-150 hours"
echo ""
echo "🌐 View in Archon UI:"
echo "   http://localhost:3737"
echo ""
echo "🔧 Test MCP Connection:"
echo "   Use this in Claude Code or any MCP client:"
echo ""
echo "   find_projects(query=\"Shared Memory\")"
echo "   find_tasks(project_id=\"$PROJECT_ID\")"
echo ""
echo "📚 Next Steps:"
echo "   1. Open Archon UI and view the project"
echo "   2. Read: docs/SHARED_MEMORY_PROJECT_GUIDE.md"
echo "   3. Start with Phase 1, Week 1 tasks"
echo "   4. Use Archon to track your progress!"
echo ""
echo "📖 Documentation:"
echo "   - Implementation Plan: See original plan document"
echo "   - Project Guide: docs/SHARED_MEMORY_PROJECT_GUIDE.md"
echo "   - Test Strategy: Included in plan document"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Pro Tip: You're now using Archon to build Archon! This is"
echo "   'dogfooding' - testing the product by using it yourself."
echo "   Every pattern you learn while building this will improve"
echo "   Archon's shared memory system. Meta! 🎯"
echo ""
