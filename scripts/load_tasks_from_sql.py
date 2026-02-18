#!/usr/bin/env python3
"""
Load Shared Memory Project Tasks from SQL File

This script parses the SQL file and loads all 64 tasks into Archon
using the Supabase client directly.

Usage:
    # Run via Docker (recommended - all deps already installed):
    docker compose exec archon-server python /app/scripts/load_tasks_from_sql.py

    # Or run locally if you have dependencies:
    cd ~/Documents/Projects/Archon/python
    uv run --group server python ../scripts/load_tasks_from_sql.py
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

# Try to import dependencies
try:
    from supabase import create_client, Client
    print("✅ Dependencies loaded")
except ImportError:
    print("❌ Missing dependencies.")
    print("   Run this script via Docker:")
    print("   docker compose exec archon-server python /app/scripts/load_tasks_from_sql.py")
    sys.exit(1)

# Environment variables (will be loaded from Docker or local env)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# Strip /rest/v1 suffix if present (Supabase client adds it automatically)
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL[:-8]  # Remove last 8 characters

SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PROJECT_ID = "7c3528df-b1a2-4fde-9fee-68727c15b6c6"  # Shared Memory project ID

def parse_sql_value(value: str) -> Any:
    """Parse SQL value to Python type."""
    value = value.strip()

    # Handle NULL
    if value.upper() == "NULL":
        return None

    # Handle strings (single-quoted in SQL)
    if value.startswith("'") and value.endswith("'"):
        # Unescape single quotes
        return value[1:-1].replace("''", "'")

    # Handle numbers
    if value.replace(".", "", 1).replace("-", "", 1).isdigit():
        if "." in value:
            return float(value)
        return int(value)

    # Handle booleans
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    return value


def parse_array(array_str: str) -> list:
    """Parse PostgreSQL ARRAY[] to Python list."""
    if not array_str or array_str.strip().upper() == "NULL":
        return []

    # Remove ARRAY[ and ]
    array_str = re.sub(r"^ARRAY\s*\[", "", array_str, flags=re.IGNORECASE)
    array_str = re.sub(r"\]$", "", array_str)

    # Split by comma, respecting quotes
    items = []
    current = ""
    in_quotes = False

    for char in array_str:
        if char == "'" and (not current or current[-1] != "\\"):
            in_quotes = not in_quotes
            current += char
        elif char == "," and not in_quotes:
            items.append(parse_sql_value(current.strip()))
            current = ""
        else:
            current += char

    # Add last item
    if current.strip():
        items.append(parse_sql_value(current.strip()))

    return items


def parse_jsonb_object(jsonb_str: str) -> dict:
    """Parse PostgreSQL jsonb_build_object() to Python dict."""
    if not jsonb_str or jsonb_str.strip().upper() == "NULL":
        return {}

    # Remove jsonb_build_object( and )
    jsonb_str = re.sub(r"^jsonb_build_object\s*\(", "", jsonb_str, flags=re.IGNORECASE)
    jsonb_str = re.sub(r"\)$", "", jsonb_str)

    # Parse key-value pairs
    result = {}
    parts = []
    current = ""
    depth = 0
    in_quotes = False

    for char in jsonb_str:
        if char == "'" and (not current or current[-1] != "\\"):
            in_quotes = not in_quotes
        elif char in "([" and not in_quotes:
            depth += 1
        elif char in ")]" and not in_quotes:
            depth -= 1
        elif char == "," and depth == 0 and not in_quotes:
            parts.append(current.strip())
            current = ""
            continue

        current += char

    if current.strip():
        parts.append(current.strip())

    # Process pairs
    i = 0
    while i < len(parts):
        if i + 1 < len(parts):
            key = parse_sql_value(parts[i])
            value_str = parts[i + 1].strip()

            # Check if value is an array
            if value_str.upper().startswith("ARRAY"):
                value = parse_array(value_str)
            else:
                value = parse_sql_value(value_str)

            result[key] = value
            i += 2
        else:
            i += 1

    return result


def parse_insert_statement(insert_sql: str) -> dict | None:
    """Parse a single INSERT INTO archon_tasks statement."""
    try:
        # Extract the SELECT values
        select_match = re.search(
            r"SELECT\s+(.*?)\s+FROM\s+project",
            insert_sql,
            re.DOTALL | re.IGNORECASE
        )

        if not select_match:
            return None

        values_str = select_match.group(1).strip()

        # Split by comma at top level (respecting parentheses and quotes)
        values = []
        current = ""
        depth = 0
        in_quotes = False

        for char in values_str:
            if char == "'" and (not current or current[-1] != "\\"):
                in_quotes = not in_quotes
            elif char in "([" and not in_quotes:
                depth += 1
            elif char in ")]" and not in_quotes:
                depth -= 1
            elif char == "," and depth == 0 and not in_quotes:
                values.append(current.strip())
                current = ""
                continue

            current += char

        if current.strip():
            values.append(current.strip())

        # Should have 8 values: project.id, title, description, status, assignee, task_order, metadata, tags
        if len(values) < 7:
            print(f"⚠️  Warning: Expected 8 values, got {len(values)}")
            return None

        # Skip project.id (values[0])
        # Parse the rest
        # Note: archon_tasks table doesn't have a 'metadata' column
        # Parse metadata to extract useful info for description/tags
        metadata = parse_jsonb_object(values[6]) if len(values) > 6 else {}

        # Build enhanced description with metadata info
        base_description = parse_sql_value(values[2])

        # Add metadata info to description if present
        if metadata:
            meta_lines = []
            if 'phase' in metadata:
                meta_lines.append(f"Phase: {metadata['phase']}")
            if 'week' in metadata:
                meta_lines.append(f"Week: {metadata['week']}")
            if 'day' in metadata:
                meta_lines.append(f"Day: {metadata['day']}")
            if 'estimated_hours' in metadata:
                meta_lines.append(f"Estimated: {metadata['estimated_hours']} hours")
            if 'acceptance_criteria' in metadata:
                criteria = metadata['acceptance_criteria']
                if isinstance(criteria, list):
                    meta_lines.append(f"Acceptance Criteria: {'; '.join(criteria)}")

            if meta_lines:
                enhanced_description = base_description + "\n\n" + " | ".join(meta_lines)
            else:
                enhanced_description = base_description
        else:
            enhanced_description = base_description

        task = {
            "project_id": PROJECT_ID,
            "title": parse_sql_value(values[1]),
            "description": enhanced_description,
            "status": parse_sql_value(values[3]),
            "assignee": parse_sql_value(values[4]),
            "task_order": parse_sql_value(values[5]),
            "priority": "medium",  # Default priority
            "feature": metadata.get('phase') if metadata else None,
        }

        # Tags might be index 7 or might not exist
        # Note: Supabase doesn't support array insertion via Python client for archon_tasks
        # We'll skip tags for now
        # if len(values) > 7:
        #     task["tags"] = parse_array(values[7])

        return task

    except Exception as e:
        print(f"❌ Error parsing INSERT: {str(e)}")
        print(f"   SQL snippet: {insert_sql[:200]}...")
        return None


def load_tasks_from_sql(sql_file: Path) -> list[dict]:
    """Parse SQL file and extract all task definitions."""
    print(f"📖 Reading SQL file: {sql_file}")

    sql_content = sql_file.read_text()

    # Find all INSERT INTO archon_tasks statements
    insert_pattern = r"INSERT INTO archon_tasks\s*\([^)]+\)\s*SELECT.*?FROM project;"
    matches = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)

    print(f"📋 Found {len(matches)} task INSERT statements")

    tasks = []
    for i, insert_sql in enumerate(matches, 1):
        task = parse_insert_statement(insert_sql)
        if task:
            tasks.append(task)
            title_short = task['title'][:50] + "..." if len(task['title']) > 50 else task['title']
            print(f"   ✅ [{i:2d}] {title_short}")
        else:
            print(f"   ❌ [{i:2d}] Failed to parse")

    return tasks


def insert_tasks(supabase: Client, tasks: list[dict]) -> tuple[int, int]:
    """Insert tasks into Supabase."""
    print(f"\n📥 Inserting {len(tasks)} tasks into Archon...")

    success_count = 0
    error_count = 0

    for i, task in enumerate(tasks, 1):
        try:
            result = supabase.table("archon_tasks").insert(task).execute()
            success_count += 1
            title_short = task['title'][:45] + "..." if len(task['title']) > 45 else task['title']
            print(f"   ✅ [{i:2d}/{len(tasks)}] {title_short}")
        except Exception as e:
            error_count += 1
            title_short = task['title'][:35] + "..." if len(task['title']) > 35 else task['title']
            print(f"   ❌ [{i:2d}/{len(tasks)}] {title_short}")
            print(f"      Error: {str(e)[:80]}")

    return success_count, error_count


def verify_tasks(supabase: Client) -> int:
    """Verify tasks were loaded correctly."""
    print(f"\n🔍 Verifying tasks...")

    try:
        result = supabase.table("archon_tasks")\
            .select("id, title, status")\
            .eq("project_id", PROJECT_ID)\
            .execute()

        task_count = len(result.data)
        print(f"   ✅ Found {task_count} tasks for project")

        # Group by status
        statuses = {}
        for task in result.data:
            status = task["status"]
            statuses[status] = statuses.get(status, 0) + 1

        print(f"   📊 Status breakdown:")
        for status, count in statuses.items():
            print(f"      - {status}: {count}")

        return task_count

    except Exception as e:
        print(f"   ❌ Verification failed: {str(e)}")
        return 0


def main():
    """Main execution."""
    print("=" * 70)
    print("🚀 Shared Memory Project - Task Loader")
    print("=" * 70)
    print()

    # Check credentials
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase credentials")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_KEY")
        sys.exit(1)

    print(f"✅ Supabase URL: {SUPABASE_URL}")
    print(f"✅ Target Project: {PROJECT_ID}")
    print()

    # Determine SQL file location (Docker vs local)
    possible_paths = [
        Path("/app/migration/shared_memory_project.sql"),  # Docker
        Path(__file__).parent.parent / "migration" / "shared_memory_project.sql",  # Local
    ]

    sql_file = None
    for path in possible_paths:
        if path.exists():
            sql_file = path
            break

    if not sql_file:
        print(f"❌ SQL file not found in any of these locations:")
        for path in possible_paths:
            print(f"   - {path}")
        sys.exit(1)

    # Parse tasks
    tasks = load_tasks_from_sql(sql_file)

    if not tasks:
        print("❌ No tasks parsed from SQL file")
        sys.exit(1)

    print(f"\n✅ Successfully parsed {len(tasks)} tasks")
    print()

    # Confirm before inserting
    print("=" * 70)
    print(f"⚠️  About to insert {len(tasks)} tasks into Archon database")
    print("=" * 70)

    # Create Supabase client
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
        sys.exit(1)

    # Insert tasks
    print()
    success_count, error_count = insert_tasks(supabase, tasks)

    # Verify
    verified_count = verify_tasks(supabase)

    # Summary
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total tasks parsed:    {len(tasks)}")
    print(f"Successfully inserted: {success_count}")
    print(f"Errors:                {error_count}")
    print(f"Verified in database:  {verified_count}")
    print()

    if success_count == len(tasks) and verified_count == len(tasks):
        print("✅ ALL TASKS LOADED SUCCESSFULLY!")
        print()
        print("🌐 View in Archon UI:")
        print("   http://localhost:3737/projects")
        print()
        return 0
    else:
        print("⚠️  Some tasks failed to load. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
