import os
import re
import json
import asyncio
from datetime import datetime
from src.server.services.projects.task_service import TaskService
from src.server.utils import get_supabase_client

PROJECT_ID = "3fc1cc09-5742-40ae-967d-c4b0f02fc5f6"
SQL_FILE = "/app/migration/shared_memory_project.sql"

async def main():
    if not os.path.exists(SQL_FILE):
        print(f"SQL file not found: {SQL_FILE}")
        return

    with open(SQL_FILE, 'r') as f:
        content = f.read()

    # Regex to find task inserts
    task_pattern = re.compile(
        r"INSERT INTO archon_tasks.*?SELECT.*?project\.id,\s*'(.*?)',\s*'(.*?)',\s*'(.*?)',\s*'(.*?)',\s*(\d+),\s*jsonb_build_object\((.*?)\),\s*ARRAY\[(.*?)\]",
        re.DOTALL
    )

    task_service = TaskService()
    tasks_created = 0

    for match in task_pattern.finditer(content):
        title, description, status, assignee, task_order, metadata_args, tags_str = match.groups()
        
        # Clean up
        description = description.replace("''", "'")
        title = title.replace("''", "'")
        
        # Parse metadata_args for the phase (feature)
        phase = "General"
        meta_matches = re.findall(r"'(.*?)',\s*(?:'(.*?)'|([\d\.]+)|ARRAY\[(.*?)\])", metadata_args, re.DOTALL)
        for key, val_str, val_num, val_array in meta_matches:
            if key == 'phase':
                phase = val_str or val_array or "General"

        # Create task using existing columns
        success, result = await task_service.create_task(
            project_id=PROJECT_ID,
            title=title,
            description=description,
            assignee=assignee,
            task_order=int(task_order),
            feature=phase
        )
        
        if success:
            tasks_created += 1
        else:
            print(f"Failed to create task '{title}': {result}")

    print(f"Successfully created {tasks_created} tasks for project {PROJECT_ID}")

if __name__ == "__main__":
    asyncio.run(main())
