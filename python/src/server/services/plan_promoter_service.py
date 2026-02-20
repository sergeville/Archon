"""
Plan Promoter Service for Archon

Parses PLANS_INDEX.md, reads plan files, uses AI to extract tasks,
and creates Archon projects + tasks from plan files.
"""

import os
import re
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


class ExtractedTask(BaseModel):
    title: str
    description: str
    priority: str
    feature: str | None = None


class TaskExtractionResult(BaseModel):
    tasks: list[ExtractedTask]


class PlanPromoterService:
    DOCUMENTS_BASE_PATH = os.getenv("DOCUMENTS_BASE_PATH", "/documents")
    PLANS_INDEX_PATH = "Documentation/System/PLANS_INDEX.md"

    def list_plans(self) -> list[dict[str, Any]]:
        """Parse PLANS_INDEX.md and return all plans with section info and promotion status."""
        index_path = os.path.join(self.DOCUMENTS_BASE_PATH, self.PLANS_INDEX_PATH)

        try:
            with open(index_path) as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"PLANS_INDEX.md not found at {index_path}. "
                "Ensure the ~/Documents/ volume is mounted and DOCUMENTS_BASE_PATH is set correctly."
            )

        plans = []
        current_section = "Uncategorized"

        for line in content.split("\n"):
            # Track current section from ## headers
            if line.startswith("## "):
                current_section = line[3:].strip()
                continue

            # Skip non-table lines
            if not line.startswith("|"):
                continue

            # Skip separator rows (e.g. |---|---|)
            if re.match(r"^\|[-| ]+\|$", line.strip()):
                continue

            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) < 3:
                continue

            name = cells[0]
            path_raw = cells[1] if len(cells) > 1 else ""
            status = cells[2] if len(cells) > 2 else ""
            notes = cells[3] if len(cells) > 3 else ""

            # Skip header row
            if name.lower() == "plan":
                continue

            # Skip struck-through entries
            if name.startswith("~~"):
                continue

            # Extract path from backticks
            path_match = re.search(r"`([^`]+)`", path_raw)
            if not path_match:
                continue
            path = path_match.group(1)

            plans.append({
                "name": name,
                "path": path,
                "status": status,
                "notes": notes,
                "section": current_section,
            })

        # Check which plans are already promoted (matching Archon project title)
        from .projects.project_service import ProjectService

        project_service = ProjectService()
        success, result = project_service.list_projects(include_content=False)
        existing_projects: dict[str, str] = {}
        if success:
            for project in result.get("projects", []):
                existing_projects[project["title"]] = project["id"]

        for plan in plans:
            project_id = existing_projects.get(plan["name"])
            plan["already_promoted"] = project_id is not None
            plan["project_id"] = project_id

        return plans

    def _read_plan_file(self, path: str) -> str:
        """Read a plan file from the documents directory."""
        full_path = os.path.join(self.DOCUMENTS_BASE_PATH, path)
        try:
            with open(full_path) as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Plan file not found: {full_path}")

    def _get_llm_model(self) -> str:
        """Determine the LLM model string for PydanticAI based on available API keys."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if anthropic_key:
            return "anthropic:claude-sonnet-4-6"
        elif openai_key:
            return "openai:gpt-4o"
        else:
            raise RuntimeError(
                "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in environment."
            )

    async def _extract_tasks_with_ai(self, plan_content: str) -> list[dict[str, Any]]:
        """Use PydanticAI to extract structured implementation tasks from plan content."""
        model = self._get_llm_model()

        agent: Agent[None, TaskExtractionResult] = Agent(
            model=model,
            result_type=TaskExtractionResult,
            system_prompt=(
                "You are a project management assistant. Extract 10-20 concrete implementation tasks "
                "from the provided plan document.\n\n"
                "For each task:\n"
                "- title: Short imperative sentence (e.g., 'Create API endpoint for plan listing')\n"
                "- description: Specific implementation details and acceptance criteria\n"
                "- priority: One of: low, medium, high, critical\n"
                "- feature: The phase or section name this task belongs to (optional)\n\n"
                "Return tasks that collectively implement the entire plan. "
                "Focus on concrete, actionable development tasks."
            ),
        )

        result = await agent.run(
            f"Extract implementation tasks from this plan document:\n\n{plan_content[:8000]}"
        )

        return [
            {
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "feature": task.feature,
            }
            for task in result.data.tasks
        ]

    async def promote_plan(self, plan_path: str, plan_name: str) -> tuple[bool, dict[str, Any]]:
        """
        Promote a plan to an Archon project with AI-generated tasks.

        Steps:
        1. Read plan file
        2. Create project in Archon
        3. Extract tasks using AI
        4. Bulk-create tasks

        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # 1. Read the plan file
            plan_content = self._read_plan_file(plan_path)

            # 2. Create the project
            from .projects.project_service import ProjectService

            project_service = ProjectService()
            success, result = project_service.create_project(title=plan_name)

            if not success:
                return False, {"error": f"Failed to create project: {result.get('error', 'Unknown error')}"}

            project_id = result["project"]["id"]
            logger.info(f"Created project '{plan_name}' with ID: {project_id}")

            # 3. Extract tasks using AI
            try:
                extracted_tasks = await self._extract_tasks_with_ai(plan_content)
            except Exception as e:
                logger.error(f"AI task extraction failed: {e}", exc_info=True)
                return False, {
                    "error": f"AI task extraction failed: {str(e)}. Project was created with ID: {project_id}",
                    "project_id": project_id,
                }

            if not extracted_tasks:
                return False, {
                    "error": "AI returned no tasks. Project was created but has no tasks.",
                    "project_id": project_id,
                }

            # 4. Bulk-create tasks
            from .projects.task_service import TaskService

            task_service = TaskService()
            tasks_created = 0

            for i, task_data in enumerate(extracted_tasks):
                success, task_result = await task_service.create_task(
                    project_id=project_id,
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    priority=task_data.get("priority", "medium"),
                    feature=task_data.get("feature"),
                    task_order=i,
                    assignee="User",
                )
                if success:
                    tasks_created += 1
                else:
                    logger.warning(
                        f"Failed to create task '{task_data['title']}': {task_result.get('error')}"
                    )

            logger.info(f"Created {tasks_created}/{len(extracted_tasks)} tasks for project '{plan_name}'")

            return True, {
                "project_id": project_id,
                "project_title": plan_name,
                "task_count": len(extracted_tasks),
                "tasks_created": tasks_created,
            }

        except FileNotFoundError as e:
            return False, {"error": str(e)}
        except Exception as e:
            logger.error(f"Error promoting plan: {e}", exc_info=True)
            return False, {"error": f"Error promoting plan: {str(e)}"}
